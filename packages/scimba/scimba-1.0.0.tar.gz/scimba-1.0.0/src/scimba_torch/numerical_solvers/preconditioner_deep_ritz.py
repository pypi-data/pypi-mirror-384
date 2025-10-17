"""Deep Ritz preconditioners."""

from typing import cast

import torch

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.numerical_solvers.functional_operator import (
    # vectorize_dict_of_func,
    # TYPE_THETA,
    TYPE_ARGS,
    # TYPE_DICT_OF_FUNC_ARGS,
    TYPE_DICT_OF_VMAPS,
    TYPE_FUNC_ARGS,
    TYPE_VMAPS,
    FunctionalOperator,
)

# from scimba_torch.domain.meshless_domain.domain_2d import Square2D
# from torchquad import set_up_backend  # Necessary to enable GPU support
# from torchquad import Trapezoid, Gaussian, Simpson
from scimba_torch.numerical_solvers.preconditioner_solvers import (
    MatrixPreconditionerSolver,
    _mjactheta,
    _transpose_i_j,
)
from scimba_torch.physical_models.elliptic_pde.abstract_elliptic_pde import (
    RitzFormEllipticPDE,
)
from scimba_torch.physical_models.elliptic_pde.linear_order_2 import (
    DivAGradUPDE,
)
from scimba_torch.utils.scimba_tensors import LabelTensor

TYPE_DATA = tuple[LabelTensor, ...] | dict[str, tuple[LabelTensor, ...]]

ACCEPTED_PDE_TYPES = RitzFormEllipticPDE | DivAGradUPDE


class MatrixPreconditionerDeepRitz(MatrixPreconditionerSolver):
    """Matrix-based preconditioner for pinns.

    Args:
        space: The approximation space.
        pde: The PDE to be solved.
        **kwargs: Additional keyword arguments.

    Raises:
        AttributeError: If the input PDE does not have the required attributes.
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        pde: ACCEPTED_PDE_TYPES,
        **kwargs,
    ):
        super().__init__(space, pde, **kwargs)

        name = "energy_matrix"
        if not (hasattr(self.pde, name)):
            raise AttributeError("input PDE must have an attribute %s" % name)
        assert hasattr(self.pde, name)
        self.energy_matrix = getattr(self.pde, name)
        if not callable(self.energy_matrix):
            raise AttributeError("attribute %s of input PDE must be a method" % name)

        self.operator_bc: None | FunctionalOperator = None
        if self.has_bc:
            self.operator_bc = FunctionalOperator(self.pde, "functional_operator_bc")

        self.operator_ic: None | FunctionalOperator = None
        if self.has_ic:
            self.operator_ic = FunctionalOperator(self.pde, "functional_operator_ic")

    def vectorize_along_physical_variables(self, func: TYPE_FUNC_ARGS) -> TYPE_VMAPS:
        """Vectorizes a function along physical variables based on the type of space.

        Args:
            func: The function to be vectorized.

        Returns:
            The vectorized function.

        Raises:
            NotImplementedError: If the type of space is not supported.
        """
        scheme: tuple[int | None, ...] = tuple()
        if self.type_space == "space":
            scheme = (0, 0, None)
        elif self.type_space == "phase_space":
            raise NotImplementedError("phase_space")
        else:
            # scheme = (0, 0, 0, None)
            raise NotImplementedError("time_space")

        return torch.func.vmap(func, scheme)


class EnergyNaturalGradientPreconditioner(MatrixPreconditionerDeepRitz):
    """Energy Natural Gradient preconditioner for Deep Ritz methods.

    Args:
        space: The approximation space used in the Deep Ritz method.
        pde: The elliptic PDE represented as an instance of RitzForm_Elliptic
        **kwargs: Additional keyword arguments.

    Raises:
        ValueError: If the number of unknowns in the space is greater than 1.
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        pde: RitzFormEllipticPDE | DivAGradUPDE,
        # is_operator_linear: bool = False,
        **kwargs,
    ):
        super().__init__(space, pde, **kwargs)
        # self.is_operator_linear = is_operator_linear
        self.matrix_regularization = kwargs.get("matrix_regularization", 1e-6)

        if self.space.nb_unknowns > 1:
            raise ValueError(
                "EnergyNaturalGradient preconditioner is only implemented for scalar "
                "problems."
            )

        self.vectorized_Phi = self.vectorize_along_physical_variables(
            self.eval_and_gradx_and_jactheta
        )
        self.vectorized_Phi_bc: None | TYPE_DICT_OF_VMAPS = None

        if self.has_bc:
            self.operator_bc = cast(FunctionalOperator, self.operator_bc)
            self.linear_Phi_bc = self.operator_bc.apply_func_to_dict_of_func(
                _transpose_i_j(-1, -2, _mjactheta),
                self.operator_bc.apply_to_func(self.eval_func),
            )
            self.vectorized_Phi_bc = self.vectorize_along_physical_variables_bc(
                self.linear_Phi_bc
            )

    def eval_and_gradx(self, *args: TYPE_ARGS):
        """Evaluate the function and compute its gradient.

        Args:
            *args: Input arguments where the last argument is the parameters of the
                network.

        Returns:
            A tensor containing the function evaluation and its gradient.
        """
        return torch.func.jacrev(self.eval_func, 0)(*args)

    def eval_and_gradx_and_jactheta(self, *args: TYPE_ARGS):
        """Evaluate the function, compute its gradient, and the Jacobian.

        Args:
            *args: Input arguments where the last argument is the parameters of the
                network.

        Returns:
            A tensor containing the function evaluation, its gradient, and the Jacobian
        """
        return _transpose_i_j(-1, -2, _mjactheta)(self.eval_and_gradx, *args)

    def compute_preconditioning_matrix(
        self, labels: torch.Tensor, *args: torch.Tensor, **kwargs
    ) -> torch.Tensor:
        """Compute the preconditioning matrix.

        Args:
            labels: Tensor of labels corresponding to the input data.
            *args: Additional arguments required for computing the matrix.
            **kwargs: Additional keyword arguments.

        Returns:
            The computed preconditioning matrix as a tensor.
        """
        # mu = args[-1]
        # N = args[0].shape[0]
        theta = self.get_formatted_current_theta()

        # if isinstance(self.space.spatial_domain, Square2D):
        #
        #     # set_up_backend("torch", data_type="float64")

        # dimx = x.shape[1]
        # dimmu = mu.shape[1]
        #
        #     # print("here")
        #     def func_to_integrate( xmu ):
        #         xarg, muarg = xmu[:, 0:dimx], xmu[:, dimx:]
        #         Phi = test_vect(xarg, muarg, theta)
        #         # print("Phi.shape: ",  Phi.shape)
        #         Phi2 = Phi*muarg.view(-1, 1, 1)
        #         return torch.einsum("ijl,ikl->ijk", Phi2, Phi)
        #
        #     x_domain = self.space.spatial_domain.bounds
        #     mu_domain = torch.cat( ( torch.min(mu, 0)[0][None],
        #       torch.max(mu, 0)[0][None] ), dim = 0).transpose(-2, -1)
        #     integration_domain = torch.cat( (x_domain, mu_domain), dim = 0 )
        #     integrator = Trapezoid()
        #     test = integrator.integrate(func_to_integrate, dim=dimx+dimmu, N=N,
        #       integration_domain=integration_domain)
        #
        # else:
        Phi = self.vectorized_Phi(*args, theta)

        # Phi2 = Phi * mu.view(-1, 1, 1)
        # M = torch.einsum("ijl,ikl->jk", Phi2, Phi) / N
        M = self.energy_matrix({"eval_and_gradx_and_gradtheta": Phi}, args[0], args[1])

        return M + self.matrix_regularization * torch.eye(self.ndof)

    def compute_preconditioning_matrix_bc(
        self, labels: torch.Tensor, *args: torch.Tensor, **kwargs
    ) -> torch.Tensor:
        """Compute the boundary condition preconditioning matrix.

        Args:
            labels: Tensor of labels corresponding to the boundary condition data.
            *args: Additional arguments required for computing the matrix.
            **kwargs: Additional keyword arguments.

        Returns:
            The computed boundary condition preconditioning matrix as a tensor.
        """
        N = args[0].shape[0]
        theta = self.get_formatted_current_theta()

        self.operator_bc = cast(FunctionalOperator, self.operator_bc)
        self.vectorized_Phi_bc = cast(TYPE_DICT_OF_VMAPS, self.vectorized_Phi_bc)

        Phi = self.operator_bc.apply_dict_of_vmap_to_label_tensors(
            self.vectorized_Phi_bc, theta, labels, *args
        )
        # print("Phi.shape: ", Phi.shape)
        # if not self.is_operator_linear:
        # Phi = Phi[..., None]

        # Phi_test = self.operator_bc.apply_dict_of_vmap_to_LabelTensors(
        #   self.vectorized_Phi_bc_test, theta, labels, *args )[..., None]
        # assert torch.allclose(Phi, Phi_test)

        M = torch.einsum(
            "ijk,ilk->jl", Phi, Phi
        ) / N + self.matrix_regularization * torch.eye(self.ndof)
        return M

    def compute_preconditioning_matrix_ic(
        self, labels: torch.Tensor, *args: torch.Tensor, **kwargs
    ) -> torch.Tensor:
        """Compute the initial condition preconditioning matrix.

        Args:
            labels: Tensor of labels corresponding to the boundary condition data.
            *args: Additional arguments required for computing the matrix.
            **kwargs: Additional keyword arguments.

        Returns:
            NotImplementedError.
        """
        #         N = args[0].shape[0]
        #         theta = self.get_formatted_current_theta()
        #
        #         self.operator_ic = cast(FunctionalOperator, self.operator_ic)
        #         self.vectorized_Phi_ic = cast(TYPE_DICT_OF_VMAPS,
        #         self.vectorized_Phi_ic)
        #
        #         Phi = self.operator_ic.apply_dict_of_vmap_to_LabelTensors(
        #             self.vectorized_Phi_ic, theta, labels, *args
        #         )
        #         if not self.is_operator_linear:
        #             Phi = Phi[..., None]
        #
        #         # Phi_test = self.operator_ic.apply_dict_of_vmap_to_LabelTensors(
        #           self.vectorized_Phi_ic_test, theta, labels, *args )[..., None]
        #         # assert torch.allclose(Phi, Phi_test)
        #
        #         M = torch.einsum(
        #             "ijk,ilk->jl", Phi, Phi
        #         ) / N + self.matrix_regularization * torch.eye(self.ndof)
        #         return M
        return NotImplementedError

    # def assemble_left_member_bc(self, data: tuple | dict, res_l: tuple)
    #   -> torch.Tensor:
    #
    #     self.operator_bc = cast(FunctionalOperator, self.operator_bc)
    #
    #     if len(self.operator_bc.dict_of_operators) == 1:
    #         return res_l[0]
    #
    #     args = self.get_args_for_operator_bc(data)
    #
    #     return self.operator_bc.cat_tuple_of_tensors(res_l, args[0], args[1])

    def __call__(
        self,
        epoch: int,
        data: tuple | dict,
        grads: torch.Tensor,
        res_l: tuple,
        res_r: tuple,
        **kwargs,
    ) -> torch.Tensor:
        """Apply the Energy Natural Gradient preconditioner to the input gradients.

        Args:
            epoch: Current training epoch.
            data: Training data, either as a tuple or a dictionary.
            grads: Gradient tensor to be preconditioned.
            res_l: Left residuals tuple.
            res_r: Right residuals tuple.
            **kwargs: Additional keyword arguments.

        Returns:
            The preconditioned gradient tensor.
        """
        M = self.get_preconditioning_matrix(data, **kwargs)

        if self.has_bc:
            Mb = self.get_preconditioning_matrix_bc(data, **kwargs)
            M += self.bc_weight * Mb
        #
        # if self.has_ic:
        #     Mi = self.get_preconditioning_matrix_ic(data, **kwargs)
        #     M += self.ic_weight * Mi

        preconditioned_grads = torch.linalg.lstsq(M, grads).solution
        return preconditioned_grads

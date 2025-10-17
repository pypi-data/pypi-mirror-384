"""Matrix preconditioner for solvers."""

from abc import abstractmethod

import torch

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.numerical_solvers.abstract_preconditioner import (
    AbstractPreconditioner,
)
from scimba_torch.numerical_solvers.functional_operator import (
    TYPE_ARGS,
    TYPE_DICT_OF_FUNC_ARGS,
    TYPE_DICT_OF_VMAPS,
    TYPE_FUNC_ARGS,
    TYPE_FUNC_FUNC_ARGS,
    TYPE_THETA,
    vectorize_dict_of_func,
)
from scimba_torch.physical_models.elliptic_pde.abstract_elliptic_pde import (
    EllipticPDE,
    RitzFormEllipticPDE,
)
from scimba_torch.physical_models.elliptic_pde.linear_order_2 import (
    DivAGradUPDE,
    LinearOrder2PDE,
)
from scimba_torch.physical_models.kinetic_pde.abstract_kinetic_pde import KineticPDE
from scimba_torch.physical_models.temporal_pde.abstract_temporal_pde import TemporalPDE
from scimba_torch.utils.scimba_tensors import LabelTensor

TYPE_DATA = tuple[LabelTensor, ...] | dict[str, tuple[LabelTensor, ...]]

ACCEPTED_PDE_TYPES = (
    EllipticPDE
    | TemporalPDE
    | KineticPDE
    | LinearOrder2PDE
    | RitzFormEllipticPDE
    | DivAGradUPDE
)


def functional_operator_id(
    func: TYPE_FUNC_ARGS,
    *args: TYPE_ARGS,
) -> torch.Tensor:
    """Identity functional operator that directly calls the input function.

    Args:
        func: The function to be called.
        *args: Arguments to be passed to the function.

    Returns:
        The result of calling the input function with the provided arguments.
    """
    return func(*args)


def default_pre_processing(*args: torch.Tensor) -> torch.Tensor:
    """Default pre-processing function that concatenates input tensors.

    Args:
        *args: Input tensors to be concatenated.

    Returns:
        The concatenated tensor.
    """
    return torch.cat(args[:], -1)


# utilities for functionals: should be in a special module called utility functions,
# or ...
# def component(self, i: int, func: TYPE_FUNC_ARGS) -> TYPE_FUNC_ARGS:
#     return lambda *args: func(*args)[..., i]


def _transpose_i_j(i: int, j: int, func: TYPE_FUNC_FUNC_ARGS) -> TYPE_FUNC_FUNC_ARGS:
    """Transpose two specified dimensions of the output of a function.

    Args:
        i: The first dimension to transpose.
        j: The second dimension to transpose.
        func: The function whose output dimensions are to be transposed.

    Returns:
        A function that transposes the i-th and j-th dimensions of the output of
        func.
    """
    return lambda *args: func(*args).transpose(i, j)


def _mjactheta(
    func: TYPE_FUNC_ARGS,
    *args: TYPE_ARGS,
    theta_pos: int = -1,
) -> torch.Tensor:
    """Compute the Jacobian of a function with respect to its parameters.

    Args:
        func: The function whose Jacobian is to be computed.
        *args: Arguments to be passed to the function.
        theta_pos: Position of the parameters in args (default: -1).

    Returns:
        The Jacobian matrix of the function with respect to its parameters.
    """
    js = torch.func.jacrev(func, theta_pos)(*args).values()

    # evaluate func to know its shape
    fshape = func(*args).shape
    reshape_arg = fshape + (-1,)

    res = torch.cat([j.reshape(reshape_arg) for j in js], dim=-1)

    return res


class MatrixPreconditionerSolver(AbstractPreconditioner):
    """Matrix-based preconditioner solver.

    Args:
        space: The approximation space.
        pde: The PDE to be solved.
        **kwargs: Additional keyword arguments:

            - functional_post_processing: A function to be applied after the main
              processing.
            - functional_pre_processing: A function to be applied before the main
              processing.
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        pde: ACCEPTED_PDE_TYPES,
        **kwargs,
    ):
        super().__init__(space, pde, **kwargs)

        self.post_processing = kwargs.get(
            "functional_post_processing", functional_operator_id
        )
        self.pre_processing = kwargs.get(
            "functional_pre_processing", default_pre_processing
        )

        assert isinstance(self.space, torch.nn.Module)

        assert hasattr(self.space, "ndof")
        self.ndof = self.space.ndof

        assert hasattr(self.space, "type_space"), (
            "self.space has no type_space attribute"
        )
        self.type_space = self.space.type_space

        assert hasattr(self.space, "named_parameters"), (
            "self.space has no named_parameters attribute"
        )
        self.named_parameters = self.space.named_parameters

    @abstractmethod
    def compute_preconditioning_matrix(
        self, labels: torch.Tensor, *args: torch.Tensor, **kwargs
    ) -> torch.Tensor:
        """Abstract method for computing the preconditioning matrix.

        Args:
            labels: The labels tensor.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            The preconditioning matrix.
        """

    @abstractmethod
    def compute_preconditioning_matrix_bc(
        self, labels: torch.Tensor, *args: torch.Tensor, **kwargs
    ) -> torch.Tensor:
        """Abstract method for computing the boundary condition preconditioning matrix.

        Args:
            labels: The labels tensor.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            The boundary condition preconditioning matrix.
        """

    @abstractmethod
    def compute_preconditioning_matrix_ic(
        self, labels: torch.Tensor, *args: torch.Tensor, **kwargs
    ) -> torch.Tensor:
        """Abstract method for computing the initial condition preconditioning matrix.

        Args:
            labels: The labels tensor.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            The initial condition preconditioning matrix.
        """

    def get_args_for_operator(self, data: TYPE_DATA, **kwargs) -> list[torch.Tensor]:
        """Get arguments for the main operator based on the type of space.

        Args:
            data: Input data, either as a tuple or a dictionary.
            **kwargs: Additional keyword arguments.

        Returns:
            A list of tensors to be used as arguments for the operator.

        Raises:
            NotImplementedError: If the type_space is 'phase_space'.
        """
        if self.type_space == "space":
            assert isinstance(data, tuple)
            args = [data[0].labels, data[0].x, data[1].x]
        elif self.type_space == "phase_space":
            # args = [data[0].x, data[1].x, data[2].x, data[3].x]
            raise NotImplementedError("phase_space")
        else:
            assert isinstance(data, dict)
            # args = [data[0].x, data[1].x, data[2].x]
            args = [
                data["inner"][1].labels,
                data["inner"][0].x,
                data["inner"][1].x,
                data["inner"][2].x,
            ]
            # raise NotImplementedError("time_space")
        return args

    def get_preconditioning_matrix(self, data: TYPE_DATA, **kwargs) -> torch.Tensor:
        """Get the preconditioning matrix using the main operator.

        Args:
            data: Input data, either as a tuple or a dictionary.
            **kwargs: Additional keyword arguments.

        Returns:
            The preconditioning matrix.
        """
        args = self.get_args_for_operator(data)

        return self.compute_preconditioning_matrix(*args, **kwargs)

    def get_args_for_operator_bc(self, data: TYPE_DATA, **kwargs) -> list[torch.Tensor]:
        """Get arguments for the boundary condition operator based on the type of space.

        Args:
            data: Input data, either as a tuple or a dictionary.
            **kwargs: Additional keyword arguments.

        Returns:
            A list of tensors to be used as arguments for the boundary condition
            operator.

        Raises:
            NotImplementedError: If the type_space is 'phase_space'.
        """
        if self.type_space == "space":
            assert isinstance(data, tuple)
            args = [data[2].labels, data[2].x, data[3].x, data[4].x]
            # TEST: add tensor of labels
            # args.append(data[2].labels[:,None])
        elif self.type_space == "phase_space":
            raise NotImplementedError("phase_space")
        else:
            assert isinstance(data, dict)
            args = [
                data["bc"][1].labels,
                data["bc"][0].x,
                data["bc"][1].x,
                data["bc"][2].x,
                data["bc"][3].x,
            ]
            # raise NotImplementedError("time_space")
        return args

    def get_preconditioning_matrix_bc(self, data: TYPE_DATA, **kwargs) -> torch.Tensor:
        """Get the preconditioning matrix using the boundary condition operator.

        Args:
            data: Input data, either as a tuple or a dictionary.
            **kwargs: Additional keyword arguments.

        Returns:
            The preconditioning matrix.
        """
        args = self.get_args_for_operator_bc(data)

        return self.compute_preconditioning_matrix_bc(args[0], *args[1:], **kwargs)

    def get_args_for_operator_ic(self, data: TYPE_DATA, **kwargs) -> list[torch.Tensor]:
        """Get arguments for the initial condition operator based on the type of space.

        Args:
            data: Input data, either as a tuple or a dictionary.
            **kwargs: Additional keyword arguments.

        Returns:
            A list of tensors to be used as arguments for the initial condition
            operator.

        Raises:
            ValueError: If the type_space is 'space'.
            NotImplementedError: If the type_space is 'phase_space'.
        """
        if self.type_space == "space":
            raise ValueError(
                "not possible to get arguments for initial condition operator for non "
                "time_space"
            )
        elif self.type_space == "phase_space":
            raise NotImplementedError("phase_space")
        else:
            assert isinstance(data, dict)
            args = [data["ic"][0].labels, data["ic"][0].x, data["ic"][1].x]
        return args

    def get_preconditioning_matrix_ic(self, data: TYPE_DATA, **kwargs) -> torch.Tensor:
        """Get the preconditioning matrix using the initial condition operator.

        Args:
            data: Input data, either as a tuple or a dictionary.
            **kwargs: Additional keyword arguments.

        Returns:
            The preconditioning matrix.
        """
        args = self.get_args_for_operator_ic(data)

        return self.compute_preconditioning_matrix_ic(*args, **kwargs)

    def vectorize_along_physical_variables(
        self, dict_of_funcs: TYPE_DICT_OF_FUNC_ARGS
    ) -> TYPE_DICT_OF_VMAPS:
        """Vectorize functions along physical variables based on the type of space.

        Args:
            dict_of_funcs: A dictionary of functions to be vectorized.

        Returns:
            A dictionary of vectorized functions.

        Raises:
            NotImplementedError: If the type_space is 'phase_space'.
        """
        scheme: tuple[int | None, ...] = tuple()
        if self.type_space == "space":
            scheme = (0, 0, None)
        elif self.type_space == "phase_space":
            raise NotImplementedError("phase_space")
        else:
            scheme = (0, 0, 0, None)

        return vectorize_dict_of_func(scheme, dict_of_funcs)

    def vectorize_along_physical_variables_bc(
        self, dict_of_funcs: TYPE_DICT_OF_FUNC_ARGS
    ) -> TYPE_DICT_OF_VMAPS:
        """Vectorize functions along physical variables for boundary conditions.

        Args:
            dict_of_funcs: A dictionary of functions to be vectorized.

        Returns:
            A dictionary of vectorized functions.

        Raises:
            NotImplementedError: If the type_space is 'phase_space'.
        """
        scheme: tuple[int | None, ...] = tuple()
        if self.type_space == "space":
            scheme = (0, 0, 0, None)
        elif self.type_space == "phase_space":
            raise NotImplementedError("phase_space")
        else:
            scheme = (0, 0, 0, 0, None)

        return vectorize_dict_of_func(scheme, dict_of_funcs)

    def vectorize_along_physical_variables_ic(
        self, dict_of_funcs: TYPE_DICT_OF_FUNC_ARGS
    ) -> TYPE_DICT_OF_VMAPS:
        """Vectorize functions along physical variables for initial conditions.

        Args:
            dict_of_funcs: A dictionary of functions to be vectorized.

        Returns:
            A dictionary of vectorized functions.

        Raises:
            NotImplementedError: If the type_space is 'phase_space'.
            ValueError: If the type_space is 'space'.
        """
        scheme: tuple[int | None, ...] = tuple()
        if self.type_space == "space":
            raise ValueError(
                "not possible to vectorize initial condition for non time_space"
            )
            # return torch.func.vmap(func, (0, 0, None))
        elif self.type_space == "phase_space":
            raise NotImplementedError("phase_space")
        else:
            scheme = (0, 0, None)

        return vectorize_dict_of_func(scheme, dict_of_funcs)

    def get_formatted_current_theta(self) -> TYPE_THETA:
        """Get the current parameters of the approximation space.

        Returns:
            A dictionary of the current parameters of the approximation space.
        """
        return {k: v for k, v in self.named_parameters()}

    # functional evaluation of the network with pre_processing
    # assume theta (parameters of the network) is the last element of args
    def eval_network(self, *args: TYPE_ARGS) -> torch.Tensor:
        """Evaluate the network with pre-processing.

        Args:
            *args: Arguments to be passed to the network, with the last argument being
                the parameters of the network.

        Returns:
            The output of the network after applying pre-processing.
        """
        physical_vars = self.pre_processing(*(args[:-1]))
        return torch.func.functional_call(self.space, args[-1], physical_vars)

    # functional evaluation of the network with pre and post processing
    # assume theta (parameters of the network) is the last element of args
    def eval_func(self, *args: TYPE_ARGS) -> torch.Tensor:
        """Evaluate the network with pre-processing and post-processing.

        Args:
            *args: Arguments to be passed to the network, with the last argument being
                the parameters of the network.

        Returns:
            The output of the network after applying pre-processing and post-processing.
        """
        return self.post_processing(self.eval_network, *args)

"""Deep Ritz method for solving elliptic PDEs using deep learning."""

from typing import Any

import torch
import torch.nn as nn

from scimba_torch.numerical_solvers.collocation_projector import (
    CollocationProjector,
)
from scimba_torch.numerical_solvers.preconditioner_deep_ritz import (
    # AnagramPreconditioner,
    EnergyNaturalGradientPreconditioner,
)
from scimba_torch.optimizers.losses import GenericLosses, MassLoss
from scimba_torch.optimizers.optimizers_data import OptimizerData
from scimba_torch.physical_models.elliptic_pde.abstract_elliptic_pde import (
    RitzFormEllipticPDE,
)
from scimba_torch.physical_models.elliptic_pde.laplacians import (
    Laplacian2DDirichletRitzForm,
)
from scimba_torch.physical_models.elliptic_pde.linear_order_2 import (
    DivAGradUPDE,
)
from scimba_torch.utils.scimba_tensors import MultiLabelTensor


class DeepRitzElliptic(CollocationProjector):
    """A deep learning-based solver for elliptic PDEs using the Ritz method.

    The class inherits from AbstractNonlinearProjector and provides methods for
    assembling the PDE system and computing the metric matrix.

    Args:
        pde: The elliptic PDE to be solved, represented as an instance of
            RitzForm_EllipticPDE.
        bc_type: The type of boundary condition to be applied ("strong" or "weak").
            (default: "strong")
        **kwargs: Additional keyword arguments for losses and optimizers.
    """

    def __init__(
        self,
        pde: RitzFormEllipticPDE | DivAGradUPDE,
        bc_type: str = "strong",
        **kwargs,
    ):
        super().__init__(pde.space, pde.linearform, **kwargs)
        self.pde = pde
        self.bc_type = bc_type

        bc_weight = kwargs.get("bc_weight", 10.0)

        default_list_losses = [("energy", MassLoss(), 1.0)]
        if self.bc_type == "weak":
            default_list_losses += [("bc", torch.nn.MSELoss(), bc_weight)]
        default_losses = GenericLosses(default_list_losses)
        self.losses = kwargs.get("losses", default_losses)

        opt_1 = {
            "name": "adam",
            "optimizer_args": {"lr": 1e-3, "betas": (0.9, 0.999)},
        }
        default_opt = OptimizerData(opt_1)
        self.optimizer = kwargs.get("optimizers", default_opt)

        # self.xmu = None

    def get_dof(self, flag_scope: str = "all", flag_format: str = "list"):
        """Gets the degrees of freedom for the solver, including those from the PDE.

        Args:
            flag_scope: Scope flag for getting degrees of freedom. (default: "all")
            flag_format: Format flag for the degrees of freedom ("list" or "tensor").
                (default: "list")

        Returns:
            The degrees of freedom tensor or list.
        """
        iterator_params = self.pde.space.get_dof(flag_scope, flag_format)
        if isinstance(self.pde, nn.Module):
            if flag_format == "list":
                iterator_params2 = list(self.pde.parameters())
                iterator_params = iterator_params + iterator_params2
            if flag_format == "tensor":
                iterator_params2 = torch.nn.utils.parameters_to_vector(
                    self.pde.parameters()
                )
                iterator_params = torch.cat((iterator_params, iterator_params2))

        return iterator_params

    def evaluate(self, x: torch.Tensor, mu: torch.Tensor) -> MultiLabelTensor:
        """Evaluates the solution at given spatial and parameter points.

        Args:
            x: Spatial points where the solution is evaluated.
            mu: Parameter points where the solution is evaluated.

        Returns:
            The evaluated solution as a MultiLabelTensor.
        """
        return self.space.evaluate(x, mu)

    def metric_matrix(self, **kwargs: Any) -> torch.Tensor:
        """Placeholder method for computing the metric matrix.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            torch.Tensor: The metric matrix.

        Raises:
            NotImplementedError: This method must be implemented in subclasses.
        """
        raise NotImplementedError(
            "You must implement the metric_matrix method for the DeepRitzElliptic "
            "class."
        )

    def sample_all_vars(self, **kwargs: Any) -> tuple:
        """Samples all necessary variables for assembling the PDE system.

        Args:
            **kwargs: Additional keyword arguments including:

                - n_collocation: Number of collocation points for the PDE.
                  Defaults to 1000.
                - n_bc_collocation: Number of collocation points for the boundary
                  conditions. Defaults to 1000.

        Returns:
            A tuple containing sampled spatial points, parameter points,
            and, if applicable, boundary points and normals.
        """
        n_collocation = kwargs.get("n_collocation", 1000)
        x, mu = self.space.integrator.sample(n_collocation)
        xmu = (x, mu)
        if self.bc_type == "weak":
            n_bc_collocation = kwargs.get("n_bc_collocation", 1000)
            xnbc, mubc = self.space.integrator.bc_sample(n_bc_collocation, index_bc=0)
            xbc, nbc = xnbc[0], xnbc[1]
            xmu = xmu + (xbc, nbc, mubc)
        return xmu

    def assembly_post_sampling(self, xmu: tuple, **kwargs) -> tuple:
        """Assembles the PDE system after sampling all necessary variables.

        Args:
            xmu: A tuple containing sampled spatial points, parameter points,
                and, if applicable, boundary points and normals.
            **kwargs: Additional keyword arguments.

        Returns:
            A tuple containing the assembled system of equations (Lo, f).
        """
        x, mu = xmu[0], xmu[1]
        w = self.space.evaluate(x, mu)
        Lo = self.pde.quadraticform(w, x, mu)  ## L is a tuple
        f = self.pde.linearform(w, x, mu)  ## f is a tuple
        if not isinstance(Lo, tuple):
            assert Lo.shape[1] == 1, (
                "you must reward a tuple of residual (batch,1) or one residual tensor "
                "(batch,1)"
            )
            Lo = (Lo,)
        if not isinstance(f, tuple):
            assert f.shape[1] == 1, (
                "you must reward a tuple of residual (batch,1) or one residual tensor "
                "(batch,1)"
            )
            f = (f,)

        if self.bc_type == "weak":
            xbc, nbc, mubc = xmu[2], xmu[3], xmu[4]
            w = self.space.evaluate(xbc, mubc)
            Lbc = self.pde.bc_operator(w, xbc, nbc, mubc)  ## Lbc is a tuple
            fbc = self.pde.bc_rhs(w, xbc, nbc, mubc)  ## Lbc is a tuple

            if not isinstance(Lbc, tuple):
                assert Lbc.shape[1] == 1, (
                    "you must reward a tuple of residual (batch,1) or one residual "
                    "tensor (batch,1)"
                )
                Lbc = (Lbc,)
            if not isinstance(fbc, tuple):
                assert fbc.shape[1] == 1, (
                    "you must reward a tuple of residual (batch,1) or one residual "
                    "tensor (batch,1)"
                )
                fbc = (fbc,)

            Lo = Lo + Lbc
            f = f + fbc
        return Lo, f

    def assembly(self, **kwargs: Any) -> tuple:
        """Assembles the system of equations for the PDE.

        (and weak boundary conditions if needed).

        Args:
            **kwargs: Additional keyword arguments including:

                - n_collocation (int): Number of collocation points for the PDE.
                  Defaults to 1000.
                - n_bc_collocation (int): Number of collocation points for the boundary
                  conditions. Defaults to 1000.

        Returns:
            A tuple containing the assembled system of equations (Lo, f).
        """
        xmu = self.sample_all_vars(**kwargs)
        return self.assembly_post_sampling(xmu, **kwargs)


class NaturalGradientDeepRitzElliptic(DeepRitzElliptic):
    """A Deep Ritz solver for elliptic PDEs using natural gradient descent.

    Args:
        pde: The elliptic PDE to be solved, represented as an instance of
            RitzForm_EllipticPDE.
        bc_type: The type of boundary condition to be applied ("strong" or "weak").
            (default: "strong")
        **kwargs: Additional keyword arguments for losses, optimizers, and
            preconditioners.
    """

    def __init__(
        self,
        pde: Laplacian2DDirichletRitzForm | DivAGradUPDE,
        bc_type: str = "strong",
        **kwargs,
    ):
        super().__init__(pde, bc_type, **kwargs)

        self.default_lr: float = kwargs.get("default_lr", 1e-2)
        opt_1 = {
            "name": "sgd",
            "optimizer_args": {"lr": self.default_lr},
        }
        self.optimizer = OptimizerData(opt_1)

        self.bool_linesearch = True
        self.type_linesearch = kwargs.get("type_linesearch", "armijo")
        # self.type_linesearch = kwargs.get("type_linesearch", "logarithmic_grid")
        self.data_linesearch = kwargs.get("data_linesearch", {})
        self.data_linesearch.setdefault("M", 10)
        self.data_linesearch.setdefault("interval", [0.0, 2.0])
        self.data_linesearch.setdefault("log_basis", 2.0)
        self.data_linesearch.setdefault("n_step_max", 10)
        self.data_linesearch.setdefault(
            "alpha",
            0.01,
        )
        self.data_linesearch.setdefault(
            "beta",
            0.5,
        )

        self.bool_preconditioner = True
        self.preconditioner = EnergyNaturalGradientPreconditioner(
            pde.space,
            pde,
            # is_operator_linear=False,
            has_bc=(bc_type == "weak"),
            # in_lhs_name = "functional_quadraticform",
            **kwargs,
        )
        self.nb_epoch_preconditioner_computing = 1
        self.projection_data = {"nonlinear": True, "linear": False, "nb_step": 1}

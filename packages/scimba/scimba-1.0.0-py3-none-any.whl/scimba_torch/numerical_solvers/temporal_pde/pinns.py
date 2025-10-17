"""Define the TemporalPinns class, which is a subclass of CollocationProjector.

It is designed to solve time-dependent partial differential equations (PDEs)
using physics-informed neural networks (PINNs).
"""

from typing import Any

import torch
import torch.nn as nn

from scimba_torch.numerical_solvers.collocation_projector import (
    CollocationProjector,
)
from scimba_torch.numerical_solvers.preconditioner_pinns import (
    AnagramPreconditioner,
    EnergyNaturalGradientPreconditioner,
)
from scimba_torch.optimizers.losses import GenericLosses
from scimba_torch.optimizers.optimizers_data import OptimizerData
from scimba_torch.physical_models.temporal_pde.abstract_temporal_pde import TemporalPDE
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor


class TemporalPinns(CollocationProjector):
    """A class to solve time-dependent PDEs using Physics-Informed Neural Networks.

    Args:
        pde: The time-dependent PDE to be solved
        bc_type: The type of boundary condition to be applied ("strong" or "weak").
            (default: "strong")
        ic_type: The type of initial condition to be applied ("strong" or "weak").
            (default: "strong")
        **kwargs: Additional keyword arguments for customization.
    """

    def __init__(
        self,
        pde: TemporalPDE,
        bc_type: str = "strong",
        ic_type: str = "strong",
        **kwargs,
    ):
        super().__init__(pde.space, pde.rhs, **kwargs)
        self.pde = pde
        self.bc_type = bc_type
        self.ic_type = ic_type
        self.space = pde.space

        self.one_loss_by_equation = kwargs.get("one_loss_by_equation", False)

        self.bc_weight = kwargs.get("bc_weight", 10.0)
        self.ic_weight = kwargs.get("ic_weight", 10.0)

        if not self.one_loss_by_equation:
            default_list_losses = [("residual", torch.nn.MSELoss(), 1.0)]
        else:
            default_list_losses = [
                ("eq" + str(i), torch.nn.MSELoss(), 1.0)
                for i in range(0, self.pde.residual_size)
            ]

        if self.bc_type == "weak":
            if not self.one_loss_by_equation:
                default_list_losses += [("bc", torch.nn.MSELoss(), self.bc_weight)]
            else:
                default_list_losses += [
                    ("eq bc " + str(i), torch.nn.MSELoss(), self.bc_weight)
                    for i in range(0, self.pde.bc_residual_size)
                ]

        if self.ic_type == "weak":
            if not self.one_loss_by_equation:
                default_list_losses += [("ic", torch.nn.MSELoss(), self.ic_weight)]
            else:
                default_list_losses += [
                    ("eq ic " + str(i), torch.nn.MSELoss(), self.ic_weight)
                    for i in range(0, self.pde.ic_residual_size)
                ]

        default_losses = GenericLosses(default_list_losses)

        self.losses = kwargs.get("losses", default_losses)

        opt_1 = {
            "name": "adam",
            "optimizer_args": {"lr": 1e-3, "betas": (0.9, 0.999)},
        }
        default_opt = OptimizerData(opt_1)
        self.optimizer = kwargs.get("optimizers", default_opt)

    def get_dof(
        self, flag_scope: str = "all", flag_format: str = "list"
    ) -> torch.Tensor | list:
        """Gets the parameters of the approximation space in use.

        Args:
            flag_scope: Scope of the degrees of freedom to retrieve.
            flag_format: Format of the output, either "list" or "tensor".

        Returns:
            Degrees of freedom in the specified format.
        """
        iterator_params = self.pde.space.get_dof(flag_scope, flag_format)

        if isinstance(self.pde, nn.Module):
            dict_param_withoutspace = {
                name: param
                for name, param in self.pde.named_parameters()
                if not name.startswith("space.")
            }
            if flag_format == "list":
                iterator_params = iterator_params + list(
                    dict_param_withoutspace.values()
                )
            if flag_format == "tensor":
                iterator_params2 = torch.nn.utils.parameters_to_vector(
                    list(dict_param_withoutspace.values())
                )
                iterator_params = torch.cat((iterator_params, iterator_params2))

        return iterator_params

    def evaluate(
        self, t: torch.Tensor, x: torch.Tensor, mu: torch.Tensor
    ) -> MultiLabelTensor:
        """Evaluates the approximation at given points.

        Args:
            t: Input tensor for time coordinates.
            x: Input tensor for spatial coordinates.
            mu: Input tensor for parameters.

        Returns:
            The evaluated solution.
        """
        return self.space.evaluate(t, x, mu)

    def sample_all_vars(self, **kwargs: Any) -> dict[str, tuple[LabelTensor, ...]]:
        """Samples collocation points for the PDE, BCs, and initial conditions.

        Args:
            **kwargs: Additional keyword arguments for sampling.

        Returns:
            Dictionary of sampled tensors.
        """
        # initialize dictionary of sampled points
        txmu = {}

        # sample inner points
        n_collocation = kwargs.get("n_collocation", 1000)
        t, x, mu = self.space.integrator.sample(n_collocation)
        txmu["inner"] = (t, x, mu)

        # sample boundary points, if weak BC
        if self.bc_type == "weak":
            n_bc_collocation = kwargs.get("n_bc_collocation", 1000)
            tbc, xnbc, mubc = self.space.integrator.bc_sample(
                n_bc_collocation, index_bc=1
            )
            xbc, nbc = xnbc[0], xnbc[1]
            txmu["bc"] = (tbc, xbc, nbc, mubc)

        # sample initial points, if weak IC
        if self.ic_type == "weak":
            n_ic_collocation = kwargs.get("n_ic_collocation", 1000)
            _, xic, muic = self.space.integrator.sample(n_ic_collocation)
            txmu["ic"] = (xic, muic)

        # return all sampled points
        return txmu

    def assembly_post_sampling(self, txmu: dict, **kwargs) -> tuple:
        """Assembles the system of equations post-sampling.

        Args:
            txmu: dictionary of sampled tensors.
            **kwargs: Additional keyword arguments.

        Returns:
            Tuple containing the assembled operator and right-hand side.
        """
        # inner points: pde residual and rhs
        t, x, mu = txmu["inner"]
        w = self.space.evaluate(t, x, mu)
        L_space = self.pde.space_operator(w, t, x, mu)  # tuple
        L_time = self.pde.time_operator(w, t, x, mu)  # tuple

        if isinstance(L_space, tuple):
            assert isinstance(L_time, tuple) and len(L_space) == len(L_time), (
                "space operator and time operator must retrieve tuple of tensors of "
                "the same length"
            )
            L = tuple(L_s + L_t for L_s, L_t in zip(L_space, L_time))
        else:
            assert (
                isinstance(L_space, torch.Tensor)
                and isinstance(L_time, torch.Tensor)
                and (L_space.shape == L_time.shape)
            ), (
                "space operator and time operator must retrieve tensors of the same "
                "shape"
            )
            L = L_space + L_time

        f = self.pde.rhs(w, t, x, mu)  # tuple

        Lo = self.make_tuple(L)
        f = self.make_tuple(f)

        if self.bc_type == "weak":
            # bc points: pde bc residual and rhs
            tbc, xbc, nbc, mubc = txmu["bc"]
            w = self.space.evaluate(tbc, xbc, mubc)
            Lbc = self.pde.bc_operator(w, tbc, xbc, nbc, mubc)  # tuple
            fbc = self.pde.bc_rhs(w, tbc, xbc, nbc, mubc)  # tuple

            Lbc = self.make_tuple(Lbc)
            fbc = self.make_tuple(fbc)

            Lo = Lo + Lbc
            f = f + fbc

        if self.ic_type == "weak":
            # ic points: initial condition
            xic, muic = txmu["ic"]
            n_ic_collocation = xic.shape[0]
            tic = LabelTensor(torch.zeros((n_ic_collocation, 1)))
            w = self.space.evaluate(tic, xic, muic)
            fic = self.pde.init(xic, muic)  # tuple

            Lic = self.make_tuple(w.w)
            fic = self.make_tuple(fic)

            Lo = Lo + Lic
            f = f + fic

        return Lo, f

    def assembly(self, **kwargs: Any) -> tuple:
        """Assembles the system of equations for the PDE.

        Assembles also weak boundary conditions if needed.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            Tuple containing the assembled operator and right-hand side.
        """
        xmu = self.sample_all_vars(**kwargs)
        return self.assembly_post_sampling(xmu, **kwargs)


class NaturalGradientTemporalPinns(TemporalPinns):
    """A class extending TemporalPinns with natural gradient preconditioning.

    Args:
        pde: The time-dependent PDE to be solved.
        bc_type: Type of boundary condition ("strong" or "weak").
            Defaults to "strong".
        ic_type: Type of initial condition ("strong" or "weak").
            Defaults to "strong".
        **kwargs: Additional keyword arguments for customization.
    """

    def __init__(
        self,
        pde: TemporalPDE,
        bc_type: str = "strong",
        ic_type: str = "strong",
        **kwargs,
    ):
        super().__init__(pde, bc_type, ic_type, **kwargs)

        self.default_lr: float = kwargs.get("default_lr", 1e-2)
        opt_1 = {
            "name": "sgd",
            "optimizer_args": {"lr": self.default_lr},
        }
        self.optimizer = OptimizerData(opt_1)

        self.bool_linesearch = True
        self.type_linesearch = kwargs.get("type_linesearch", "armijo")
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
            is_operator_linear=pde.linear,
            has_bc=(bc_type == "weak"),
            has_ic=(ic_type == "weak"),
            **kwargs,
        )
        self.nb_epoch_preconditioner_computing = 1
        self.projection_data = {"nonlinear": True, "linear": False, "nb_step": 1}


class AnagramTemporalPinns(TemporalPinns):
    """A class extending TemporalPinns with Anagram preconditioning.

    Args:
        pde: The time-dependent PDE to be solved.
        bc_type: Type of boundary condition ("strong" or "weak").
            Defaults to "strong".
        ic_type: Type of initial condition ("strong" or "weak").
            Defaults to "strong".
        **kwargs: Additional keyword arguments for customization.
    """

    def __init__(
        self,
        pde: TemporalPDE,
        bc_type: str = "strong",
        ic_type: str = "strong",
        **kwargs,
    ):
        super().__init__(pde, bc_type, ic_type, **kwargs)

        self.default_lr: float = kwargs.get("default_lr", 1e-2)
        opt_1 = {
            "name": "sgd",
            "optimizer_args": {"lr": self.default_lr},
        }
        self.optimizer = OptimizerData(opt_1)

        self.bool_linesearch = True
        self.type_linesearch = kwargs.get("type_linesearch", "armijo")
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
        self.preconditioner = AnagramPreconditioner(
            pde.space,
            pde,
            has_bc=(bc_type == "weak"),
            has_ic=(ic_type == "weak"),
            **kwargs,
        )
        self.nb_epoch_preconditioner_computing = 1
        self.projection_data = {"nonlinear": True, "linear": False, "nb_step": 1}

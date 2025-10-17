"""This module defines the PinnsElliptic class.

PinnsElliptic is a subclass of NonlinearGalerkinProjector designed to solve elliptic
partial differential equations (PDEs) using physics-informed neural networks (PINNs).
"""

from typing import TYPE_CHECKING, Any, cast

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
from scimba_torch.physical_models.elliptic_pde.abstract_elliptic_pde import (
    StrongFormEllipticPDE,
)
from scimba_torch.physical_models.elliptic_pde.linear_order_2 import (
    LinearOrder2PDE,
)
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor


class PinnsElliptic(CollocationProjector):
    """A class to solve elliptic PDEs using Physics-Informed Neural Networks (PINNs).

    Args:
        pde: The elliptic PDE to be solved, represented as an instance of
            StrongFormEllipticPDE or LinearOrder2PDE.
        bc_type: The type of boundary condition to be applied ("strong" or "weak").
            (default: "strong")
        **kwargs: Additional keyword arguments for losses and optimizers.
    """

    def __init__(
        self,
        pde: StrongFormEllipticPDE | LinearOrder2PDE,
        bc_type: str = "strong",
        **kwargs,
    ):
        super().__init__(pde.space, pde.rhs, **kwargs)
        self.pde = pde
        self.bc_type = bc_type
        self.space = pde.space

        self.one_loss_by_equation = kwargs.get("one_loss_by_equation", False)

        bc_weight = kwargs.get("bc_weight", 10.0)

        if not self.one_loss_by_equation:
            default_list_losses = [("residual", torch.nn.MSELoss(), 1.0)]
        else:
            default_list_losses = [
                ("eq " + str(i), torch.nn.MSELoss(), 1.0)
                for i in range(0, self.pde.residual_size)
            ]

        if self.bc_type == "weak":
            if not self.one_loss_by_equation:
                default_list_losses += [("bc", torch.nn.MSELoss(), bc_weight)]
            else:
                default_list_losses += [
                    ("eq bc " + str(i), torch.nn.MSELoss(), bc_weight)
                    for i in range(0, self.pde.bc_residual_size)
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
            torch.Tensor | list: Degrees of freedom in the specified format.
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
                iterator_params = torch.cat(
                    (cast(torch.Tensor, iterator_params), iterator_params2)
                )

        return iterator_params

    def evaluate(self, x: LabelTensor, mu: LabelTensor) -> MultiLabelTensor:
        """Evaluates the approximation at given points.

        Args:
            x: Input tensor for spatial coordinates.
            mu: Input tensor for parameters.

        Returns:
            The evaluated solution.
        """
        return self.space.evaluate(x, mu)

    def sample_all_vars(self, **kwargs: Any) -> tuple[LabelTensor, ...]:
        """Samples collocation points for the PDE and boundary conditions.

        Args:
            **kwargs: Additional keyword arguments for sampling.

        Returns:
            tuple[LabelTensor, ...]: tuple of sampled tensors.
        """
        n_collocation = kwargs.get("n_collocation", 1000)
        x, mu = self.space.integrator.sample(n_collocation)
        xmu: tuple[LabelTensor, ...] = (x, mu)
        if self.bc_type == "weak":
            n_bc_collocation = kwargs.get("n_bc_collocation", 1000)
            xnbc, mubc = self.space.integrator.bc_sample(n_bc_collocation, index_bc=0)
            xbc, nbc = xnbc[0], xnbc[1]
            if TYPE_CHECKING:
                xbc = cast(LabelTensor, xbc)
                nbc = cast(LabelTensor, nbc)
                mubc = cast(LabelTensor, mubc)
            xmu = xmu + (xbc, nbc, mubc)
        return xmu

    def assembly_post_sampling(
        self, data: tuple[LabelTensor, ...], **kwargs
    ) -> tuple[tuple[torch.Tensor, ...], tuple[torch.Tensor, ...]]:
        """Assembles the system of equations post-sampling.

        Args:
            data: tuple of sampled tensors.
            **kwargs: Additional keyword arguments.

        Returns:
            tuple: tuple containing the assembled operator and right-hand side.
        """
        x, mu = data[0], data[1]
        w = self.space.evaluate(x, mu)
        Lot = self.pde.operator(w, x, mu)
        Ft = self.pde.rhs(w, x, mu)

        ## Lo is a tuple of tensors or of dict in case of different labels
        ## F  is a tuple of tensors or of dict in case of different labels

        errormessage = (
            "you must reward one residual tensor (batch,1) or a dict of "
            "tensors (batch,1) or a tuple of those"
        )

        Lores: tuple[torch.Tensor, ...] = tuple()
        Fres: tuple[torch.Tensor, ...] = tuple()

        Lo = (Lot,) if not isinstance(Lot, tuple) else Lot
        F = (Ft,) if not isinstance(Ft, tuple) else Ft

        assert len(Lo) == len(F), "lhs and rhs must have the same number of components"
        for lo, f in zip(Lo, F):
            if isinstance(lo, dict):
                assert isinstance(f, dict)
                for key in lo:
                    assert key in f
                    assert lo[key].shape[1] == 1, errormessage
                    assert f[key].shape[1] == 1, errormessage
                    Lores = Lores + (lo[key],)
                    Fres = Fres + (f[key],)
            else:  # lo, f, are tensors
                assert isinstance(lo, torch.Tensor) and isinstance(f, torch.Tensor)
                assert lo.shape[1] == 1, errormessage
                assert f.shape[1] == 1, errormessage
                Lores = Lores + (lo,)
                Fres = Fres + (f,)

        if self.bc_type == "weak":
            xbc, nbc, mubc = data[2], data[3], data[4]
            w = self.space.evaluate(xbc, mubc)
            Lbct = self.pde.bc_operator(w, xbc, nbc, mubc)  ## Lbc is a tuple
            Fbct = self.pde.bc_rhs(w, xbc, nbc, mubc)  ## Lbc is a tuple

            Lbc = (Lbct,) if not isinstance(Lbct, tuple) else Lbct
            Fbc = (Fbct,) if not isinstance(Fbct, tuple) else Fbct

            assert len(Lbc) == len(Fbc), (
                "lhs and rhs must have the same number of components"
            )
            for lo, f in zip(Lbc, Fbc):
                if isinstance(lo, dict):
                    assert isinstance(f, dict)
                    for key in lo:
                        assert key in f
                        assert lo[key].shape[1] == 1, errormessage
                        assert f[key].shape[1] == 1, errormessage
                        Lores = Lores + (lo[key],)
                        Fres = Fres + (f[key],)
                else:  # lo, f, are tensors
                    assert isinstance(lo, torch.Tensor) and isinstance(f, torch.Tensor)
                    assert lo.shape[1] == 1, errormessage
                    assert f.shape[1] == 1, errormessage
                    Lores = Lores + (lo,)
                    Fres = Fres + (f,)

        return Lores, Fres

    def assembly(self, **kwargs: Any) -> tuple[torch.Tensor, ...]:
        """Assembles the system of equations for the PDE.

        Assembles also weak boundary conditions if needed.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            tuple containing the assembled operator and right-hand side.
        """
        xmu = self.sample_all_vars(**kwargs)
        return self.assembly_post_sampling(xmu, **kwargs)


class NaturalGradientPinnsElliptic(PinnsElliptic):
    """A class extending PinnsElliptic with natural gradient preconditioning.

    Args:
        pde: The elliptic PDE to be solved, represented as an instance of
            StrongFormEllipticPDE or LinearOrder2PDE.
        bc_type: The type of boundary condition to be applied ("strong" or "weak").
            (default: "strong")
        **kwargs: Additional keyword arguments for customization.
    """

    def __init__(
        self,
        pde: StrongFormEllipticPDE | LinearOrder2PDE,
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
        self.data_linesearch = kwargs.get("data_linesearch", {})
        self.data_linesearch.setdefault("M", 10)
        self.data_linesearch.setdefault("interval", [0.0, 2.0])
        self.data_linesearch.setdefault("log_basis", 2.0)
        self.data_linesearch.setdefault("n_step_max", 10)
        self.data_linesearch.setdefault("alpha", 0.01)
        self.data_linesearch.setdefault("beta", 0.5)

        assert hasattr(pde, "linear")

        self.bool_preconditioner = True
        self.preconditioner = EnergyNaturalGradientPreconditioner(
            pde.space,
            pde,
            is_operator_linear=pde.linear,
            has_bc=(bc_type == "weak"),
            **kwargs,
        )
        self.nb_epoch_preconditioner_computing = 1
        self.projection_data = {"nonlinear": True, "linear": False, "nb_step": 1}


class AnagramPinnsElliptic(PinnsElliptic):
    """A class extending PinnsElliptic with Anagram preconditioning.

    Args:
        pde: The elliptic PDE to be solved, represented as an instance of
            StrongFormEllipticPDE or LinearOrder2PDE.
        bc_type: The type of boundary condition to be applied ("strong" or "weak").
            (default: "strong")
        **kwargs: Additional keyword arguments for customization.
    """

    def __init__(
        self,
        pde: StrongFormEllipticPDE | LinearOrder2PDE,
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
        self.data_linesearch = kwargs.get("data_linesearch", {})
        self.data_linesearch.setdefault("M", 10)
        self.data_linesearch.setdefault("interval", [0.0, 2.0])
        self.data_linesearch.setdefault("log_basis", 2.0)
        self.data_linesearch.setdefault("n_step_max", 10)
        self.data_linesearch.setdefault("alpha", 0.01)
        self.data_linesearch.setdefault("beta", 0.5)

        self.bool_preconditioner = True
        self.preconditioner = AnagramPreconditioner(
            pde.space, pde, has_bc=(bc_type == "weak"), **kwargs
        )
        self.nb_epoch_preconditioner_computing = 1
        self.projection_data = {"nonlinear": True, "linear": False, "nb_step": 1}

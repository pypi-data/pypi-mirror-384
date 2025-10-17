"""Collocation-based projectors for approximation spaces."""

from typing import TYPE_CHECKING, Any, Callable

import torch

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.numerical_solvers.abstract_projector import (
    RHS_FUNC_TYPE,
    AbstractNonlinearProjector,
)
from scimba_torch.numerical_solvers.preconditioner_projector import (
    AnagramPreconditionerProjector,
    EnergyNaturalGradientPreconditionerProjector,
)
from scimba_torch.optimizers.optimizers_data import OptimizerData
from scimba_torch.utils.scimba_tensors import LabelTensor


class CollocationProjector(AbstractNonlinearProjector):
    """A collocation-based nonlinear projection method.

    This subclass implements methods to assemble the input and output tensors
    for a specific nonlinear projection problem using collocation points. It computes
    the approximation of a nonlinear problem by sampling collocation points and
    evaluating the corresponding function values.

    Args:
        space: The approximation space where the projection will take place.
        rhs: The function representing the right-hand side of the problem.
        **kwargs: Additional parameters for the projection, including collocation
            points and losses.
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        rhs: RHS_FUNC_TYPE | None = None,
        **kwargs,
    ):
        self.rhs: RHS_FUNC_TYPE | None = rhs
        super().__init__(space, rhs, **kwargs)
        # Rémi why not having rhs here as self.rhs instead of self.space.rhs???

    def set_rhs(self, rhs: RHS_FUNC_TYPE):
        """Sets the right-hand side function for the projection.

        Args:
            rhs: The function representing the right-hand side of the problem.
        """
        self.rhs = rhs

    def get_dof(self, flag_scope: str = "all", flag_format: str = "list"):
        """Retrieves the degrees of freedom (DoF) of the approximation space.

        Args:
            flag_scope: Specifies the scope of the parameters to return.
            flag_format: The format for returning the parameters.

        Returns:
            The degrees of freedom in the specified format.
        """
        return self.space.get_dof(flag_scope, flag_format)

    def metric_matrix(
        self,
        x: LabelTensor,
        mu: LabelTensor,
        t: LabelTensor | None = None,
        v: LabelTensor | None = None,
        **kwargs,
    ) -> torch.Tensor:
        """Computes the metric matrix for the given tensors.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.
            t: Input tensor from the time domain (optional).
            v: Input tensor from the velocity domain (optional).
            **kwargs: Additional arguments.

        Returns:
            The computed metric matrix.

        Raises:
            NotImplementedError: If the metric matrix is not defined for the current
                space type.
        """
        if not (
            self.space.type_space == "space" or self.space.type_space == "phase_space"
        ):
            raise NotImplementedError(
                "The metric matrix is not yet defined for time-dependent problems."
            )
        # assert (
        #     self.space.type_space == "space" or self.space.type_space == "phase_space"
        # ), "The metric matrix is not yet defined for time-dependent problems."

        N = x.shape[0]
        if self.space.type_space == "space":
            jacobian = self.space.jacobian(x, mu)
        elif self.space.type_space == "time_space":
            if TYPE_CHECKING:  # pragma: no cover
                assert isinstance(t, torch.Tensor)
            jacobian = self.space.jacobian(t, x, mu)
        else:
            if TYPE_CHECKING:  # pragma: no cover
                assert isinstance(v, torch.Tensor)
            jacobian = self.space.jacobian(x, v, mu)

        return torch.einsum("ijk,ilk->jl", jacobian, jacobian) / N

    def sample_all_vars(self, **kwargs: Any) -> tuple[LabelTensor, ...]:
        """Samples values in the domains of the arguments of the function to project.

        Args:
            **kwargs: Additional arguments for sampling.

        Returns:
            A tuple containing the sampled tensors.
        """
        n_collocation = kwargs.get("n_collocation", 1000)
        return tuple(self.space.integrator.sample(n_collocation))

    def assembly_post_sampling(
        self, data: tuple[LabelTensor, ...], **kwargs
    ) -> tuple[tuple[torch.Tensor, ...], tuple[torch.Tensor, ...]]:
        """Assemble the I/O tensors for the nonlinear projection problem after sampling.

        Args:
            data: The sampled data.
            **kwargs: Additional arguments for assembly, including flag_scope.

        Returns:
            A tuple of tuples containing the assembled left and right-hand sides.
        """
        flag_scope = kwargs.get("flag_scope", "all")
        with_last_layer = True
        if flag_scope == "except_last_layer":
            with_last_layer = False

        # print("with_last_layer: ", with_last_layer)

        if self.space.type_space == "space":
            args = [data[0], data[1]]
        elif self.space.type_space == "phase_space":
            args = [data[0], data[1], data[2]]
        else:  # time_space
            args = [data[0], data[1], data[2]]

        u = self.space.evaluate(
            *args, with_last_layer=with_last_layer
        )  # u is a multilabelTensor
        assert self.rhs is not None
        f = self.rhs(*args)  # f is a Tensor

        left = (u.w,) if (not with_last_layer) else self.make_tuple(u.get_components())
        right = self.make_tuple(f)

        return left, right

    def assembly(
        self, **kwargs: Any
    ) -> tuple[tuple[torch.Tensor, ...], tuple[torch.Tensor, ...]]:
        """Assembles the system of equations for the projection problem.

        Args:
            **kwargs: Additional arguments for assembly, including the number of
                collocation points.

        Returns:
            A tuple of tuples containing the assembled left and right-hand sides.
        """
        data = self.sample_all_vars(**kwargs)
        return self.assembly_post_sampling(data, **kwargs)


class NaturalGradientProjector(CollocationProjector):
    """Subclass of CollocationProjector using natural gradient optimization.

    This class extends the CollocationProjector to use natural gradient optimization
    for solving the projection problem.

    Args:
        space: The approximation space where the projection will take place.
        rhs: The function representing the right-hand side of the problem.
        **kwargs: Additional parameters for the projection, including collocation points
            and losses.

    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        rhs: RHS_FUNC_TYPE | None = None,
        **kwargs,
    ):
        super().__init__(space, rhs, **kwargs)

        self.default_lr: float = kwargs.get("default_lr", 1e-2)
        opt_1 = {
            "name": "sgd",
            "optimizer_args": {"lr": self.default_lr},
        }
        self.optimizer = OptimizerData(opt_1)
        self.bool_linesearch = True
        self.bool_preconditioner = True
        self.nb_epoch_preconditioner_computing = 1
        self.type_linesearch = kwargs.get("type_linesearch", "armijo")
        self.projection_data = {"nonlinear": True, "linear": False, "nb_step": 1}
        self.preconditioner = EnergyNaturalGradientPreconditionerProjector(
            space, has_bc=False, **kwargs
        )
        self.data_linesearch = kwargs.get("data_linesearch", {})
        self.data_linesearch.setdefault("M", 10)
        self.data_linesearch.setdefault("interval", [0.0, 2.0])
        self.data_linesearch.setdefault("log_basis", 2.0)
        self.data_linesearch.setdefault("n_step_max", 10)
        self.data_linesearch.setdefault("alpha", 0.01)
        self.data_linesearch.setdefault("beta", 0.5)


class AnagramProjector(CollocationProjector):
    """Subclass of CollocationProjector using anagram-based optimization.

    This class extends the CollocationProjector to use anagram-based optimization
    for solving the projection problem.

    Args:
        space: The approximation space where the projection will take place.
        rhs: The function representing the right-hand side of the problem.
        **kwargs: Additional parameters for the projection, including collocation points
            and losses.
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        rhs: RHS_FUNC_TYPE | None = None,
        **kwargs,
    ):
        super().__init__(space, rhs, **kwargs)

        self.default_lr: float = kwargs.get("default_lr", 1e-2)
        opt_1 = {
            "name": "sgd",
            "optimizer_args": {"lr": self.default_lr},
        }
        self.optimizer = OptimizerData(opt_1)
        self.bool_linesearch = True
        self.bool_preconditioner = True
        self.nb_epoch_preconditioner_computing = 1
        self.type_linesearch = kwargs.get("type_linesearch", "armijo")
        self.projection_data = {"nonlinear": True, "linear": False, "nb_step": 1}
        self.preconditioner = AnagramPreconditionerProjector(
            space, has_bc=False, **kwargs
        )
        self.data_linesearch = kwargs.get("data_linesearch", {})
        self.data_linesearch.setdefault("M", 10)
        self.data_linesearch.setdefault("interval", [0.0, 2.0])
        self.data_linesearch.setdefault("log_basis", 2.0)
        self.data_linesearch.setdefault("n_step_max", 10)
        self.data_linesearch.setdefault("alpha", 0.01)
        self.data_linesearch.setdefault("beta", 0.5)


class LinearProjector(CollocationProjector):
    """Subclass of CollocationProjector for linear projection problems.

    This class extends the CollocationProjector to handle linear projection problems.

    Args:
        space: The approximation space where the projection will take place.
        rhs: The function representing the right-hand side of the problem.
        **kwargs: Additional parameters for the projection, including collocation points
            and losses.
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        rhs: Callable,
        **kwargs,
    ):
        super().__init__(space, rhs, **kwargs)

        self.projection_data = {"nonlinear": False, "linear": True, "nb_step": 1}


def plot(f: Callable, sampler: Callable, n_visu: int = 500):  # pragma: no cover
    """Plot the function f over a 2D domain using sampled points.

    Args:
        f: The function to plot, which takes in sampled points and parameters.
        sampler: A callable that samples points from the domain.
        n_visu: The number of points along each axis for visualization.
    """
    import matplotlib.pyplot as plt

    from scimba_torch.utils.scimba_tensors import LabelTensor

    x, mu = sampler(n_visu**2)

    x1 = torch.linspace(0, 1 - 0, n_visu)
    x2 = torch.linspace(0, 1 - 0, n_visu)
    x1, x2 = torch.meshgrid(x1, x2, indexing="ij")
    x = LabelTensor(torch.stack((x1.flatten(), x2.flatten()), dim=1))

    x1, x2 = x.get_components()
    x1, x2 = x1.detach().cpu(), x2.detach().cpu()

    predictions = f(x, mu).detach().cpu()

    fig, ax = plt.subplots(1, 1, figsize=(9, 3), constrained_layout=True)

    x1 = x1.reshape(n_visu, n_visu)
    x2 = x2.reshape(n_visu, n_visu)
    predictions = predictions.reshape(n_visu, n_visu)

    contour = ax.contourf(x1, x2, predictions, levels=256, cmap="turbo")
    fig.colorbar(contour, ax=ax, fraction=0.046, pad=0.04)
    ax.contour(x1, x2, predictions, levels=8, colors="white", linewidths=0.5)
    ax.set_title("Predictions")

    plt.show()

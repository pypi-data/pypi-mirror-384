"""Flow trainers for optimization and projection in flow spaces."""

from typing import Any

import torch

from scimba_torch.flows.deep_flows import ContinuousFlowSpace, DiscreteFlowSpace
from scimba_torch.numerical_solvers.abstract_projector import (
    AbstractNonlinearProjector,
)
from scimba_torch.numerical_solvers.preconditioner_projector import (
    EnergyNaturalGradientPreconditionerProjector,
)
from scimba_torch.optimizers.optimizers_data import OptimizerData


class FlowTrainer(AbstractNonlinearProjector):
    """Abstract class for a nonlinear projector.

    This class defines a nonlinear projector with various projection options
    and an optimization method. It is used to solve projection problems in a given
    approximation space, using optimization methods.

    Args:
        flow: The flow space (discrete or continuous) where the projection takes place.
        full_data: Tuple containing the full dataset for training.
        **kwargs: Additional parameters, such as the type of projection, losses, and
            optimizers.
    """

    space: (
        DiscreteFlowSpace | ContinuousFlowSpace
    )  #: The approximation space where the projection takes place.
    full_data: tuple  #: Tuple containing the full dataset for training.
    y: torch.Tensor  #: Target tensor for training.

    def __init__(
        self,
        flow: DiscreteFlowSpace | ContinuousFlowSpace,
        full_data: tuple,
        **kwargs: Any,
    ):
        super().__init__(space=flow, rhs=None, **kwargs)
        self.full_data = full_data

    def get_dof(self, flag_scope: str = "all", flag_format: str = "list") -> Any:
        """Get degrees of freedom from the space.

        Args:
            flag_scope: Scope for the degrees of freedom. Defaults to "all".
            flag_format: Format for the degrees of freedom. Defaults to "list".

        Returns:
            Degrees of freedom in the specified format.
        """
        return self.space.get_dof(flag_scope, flag_format)

    def sample_all_vars(self, **kwargs: Any) -> tuple:
        """Sample variables from the full dataset.

        Args:
            **kwargs: Additional keyword arguments, including :code:`batch_size (int)`:
                Number of samples to draw. Defaults to 10.

        Returns:
            A tuple containing sampled inputs and corresponding targets.
        """
        batch_size = kwargs.get("batch_size", 10)
        inputs, y = self.full_data
        indices = torch.randperm(inputs.shape[0])[:batch_size]
        self.y = y[indices]
        return (
            inputs[indices, : -self.space.param_dim],
            inputs[indices, -self.space.param_dim :],
        )

    def assembly_post_sampling(self, data: tuple, **kwargs: Any) -> tuple:
        """Assemble the system after sampling.

        Args:
            data: Tuple containing sampled inputs and parameters.
            **kwargs: Additional keyword arguments, including :code:`flag_scope (str)`:
                scope for the last layer. Defaults to "all".

        Returns:
            A tuple containing the left-hand side and right-hand side of the system.
        """
        flag_scope = kwargs.get("flag_scope", "all")
        with_last_layer = True
        if flag_scope == "expect_last_layer":
            with_last_layer = False

        args = [data[0], data[1]]
        u = self.space.evaluate(*args, with_last_layer)  # u is a multilabelTensor

        left = (u,)
        right = (self.y,)

        return left, right

    def assembly(self, **kwargs: Any) -> tuple:
        """Assembles the system of equations for the PDE.

        (and weak boundary conditions if needed).

        Args:
            **kwargs: Additional keyword arguments including:

                - :code:`n_collocation (int)`: Number of collocation points for the PDE.
                  Defaults to 1000.
                - :code:`n_bc_collocation (int)`: Number of collocation points for the
                  boundary conditions. Defaults to 1000.

        Returns:
            tuple: A tuple containing the assembled system of equations (Lo, f).
        """
        data = self.sample_all_vars(**kwargs)
        return self.assembly_post_sampling(data, **kwargs)


class NaturalGradientFlowTrainer(FlowTrainer):
    """Natural gradient flow trainer for optimization.

    This class extends FlowTrainer to use natural gradient optimization with
    preconditioning and line search capabilities.

    Args:
        flow: The flow space (discrete or continuous) where the projection takes place.
        full_data: Tuple containing the full dataset for training.
        **kwargs: Additional parameters including learning rate, line search options,
            etc.
    """

    default_lr: float  #: Default learning rate for the optimizer.
    optimizer: OptimizerData  #: The optimizer used for parameter updates.
    bool_linesearch: bool  #: Whether to use line search.
    bool_preconditioner: bool  #: Whether to use preconditioning.
    nb_epoch_preconditioner_computing: (
        int  #: Number of epochs for preconditioner computation.
    )
    type_linesearch: str  #: Type of line search algorithm.
    projection_data: dict  #: Data structure for projection settings.
    preconditioner: (
        EnergyNaturalGradientPreconditionerProjector  #: The preconditioner instance.
    )
    data_linesearch: dict  #: Parameters for line search configuration.

    def __init__(
        self,
        flow: DiscreteFlowSpace | ContinuousFlowSpace,
        full_data: tuple,
        **kwargs: Any,
    ):
        super().__init__(flow, full_data, **kwargs)

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
            flow, **kwargs
        )
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

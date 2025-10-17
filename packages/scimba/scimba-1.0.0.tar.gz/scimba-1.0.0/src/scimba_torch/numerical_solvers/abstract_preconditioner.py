"""Preconditioners for projectors."""

from abc import ABC, abstractmethod

import torch

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
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

ACCEPTED_PDE_TYPES = (
    EllipticPDE
    | TemporalPDE
    | KineticPDE
    | LinearOrder2PDE
    | RitzFormEllipticPDE
    | DivAGradUPDE
    | None
)


class AbstractPreconditioner(ABC):
    """Abstract class for preconditioner solvers.

    Args:
        space: The approximation space.
        pde: The PDE to be solved, None by default for projection.
        **kwargs: Additional keyword arguments:

            - `has_bc` (:code:`bool`): Whether the PDE has boundary conditions.
              (default: False)
            - `bc_weight` (:code:`float`): Weight for the boundary conditions.
              (default: 10.0)
            - `has_ic` (:code:`bool`): Whether the PDE has initial conditions.
              (default: False)
            - `ic_weight` (:code:`float`): Weight for the initial conditions.
              (default: 10.0)
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        pde: ACCEPTED_PDE_TYPES = None,
        **kwargs,
    ):
        self.space = space
        self.pde = pde

        self.has_bc = kwargs.get("has_bc", False)
        self.bc_weight = kwargs.get("bc_weight", 10.0)

        self.has_ic = kwargs.get("has_ic", False)
        self.ic_weight = kwargs.get("ic_weight", 10.0)

        # print("bc_weight: ", self.bc_weight)
        # print("ic_weight: ", self.ic_weight)

    @abstractmethod
    def __call__(
        self,
        epoch: int,
        data: tuple | dict,
        grads: torch.Tensor,
        res_l: tuple,
        res_r: tuple,
        **kwargs,
    ) -> torch.Tensor:
        """Abstract method for preconditioner call.

        Args:
            epoch: Current training epoch.
            data: Input data, either as a tuple or a dictionary.
            grads: Gradient tensor to be preconditioned.
            res_l: Left residuals.
            res_r: Right residuals.
            **kwargs: Additional keyword arguments.

        Returns:
            The preconditioned gradient tensor.
        """


class IdPreconditioner(AbstractPreconditioner):
    """Identity preconditioner that returns the input gradients unchanged.

    Args:
        space: The approximation space.
        pde: The PDE to be solved, None by default for projection.
        **kwargs: Additional keyword arguments.
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        pde: ACCEPTED_PDE_TYPES = None,
        **kwargs,
    ):
        super().__init__(space, pde, **kwargs)

    def __call__(
        self,
        epoch: int,
        data: tuple | dict,
        grads: torch.Tensor,
        res_l: tuple,
        res_r: tuple,
        **kwargs,
    ) -> torch.Tensor:
        """Return the input gradients unchanged.

        Args:
            epoch: Current training epoch.
            data: Input data, either as a tuple or a dictionary.
            grads: Gradient tensor to be preconditioned.
            res_l: Left residuals.
            res_r: Right residuals.
            **kwargs: Additional keyword arguments.

        Returns:
            The unmodified gradient tensor.
        """
        return grads

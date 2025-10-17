"""Abstract models for kinetic and collisional EDPs."""

from abc import ABC, abstractmethod

import torch

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.physical_models.elliptic_pde.abstract_elliptic_pde import EllipticPDE
from scimba_torch.physical_models.temporal_pde.abstract_temporal_pde import TemporalPDE
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor


class KineticPDE(ABC):
    """Base class for representing elliptic Partial Differential Equations (PDEs).

    Args:
        space: Approximation space used for the PDE
        field: Associated field
        linear: Indicates if the PDE is linear
        **kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        field: EllipticPDE | TemporalPDE | None = None,
        linear: bool = False,
        **kwargs,
    ):
        super().__init__()
        self.space = space
        self.field = field
        self.linear = linear
        self.constant_advection = kwargs.get("constant_advection", False)

    def time_operator(
        self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the time derivative of the tensor `w` with respect to the tensor `t`.

        Args:
            w: Input tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            Time derivative tensor

        Raises:
            NotImplementedError: If not implemented in subclass.
        """
        raise NotImplementedError("Implement time_operator in subclass.")

    @abstractmethod
    def rhs(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        v: LabelTensor,
        mu: LabelTensor,
    ) -> torch.Tensor:
        """Compute the right-hand side (RHS) of the PDE.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            v: Velocity coordinate tensor
            mu: Parameter tensor

        Returns:
            RHS tensor
        """
        pass

    @abstractmethod
    def space_operator(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        v: LabelTensor,
        mu: LabelTensor,
    ) -> torch.Tensor:
        """Apply the PDE operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            v: Velocity coordinate tensor
            mu: Parameter tensor

        Returns:
            Operator tensor
        """
        pass

    @abstractmethod
    def bc_rhs(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        v: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> torch.Tensor:
        """Compute the boundary condition RHS.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            v: Velocity coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            Boundary condition RHS tensor
        """
        pass

    @abstractmethod
    def bc_operator(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        v: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> torch.Tensor:
        """Apply the boundary condition operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            v: Velocity coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            Boundary condition operator tensor
        """
        pass

    @abstractmethod
    def initial_condition(
        self, x: LabelTensor, v: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the initial condition.

        Args:
            x: Spatial coordinate tensor
            v: Velocity coordinate tensor
            mu: Parameter tensor

        Returns:
            Initial condition tensor
        """
        pass


class CollisionalKineticPDE(KineticPDE):
    """Base class for collisional kinetic PDEs.

    Args:
        space: Approximation space used for the PDE
        field: Associated field
        linear: Indicates if the PDE is linear
        **kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        field: EllipticPDE | TemporalPDE | None = None,
        linear: bool = False,
        **kwargs,
    ):
        super().__init__(space, field, linear, **kwargs)
        self.space = space
        self.field = field
        self.linear = linear

    @abstractmethod
    def rhs(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        v: LabelTensor,
        mu: LabelTensor,
    ) -> torch.Tensor:
        """Compute the right-hand side (RHS) of the PDE.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            v: Velocity coordinate tensor
            mu: Parameter tensor

        Returns:
            RHS tensor
        """
        pass

    @abstractmethod
    def space_operator(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        v: LabelTensor,
        mu: LabelTensor,
    ) -> torch.Tensor:
        """Apply the PDE operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            v: Velocity coordinate tensor
            mu: Parameter tensor

        Returns:
            Operator tensor
        """
        pass

    @abstractmethod
    def bc_rhs(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        v: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> torch.Tensor:
        """Compute the boundary condition RHS.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            v: Velocity coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            Boundary condition RHS tensor
        """
        pass

    @abstractmethod
    def bc_operator(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        v: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> torch.Tensor:
        """Apply the boundary condition operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            v: Velocity coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            Boundary condition operator tensor
        """
        pass

    @abstractmethod
    def initial_condition(
        self, x: LabelTensor, v: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the initial condition.

        Args:
            x: Spatial coordinate tensor
            v: Velocity coordinate tensor
            mu: Parameter tensor

        Returns:
            Initial condition tensor
        """
        pass

    @abstractmethod
    def collision_kernel(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        v: LabelTensor,
        mu: LabelTensor,
    ) -> torch.Tensor:
        """Compute the collision kernel for the PDE.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            v: Velocity coordinate tensor
            mu: Parameter tensor

        Returns:
            Collision kernel tensor
        """
        pass


# TODO: How to make the splitting with several spaces and several RHS?
# PDE temporal lists with a method so that the W is all the variables
# of all spaces?

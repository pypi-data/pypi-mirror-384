"""Model for the kinetic radiative transfer equation."""

from typing import Callable

from torch import Tensor

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.physical_models.elliptic_pde.abstract_elliptic_pde import EllipticPDE
from scimba_torch.physical_models.kinetic_pde.abstract_kinetic_pde import KineticPDE
from scimba_torch.physical_models.temporal_pde.abstract_temporal_pde import TemporalPDE
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor


class RadiativeTransfer(KineticPDE):
    """Base class for representing Radiative Transfer PDEs.

    Args:
        space: Approximation space used for the PDE
        field: Field of the PDE
        init: Callable for the initial condition
        f: Callable for the source term
        g: Callable for the boundary condition
        **kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        field: EllipticPDE | TemporalPDE,
        init: Callable,
        f: Callable,
        g: Callable,
        **kwargs,
    ):
        super().__init__(space, field, **kwargs)
        self.init = init
        self.f = f
        self.g = g

    def rhs(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        v: LabelTensor,
        mu: LabelTensor,
    ) -> Tensor:
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
        return self.f(w, t, x, v, mu)

    def space_operator(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        v: LabelTensor,
        mu: LabelTensor,
    ) -> Tensor:
        """Apply the PDE operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            v: Velocity coordinate tensor
            mu: Parameter tensor

        Returns:
            Operator tensor

        Raises:
            NotImplementedError: If x.dim is not 2 or 3.
        """
        u = w.get_components()
        if x.dim == 2:
            v_x, v_y = v.get_components()
            u_x, u_y = self.space.grad(u, x)
            return v_x * u_x + v_y * u_y
        elif x.dim == 3:
            v_x, v_y, v_z = v.get_components()
            u_x, u_y, u_z = self.space.grad(u, x)
            return v_x * u_x + v_y * u_y + v_z * u_z
        raise NotImplementedError("space_operator: x.dim must be 2 or 3")

    def bc_rhs(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        v: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> LabelTensor:
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
        return self.g(w, t, x, v, n, mu)

    def bc_operator(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        v: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> LabelTensor:
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
        ul = w.get_components(index=0)
        ur = w.get_components(index=1)
        ub = w.get_components(index=2)
        ut = w.get_components(index=3)
        return ur - ul + ut - ub

    def initial_condition(
        self,
        x: LabelTensor,
        v: LabelTensor,
        mu: LabelTensor,
    ) -> Tensor:
        """Compute the initial condition.

        Args:
            x: Spatial coordinate tensor
            v: Velocity coordinate tensor
            mu: Parameter tensor

        Returns:
            Initial condition tensor
        """
        return self.init(x, v, mu)

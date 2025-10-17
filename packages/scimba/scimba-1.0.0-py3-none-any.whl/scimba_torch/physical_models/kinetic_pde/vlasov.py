"""Model for the Vlasov equation."""

from typing import Callable

import torch

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.physical_models.kinetic_pde.abstract_kinetic_pde import KineticPDE
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor


def scalar_zero(
    t: LabelTensor, x: LabelTensor, v: LabelTensor, mu: LabelTensor
) -> torch.Tensor:
    """Returns a tensor of zeros with shape (x.shape[0], 1).

    Args:
        t: Temporal coordinate tensor
        x: Spatial coordinate tensor
        v: Velocity coordinate tensor
        mu: Parameter tensor

    Returns:
        A tensor of zeros with shape (x.shape[0], 1)
    """
    return torch.zeros((x.shape[0], 1))


class Vlasov(KineticPDE):
    """Base class for representing Vlasov PDEs.

    Args:
        space: Approximation space used for the PDE
        initial_condition: Initial condition function
        electric_field: Electric field function
        f: Source term function
        g: Boundary condition function
        **kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        initial_condition: Callable,
        electric_field: Callable,
        f: Callable = scalar_zero,
        g: Callable = scalar_zero,
        **kwargs,
    ):
        super().__init__(space, linear=True, constant_advection=False, **kwargs)
        self.initial_condition = initial_condition
        self.electric_field = electric_field
        self.f = f
        self.g = g

        self.dim_x = space.dim_x
        self.dim_v = space.dim_v

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
        return self.f(w, t, x, v, mu)

    def dot_product_of_tuples(
        self, f: tuple[torch.Tensor], g: tuple[torch.Tensor]
    ) -> torch.Tensor:
        """Performs a dot product between two tuples of tensors.

        Args:
            f: First tuple of tensors
            g: Second tuple of tensors

        Returns:
            Dot product result
        """
        return sum([f_ * g_ for f_, g_ in zip(f, g)])

    def dot_product_of_tensor_and_tuple(
        self, f: torch.Tensor, g: tuple[torch.Tensor]
    ) -> torch.Tensor:
        """Performs a dot product between a tensor and a tuple of tensors.

        (the tuple should have the same size as the tensor).

        Args:
            f: Tensor
            g: Tuple of tensors

        Returns:
            Dot product result
        """
        return sum([f[..., i] * g[i] for i in range(len(g))])

    def a(self, t: LabelTensor, xv: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        """Full advection field: a = [v, E].

        Args:
            t: Temporal coordinate tensor
            xv: Concatenated spatial and velocity coordinate tensors
            mu: Parameter tensor

        Returns:
            Advection field tensor
        """
        x, v = xv[:, : self.dim_x], xv[:, self.dim_x :]
        E = self.electric_field(t, x, mu)
        return torch.cat((v.x, E), dim=1)

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
        u = w.get_components()

        # first part of the Vlasov operator: <v, grad_x(u)>

        v_ = v.get_components()
        u_x = self.space.grad(u, x)

        v_u_x = self.dot_product_of_tuples(v_, u_x)

        # second part of the Vlasov operator: <E, grad_v(u)>

        E = self.electric_field(t, x, mu).get_components()
        u_v = self.space.grad(u, v)

        E_u_v = self.dot_product_of_tensor_and_tuple(E, u_v)

        # assemble both parts

        return v_u_x + E_u_v

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
        return self.g(w, x, v, n, mu)

    def bc_operator(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        v: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> torch.Tensor:
        """Apply the periodic boundary condition operator.

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
    ) -> torch.Tensor:
        """Compute the initial condition.

        Args:
            x: Spatial coordinate tensor
            v: Velocity coordinate tensor
            mu: Parameter tensor

        Returns:
            Initial condition tensor
        """
        return self.initial_condition(x, v, mu)

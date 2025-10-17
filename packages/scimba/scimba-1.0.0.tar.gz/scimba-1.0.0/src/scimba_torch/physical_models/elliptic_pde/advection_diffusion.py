"""Advection-reaction-diffusion problems in 1D and 2D.

Use Dirichlet boundary conditions in strong form.
"""

from typing import Callable

import torch

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.physical_models.elliptic_pde.abstract_elliptic_pde import (
    StrongFormEllipticPDE,
)
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor


def scalar_zero(x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
    """Return a tensor of zeros with shape (batch_size, 1).

    Args:
        x: Input tensor.
        mu: Parameter tensor.

    Returns:
        A tensor of zeros with shape (batch_size, 1).
    """
    return torch.zeros((x.shape[0], 1))


def scalar_ones(x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
    """Return a tensor of ones with shape (batch_size, 1).

    Args:
        x: Input tensor.
        mu: Parameter tensor.

    Returns:
        A tensor of ones with shape (batch_size, 1).
    """
    return torch.ones((x.shape[0], 1))


def vector_ones(x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
    """Return a tensor of ones with shape (batch_size, 2).

    Args:
        x: Input tensor.
        mu: Parameter tensor.

    Returns:
        A tensor of ones with shape (batch_size, 2).
    """
    return torch.ones((x.shape[0], 2))


def matrix_zero(x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
    """Return a tensor of zeros with shape (batch_size, 2, 2).

    Args:
        x: Input tensor.
        mu: Parameter tensor.

    Returns:
        A tensor of zeros with shape (batch_size, 2, 2).
    """
    return torch.zeros((x.shape[0], 2, 2))


class AdvectionReactionDiffusion1DDirichletStrongForm(StrongFormEllipticPDE):
    r"""1D advection-reaction-diffusion problem with strong Dirichlet BCs.

    .. math::

        r(x, \mu) u(x, \mu) + a(x, \mu) \partial_x u(x, \mu)
        - \partial_x (d(x, \mu) \partial_x u(x, \mu))
        & = f(x, \mu) \text{ in } \Omega, \\
        u(x, \mu) & = g(x, \mu) \text{ on } \partial \Omega.

    By default, $r = 0$, $a = 1$, $d = 0$, $f = 0$, and $g = 0$.
    The user can specify these functions as needed.

    Args:
        space: The approximation space for the problem.
        r: Callable representing the reaction term r(x, mu).
        a: Callable representing the advection term a(x, mu).
        d: Callable representing the advection term d(x, mu).
        f: Callable representing the source term f(x, mu).
        g: Callable representing the Dirichlet boundary condition g(x, mu).
        constant_advection: Whether the advection term is constant.
        constant_diffusion: Whether the diffusion term is constant.
        zero_diffusion: Whether the diffusion term is zero.
        **kwargs: Additional keyword arguments.
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        r: Callable[[LabelTensor, LabelTensor], torch.Tensor] = scalar_zero,
        a: Callable[[LabelTensor, LabelTensor], torch.Tensor] = scalar_ones,
        d: Callable[[LabelTensor, LabelTensor], torch.Tensor] = scalar_zero,
        f: Callable[[LabelTensor, LabelTensor], torch.Tensor] = scalar_zero,
        g: Callable[[LabelTensor, LabelTensor], torch.Tensor] = scalar_zero,
        constant_advection: bool = True,
        constant_diffusion: bool = True,
        zero_diffusion: bool = True,
        **kwargs,
    ):
        super().__init__(
            space, linear=True, residual_size=1, bc_residual_size=1, **kwargs
        )
        self.r = r
        self.a = a
        self.d = d
        self.f = f
        self.g = g
        self.constant_diffusion = constant_diffusion
        self.constant_advection = constant_advection
        self.zero_diffusion = zero_diffusion

    def rhs(self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        r"""Compute the right-hand side (RHS) of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            The source term f(x, mu).
        """
        return self.f(x, mu)

    def operator(
        self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        r"""Compute the differential operator of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            The result of applying the operator to the state.
        """
        u = w.get_components()
        u_x = self.grad(w, x)

        reaction = self.r(x, mu) * u
        advection = self.a(x, mu) * u_x

        if self.zero_diffusion:
            return reaction + advection

        diffusion = self.grad(self.d(x, mu) * u_x, x)
        return reaction + advection - diffusion

    def bc_rhs(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        r"""Compute the RHS for the boundary conditions.

        Args:
            w: State tensor.
            x: Boundary coordinates tensor.
            n: Normal vector tensor.
            mu: Parameter tensor.

        Returns:
            The boundary condition g(x, mu).
        """
        return self.g(x, mu)

    def bc_operator(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        r"""Compute the operator for the boundary conditions.

        Args:
            w: State tensor.
            x: Boundary coordinates tensor.
            n: Normal vector tensor.
            mu: Parameter tensor.

        Returns:
            The boundary operator applied to the state.
        """
        u = w.get_components()
        assert isinstance(u, torch.Tensor)
        return u


class AdvectionReactionDiffusion2DDirichletStrongForm(StrongFormEllipticPDE):
    r"""2D advection-reaction-diffusion problem with strong Dirichlet BCs.

    .. math::

        r(x, \mu) u(x, \mu)
        + a(x, \mu) \cdot \nabla_x u(x, \mu)
        - \nabla_x \cdot (d(x, \mu) \nabla_x u(x, \mu))
        & = f(x, \mu) \text{ in } \Omega, \\
        u(x, \mu) & = g(x, \mu) \text{ on } \partial \Omega.

    By default, $r = 0$, $a = (1, 1)$, $d = [(0, 0), (0, 0)]$, $f = 0$, and $g = 0$.
    The user can specify these functions as needed.

    Args:
        space: The approximation space for the problem.
        r: Callable representing the reaction term r(x, mu).
        a: Callable representing the advection term a(x, mu).
        d: Callable representing the advection term d(x, mu).
        f: Callable representing the source term f(x, mu).
        g: Callable representing the Dirichlet boundary condition g(x, mu).
        constant_advection: Whether the advection term is constant.
        constant_diffusion: Whether the diffusion term is constant.
        zero_diffusion: Whether the diffusion term is zero.
        **kwargs: Additional keyword arguments.
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        r: Callable[[LabelTensor, LabelTensor], torch.Tensor] = scalar_zero,
        a: Callable[[LabelTensor, LabelTensor], torch.Tensor] = vector_ones,
        d: Callable[[LabelTensor, LabelTensor], torch.Tensor] = matrix_zero,
        f: Callable[[LabelTensor, LabelTensor], torch.Tensor] = scalar_zero,
        g: Callable[[LabelTensor, LabelTensor], torch.Tensor] = scalar_zero,
        constant_advection: bool = True,
        constant_diffusion: bool = True,
        zero_diffusion: bool = True,
        **kwargs,
    ):
        super().__init__(
            space, linear=True, residual_size=1, bc_residual_size=1, **kwargs
        )
        self.r = r
        self.a = a
        self.d = d
        self.f = f
        self.g = g
        self.constant_diffusion = constant_diffusion
        self.constant_advection = constant_advection
        self.zero_diffusion = zero_diffusion

    def rhs(self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        r"""Compute the right-hand side (RHS) of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            The source term f(x, mu).
        """
        return self.f(x, mu)

    def operator(
        self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        r"""Compute the differential operator of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            The result of applying the operator to the state.
        """
        u = w.get_components()  # scalar field, [batch, 1]
        a = self.a(x, mu)  # 2D vector, [batch, 2]
        d = self.d(x, mu)  # 2x2 matrix, [batch, 2, 2]

        reaction = self.r(x, mu) * u

        u_x, u_y = self.grad(w, x)
        advection = a[:, 0:1] * u_x + a[:, 1:2] * u_y

        if self.zero_diffusion:
            return reaction + advection

        diffusion_x = d[:, 0, 0:1] * u_x + d[:, 0, 1:2] * u_y
        diffusion_y = d[:, 1, 0:1] * u_x + d[:, 1, 1:2] * u_y
        diffusion_xx, _ = self.grad(diffusion_x, x)
        _, diffusion_yy = self.grad(diffusion_y, x)
        diffusion = diffusion_xx + diffusion_yy

        return reaction + advection - diffusion

    def bc_rhs(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        r"""Compute the RHS for the boundary conditions.

        Args:
            w: State tensor.
            x: Boundary coordinates tensor.
            n: Normal vector tensor.
            mu: Parameter tensor.

        Returns:
            The boundary condition g(x, mu).
        """
        return self.g(x, mu)

    def bc_operator(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        r"""Compute the operator for the boundary conditions.

        Args:
            w: State tensor.
            x: Boundary coordinates tensor.
            n: Normal vector tensor.
            mu: Parameter tensor.

        Returns:
            The boundary operator applied to the state.
        """
        u = w.get_components()
        assert isinstance(u, torch.Tensor)
        return u

"""Advection-reaction-diffusion equation."""

from typing import Callable

import torch
from torch._tensor import Tensor

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.physical_models.temporal_pde.abstract_temporal_pde import (
    FirstOrderTemporalPDE,
)
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor


def scalar_zeros(t: LabelTensor, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
    """Return a tensor of zeros with shape (batch_size, 1).

    Args:
        t: Temporal coordinate tensor
        x: Spatial coordinate tensor
        mu: Parameter tensor

    Returns:
        A tensor of zeros with shape (x.shape[0], 1)
    """
    return torch.zeros((x.shape[0], 1))


def init_ones(x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
    """Return a tensor of ones with shape (batch_size, 1).

    Args:
        x: Spatial coordinate tensor
        mu: Parameter tensor

    Returns:
        A tensor of ones with shape (x.shape[0], 1)
    """
    return torch.ones((x.shape[0], 1))


def vector_ones(t: LabelTensor, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
    """Return a tensor of ones with shape (batch_size, spatial_dim).

    Args:
        t: Temporal coordinate tensor
        x: Spatial coordinate tensor
        mu: Parameter tensor

    Returns:
        A tensor of ones with shape (x.shape[0], x.shape[1])
    """
    return torch.ones((x.shape[0], x.shape[1]))


def matrix_zeros(t: LabelTensor, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
    """Return a tensor of zeros with shape (batch_size, spatial_dim, spatial_dim).

    Args:
        t: Temporal coordinate tensor
        x: Spatial coordinate tensor
        mu: Parameter tensor

    Returns:
        A tensor of zeros with shape (x.shape[0], x.shape[1], x.shape[1])
    """
    return torch.zeros((x.shape[0], x.shape[1], x.shape[1]))


class AdvectionReactionDiffusion(FirstOrderTemporalPDE):
    r"""Class implementing the reaction, advection and diffusion coefficients.

    For an advection-reaction-diffusion problem in n space dimensions.
    In general, the PDE is given by:

    .. math::
        r(t, x, \mu) u(t, x, \mu)
        + a(t, x, \mu) \cdot \nabla_x u(t, x, \mu)
        - \nabla_x \cdot (d(t, x, \mu) \nabla_x u(t, x, \mu))
        = f(t, x, \mu)

    By default, $r = 0$, :math:`a = \mathbb{1}_{\mathbb{R}^n}`,
    :math:`d = \mathbb{0}_{\mathcal{M}_n(\mathbb{R})}`, $f = 0$, and $u0 = 1$.
    The user can specify these functions as needed.

    Args:
        space: The approximation space for the problem.
        r: Reaction term function
        a: Advection term function
        d: Diffusion term function
        f: Source term function
        u0: Initial condition function
        constant_advection: Whether the advection term is constant
        constant_diffusion: Whether the diffusion term is constant
        zero_diffusion: Whether the diffusion term is zero
        **kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        r: Callable = scalar_zeros,
        a: Callable = vector_ones,
        d: Callable = matrix_zeros,
        f: Callable = scalar_zeros,
        u0: Callable = init_ones,
        constant_advection: bool = False,
        constant_diffusion: bool = False,
        zero_diffusion: bool = False,
        **kwargs,
    ):
        # Rémi: no attribute 'residual_size', 'bc_residual_size'...
        # super().__init__(
        #     space, linear=True, residual_size=1, bc_residual_size=1, **kwargs
        # )
        super().__init__(space, linear=True, **kwargs)

        # get functions
        self.r = r
        self.a = a
        self.d = d
        self.f = f
        self.u0 = u0

        # get flags
        self.constant_advection = a == vector_ones
        self.zero_diffusion = d == matrix_zeros

        if self.constant_advection:
            assert constant_advection, (
                "Advection velocity is constant, but constant_advection is False."
            )

        if self.zero_diffusion:
            assert zero_diffusion, (
                "Diffusion matrix is zero, but zero_diffusion is False."
            )

        self.constant_advection = constant_advection
        self.constant_diffusion = constant_diffusion
        self.zero_diffusion = zero_diffusion

        # extract kwargs

        self.exact_solution = kwargs.get("exact_solution", None)

    def rhs(
        self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> Tensor:
        """Compute the right-hand side (RHS) of the PDE.

        Args:
            w: State tensor
            t: Temporal coordinates tensor
            x: Spatial coordinates tensor
            mu: Parameter tensor

        Returns:
            The source term
        """
        return self.f(t, x, mu)

    def space_operator(
        self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> Tensor:
        """Compute the differential operator of the PDE, in space.

        Args:
            w: State tensor
            t: Temporal coordinates tensor
            x: Spatial coordinates tensor
            mu: Parameter tensor

        Returns:
            The result of applying the operator to the state
        """
        u = w.get_components()
        assert isinstance(u, Tensor)
        u_x = self.grad(u, x)

        reaction = self.r(t, x, mu) * u

        advection = self.a(t, x, mu) * u_x

        if self.zero_diffusion:
            return reaction + advection

        d = self.d(t, x, mu) * u_x.squeeze()
        diffusion = self.grad(d, x)
        return reaction + advection - diffusion

    def initial_condition(self, x: LabelTensor, mu: LabelTensor) -> Tensor:
        """Compute the initial condition.

        Args:
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            Initial condition tensor
        """
        return self.u0(x, mu)


class AdvectionReactionDiffusionDirichletStrongForm(AdvectionReactionDiffusion):
    r"""advection-reaction-diffusion problem with Dirichlet BCs in strong form.

    .. math::
        r(t, x, \mu) u(t, x, \mu)
        + a(t, x, \mu) \cdot \nabla_x u(t, x, \mu)
        - \nabla_x \cdot (d(t, x, \mu) \nabla_x u(t, x, \mu))
        & = f(t, x, \mu) \text{ in } \Omega, \\
        u(t, x, \mu) & = g(t, x, \mu) \text{ on } \partial \Omega, \\
        u(0, x, \mu) & = u_0(x, \mu) \text{ in } \Omega.

    By default, $r = 0$, :math:`a = \mathbb{1}_{\mathbb{R}^n}`,
    :math:`d = \mathbb{0}_{\mathcal{M}_n(\mathbb{R})}`, $f = 0$, and $u0 = 1$.
    The user can specify these functions as needed.

    Args:
        space: The approximation space for the problem
        r: Reaction term function
        a: Advection term function
        d: Diffusion term function
        f: Source term function
        g: Dirichlet boundary condition function
        u0: Initial condition function
        constant_advection: Whether the advection term is constant
        constant_diffusion: Whether the diffusion term is constant
        zero_diffusion: Whether the diffusion term is zero
        **kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        r: Callable = scalar_zeros,
        a: Callable = vector_ones,
        d: Callable = matrix_zeros,
        f: Callable = scalar_zeros,
        g: Callable = scalar_zeros,
        u0: Callable = init_ones,
        constant_advection: bool = False,
        constant_diffusion: bool = False,
        zero_diffusion: bool = False,
        **kwargs,
    ):
        super().__init__(
            space,
            r,
            a,
            d,
            f,
            u0,
            constant_advection,
            constant_diffusion,
            zero_diffusion,
            **kwargs,
        )

        self.g = g

    def bc_operator(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> Tensor:
        r"""Compute the operator for the boundary conditions.

        Args:
            w: State tensor
            t: Temporal coordinates tensor
            x: Boundary coordinates tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            The boundary operator applied to the state
        """
        u = w.get_components()
        assert isinstance(u, Tensor)
        return u

    def bc_rhs(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> Tensor:
        r"""Compute the RHS for the boundary conditions.

        Args:
            w: State tensor
            t: Temporal coordinates tensor
            x: Boundary coordinates tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            The boundary condition
        """
        return self.g(w, t, x, n, mu)

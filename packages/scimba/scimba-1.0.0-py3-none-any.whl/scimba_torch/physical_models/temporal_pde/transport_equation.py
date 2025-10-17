"""1D transport equation in strong form."""

from typing import Callable

import torch
from torch._tensor import Tensor

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.physical_models.temporal_pde.abstract_temporal_pde import (
    FirstOrderTemporalPDE,
)
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor
from scimba_torch.utils.typing_protocols import VarArgCallable


class Transport1D(FirstOrderTemporalPDE):
    r"""Implementation of a 1D transport equation with Dirichlet boundary conditions.

    Args:
        space: The approximation space for the problem
        init: Initial condition function
        f: Source term function
        g: Dirichlet boundary condition function
        **kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        init: Callable,
        f: Callable,
        g: Callable,
        **kwargs,
    ):
        super().__init__(space, linear=True, **kwargs)
        self.f = f
        self.g = g
        self.init = init

        self.a = kwargs.get("a", lambda x, t, mu: 1)
        self.functional_a = kwargs.get("functional_a", lambda x, t, mu: 1)

        self.residual_size = 1
        self.bc_residual_size = 1
        self.ic_residual_size = 1

    def space_operator(
        self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> Tensor:
        """Apply the spatial operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            Spatial operator tensor
        """
        u = w.get_components()
        u_x = self.space.grad(u, x)
        return self.a(t, x, mu) * u_x

    def time_operator(
        self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> Tensor:
        """Apply the temporal operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            Temporal operator tensor
        """
        return self.grad(w.get_components(), t)

    def bc_operator(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> Tensor:
        """Apply the boundary condition operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            Boundary condition operator tensor
        """
        return w.get_components()

    def rhs(
        self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> Tensor:
        """Compute the right-hand side (RHS) of the PDE.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            RHS tensor
        """
        return self.f(w, t, x, mu)

    def bc_rhs(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> Tensor:
        """Compute the boundary condition RHS.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            Boundary condition RHS tensor
        """
        return self.g(w, t, x, n, mu)

    def initial_condition(self, x: LabelTensor, mu: LabelTensor) -> Tensor:
        """Compute the initial condition.

        Args:
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            Initial condition tensor
        """
        return self.init(x, mu)

    def functional_operator(
        self,
        func: VarArgCallable,
        t: torch.Tensor,
        x: torch.Tensor,
        mu: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Compute the functional operator for the PDE.

        Args:
            func: Function to differentiate
            t: Temporal tensor
            x: Spatial tensor
            mu: Parameter tensor
            theta: Parameter tensor

        Returns:
            Result of the functional operator
        """
        # space operator
        space_op = self.functional_a(t, x, mu)[0] * torch.func.jacrev(func, 1)(
            t, x, mu, theta
        )
        # time operator
        time_op = torch.func.jacrev(func, 0)(t, x, mu, theta)
        # print((time_op + space_op)[0].shape)
        return (time_op + space_op)[0]

    # Dirichlet conditions
    def functional_operator_bc(
        self,
        func: VarArgCallable,
        t: torch.Tensor,
        x: torch.Tensor,
        n: torch.Tensor,
        mu: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Compute the functional operator for the boundary condition.

        Args:
            func: Function to differentiate
            t: Temporal tensor
            x: Spatial tensor
            n: Normal vector tensor
            mu: Parameter tensor
            theta: Parameter tensor

        Returns:
            Result of the boundary functional operator
        """
        return func(t, x, mu, theta)

    def functional_operator_ic(
        self,
        func: VarArgCallable,
        x: torch.Tensor,
        mu: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Compute the functional operator for the initial condition.

        Args:
            func: Function to differentiate
            x: Spatial tensor
            mu: Parameter tensor
            theta: Parameter tensor

        Returns:
            Result of the initial condition functional operator
        """
        t = torch.zeros_like(x)
        return func(t, x, mu, theta)


class Transport1DImplicit(FirstOrderTemporalPDE):
    r"""1D transport equation with Dirichlet boundary conditions for implicit PINNs.

    Args:
        space: The approximation space for the problem
        init: Initial condition function
        f: Source term function
        g: Dirichlet boundary condition function
        **kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        init: Callable,
        f: Callable,
        g: Callable,
        **kwargs,
    ):
        super().__init__(space, linear=True, **kwargs)
        self.f = f
        self.g = g
        self.init = init

        self.a = kwargs.get("a", lambda x, mu: 1)
        self.functional_a = kwargs.get("functional_a", lambda x, mu: 1)

        self.dt = kwargs.get("dt", 1e-3)
        self.alpha = kwargs.get("alpha", 1.0)

        self.residual_size = 1
        self.bc_residual_size = 1
        self.ic_residual_size = 1

    def space_operator(
        self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> Tensor:
        """Apply the spatial operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            Spatial operator tensor
        """
        u = w.get_components()
        u_x = self.space.grad(u, x)
        return self.a(x, mu) * u_x

    def bc_operator(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> Tensor:
        """Apply the boundary condition operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            Boundary condition operator tensor
        """
        return w.get_components()

    def rhs(
        self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> Tensor:
        """Compute the right-hand side (RHS) of the PDE.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            RHS tensor
        """
        return self.f(w, t, x, mu)

    def initial_condition(self, x: LabelTensor, mu: LabelTensor) -> Tensor:
        """Compute the initial condition.

        Args:
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            Initial condition tensor
        """
        return self.init(x, mu)

    def bc_rhs(
        self,
        w: MultiLabelTensor,
        x: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> Tensor:
        """Compute the boundary condition RHS.

        Args:
            w: Solution tensor
            x: Spatial coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            Boundary condition RHS tensor
        """
        return self.g(w, x, n, mu)

    def functional_operator(
        self,
        func: VarArgCallable,
        # t: LabelTensor,
        x: torch.Tensor,
        mu: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Compute the functional operator for the PDE.

        Args:
            func: Function to differentiate
            x: Spatial tensor
            mu: Parameter tensor
            theta: Parameter tensor

        Returns:
            Result of the functional operator
        """
        space_op = self.functional_a(x, mu) * torch.func.jacrev(func, 0)(x, mu, theta)
        return func(x, mu, theta) - self.alpha * self.dt * space_op[0]

    # Dirichlet conditions
    def functional_operator_bc(
        self,
        func: VarArgCallable,
        t: LabelTensor,
        x: torch.Tensor,
        n: torch.Tensor,
        mu: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Compute the functional operator for the boundary condition.

        Args:
            func: Function to differentiate
            t: Temporal tensor
            x: Spatial tensor
            n: Normal vector tensor
            mu: Parameter tensor
            theta: Parameter tensor

        Returns:
            Result of the boundary functional operator
        """
        return func(x, mu, theta)

    def functional_operator_ic(
        self,
        func: VarArgCallable,
        x: torch.Tensor,
        mu: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Compute the functional operator for the initial condition.

        Args:
            func: Function to differentiate
            x: Spatial tensor
            mu: Parameter tensor
            theta: Parameter tensor

        Returns:
            Result of the initial condition functional operator
        """
        return func(x, mu, theta)

"""Heat equation in strong form."""

from typing import Callable

import torch
from torch._tensor import Tensor

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.physical_models.elliptic_pde.laplacians import (
    Laplacian1DDirichletStrongForm,
    Laplacian1DNeumannStrongForm,
    Laplacian2DDirichletStrongForm,
)
from scimba_torch.physical_models.temporal_pde.abstract_temporal_pde import (
    FirstOrderTemporalPDE,
)
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor
from scimba_torch.utils.typing_protocols import VarArgCallable


class HeatEquation1DStrongForm(FirstOrderTemporalPDE):
    """Implementation of a 1D heat equation with Neumann BCs in strong form.

    Args:
        space: The approximation space for the problem
        init: Callable for the initial condition
        f: Source term function
        g: Neumann boundary condition function
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
        self.space_component = Laplacian1DNeumannStrongForm(space, f, g)
        self.f = f
        self.g = g
        self.init = init

    def space_operator(
        self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor | tuple[torch.Tensor, ...]:
        """Apply the spatial operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            Spatial operator tensor
        """
        return self.space_component.operator(w, x, mu)

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
        return self.space_component.bc_operator(w, x, n, mu)

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
        """Compute the functional operator.

        Args:
            func: Callable representing the function
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor
            theta: Additional parameters tensor

        Returns:
            Functional operator tensor
        """
        # space operator
        grad_func = torch.func.jacrev(func, 1)
        space_op = -mu[0] * torch.func.jacrev(grad_func, 1)(t, x, mu, theta)
        # time operator
        time_op = torch.func.jacrev(func, 0)(t, x, mu, theta)
        return (time_op + space_op)[0, 0]

    # Neumann conditions
    def functional_operator_bc(
        self,
        func: VarArgCallable,
        t: torch.Tensor,
        x: torch.Tensor,
        n: torch.Tensor,
        mu: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Compute the functional operator for boundary conditions.

        Args:
            func: Callable representing the function
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor
            theta: Additional parameters tensor

        Returns:
            Functional operator tensor for boundary conditions
        """
        grad_u = torch.func.jacrev(func, 1)(t, x, mu, theta)
        return (grad_u * n)[0]

    def functional_operator_ic(
        self,
        func: VarArgCallable,
        x: torch.Tensor,
        mu: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Compute the functional operator for initial conditions.

        Args:
            func: Callable representing the function
            x: Spatial coordinate tensor
            mu: Parameter tensor
            theta: Additional parameters tensor

        Returns:
            Functional operator tensor for initial conditions
        """
        t = torch.zeros_like(x)
        return func(t, x, mu, theta)


class HeatEquation1DDirichletStrongForm(FirstOrderTemporalPDE):
    r"""Implementation of a 1D heat equation with Dirichlet BCs in strong form.

    Args:
        space: The approximation space for the problem
        init: Callable for the initial condition
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
        self.space_component = Laplacian1DDirichletStrongForm(space, f, g)
        self.f = f
        self.g = g
        self.init = init

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
        return self.space_component.operator(w, x, mu)

    # Rémi: time_operator is already in FirstOrderTemporalPDE!
    # def time_operator(
    #     self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    # ) -> Tensor:
    #     return self.grad(w.get_components(), t)

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
        return self.space_component.bc_operator(w, x, n, mu)

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
        """Compute the functional operator.

        Args:
            func: Callable representing the function
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor
            theta: Additional parameters tensor

        Returns:
            Functional operator tensor
        """
        # space operator
        grad_func = torch.func.jacrev(func, 1)
        space_op = -mu[0] * torch.func.jacrev(grad_func, 1)(t, x, mu, theta)
        # time operator
        time_op = torch.func.jacrev(func, 0)(t, x, mu, theta)
        return (time_op + space_op)[0, 0]

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
        """Compute the functional operator for boundary conditions.

        Args:
            func: Callable representing the function
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor
            theta: Additional parameters tensor

        Returns:
            Functional operator tensor for boundary conditions
        """
        return func(t, x, mu, theta)

    def functional_operator_ic(
        self,
        func: VarArgCallable,
        x: torch.Tensor,
        mu: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Compute the functional operator for initial conditions.

        Args:
            func: Callable representing the function
            x: Spatial coordinate tensor
            mu: Parameter tensor
            theta: Additional parameters tensor

        Returns:
            Functional operator tensor for initial conditions
        """
        t = torch.zeros_like(x)
        return func(t, x, mu, theta)


class HeatEquation2DStrongForm(FirstOrderTemporalPDE):
    r"""Implementation of a 2D Laplacian problem with Dirichlet BCs in strong form.

    Args:
        space: The approximation space for the problem
        init: Callable for the initial condition
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
        self.space_component = Laplacian2DDirichletStrongForm(space, f, g)
        self.f = f
        self.g = g
        self.init = init

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
        return self.space_component.operator(w, x, mu)

    # Rémi: time_operator is already in FirstOrderTemporalPDE!
    # def time_operator(
    #     self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    # ) -> Tensor:
    #     return self.grad(w.get_components(), t)

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
        return self.space_component.bc_operator(w, x, n, mu)

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


class HeatEquation2DStrongFormImplicit(FirstOrderTemporalPDE):
    r"""2D heat equation for implicit discrete_pinns.

    Args:
        space: the approx. space.
        init: the rhs of the initial condition.
        f: the rhs of the residual.
        g: the rhs of the boundary condition.
        **kwargs: Additional keyword arguments.
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
        self.space_component = Laplacian2DDirichletStrongForm(space, f, g)
        self.f = f
        self.g = g
        self.init = init

        self.dt = kwargs.get("dt", 1e-3)
        self.alpha = kwargs.get("alpha", 1.0)

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
        return self.space_component.operator(w, x, mu)

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
        return self.space_component.bc_operator(w, x, n, mu)

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
        # t: LabelTensor,
        x: torch.Tensor,
        mu: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Compute the functional operator.

        Args:
            func: Callable representing the function
            x: Spatial coordinate tensor
            mu: Parameter tensor
            theta: Additional parameters tensor

        Returns:
            Functional operator tensor
        """
        # space operator
        grad_func = torch.func.jacrev(func, 0)
        space_op = -mu[0] * torch.func.jacrev(grad_func, 0)(x, mu, theta)
        return func(x, mu, theta) - self.alpha * self.dt * space_op[0, 0]

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
        """Compute the functional operator for boundary conditions.

        Args:
            func: Callable representing the function
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor
            theta: Additional parameters tensor

        Returns:
            Functional operator tensor for boundary conditions
        """
        return func(x, mu, theta)

    def functional_operator_ic(
        self,
        func: VarArgCallable,
        x: torch.Tensor,
        mu: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Compute the functional operator for initial conditions.

        Args:
            func: Callable representing the function
            x: Spatial coordinate tensor
            mu: Parameter tensor
            theta: Additional parameters tensor

        Returns:
            Functional operator tensor for initial conditions
        """
        return func(x, mu, theta)

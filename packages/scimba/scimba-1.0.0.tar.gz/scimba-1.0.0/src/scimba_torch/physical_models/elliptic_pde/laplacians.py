"""Laplacian operators in 1D and 2D."""

from typing import Callable

import torch

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.physical_models.elliptic_pde.abstract_elliptic_pde import (
    RitzFormEllipticPDE,
    StrongFormEllipticPDE,
)
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor
from scimba_torch.utils.typing_protocols import VarArgCallable


class Laplacian1DNeumannStrongForm(StrongFormEllipticPDE):
    """Implementation of a 1D Laplacian problem with Neumann BCs in strong form.

    Args:
        space: The approximation space for the problem.
        f: Callable representing the source term f(x, μ).
        g: Callable representing the Neumann boundary condition g(x, μ).
        **kwargs: Additional keyword arguments.
    """

    def __init__(self, space: AbstractApproxSpace, f: Callable, g: Callable, **kwargs):
        super().__init__(
            space, linear=True, residual_size=1, bc_residual_size=1, **kwargs
        )
        self.f = f
        self.g = g

    def rhs(self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        r"""Compute the right-hand side (RHS) of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
             The source term \( f(x, \mu) \).
        """
        return self.f(x, mu)

    def operator(
        self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the differential operator of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            The result of applying the operator to the state.
        """
        alpha = mu.get_components()
        u_x = self.grad(w, x)
        assert isinstance(u_x, torch.Tensor)
        u_xx = self.grad(u_x, x)
        assert isinstance(u_xx, torch.Tensor)
        assert isinstance(alpha, torch.Tensor)
        return -alpha * u_xx

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
            The boundary condition \( g(x, \mu) \).
        """
        return self.g(x, mu)

    def bc_operator(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the operator for the boundary conditions.

        Args:
            w: State tensor.
            x: Boundary coordinates tensor.
            n: Normal vector tensor.
            mu: Parameter tensor.

        Returns:
            The boundary operator applied to the state.
        """
        u = w.get_components()
        n_ = n.get_components()
        u_x = self.grad(u, x)
        return u_x * n_


class Laplacian1DDirichletStrongForm(StrongFormEllipticPDE):
    """Implementation of a 1D Laplacian problem with Dirichlet BCs in strong form.

    Args:
        space: The approximation space for the problem.
        f: Callable representing the source term f(x, μ).
        g: Callable representing the Dirichlet boundary condition g(x, μ).
        **kwargs: Additional keyword arguments.
    """

    def __init__(self, space: AbstractApproxSpace, f: Callable, g: Callable, **kwargs):
        super().__init__(
            space, linear=True, residual_size=1, bc_residual_size=1, **kwargs
        )
        self.f = f
        self.g = g

    def rhs(self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        """Compute the right-hand side (RHS) of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            The source term f(x, μ).
        """
        return self.f(x, mu)

    def operator(
        self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the differential operator of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            The result of applying the operator to the state.
        """
        u = w.get_components()
        alpha = mu.get_components()
        u_xx = self.grad(self.grad(u, x), x)
        return -alpha * u_xx

    def bc_rhs(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the RHS for the boundary conditions.

        Args:
            w: State tensor.
            x: Boundary coordinates tensor.
            n: Normal vector tensor.
            mu: Parameter tensor.

        Returns:
            The boundary condition g(x, μ).
        """
        return self.g(x, mu)

    def bc_operator(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the operator for the boundary conditions.

        Args:
            w: State tensor.
            x: Boundary coordinates tensor.
            n: Normal vector tensor.
            mu: Parameter tensor.

        Returns:
            The boundary operator applied to the state.
        """
        return w.get_components()


class Laplacian2DDirichletStrongForm(StrongFormEllipticPDE):
    """Implementation of a 2D Laplacian problem with Dirichlet BCs in strong form.

    Args:
        space: The approximation space for the problem.
        f: Callable representing the source term f(x, μ).
        g: Callable representing the Dirichlet boundary condition g(x, μ).
        **kwargs: Additional keyword arguments.
    """

    def __init__(self, space: AbstractApproxSpace, f: Callable, g: Callable, **kwargs):
        super().__init__(
            space, linear=True, residual_size=1, bc_residual_size=1, **kwargs
        )
        self.f = f
        self.g = g

    def rhs(self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        """Compute the right-hand side (RHS) of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            The source term f(x, μ).
        """
        return self.f(x, mu)

    def operator(
        self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the differential operator of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            The result of applying the operator to the state.
        """
        u = w.get_components()
        alpha = mu.get_components()
        u_x, u_y = self.grad(u, x)
        u_xx, _ = self.grad(u_x, x)
        _, u_yy = self.grad(u_y, x)
        return -alpha * (u_xx + u_yy)

    def bc_rhs(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the RHS for the boundary conditions.

        Args:
            w: State tensor.
            x: Boundary coordinates tensor.
            n: Normal vector tensor.
            mu: Parameter tensor.

        Returns:
            The boundary condition g(x, μ).
        """
        return self.g(x, mu)

    # Dirichlet condition
    def bc_operator(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the operator for the boundary conditions.

        Args:
            w: State tensor.
            x: Boundary coordinates tensor.
            n: Normal vector tensor.
            mu: Parameter tensor.

        Returns:
            The boundary operator applied to the state.
        """
        u = w.get_components()
        return u

    def functional_operator_bc(
        self,
        func: VarArgCallable,
        x: torch.Tensor,
        n: torch.Tensor,
        mu: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Apply the functional operator for boundary conditions.

        Args:
            func: The callable function to apply.
            x: Spatial coordinates tensor.
            n: Normal vector tensor.
            mu: Parameter tensor.
            theta: Theta parameter tensor.

        Returns:
            The result of applying the functional operator.
        """
        return func(x, mu, theta)

    def functional_operator(
        self,
        func: VarArgCallable,
        x: torch.Tensor,
        mu: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Apply the functional operator for the differential equation.

        Args:
            func: The callable function to apply.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.
            theta: Theta parameter tensor.

        Returns:
            The result of applying the functional operator.
        """
        grad_u = torch.func.jacrev(func, 0)
        hessian_u = torch.func.jacrev(grad_u, 0, chunk_size=None)(x, mu, theta)
        return -mu[0] * (hessian_u[..., 0, 0] + hessian_u[..., 1, 1])


class Laplacian2DDirichletRitzForm(RitzFormEllipticPDE):
    """Implementation of a 2D Laplacian problem with Dirichlet BCs in Ritz form.

    Args:
        space: The approximation space for the problem.
        f: Callable representing the source term f(x, μ).
        g: Callable representing the Dirichlet boundary condition g(x, μ).
        **kwargs: Additional keyword arguments.
    """

    def __init__(self, space: AbstractApproxSpace, f: Callable, g: Callable, **kwargs):
        super().__init__(space, bc_residual_size=1, **kwargs)
        self.f = f
        self.g = g

    def linearform(
        self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the linear form of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            The linear form result.
        """
        u = w.get_components()
        return self.f(x, mu) * u

    def quadraticform(
        self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the quadratic form of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            The quadratic form result.
        """
        u = w.get_components()
        alpha = mu.get_components()
        u_x, u_y = self.grad(u, x)
        return 0.5 * alpha * (u_x**2.0 + u_y**2.0)

    def energy_matrix(
        self, vals: dict, x: torch.Tensor, mu: torch.Tensor
    ) -> torch.Tensor:
        """Compute the energy matrix for the Ritz formulation.

        Args:
            vals: Dictionary containing precomputed values.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            The energy matrix.
        """
        N = x.shape[0]
        Phi = (vals["eval_and_gradx_and_gradtheta"]).squeeze()
        Phi2 = Phi * mu.view(-1, 1, 1)
        return torch.einsum("ijl,ikl->jk", Phi2, Phi) / N

    # def functional_bilinearform(
    #     self,
    #     u: VarArgCallable,
    #     v: VarArgCallable,
    #     x: torch.Tensor,
    #     mu: torch.Tensor,
    #     theta: torch.Tensor,
    # ) -> torch.Tensor:
    #     grad_u_x_mu_theta = torch.func.grad(u, 0)(x, mu, theta)
    #     grad_v_x_mu_theta = torch.func.grad(v, 0)(x, mu, theta)
    #     return (
    #         mu[0]
    #         * (
    #             grad_u_x_mu_theta[0] * grad_v_x_mu_theta[0]
    #             + grad_u_x_mu_theta[1] * grad_v_x_mu_theta[1]
    #         )[None]
    #     )

    def bc_rhs(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the RHS for the boundary conditions.

        Args:
            w: State tensor.
            x: Boundary coordinates tensor.
            n: Normal vector tensor.
            mu: Parameter tensor.

        Returns:
            The boundary condition g(x, μ).
        """
        return self.g(x, mu)

    # Dirichlet condition
    def bc_operator(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the operator for the boundary conditions.

        Args:
            w: State tensor.
            x: Boundary coordinates tensor.
            n: Normal vector tensor.
            mu: Parameter tensor.

        Returns:
            The boundary operator applied to the state.
        """
        u = w.get_components()
        return u

    def functional_operator_bc(
        self,
        func: VarArgCallable,
        x: torch.Tensor,
        n: torch.Tensor,
        mu: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Apply the functional operator for boundary conditions.

        Args:
            func: The callable function to apply.
            x: Spatial coordinates tensor.
            n: Normal vector tensor.
            mu: Parameter tensor.
            theta: Theta parameter tensor.

        Returns:
            The result of applying the functional operator.
        """
        return func(x, mu, theta)

"""General linear order-2 and specific PDEs of advection-reaction-diffusion problems."""

from typing import Callable, Generator

import torch

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor
from scimba_torch.utils.typing_protocols import VarArgCallable


def a_laplacian(spatial_dim: int) -> Callable[[torch.Tensor], torch.Tensor]:
    """Return the diffusion matrix function for the Laplacian operator.

    Args:
        spatial_dim: The spatial dimension of the problem.

    Returns:
        A function that takes a tensor of shape (N, spatial_dim) and returns a tensor
        of shape (N, spatial_dim, spatial_dim).
    """
    return lambda var: (
        torch.eye(
            spatial_dim,
            dtype=torch.get_default_dtype(),
            device=torch.get_default_device(),
        )[None, :, :]
    ).repeat([var.shape[0], 1, 1])


def b_laplacian(spatial_dim: int) -> Callable[[torch.Tensor], torch.Tensor]:
    """Return the advection vector function for the Laplacian operator.

    Args:
        spatial_dim: The spatial dimension of the problem.

    Returns:
        A function that takes a tensor of shape (N, spatial_dim) and returns a tensor
        of shape (N, spatial_dim).
    """
    return lambda var: (
        torch.zeros(
            (spatial_dim),
            dtype=torch.get_default_dtype(),
            device=torch.get_default_device(),
        )[None, :]
    ).repeat([var.shape[0], 1])


def c_laplacian() -> Callable[[torch.Tensor], torch.Tensor]:
    """Return the reaction coefficient function for the Laplacian operator.

    Returns:
        A function that takes a tensor of shape (N, spatial_dim) and returns a tensor
        of shape (N, 1).
    """
    return lambda var: (
        torch.tensor(
            0.0, dtype=torch.get_default_dtype(), device=torch.get_default_device()
        )[None]
    ).repeat([var.shape[0], 1])


def d_dirichlet() -> Callable[[torch.Tensor], torch.Tensor]:
    """Return the boundary reaction coefficient function for Dirichlet BCs.

    Returns:
        A function that takes a tensor of shape (N, spatial_dim) and returns a tensor
        of shape (N, 1).
    """
    return lambda var: (
        torch.tensor(
            1.0, dtype=torch.get_default_dtype(), device=torch.get_default_device()
        )[None]
    ).repeat([var.shape[0], 1])


def e_dirichlet() -> Callable[[torch.Tensor], torch.Tensor]:
    """Return the boundary diffusion coefficient function for Dirichlet BCs.

    Returns:
        A function that takes a tensor of shape (N, spatial_dim) and returns a tensor
        of shape (N, 1).
    """
    return lambda var: (
        torch.tensor(
            0.0, dtype=torch.get_default_dtype(), device=torch.get_default_device()
        )[None]
    ).repeat([var.shape[0], 1])


# Remi: not used
# def fd_Dirichlet() -> Callable[[torch.Tensor, torch.Tensor], torch.Tensor]:
#     return lambda var, label: (
#         torch.tensor(
#             1.0, dtype=torch.get_default_dtype(), device=torch.get_default_device()
#         )[None]
#     ).repeat([var.shape[0], 1])
#
#
# def fe_Dirichlet() -> Callable[[torch.Tensor, torch.Tensor], torch.Tensor]:
#     return lambda var, label: (
#         torch.tensor(
#             0.0, dtype=torch.get_default_dtype(), device=torch.get_default_device()
#         )[None]
#     ).repeat([var.shape[0], 1])


class LinearOrder2PDE:
    r"""General linear order-2 PDE over a subdomain :math:`\Omega \subset \mathbb{R}^d`.

    The equation is:

    .. math::
        \mu \left( -\operatorname{div}(A(x) \nabla u(x)) + \operatorname{div}(b(x) u(x))
          + c(x) u(x) \right) = f(x)

    for :math:`x` in the interior of :math:`\Omega`.

    On the boundary :math:`\partial\Omega`:

    .. math::
        e \left( A(x) \nabla u(x) \cdot n(x) \right) + d(x) u(x) = g(x)

    where:
        - :math:`u` is the unknown function,
        - :math:`f`, :math:`g` are given functions,
        - :math:`\mu \in \mathbb{R}` is a parameter,
        - :math:`A(x)` is a matrix in :math:`\mathbb{R}^{d \times d}` (diffusion),
        - :math:`b(x)` is a vector in :math:`\mathbb{R}^d` (advection),
        - :math:`c(x), d(x), e` are scalars (reaction, boundary coefficients),
        - :math:`n(x)` is the outward normal at :math:`x`,
        - :math:`\operatorname{div}` is the divergence operator,
        - :math:`\nabla` is the gradient operator,
        - :math:`\cdot` is the dot product.

    For instance:
        - Laplace equation with Dirichlet boundary: :math:`A(x) = I`, :math:`b(x) = 0`,
          :math:`c(x) = 0`, :math:`d(x) = 1`, :math:`e = 0`.
        - Neumann boundary: :math:`d(x) = 0`, :math:`e = 1`.

    Args:
        space: Approximation space used for the PDE.
        spatial_dim: Spatial dimension of the problem.
        f: Right-hand side function for the PDE.
        g: Right-hand side function for the boundary conditions.
        **kwargs: Additional keyword arguments for coefficients A, b, c, d, e.
    """

    # noqa: E501

    def __init__(
        self,
        space: AbstractApproxSpace,
        spatial_dim: int,
        f: Callable,
        g: Callable,
        **kwargs,
    ):
        #: Approximation space
        self.space: AbstractApproxSpace = space
        #: Spatial dimension
        self.spatial_dim: int = spatial_dim
        #: the A function
        self.A: Callable = kwargs.get("A", a_laplacian(self.spatial_dim))
        #: the b function
        self.b: Callable = kwargs.get("b", b_laplacian(self.spatial_dim))
        #: the c function
        self.c: Callable = kwargs.get("c", c_laplacian())
        #: the d function
        self.d: Callable = kwargs.get("d", d_dirichlet())
        #: the e coefficient
        self.e: float = kwargs.get("e", e_dirichlet())
        # self.fd = kwargs.get("fd", fd_Dirichlet())
        # self.fe = kwargs.get("fe", fe_Dirichlet())
        #: the right-hand side function for the PDE
        self.f: Callable = f
        #: the right-hand side function for the boundary conditions
        self.g: Callable = g

        self.linear = True
        self.residual_size = 1
        self.bc_residual_size = 1

    def grad(
        self,
        w: torch.Tensor | MultiLabelTensor,
        y: torch.Tensor | LabelTensor,
    ) -> torch.Tensor | Generator[torch.Tensor, None, None]:
        r"""Compute the gradient of the tensor `w` with respect to the tensor `y`.

        Args:
            w: Input tensor
            y: Tensor with respect to which the gradient is computed

        Returns:
            Gradient tensor
        """
        return self.space.grad(w, y)

    def rhs(self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        r"""Compute the right-hand side (RHS) of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            torch.Tensor: The source term \( f(x, \mu) \).
        """
        return self.f(x, mu)

    def bc_rhs(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> LabelTensor:
        r"""Compute the RHS for the boundary conditions.

        Args:
            w: State tensor.
            x: Boundary coordinates tensor.
            n: Normal vector tensor.
            mu: Parameter tensor.

        Returns:
            torch.Tensor: The boundary condition \( g(x, \mu) \).
        """
        return self.g(x, mu)

    def operator(
        self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        r"""Compute the differential operator of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            torch.Tensor: The result of applying the operator to the
            state.
        """
        u = w.get_components()
        alpha = mu.get_components()
        assert isinstance(u, torch.Tensor)
        assert isinstance(alpha, torch.Tensor)

        if self.spatial_dim == 1:
            A = self.A(x).squeeze()
            b = self.b(x).squeeze()
            c = self.c(x).squeeze()
            u = u.squeeze()
            alpha = alpha.squeeze()

            c_u = c * u
            b_u = b * u
            div_b_u = self.grad(b_u, x)
            assert isinstance(div_b_u, torch.Tensor)
            div_b_u = div_b_u.squeeze()
            grad_u = self.grad(u, x)
            assert isinstance(grad_u, torch.Tensor)
            grad_u = grad_u.squeeze()
            A_grad_u = A * grad_u
            div_A_grad_u = self.grad(A_grad_u, x)
            assert isinstance(div_A_grad_u, torch.Tensor)
            div_A_grad_u = div_A_grad_u.squeeze()

            return (-alpha * (div_A_grad_u - div_b_u - c_u))[..., None]

        A = self.A(x)
        b = self.b(x)
        c = self.c(x)

        c_u = c * u
        b_u = b * u
        div_b_u = tuple(self.grad(b_u[:, 0], x))[0]
        for i in range(1, self.spatial_dim):
            div_b_u += tuple(self.grad(b_u[:, i], x))[i]

        grad_u = torch.cat(tuple(self.grad(u, x)), dim=-1)
        A_grad_u = torch.matmul(A, grad_u[..., None]).squeeze()

        div_A_grad_u = tuple(self.grad(A_grad_u[:, 0], x))[0]
        for i in range(1, self.spatial_dim):
            div_A_grad_u += tuple(self.grad(A_grad_u[:, i], x))[i]

        assert isinstance(div_A_grad_u, torch.Tensor)

        return -alpha * (div_A_grad_u - div_b_u - c_u)

    # def functional_operator(
    #     self,
    #     func: VarArgCallable,
    #     x: torch.Tensor,
    #     mu: torch.Tensor,
    #     theta: torch.Tensor,
    # ) -> torch.Tensor:
    #
    #     A = self.A(x[None, ...])[
    #         0
    #     ]  # tensor of shape (self.spatial_dim, self.spatial_dim)
    #     b = self.b(x[None, ...])[0]  # tensor of shape (self.spatial_dim)
    #     c = self.c(x[None, ...])[0, 0]  # tensor of shape ()
    #
    #     c_ux = c * func(x, mu, theta)
    #
    #     grad_u = torch.func.grad(func, 0)
    #
    #     def mmm(func, b, i):
    #         return lambda *args: b[i] * func(*args)
    #
    #     div_b_u = torch.func.grad(mmm(func, b, 0), 0)(x, mu, theta)[0]
    #     for i in range(1, self.spatial_dim):
    #         div_b_u += torch.func.grad(mmm(func, b, i), 0)(x, mu, theta)[i]
    #
    #     def mm2(func, A, i):
    #         return lambda *args: (A @ func(*args))[i]
    #
    #     div_A_grad_u = torch.func.grad(mm2(grad_u, A, 0), 0)(x, mu, theta)[0]
    #     for i in range(1, self.spatial_dim):
    #         div_A_grad_u += torch.func.grad(mm2(grad_u, A, i), 0)(x, mu, theta)[i]
    #
    #     return (-mu[0] * (-c_ux - div_b_u + div_A_grad_u))[None]

    def functional_operator(
        self,
        func: VarArgCallable,
        x: torch.Tensor,
        mu: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Compute the differential operator of the PDE using functional programming.

        Args:
            func: Function representing the state.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.
            theta: Additional parameters for the function.

        Returns:
            The result of applying the operator to the state.
        """
        A = self.A(x[None, ...])[
            0
        ]  # tensor of shape (self.spatial_dim, self.spatial_dim)
        b = self.b(x[None, ...])[0]  # tensor of shape (self.spatial_dim)
        c = self.c(x[None, ...])[0, 0]  # tensor of shape ()

        c_ux = c * func(x, mu, theta)

        # print("func.shape: ", func(x, mu, theta).shape)

        grad_u = torch.func.jacrev(func, 0)
        # print("grad_u.shape: ", grad_u(x, mu, theta).shape)

        # def mmm(func, b, i):
        #     return lambda *args: b[i] * func(*args)
        #
        # print("func.shape: ", func(x, mu, theta).shape)
        # print("mmm(func).shape: ", mmm(func, b, 0)(x, mu, theta).shape)
        #
        # div_b_u2 = torch.func.jacrev(mmm(func, b, 0))(x, mu, theta)[...,0]
        # # print("div_b_u.shape: ", div_b_u.shape)
        # for i in range(1, self.spatial_dim):
        #     div_b_u2 = div_b_u2 +\
        #         torch.func.jacrev(mmm(func, b, i))(x, mu, theta)[...,i]
        # print("div_b_u2.shape: ", div_b_u2.shape)

        def mul(func, b):
            return lambda *args: b * func(*args)

        # print("func.shape: ", func(x, mu, theta).shape)
        # print("mul(func).shape: ", mul(func, b)(x, mu, theta).shape)

        # print(torch.func.jacrev(mul(func, b))(x, mu, theta).shape)
        div_b_u = torch.einsum("ii", torch.func.jacrev(mul(func, b), 0)(x, mu, theta))[
            None
        ]
        # print("div_b_u.shape: ", div_b_u.shape)

        # assert torch.allclose(div_b_u, div_b_u2)

        # print("A[None,...].shape: ", A[None,...].shape)
        # def mm2(func, A, i):
        #     return lambda *args: (torch.einsum("ij,bj->bi", A, func(*args)))[..., i]
        #
        # div_A_grad_u = torch.func.jacrev(mm2(grad_u, A, 0), 0)(x, mu, theta)[..., 0]
        #
        # for i in range(1, self.spatial_dim):
        #     div_A_grad_u = div_A_grad_u + torch.func.jacrev(mm2(grad_u, A, i), 0)(x,
        #          mu, theta)[...,i]
        #
        # print("div_A_grad_u.shape: ", div_A_grad_u.shape)

        def mul2(func, a):
            return lambda *args: (torch.einsum("ij,bj->bi", a, func(*args)))

        # print(torch.func.jacrev(mul2(grad_u, A), 0)(x, mu, theta).shape)
        div_A_grad_u = torch.einsum(
            "bii->b", torch.func.jacrev(mul2(grad_u, A), 0)(x, mu, theta)
        )
        # print("div_A_grad_u.shape: ", div_A_grad_u.shape)

        return -mu[0] * (-c_ux - div_b_u + div_A_grad_u)

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

        if self.spatial_dim == 1:
            A = self.A(x).squeeze()
            u = u.squeeze()

            grad_u = self.grad(u, x)
            assert isinstance(grad_u, torch.Tensor)
            grad_u = grad_u.squeeze()
            A_grad_u = A * grad_u
            A_grad_u_dot_n = A_grad_u * n.x.squeeze()

            d = self.d(x).squeeze()
            e = self.e(x).squeeze()

            return (e * A_grad_u_dot_n + d * u)[..., None]

        A = self.A(x)
        # print("A.shape :", A.shape)
        grad_u = torch.cat(tuple(self.grad(u, x)), dim=-1)
        # print("grad_u.shape :", grad_u.shape)
        A_grad_u = torch.matmul(A, grad_u[..., None]).squeeze()
        # print("A_grad_u.shape :", A_grad_u.shape)
        # print("n.x.shape :", n.x.shape)
        A_grad_u_dot_n = torch.matmul(A_grad_u[:, None, :], n.x[..., None]).squeeze(-1)
        # print("A_grad_u_dot_n.shape :", A_grad_u_dot_n.shape)
        d = self.d(x)
        e = self.e(x)
        return e * A_grad_u_dot_n + d * u

    # def functional_operator_bc(
    #     self,
    #     func: VarArgCallable,
    #     x: torch.Tensor,
    #     n: torch.Tensor,
    #     mu: torch.Tensor,
    #     # label: torch.Tensor,
    #     theta: torch.Tensor,
    # ) -> torch.Tensor:
    #     # return func(x, mu, theta)
    #     A = self.A(x[None, ...])[0]
    #     # print("A.shape :", A.shape)
    #     grad_u = torch.func.grad(func, 0)(x, mu, theta)
    #     # print("grad_u.shape :", grad_u.shape)
    #     A_grad_u = torch.matmul(A, grad_u[..., None]).squeeze()
    #     # print("A_grad_u.shape :", A_grad_u.shape)
    #     # print("n.shape :", n.shape)
    #     if self.spatial_dim == 1:
    #         A_grad_u = A_grad_u[..., None]
    #     A_grad_u_dot_n = torch.matmul(A_grad_u[None, :], n[..., None]).squeeze()
    #     # print("A_grad_u_dot_n.shape :", A_grad_u_dot_n.shape)
    #     # d = self.fd(x[None, ...], label)[0, 0]
    #     d = self.d(x[None, ...])[0, 0]
    #     # e = self.fe(x[None, ...], label)[0, 0]
    #     e = self.e(x[None, ...])[0, 0]
    #     return (e * A_grad_u_dot_n + d * func(x, mu, theta))[None]

    def functional_operator_bc(
        self,
        func: VarArgCallable,
        x: torch.Tensor,
        n: torch.Tensor,
        mu: torch.Tensor,
        # label: torch.Tensor,
        theta: torch.Tensor,
    ) -> torch.Tensor:
        """Compute the boundary operator using functional programming.

        Args:
            func: Function representing the state.
            x: Boundary coordinates tensor.
            n: Normal vector tensor.
            mu: Parameter tensor.
            theta: Additional parameters for the function.

        Returns:
            The boundary operator applied to the state.
        """
        # return func(x, mu, theta)
        A = self.A(x[None, ...])[0]
        # print("A.shape :", A.shape)
        grad_u = torch.func.jacrev(func, 0)(x, mu, theta)
        # print("grad_u.shape :", grad_u.shape)
        A_grad_u = torch.matmul(A, grad_u[..., None]).squeeze()
        # print("A_grad_u.shape :", A_grad_u.shape)
        # print("n.shape :", n.shape)
        if self.spatial_dim == 1:
            A_grad_u = A_grad_u[..., None]
        A_grad_u_dot_n = torch.matmul(A_grad_u[None, :], n[..., None]).squeeze()
        # print("A_grad_u_dot_n.shape :", A_grad_u_dot_n.shape)
        d = self.d(x[None, ...])[0, 0]
        e = self.e(x[None, ...])[0, 0]
        return e * A_grad_u_dot_n + d * func(x, mu, theta)


class DivAGradUPDE(LinearOrder2PDE):
    r"""Diffusion-only PDE over a subdomain :math:`\Omega \subset \mathbb{R}^d`.

    The equation is:

    .. math::
        \mu \left( -\operatorname{div}(A(x) \nabla u(x)) \right) = f(x)

    for :math:`x` in the interior of :math:`\Omega`.

    On the boundary :math:`\partial\Omega`:

    .. math::
        e \left( A(x) \nabla u(x) \cdot n(x) \right) + d(x) u(x) = g(x)

    where:
        - :math:`u` is the unknown function,
        - :math:`f`, :math:`g` are given functions,
        - :math:`\mu \in \mathbb{R}` is a parameter,
        - :math:`A(x)` is a matrix in :math:`\mathbb{R}^{d \times d}` (diffusion),
        - :math:`d(x), e` are scalars (boundary coefficients),
        - :math:`n(x)` is the outward normal at :math:`x`,
        - :math:`\operatorname{div}` is the divergence operator,
        - :math:`\nabla` is the gradient operator,
        - :math:`\cdot` is the dot product.

    For instance:
        - Laplace equation with Dirichlet boundary: :math:`A(x) = I`, :math:`d(x) = 1`,
          :math:`e = 0`.
        - Neumann boundary: :math:`d(x) = 0`, :math:`e = 1`.

    Args:
        space: Approximation space used for the PDE.
        spatial_dim: Spatial dimension of the problem.
        f: Right-hand side function for the PDE.
        g: Right-hand side function for the boundary conditions.
        **kwargs: Additional keyword arguments for coefficients A, d, e.

    Raises:
        KeyError: If 'b' or 'c' are provided in kwargs, as they are not used in this
            model.
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        spatial_dim: int,
        f: Callable,
        g: Callable,
        **kwargs,
    ):
        if ("b" in kwargs) or ("c" in kwargs):
            raise KeyError("not possible to create a %s object with b or c args")

        super().__init__(space, spatial_dim, f, g, **kwargs)

    def linearform(
        self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        r"""Compute the right-hand side (RHS) of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            The source term \( f(x, \mu) \).
        """
        u = w.get_components()
        return self.f(x, mu) * u

    def quadraticform(
        self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        r"""Compute the differential operator of the PDE.

        Args:
            w: State tensor.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            torch.Tensor: The result of applying the operator to the
            state.
        """
        u = w.get_components()
        alpha = mu.get_components()

        if self.spatial_dim == 1:
            A = self.A(x).squeeze()
            u = u.squeeze()
            alpha = alpha.squeeze()
            grad_u = self.grad(u, x).squeeze()
            A_grad_u = A * grad_u
            A_grad_u_dot_grad_u = A_grad_u * grad_u
            return (0.5 * alpha * A_grad_u_dot_grad_u)[..., None]

        A = self.A(x)
        grad_u = torch.cat(tuple(self.grad(u, x)), dim=-1)
        A_grad_u = torch.matmul(A, grad_u[..., None]).squeeze()
        A_grad_u_dot_grad_u = torch.matmul(
            A_grad_u[..., None, :], grad_u[..., None]
        ).squeeze(-1)
        return 0.5 * alpha * A_grad_u_dot_grad_u

    def energy_matrix(
        self, vals: dict, x: torch.Tensor, mu: torch.Tensor
    ) -> torch.Tensor:
        """Compute the energy matrix.

        Args:
            vals: A dictionary containing precomputed values, including the
                evaluation of the function and its gradients.
            x: Spatial coordinates tensor.
            mu: Parameter tensor.

        Returns:
            The energy matrix.
        """
        N = x.shape[0]
        grad_u = (vals["eval_and_gradx_and_gradtheta"]).squeeze()
        if self.spatial_dim == 1:
            grad_u = grad_u[..., None]
        A = self.A(x)
        # print("A.shape: ", A.shape)
        # print("grad_u.shape: ", grad_u.shape)
        A_grad_u = torch.einsum("ijk,ilk->ilj", A, grad_u)
        mu_A_grad_u = A_grad_u * mu.view(-1, 1, 1)
        return torch.einsum("ijl,ikl->jk", mu_A_grad_u, grad_u) / N

    # def functional_operator_bc(
    #     self,
    #     func: VarArgCallable,
    #     x: torch.Tensor,
    #     n: torch.Tensor,
    #     mu: torch.Tensor,
    #     # label: torch.Tensor,
    #     theta: torch.Tensor,
    # ) -> torch.Tensor:
    #     # return func(x, mu, theta)
    #     A = self.A(x[None, ...])[0]
    #     # print("A.shape :", A.shape)
    #     grad_u = torch.func.jacrev(func, 0)(x, mu, theta)
    #     # print("grad_u.shape :", grad_u.shape)
    #     A_grad_u = torch.matmul(A, grad_u[..., None]).squeeze()
    #     # print("A_grad_u.shape :", A_grad_u.shape)
    #     # print("n.shape :", n.shape)
    #     if self.spatial_dim == 1:
    #         A_grad_u = A_grad_u[..., None]
    #     A_grad_u_dot_n = torch.matmul(A_grad_u[None, :], n[..., None]).squeeze()
    #     # print("A_grad_u_dot_n.shape :", A_grad_u_dot_n.shape)
    #     # d = self.fd(x[None, ...], label)[0, 0]
    #     d = self.d(x[None, ...])[0, 0]
    #     # e = self.fe(x[None, ...], label)[0, 0]
    #     e = self.e(x[None, ...])[0, 0]
    #     return (e * A_grad_u_dot_n + d * func(x, mu, theta))[None]

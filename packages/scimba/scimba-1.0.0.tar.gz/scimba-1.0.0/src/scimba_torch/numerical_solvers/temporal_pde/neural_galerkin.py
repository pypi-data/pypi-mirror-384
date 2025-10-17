"""Neural Galerkin method for time-dependent PDEs."""

import copy

import torch

from scimba_torch.numerical_solvers.temporal_pde.time_discrete import (
    ExplicitTimeDiscreteScheme,
    TimeDiscreteCollocationProjector,
)
from scimba_torch.physical_models.temporal_pde.abstract_temporal_pde import TemporalPDE
from scimba_torch.utils.scimba_tensors import LabelTensor
from scimba_torch.utils.verbosity import get_verbosity


class NeuralGalerkin(ExplicitTimeDiscreteScheme):
    """Implementation of the Neural Galerkin method for time-dependent PDEs.

    Args:
        pde: The temporal PDE to be solved.
        projector: The time discrete collocation projector.
        scheme: The time integration scheme to use ('euler_exp', 'rk2', 'rk4').
        **kwargs: Additional keyword arguments.
    """

    def __init__(
        self,
        pde: TemporalPDE,
        projector: TimeDiscreteCollocationProjector,
        scheme: str = "euler_exp",
        **kwargs,
    ):
        super().__init__(pde, projector, **kwargs)

        self.scheme = scheme
        assert scheme in ["euler_exp", "rk2", "rk4"], "Unknown scheme in NeuralGalerkin"

        self.nb_params = self.pde.space.ndof

        self.ls_bool = kwargs.get("ls_bool", False)

        self.N = kwargs.get("n_collocation", 2000)

        self.m_jac: torch.Tensor | None = None
        self.M: torch.Tensor | None = None
        self.f: torch.Tensor | None = None

        self.matrix_regularization = kwargs.get("matrix_regularization", 1e-5)

        if self.ls_bool:
            self.inner_update = self.inner_update_lstsq
        else:
            self.inner_update = self.inner_update_matrix

        self.subsample = kwargs.get("subsample", False)
        # if subsample is activated, the ratio of subsampling
        # 0.25 means that 25% of the parameters evolve at each time step

        self.subsample_ratio = kwargs.get("subsample_ratio", 0.5)
        assert 0 < self.subsample_ratio <= 1, (
            "subsample_ratio should be between 0 and 1"
        )

        if not self.subsample:
            self.S_t = torch.arange(self.nb_params)

        else:
            self.subsample_size = int(self.subsample_ratio * self.nb_params)

        if get_verbosity():
            print("/////////////// Neural Galerkin method ///////////////")
            print(f"///// Time scheme: {self.scheme}")
            print(f"///// The model used: {self.nb_params} parameters")

    def sampling(self):
        """Call the sampling function of the two samplers.

        Save the number of points.
        """
        self.x, self.mu = self.pde.space.integrator.sample(self.N)
        self.x_no_grad = copy.deepcopy(self.x)
        self.x_no_grad.requires_grad = False
        self.mu_no_grad = copy.deepcopy(self.mu)
        self.mu_no_grad.requires_grad = False

    def compute_model(self, t: float):
        r"""Compute the mass matrix and the RHS of the Neural Galerkin method.

        Computes:

        .. math::

            M(\theta) &= \frac{1}{N} \sum (J(\theta) \otimes J(\theta))(x,mu) \\
            F(\theta) &= \frac{1}{N} \sum (J(\theta) * f(\theta))(x,mu)

        Args:
            t: Current time.
        """
        self.m_jac = self.pde.space.jacobian(self.x_no_grad, self.mu_no_grad)

        eye_matrix = self.matrix_regularization * torch.eye(self.nb_params)

        self.jac_mt = self.m_jac.transpose(1, 2)

        if not self.ls_bool:
            self.M = (
                torch.einsum("bjs,bjr->sr", self.jac_mt, self.jac_mt) / self.N
                + eye_matrix
            )

        large_f = self.residual(t, self.x, self.mu)

        if not self.ls_bool:
            self.f = torch.einsum("bij,bi->j", self.jac_mt, large_f) / self.N
        else:
            self.f = large_f

    def residual(self, t: float, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        """This function computes the PDE residual and concatenates it, if needed.

        Args:
            t: Current time.
            x: Spatial points where the residual is computed.
            mu: Parameter points where the residual is computed.

        Returns:
            The residual tensor.

        Raises:
            ValueError: If the residual is neither a tensor nor a tuple of tensors.
        """
        t_ = LabelTensor(t * torch.ones((self.N, 1)))

        u_theta = self.pde.space.evaluate(x, mu)

        space_term = self.pde.space_operator(u_theta, t_, x, mu)
        rhs_term = self.pde.rhs(u_theta, t_, x, mu)

        residual = -space_term + rhs_term

        if isinstance(residual, torch.Tensor):
            return residual
        elif isinstance(residual, tuple):
            return torch.cat(residual, axis=1)
        else:
            raise ValueError("residual should be a tensor or a tuple of tensors")

    def inner_update_lstsq(self, t: float) -> torch.Tensor:
        r"""Computes the update of the parameters :math:`\theta_n`.

        Uses a least squares solver, based on the Jacobian J and the RHS f.

        Args:
            t: Current time.

        Returns:
            The update of the parameters :math:`\theta_n`.
        """
        self.compute_model(t)

        assert isinstance(self.jac_mt, torch.Tensor), (
            "inner_update_lstsq called with jac_mt being None"
        )
        assert isinstance(self.f, torch.Tensor), (
            "inner_update_lstsq called with f being None"
        )

        J = torch.squeeze(self.jac_mt)[:, self.S_t]
        b = torch.squeeze(self.f)

        return torch.linalg.lstsq(J, b).solution

    def inner_update_matrix(self, t: float) -> torch.Tensor:
        r"""Compute the update of the parameters :math:`\theta_n`.

        Based on the mass matrix :math:`M = J^T J` and the RHS :math:`F = J^T f`.

        Args:
            t: Current time.

        Returns:
            The update of the parameters :math:`\theta_n`.
        """
        self.compute_model(t)

        assert isinstance(self.M, torch.Tensor), (
            "inner_update_matrix called with M being None"
        )
        assert isinstance(self.f, torch.Tensor), (
            "inner_update_matrix called with f being None"
        )

        b = self.f.flatten()[self.S_t]
        self.M = self.M[:, self.S_t][self.S_t, :]

        return torch.linalg.solve(self.M, b)

    def inner_rk_step(
        self,
        t: float,
        dt: float | list[float],
        k: torch.Tensor | list[torch.Tensor] | None = None,
    ) -> torch.Tensor:
        r"""Compute the n-th step of the Runge-Kutta method.

        Computes:

        .. math::

            k_n = f(\theta_n + \Delta t \sum_{i=1}^{n-1} a_{n,i} k_i)

        Args:
            t: Current time.
            dt: Time step multiplied by the coefficients :math:`a_{n,i}`. If dt or k are
                not lists, they are converted to lists.
            k: list of :math:`k_i`. If dt or k are not lists, they are converted to
                lists.

        Returns:
            The value of the new :math:`k_n` based on the new parameters.

        Note:
            If :math:`dt = 0`, computes :math:`f(\theta_n)`. Otherwise, k should not be
            `None`, to be multiplied to dt.
        """
        # if dt = 0, computes f(θ_n)
        if dt == 0:
            return self.inner_update(t)

        # otherwise, k should not be none, to be multiplied to dt
        assert k is not None, "k should be provided if dt is not 0"

        # if dt or k are not lists, they are converted to lists
        if not isinstance(dt, list):
            dt = [dt]
        if not isinstance(k, list):
            k = [k]

        assert len(dt) == len(k), "dt and k should have the same length"

        theta_new = self.theta_n_full.clone()
        theta_new[self.S_t] = self.theta_n + sum([dt_ * k_ for dt_, k_ in zip(dt, k)])

        # theta_new = self.theta + sum([dt_ * k_ for dt_, k_ in zip(dt, k)])
        self.pde.space.set_dof(theta_new, flag_scope="all")

        # returns the value of the new k_n based on the new parameters
        return self.inner_update(t)

    def update(self, t: float, dt: float, **kwargs):
        """Computes the next time step of the Neural Galerkin method.

        Args:
            t: Current time.
            dt: Time step.
            **kwargs: Additional keyword arguments.
        """
        self.sampling()

        self.list_theta: list[torch.Tensor] = []

        self.theta = self.pde.space.get_dof(flag_scope="all", flag_format="tensor")
        assert isinstance(self.theta, torch.Tensor)
        self.list_theta.append(self.theta)

        self.theta_n_full = self.list_theta[-1]
        self.theta_n = self.theta_n_full[self.S_t]

        if self.scheme == "euler_exp":
            k1 = self.inner_rk_step(t, 0)
            self.theta[self.S_t] = self.theta_n + dt * k1

        elif self.scheme == "rk2":
            k1 = self.inner_rk_step(t, 0)
            k2 = self.inner_rk_step(t, dt, k1)
            self.theta[self.S_t] = self.theta_n + dt / 2 * (k1 + k2)

        elif self.scheme == "rk4":
            k1 = self.inner_rk_step(t, 0)
            k2 = self.inner_rk_step(t, 0.5 * dt, k1)
            k3 = self.inner_rk_step(t, 0.5 * dt, k2)
            k4 = self.inner_rk_step(t, dt, k3)
            self.theta[self.S_t] = self.theta_n + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)

        self.pde.space.set_dof(self.theta, flag_scope="all")
        self.list_theta.append(self.theta)

"""Implement a discrete PINN for solving temporal PDEs."""

import copy
import math
from typing import Callable

import torch

from scimba_torch.numerical_solvers.temporal_pde.time_discrete import (
    ExplicitTimeDiscreteScheme,
    TimeDiscreteCollocationProjector,
)
from scimba_torch.physical_models.kinetic_pde.abstract_kinetic_pde import KineticPDE
from scimba_torch.physical_models.temporal_pde.abstract_temporal_pde import TemporalPDE
from scimba_torch.utils.scimba_tensors import LabelTensor

TYPE_ARG = LabelTensor
TYPE_FUNC_RES = (
    Callable[[TYPE_ARG, TYPE_ARG], torch.Tensor]
    | Callable[[TYPE_ARG, TYPE_ARG, TYPE_ARG], torch.Tensor]
)
TYPE_FUNC_BC_RES = (
    Callable[[TYPE_ARG, TYPE_ARG, TYPE_ARG], torch.Tensor]
    | Callable[[TYPE_ARG, TYPE_ARG, TYPE_ARG, TYPE_ARG], torch.Tensor]
)
TYPE_PDES = TemporalPDE | KineticPDE


class DiscretePINN(ExplicitTimeDiscreteScheme):
    """A discrete PINN for solving a differential equation.

    It uses linear and/or nonlinear spaces.

    The class supports initialization of the model with a target function,
    computation of the right-hand side (RHS) from the model, and stepping through time
    using a projector.

    Args:
        pde: The PDE model, which can be either a TemporalPDE or KineticPDE.
        projector: The projector for training the model, typically a
            TimeDiscreteCollocationProjector.
        scheme: The time scheme used for updating the model. Options include
            "euler_exp", "rk2", and "rk4".
        **kwargs: Additional hyperparameters for the scheme.


    Attributes:
        model (nn.Module): The neural network model used for computing the solution.
        projector (ProjectorPINNs): The projector used for training the model.
        scheme (str): The time scheme used for updating the model.
    """

    def __init__(
        self,
        pde: TYPE_PDES,
        projector: TimeDiscreteCollocationProjector,
        scheme: str = "euler_exp",
        **kwargs,
    ):
        super().__init__(pde, projector, **kwargs)
        self.scheme = scheme

        assert scheme in ["euler_exp", "rk2", "rk4"], "Unknown scheme in DiscretePINN"

    def construct_rhs_ee(self, pde_n: TYPE_PDES, t: float, dt: float) -> TYPE_FUNC_RES:
        r"""Returns :math:`u_n + \Delta t f(u_n)` as a function.

        Args:
            pde_n: The PDE model at the current time step.
            t: The current time.
            dt: The time step size.

        Returns:
            A function representing the right-hand side (RHS) for the explicit Euler
            scheme.
        """
        if isinstance(pde_n, TemporalPDE):

            def res_temporal_pde(x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, mu)
                f_u_n = pde_n.space_operator(u_n, t_, x, mu)
                s_u_n = pde_n.rhs(u_n, t_, x, mu)
                return (u_n.w - dt * f_u_n + dt * s_u_n).detach()

            return res_temporal_pde

        else:

            def res_kinetic_pde(
                x: LabelTensor, v: LabelTensor, mu: LabelTensor
            ) -> torch.Tensor:
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, v, mu)
                f_u_n = pde_n.space_operator(u_n, t_, x, v, mu)
                s_u_n = pde_n.rhs(u_n, t_, x, v, mu)
                return (u_n.w - dt * f_u_n + dt * s_u_n).detach()

            return res_kinetic_pde

    def construct_rhs_ee_weak_bc(
        self, pde_n: TYPE_PDES, t: float, dt: float
    ) -> tuple[TYPE_FUNC_RES, TYPE_FUNC_BC_RES]:
        r"""Returns :math:`u_n + \Delta t f(u_n)` as a function.

        Args:
            pde_n: The PDE model at the current time step.
            t: The current time.
            dt: The time step size.

        Returns:
            A tuple containing two functions: one for the right-hand side (RHS) and
            another for the boundary condition (BC) residuals for the explicit Euler
            scheme with weak boundary conditions.
        """
        if isinstance(pde_n, TemporalPDE):

            def res_temporal_pde(x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, mu)
                f_u_n = pde_n.space_operator(u_n, t_, x, mu)
                s_u_n = pde_n.rhs(u_n, t_, x, mu)
                return (u_n.w - dt * f_u_n + dt * s_u_n).detach()

            def bc_res_temporal_pde(
                x: LabelTensor, n: LabelTensor, mu: LabelTensor
            ) -> torch.Tensor:
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, mu)
                s_u_n = pde_n.bc_rhs(u_n, t_, x, n, mu)
                return s_u_n.detach()  ## car on va mininiser u-  bc_res

            return res_temporal_pde, bc_res_temporal_pde

        else:

            def res_kinetic_pde(
                x: LabelTensor, v: LabelTensor, mu: LabelTensor
            ) -> torch.Tensor:
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, v, mu)
                f_u_n = pde_n.space_operator(u_n, t_, x, v, mu)
                s_u_n = pde_n.rhs(u_n, t_, x, v, mu)
                return (u_n.w - dt * f_u_n + dt * s_u_n).detach()

            def bc_res_kinetic_pde(
                x: LabelTensor, v: LabelTensor, n: LabelTensor, mu: LabelTensor
            ) -> torch.Tensor:
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, v, mu)
                s_u_n = pde_n.bc_rhs(u_n, t_, x, v, n, mu)
                return s_u_n.detach()

            return res_kinetic_pde, bc_res_kinetic_pde

    def construct_rhs_rk2(
        self, pde_n: TYPE_PDES, pde_nph: TYPE_PDES, t: float, dt: float
    ) -> TYPE_FUNC_RES:
        r"""Returns :math:`u_n + \Delta t f(u_n)` as a function.

        Args:
            pde_n: The PDE model at the current time step.
            pde_nph: The PDE model at the next half time step.
            t: The current time.
            dt: The time step size.

        Returns:
            A function representing the right-hand side (RHS) for the second-order
            Runge-Kutta (RK2) scheme.
        """
        if isinstance(pde_n, TemporalPDE):
            assert isinstance(pde_nph, TemporalPDE)

            def res_temporal_pde(x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, mu)
                u_nph = pde_nph.space.evaluate(x, mu)
                f_u_nph = pde_nph.space_operator(u_nph, t_, x, mu)
                s_u_nph = pde_nph.rhs(u_n, t_, x, mu)
                return (u_n.w - dt * f_u_nph + dt * s_u_nph).detach()

            return res_temporal_pde

        else:
            assert isinstance(pde_nph, KineticPDE)

            def res_kinetic_pde(
                x: LabelTensor, v: LabelTensor, mu: LabelTensor
            ) -> torch.Tensor:
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, v, mu)
                u_nph = pde_nph.space.evaluate(x, v, mu)
                f_u_nph = pde_nph.space_operator(u_nph, t_, x, v, mu)
                s_u_nph = pde_nph.rhs(u_n, t_, x, v, mu)
                return (u_n.w - dt * f_u_nph + dt * s_u_nph).detach()

            return res_kinetic_pde

    def construct_rhs_rk2_weak_bc(
        self, pde_n: TYPE_PDES, pde_nph: TYPE_PDES, t: float, dt: float
    ) -> tuple[TYPE_FUNC_RES, TYPE_FUNC_BC_RES]:
        r"""Returns :math:`u_n + \Delta t f(u_n)` as a function.

        Args:
            pde_n: The PDE model at the current time step.
            pde_nph: The PDE model at the next half time step.
            t: The current time.
            dt: The time step size.

        Returns:
            A tuple containing two functions: one for the right-hand side (RHS) and
            another for the boundary condition (BC) residuals for the second-order
            Runge-Kutta (RK2) scheme with weak boundary conditions.
        """
        if isinstance(pde_n, TemporalPDE):
            assert isinstance(pde_nph, TemporalPDE)

            def res_temporal_pde(x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, mu)
                u_nph = pde_nph.space.evaluate(x, mu)
                f_u_nph = pde_nph.space_operator(u_nph, t_, x, mu)
                s_u_nph = pde_nph.rhs(u_n, t_, x, mu)
                return (u_n.w - dt * f_u_nph + dt * s_u_nph).detach()

            def bc_res_temporal_pde(
                x: LabelTensor, n: LabelTensor, mu: LabelTensor
            ) -> torch.Tensor:
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_nph = pde_nph.space.evaluate(x, mu)
                s_u_nph = pde_nph.bc_rhs(u_nph, t_, x, n, mu)
                return s_u_nph.detach()  ## car on va mininiser u-  bc_res

            return res_temporal_pde, bc_res_temporal_pde

        else:
            assert isinstance(pde_nph, KineticPDE)

            def res_kinetic_pde(
                x: LabelTensor, v: LabelTensor, mu: LabelTensor
            ) -> torch.Tensor:
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, v, mu)
                u_nph = pde_nph.space.evaluate(x, v, mu)
                f_u_nph = pde_nph.space_operator(u_nph, t_, x, v, mu)
                s_u_nph = pde_nph.rhs(u_n, t_, x, v, mu)
                return (u_n.w - dt * f_u_nph + dt * s_u_nph).detach()

            def bc_res_kinetic_pde(
                x: LabelTensor, v: LabelTensor, n: LabelTensor, mu: LabelTensor
            ) -> torch.Tensor:
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_nph = pde_nph.space.evaluate(x, v, mu)
                s_u_nph = pde_n.bc_rhs(u_nph, t_, x, v, n, mu)
                return s_u_nph.detach()  ## car on va mininiser u-  bc_res

            return res_kinetic_pde, bc_res_kinetic_pde

    def construct_rhs_rk4(
        self,
        pde_n: TYPE_PDES,
        pde_1: TYPE_PDES,
        pde_2: TYPE_PDES,
        pde_3: TYPE_PDES,
        t: float,
        dt: float,
    ) -> TYPE_FUNC_RES:
        r"""Returns :math:`u_n + \Delta t f(u_n)` as a function.

        Args:
            pde_n: The PDE model at the current time step.
            pde_1: The PDE model at the first intermediate step.
            pde_2: The PDE model at the second intermediate step.
            pde_3: The PDE model at the third intermediate step.
            t: The current time.
            dt: The time step size.

        Returns:
            A function representing the right-hand side (RHS) of the RK4 scheme.

        Raises:
            NotImplementedError: If the PDE models are not of type TemporalPDE, as RK4
                is not implemented for KineticPDE.
        """
        if isinstance(pde_n, TemporalPDE):
            assert isinstance(pde_1, TemporalPDE)
            assert isinstance(pde_2, TemporalPDE)
            assert isinstance(pde_3, TemporalPDE)

            def res_temporal_pde(x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, mu)
                u_1 = pde_1.space.evaluate(x, mu)
                u_2 = pde_2.space.evaluate(x, mu)
                u_3 = pde_3.space.evaluate(x, mu)
                f_u_3 = pde_3.space_operator(u_3, t_, x, mu)
                s_u_3 = pde_3.rhs(u_n, t_, x, mu)
                u_ = (-u_n.w + u_1.w + 2 * u_2.w + u_3.w) / 3
                return (u_ - dt * f_u_3 + dt * s_u_3).detach()

            return res_temporal_pde

        else:
            raise NotImplementedError(
                "construct_rhs_RK4 not implemented for KineticPDE"
            )

    def update(self, t: float, dt: float, **kwargs):
        r"""Compute the new parameters :math:`\theta_{n+1}` from :math:`\theta_n`.

        Uses the time step dt and the chosen time scheme.

        Args:
            t: The current time.
            dt: The time step size.
            **kwargs: Additional arguments for the projector's solve method.

        Raises:
            NotImplementedError: If the RK4 scheme is chosen with weak boundary
                conditions, as it is not implemented.
        """
        self.projector.best_loss = 1e10
        pde_n = copy.deepcopy(self.pde)

        if self.scheme == "euler_exp":
            if self.bool_weak_bc:
                self.projector.rhs, self.projector.bc_rhs = (
                    self.construct_rhs_ee_weak_bc(pde_n, t, dt)
                )
            else:
                self.projector.rhs = self.construct_rhs_ee(pde_n, t, dt)
            self.projector.solve(**kwargs)

        elif self.scheme == "rk2":
            if self.bool_weak_bc:
                self.projector.rhs, self.projector.bc_rhs = (
                    self.construct_rhs_ee_weak_bc(pde_n, t, dt / 2)
                )
            else:
                self.projector.rhs = self.construct_rhs_ee(pde_n, t, dt / 2)
            self.projector.solve(**kwargs)

            self.projector.best_loss = 1e10
            pde_nph = copy.deepcopy(self.pde)

            if self.bool_weak_bc:
                self.projector.rhs, self.projector.bc_rhs = (
                    self.construct_rhs_rk2_weak_bc(pde_n, pde_nph, t + dt / 2, dt)
                )
            else:
                self.projector.rhs = self.construct_rhs_rk2(
                    pde_n, pde_nph, t + dt / 2, dt
                )
            self.projector.solve(**kwargs)

        elif self.scheme == "rk4":
            if self.bool_weak_bc:
                raise NotImplementedError("RK4 not implemented for weak BC conditions")

            self.projector.rhs = self.construct_rhs_ee(pde_n, t, dt / 2)
            self.projector.solve(**kwargs)

            self.projector.best_loss = 1e10
            pde_1 = copy.deepcopy(self.pde)

            self.projector.rhs = self.construct_rhs_rk2(
                pde_n, pde_1, t + dt / 2, dt / 2
            )
            self.projector.solve(**kwargs)

            self.projector.best_loss = 1e10
            pde_2 = copy.deepcopy(self.pde)

            self.projector.rhs = self.construct_rhs_rk2(pde_n, pde_2, t + dt / 2, dt)
            self.projector.solve(**kwargs)

            self.projector.best_loss = 1e10
            pde_3 = copy.deepcopy(self.pde)

            self.projector.rhs = self.construct_rhs_rk4(
                pde_n, pde_1, pde_2, pde_3, t + dt, dt / 6
            )
            self.projector.solve(**kwargs)


class DiscretePINNImplicit(DiscretePINN):
    """Feature-branch DiscretePINN_Implicit that extends the base DiscretePINN.

    This subclass keeps all base behaviour (explicit schemes) and adds implicit
    schemes (Euler-imp, Crank–Nicolson, SDIRK2) using an extra PDE instance `pde_imp`
    and a `type_scheme` switch.

    Args:
        pde: The PDE model, which can be either a TemporalPDE or KineticPDE.
        pde_imp: The PDE for implicit scheme.
        projector: The projector for training the model, typically a
            TimeDiscreteCollocationProjector.
        type_scheme: a switch explicit/implicit.
        scheme: The time scheme used for updating the model. Options include
            "euler_exp", "rk2", and "rk4".
        **kwargs: Additional hyperparameters for the scheme.

    Raises:
            ValueError: If the time_scheme is not implicit or explicit.

    """

    def __init__(
        self,
        pde: TYPE_PDES,
        pde_imp: TYPE_PDES,
        projector: TimeDiscreteCollocationProjector,
        type_scheme: str = "implicit",
        scheme: str = "euler_imp",
        **kwargs,
    ):
        super().__init__(pde, projector, scheme="euler_exp", **kwargs)
        self.type_scheme = type_scheme
        self.scheme = scheme
        self.pde_imp = pde_imp

        self.gamma_sdirk2 = 1.0 - 1.0 / math.sqrt(2.0)

        if type_scheme == "explicit":
            assert scheme in ["euler_exp", "rk2", "rk4"], (
                f"Unknown explicit scheme: {scheme}"
            )
        elif type_scheme == "implicit":
            assert scheme in ["euler_imp", "crank_nicolson", "sdirk2"], (
                f"Unknown implicit scheme: {scheme}"
            )
        else:
            raise ValueError(f"Unknown type_scheme: {type_scheme}")

    def construct_rhs_ei(self, pde_n: TYPE_PDES, t: float, dt: float) -> TYPE_FUNC_RES:
        r"""Construct the right-hand side of the implicit Euler scheme.

        Returns `u_n + \Delta t \, S(u_n)` as a function,
        corresponding to the right-hand side (RHS) of the implicit Euler scheme.

        Args:
            pde_n: The PDE model at the current time step.
            t: The current time.
            dt: The time step size.

        Returns:
            A function representing the right-hand side (RHS) for the implicit Euler
            scheme, where `S(u_n)` denotes the source or reaction term of the PDE.
        """
        if isinstance(pde_n, TemporalPDE):

            def res_temporal_pde(x, mu):
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, mu)
                s_un = pde_n.rhs(u_n, t_, x, mu)
                return (u_n.w + dt * s_un).detach()

            return res_temporal_pde

        else:

            def res_kinetic_pde(x, mu, v):
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, mu, v)
                s_un = pde_n.rhs(u_n, t_, x, v, mu)
                return (u_n.w + dt * s_un).detach()

            return res_kinetic_pde

    def construct_lhs_ei(
        self, pde_np1: TYPE_PDES, t: float, dt: float
    ) -> TYPE_FUNC_RES:
        r"""Construct the left-hand side of the implicit Euler scheme.

        Returns `u_{n+1} - \Delta t \, F(u_{n+1})` as a function,
        corresponding to the left-hand side (LHS) of the implicit Euler scheme.

        Args:
            pde_np1: The PDE model evaluated at the next time step :math:`t_{n+1}`.
            t: The current time.
            dt: The time step size.

        Returns:
            A function representing the left-hand side (LHS) for the implicit Euler
            scheme, where `F(u_{n+1})` denotes the spatial operator of the PDE.
        """
        if isinstance(pde_np1, TemporalPDE):

            def res_temporal_pde(x, mu, with_last_layer: bool = True):
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_np1 = pde_np1.space.evaluate(x, mu, with_last_layer=with_last_layer)
                f_u_np1 = pde_np1.space_operator(u_np1, t_, x, mu)
                # s_u_np1 = pde_np1.rhs(u_np1, t_, x, mu)
                return u_np1.w + dt * f_u_np1

            return res_temporal_pde

        else:

            def res_kinetic_pde(x, mu, v, with_last_layer: bool = True):
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_np1 = pde_np1.space.evaluate(
                    x, mu, v, with_last_layer=with_last_layer
                )
                f_u_np1 = pde_np1.space_operator(u_np1, t_, x, v, mu)
                # s_u_np1 = pde_np1.rhs(u_np1, t_, x, v, mu)
                return u_np1.w + dt * f_u_np1

        return res_kinetic_pde

    def construct_rhs_cn(self, pde_n: TYPE_PDES, t: float, dt: float) -> TYPE_FUNC_RES:
        r"""Construct the right-hand side of the Crank–Nicolson scheme.

        Returns `u^n - \tfrac{1}{2} \Delta t \, (F(u^n) + S(u^n))` as a function,
        corresponding to the right-hand side (RHS) of the Crank–Nicolson scheme.

        Args:
            pde_n: The PDE model at the current time step.
            t: The current time.
            dt: The time step size.

        Returns:
            A function representing the right-hand side (RHS) for the Crank–Nicolson
            scheme, combining both the spatial operator `F(u^n)` and the source
            term `S(u^n)` evaluated at the current time step.
        """
        if isinstance(pde_n, TemporalPDE):

            def res_temporal_pde(x, mu):
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, mu)
                f_u_n = pde_n.space_operator(u_n, t_, x, mu)
                s_u_n = pde_n.rhs(u_n, t_, x, mu)
                return (u_n.w - 0.5 * dt * f_u_n - 0.5 * dt * s_u_n).detach()

            return res_temporal_pde

        else:

            def res_kinetic_pde(x, mu, v):
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, mu, v)
                f_u_n = pde_n.space_operator(u_n, t_, x, v, mu)
                s_u_n = pde_n.rhs(u_n, t_, x, v, mu)
                return (u_n.w - 0.5 * dt * f_u_n - 0.5 * dt * s_u_n).detach()

            return res_kinetic_pde

    def construct_lhs_cn(
        self, pde_np1: TYPE_PDES, t: float, dt: float
    ) -> TYPE_FUNC_RES:
        r"""Construct the left-hand side of the Crank–Nicolson scheme.

        Returns `u^{n+1} + \tfrac{1}{2} \Delta t \, (F(u^{n+1}) - S(u^{n+1}))`
            as a function, corresponding to the left-hand side (LHS)
            of the Crank–Nicolson scheme.

        Args:
            pde_np1: The PDE model evaluated at the next time step `t_{n+1}`.
            t: The current time.
            dt: The time step size.

        Returns:
            A function representing the left-hand side (LHS) for the Crank–Nicolson
            scheme, where `F(u^{n+1})` and `S(u^{n+1})` denote respectively
            the spatial operator and the source term of the PDE, both evaluated at the
            next time step.
        """
        if isinstance(pde_np1, TemporalPDE):

            def res_temporal_pde(x, mu, with_last_layer: bool = True):
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_np1 = pde_np1.space.evaluate(x, mu, with_last_layer=with_last_layer)
                f_u_np1 = pde_np1.space_operator(u_np1, t_, x, mu)
                s_u_np1 = pde_np1.rhs(u_np1, t_, x, mu)
                return u_np1.w + 0.5 * dt * f_u_np1 - 0.5 * dt * s_u_np1

            return res_temporal_pde

        else:

            def res_kinetic_pde(x, mu, v, with_last_layer: bool = True):
                t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
                u_np1 = pde_np1.space.evaluate(
                    x, mu, v, with_last_layer=with_last_layer
                )
                f_u_np1 = pde_np1.space_operator(u_np1, t_, x, v, mu)
                s_u_np1 = pde_np1.rhs(u_np1, t_, x, v, mu)
                return u_np1.w + 0.5 * dt * f_u_np1 - 0.5 * dt * s_u_np1

            return res_kinetic_pde

    def construct_rhs_sdirk2_step1(
        self, pde_n: TYPE_PDES, t: float, dt: float
    ) -> TYPE_FUNC_RES:
        r"""Construct the right-hand side of the first stage of the SDIRK2 scheme.

        Returns `u^n` as a function, corresponding to the right-hand side (RHS)
        of the first stage of the SDIRK2 scheme.

        Args:
            pde_n: The PDE model at the current time step.
            t: The current time.
            dt: The time step size.

        Returns:
            A function representing the RHS for the first stage of the SDIRK2 scheme,
            where the initial value :math:`u^n` is used as input for the implicit solve.
        """
        if isinstance(pde_n, TemporalPDE):

            def res_temporal_pde(x, mu):
                u_n = pde_n.space.evaluate(x, mu)
                return u_n.w.detach()

            return res_temporal_pde

        else:

            def res_kinetic_pde(x, mu, v):
                u_n = pde_n.space.evaluate(x, mu, v)
                return u_n.w.detach()

            return res_kinetic_pde

    def construct_lhs_sdirk2_step1(
        self, pde: TYPE_PDES, t: float, dt: float
    ) -> TYPE_FUNC_RES:
        r"""Construct the left-hand side of the first stage of the SDIRK2 scheme.

        Returns `u_1 - \Delta t \, \gamma \, (F(u_1) - S(u_1))` as a function,
        corresponding to the left-hand side (LHS) of the first stage
        of the SDIRK2 scheme.

        Args:
            pde: The PDE model evaluated at the first stage.
            t: The current time.
            dt: The time step size.

        Returns:
            A function representing the LHS for the first stage of the SDIRK2 scheme,
            where `\gamma` is the SDIRK2 coefficient and `F` and `S`
            denote respectively the spatial and source operators of the PDE.
        """
        t_stage = t + self.gamma_sdirk2 * dt

        if isinstance(pde, TemporalPDE):

            def res_temporal_pde(x, mu, with_last_layer: bool = True):
                t_ = LabelTensor(t_stage * torch.ones((x.shape[0], 1)))
                u1 = pde.space.evaluate(x, mu, with_last_layer=with_last_layer)
                f_u1 = pde.space_operator(u1, t_, x, mu)
                s_u1 = pde.rhs(u1, t_, x, mu)
                return (
                    u1.w + dt * self.gamma_sdirk2 * f_u1 - dt * self.gamma_sdirk2 * s_u1
                )

            return res_temporal_pde

        else:

            def res_kinetic_pde(x, mu, v, with_last_layer: bool = True):
                t_ = LabelTensor(t_stage * torch.ones((x.shape[0], 1)))
                u1 = pde.space.evaluate(x, mu, v, with_last_layer=with_last_layer)
                f_u1 = pde.space_operator(u1, t_, x, v, mu)
                s_u1 = pde.rhs(u1, t_, x, v, mu)
                return (
                    u1.w + dt * self.gamma_sdirk2 * f_u1 - dt * self.gamma_sdirk2 * s_u1
                )

            return res_kinetic_pde

    def construct_rhs_sdirk2_step2(
        self, pde_n: TYPE_PDES, u1_copy: TYPE_PDES, t: float, dt: float
    ) -> TYPE_FUNC_RES:
        r"""Construct the right-hand side of the second stage of the SDIRK2 scheme.

        Returns `u^n - \Delta t \, (1 - \gamma) \, (F(u_1) - S(u_1))` as a function,
        corresponding to the right-hand side (RHS) of the second stage
        of the SDIRK2 scheme.

        Args:
            pde_n: The PDE model at the current time step.
            u1_copy: The PDE model containing the intermediate stage solution `u_1`.
            t: The current time.
            dt: The time step size.

        Returns:
            A function representing the RHS for the second stage of the SDIRK2 scheme,
            using the already computed intermediate solution `u_1`.
        """
        t_stage = t + self.gamma_sdirk2 * dt

        if isinstance(pde_n, TemporalPDE):

            def res_temporal_pde(x, mu):
                t_ = LabelTensor(t_stage * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, mu)
                u1 = u1_copy.space.evaluate(x, mu)
                f_u1 = pde_n.space_operator(u1, t_, x, mu)
                s_u1 = pde_n.rhs(u1, t_, x, mu)
                return (
                    u_n.w
                    - dt * (1 - self.gamma_sdirk2) * f_u1
                    + dt * (1 - self.gamma_sdirk2) * s_u1
                ).detach()

            return res_temporal_pde

        else:

            def res_kinetic_pde(x, mu, v):
                t_ = LabelTensor(t_stage * torch.ones((x.shape[0], 1)))
                u_n = pde_n.space.evaluate(x, mu, v)
                u1 = u1_copy.space.evaluate(x, mu, v)
                f_u1 = pde_n.space_operator(u1, t_, x, v, mu)
                s_u1 = pde_n.rhs(u1, t_, x, v, mu)
                return (
                    u_n.w
                    - dt * (1 - self.gamma_sdirk2) * f_u1
                    + dt * (1 - self.gamma_sdirk2) * s_u1
                ).detach()

            return res_kinetic_pde

    def construct_lhs_sdirk2_step2(
        self, pde: TYPE_PDES, t: float, dt: float
    ) -> TYPE_FUNC_RES:
        r"""Construct the left-hand side of the second stage of the SDIRK2 scheme.

        Returns `u_2 - \Delta t \, \gamma \, (F(u_2) - S(u_2))` as a function,
        corresponding to the left-hand side (LHS) of the second stage
        of the SDIRK2 scheme.

        Args:
            pde: The PDE model evaluated at the second stage.
            t: The current time.
            dt: The time step size.

        Returns:
            A function representing the LHS for the second stage of the SDIRK2 scheme,
            where `\gamma` is the SDIRK2 coefficient and `F` and `S`
            denote respectively the spatial and source operators of the PDE.
        """
        t_stage = t + self.gamma_sdirk2 * dt

        if isinstance(pde, TemporalPDE):

            def res_temporal_pde(x, mu, with_last_layer: bool = True):
                t_ = LabelTensor(t_stage * torch.ones((x.shape[0], 1)))
                u2 = pde.space.evaluate(x, mu, with_last_layer=with_last_layer)
                f_u2 = pde.space_operator(u2, t_, x, mu)
                s_u2 = pde.rhs(u2, t_, x, mu)
                return (
                    u2.w + dt * self.gamma_sdirk2 * f_u2 - dt * self.gamma_sdirk2 * s_u2
                )

            return res_temporal_pde

        else:

            def res_kinetic_pde(x, mu, v, with_last_layer: bool = True):
                t_ = LabelTensor(t_stage * torch.ones((x.shape[0], 1)))
                u2 = pde.space.evaluate(x, mu, v, with_last_layer=with_last_layer)
                f_u2 = pde.space_operator(u2, t_, x, v, mu)
                s_u2 = pde.rhs(u2, t_, x, v, mu)
                return (
                    u2.w + dt * self.gamma_sdirk2 * f_u2 - dt * self.gamma_sdirk2 * s_u2
                )

            return res_kinetic_pde

    def update(self, t: float, dt: float, **kwargs):
        r"""Compute \theta_{n+1} from \theta_n.

        Compute the new parameters \theta_{n+1} from \theta_n
        using either explicit or implicit time schemes.

        Dispatches to : update (explicit) or update_implicit (implicit)
        depending on ``type_scheme``.

        Args:
            t: The current time.
            dt: The time step size.
            **kwargs: Additional arguments for the projector's ``solve`` method.

        Raises:
            ValueError: If ``type_scheme`` is neither ``explicit`` nor ``implicit``.
        """
        if self.type_scheme == "explicit":
            super().update(t, dt, **kwargs)
        elif self.type_scheme == "implicit":
            self.update_implicit(t, dt, **kwargs)
        else:
            raise ValueError(f"Unknown scheme_type: {self.type_scheme}")

    def update_implicit(self, t: float, dt: float, **kwargs):
        r"""Compute \theta_{n+1} from \theta_n for implicit schemes.

        Compute the new parameters `\theta_{n+1}` from `\theta_n`
        for implicit schemes, using self.pde_imp`.

        Uses the time step ``dt`` and the chosen implicit scheme.

        Args:
            t: The current time.
            dt: The time step size.
            **kwargs: Additional arguments for the projector's ``solve`` method.
        """
        self.projector.best_loss = 1e10

        pde_n = copy.deepcopy(self.pde_imp)
        pde_np1 = self.pde_imp

        if self.scheme == "euler_imp":
            self.projector.rhs = self.construct_rhs_ei(pde_n, t, dt)
            self.projector.lhs = self.construct_lhs_ei(pde_np1, t + dt, dt)
            self.projector.solve(**kwargs)

        elif self.scheme == "crank_nicolson":
            self.projector.rhs = self.construct_rhs_cn(pde_n, t, dt)
            self.projector.lhs = self.construct_lhs_cn(pde_np1, t + dt, dt)
            self.projector.solve(**kwargs)

        elif self.scheme == "sdirk2":
            self.projector.best_loss = 1e10
            pde_n = copy.deepcopy(self.pde_imp)

            self.projector.rhs = self.construct_rhs_sdirk2_step1(pde_n, t, dt)
            self.projector.lhs = self.construct_lhs_sdirk2_step1(self.pde_imp, t, dt)
            self.projector.solve(**kwargs)

            self.projector.best_loss = 1e10
            u1_copy = copy.deepcopy(self.pde_imp)

            self.projector.rhs = self.construct_rhs_sdirk2_step2(pde_n, u1_copy, t, dt)
            self.projector.lhs = self.construct_lhs_sdirk2_step2(self.pde_imp, t, dt)
            self.projector.solve(**kwargs)

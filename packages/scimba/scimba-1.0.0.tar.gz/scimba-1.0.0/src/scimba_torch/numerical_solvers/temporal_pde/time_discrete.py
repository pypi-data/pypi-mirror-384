"""Time-discrete numerical solvers for temporal PDEs."""

import copy
from abc import abstractmethod
from typing import Any, Callable, cast

import numpy as np
import torch

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.numerical_solvers.collocation_projector import (
    CollocationProjector,
)
from scimba_torch.numerical_solvers.preconditioner_pinns import (
    EnergyNaturalGradientPreconditioner,
)
from scimba_torch.numerical_solvers.preconditioner_projector import (
    AnagramPreconditionerProjector,
    EnergyNaturalGradientPreconditionerProjector,
)
from scimba_torch.optimizers.losses import GenericLosses
from scimba_torch.optimizers.optimizers_data import OptimizerData
from scimba_torch.physical_models.kinetic_pde.abstract_kinetic_pde import KineticPDE
from scimba_torch.physical_models.temporal_pde.abstract_temporal_pde import TemporalPDE
from scimba_torch.utils.scimba_tensors import LabelTensor


class TimeDiscreteCollocationProjector(CollocationProjector):
    """Implement the Galerkin-based nonlinear projection method.

    This subclass implements the `assembly` method to assemble the input and output
    tensors
    for a specific nonlinear projection problem using the Galerkin approach.
    It computes the approximation of a nonlinear problem by sampling collocation points
    and evaluating the corresponding function values.

    Args:
        pde: The PDE model to solve.
        **kwargs: Additional parameters for the projection, including collocation points
            and losses.
    """

    def __init__(
        self,
        pde: TemporalPDE | KineticPDE,
        **kwargs,
    ):
        self.pde = pde
        self.rhs: Callable = pde.rhs
        self.bc_rhs: Callable = pde.bc_rhs  # dummy assignment
        self.bool_weak_bc = kwargs.get("bool_weak_bc", False)
        self.bc_weight = kwargs.get("bc_weight", 10.0)

        def identity_lhs(space):
            def lhs(*args, with_last_layer: bool):
                u = space.evaluate(*args, with_last_layer=with_last_layer)
                return u.w

            return lhs

        self.lhs = identity_lhs(pde.space)

        super().__init__(pde.space, **kwargs)

        if self.type_projection == "L1":
            default_losses = (
                GenericLosses([("L1", torch.nn.L1Loss(), 1.0)])
                if (not self.bool_weak_bc)
                else GenericLosses(
                    [
                        ("L1", torch.nn.L1Loss(), 1.0),
                        ("bc", torch.nn.L1Loss(), self.bc_weight),
                    ]
                )
            )
        elif self.type_projection == "H1":
            default_losses = (
                GenericLosses(
                    [
                        ("L2", torch.nn.MSELoss(), 1.0),
                        ("L2 grad", torch.nn.MSELoss(), 0.1),
                    ],
                )
                if (not self.bool_weak_bc)
                else GenericLosses(
                    [
                        ("L2", torch.nn.MSELoss(), 1.0),
                        ("L2 grad", torch.nn.MSELoss(), 0.1),
                        ("L2 bc", torch.nn.MSELoss(), self.bc_weight),
                        ("L2 grad bc", torch.nn.MSELoss(), 0.1 * self.bc_weight),
                    ]
                )
            )
        else:  # Default is L2
            default_losses = (
                GenericLosses([("L2", torch.nn.MSELoss(), 1.0)])
                if (not self.bool_weak_bc)
                else GenericLosses(
                    [
                        ("L2", torch.nn.MSELoss(), 1.0),
                        ("L2 bc", torch.nn.MSELoss(), self.bc_weight),
                    ]
                )
            )
        self.losses = kwargs.get("losses", default_losses)

    def sample_all_vars(self, **kwargs: Any) -> tuple[LabelTensor, ...]:
        """Samples all variables required for the projection.

        Include the collocation and boundary points.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            A tuple containing sampled collocation points and boundary data.

        Raises:
            ValueError: If the approximation space type is not recognized.
        """
        n_collocation = kwargs.get("n_collocation", 1000)
        # if self.space.type_space == "space":
        #     x, mu = self.space.integrator.sample(n_collocation)
        #     data = (x, mu)
        # elif self.space.type_space == "phase_space":
        #     x, v, mu = self.space.integrator.sample(n_collocation)
        #     data = (x, v, mu)
        # else: # REMI: ??? should never happen?
        #     t, x, mu = self.space.integrator.sample(n_collocation)
        #     data = (t, x, mu)
        data = tuple(self.space.integrator.sample(n_collocation))

        if self.bool_weak_bc:
            n_bc_collocation = kwargs.get("n_bc_collocation", 1000)
            if self.space.type_space == "space":
                xnbc, mubc = self.space.integrator.bc_sample(
                    n_bc_collocation, index_bc=0
                )
                xbc, nbc = xnbc[0], xnbc[1]
                mubc = cast(LabelTensor, mubc)  # for the static typechecker...
                data = data + (xbc, nbc, mubc)
            elif self.space.type_space == "phase_space":
                # raise NotImplementedError("phase_space")
                xnbc, vbc, mubc = self.space.integrator.bc_sample(
                    n_bc_collocation, index_bc=0
                )
                xbc, nbc = xnbc[0], xnbc[1]
                mubc = cast(LabelTensor, mubc)  # for the static typechecker...
                data = data + (xbc, vbc, nbc, mubc)
            else:
                raise ValueError("space should be of type space or phase_space")
                # # raise NotImplementedError("time_space")
                # # REMI: ??? should never happen?
                # tbc, xnbc, mubc = self.space.integrator.bc_sample(
                #     n_bc_collocation, index_bc=1
                # )
                # xbc, nbc = xnbc[0], xnbc[1]
                # tbc = cast(LabelTensor, tbc)  # for the static typechecker...
                # mubc = cast(LabelTensor, mubc)  # for the static typechecker...
                # data = data + (tbc, xbc, nbc, mubc)
        return data

    def assembly_post_sampling(
        self, data: tuple[LabelTensor, ...], **kwargs
    ) -> tuple[tuple[torch.Tensor, ...], tuple[torch.Tensor, ...]]:
        """Assembles the I/Otensors for the nonlinear Galerkin projection problem.

        This method samples collocation points and evaluates the corresponding function
        values from the approximation space and the right-hand side of the problem.
        It then returns the tensors representing the inputs and outputs of the
        projection.

        Args:
            data: tuple containing sampled collocation points and boundary data.
            **kwargs: Additional keyword arguments.

        Returns:
            A tuple of tensors representing the inputs (u) and outputs (f) of the
            projection problem.

        Raises:
            ValueError: If the approximation space type is not recognized.
        """
        flag_scope = kwargs.get("flag_scope", "all")
        with_last_layer = True
        if flag_scope == "expect_last_layer":
            with_last_layer = False

        if self.space.type_space == "space":
            args = [data[0], data[1]]
        else:
            args = [data[0], data[1], data[2]]
        # u = self.space.evaluate(
        #     *args, with_last_layer=with_last_layer
        # )  # u is a multilabelTensor
        lhs = self.lhs(*args, with_last_layer=with_last_layer)
        f = self.rhs(*args)  # f is a Tensor
        left: tuple[torch.Tensor, ...] = (lhs,)
        right: tuple[torch.Tensor, ...] = (f,)

        if self.bool_weak_bc:
            if self.space.type_space == "space":
                # TODO give the good time vector? 0 is OK as far as operator does not
                # depend on t
                t_ = LabelTensor(0.0 * torch.ones((data[2].shape[0], 1)))
                args_for_space_evaluate = [data[2], data[4]]  # do not need the normals
                args_for_bc_operator = [
                    t_,
                    data[2],
                    data[3],
                    data[4],
                ]  # need the normals
                args_for_bc_rhs_evaluate = [
                    data[2],
                    data[3],
                    data[4],
                ]  # need the normals
            elif self.space.type_space == "phase_space":
                # raise NotImplementedError("phase_space")
                # TODO give the good time vector? 0 is OK as far as operator does not
                # depend on t
                t_ = LabelTensor(0.0 * torch.ones((data[3].shape[0], 1)))
                args_for_space_evaluate = [
                    data[3],
                    data[4],
                    data[6],
                ]  # do not need the normals
                args_for_bc_operator = [
                    t_,
                    data[3],
                    data[4],
                    data[5],
                    data[6],
                ]  # need the normals
                args_for_bc_rhs_evaluate = [
                    data[3],
                    data[4],
                    data[5],
                    data[6],
                ]  # need the normals
            else:
                raise ValueError("space should be of type space or phase_space")

            ub = self.space.evaluate(
                *args_for_space_evaluate, with_last_layer=with_last_layer
            )  # u is a multilabelTensor
            Lbc: torch.Tensor = self.pde.bc_operator(ub, *args_for_bc_operator)
            # REMI: consider adding the following, but this puts mess in type checking
            # if not with_last_layer: #Lbc is a tuple of b tensors (where b is the size
            # of the last hidden layer),
            #                         #should be a tensor
            #     Lbc =torch.concatenate( Lbc, dim=-1)
            fb = self.bc_rhs(*args_for_bc_rhs_evaluate)  # f is a Tensor
            left = (
                lhs,
                Lbc,
            )
            right = (
                f,
                fb,
            )
        return left, right


class TimeDiscreteNaturalGradientProjector(TimeDiscreteCollocationProjector):
    """A time-discrete natural gradient projector for solving temporal PDEs.

    Args:
        pde: The PDE model to solve.
        **kwargs: Additional parameters for the projection, including collocation points
            and losses.
    """

    def __init__(
        self,
        pde: TemporalPDE | KineticPDE,
        **kwargs,
    ):
        super().__init__(pde, **kwargs)

        self.default_lr: float = kwargs.get("default_lr", 1e-2)
        opt_1 = {
            "name": "sgd",
            "optimizer_args": {"lr": self.default_lr},
        }
        self.optimizer = OptimizerData(opt_1)
        self.bool_linesearch = True
        self.bool_preconditioner = True
        self.nb_epoch_preconditioner_computing = 1
        self.type_linesearch = kwargs.get("type_linesearch", "armijo")
        self.projection_data = {"nonlinear": True, "linear": False, "nb_step": 1}
        self.preconditioner = EnergyNaturalGradientPreconditionerProjector(
            pde.space, has_bc=self.bool_weak_bc, **kwargs
        )
        self.data_linesearch = kwargs.get("data_linesearch", {})
        self.data_linesearch.setdefault("M", 10)
        self.data_linesearch.setdefault("interval", [0.0, 2.0])
        self.data_linesearch.setdefault("log_basis", 2.0)
        self.data_linesearch.setdefault("n_step_max", 10)
        self.data_linesearch.setdefault(
            "alpha",
            0.01,
        )
        self.data_linesearch.setdefault(
            "beta",
            0.5,
        )


class TimeDiscreteImplicitNaturalGradientProjector(TimeDiscreteCollocationProjector):
    """A time-discrete natural gradient for solving temporal PDEs.

    Args:
        pde: The PDE model to solve.
        bc_type: The way the boundary condition is handled;
            "strong" for strongly, "weak" for weakly
        **kwargs: Additional parameters for the projection, including collocation points
            and losses.
    """

    def __init__(
        self,
        pde: TemporalPDE | KineticPDE,
        bc_type: str = "strong",
        **kwargs,
    ):
        super().__init__(pde, **kwargs)

        self.default_lr: float = kwargs.get("default_lr", 1e-2)
        opt_1 = {
            "name": "sgd",
            "optimizer_args": {"lr": self.default_lr},
        }
        self.optimizer = OptimizerData(opt_1)
        self.bool_linesearch = True
        self.bool_preconditioner = True
        self.nb_epoch_preconditioner_computing = 1
        self.type_linesearch = kwargs.get("type_linesearch", "armijo")
        self.projection_data = {"nonlinear": True, "linear": False, "nb_step": 1}
        self.preconditioner = EnergyNaturalGradientPreconditioner(
            pde.space,
            pde,
            is_operator_linear=pde.linear,
            has_bc=(bc_type == "weak"),
            **kwargs,
        )
        self.data_linesearch = kwargs.get("data_linesearch", {})
        self.data_linesearch.setdefault("M", 10)
        self.data_linesearch.setdefault("interval", [0.0, 2.0])
        self.data_linesearch.setdefault("log_basis", 2.0)
        self.data_linesearch.setdefault("nbMaxSteps", 10)
        self.data_linesearch.setdefault(
            "alpha",
            0.01,
        )
        self.data_linesearch.setdefault(
            "beta",
            0.5,
        )


class TimeDiscreteAnagramProjector(TimeDiscreteCollocationProjector):
    """A time-discrete natural gradient projector for solving temporal PDEs.

    Args:
        pde: The PDE model to solve.
        **kwargs: Additional parameters for the projection, including collocation points
            and losses.
    """

    def __init__(
        self,
        pde: TemporalPDE | KineticPDE,
        **kwargs,
    ):
        super().__init__(pde, **kwargs)

        self.default_lr: float = kwargs.get("default_lr", 1e-2)
        opt_1 = {
            "name": "sgd",
            "optimizer_args": {"lr": self.default_lr},
        }
        self.optimizer = OptimizerData(opt_1)
        self.bool_linesearch = True
        self.bool_preconditioner = True
        self.nb_epoch_preconditioner_computing = 1
        self.type_linesearch = kwargs.get("type_linesearch", "armijo")
        self.projection_data = {"nonlinear": True, "linear": False, "nb_step": 1}
        self.preconditioner = AnagramPreconditionerProjector(
            pde.space, has_bc=self.bool_weak_bc, **kwargs
        )
        self.data_linesearch = kwargs.get("data_linesearch", {})
        self.data_linesearch.setdefault("M", 10)
        self.data_linesearch.setdefault("interval", [0.0, 2.0])
        self.data_linesearch.setdefault("log_basis", 2.0)
        self.data_linesearch.setdefault("n_step_max", 10)
        self.data_linesearch.setdefault(
            "alpha",
            0.01,
        )
        self.data_linesearch.setdefault(
            "beta",
            0.5,
        )


class ExplicitTimeDiscreteScheme:
    """An explicit time-discrete scheme for solving a differential equation.

    Use linear and/or nonlinear spaces.

    The class supports initialization of the model with a target function, computation
    of the right-hand side (RHS)
    from the model, and stepping through time using a projector.

    Args:
        pde: The PDE model.
        projector: The projector for training the model.
        projector_init: The projector for initializing the model
            (if None, uses the same as projector).
        **kwargs: Additional hyperparameters for the scheme.
    """

    def __init__(
        self,
        pde: TemporalPDE | KineticPDE,
        projector: TimeDiscreteCollocationProjector,
        projector_init: TimeDiscreteCollocationProjector | None = None,
        **kwargs,
    ):
        self.pde = pde
        self.projector = projector
        if projector_init is None:
            self.projector_init = projector
        else:
            self.projector_init = projector_init

        self.initial_time: float = kwargs.get("initial_time", 0.0)
        self.initial_space: AbstractApproxSpace = copy.deepcopy(self.projector.space)
        self.saved_times: list[float] = []
        self.saved_spaces: list[AbstractApproxSpace] = []
        self.bool_weak_bc = kwargs.get("bool_weak_bc", False)

        self.final_time: float = kwargs.get("T", 0.1)

        if hasattr(pde, "exact_solution"):
            self.exact_solution = pde.exact_solution
        else:
            self.exact_solution = None

    def initialization(self, **kwargs: Any):
        """Initializes the model by projecting the initial condition onto the model.

        Args:
            **kwargs: Additional parameters for the initialization, such as the number
                of epochs and collocation points.
        """
        self.rhs = self.pde.initial_condition  # rhs is the initial condition
        self.projector_init.set_rhs(self.rhs)
        self.projector_init.solve(**kwargs)  # Use projector to fit the model

        if "initial_time" in kwargs:
            self.initial_time = kwargs["initial_time"]
        self.initial_space = copy.deepcopy(self.projector.space)

    @abstractmethod
    def update(self, t: float, dt: float, **kwargs):
        """Updates the model parameters using the time step and the chosen time scheme.

        Args:
            t: The current time.
            dt: The time step.
            **kwargs: Additional parameters for the update.
        """

    def compute_relative_error_in_time(
        self, t: float, n_error: int = 5_000
    ) -> list[float | torch.Tensor]:
        """Computes the relative error between the current and exact solution.

        Args:
            t: The time at which the error is computed.
            n_error: The number of points used for computing the error.
                Default is 5_000.

        Returns:
            list: The L1, L2, and Linf errors.
        """
        x, mu = self.pde.space.integrator.sample(n_error)
        u = self.pde.space.evaluate(x, mu)

        t_ = LabelTensor(t * torch.ones((x.shape[0], 1)))
        u_exact = self.exact_solution(t_, x, mu)
        error = u.w - u_exact

        # if relative := torch.min(torch.abs(u_exact)) > 1e-3:
        #     error = error / u_exact

        with torch.no_grad():
            L1_error = torch.mean(torch.abs(error))
            L2_error = torch.mean(error**2) ** 0.5
            Linf_error = torch.max(torch.abs(error))

        return [t, L1_error, L2_error, Linf_error]

    def solve(
        self,
        dt: float = 1e-5,
        final_time: float = 0.1,
        sol_exact: Callable | None = None,
        **kwargs,
    ):
        """Solves the full time-dependent problem, using time_step.

        Args:
            dt: The time step.
            final_time: The final time.
            sol_exact: The exact solution, if available.
            **kwargs: Additional parameters for the time-stepping, such as the number
                of epochs, collocation points, and options for saving and plotting.
        """
        self.nb_keep = kwargs.get("nb_keep", 1)
        inter_times = np.linspace(self.initial_time, final_time, self.nb_keep + 2)[1:-1]
        self.saved_times = []
        self.saved_spaces = []
        index_of_next_t_to_be_saved = 0

        self.final_time = final_time
        nt = 0
        time = self.initial_time

        save = kwargs.get("save", None)
        plot = kwargs.get("plot", None)
        additional_epochs_for_first_iteration = kwargs.get(
            "additional_epochs_for_first_iteration", 0
        )
        epochs = kwargs.get("epochs", 100)

        if self.exact_solution:
            self.list_errors = [self.compute_relative_error_in_time(0)]
            print(f"Time: {time}, L2 error: {self.list_errors[-1][2]:.3e}", flush=True)

        while time < final_time:
            if time + dt > final_time:
                dt = final_time - time
            if final_time - time - dt < 1e-16:
                dt = final_time - time

            if (nt == 0) and ("epochs" in kwargs):
                epochs += additional_epochs_for_first_iteration
                kwargs["epochs"] = epochs

            self.update(time, dt, **kwargs)

            if (nt == 0) and ("epochs" in kwargs):
                epochs -= additional_epochs_for_first_iteration
                kwargs["epochs"] = epochs

            time = time + dt

            nt = nt + 1

            if plot:
                assert hasattr(self.pde.space, "integrator")
                plot(
                    self.pde.space.evaluate,
                    self.pde.space.integrator.sample,
                    T=time,
                    iter=nt,
                )

            if save:
                self.projector.save(f"{nt}_{save}")

            if self.exact_solution:
                self.list_errors.append(self.compute_relative_error_in_time(time))
                print(
                    f"Time: {time}, L2 error: {self.list_errors[-1][2]:.3e}", flush=True
                )

            if (
                (time < final_time)
                and (index_of_next_t_to_be_saved < self.nb_keep)
                and (time >= inter_times[index_of_next_t_to_be_saved])
            ):
                self.saved_times.append(time)
                self.saved_spaces.append(copy.deepcopy(self.projector.space))
                index_of_next_t_to_be_saved += 1

            # if sol_exact is not None:
            #     error = self.compute_relative_error_in_time(time, sol_exact)
            #     self.errors.append(error)
            #     print(f"current iteration : {nt}, error: {error:.2e}")
            # else:
            #     print("current iteration :", nt)
            #     # self.list_err.append(err_abs)
            # nt = nt + 1

            if plot:
                assert hasattr(self.pde.space, "integrator")
                plot(
                    self.pde.space.evaluate,
                    self.pde.space.integrator.sample,
                    T=time,
                    iter=nt,
                )

            # self.times.append(time)

        if self.exact_solution:
            self.errors = torch.tensor(self.list_errors)

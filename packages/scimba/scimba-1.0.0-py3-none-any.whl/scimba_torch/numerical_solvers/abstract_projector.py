"""An abstract class for a nonlinear projector."""

import math
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable
from warnings import warn

import torch

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.numerical_solvers.abstract_preconditioner import (
    IdPreconditioner,
)
from scimba_torch.optimizers.line_search import (
    backtracking_armijo_line_search_with_loss_theta_grad_loss_theta,
    logarithmic_grid_line_search,
)
from scimba_torch.optimizers.losses import GenericLosses
from scimba_torch.optimizers.optimizers_data import OptimizerData
from scimba_torch.optimizers.scimba_optimizers import ScimbaSGD
from scimba_torch.utils.paths import (
    DEFAULT_PATH_FOR_SAVING,
    FOLDER_FOR_SAVED_PROJECTORS,
    get_filepath_for_save,
)
from scimba_torch.utils.scimba_tensors import LabelTensor
from scimba_torch.utils.verbosity import get_verbosity

RHS_FUNC_TYPE = Callable[..., torch.Tensor]


class AbstractNonlinearProjector(ABC):
    """Abstract class for a nonlinear projector.

    This class defines a nonlinear projector with various projection options
    and an optimization method. It is used to solve projection problems in a given
    approximation space, using optimization methods.

    Args:
        space: The approximation space where the projection will take place.
        rhs: The function representing the right-hand side of the problem.
        has_bc: Whether boundary conditions are present.
        **kwargs: Additional parameters, such as the type of projection, losses,
            and optimizers.
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        rhs: RHS_FUNC_TYPE | None,
        has_bc: bool = False,
        **kwargs,
    ):
        self.space: AbstractApproxSpace = (
            space  #: The approximation space where the projection takes place.
        )
        self.rhs: RHS_FUNC_TYPE | None = (
            rhs  #: The function representing the right-hand side of the problem.
        )

        self.type_projection: str = kwargs.get(
            "type_projection", "L2"
        )  #: The type of projection (default is "L2").

        assert self.type_projection in [
            "L1",
            "L2",
            "H1",
        ], "type_projection must be one of 'L1', 'L2', or 'H1'"

        self.nb_components = kwargs.get("nb_components", 1)
        # assert self.space.nb_unknowns == self.nb_components

        if self.type_projection == "L1":
            default_losses = GenericLosses(
                [
                    ("L1 %d" % i, torch.nn.L1Loss(), 1.0)
                    for i in range(self.nb_components)
                ]
            )

        elif self.type_projection == "H1":
            default_losses_list: list[
                tuple[str, Callable[[torch.Tensor, torch.Tensor], torch.Tensor], float]
            ] = (
                [("L2", torch.nn.MSELoss(), 1.0), ("L2 grad", torch.nn.MSELoss(), 0.1)]
                if (self.nb_components == 1)
                else [
                    ("L2 0", torch.nn.MSELoss(), 1.0),
                    ("L2 grad 0", torch.nn.MSELoss(), 0.1),
                ]
            )
            for i in range(1, self.nb_components):
                default_losses_list += [
                    ("L2 %d" % i, torch.nn.MSELoss(), 1.0),
                    ("L2 grad %d" % i, torch.nn.MSELoss(), 0.1),
                ]
            default_losses = GenericLosses(default_losses_list)

        else:  # Default is L2
            default_losses = GenericLosses(
                [
                    ("L2 %d" % i, torch.nn.MSELoss(), 1.0)
                    for i in range(self.nb_components)
                ]
            )

        self.losses: GenericLosses = kwargs.get(
            "losses", default_losses
        )  #: The losses to minimize during optimization.

        opt_1 = {
            "name": "adam",
            "optimizer_args": {"lr": 1e-2, "betas": (0.9, 0.999)},
        }
        default_opt = OptimizerData(opt_1)
        #: The optimizer used for parameter updates.
        self.optimizer: OptimizerData = kwargs.get("optimizers", default_opt)
        #: Whether to use line search during optimization.
        self.bool_linesearch: bool = kwargs.get("bool_linesearch", False)
        #: The type of line search to use.
        self.type_linesearch: str = kwargs.get("type_linesearch", "armijo")
        #: Parameters for line search.
        self.data_linesearch: dict = kwargs.get(
            "data_linesearch", {"alpha": 0.5, "beta": 0.5}
        )
        #: Data related to the projection process.
        self.projection_data: dict = kwargs.get(
            "projection_data",
            {"nonlinear": True, "linear": False, "nb_step": 1},
        )
        #: Default learning rate for the optimizer.
        self.default_lr: float = kwargs.get("default_lr", 1e-2)
        #: Ridge regularization parameter.
        self.ridge = kwargs.get("ridge_for_linear", 1e-3)
        #: Whether to use a preconditioner.
        self.bool_preconditioner = kwargs.get("bool_preconditioner", False)
        self.nb_epoch_preconditioner_computing = kwargs.get(
            "nb_epoch_preconditioner_computing", 1
        )  #: Number of epochs for computing the preconditioner.
        self.preconditioner = kwargs.get(
            "preconditioner", IdPreconditioner(space, **kwargs)
        )  #: The preconditioner used during optimization.
        self.best_loss = float("+Inf")  #: Best loss achieved during optimization.

        # Function to pass non-differentiable data from one epoch to the next
        self.create_quantities_for_loss = kwargs.get(
            "create_quantities_for_loss", lambda data: None
        )

    @abstractmethod
    def get_dof(
        self, flag_scope: str = "all", flag_format: str = "list"
    ) -> list | torch.Tensor:
        """Retrieves the degrees of freedom (DoF) of the approximation space.

        Args:
            flag_scope: Specifies the scope of the parameters to return.
                (Default value = "all")
            flag_format: The format for returning the parameters.
                (Default value = "list")

        Returns:
            The degrees of freedom in the specified format.
        """

    def get_gradient(self) -> torch.Tensor:
        """Retrieves the gradient of the parameters.

        Returns:
            The gradient of the parameters.

        Raises:
            RuntimeError: If no gradient is available.
        """
        grads = []
        for param in self.get_dof(flag_scope="all", flag_format="list"):
            if param.grad is None:
                raise RuntimeError(
                    "no gradient available; make sure they have already been calculated"
                )
            grads.append(param.grad.view(-1))
        return torch.cat(grads)

    def set_gradient(self, grads: torch.Tensor) -> None:
        """Sets the gradient of the parameters.

        Args:
            grads: The gradient values to set.

        Raises:
            RuntimeError: If no gradient is available.
        """
        offset = 0
        for param in self.get_dof(flag_scope="all", flag_format="list"):
            if param.grad is None:
                raise RuntimeError(
                    "no gradient available; make sure they have already been calculated"
                )
            num_params = param.numel()
            param.grad.copy_(grads[offset : offset + num_params].view(param.size()))
            offset += num_params

    def get_loss_grad_loss(
        self, data: None | tuple[LabelTensor, ...] = None, **kwargs
    ) -> tuple[
        Callable[[torch.Tensor], torch.Tensor], Callable[[torch.Tensor], torch.Tensor]
    ]:
        """Returns functions to compute the loss and its gradient.

        Uses fixed data and non-fixed parameter's values.

        Args:
            data: The data to use for computing the loss and gradient.
                (Default value = None)
            **kwargs: Additional arguments.

        Returns:
            A tuple of functions (L, gradL) to compute the loss and its gradient.

        """
        if data is None:
            data = self.sample_all_vars(**kwargs)

        # Rémi: I'm not sure we might need to precondition the gradient
        # preconditioner = kwargs.get("preconditioner", False)

        def get_loss(theta: torch.Tensor) -> torch.Tensor:
            # print("L, theta.shape : ", theta.shape)
            thetasave = self.space.get_dof(flag_scope="all", flag_format="tensor")
            if TYPE_CHECKING:  # pragma: no cover
                assert isinstance(thetasave, torch.Tensor)

            thetadim = theta.dim()
            # print("thetadim : ", thetadim)
            # accepts bash evaluation
            if thetadim == 1:
                theta = theta.view(1, theta.shape[0])

            # print("theta.shape : ", theta.shape)
            # print("theta[0, :].shape : ", theta[0, :].shape)
            self.space.set_dof(theta[0, :], flag_scope="all")
            left, right = self.assembly_post_sampling(data)
            loss = self.losses.compute_full_loss_without_updating(left, right)[None]
            for i in range(1, theta.shape[0]):
                self.space.set_dof(theta[i, :], flag_scope="all")
                left, right = self.assembly_post_sampling(data)
                temp = self.losses.compute_full_loss_without_updating(left, right)[None]
                loss = torch.cat((loss, temp))
            if thetadim == 1:
                loss = loss[0]

            self.space.set_dof(thetasave, flag_scope="all")
            return loss

        def get_grad_loss(theta: torch.Tensor) -> torch.Tensor:
            thetadim = theta.dim()
            if thetadim == 1:
                theta = theta.view(1, theta.shape[0])

            loss = get_loss(theta[0, :])
            params_list = self.space.get_dof(flag_scope="all", flag_format="list")
            gradLtheta_t = torch.autograd.grad(loss, params_list, create_graph=False)
            gradLtheta = torch.nn.utils.parameters_to_vector(gradLtheta_t)[None, :]
            # if preconditioner:
            #    A = self.preconditioner(data, **kwargs)
            #    # print("gradL: gradLtheta.shape: ", gradLtheta.shape)
            #    gradLtheta[None, :] = torch.linalg.lstsq(A, gradLtheta[0, :]).solution

            for i in range(1, theta.shape[0]):
                loss = get_loss(theta[i, :])
                temp_t = torch.autograd.grad(loss, params_list, create_graph=False)
                temp = torch.nn.utils.parameters_to_vector(temp_t)[None, :]
                # if preconditioner:
                #    A = self.preconditioner(data, **kwargs)
                #    temp[None, :] = torch.linalg.lstsq(A, temp[0, :]).solution
                gradLtheta = torch.cat((gradLtheta, temp))

            if thetadim == 1:
                gradLtheta = gradLtheta[0, :]

            return gradLtheta

        return get_loss, get_grad_loss

    @abstractmethod
    def sample_all_vars(self, **kwargs: Any) -> tuple[LabelTensor, ...]:
        """Samples values in the domains of the arguments of the function to project.

        Args:
            **kwargs: Additional arguments for sampling.

        Returns:
            A tuple of sampled tensors.
        """

    @abstractmethod
    def assembly_post_sampling(
        self, data: tuple[LabelTensor, ...]
    ) -> tuple[tuple[torch.Tensor, ...], tuple[torch.Tensor, ...]]:
        """Assembles the projection problem after sampling.

        Args:
            data: The sampled data.

        Returns:
            A tuple of tuples containing the assembled left and right-hand sides.
        """

    @abstractmethod
    def assembly(
        self, **kwargs: Any
    ) -> tuple[tuple[torch.Tensor, ...], tuple[torch.Tensor, ...]]:
        """Abstract method to assemble the terms of the projection problem.

        Args:
            **kwargs: Additional arguments required for the assembly.

        Returns:
            A tuple of tuples containing the assembled left and right-hand sides.
        """

    def solve_nnstep(self, first_call: bool = True, **kwargs) -> None:
        """Solves the projection problem using optimization and the defined losses.

        This method performs optimization to minimize the loss function over a given
        number of epochs, or until a specified target for the loss is reached.
        At each epoch, it updates the parameters based on the calculated loss and the
        optimizer.

        Args:
            first_call: Whether this is the first call to the method.
                (Default value = True)
            **kwargs: Additional parameters such as the number of epochs and verbosity.
        """
        self.epochs = kwargs.get("epochs", 1000)
        self.verbose = kwargs.get("verbose", False)

        self.loss_target = kwargs.get("loss_target", float("-Inf"))
        self.max_epochs = kwargs.get("max_epochs", self.epochs)

        if self.loss_target is None:
            self.loss_target = float("-Inf")
        if self.max_epochs is None:
            self.max_epochs = self.epochs

        if first_call:
            # print("First call")
            # TODO: is flag_scope inside or outside the if?
            self.flag_scope = kwargs.get("flag_scope", "all")
            # print("flag scope nn optimization :", self.flag_scope)
            self.optimizer.activate_first_optimizer(
                self.get_dof(flag_scope=self.flag_scope, flag_format="list"),
                verbose=self.verbose,
            )
            self.best_loss = float("+Inf")
            self.losses.init_losses()

        epoch = 0

        while epoch < self.max_epochs and self.best_loss > self.loss_target:
            data = self.sample_all_vars(**kwargs)

            # using data just sampled, the function below is a possibility to create
            # non-differentiable quantities to be passed
            # to the loss function of the neural network
            self.create_quantities_for_loss(data)

            def closure():
                self.optimizer.zero_grad()
                kwargs["flag_scope"] = "all"
                left, right = self.assembly_post_sampling(data, **kwargs)
                kwargs["flag_scope"] = self.flag_scope

                # REMI: OLD
                # for i in range(0, len(self.losses.losses_names)):
                #     key = self.losses.losses_names[i]
                #     self.losses.call_and_update(key, left[i], right[i])
                # REMI: NEW
                self.losses.compute_all_losses(left, right)

                self.losses.loss = self.losses.compute_full_loss(self.optimizer, epoch)

                self.losses.loss.backward(retain_graph=True)
                if self.bool_preconditioner:
                    preconditioned_grads = self.preconditioner(
                        epoch,
                        data,
                        self.get_gradient(),
                        left,
                        right,
                        **kwargs,
                    )
                    self.set_gradient(preconditioned_grads)

                return self.losses.loss.item()

            if self.bool_linesearch:
                closure()  # to get the preconditioned gradient
                dsearch = self.get_gradient()  # descent direction
                L, GradL = self.get_loss_grad_loss(data, **kwargs)
                theta = self.get_dof(flag_scope=self.flag_scope, flag_format="tensor")
                if TYPE_CHECKING:  # pragma: no cover
                    assert isinstance(theta, torch.Tensor)

                gradLtheta = GradL(theta)  # non-preconditioned gradient
                if self.type_linesearch == "armijo":
                    eta = (
                        backtracking_armijo_line_search_with_loss_theta_grad_loss_theta(
                            L,
                            theta,
                            L(theta),
                            gradLtheta,
                            dsearch,
                            **self.data_linesearch,
                        )
                    )
                else:
                    eta = logarithmic_grid_line_search(
                        L, theta, dsearch, **self.data_linesearch
                    )
                if torch.all(L(theta) > L(theta - eta * dsearch)):
                    self.optimizer.set_lr(eta)
                else:
                    self.optimizer.set_lr(self.default_lr)

            ####print(self.get_dof(flag_scope=self.flag_scope, flag_format="list"))
            if self.bool_linesearch:
                assert len(self.optimizer.activated_optimizer) == 1, (
                    "self.optimizers.activated_optimizer should have length 1"
                )
                if isinstance(self.optimizer.activated_optimizer[0], ScimbaSGD):

                    def closure():
                        return self.losses.loss.item()

            self.optimizer.step(closure)
            closure()
            self.losses.update_histories()

            if math.isinf(self.losses.loss.item()) or math.isnan(
                self.losses.loss.item()
            ):
                self.losses.loss = torch.tensor(self.best_loss)

            if self.losses.loss.item() < self.best_loss:
                self.best_loss = self.losses.loss.item()
                # Save the model
                self.optimizer.update_best_optimizer()
                self.space.update_best_approx()

                if self.verbose:
                    print(
                        f"epoch: {epoch}, best loss: {self.losses.loss.item():.3e}",
                        flush=True,
                    )

            if epoch % 100 == 0 and self.verbose:
                print(
                    f"epoch: {epoch},      loss: {self.losses.loss.item():.3e}",
                    flush=True,
                )

            # print("self.losses.loss_history[0]: ", self.losses.loss_history[0])
            if self.optimizer.test_activate_next_optimizer(
                self.losses.loss_history,
                self.losses.loss.item(),
                self.losses.loss_history[0],
                epoch,
                self.epochs,
            ):
                if self.verbose:
                    print("activate next opt! epoch = ", epoch)
                self.space.load_from_best_approx()
                self.optimizer.activate_next_optimizer(
                    self.get_dof(flag_scope=self.flag_scope, flag_format="list"),
                    verbose=self.verbose,
                )

            epoch += 1

        self.space.load_from_best_approx()

    def solve_linearstep(self, **kwargs: Any) -> None:
        """Find the optimal values for the parameters of the last layer.

        Targets the neural network of the approximation space
        with a least square solver.

        Args:
            **kwargs: Additional parameters for solving the linear step.

        Raises:
            NotImplementedError: If the method is called for a non-scalar equation.
        """
        # TODO: change for vectorial function

        flag_scope = "except_last_layer"
        phi, f = self.assembly(
            flag_scope=flag_scope, **kwargs
        )  ### phi and f are tuple with the residue

        if len(f) > 1:
            raise NotImplementedError(
                "solve_linearstep not implemented yet for non scalar"
            )

        phi_with_bias = torch.cat(
            [phi[0], torch.ones(phi[0].shape[0], 1, device=phi[0].device)], dim=1
        )

        m, n = phi_with_bias.shape
        phi_with_bias = torch.cat(
            [phi_with_bias, self.ridge**0.5 * torch.eye(n)], dim=0
        )
        f_0 = torch.cat([f[0], torch.zeros((n, 1))], dim=0)
        if phi_with_bias.is_cuda:
            alpha_new = torch.linalg.pinv(phi_with_bias) @ f_0
        else:
            alpha_new = torch.linalg.lstsq(phi_with_bias, f_0).solution

        self.space.set_dof(
            alpha_new.reshape(-1, 1), flag_scope="last_layer"
        )  ## the reshape is important for non scalar equation

    def solve(self, **kwargs: Any) -> None:
        """Solves numerically, with optimization, the projection problem.

        This method performs interleaved optimization steps on the parameters of
        the inner layers and least square fitting steps on the parameters of
        the last layer.

        Args:
            **kwargs: Additional parameters for solving the projection problem.
        """
        epochs = kwargs.get("epochs", 1)
        self.verbose = kwargs.get("verbose", False)

        # we do multiple steps ONLY if we have BOTH linear and nonlinear steps
        perform_multiple_steps = (
            self.projection_data["linear"] + self.projection_data["nonlinear"]
        ) >= 2  # Rémi it was 1 ??? True + True = 2
        flag_scope = "all"
        if self.projection_data["linear"]:
            flag_scope = "except_last_layer"

        q = self.projection_data["nb_step"]
        for k in range(0, q):
            if self.projection_data["linear"]:
                self.solve_linearstep(**kwargs)

                left, right = self.assembly(**kwargs)
                self.losses.compute_all_losses(left, right)

                self.losses.loss = self.losses.compute_full_loss(
                    self.optimizer,
                    self.projection_data["nb_step"] * epochs,
                )
                if perform_multiple_steps and self.verbose:
                    print(
                        f"Value of the loss after the {k}th linear step: "
                        f"{self.losses.loss.item():.3e}",
                    )

                # print(torch.linalg.norm(self.space.network.output_layer.weight))

            if self.projection_data["nonlinear"]:
                self.solve_nnstep(flag_scope=flag_scope, **kwargs)

            if not perform_multiple_steps:
                break

        left, right = self.assembly(**kwargs)
        # REMI: OLD
        # for i in range(0, len(self.losses.losses_names)):
        #     key = self.losses.losses_names[i]
        #     self.losses.call_and_update(key, left[i], right[i])
        # REMI: NEW
        self.losses.compute_all_losses(left, right)

        self.losses.loss = self.losses.compute_full_loss(
            self.optimizer,
            self.projection_data["nb_step"] * epochs,
        )
        if self.verbose:
            print("Training done!")
            print(f"    Final loss value: {self.losses.loss.item():.3e}")
            print(f"     Best loss value: {self.best_loss:.3e}")

    def make_tuple(self, x: torch.Tensor | tuple[torch.Tensor, ...]) -> tuple:
        """Converts input to a tuple of tensors.

        Args:
            x: Input tensor or tuple of tensors.

        Returns:
            A tuple of tensors.

        """
        if isinstance(x, tuple):
            return x
        else:
            # REMI: check if ok!
            assert len(x.shape) == 2, (
                "expected a tensor of shape (n, 1) or (n, d) or a tuple of tensors "
                "of shape (n, 1)"
            )
            return tuple(x[..., i : i + 1] for i in range(x.shape[-1]))

    def dict_for_save(self) -> dict[str, dict | float]:
        """Returns a dictionary representing the state of the projector for saving.

        Returns:
            A dictionary containing the state of the projector.

        """
        # save self.space.state_dict()
        state_dict: dict[str, dict | float] = {"space": self.space.dict_for_save()}
        # save self.losses.state_dict()
        state_dict["losses"] = self.losses.dict_for_save()
        # save best loss
        state_dict["best_loss"] = self.best_loss
        # save self.optimizers.state_dict()
        state_dict["optimizer"] = self.optimizer.dict_for_save()
        return state_dict

    def load_from_dict(self, state_dict: dict[str, Any], **kwargs: dict) -> None:
        """Loads the state of the projector from a dictionary.

        Args:
            state_dict: The dictionary containing the state to load.
            **kwargs: Additional parameters for loading the state.
        """
        load_best_approx = kwargs.get("load_best_approx", True)
        # recover space
        if "space" in state_dict:
            self.space.load_from_dict(state_dict["space"])
            if load_best_approx:
                self.space.load_from_best_approx()
        else:
            warn(
                "input state_dict has no key 'space' - will not load space",
                RuntimeWarning,
            )
        if "losses" in state_dict:
            self.losses.load_from_dict(state_dict["losses"])
        else:
            warn(
                "input state_dict has no key 'losses' - will not load losses",
                RuntimeWarning,
            )
        # recover best loss
        if "best_loss" in state_dict:
            self.best_loss = state_dict["best_loss"]
        else:
            warn(
                "input state_dict has no key 'best_loss' - will not load best_loss",
                RuntimeWarning,
            )
        if "optimizer" in state_dict:
            self.optimizer.load_from_dict(
                self.get_dof(flag_format="list"), state_dict["optimizer"]
            )
        else:
            warn(
                "input state_dict has no key 'optimizer' - will not load optimizer",
                RuntimeWarning,
            )

    def save(
        self,
        scriptname: str,
        postfix: str = "",
        path: Path = DEFAULT_PATH_FOR_SAVING,
        folder_name: str = FOLDER_FOR_SAVED_PROJECTORS,
        verbose: bool | None = None,
    ) -> None:
        """Saves the current state of the projector to a file.

        Args:
            scriptname: The name of the script.
            postfix: An optional postfix for the filename. (Default value = "")
            path: (Default value = DEFAULT_PATH_FOR_SAVING)
            folder_name: (Default value = FOLDER_FOR_SAVED_PROJECTORS)
            verbose: if None then global verbosity of scimba is used;
                otherwise the wanted verbosity (Default value = None)
        """
        verbose = get_verbosity() if verbose is None else verbose
        file_path = get_filepath_for_save(scriptname, postfix, path, folder_name)
        if verbose:
            print(">> saving state dict in file %s" % file_path)
        torch.save(self.dict_for_save(), file_path)

    def load(
        self,
        scriptname: str,
        postfix: str = "",
        path: Path = DEFAULT_PATH_FOR_SAVING,
        folder_name: str = FOLDER_FOR_SAVED_PROJECTORS,
        verbose: bool | None = None,
    ) -> bool:
        """Loads the current state of the projector from a file.

        Args:
            scriptname: The name of the script.
            postfix: An optional postfix for the filename. (Default value = "")
            path: (Default value = DEFAULT_PATH_FOR_SAVING)
            folder_name: (Default value = FOLDER_FOR_SAVED_PROJECTORS)
            verbose: if None then global verbosity of scimba is used;
                otherwise the wanted verbosity (Default value = None)

        Returns:
            Whether the load was successful.
        """
        verbose = get_verbosity() if verbose is None else verbose

        file_path = get_filepath_for_save(scriptname, postfix, path, folder_name)
        if not file_path.is_file():
            # print(
            #     ">> loading state dict in file %s: file does not exists; do nothing"
            #     % file_path
            # )
            warn(
                "trying to load state dict in file %s: file does not exists; do nothing"
                % file_path,
                RuntimeWarning,
            )
            return False
        if verbose:
            print(">> loading state dict in file %s" % file_path)
        state_dict = torch.load(
            file_path, weights_only=True, map_location=torch.get_default_device()
        )
        try:
            self.load_from_dict(state_dict)
        except RuntimeError:
            # print(
            #     ">> loading from state dict in file %s: something went wrong; "
            #     "maybe the nn has not the same size" % file_path
            # )
            warn(
                "loading state dict in file %s: something went wrong; "
                "maybe the nn has not the same size" % file_path,
                RuntimeWarning,
            )
            return False
        return True

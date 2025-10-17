"""A module to handle losses."""

from collections.abc import Sequence
from typing import Any, Callable

import numpy as np
import torch
import torch.nn as nn
from matplotlib.axes import Axes

from scimba_torch.optimizers.optimizers_data import OptimizerData


class MassLoss(nn.modules.loss._Loss):
    """Custom loss function for the difference in mass between input and target tensors.

    This loss returns either the **mean** or **sum**
    of the element-wise difference between
    `input` and `target`, depending on the `reduction` parameter.

    Args:
        size_average: Deprecated (unused). Included for API compatibility.
        reduce: Deprecated (unused). Included for API compatibility.
        reduction: Specifies the reduction to apply to the output.
            Must be `'mean'` (default) or `'sum'`.

    Example:
        >>> loss = MassLoss(reduction='sum')
        >>> input = torch.tensor([1.0, 2.0, 3.0])
        >>> target = torch.tensor([0.5, 1.5, 2.5])
        >>> output = loss(input, target)
        >>> print(output)
        tensor(1.5)
    """

    __constants__ = ["reduction"]

    def __init__(
        self,
        size_average: bool | None = None,
        reduce: bool | None = None,
        reduction: str = "mean",
    ) -> None:
        super().__init__(size_average, reduce, reduction)

    def forward(self, input: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """Computes the mass loss between input and target tensors.

        Args:
            input: The predicted values.
            target: The ground-truth values.

        Returns:
            The scalar loss value (mean or sum of differences).
        """
        if self.reduction == "mean":
            return torch.mean(input - target)
        else:
            return torch.sum(input - target)


class GenericLoss:
    """A class for a loss with a coefficient and history.

    Args:
        loss_function: The loss function.
        coeff: A coefficient that scales the computed loss value.

    """

    def __init__(
        self,
        loss_function: Callable[[torch.Tensor, torch.Tensor], torch.Tensor],
        coeff: float,
    ):
        self.func = loss_function  #: The loss function.
        self.coeff = coeff  #: The coeff.
        self.coeff_history: list[float] = [coeff]  #: The history of coeffs.
        self.loss = torch.tensor(float("+Inf"))  #: The current loss value.
        self.weighted_loss = self.coeff * self.loss  #: The current weighted loss value.
        self.loss_history: list[float] = []  #: The history of losses.

    def get_loss(self) -> torch.Tensor:
        """Returns the current loss value.

        Returns:
            The current loss value.
        """
        return self.loss

    def get_weighted_loss(self) -> torch.Tensor:
        """Returns the current weighted loss value.

        Returns:
            The current weighted loss value (coeff * loss).
        """
        return self.weighted_loss

    def get_loss_history(self) -> list[float]:
        """Returns the history of computed loss values.

        Returns:
            A list of loss values (in float).
        """
        return self.loss_history

    def get_coeff(self) -> float:
        """Returns the current coefficient value.

        Returns:
            The current coefficient value.
        """
        return self.coeff

    def get_coeff_history(self) -> list[float]:
        """Returns the history of coefficient values.

        Returns:
             A list of coefficient values representing the history of coefficients used.
        """
        return self.coeff_history

    def init_loss(self) -> None:
        """Resets the loss and weighted loss to infinity."""
        self.loss = torch.tensor(float("+Inf"))
        self.weighted_loss = self.coeff * self.loss

    def update_loss(self, value: torch.Tensor):
        """Updates the current loss value and recalculates the weighted loss.

        Args:
            value: The new loss value to be set.
        """
        self.loss = value
        self.weighted_loss = self.coeff * self.loss

    def update_history(self, loss_factor: float = 1.0) -> None:
        """Appends the current loss (optionally scaled by a factor) to the loss history.

        Args:
            loss_factor: A factor by which to scale the loss before
                adding it to the history. Defaults to 1.0.
        """
        self.loss_history.append(self.loss.item() * loss_factor)

    def set_history(self, history: list[float]) -> None:
        """Sets the history of loss values to the provided list of floats.

        Args:
            history: A list of float values representing the new loss history.
        """
        self.loss_history = history.copy()

    def update_coeff(self, coeff: float) -> None:
        """Updates the coefficient value and recalculates the weighted loss.

        Args:
            coeff: The new coefficient value to be set.
        """
        self.coeff = coeff
        self.coeff_history.append(coeff)
        self.weighted_loss = self.coeff * self.loss

    def __call__(self, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        """Calls the loss function with two input tensors.

        Args:
            a: The first input tensor.
            b: The second input tensor.

        Returns:
            The result of applying the loss function to the two tensors.
        """
        return self.func(a, b)

    def call_and_update(self, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        """Calls the loss function, updates the loss, and returns the updated loss.

        Args:
            a: The first input tensor.
            b: The second input tensor.

        Returns:
            The updated loss value.
        """
        self.update_loss(self.func(a, b))
        return self.loss

    def __repr__(self) -> str:
        """Returns a string representation of the object.

        Returns:
            A string representing the object, including the loss function
                and coefficient.
        """
        return "%s(%s, %s)" % (self.__class__.__name__, self.func, self.coeff)

    def __str__(self) -> str:
        """Returns a human-readable string representation of the object.

        Returns:
            A string that shows the loss function and coefficient.
        """
        return "func: %s, coeff: %s" % (self.func, self.coeff)


class GenericLosses:
    """A class to handle several losses: residual, boundary conditions, etc.

    A class that manages multiple instances of `GenericLoss` and
        computes the full loss as a combination of all individual losses.

    Args:
        losses: A list of tuples;
            each tuple contains a loss name, a callable loss function,
            and a coefficient. Default is None.
        **kwargs: Additional keyword arguments.
            "adaptive_weights": The method for adaptive weighting of losses.
            currently only "annealing" is supported.

            "principal_weights": the name of the reference loss for adapting
            weights.

            "epochs_adapt": the number of epochs between adaptive weight updates.

            "alpha_lr_annealing": the learning rate annealing factor for adaptive
            weighting.

    Raises:
        ValueError: If the input list is empty.
        TypeError: If the input list contains elements with incorrect types.

    """

    losses_dict: dict[str, GenericLoss]
    """A dictionary mapping loss names to `GenericLoss` instances."""
    loss: torch.Tensor
    """The current full loss value, which is the sum of all weighted losses."""
    loss_history: list[float]
    """A list storing the history of computed full loss values."""
    adaptive_weights: str | None
    """The method for adaptive weighting of losses. Default is None."""
    principal_weights: str | None
    """The name of the principal loss used for adaptive weighting."""
    epochs_adapt: int
    """The number of epochs between adaptive weight updates. Default is 10."""
    alpha_lr_annealing: float
    """"The learning rate annealing factor for adaptive weighting. Default is 0.9."""

    def __init__(
        self,
        losses: Sequence[
            tuple[
                str, Callable[[torch.Tensor, torch.Tensor], torch.Tensor], float | int
            ]
        ]
        | None = None,
        **kwargs,
    ):
        # Create a dictionary of GenericLoss from losses
        self.losses_dict: dict[str, GenericLoss] = {}
        if losses is None:
            self.losses_dict["residual"] = GenericLoss(torch.nn.MSELoss(), 1.0)
            self.losses_names = list()
        else:
            # Check non-emptyness of input list
            if len(losses) == 0:
                raise ValueError(
                    f"can not create a {self.__class__.__name__} from an empty list"
                )
            for loss in losses:
                if not (
                    len(loss) == 3
                    and isinstance(loss[0], str)
                    and callable(loss[1])
                    and isinstance(loss[2], float | int)
                ):
                    raise TypeError(
                        f"can not create a {self.__class__.__name__} from input list; \
                        wrong types"
                    )

            self.losses_dict = {
                loss[0]: GenericLoss(loss[1], float(loss[2])) for loss in losses
            }
            # REMI: NEW: keep order of the input list.... could use an ordered dict...
            self.losses_names = [loss[0] for loss in losses]

        # REMI: OLD
        # self.losses_names = list(self.losses_dict.keys())

        # The full loss, i.e., the sum of weighted losses
        self.loss = torch.tensor(float("+Inf"))
        self.loss_history: list[float] = []

        self.adaptive_weights = kwargs.get("adaptive_weights", None)
        self.principal_weights = kwargs.get("principal_weights", None)
        if self.principal_weights is None:
            if losses is None:
                self.principal_weights = "residual"
            else:  # losses is not empty
                self.principal_weights = losses[0][0]

        self.epochs_adapt = kwargs.get("epochs_adapt", 10)
        self.alpha_lr_annealing = kwargs.get("alpha_lr_annealing", 0.9)

    # Accessors
    # Return full loss
    def get_full_loss(self) -> torch.Tensor:
        """Returns the current full loss value.

        Returns:
            The current full loss value.
        """
        return self.loss

    def get_loss(self, key: str) -> torch.Tensor:
        """Returns the current loss value for a specific loss function.

        Args:
            key: The name of the loss function.

        Returns:
            The current loss value for the specified loss function.

        Raises:
            KeyError: If the key is not found in the losses dictionary.
        """
        if key not in self.losses_dict:
            raise KeyError(f"key {key} not in losses dictionary")
        return (self.losses_dict[key]).get_loss()

    def get_history(self, key: str) -> list[float]:
        """Returns the history of computed loss values for a specific loss function.

        Args:
            key: The name of the loss function.

        Returns:
            The history of computed loss values for the specified loss function.

        Raises:
            KeyError: If the key is not found in the losses dictionary.
        """
        if key not in self.losses_dict:
            raise KeyError(f"key {key} not in losses dictionary")
        return (self.losses_dict[key]).get_loss_history()

    def get_coeff(self, key: str) -> float:
        """Returns the current coefficient value for a specific loss function.

        Args:
            key: The name of the loss function.

        Returns:
            The current coefficient value for the specified loss function.

        Raises:
            KeyError: If the key is not found in the losses dictionary.
        """
        if key not in self.losses_dict:
            raise KeyError(f"key {key} not in losses dictionary")
        return (self.losses_dict[key]).get_coeff()

    def get_coeff_history(self, key: str) -> list[float]:
        """Returns the history of coefficient values for a specific loss function.

        Args:
            key: The name of the loss function.

        Returns:
            The history of coefficient values for the specified loss function.

        Raises:
            KeyError: If the key is not found in the losses dictionary.
        """
        if key not in self.losses_dict:
            raise KeyError(f"key {key} not in losses dictionary")
        return (self.losses_dict[key]).get_coeff_history()

    # Mutators
    def init_losses(self) -> None:
        """Resets all loss values to infinity."""
        for name, loss in self.losses_dict.items():
            loss.init_loss()
        self.loss = torch.tensor(float("+Inf"))

    def init_loss(self, key: str) -> None:
        """Resets the loss value for a specific loss function to infinity.

        Args:
            key: The name of the loss function.

        Raises:
            KeyError: If the key is not found in the losses dictionary.
        """
        if key not in self.losses_dict:
            raise KeyError(f"key {key} not in losses dictionary")
        (self.losses_dict[key]).init_loss()

    def update_loss(self, key: str, value: torch.Tensor) -> None:
        """Updates the loss value for a specific loss function.

        Args:
            key: The name of the loss function.
            value: The new loss value to be set.

        Raises:
            KeyError: If the key is not found in the losses dictionary.
        """
        if key not in self.losses_dict:
            raise KeyError(f"key {key} not in losses dictionary")
        (self.losses_dict[key]).update_loss(value)

    def update_histories(self, loss_factor: float = 1.0) -> None:
        """Appends the current loss (optionally scaled by a factor) to the loss history.

        Args:
            loss_factor: A factor by which to scale the loss before
                adding it to the history. Defaults to 1.0.
        """
        for name, loss in self.losses_dict.items():
            loss.update_history(loss_factor)
        self.loss_history.append(self.loss.item() * loss_factor)

    def update_coeff(self, key: str, value: float) -> None:
        """Updates the coefficient value for a specific loss function.

        Args:
            key: The name of the loss function.
            value: The new coefficient value to be set.

        Raises:
            KeyError: If the key is not found in the losses dictionary.
        """
        if key not in self.losses_dict:
            raise KeyError(f"key {key} not in losses dictionary")
        (self.losses_dict[key]).update_coeff(value)

    # Calls to losses funcs
    def __call__(self, key: str, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        """Calls the loss function with two input tensors.

        Args:
            key: The name of the loss function.
            a: The first input tensor.
            b: The second input tensor.

        Returns:
            The result of applying the loss function to the two tensors.

        Raises:
            KeyError: If the key is not found in the losses dictionary.
        """
        if key not in self.losses_dict:
            raise KeyError(f"key {key} not in losses dictionary")
        return (self.losses_dict[key])(a, b)

    def call_and_update(
        self, key: str, a: torch.Tensor, b: torch.Tensor
    ) -> torch.Tensor:
        """Calls the loss function, updates the loss, and returns the updated loss.

        Args:
            key: The name of the loss function.
            a: The first input tensor.
            b: The second input tensor.

        Returns:
            The updated loss value.

        Raises:
            KeyError: If the key is not found in the losses dictionary.
        """
        if key not in self.losses_dict:
            raise KeyError(f"key {key} not in losses dictionary")
        return (self.losses_dict[key]).call_and_update(a, b)

    # Adapting weights
    def __learning_rate_annealing(self, key: str, optimizers: OptimizerData) -> None:
        """Annealing of the learning rate.

        Args:
            key: The name of the principal loss function.
            optimizers: The optimizer data object.
        """
        ((self.losses_dict[key]).get_loss()).backward(
            create_graph=False, retain_graph=True
        )
        grad_key = optimizers.get_opt_gradients()
        max_grad_key = torch.max(torch.abs(grad_key))
        (self.losses_dict[key]).update_coeff(1.0)

        for key2, loss in self.losses_dict.items():
            if not (key == key2):
                ((self.losses_dict[key2]).get_loss()).backward(
                    create_graph=False, retain_graph=True
                )
                grad_key2 = optimizers.get_opt_gradients()
                mean_grad_key2 = torch.mean(torch.abs(grad_key2))
                new_coeff = (
                    self.alpha_lr_annealing * max_grad_key / mean_grad_key2
                    + (1 - self.alpha_lr_annealing)
                    * (self.losses_dict[key2]).get_coeff()
                )
                (self.losses_dict[key2]).update_coeff(new_coeff.item())

        self.alpha_lr_annealing *= 0.999

    def compute_all_losses(
        self,
        left: tuple[torch.Tensor, ...],
        right: tuple[torch.Tensor, ...],
        update: bool = True,
    ) -> torch.Tensor:
        """Computes all losses.

        Returns the combination of all the losses, possibly updates the loss values.

        Args:
            left: The left tensors.
            right: The right tensors.
            update: Whether to update the current loss.

        Returns:
            torch.Tensor: The computed full loss value.

        Raises:
            ValueError: when left and right do not have the same length
                or the length of left (and right) is not a divisor of
                the number of losses.
        """
        if len(left) != len(right):
            raise ValueError("left and right should have the same length")
        if len(self.losses_names) % len(left):
            raise ValueError(
                "the number of losses should be a multiple of the length of left/right"
            )

        fullloss = torch.tensor(0.0)

        nb_losses_per_equation = len(self.losses_names) // len(left)
        for i in range(len(left)):
            for k in range(nb_losses_per_equation):
                key = self.losses_names[i * nb_losses_per_equation + k]
                if update:
                    self.call_and_update(key, left[i], right[i])
                    fullloss += (self.losses_dict[key]).get_weighted_loss()
                else:
                    fullloss += (
                        (self.losses_dict[key]).func(left[i], right[i])
                        * (self.losses_dict[key]).coeff
                    )

        return fullloss

    def compute_full_loss_without_updating(
        self, left: tuple[torch.Tensor, ...], right: tuple[torch.Tensor, ...]
    ) -> torch.Tensor:
        """Computes the full loss without updating the loss values.

        Args:
            left: The left tensors.
            right: The right tensors.

        Returns:
            The computed full loss value.
        """
        return self.compute_all_losses(left, right, update=False)

    def compute_full_loss(self, optimizers: OptimizerData, epoch: int) -> torch.Tensor:
        """Computes the full loss as the combination of all the losses.

        Args:
            optimizers: The optimizer data object.
            epoch: The current epoch.

        Returns:
            The computed full loss value.

        Raises:
            ValueError: when adaptive_weights is not recognized.
        """
        if (self.adaptive_weights is not None) and (epoch % self.epochs_adapt == 0):
            assert isinstance(self.principal_weights, str)
            if self.adaptive_weights == "annealing":
                self.__learning_rate_annealing(self.principal_weights, optimizers)
            else:
                raise ValueError(
                    f"adaptive_weights {self.adaptive_weights} not recognized"
                )

        self.loss = torch.tensor(0.0)  # self.losses_dict can not be empty
        for name, loss in self.losses_dict.items():
            self.loss += loss.get_weighted_loss()

        return self.loss

    def dict_for_save(
        self,
        # best_loss: torch.Tensor
    ) -> dict[str, torch.Tensor | list[float]]:
        """Returns a dictionary of best loss values for saving.

        Returns:
            A dictionary containing the best loss value and loss history.
        """
        dic: dict[str, torch.Tensor | list[float]] = {
            # "loss": best_loss,
            "loss": self.loss,
            "loss_history": self.loss_history,
        }
        for name, loss in self.losses_dict.items():
            key = name + "_loss_history"
            dic[key] = loss.get_loss_history()

        return dic

    def try_to_load(self, checkpoint: dict, string: str) -> Any:
        """Tries to load a value from the checkpoint.

        Args:
            checkpoint: The checkpoint dictionary.
            string: The key to look for in the checkpoint.

        Returns:
            The loaded value if found, otherwise None.
        """
        try:
            return checkpoint[string]
        except KeyError:
            return None

    def load_from_dict(self, checkpoint: dict) -> None:
        """Loads the loss history from a checkpoint.

        Args:
            checkpoint: The checkpoint dictionary.
        """
        loss = self.try_to_load(
            checkpoint, "loss"
        )  # TODO it is best_loss and not loss that has been saved...
        # if (
        #     (loss is not None)
        #     and isinstance(loss, torch.Tensor)
        #     and (loss.shape == torch.Size([]))
        # ):
        self.loss = loss

        his = self.try_to_load(checkpoint, "loss_history")
        # if (not his is None) and isinstance(his, list[float]) :
        if his is not None:  # TODO check type of his?
            self.loss_history = his.copy()

        for (
            name,
            loss,
        ) in (
            self.losses_dict.items()
        ):  # will the keys be stored in the same order??? it seams that it depends
            # on several things, in particular python version... TODO
            key = name + "_loss_history"
            his = self.try_to_load(checkpoint, key)
            # if (not his is None) and isinstance(his, list[float]) :
            if his is not None:  # TODO check type of his?
                loss.set_history(his)

    def plot(self, ax: Axes, **kwargs) -> Axes:
        """Plots the loss history on the given axis.

        Args:
            ax: The axis on which to plot the loss history.
            **kwargs: Additional keyword arguments.

        Returns:
            The axis with the plotted loss history.
        """
        groups = kwargs.get("loss_groups", [])
        dict_of_grouped_losses: dict["str", np.ndarray | float] = {
            gr: 0.0 for gr in groups
        }

        def is_in_dict_of_grouped_losses(name: str):
            return not all(key not in name for key in dict_of_grouped_losses)

        def key_in_dict_of_grouped_losses(name: str):
            for key in dict_of_grouped_losses:
                if key in name:
                    return key
            return ""

        for name, loss in self.losses_dict.items():
            if is_in_dict_of_grouped_losses(name):
                key = key_in_dict_of_grouped_losses(name)
                dict_of_grouped_losses[key] += (
                    np.array(loss.get_loss_history())
                    if (len(loss.get_loss_history()) > 0)
                    else 0.0
                )
        # print("groups: ", groups)

        minval = (
            np.min(np.array(self.loss_history)) if (len(self.loss_history) > 0) else 0.0
        )
        minvals = np.min(
            np.array(
                [
                    (
                        np.min(np.array(loss.get_loss_history()))
                        if (len(loss.get_loss_history()) > 0)
                        else 0.0
                    )
                    for _, loss in self.losses_dict.items()
                ]
            )
        )
        minval = np.min([minval, minvals])

        if minval >= 0.0:
            ax.semilogy(self.loss_history, label="total loss")

            for name, loss in self.losses_dict.items():
                if not is_in_dict_of_grouped_losses(name):
                    ax.semilogy(loss.get_loss_history(), label=name)

            for key, loss_history in dict_of_grouped_losses.items():
                ax.semilogy(loss_history, label=key)

            ax.set_title("loss history")
        else:
            ax.semilogy(np.array(self.loss_history) - minval, label="total loss - min")

            for name, loss in self.losses_dict.items():
                if not is_in_dict_of_grouped_losses(name):
                    if (len(loss.get_loss_history()) > 0) and np.min(
                        np.array(loss.get_loss_history())
                    ) < 0.0:
                        ax.semilogy(
                            loss.get_loss_history() - minval, label=name + " - min"
                        )
                    else:
                        ax.semilogy(loss.get_loss_history(), label=name)

            for key, nloss in dict_of_grouped_losses.items():
                if (len(np.array(nloss)) > 0) and np.min(np.array(nloss)) < 0.0:
                    ax.semilogy(nloss - minval, label=key + " - min")
                else:
                    ax.semilogy(nloss, label=key)

            ax.set_title("loss history, min = %.2e" % minval)
        ax.legend()
        return ax

    def __str__(self) -> str:
        """Returns a human-readable string representation of the object.

        Returns:
            A string that shows the loss functions and their coefficients.
        """
        res = "losses: [\n"
        for name, loss in self.losses_dict.items():
            res += "         " + name + ": " + str(loss) + "\n"
        res += "        ]"
        return res


if __name__ == "__main__":  # pragma: no cover

    def loss_func(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        """For test.

        Args:
            a: for test.
            b: for test.

        Returns:
            For test.
        """
        return torch.sum(torch.abs(b - a))

    # create a GenericLosses with only a residual
    losses = GenericLosses()
    print(losses)

    # create a GenericLosses with a residual and a bc with custom function
    losses2 = GenericLosses(
        [("residual", torch.nn.MSELoss(), 0.5), ("bc", loss_func, 0.8)]
    )
    print(losses2)

    # eval losses
    print(
        "eval losses2[residual]: ",
        losses2("residual", torch.ones((2, 3)) + 1e-6, torch.ones((2, 3))),
    )
    print(
        "eval losses2[bc]: ",
        losses2("bc", torch.ones((2, 3)) + 1e-6, torch.ones((2, 3))),
    )

    # eval and update losses
    losses2.call_and_update(
        "residual",
        torch.ones((2, 3), requires_grad=True) + 1e-6,
        torch.ones((2, 3), requires_grad=True),
    )
    losses2.call_and_update("bc", torch.ones((2, 3)) + 1e-6, torch.ones((2, 3)))
    print("losses2 residual: ", losses2.get_loss("residual"))
    print("losses2 bc : ", losses2.get_loss("bc"))

    # update histories
    losses2.update_histories()
    print("losses2 residual loss_history: ", losses2.get_history("residual"))
    print("losses2 bc loss_history: ", losses2.get_history("bc"))

    # test compute full loss
    opt = OptimizerData()
    epo = 0
    loss = losses2.compute_full_loss(opt, epo)
    print("losses2 full loss: ", loss, ", ", losses2.get_full_loss())

    # errors
    try:
        losses3 = GenericLosses([])
    except ValueError as error:
        print(error)

    try:
        losses2.call_and_update("test", torch.ones((2, 3)) + 1e-6, torch.ones((2, 3)))
    except KeyError as error:
        print(error)

    # test adaptive weights
    class SimpleNN(torch.nn.Module):
        """For test."""

        def __init__(self):
            super(SimpleNN, self).__init__()
            self.fc1 = torch.nn.Linear(10, 10)
            self.fc2 = torch.nn.Linear(10, 1)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """For test.

            Args:
                x: For test.

            Returns:
                For test.
            """
            x = torch.relu(self.fc1(x))
            x = self.fc2(x)
            return x

    opt_1 = {
        "name": "adam",
        "optimizer_args": {"lr": 0.01},
        "scheduler_args": {"gamma": 0.9, "step_size": 10},
    }

    net = SimpleNN()
    optimizer_data = OptimizerData(
        opt_1,
        {"name": "lbfgs", "switch_at_epoch_ratio": 0.7, "switch_at_plateau": [50, 10]},
    )
    optimizer_data.activate_first_optimizer(list(net.parameters()))

    # Create dummy input and target tensors
    input_tensor = torch.randn(5, 10)  # Batch of 5 samples, each of size 10
    target_tensor = torch.randn(5, 1)  # Target tensor with batch size 5

    # Forward pass
    output_tensor = net(input_tensor)

    losses3 = GenericLosses(
        [("residual", torch.nn.MSELoss(), 0.5), ("bc", loss_func, 0.8)],
        adaptive_weights="annealing",
    )

    losses3.call_and_update("residual", output_tensor, target_tensor)
    losses3.call_and_update("bc", output_tensor, target_tensor)

    loss = losses3.compute_full_loss(optimizer_data, 10)

    print("losses3 full loss: ", loss, ", ", losses3.get_full_loss())

    print("losses3 residual coeff        : ", losses3.get_coeff("residual"))
    print("losses3 residual coeff history: ", losses3.get_coeff_history("residual"))
    print("losses3 bc       coeff        : ", losses3.get_coeff("bc"))
    print("losses3 bc       coeff history: ", losses3.get_coeff_history("bc"))

    losses3.update_histories()

    input_tensor = torch.randn(5, 10)  # Batch of 5 samples, each of size 10
    # Forward pass
    output_tensor = net(input_tensor)
    losses3.call_and_update("residual", output_tensor, target_tensor)
    losses3.call_and_update("bc", output_tensor, target_tensor)
    losses3.compute_full_loss(optimizer_data, 10)
    losses3.update_histories()

    print("losses3 dict_for_save: ", losses3.dict_for_save())

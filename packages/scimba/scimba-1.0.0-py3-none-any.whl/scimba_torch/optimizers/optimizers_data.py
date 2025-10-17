"""A module to handle several optimizers."""

import copy
import operator  # for xor
import warnings
from typing import Any, Callable

import torch
from torch.optim.optimizer import ParamsT

from scimba_torch.optimizers.scimba_optimizers import (
    AbstractScimbaOptimizer,
    ScimbaAdam,
    ScimbaCustomOptomizer,
    ScimbaLBFGS,
    ScimbaSGD,
)

SCIMBA_OPTIMIZERS = {"adam": ScimbaAdam, "lbfgs": ScimbaLBFGS, "sgd": ScimbaSGD}

SWITCH_AT_EPOCH_DEFAULT = False
SWITCH_AT_EPOCH_N_DEFAULT = 5000
SWITCH_AT_EPOCH_RATIO_DEFAULT = 0.7
SWITCH_AT_PLATEAU_DEFAULT = False
SWITCH_AT_PLATEAU_N1_N2_DEFAULT = (50, 10)
SWITCH_AT_PLATEAU_RATIO_DEFAULT = 500.0


class OptimizerData:
    r"""A class to manage multiple optimizers and their activation criteria.

    Args:
        *args: Variable length argument list of optimizer configurations.

            Input dictionary must have one of the form:

            { "class": value (a subclass of AbstractScimbaOptimizer), keys: value }

            { "name": value (either "adam" or "lbfgs"), keys: value }

            where pairs keys value can be:

            "optimizer_args": a dictionary of arguments for the optimizer,

            "scheduler": a subclass of torch.optim.lr_scheduler.LRScheduler,

            "scheduler_args: a dictionary of arguments for the scheduler

            "switch_at_epoch": a bool or an int, default false,
            if true then default value 5000 is used

            "switch_at_epoch_ratio": a bool or a float, default 0.7,
            if true then default value is used

            "switch_at_plateau": a bool or a tuple of two int, default False,
            if True then default (50, 10) is used

            "switch_at_plateau_ratio": a float r, default value 500.;
            triggers the plateau tests if current_loss < init_loss/r

        **kwargs: Arbitrary keyword arguments.

    Examples:
        >>> from scimba_torch.optimizers.scimba_optimizers\
        ... import ScimbaMomentum
        >>> opt_1 = {\
        ... "name": "adam",\
        ... "optimizer_args": {"lr": 1e-3, "betas": (0.9, 0.999)},\
        ... }
        >>> opt_2 = {"class": ScimbaMomentum, "switch_at_epoch": 500}
        >>> opt_3 = {\
        ... "name": "lbfgs",\
        ... "switch_at_epoch_ratio": 0.7,\
        ... "switch_at_plateau": [500, 20],\
        ... "switch_at_plateau_ratio": 3.0,\
        ... }
        >>> optimizers = OptimizerData(opt_1, opt_2, opt_3)
    """

    activated_optimizer: list[AbstractScimbaOptimizer]
    """A list containing the current optimizer; empty if none."""

    def __init__(self, *args: dict[str, Any], **kwargs):
        self.activated_optimizer = []
        #: A list containing the current optimizer; empty if none.
        self.optimizers: list[dict[str, Any]] = []  #: List of optimizers.
        self.next_optimizer: int = 0  #: Index of the next optimizer to be activated.

        # in case of lr modified by linesearch, need to remenber initial lr
        # self.default_lr: float = kwargs.get("default_lr", 1e-2)

        for opt in args:
            self._check_dictionary_and_append_to_optimizers_list(opt)

        if len(self.optimizers) == 0:  # default optimizers
            self.optimizers.append({"name": "adam"})
            self.optimizers.append({"name": "lbfgs"})

    def _check_dictionary_and_append_to_optimizers_list(self, opt: dict[str, Any]):
        """Checks the input configuration and appends it to the optimizers list.

        Args:
            opt: Optimizer configuration dictionary.

        Raises:
            KeyError: If the dictionary does not contain
                exactly one of "name" or "class".
            ValueError: If the dictionary contains invalid values for any of the keys.
        """
        # Check that there is either a "name" or a "class" key
        if not operator.xor(("name" in opt), ("class" in opt)):
            raise KeyError(
                f"Cannot create a {self.__class__.__name__} from dict: {opt}"
            )

        # Check types and values of entries
        for key in opt:
            if key == "name":
                opt_name = opt["name"]
                if opt_name not in SCIMBA_OPTIMIZERS:
                    raise ValueError(
                        f"Cannot create a {self.__class__.__name__} \
                        from name: {opt_name}"
                    )
            elif key == "class":
                opt_class = opt["class"]
                if not issubclass(opt_class, ScimbaCustomOptomizer):
                    raise ValueError(
                        f"Cannot create a {self.__class__.__name__} \
                        from class: {opt_class}; it must be a subclass \
                        of AbstractOptimizer"
                    )
            elif key == "optimizer_args":
                opt_args = opt[key]
                if not isinstance(opt_args, dict):
                    raise ValueError(
                        f"Cannot create a {self.__class__.__name__} from given {key}"
                    )
            elif key == "scheduler":
                opt_args = opt[key]
                if not issubclass(opt_args, torch.optim.lr_scheduler.LRScheduler):
                    raise ValueError(
                        f"Cannot create a {self.__class__.__name__} \
                        from given {key}; it must be a subclass of \
                        torch.optim.lr_scheduler.LRScheduler"
                    )
            elif key == "scheduler_args":
                opt_args = opt[key]
                if not isinstance(opt_args, dict):
                    raise ValueError(
                        f"Cannot create a {self.__class__.__name__} from given {key}"
                    )
            elif key == "switch_at_epoch":
                opt_args = opt[key]
                if not (isinstance(opt_args, bool) or isinstance(opt_args, int)):
                    raise ValueError(
                        f"In {self.__class__.__name__}.init: {key} \
                        must be either a bool or an int"
                    )
            elif key == "switch_at_epoch_ratio":
                opt_args = opt[key]
                if not (isinstance(opt_args, bool) or isinstance(opt_args, float)):
                    raise ValueError(
                        f"In {self.__class__.__name__}.init: {key} \
                        must be either a bool or a float"
                    )
            elif key == "switch_at_plateau":
                opt_args = opt[key]
                if not (isinstance(opt_args, bool) or isinstance(opt_args, list)):
                    raise ValueError(
                        f"In {self.__class__.__name__}.init: {key} \
                        must be either a bool or tuple of two ints"
                    )
            elif key == "switch_at_plateau_ratio":
                opt_args = opt[key]
                if not isinstance(opt_args, float):
                    raise ValueError(
                        f"In {self.__class__.__name__}.init: {key} must be a float"
                    )
            else:
                warnings.warn(
                    f"In {self.__class__.__name__}.init: unrecognized option {key}",
                    UserWarning,
                )

        self.optimizers.append(opt.copy())

    def step(self, closure: Callable[[], float]) -> None:
        """Performs an optimization step using the currently activated optimizer.

        Args:
            closure: A closure that reevaluates the model and returns the loss.
        """
        if len(self.activated_optimizer) == 1:
            self.activated_optimizer[0].optimizer_step(closure)

    def set_lr(self, lr: float) -> None:
        """Set learning rate of activated optimizer.

        Args:
            lr: The new learning rate.
        """
        if len(self.activated_optimizer) == 1:
            for group in self.activated_optimizer[0].param_groups:
                group["lr"] = lr

    def zero_grad(self) -> None:
        """Zeros the gradients of the currently activated optimizer."""
        self.activated_optimizer[0].zero_grad()

    def test_activate_next_optimizer(
        self,
        loss_history: list[float],
        loss_value: float,
        init_loss: float,
        epoch: int,
        epochs: int,
    ) -> bool:
        """Tests whether the next opt. should be activated based on the given criteria.

        Args:
            loss_history: History of loss values.
            loss_value: Current loss value.
            init_loss: Initial loss value.
            epoch: Current epoch.
            epochs: Total number of epochs.

        Returns:
            True if the next optimizer should be activated, False otherwise.
        """
        if self.next_optimizer >= len(self.optimizers):
            return False

        next_opt = self.optimizers[self.next_optimizer]

        switch_if_epoch = next_opt.get(
            "switch_at_epoch", SWITCH_AT_EPOCH_DEFAULT
        )  # default value = False
        if isinstance(switch_if_epoch, bool):
            n = SWITCH_AT_EPOCH_N_DEFAULT
        else:
            n = switch_if_epoch
            switch_if_epoch = True

        switch_if_epoch_ratio = True
        switch_at_epoch_ratio = next_opt.get(
            "switch_at_epoch_ratio", SWITCH_AT_EPOCH_RATIO_DEFAULT
        )
        if isinstance(switch_at_epoch_ratio, bool):
            switch_if_epoch_ratio = switch_at_epoch_ratio
            switch_at_epoch_ratio = SWITCH_AT_EPOCH_RATIO_DEFAULT

        switch_if_plateau = next_opt.get("switch_at_plateau", SWITCH_AT_PLATEAU_DEFAULT)
        if isinstance(switch_if_plateau, bool):
            n1, n2 = SWITCH_AT_PLATEAU_N1_N2_DEFAULT
        else:
            n1, n2 = switch_if_plateau
            switch_if_plateau = True
        switch_at_plateau_ratio = next_opt.get(
            "switch_at_plateau_ratio", SWITCH_AT_PLATEAU_RATIO_DEFAULT
        )

        if (switch_if_epoch) and (epoch >= n):
            return True

        if (switch_if_epoch_ratio) and (epoch / epochs > switch_at_epoch_ratio):
            return True

        if switch_if_plateau:
            if (loss_value < (init_loss / switch_at_plateau_ratio)) and (
                sum(loss_history[-n2:-1]) - sum(loss_history[-n1 : -n1 + n2]) > 0
            ):
                return True

        return False

    def activate_next_optimizer(
        self, parameters: ParamsT, verbose: bool = False
    ) -> None:
        """Activates the next optimizer in the list.

        Args:
            parameters: Parameters to be optimized.
            verbose: whether to print activation message or not.
        """
        if self.next_optimizer >= len(self.optimizers):
            warnings.warn(
                "trying to overflow list of optimizers - nothing will happen",
                RuntimeWarning,
            )
            return

        opt = self.optimizers[self.next_optimizer]

        if "name" in opt:
            opt_name = opt["name"]
            opt_class = SCIMBA_OPTIMIZERS[opt_name]
        else:
            opt_class = opt["class"]

        # Prepare the arguments
        arguments = {}
        if "optimizer_args" in opt:
            arguments["optimizer_args"] = opt["optimizer_args"].copy()
        if "scheduler" in opt:
            arguments["scheduler"] = opt["scheduler"]
        if "scheduler_args" in opt:
            arguments["scheduler_args"] = opt["scheduler_args"].copy()

        if len(self.activated_optimizer) == 1:
            self.activated_optimizer[0] = opt_class(parameters, **arguments)
        else:
            self.activated_optimizer.append(opt_class(parameters, **arguments))

        if verbose:
            print(f"activating optimizer {opt_class.__name__}")

        self.next_optimizer += 1

    def activate_first_optimizer(
        self, parameters: ParamsT, verbose: bool = False
    ) -> None:
        """Activates the first optimizer in the list.

        Args:
            parameters: Parameters to be optimized.
            verbose: whether to print activation message or not.
        """
        # case where optimizers have already been activated: do nothing
        if len(self.activated_optimizer):
            return

        # try first to activate all the optimizers to report
        # possible errors at the begining of the training!
        next_optimizer_save = (
            self.next_optimizer
        )  # in case where self was loaded from a file
        while self.next_optimizer < len(self.optimizers):
            self.activate_next_optimizer(parameters, verbose=False)
        self.activated_optimizer = []
        self.next_optimizer = next_optimizer_save
        # activate the first optimizer
        self.activate_next_optimizer(parameters, verbose)

    def test_and_activate_next_optimizer(
        self,
        parameters: ParamsT,
        loss_history: list[float],
        loss_value: float,
        init_loss: float,
        epoch: int,
        epochs: int,
    ) -> None:
        """Tests whether next optimizer should be activated; activates it.

        Args:
            parameters: Parameters to be optimized.
            loss_history: History of loss values.
            loss_value: Current loss value.
            init_loss: Initial loss value.
            epoch: Current epoch.
            epochs: Total number of epochs.
        """
        if self.test_activate_next_optimizer(
            loss_history, loss_value, init_loss, epoch, epochs
        ):
            self.activate_next_optimizer(parameters)

    def get_opt_gradients(self) -> torch.Tensor:
        """Gets the gradients of the currently activated optimizer.

        Returns:
            Flattened tensor of gradients.
        """
        grads = torch.tensor([])
        for p in self.activated_optimizer[0].param_groups[0]["params"]:
            if p.grad is not None:
                grads = torch.cat((grads, p.grad.flatten()[:, None]), 0)
        return grads

    def update_best_optimizer(self) -> None:
        """Updates the best state of the currently activated optimizer."""
        self.activated_optimizer[0].update_best_optimizer()

    def dict_for_save(self) -> dict:
        """Returns a dictionary containing the best state of the current optimizer.

        Returns:
            dictionary containing the best state of the optimizer.
        """
        res = self.activated_optimizer[0].dict_for_save()
        res["next_optimizer"] = self.next_optimizer
        return res

    def load_from_dict(self, parameters: ParamsT, checkpoint: dict) -> None:
        """Loads the optimizer and scheduler states from a checkpoint.

        Args:
            parameters: Parameters to be optimized.
            checkpoint: dictionary containing the optimizer and scheduler states.

        Raises:
            ValueError: when there is no active optimizer to load in.
        """
        self.next_optimizer = checkpoint["next_optimizer"]
        self.next_optimizer = self.next_optimizer - 1
        self.activate_next_optimizer(parameters)
        if len(self.activated_optimizer) < 1:
            raise ValueError("there is no active optimizer to load in!")
        self.activated_optimizer[0].load(checkpoint)

    def __str__(self) -> str:
        """Returns a string representation of the optimizers.

        Returns:
            str: String representation of the optimizers.
        """
        ret = "optimizers: ["
        for opt in self.optimizers:
            try:
                opt_name = opt["name"]
                ret = ret + opt_name + ", "
            except KeyError:
                opt_class = opt["class"]
                ret = ret + opt_class.__name__ + ", "
        ret = ret + "]"
        return ret


if __name__ == "__main__":  # pragma: no cover
    import math

    from scimba_torch.optimizers.scimba_optimizers import ScimbaMomentum

    opt_1 = {
        "name": "adam",
        "optimizer_args": {"lr": 1e-3, "betas": (0.9, 0.999)},
    }

    opt_2 = {"class": ScimbaMomentum, "switch_at_epoch": 500}

    opt_3 = {
        "name": "lbfgs",
        "switch_at_epoch_ratio": 0.7,
        "switch_at_plateau": [500, 20],
        "switch_at_plateau_ratio": 3.0,
    }

    optimizers = OptimizerData(opt_1, opt_2, opt_3)

    print("optimizers: ", optimizers)

    class SimpleNN(torch.nn.Module):
        """For test."""

        def __init__(self):
            super(SimpleNN, self).__init__()
            self.fc1 = torch.nn.Linear(10, 1)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """For test.

            Args:
                x: For test.

            Returns:
                For test.
            """
            return self.fc1(x)

    net = SimpleNN()

    opt_1 = {"name": "adam", "optimizer_args": {"lr": 1e-3, "betas": (0.9, 0.999)}}
    opt_2 = {
        "name": "adam",
        "optimizer_args": {"lrTEST": 1e-3, "betasTEST": (0.9, 0.999)},
    }  # wrong list of arguments

    try:
        optimizers2 = OptimizerData(opt_1, opt_2)
        optimizers2.activate_first_optimizer(list(net.parameters()))
    except TypeError as error:
        print(error)

    input_tensor = torch.randn(10000, 10)  # Batch of 10000 samples, each of size 10
    target_tensor = torch.sum(input_tensor, dim=1)[
        :, None
    ]  # Target tensor with batch size 10000

    loss = [torch.tensor(float("+inf"))]
    loss_func = torch.nn.MSELoss()

    opt = optimizers
    opt.activate_first_optimizer(list(net.parameters()))

    def closure():
        """For test.

        Returns:
            For test.
        """
        opt.zero_grad()
        # Forward pass
        output_tensor = net(input_tensor)
        loss[0] = loss_func(output_tensor, target_tensor)
        loss[0].backward(retain_graph=True)
        return loss[0].item()

    init_loss = closure()

    # grads = opt.get_opt_gradients()
    # print("get_opt_gradients: ", grads)

    loss_history = [init_loss]
    best_loss = init_loss
    best_net = copy.deepcopy(net.state_dict())

    epochs = 1000
    for epoch in range(epochs):
        opt.step(closure)

        if math.isinf(loss[0].item()) or math.isnan(loss[0].item()):
            loss[0] = torch.tensor(best_loss)
            net.load_state_dict(best_net)

        if loss[0].item() < best_loss:
            best_loss = loss[0].item()
            best_net = copy.deepcopy(net.state_dict())
            opt.update_best_optimizer()

        loss_history.append(loss[0].item())

        if epoch % 100 == 0:
            print("epoch: ", epoch, "loss: ", loss[0].item())

        if opt.test_activate_next_optimizer(
            loss_history, loss[0].item(), init_loss, epoch, epochs
        ):
            print("activate next opt! epoch = ", epoch)
            opt.activate_next_optimizer(list(net.parameters()))

        # opt.test_and_activate_next_optimizer(\
        # list(net.parameters()), loss_history,\
        # loss[0].item(), init_loss, epoch, epochs )

    net.load_state_dict(best_net)
    closure()
    print("loss after training: ", loss[0].item())
    print("net( torch.ones( 10 ) ) : ", net(torch.ones(10)))

    # grads = opt.get_opt_gradients()
    # print("get_opt_gradients: ", grads)

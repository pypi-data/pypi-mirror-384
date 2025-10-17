"""A module defining scimba optimizers."""

import copy
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Callable

import torch
from torch.optim.optimizer import ParamsT


class NoScheduler:
    """A placeholder class to indicate the absence of a scheduler."""


class AbstractScimbaOptimizer(torch.optim.Optimizer, ABC):
    """Abstract base class for Scimba optimizers with optional learning rate scheduler.

    Args:
        params: Iterable of parameters to optimize or dicts defining parameter groups.
        optimizer_args: Additional arguments for the optimizer. Defaults to {}.
        scheduler: Learning rate scheduler class. Defaults to NoScheduler.
        scheduler_args: Additional arguments for the scheduler. Defaults to {}.
        **kwargs: Arbitrary keyword arguments.

    Raises:
        ValueError: scheduler is not an object of a
            subclass of torch.optim.lr_scheduler.LRScheduler.

    Attributes:
        scheduler_exists: Flag indicating if a scheduler is set.
        scheduler: list containing the scheduler.
        best_optimizer: dictionary containing the best state of the optimizer.
        best_scheduler: list containing the best state of the scheduler.
    """

    scheduler_exists: bool
    scheduler: list[torch.optim.lr_scheduler.LRScheduler]
    best_optimizer: dict
    best_scheduler: list[dict]

    def __init__(
        self,
        params: ParamsT,
        optimizer_args: dict[str, Any] = {},
        scheduler: type = NoScheduler,
        scheduler_args: dict[str, Any] = {},
        **kwargs,
    ) -> None:
        # initializes torch.optim.Optimizer part from params and optimizer_args
        super().__init__(params, **optimizer_args)
        # initializes scheduler if given
        self.scheduler_exists = not (scheduler == NoScheduler)
        if self.scheduler_exists:
            if not issubclass(scheduler, torch.optim.lr_scheduler.LRScheduler):
                raise ValueError(
                    f"Cannot create a {self.__class__.__name__} from scheduler class:\
                    {scheduler}; it must be a subclass of\
                    torch.optim.lr_scheduler.LRScheduler"
                )
            self.scheduler = [scheduler(self, **scheduler_args)]
        else:
            self.scheduler = []

        self.best_optimizer = copy.deepcopy(self.state_dict())
        if self.scheduler_exists:
            self.best_scheduler = [copy.deepcopy(self.scheduler[0].state_dict())]
        else:
            self.best_scheduler = []

    def optimizer_step(self, closure: Callable[[], float]) -> None:
        """Performs an optimization step and updates the scheduler if it exists.

        Args:
            closure: A closure that reevaluates the model and returns the loss.
        """
        self.inner_step(closure)
        if self.scheduler_exists:
            self.scheduler[0].step()

    @abstractmethod
    def inner_step(self, closure: Callable[[], float]) -> None:  # pragma: no cover
        """Abstract method for performing the inner optimization step.

        Args:
            closure: A closure that reevaluates the model and returns the loss.
        """
        pass

    def update_best_optimizer(self) -> None:
        """Updates the best optimizer state."""
        self.best_optimizer = copy.deepcopy(self.state_dict())
        if self.scheduler_exists:
            self.best_scheduler[0] = copy.deepcopy(self.scheduler[0].state_dict())

    def dict_for_save(self) -> dict:
        """Returns a dictionary containing the best optimizer and scheduler states.

        Returns:
            dict: dictionary containing the best optimizer and scheduler states.
        """
        res = {"optimizer_state_dict": self.best_optimizer}
        if self.scheduler_exists:
            res["scheduler_state_dict"] = self.best_scheduler[0]
        return res

    def load(self, checkpoint: dict) -> None:
        """Loads the optimizer and scheduler states from a checkpoint.

        Args:
            checkpoint: dictionary containing the optimizer and scheduler states.
        """
        try:
            self.load_state_dict(checkpoint["optimizer_state_dict"])
            if self.scheduler_exists:
                self.scheduler[0].load_state_dict(checkpoint["scheduler_state_dict"])
        # except FileNotFoundError: #Rémi: ????????
        except KeyError:
            print("optimizer was not loaded from file: training needed")


class ScimbaAdam(AbstractScimbaOptimizer, torch.optim.Adam):
    """Scimba wrapper for Adam optimizer with optional learning rate scheduler.

    Args:
        params: Iterable of parameters to optimize or dicts defining parameter groups.
        optimizer_args: Additional arguments for the Adam optimizer. Defaults to {}.
        scheduler: Learning rate scheduler class.
            Defaults to torch.optim.lr_scheduler.StepLR.
        scheduler_args: Additional arguments for the scheduler. Defaults to {}.
        **kwargs: Arbitrary keyword arguments.
    """

    def __init__(
        self,
        params: ParamsT,
        optimizer_args: dict[str, Any] = {},
        scheduler: type = torch.optim.lr_scheduler.StepLR,
        scheduler_args: dict[str, Any] = {},
        **kwargs,
    ) -> None:
        if scheduler == torch.optim.lr_scheduler.StepLR:
            scheduler_args.setdefault("gamma", 0.99)
            scheduler_args.setdefault("step_size", 20)

        super().__init__(params, optimizer_args, scheduler, scheduler_args)

    def inner_step(self, closure: Callable[[], float]) -> None:
        """Performs the inner optimization step for ScimbaAdam.

        Args:
            closure: A closure that reevaluates the model and returns the loss.
        """
        closure()
        self.step()


class ScimbaSGD(AbstractScimbaOptimizer, torch.optim.SGD):
    """Scimba wrapper for SGD optimizer with optional learning rate scheduler.

    Args:
        params: Iterable of parameters to optimize or dicts defining parameter groups.
        optimizer_args: Additional arguments for the Adam optimizer. Defaults to {}.
        scheduler: Learning rate scheduler class.
            Defaults to torch.optim.lr_scheduler.StepLR.
        scheduler_args: Additional arguments for the scheduler. Defaults to {}.
        **kwargs: Arbitrary keyword arguments.
    """

    def __init__(
        self,
        params: ParamsT,
        optimizer_args: dict[str, Any] = {},
        scheduler: type = torch.optim.lr_scheduler.StepLR,
        scheduler_args: dict[str, Any] = {},
        **kwargs,
    ) -> None:
        if scheduler == torch.optim.lr_scheduler.StepLR:
            scheduler_args.setdefault("gamma", 0.99)
            scheduler_args.setdefault("step_size", 20)

        super().__init__(params, optimizer_args, scheduler, scheduler_args)

    def inner_step(self, closure: Callable[[], float]) -> None:
        """Performs the inner optimization step for ScimbaAdam.

        Args:
            closure: A closure that reevaluates the model and returns the loss.
        """
        closure()
        self.step()


class ScimbaLBFGS(AbstractScimbaOptimizer, torch.optim.LBFGS):
    """Scimba wrapper for LBFGS optimizer with optional learning rate scheduler.

    Args:
        params: Iterable of parameters to optimize or dicts defining parameter groups.
        optimizer_args: Additional arguments for the LBFGS optimizer. Defaults to {}.
        **kwargs: Arbitrary keyword arguments.
    """

    def __init__(self, params: ParamsT, optimizer_args: dict[str, Any] = {}, **kwargs):
        optimizer_args.setdefault("history_size", 15)
        optimizer_args.setdefault("max_iter", 5)
        optimizer_args.setdefault("line_search_fn", "strong_wolfe")

        super().__init__(params, optimizer_args)

    def inner_step(self, closure: Callable[[], float]) -> None:
        """Performs the inner optimization step for ScimbaLBFGS.

        Args:
            closure: A closure that reevaluates the model and returns the loss.
        """
        # super(AbstractScimbaOptimizer, self).step(closure)
        self.step(closure)


class ScimbaCustomOptomizer(AbstractScimbaOptimizer, ABC):
    """An abstract class of which user defined optimizer must inherit."""

    @abstractmethod
    def step(self, closure: Callable[[], float]):
        """To be implemented in subclasses: applies one step of optimizer.

        Args:
            closure: A closure that reevaluates the model and returns the loss.

        """


class ScimbaMomentum(ScimbaCustomOptomizer):
    """Custom Momentum optimizer with scheduler.

    For an example of a custom optimizer inheriting from AbstractScimbaOptimizer.

    Args:
        params: Iterable of parameters to optimize or dicts defining parameter groups.
        lr: learning rate
        momentum: momentum
    """

    def __init__(self, params: ParamsT, lr: float = 1e-3, momentum: float = 0.0):
        super().__init__(
            params,
            optimizer_args={"defaults": {"lr": lr}},
            scheduler=torch.optim.lr_scheduler.StepLR,
            scheduler_args={"gamma": 0.99, "step_size": 10},
        )

        self.momentum = momentum
        self.state = defaultdict(dict)
        for group in self.param_groups:
            for p in group["params"]:
                self.state[p] = dict(mom=torch.zeros_like(p.data))

    # this step method must be implemented in order for the scheduler to work properly
    def step(self, closure: Callable[[], float] | None = None):
        """Re-implements the step method.

        Args:
            closure: A closure that reevaluates the model and returns the loss.
        """
        for group in self.param_groups:
            for p in group["params"]:
                mom = self.state[p]["mom"]
                mom = self.momentum * mom - group["lr"] * p.grad.data
                p.data += mom

    def inner_step(self, closure: Callable[[], float]) -> None:
        """The inner step method.

        Args:
            closure: A closure that reevaluates the model and returns the loss.
        """
        closure()
        self.step()


if __name__ == "__main__":  # pragma: no cover
    import math

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

    class DummyScheduler:
        """For test."""

    try:
        opt_test = ScimbaAdam(list(net.parameters()), scheduler=DummyScheduler)
    except ValueError as error:
        print(error)

    # Batch of 10000 samples, each of size 10
    input_tensor = torch.randn(10000, 10)
    # learn sum function
    # Target tensor with batch size 10000
    target_tensor = torch.sum(input_tensor, dim=1)[:, None]

    loss = [torch.tensor(float("+inf"))]
    best_loss = float("+inf")
    best_net = copy.deepcopy(net.state_dict())

    opt = ScimbaAdam(list(net.parameters()))
    # opt = ScimbaMomentum(list(net.parameters()))

    loss_func = torch.nn.MSELoss()
    # opt.zero_grad()

    def closure() -> float:
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

    # perform one step
    # optimizer_step_count_before = opt._step_count
    opt.optimizer_step(closure)
    # optimizer_step_count_after = opt._step_count
    # print("step_count before, after: ", optimizer_step_count_before, ", ",\
    # optimizer_step_count_after)

    epochs = 1000
    for epoch in range(epochs):
        opt.optimizer_step(closure)

        if math.isinf(loss[0].item()) or math.isnan(loss[0].item()):
            loss[0] = torch.tensor(best_loss)
            net.load_state_dict(best_net)

        if loss[0].item() < best_loss:
            best_loss = loss[0].item()
            best_net = copy.deepcopy(net.state_dict())
            opt.update_best_optimizer()

        if epoch % 100 == 0:
            print("epoch: ", epoch, "loss: ", loss[0].item())
            print("lr: ", opt.param_groups[0]["lr"])

    net.load_state_dict(best_net)
    closure()
    print("loss after training: ", loss[0].item())
    # optimizer_step_count_after = opt._step_count
    # print("step_count after: ", optimizer_step_count_after)

    print("\n")
    # print("dict_for_save: ", opt.dict_for_save())
    print("state_dict   : ", opt.state_dict())
    print("\n")
    optt = ScimbaAdam(list(net.parameters()))
    # print("dict_for_save: ", optt.dict_for_save())
    print("state_dict   : ", optt.state_dict())
    print("\n")
    optt.load(opt.dict_for_save())
    # print("dict_for_save: ", optt.dict_for_save())
    print("state_dict   : ", optt.state_dict())
    print("\n")
    # print( "==", optt.state_dict() == opt.state_dict())

    opt2 = ScimbaLBFGS(list(net.parameters()))

    def closure() -> float:
        """For test.

        Returns:
            For test.
        """
        opt2.zero_grad()
        # Forward pass
        output_tensor = net(input_tensor)
        loss[0] = loss_func(output_tensor, target_tensor)
        loss[0].backward(retain_graph=True)
        return loss[0].item()

    epochs = 1000
    for epoch in range(epochs):
        opt2.optimizer_step(closure)

        if math.isinf(loss[0].item()) or math.isnan(loss[0].item()):
            loss[0] = torch.tensor(best_loss)
            net.load_state_dict(best_net)

        if loss[0].item() < best_loss:
            best_loss = loss[0].item()
            best_net = copy.deepcopy(net.state_dict())
            opt2.update_best_optimizer()

        if epoch % 100 == 0:
            print("epoch: ", epoch, "loss: ", loss[0].item())

    net.load_state_dict(best_net)
    closure()
    print("loss after training: ", loss[0].item())

    print("net( torch.ones( 10 ) ) : ", net(torch.ones(10)))

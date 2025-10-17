"""Defines an abstract class for an approximation space."""

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Generator
from warnings import warn

import torch

from scimba_torch.integration.monte_carlo import TensorizedSampler
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor


### Describe a numerical model with where we gives a transition between 2 times
### We assume that the formulation between two time can be non explicit
class AbstractApproxSpace(ABC):
    """Abstract class for an approximation space.

    This class provides the base structure for approximation spaces, including
    methods for gradient computation, evaluation, and handling degrees of freedom.

    Args:
        nb_unknowns: Number of unknowns in the approximation space.
        **kwargs: Additional keyword arguments.
    """

    type_space: str  #: Type of the approximation space.
    integrator: TensorizedSampler  #: An integrator for tensorized sampling.
    ndof: int  #: Number of degrees of freedom.

    def __init__(self, nb_unknowns: int, **kwargs):
        self.nb_unknowns: int = (
            nb_unknowns  #: Number of unknowns in the approximation space.
        )
        #: dictionary to store the best approximation state.
        self.best_approx: dict = {}

    def grad(
        self,
        w: torch.Tensor | MultiLabelTensor,
        y: torch.Tensor | LabelTensor,
    ) -> torch.Tensor | Generator[torch.Tensor, None, None]:
        """Computes the gradient of `w` with respect to `y`.

        Args:
            w: The tensor to differentiate.
            y: The tensor with respect to which the gradient is computed.

        Returns:
            torch.Tensor | Generator[torch.Tensor, None, None]: The gradient tensor.

        Raises:
            ValueError: If `w` and `y` are not compatible tensor types or shapes.

        """
        if isinstance(w, MultiLabelTensor):
            w = w.w
            if not isinstance(y, LabelTensor):
                raise ValueError(
                    "y must be a LabelTensor. You must differentiate with respect to "
                    "all coordinates."
                )
        if (w.ndim > 1) and (not w.shape[1] == 1):
            raise ValueError(
                "this function must call on a scalar unknown (shape =(batch,1)). "
                "Call get_component before to extract the component"
            )
        if isinstance(y, LabelTensor):
            y = y.x
        ones = torch.ones_like(w)
        grad_output = torch.autograd.grad(
            w, y, ones, create_graph=True, allow_unused=True
        )[0]
        if y.size(1) > 1:
            return (grad_output[:, i, None] for i in range(y.size(1)))
        else:
            return grad_output[:, 0, None]

    @abstractmethod
    def evaluate(
        self, *args: LabelTensor, with_last_layer: bool = True
    ) -> MultiLabelTensor:
        """Evaluates the approximation space.

        Args:
            *args: Input tensors for evaluation.
            with_last_layer: Whether to include the last layer in evaluation.
                (Default value = True)

        Returns:
            The result of the evaluation.

        """
        pass

    @abstractmethod
    def jacobian(self, *args: LabelTensor) -> torch.Tensor:
        """Computes the Jacobian of the approximation space.

        Args:
            *args: Input tensors for Jacobian computation.

        Returns:
            The Jacobian tensor.

        """
        pass

    @abstractmethod
    def set_dof(self, theta: torch.Tensor, flag_scope: str) -> None:
        """Sets the degrees of freedom for the approximation space.

        Args:
            theta: Tensor representing the degrees of freedom.
            flag_scope: Scope flag for setting degrees of freedom.
        """
        pass

    @abstractmethod
    def get_dof(self, flag_scope: str, flag_format: str) -> torch.Tensor | list:
        """Gets the degrees of freedom for the approximation space.

        Args:
            flag_scope: Scope flag for getting degrees of freedom.
            flag_format: Format flag for the degrees of freedom.

        Returns:
            The degrees of freedom.

        """
        pass

    def dict_for_save(self) -> dict:
        """Returns a dictionary representing the space that can be stored/saved.

        Returns:
            A dictionary representing the space.

        """
        assert isinstance(self, torch.nn.Module)
        state_dict = {"current_state_dict": deepcopy(self.state_dict())}
        if "model_state_dict" in self.best_approx:
            state_dict["best_state_dict"] = deepcopy(
                self.best_approx["model_state_dict"]
            )
        return state_dict

    def load_from_dict(self, checkpoint: dict) -> None:
        """Restores the space from a dictionary.

        Args:
            checkpoint: dictionary containing the state to restore.

        """
        assert isinstance(self, torch.nn.Module)
        self.load_state_dict(checkpoint["current_state_dict"])
        if "best_state_dict" in checkpoint:
            self.best_approx["model_state_dict"] = checkpoint["best_state_dict"]
        else:
            self.best_approx = {}
        self.eval()

    def update_best_approx(self) -> None:
        """Updates the best approximation state to the current approximation state."""
        assert isinstance(self, torch.nn.Module)
        self.best_approx["model_state_dict"] = deepcopy(self.state_dict())

    def load_from_best_approx(self) -> None:
        """Loads the current approximation state from the best approximation state.

        Notes:
            If no best approximation has been saved with `update_best_approx()` yet,
            raises a warning and does nothing.
        """
        assert isinstance(self, torch.nn.Module)
        if "model_state_dict" in self.best_approx:
            self.load_state_dict(self.best_approx["model_state_dict"])
            self.eval()
        else:
            warn(
                "self.best_approx has no key model_state_dict; nothing will happen; "
                "perhaps update_best_approx has not been called",
                RuntimeWarning,
            )

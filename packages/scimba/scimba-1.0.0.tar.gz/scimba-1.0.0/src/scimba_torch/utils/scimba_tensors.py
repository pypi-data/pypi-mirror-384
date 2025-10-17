"""Utility classes for handling tensors with associated labels in PyTorch."""

from __future__ import annotations

from typing import Sequence

import torch


class MultiLabelTensor:
    """A class to manage tensors with space coordinates and associated labels.

    Args:
        w: The main tensor of coordinates, expected to have shape `(batch_size, dim)`.
        labels: A list of tensors containing labels for filtering operations.
            Defaults to empty list.

    Raises:
        ValueError: If input tensor has dimension <= 1, or if w and labels
            have different shapes[0].
    """

    def __init__(
        self,
        w: torch.Tensor,
        labels: list[torch.Tensor] | None = [],
    ):
        self.w: torch.Tensor = w  #: The main tensor representing coordinates

        if w.dim() <= 1:
            raise ValueError("can not create MultiLabelTensor from tensors of dim <= 1")

        #: Number of dimensions in the coordinates
        self.size: int = w.shape[1]

        #: A list of label tensors, where each tensor contains integer labels
        #: associated with the corresponding batch entries.
        self.labels: list[torch.Tensor] = [] if labels is None else labels

        if not all(label.shape[0] == w.shape[0] for label in self.labels):
            raise ValueError("w and labels must have the same shape[0]")

        #: The shape of the tensor `w`, useful for validation and debugging.
        self.shape: torch.Size = w.shape

    def get_components(
        self, index: int | None = None
    ) -> torch.Tensor | tuple[torch.Tensor, ...]:
        """Retrieve specific components of the tensor `w`.

        Args:
            index: The specific dimension to extract from the tensor. If `None`,
                all dimensions are extracted as a tuple of tensors.

        Returns:
            - If `index` is specified, a single tensor corresponding to the selected
              dimension.
            - If `index` is `None`, a tuple of tensors for all dimensions.
        """
        if (index is None) and (not (self.size == 1)):
            # Return all dimensions as a tuple
            return tuple(self.w[:, i, None] for i in range(self.size))
        else:
            if self.size == 1:
                return self.w[:, 0, None]
            else:
                return self.w[:, index, None]

    def restrict_to_labels(
        self, component: torch.Tensor | None = None, labels: list[int] | None = []
    ) -> torch.Tensor:
        """Filter tensor `w` (or one of its components) by a list of reference labels.

        Args:
            component: The specific component to be filtered. If `None`, `self.w`.
            labels: A list of integers specifying the reference labels to filter rows.
                If `None`, no filtering is applied.

        Returns:
            Filtered tensor based on the following logic:
            - If `component` and `labels` are specified, `component` filtered by input
              list of labels
            - If `component` is `None` and `labels` are specified, `self.w` filtered by
              input list of labels
            - If `component` is provided and `labels` is None, a copy of `component`
            - Otherwise a copy of `self.w`

        Raises:
            ValueError: If provided reference labels do not match the structure of the
                label tensors.
        """
        nlabels = [] if labels is None else labels
        # Validate the input
        if len(self.labels) < len(nlabels):
            raise ValueError(
                "Provided reference labels do not match the structure of the "
                "label tensors."
            )
        # Initialize a boolean mask
        batch_size = self.w.shape[0]
        if len(nlabels) == 0:
            mask = torch.arange(batch_size)
        else:
            mask = torch.ones(batch_size, dtype=torch.bool)
            for label_tensor, ref_label in zip(self.labels, nlabels):
                mask &= label_tensor == ref_label
        # Filter the tensor `w` based on the mask
        if component is not None:  # 1D case
            res = component[mask, 0, None]
        else:
            res = self.w[mask, :]
        return res


class LabelTensor:
    """Class for tensors representing space coordinates.

    Args:
        x: Coordinates tensor.
        labels: Labels for the coordinates (e.g. labels for boundary conditions, etc.).
            If None, creates zero labels.

    Raises:
        ValueError: If x has dimension <= 1, or if x and labels have different shape[0].
    """

    def __init__(
        self,
        x: torch.Tensor,
        labels: torch.Tensor | None = None,
    ):
        self.x: torch.Tensor = x  #: Coordinate tensor

        if x.dim() <= 1:
            raise ValueError("can not create LabelTensor from tensors of dim <= 1")

        self.dim: int = x.shape[1]  #: Space dimension

        self.labels: torch.Tensor  #: Labels for the coordinates
        if labels is not None:
            if not labels.shape[0] == x.shape[0]:
                raise ValueError(
                    "x and labels must have the same shape[0]: has %d and %d"
                    % (x.shape[0], labels.shape[0])
                )

            self.labels = labels
        else:
            self.labels = torch.zeros(x.shape[0], dtype=torch.int32)

        self.shape = x.shape

    def __getitem__(self, key: int | slice) -> LabelTensor:
        """Overload the getitem [] operator.

        Args:
            key: Index where you want the data.

        Returns:
            The space tensor with the data only for the key.
        """
        if isinstance(key, int):
            return LabelTensor(self.x[key, None], self.labels[key, None])
        else:
            return LabelTensor(self.x[key], self.labels[key])

    def __setitem__(self, key: int | slice, value: LabelTensor) -> None:
        """Overload the setitem [] operator.

        Args:
            key: Index where you want to set the data.
            value: New values for the LabelTensor associated to the given key.
        """
        self.x[key] = value.x
        self.labels[key] = value.labels

    def repeat(self, repeats: int | torch.Tensor) -> LabelTensor:
        """Overload the repeat function.

        Args:
            repeats: The size of the repeat.

        Returns:
            New LabelTensor with repeated coordinates and labels.
        """
        return LabelTensor(
            torch.repeat_interleave(self.x, repeats, dim=0),
            torch.repeat_interleave(self.labels, repeats, dim=0),
        )

    def get_components(
        self, label: int | None = None
    ) -> torch.Tensor | tuple[torch.Tensor, ...]:
        """Returns the components from the current LabelTensor.

        Args:
            label: The label of the x that the users want. If None, returns all
                components.

        Returns:
            The list of coordinates. If dim=1, returns single tensor, otherwise tuple of
                tensors.

        Raises:
            ValueError: If no coordinates with the specified label are found.
        """
        if label is None:
            if self.dim == 1:
                return self.x[:, 0, None]
            else:
                return tuple(self.x[:, i, None] for i in range(self.dim))
        else:
            mask = self.labels == label
            if mask.sum() == 0:
                raise ValueError(f"No coordinates with label {label}")
            else:
                if self.dim == 1:
                    return self.x[mask, 0, None]
                else:
                    return tuple(self.x[mask, i, None] for i in range(self.dim))

    @staticmethod
    def cat(inputs: Sequence[LabelTensor]) -> LabelTensor:
        """Concatenate a list of LabelTensors.

        Args:
            inputs: The list of LabelTensors to concatenate.

        Returns:
            The LabelTensor which contains all the previous LabelTensors.
        """
        return LabelTensor(
            torch.cat([data.x for data in inputs], dim=0),
            torch.cat([data.labels for data in inputs], dim=0),
        )

    def __str__(self) -> str:
        """String representation of the LabelTensor.

        Returns:
            A string describing the LabelTensor.
        """
        return f"LabelTensor:\n x = {self.x}\n labels = {self.labels}"

    def detach(self):
        """Detach the space tensor.

        Returns:
            The LabelTensor where x is detached on CPU.
        """
        return LabelTensor(self.x.detach(), self.labels)

    def __add__(self, other: int | float | torch.Tensor | LabelTensor) -> LabelTensor:
        """Overload the + operator.

        Args:
            other: A value or tensor to add.

        Returns:
            The LabelTensor resulting from the addition.

        Raises:
            TypeError: If other is not a valid type.
            ValueError: If labels do not match when adding two LabelTensors.
        """
        if not isinstance(other, (int, float, torch.Tensor, LabelTensor)):
            raise TypeError(
                f"Invalid type {type(other)} for element added to LabelTensor"
            )

        if isinstance(other, LabelTensor):
            # assert not torch.logical_xor(
            #     self.labels, other.labels
            # ).sum(), "Labels do not match" #Remi: ???
            if not torch.all(self.labels == other.labels):
                raise ValueError("Labels do not match")

            return LabelTensor(self.x + other.x, self.labels)
        else:
            return LabelTensor(self.x + other, self.labels)

    def __sub__(self, other: int | float | torch.Tensor | LabelTensor) -> LabelTensor:
        """Overload the - operator.

        Args:
            other: A value or tensor to subtract.

        Returns:
            The LabelTensor resulting from the subtraction.

        Raises:
            TypeError: If other is not a valid type.
            ValueError: If labels do not match when subtracting two LabelTensors.
        """
        if not isinstance(other, (int, float, torch.Tensor, LabelTensor)):
            raise TypeError(
                f"Invalid type {type(other)} for element subtracted to LabelTensor"
            )

        if isinstance(other, LabelTensor):
            # assert not torch.logical_xor(
            #     self.labels, other.labels
            # ).sum(), "Labels do not match"
            if not torch.all(self.labels == other.labels):
                raise ValueError("Labels do not match")

            return LabelTensor(self.x - other.x, self.labels)
        else:
            return self + (-other)

    def __mul__(self, other: int | float | torch.Tensor | LabelTensor) -> LabelTensor:
        """Overload the * operator.

        Args:
            other: A value or tensor to multiply.

        Returns:
            The LabelTensor resulting from the multiplication.

        Raises:
            TypeError: If other is not a valid type.
            ValueError: If labels do not match when multiplying two LabelTensors.
        """
        if not isinstance(other, (int, float, torch.Tensor, LabelTensor)):
            raise TypeError(
                f"Invalid type {type(other)} for element multiplied to LabelTensor"
            )

        if isinstance(other, LabelTensor):
            # assert not torch.logical_xor(
            #     self.labels, other.labels
            # ).sum(), "Labels do not match"
            if not torch.all(self.labels == other.labels):
                raise ValueError("Labels do not match")

            return LabelTensor(self.x * other.x, self.labels)
        else:
            return LabelTensor(self.x * other, self.labels)

    def __rmul__(self, other: int | float | torch.Tensor | LabelTensor) -> LabelTensor:
        """Overload the right * operator.

        Args:
            other: A value or tensor to multiply.

        Returns:
            The LabelTensor resulting from the multiplication.
        """
        return self * other

    def no_grad(self) -> LabelTensor:
        """Returns a LabelTensor with no grad on x.

        Returns:
            A LabelTensor with x detached from the computation graph.
        """
        x_no_grad = self.x.clone().detach()
        x_no_grad.requires_grad = False
        return LabelTensor(x_no_grad, self.labels)

    def unsqueeze(self, dim: int) -> LabelTensor:
        """Unsqueeze the space tensor.

        Args:
            dim: Dimension to unsqueeze.

        Returns:
            A LabelTensor with the specified dimension unsqueezed.
        """
        return LabelTensor(self.x.unsqueeze(dim), self.labels)

    def concatenate(self, other: LabelTensor, dim: int) -> LabelTensor:
        """Concatenate two LabelTensors along a specified dimension.

        Args:
            other: The LabelTensor to concatenate with the current instance.
            dim: The dimension along which to concatenate.

        Returns:
            The LabelTensor which contains the concatenation of the two LabelTensors.
        """
        try:
            return LabelTensor(
                torch.cat((self.x, other.x), dim=dim),
                torch.cat((self.labels, other.labels), dim=dim),
            )
        except IndexError:
            return LabelTensor(
                torch.cat((self.x, other.x), dim=dim),
                torch.stack((self.labels, other.labels), dim=dim),
            )

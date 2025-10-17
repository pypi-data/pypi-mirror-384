"""Defines the GradPotential class for neural networks."""

import torch
from torch import nn

from scimba_torch.neural_nets.coordinates_based_nets.activation import (
    activation_function,
)


class GradPotential(nn.Module):
    """Combines a linear transformation on two input tensors :code:`y` and :code:`p`.

    Applies an activation function, scales the result based on :code:`p`,
    and returns a matrix product of the transformed tensors.

    The module is used to model potential gradients in neural network architectures,
    especially in problems involving structured data.

    Args:
        y_dim: Dimension of the input tensor :code:`y`.
        p_dim: Dimension of the input tensor :code:`p`.
        width: Width of the internal layers (i.e., the number of units in the hidden
            layers).
        **kwargs: Additional keyword arguments. The activation function type can be
            passed as a keyword argument (e.g., "tanh", "relu").
    """

    def __init__(self, y_dim: int, p_dim: int, width: int, **kwargs):
        super().__init__()
        self.width = width
        #: Linear transformation for the `y` input tensor.
        self.linear_y: nn.Linear = nn.Linear(y_dim, width, bias=False)
        #: Linear transformation for the `p` input tensor.
        self.linear_p: nn.Linear = nn.Linear(p_dim, width)
        #: Activation function type (e.g., 'tanh') applied to the sum of the linear
        #: transformations.
        self.activation_type: str = kwargs.get("activation", "tanh")
        #: Linear scaling transformation for the `p` tensor.
        self.scaling: nn.Linear = nn.Linear(p_dim, width)
        #: Activation function applied to the sum of the linear transformations.
        self.activation = activation_function(self.activation_type, **kwargs)

    def forward(self, y: torch.Tensor, p: torch.Tensor) -> torch.Tensor:
        """Computes the forward pass.

        This method combines the transformations of the input tensors `y` and `p`,
        applies an activation function, scales the result based on `p`,
        and returns the matrix product.

        Args:
            y: The input tensor of dimension `(batch_size, y_dim)`.
            p: The input tensor of dimension `(batch_size, p_dim)`.

        Returns:
            The output tensor after applying the transformation and scaling.
        """
        z = self.activation(self.linear_y(y) + self.linear_p(p))
        return (self.scaling(p) * z) @ self.linear_y.weight

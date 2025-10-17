"""Defines the SympNet class for symplectic neural networks."""

import torch
from torch import nn

from scimba_torch.neural_nets.coordinates_based_nets.scimba_module import ScimbaModule
from scimba_torch.neural_nets.structure_preserving_nets.gradpotential import (
    GradPotential,
)


class SympLayer(nn.Module):
    """A layer of a symplectic neural network.

    It applies transformations to input tensors `x` and `y`
    based on the `GradPotential` module.

    Args:
        y_dim: Dimension of the input tensor `y`.
        p_dim: Dimension of the input tensor `p`.
        **kwargs: Additional keyword arguments. Parameters scaling and number can be
            passed.
    """

    def __init__(self, y_dim: int, p_dim: int, **kwargs):
        super().__init__()
        width = kwargs.get("width", 5)
        #: The first GradPotential module used for transformations.
        self.grad_potential1: GradPotential = GradPotential(y_dim, p_dim, width)
        #: The second GradPotential module used for transformations.
        self.grad_potential2: GradPotential = GradPotential(y_dim, p_dim, width)
        #: A flag indicating if parameters scaling should be applied.
        self.parameters_scaling: bool = kwargs.get("parameters_scaling", False)
        #: The index for the scaling parameter.
        self.parameters_scaling_number: int = kwargs.get("parameters_scaling_number", 0)

    def forward(
        self, x: torch.Tensor, y: torch.Tensor, p: torch.Tensor, sign: int = 1
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Performs the forward pass of the symplectic layer.

        Applies transformations using `GradPotential` layers, with optional scaling for
        the `p` tensor.

        Args:
            x: The input tensor `x` of shape `(batch_size, y_dim)`.
            y: The input tensor `y` of shape `(batch_size, y_dim)`.
            p: The input tensor `p` of shape `(batch_size, p_dim)`.
            sign: The sign used to apply the transformations. Default is 1.

        Returns:
            The output tensors `(x, y)` after transformations.
        """
        c = (
            p[:, self.parameters_scaling_number, None]
            if self.parameters_scaling
            else 1.0
        )

        if sign == 1:
            x, y = x, y + c * self.grad_potential1(x, p)
            x, y = x + c * self.grad_potential2(y, p), y
        else:
            x, y = x - c * self.grad_potential2(y, p), y
            x, y = x, y - c * self.grad_potential1(x, p)
        return x, y


class SympNet(ScimbaModule):
    """A symplectic neural network composed of multiple `SympLayer` layers.

    The network processes input tensors `x`, `y`, and `p`,
    applying transformations through each layer.

    Args:
        dim: The dimension of the state space.
        p_dim: The dimension of the parameter space.
        widths: The widths of the `SympLayer` layers. Default is `[20] * 5`.
        **kwargs: Additional keyword arguments for the layers.
    """

    def __init__(self, dim: int, p_dim: int, widths: list[int] = [20] * 5, **kwargs):
        super().__init__(in_size=dim + p_dim, out_size=dim, **kwargs)
        self.dim = dim
        self.y_dim = dim // 2
        self.p_dim = p_dim

        #: list of `SympLayer` layers that form the network.
        self.layers: nn.ModuleList = nn.ModuleList(
            [SympLayer(self.y_dim, p_dim, width=w, **kwargs) for w in widths]
        )

    def forward(self, inputs: torch.Tensor, with_last_layer: bool = True):
        """Applies the forward pass of the symplectic network.

        Args:
            inputs: the input tensor of shape `(batch_size, dim + p_dim)`.
            with_last_layer: whether to use the last layer of the network or not
                (default: True)

        Returns:
            The output tensor of shape `(batch_size, dim + p_dim)` after applying all
            layers.
        """
        x, y, p = inputs.tensor_split(
            (self.y_dim, 2 * self.y_dim),
            dim=-1,
        )

        for layer in self.layers:
            x, y = layer(x, y, p)

        return torch.cat((x, y), dim=-1)

    def inverse(self, inputs: torch.Tensor, with_last_layer: bool = True):
        """Applies the inverse pass of the symplectic network.

        Args:
            inputs: the input tensor of shape `(batch_size, dim + p_dim)`.
            with_last_layer: whether to use the last layer of the network or not
                (default: True)

        Returns:
            The output tensor of shape `(batch_size, dim + p_dim)` after applying all
            layers in reverse order.
        """
        x, y, p = inputs.tensor_split(
            (self.y_dim, 2 * self.y_dim),
            dim=1,
        )

        for layer in reversed(self.layers):
            x, y = layer(x, y, p, sign=-1)

        return torch.cat((x, y), dim=-1)

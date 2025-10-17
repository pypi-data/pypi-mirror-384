"""An invertible neural network made of RealNVP layers."""

from __future__ import annotations

from abc import ABC, abstractmethod

import torch
from torch import nn

from scimba_torch.neural_nets.coordinates_based_nets.mlp import GenericMLP
from scimba_torch.neural_nets.coordinates_based_nets.scimba_module import ScimbaModule


class InvertibleLayer(ScimbaModule, ABC):
    """An abstract class for an invertible layer."""

    @abstractmethod
    def backward(self, inputs: torch.Tensor, with_last_layer: bool = True):
        """Abstract method for the backward pass of the invertible layer.

        Args:
            inputs: the input tensor
            with_last_layer: whether to use the last layer of the network or not
                (default: True)
        """


class RealNVPFlowLayer(InvertibleLayer):
    r"""Conservative volumes flow where the type of neural network is given by net.

    It is to approximate probability :math:`p(y\mid x)`.

    Flow:

    .. math::

        z[k:d] &= y[k:d] \exp^{s(y[1:k],x)} + t(y[1:k],x) \\
        z[1:k] &= y[1:k]

    with :math:`s` the scale and :math:`t` the shift/translation term.

    Args:
        dim: the dimension of the input x of the flow
        p_dim: the dimension of the conditional input y of the flow
        net_type: the type of neural network used
        **kwargs: other arguments for the neural network:

            - :code:`parity`: parity of the layer
            - :code:`scale`: to indicate whether we scale or not
            - :code:`shift`: to indicate whether we shift or not
    """

    def __init__(
        self,
        dim: int,
        p_dim: int,
        net_type: nn.Module = GenericMLP,
        **kwargs,
    ):
        super().__init__(in_size=dim + p_dim, out_size=dim)
        #: dimension of the input x of the flow
        self.dim: int = dim
        #: dimension of the conditional input y of the flow
        self.dim_p: int = p_dim  # TODO: uniformize p_dim vs dim_p
        #: type of neural network used
        self.net_type: nn.Module = net_type
        #: parity of the layer
        self.parity: bool = kwargs.get("parity", False)
        #: scale the layer
        self.scale: bool = kwargs.get("scale", True)
        #: shift the layer
        self.shift: bool = kwargs.get("shift", True)
        self.s_cond = lambda x: x.new_zeros(x.size(0), self.dim // 2 + self.dim_p)
        self.t_cond = lambda x: x.new_zeros(x.size(0), self.dim // 2 + self.dim_p)
        if self.scale:
            self.s_cond = self.net_type(
                in_size=self.dim // 2 + self.dim_p, out_size=self.dim // 2, **kwargs
            )
        if self.shift:
            self.t_cond = self.net_type(
                in_size=self.dim // 2 + self.dim_p, out_size=self.dim // 2, **kwargs
            )

    def forward(
        self, y: torch.Tensor, p: torch.Tensor, with_last_layer: bool = True
    ) -> torch.Tensor:
        """Compute the flow.

        Args:
            y: the tensor of the data y
            p: the tensor of the conditional data x
            with_last_layer: whether to use the last layer of the network or not
                (default: True)

        Returns:
            the tensor containing the result
        """
        y0, y1 = y[:, ::2], y[:, 1::2]
        if self.parity:
            y0, y1 = y1, y0
        s = self.s_cond(torch.cat([y0, p], axis=1))
        t = self.t_cond(torch.cat([y0, p], axis=1))
        z0 = y0  # untouched half
        # transform this half as a function of the other
        z1 = torch.exp(s) * y1 + t
        if self.parity:
            z0, z1 = z1, z0
        z = torch.cat([z0, z1], dim=1)
        return z

    def backward(
        self, z: torch.Tensor, p: torch.Tensor, with_last_layer: bool = True
    ) -> torch.Tensor:
        """Compute the backward flow.

        Args:
            z: the tensor of the data z
            p: the tensor of the conditional data x
            with_last_layer: whether to use the last layer of the network or not
                (default: True)

        Returns:
            the tensor containing the result
        """
        z0, z1 = z[:, ::2], z[:, 1::2]
        if self.parity:
            z0, z1 = z1, z0
        s = self.s_cond(torch.cat([z0, p], axis=1))
        t = self.t_cond(torch.cat([z0, p], axis=1))
        y0 = z0  # this was the same
        y1 = (z1 - t) * torch.exp(-s)  # reverse the transform on this half
        if self.parity:
            y0, y1 = y1, y0
        y = torch.cat([y0, y1], dim=1)
        return y


class InvertibleNet(ScimbaModule):
    """An invertible neural network made of RealNVP layers.

    Args:
        dim: dimension of the input data
        p_dim: dimension of the conditional input data
        nb_layers: number of invertible layers
        layer_type: type of invertible layer (default: RealNVPFlowLayer)
        net_type: type of neural network used in each layer (default: GenericMLP)
        **kwargs: other arguments for the invertible layers.

    """

    def __init__(
        self,
        dim: int,
        p_dim: int,
        nb_layers: int = 2,
        layer_type: InvertibleLayer = RealNVPFlowLayer,
        net_type: nn.Module = GenericMLP,
        **kwargs,
    ):
        super().__init__(in_size=dim + p_dim, out_size=dim)
        self.dim = dim
        self.p_dim = p_dim
        self.layer_type = layer_type
        self.layers = nn.ModuleList(
            [
                self.layer_type(dim, p_dim, net_type, **kwargs)
                for i in range(0, nb_layers)
            ]
        )
        self.nb_layers = nb_layers

    def forward(
        self, inputs: torch.Tensor, with_last_layer: bool = True
    ) -> torch.Tensor:
        """Applies the forward pass of the invertible network.

        Args:
            inputs: the input tensor of shape `(batch_size, dim + p_dim)`.
            with_last_layer: whether to use the last layer of the network or not
                (default: True)

        Returns:
            The output tensor of shape `(batch_size, dim + p_dim)` after applying all
            layers.
        """
        y, p = inputs.tensor_split(
            (self.dim),
            dim=-1,
        )
        for layer in self.layers:
            y = layer.forward(y, p)
        return y

    def backward(
        self, inputs: torch.Tensor, with_last_layer: bool = True
    ) -> torch.Tensor:
        """Applies the backward pass of the invertible network.

        Args:
            inputs: the input tensor of shape `(batch_size, dim + p_dim)`.
            with_last_layer: whether to use the last layer of the network or not
                (default: True)

        Returns:
            the output tensor of shape `(batch_size, dim + p_dim)` after applying
                all layers in reverse order.
        """
        y, mu = inputs.tensor_split(
            (self.dim),
            dim=-1,
        )
        for layer in reversed(self.layers):
            y = layer.backward(y, mu)
        return y

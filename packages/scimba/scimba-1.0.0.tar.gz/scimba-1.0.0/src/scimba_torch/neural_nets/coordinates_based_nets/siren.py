"""Siren architecture implementation."""

import numpy as np
import torch
from torch import nn

from scimba_torch.neural_nets.coordinates_based_nets.scimba_module import ScimbaModule

from .activation import Sine


class SirenLayer(nn.Module):
    """Class representing a Siren Layer.

    Args:
        in_size: Dimension of the inputs.
        out_size: Dimension of the outputs.
        w0: Frequency parameter. Defaults to 1.
        c: Initialization parameter. Defaults to 6.
        is_first: Whether this is the first layer. Defaults to False.
        use_bias: Whether to use bias. Defaults to True.
    """

    def __init__(
        self,
        in_size: int,
        out_size: int,
        w0: int = 1,
        c: int = 6,
        is_first: bool = False,
        use_bias: bool = True,
    ):
        super().__init__()
        self.in_size = in_size  #: Dimension of the inputs.
        self.is_first = is_first  #: Whether this is the first layer.
        self.out_size = out_size  #: Dimension of the outputs.

        self.layer = nn.Linear(
            in_size, out_size, bias=use_bias
        )  #: The linear layer applied to the vector of features.
        self.init_(self.layer.weight, self.layer.bias, c=c, w0=w0)

        self.activation = Sine(freq=w0)  #: The sine activation function.

    def init_(self, weight: torch.Tensor, bias: torch.Tensor, c: int, w0: int):
        """Init the weights of the layer using the specific Siren initialization.

        Args:
            weight: The weight of the layer to initialize.
            bias: The bias of the layer to initialize.
            c: A parameter for the weight initialization.
            w0: The frequency of the sinus activation function.
        """
        dim = self.in_size

        w_std = (1 / dim) if self.is_first else (np.sqrt(c / dim) / w0)
        torch.nn.init.uniform_(weight, -w_std, w_std)

        if bias is not None:
            torch.nn.init.uniform_(bias, -w_std, w_std)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the network to the inputs.

        Args:
            x: Input tensor.

        Returns:
            The result of the layer.
        """
        return self.activation(self.layer(x))


class SirenNet(ScimbaModule):
    """Class representing a Siren architecture with optional ResNet layers.

    Args:
        in_size: dimension of inputs
        out_size: dimension of outputs
        **kwargs: Additional keyword arguments:

            - `w` (:code:`int`): frequency for the internal layers' activation functions
            - `w0` (:code:`int`): frequency for the first layer's activation function
            - `layer_sizes` (:code:`list[int]`): list of the size for each layer
            - `use_res_net` (:code:`bool`, default=False): whether to use a ResNet
              architecture
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__(in_size, out_size, **kwargs)
        self.layer_sizes = kwargs.get("layer_sizes", [20, 20, 20])
        self.w = kwargs.get("w", 1)
        self.w0 = kwargs.get("w0", 30)

        #: list of Siren layers, potentially with residual connections
        self.layers = nn.ModuleList([])

        # First layer (special initialization)
        self.layers.append(
            SirenLayer(
                in_size=self.in_size,
                out_size=self.layer_sizes[0],
                w0=self.w0,
                use_bias=True,
                is_first=True,
            )
        )

        # Hidden layers
        for i in range(1, len(self.layer_sizes) - 1):
            self.layers.append(
                SirenLayer(
                    in_size=self.layer_sizes[i],
                    out_size=self.layer_sizes[i + 1],
                    w0=self.w,
                    use_bias=True,
                    is_first=False,
                )
            )

        # Output layer
        self.output_layer = nn.Linear(self.layer_sizes[-1], self.out_size)

    def forward(self, x: torch.Tensor, with_last_layer: bool = True) -> torch.Tensor:
        """Apply the network to the inputs x.

        Args:
            x: input tensor
            with_last_layer: Whether to apply the final output layer

        Returns:
            the result of the network
        """
        for layer in self.layers:
            x = layer(x)

        # Output layer
        if with_last_layer:
            x = self.output_layer(x)
        return x

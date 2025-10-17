"""PirateNet architecture implementation."""

import torch
from torch import nn

from scimba_torch.neural_nets.coordinates_based_nets.features import EnhancedFeatureNet
from scimba_torch.neural_nets.coordinates_based_nets.scimba_module import ScimbaModule

from .activation import activation_function


class PirateNetBlock(ScimbaModule):
    """Implements a block of the PirateNet.

    Each block applies three linear transformations with activation
    to compute weighting matrices U and V, then updates the input `x`
    by combining these matrices using a residual scheme.

    Args:
        dim: Input and output dimension of the block, default is 1
        **kwargs: Additional parameters for block configuration
    """

    def __init__(self, dim: int = 1, **kwargs):
        super().__init__(dim, dim, **kwargs)
        self.in_size = dim
        self.out_size_embedded = dim
        #: Linear layer for the `f_l` transformation
        self.W_f = nn.Linear(dim, dim)
        #: Linear layer for the `g_l` transformation
        self.W_g = nn.Linear(dim, dim)
        #: Linear layer for the `h_l` transformation
        self.W_h = nn.Linear(dim, dim)

        #: Trainable parameter for mixing the old and new value of `x`
        self.alpha = nn.Parameter(torch.tensor(0.1))  # Trainable parameter
        self.activation_type = kwargs.get("activation_type", "tanh")
        #: Activation function used in the block
        self.activation = activation_function(
            self.activation_type, in_size=dim, **kwargs
        )

    def forward(
        self, x: torch.Tensor, u: torch.Tensor, v: torch.Tensor
    ) -> torch.Tensor:
        """Applies the block transformation to the input `x`.

        Args:
            x: Input of the block
            u: Weighting matrix U
            v: Weighting matrix V

        Returns:
            Output of the block after transformation
        """
        f_l = self.activation(self.W_f(x))
        z_l = f_l * u + (1 - f_l) * v

        g_l = self.activation(self.W_g(z_l))
        e_l = g_l * u + (1 - g_l) * v

        h_l = self.activation(self.W_h(e_l))
        x_next = self.alpha * h_l + (1 - self.alpha) * x

        return x_next


class PirateNet(ScimbaModule):
    """A PirateNet neural network implementation.

    Args:
        in_size: Input dimension, default is 1
        out_size: Output dimension, default is 1
        nb_features: Number of features used for encoding, default is 1
        nb_blocks: Number of stacked `PiranteNet_block` layers, default is 1
        **kwargs: Additional parameters for network configuration
    """

    def __init__(
        self,
        in_size: int = 1,
        out_size: int = 1,
        nb_features: int = 1,
        nb_blocks: int = 1,
        **kwargs,
    ):
        super().__init__(in_size=in_size, out_size=out_size, **kwargs)
        activation_type = kwargs.get("activation_type", "tanh")
        activation_output = kwargs.get("activation_output", "id")
        last_layer_has_bias = kwargs.get("last_layer_has_bias", False)

        #: Input dimension
        self.in_size = in_size
        #: Output dimension
        self.out_size = out_size
        #: Number of residual blocks in the network
        self.nb_blocks = nb_blocks
        #: Dimension of the latent space after encoding
        self.dim_hidden = 2 * nb_features

        #: Input encoding network
        self.embedding = EnhancedFeatureNet(
            in_size=in_size, nb_features=nb_features, **kwargs
        )
        #: Linear layer to compute `U`
        self.embedding_1 = nn.Linear(self.dim_hidden, self.dim_hidden)
        #: Linear layer to compute `V`
        self.embedding_2 = nn.Linear(self.dim_hidden, self.dim_hidden)
        #: Main activation function
        self.activation = activation_function(
            activation_type, in_size=in_size, **kwargs
        )

        #: list of `PiranteNet_block` blocks
        self.blocks = nn.ModuleList(
            [PirateNetBlock(self.dim_hidden, **kwargs) for _ in range(self.nb_blocks)]
        )

        #: Output layer
        self.output_layer = nn.Linear(
            self.dim_hidden, self.out_size, bias=last_layer_has_bias
        )
        #: Final activation function applied to the output
        self.activation_output = activation_function(
            activation_output, in_size=in_size, **kwargs
        )

    def forward(
        self, inputs: torch.Tensor, with_last_layer: bool = True
    ) -> torch.Tensor:
        """Applies the network transformation to the inputs.

        Args:
            inputs: Input of the network
            with_last_layer: If `True`, applies the output layer and final activation,
                default is `True`

        Returns:
            Output of the network after transformation
        """
        inputs = self.embedding(inputs)
        U = self.activation(self.embedding_1(inputs))
        V = self.activation(self.embedding_2(inputs))

        for i in range(self.nb_blocks):
            inputs = self.blocks[i](inputs, U, V)

        if with_last_layer:
            inputs = self.activation_output(self.output_layer(inputs))

        return inputs

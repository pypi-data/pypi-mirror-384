"""Residual Network (ResNet) architectures."""

import torch
from torch import nn
from torch.nn.utils.parametrizations import weight_norm

from scimba_torch.neural_nets.coordinates_based_nets.scimba_module import ScimbaModule

from .activation import activation_function


class GenericResNet(ScimbaModule):
    """A general Residual Network (ResNet) architecture.

    The layer structure is defined by the `layer_structure` parameter,
    and specifies the width, depth, and skip connections.
    `layer_structure` is a list, where:

    - the first element is the width of the hidden layers,
    - the second element is the number of layers,
    - the remaining elements are list of pairs of integers representing the skip
      connections.

    For instance, the default value `[10, 6, [1, 3], [4, 6]]` means:
        - 10 hidden units in each layer,
        - 6 layers,
        - skip connection from layer 1 to layer 3,
        - skip connection from layer 4 to layer 6.

    Args:
        in_size: Dimension of the input
        out_size: Dimension of the output
        **kwargs: Additional keyword arguments:

            - `activation_type` (:code:`str`, default="tanh"): The activation function
              type to use in hidden layers.
            - `activation_output` (:code:`str`, default="id"): The activation function
              type to use in the output layer.
            - `layer_structure` (:code:`list`, default=[10, 6, [1, 3], [4, 6]]): A list
              representing the layer structure of the ResNet.
            - `weights_norm_bool` (:code:`bool`, default=False): If True, applies
              weight normalization to the layers.

    Example:
        >>> model = ResNet(
        ...     4, 1, activation_type='tanh',
        ...     layer_structure=[20, 6, [1, 3], [4, 6]]
        ... )
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__(in_size, out_size, **kwargs)

        activation_type = kwargs.get("activation_type", "tanh")
        activation_type = kwargs.get("activation_type", "tanh")
        activation_output = kwargs.get("activation_output", "id")
        layer_structure = kwargs.get("layer_structure", [10, 6, [1, 3], [4, 6]])
        weights_norm_bool = kwargs.get("weights_norm_bool", False)
        self.last_layer_has_bias = kwargs.get("last_layer_has_bias", False)

        assert len(layer_structure) >= 2, (
            "Layer structure must contain at least width and depth."
        )

        self.in_size = in_size
        self.out_size = out_size

        layer_sizes = [layer_structure[0]] * layer_structure[1]
        self.layer_sizes = [in_size] + layer_sizes + [out_size]

        skip_connections = layer_structure[2:]
        for skip in skip_connections:
            assert len(skip) == 2, "Each skip connection must be a pair of integers."
            assert skip[0] < skip[1], (
                "The first element of a skip connection must be smaller than the "
                "second."
            )

        self.skip_sources = [skip[0] for skip in skip_connections]
        self.skip_targets = [skip[1] for skip in skip_connections]

        #: A list of hidden linear layers.
        self.hidden_layers = []

        for l1, l2 in zip(self.layer_sizes[:-2], self.layer_sizes[+1:-1]):
            if weights_norm_bool:
                self.hidden_layers.append(weight_norm(nn.Linear(l1, l2)))
            else:
                self.hidden_layers.append(nn.Linear(l1, l2))

        self.hidden_layers = nn.ModuleList(self.hidden_layers)

        if weights_norm_bool:
            #: The final output linear layer.
            self.output_layer = weight_norm(
                nn.Linear(
                    self.layer_sizes[-2],
                    self.layer_sizes[-1],
                    bias=self.last_layer_has_bias,
                )
            )
        else:
            self.output_layer = nn.Linear(
                self.layer_sizes[-2],
                self.layer_sizes[-1],
                bias=self.last_layer_has_bias,
            )

        self.activation = []

        for _ in range(len(self.layer_sizes) - 1):
            self.activation.append(
                activation_function(activation_type, in_size=in_size, **kwargs)
            )

        self.activation_output = activation_function(
            activation_output, in_size=in_size, **kwargs
        )

    def forward(
        self, inputs: torch.Tensor, with_last_layer: bool = True
    ) -> torch.Tensor:
        """Apply the network to the inputs.

        Args:
            inputs: Input tensor
            with_last_layer: Whether to apply the final output layer

        Returns:
            The result of the network
        """
        outputs = [0] * (len(self.layer_sizes) - 1)
        outputs[0] = inputs

        for i_layer, (hidden_layer, activation) in enumerate(
            zip(self.hidden_layers, self.activation)
        ):
            outputs[i_layer + 1] = activation(hidden_layer(outputs[i_layer]))
            if i_layer + 1 in self.skip_targets:
                outputs[i_layer + 1] = (
                    outputs[i_layer + 1]
                    + outputs[self.skip_sources[self.skip_targets.index(i_layer + 1)]]
                )

        if with_last_layer:
            outputs[-1] = self.activation_output(self.output_layer(outputs[-1]))

        return outputs[-1]

    def __str__(self) -> str:
        """String representation of the model.

        Returns:
            A string describing the model.
        """
        return f"ResNet with {self.layer_sizes} layers"

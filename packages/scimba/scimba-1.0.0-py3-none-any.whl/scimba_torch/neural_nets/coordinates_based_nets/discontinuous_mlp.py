"""A Multi-Layer Perceptron (MLP) with discontinuous layers.

Each hidden layer can either be discontinuous or regular.
"""

import torch
from torch import nn

from scimba_torch.neural_nets.coordinates_based_nets.scimba_module import ScimbaModule

from .activation import Heaviside, activation_function


class DiscontinuousLayer(nn.Module):
    r"""Class that encodes a fully connected layer which can be discontinuous or not.

    It computes: :math:`y = \sigma(Ax + b) + \epsilon * H(Ax + b)`.

    where :math:`H(x)` is the Heaviside function and :math:`\epsilon` is a learnable
    vector.

    Args:
        in_size: The input dimension size.
        out_size: The output dimension size.
        **kwargs: Keyword arguments including:

            * `activation_type` (:code:`str`): The activation function type.
              Defaults to "tanh".
            * `dis` (:code:`bool`): If True, the layer includes the discontinuous term,
              otherwise it behaves as a regular layer. Defaults to True.

    Example:
        >>> layer = DiscontinuousLayer(10, 5, activation_type='relu', dis=True)
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__()

        self.in_size = in_size
        self.out_size = out_size
        self.dis = kwargs.get("dis", True)

        #: The linear transformation applied to the inputs.
        self.linearlayer = nn.Linear(in_size, out_size)
        #: The parameters which multiply the Heaviside function.
        #: The size is the size of the output of the layer.
        self.eps = nn.Parameter(torch.zeros(out_size))

        # Get the keyword arguments
        self.layer_type = kwargs.get("dis", True)
        self.activation_type = kwargs.get("activation_type", "tanh")

        # Define the layers
        self.linearlayer = nn.Linear(in_size, out_size)
        self.eps = nn.Parameter(torch.rand((out_size)))
        self.activation = activation_function(
            self.activation_type, in_size=in_size, **kwargs
        )

        # Define Heaviside function
        self.heaviside = Heaviside(k=100)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        """Apply the network to the inputs.

        Args:
            inputs: Input tensor

        Returns:
            The result of the network
        """
        if self.layer_type:
            # Compute the discontinuous version
            x = self.activation(self.linearlayer(inputs))
            res = x + self.eps[None, :] * x
        else:
            # Standard linear layer with activation
            res = self.activation(self.linearlayer(inputs))

        return res

    def __str__(self):
        """String representation of the layer.

        Returns:
            A string describing the layer.
        """
        return (
            f"Discontinuous Layer, input size: {self.in_size}, "
            f"output size: {self.out_size}, layer_type: {self.layer_type}"
        )


class DiscontinuousMLP(ScimbaModule):
    """A Multi-Layer Perceptron (MLP) with discontinuous layers.

    Each hidden layer can either be discontinuous or regular.

    Args:
        in_size: Input dimension.
        out_size: Output dimension.
        **kwargs: Keyword arguments including:

            * `activation_type` (:code:`str`): The type of activation function to be
              used for hidden layers. Defaults to "tanh".
            * `activation_output` (:code:`str`): The type of activation function for
              the output layer. Defaults to "id".
            * `layer_sizes` (:code:`list[int]`): List of sizes for each hidden layer.
              Defaults to :code:`[10, 20, 20, 20, 5]`.
            * `layer_type` (:code:`list[bool]`): List of booleans indicating whether
              each hidden layer should be discontinuous. Defaults to :code:`[False,
              False, True, False, False]`.

    Raises:
        ValueError: If layer_sizes and layer_type lists have different lengths.

    Example:
        >>> model = DiscontinuousMLP(
        ...     10, 5, activation_type="relu", activation_output="tanh",
        ...     layer_sizes=[50, 30], layer_type=[False, True, False]
        ... )
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__(in_size, out_size, **kwargs)

        # Default parameter values
        self.activation_type = kwargs.get("activation_type", "tanh")
        self.activation_output_type = kwargs.get("activation_output", "id")
        layer_sizes = kwargs.get("layer_sizes", [10, 20, 20, 20, 5])
        layer_type = kwargs.get("layer_type", [False, False, True, False, False])
        last_layer_has_bias = kwargs.get("last_layer_has_bias", False)

        # Ensure layer_type length matches layer_sizes length
        if len(layer_type) != len(layer_sizes):
            raise ValueError(
                "The length of 'layer_type' must match the length of 'layer_sizes'."
            )

        # Prepare the network architecture
        self.layer_sizes = [in_size] + layer_sizes + [out_size]

        # Adding "C" to layer_type list for the output layer
        self.layer_type = layer_type + ["C"]

        # Hidden layers initialization
        #: The list of discontinuous or regular layers in the model.
        self.hidden_layers = []
        for l1, l2, ltype in zip(
            self.layer_sizes[:-2], self.layer_sizes[1:-1], self.layer_type
        ):
            self.hidden_layers.append(
                DiscontinuousLayer(
                    l1, l2, dis=ltype, activation_type=self.activation_type
                )
            )
        self.hidden_layers = nn.ModuleList(self.hidden_layers)

        # Output layer
        #: The final output layer.
        self.output_layer = nn.Linear(
            self.layer_sizes[-2], self.layer_sizes[-1], bias=last_layer_has_bias
        )

        # Output activation function
        self.activation_output = activation_function(
            self.activation_output_type, in_size=in_size, **kwargs
        )

    def forward(
        self, inputs: torch.Tensor, with_last_layer: bool = True
    ) -> torch.Tensor:
        """Forward pass through the discontinuous MLP network.

        Args:
            inputs: Input tensor.
            with_last_layer: Whether to apply the final output layer. Defaults to True.

        Returns:
            Output tensor after processing through the MLP.
        """
        for hidden_layer in self.hidden_layers:
            inputs = hidden_layer(inputs)
        if with_last_layer:
            inputs = self.activation_output(self.output_layer(inputs))
        return inputs

    def __str__(self) -> str:
        """String representation of the model.

        Returns:
            A string describing the model.
        """
        return f"Discontinuous MLP network with layers: {self.layer_sizes}"

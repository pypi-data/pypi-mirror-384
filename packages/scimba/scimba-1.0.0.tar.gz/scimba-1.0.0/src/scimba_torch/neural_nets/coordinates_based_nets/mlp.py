"""Multi-Layer Perceptron (MLP) architectures."""

from typing import Callable

import torch
from torch import nn
from torch.nn.utils.parametrizations import weight_norm

from scimba_torch.neural_nets.coordinates_based_nets.scimba_module import ScimbaModule

from .activation import activation_function


def factorized_glorot_normal(mean: float = 1.0, stddev: float = 0.1) -> Callable:
    """Initializes parameters.

    Use a factorized version of the Glorot normal initialization.

    Args:
        mean: Mean of the log-normal distribution used to scale the singular values.
        stddev: Standard deviation of the log-normal distribution.

    Returns:
        A function that takes a shape tuple and returns the factorized parameters `s`
        and `v`.

    Example:
        >>> init_fn = factorized_glorot_normal()
        >>> s, v = init_fn((64, 128))
    """

    def init(shape: tuple) -> tuple[torch.Tensor, torch.Tensor]:
        """Inner function to initialize weights.

        Args:
            shape: Shape of the weight matrix (fan_in, fan_out).

        Returns:
            Two tensors:
                - `s`: Scaling factors for each column (log-normal distributed).
                - `v`: Normalized weight matrix after division by `s`.
        """
        fan_in, fan_out = shape
        std = (2.0 / (fan_in + fan_out)) ** 0.5
        w = torch.randn(shape) * std
        s = mean + torch.randn(shape[-1]) * stddev
        s = torch.exp(s)
        v = w / s
        return s, v

    return init


class FactorizedLinear(nn.Module):
    """A linear transformation with factorized parameterization of the weights.

    The weight matrix is expressed as the product of two factors:
    - `s`: A column-wise scaling factor.
    - `v`: A normalized weight matrix.

    Args:
        input_dim: Size of each input sample.
        output_dim: Size of each output sample.
        has_bias: Whether to include a bias term (default: True).
    """

    def __init__(self, input_dim: int, output_dim: int, has_bias: bool = True):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.has_bias = has_bias

        # Initialize kernel parameters (s and v) using factorized_glorot_normal
        init_fn = factorized_glorot_normal()
        s, v = init_fn((input_dim, output_dim))
        self.s = nn.Parameter(s)  #: Column-wise scaling factors
        self.v = nn.Parameter(v)  #: Normalized weight matrix

        # Initialize bias
        if self.has_bias:
            #: Bias vector added to the output
            self.bias = nn.Parameter(torch.zeros(output_dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass of the FactorizedLinear layer.

        Args:
            x: Input tensor of shape (batch_size, input_dim).

        Returns:
            Output tensor of shape (batch_size, output_dim).
        """
        kernel = self.s * self.v
        y = torch.matmul(x, kernel)
        if self.has_bias:
            y = y + self.bias
        return y


class GenericMLP(ScimbaModule):
    """A general Multi-Layer Perceptron (MLP) architecture.

    Args:
        in_size: Dimension of the input
        out_size: Dimension of the output
        **kwargs: Additional keyword arguments:

            - `activation_type` (:code:`str`, default="tanh"): The activation function
              type to use in hidden layers.
            - `activation_output` (:code:`str`, default="id"): The activation function
              type to use in the output layer.
            - `layer_sizes` (:code:`list[int]`, default=[20]*6): A list of integers
              representing the number of neurons in each hidden layer.
            - `weights_norm_bool` (:code:`bool`, default=False): If True, applies weight
              normalization to the layers.
            - `random_fact_weights_bool` (:code:`bool`, default=False): If True, applies
              factorized weights to the layers.

    Example:
        >>> model = GenericMLP(10, 1, activation_type='relu', layer_sizes=[64, 128, 64])
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__(in_size, out_size, **kwargs)

        activation_type = kwargs.get("activation_type", "tanh")
        activation_type = kwargs.get("activation_type", "tanh")
        activation_output = kwargs.get("activation_output", "id")
        layer_sizes = kwargs.get("layer_sizes", [20] * 6)
        weights_norm_bool = kwargs.get("weights_norm_bool", False)
        random_fact_weights_bool = kwargs.get("random_fact_weights_bool", False)
        self.last_layer_has_bias = kwargs.get("last_layer_has_bias", False)

        self.in_size = in_size
        self.out_size = out_size

        self.layer_sizes = [in_size] + layer_sizes + [out_size]
        #: A list of hidden linear layers.
        self.hidden_layers = []

        for l1, l2 in zip(self.layer_sizes[:-2], self.layer_sizes[+1:-1]):
            if weights_norm_bool:
                self.hidden_layers.append(weight_norm(nn.Linear(l1, l2)))
            elif random_fact_weights_bool:
                self.hidden_layers.append(FactorizedLinear(l1, l2))
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
        elif random_fact_weights_bool:
            self.output_layer = FactorizedLinear(
                self.layer_sizes[-2],
                self.layer_sizes[-1],
                has_bias=self.last_layer_has_bias,
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
        for hidden_layer, activation in zip(self.hidden_layers, self.activation):
            inputs = activation(hidden_layer(inputs))
        if with_last_layer:
            inputs = self.activation_output(self.output_layer(inputs))
        return inputs

    def __str__(self) -> str:
        """String representation of the model.

        Returns:
            A string describing the MLP network and its layer sizes.
        """
        return f"MLP network with {self.layer_sizes} layers"

    def expand_hidden_layers(
        self, new_layer_sizes: list[int], set_to_zero: bool = True
    ):
        """Expands the hidden layers of the MLP to new sizes.

        The new sizes must match the number of hidden layers in the MLP.
        The weights of the new layers are initialized to zero, and the weights of the
        old layers are copied into the new layers.
        The output layer is also expanded to match the new sizes.

        Args:
            new_layer_sizes: list of integers representing
                the new sizes of the hidden layers.
            set_to_zero: If True, initializes the weights of the
                new layers to zero. Otherwise, set them to small random
                values.
        """
        assert len(new_layer_sizes) == len(self.hidden_layers), (
            f"Expected {len(self.hidden_layers)} new sizes, got {len(new_layer_sizes)}."
        )

        # Calcule les nouvelles tailles d'entrée/sortie couche par couche
        new_shapes = list(zip([self.in_size] + new_layer_sizes[:-1], new_layer_sizes))

        updated_layers = []

        for i, (new_in, new_out) in enumerate(new_shapes):
            old_layer = self.hidden_layers[i]
            old_in, old_out = old_layer.in_features, old_layer.out_features

            # Nouvelle couche élargie
            new_layer = nn.Linear(new_in, new_out)
            with torch.no_grad():
                # Zéro par défaut
                new_layer.weight.zero_()
                new_layer.bias.zero_()
                # Copie dans le coin supérieur gauche
                new_layer.weight[:old_out, :old_in] = old_layer.weight
                new_layer.bias[:old_out] = old_layer.bias
                if not set_to_zero:
                    new_layer.weight[:, old_in:] = torch.randn(
                        new_layer.weight[:, old_in:].shape
                    )
                    new_layer.bias[:, old_out:] = torch.randn(
                        new_layer.bias[:, old_out:].shape
                    )

            updated_layers.append(new_layer)

        # Nouvelle couche de sortie
        new_output_layer = nn.Linear(
            new_layer_sizes[-1], self.out_size, bias=self.last_layer_has_bias
        )
        with torch.no_grad():
            old_w = self.output_layer.weight.data
            new_output_layer.weight.zero_()
            new_output_layer.weight[:, : old_w.shape[1]] = old_w
            if not set_to_zero:
                new_output_layer.weight[:, old_w.shape[1] :] = torch.randn(
                    new_output_layer.weight[:, old_w.shape[1] :].shape
                )
            if self.last_layer_has_bias:
                old_b = self.output_layer.bias.data
                new_output_layer.bias.copy_(old_b)

        self.hidden_layers = nn.ModuleList(updated_layers)
        self.output_layer = new_output_layer
        self.layer_sizes = [self.in_size] + new_layer_sizes + [self.out_size]


class GenericMMLP(ScimbaModule):
    """A general Multiplicative Multi-Layer Perceptron (MMLP) architecture.

    As proposed by Yanfei Xiang.

    Args:
        in_size: Dimension of the input
        out_size: Dimension of the output
        **kwargs: Additional keyword arguments:

            - `activation_type` (:code:`str`, default="tanh"): The activation function
              type to use in hidden layers.
            - `activation_output` (:code:`str`, default="id"): The activation function
              type to use in the output layer.
            - `layer_sizes` (:code:`list[int]`, default=[10, 20, 20, 20, 5]): A list of
              integers representing the number of neurons in each hidden layer.
            - `weights_norm_bool` (:code:`bool`, default=False): If True, applies weight
              normalization to the layers.
            - `random_fact_weights_bool` (:code:`bool`, default=False): If True, applies
              factorized weights to the layers.

    Example:
        >>> model = GenericMMLP(
        ...     10, 5, activation_type='relu', layer_sizes=[64, 128, 64]
        ... )
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__(in_size, out_size, **kwargs)

        activation_type = kwargs.get("activation_type", "tanh")
        activation_output = kwargs.get("activation_output", "id")
        layer_sizes = kwargs.get("layer_sizes", [10, 20, 20, 20, 5])
        weights_norm_bool = kwargs.get("weights_norm_bool", False)
        random_fact_weights_bool = kwargs.get("random_fact_weights_bool", False)

        self.layer_sizes = [in_size] + layer_sizes + [out_size]

        #: A list of hidden linear layers.
        self.hidden_layers = []

        for l1, l2 in zip(self.layer_sizes[:-2], self.layer_sizes[+1:-1]):
            if weights_norm_bool:
                self.hidden_layers.append(weight_norm(nn.Linear(l1, l2)))
            elif random_fact_weights_bool:
                self.hidden_layers.append(FactorizedLinear(l1, l2))
            else:
                self.hidden_layers.append(nn.Linear(l1, l2))
        self.hidden_layers = nn.ModuleList(self.hidden_layers)

        #: A list of multiplicative linear layers.
        self.hidden_layers_mult = []

        for layer_size in self.layer_sizes[+1:-1]:
            if weights_norm_bool:
                self.hidden_layers_mult.append(
                    weight_norm(nn.Linear(self.in_size, layer_size))
                )
            elif random_fact_weights_bool:
                self.hidden_layers_mult.append(
                    FactorizedLinear(self.in_size, layer_size)
                )
            else:
                self.hidden_layers_mult.append(nn.Linear(self.in_size, layer_size))
        self.hidden_layers_mult = nn.ModuleList(self.hidden_layers_mult)

        if weights_norm_bool:
            #: The final output linear layer.
            self.output_layer = weight_norm(
                nn.Linear(self.layer_sizes[-2], self.layer_sizes[-1])
            )
        elif random_fact_weights_bool:
            self.output_layer = FactorizedLinear(
                self.layer_sizes[-2], self.layer_sizes[-1]
            )
        else:
            self.output_layer = nn.Linear(self.layer_sizes[-2], self.layer_sizes[-1])

        self.activation = []
        self.activation_mult = []

        for _ in range(len(self.layer_sizes) - 1):
            self.activation.append(
                activation_function(activation_type, in_size=in_size, **kwargs)
            )
            self.activation_mult.append(
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
            with_last_layer: Whether to apply the final output layer (default: True)

        Returns:
            The result of the network
        """
        multiplicators = []

        for hidden_layer_mult, activation_mult in zip(
            self.hidden_layers_mult,
            self.activation_mult,
        ):
            multiplicators.append(activation_mult(hidden_layer_mult(inputs)))

        for hidden_layer, activation, multiplicator in zip(
            self.hidden_layers, self.activation, multiplicators
        ):
            inputs = multiplicator * activation(hidden_layer(inputs))
        if with_last_layer:
            inputs = self.activation_output(self.output_layer(inputs))
        return inputs

    def __str__(self) -> str:
        """String representation of the model.

        Returns:
            A string describing the MMLP network and its layer sizes.
        """
        return f"MMLP network, with {self.layer_sizes} layers"

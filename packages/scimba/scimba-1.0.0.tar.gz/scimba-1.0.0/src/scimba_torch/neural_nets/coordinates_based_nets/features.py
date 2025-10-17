"""Neural networks with feature transformations such as Fourier features."""

from typing import Any

import torch
from torch import nn

from scimba_torch.neural_nets.coordinates_based_nets.scimba_module import ScimbaModule

from ..embeddings.periodic_embedding import FlippedEmbedding, PeriodicEmbedding
from .activation import activation_function
from .mlp import GenericMLP
from .res_net import GenericResNet


class EnhancedFeatureNet(nn.Module):
    """A network that generates learnable features such as Fourier features.

    The weights are initialized using a normal distribution.

    Args:
        in_size: The input dimension (number of features in the input tensor).
        **kwargs: Additional keyword arguments:

            - `nb_features` (:code:`int`, default=1): The number of features generated
              by the network.
            - `type_feature` (:code:`str`, default="fourier"): The type of feature
              transformation to apply.
            - `mean` (:code:`float`, default=0.0): The mean used for initializing the
              weights.
            - `std` (:code:`float`, default=1.0): The standard deviation used for
              initializing the weights.
    """

    def __init__(self, in_size: int, **kwargs: Any):
        super().__init__()
        self.in_size = in_size
        self.nb_features = kwargs.get("nb_features", 1)
        self.type_feature = kwargs.get("type_feature", "fourier")
        self.mean = kwargs.get("mean", 0.0)
        self.std = kwargs.get("std", 1.0)
        self.activation = kwargs.get("activation", "sine")

        # Layer initialization
        if self.type_feature == "periodic":
            assert "periods" in kwargs, (
                "Periods must be provided for periodic features."
            )
            self.layer = PeriodicEmbedding(in_size, self.nb_features, kwargs["periods"])
        elif self.type_feature == "flipped":
            assert in_size == 2, "Flipped features are only available for 2D inputs."
            self.layer = FlippedEmbedding(in_size, self.nb_features)
        else:
            self.layer = nn.Linear(in_size, self.nb_features, bias=False)

        if self.type_feature == "fourier":
            # Fourier features initialization
            nn.init.normal_(self.layer.weight, self.mean, self.std)
            self.ac_sine = activation_function("sine", **kwargs)
            self.ac_cosine = activation_function("cosine", **kwargs)
            self.enhanced_dim = 2 * self.nb_features
        elif self.type_feature in ["periodic", "flipped"]:
            # Periodic or flipped features initialization
            self.enhanced_dim = self.nb_features

    def re_init(self, mean: float, std: float):
        """Reinitialize the weights of the linear layer using a normal distribution.

        Args:
            mean: Mean value for normal distribution initialization.
            std: Standard deviation for normal distribution
                initialization.
        """
        nn.init.normal_(self.layer.weight, mean, std)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the feature transformation to the input tensor `x`.

        Args:
            x: Input tensor.

        Returns:
            Transformed feature tensor.
        """
        # Apply the linear transformation
        transformed_features = self.layer(x)

        # Depending on the feature type, apply Fourier transformations
        if self.type_feature == "fourier":
            # Apply sine and cosine transformations for Fourier features
            out_sine = self.ac_sine(transformed_features)
            out_cosine = self.ac_cosine(transformed_features)
            # print(out_sine.shape)
            # print(out_cosine.shape)
            out = torch.cat([out_sine, out_cosine], dim=-1)
        elif self.type_feature in ["periodic", "flipped"]:
            # For periodic features, use the output as is
            out = transformed_features
        else:
            # For other feature types (e.g., wavelets), use a default activation
            out = self.activation(transformed_features)

        return out


class GenericFeatureNet(ScimbaModule):
    """A template for a general network with enhanced features.

    A feature can be a periodic embedding, Fourier features, etc.
    """

    def parameters(
        self, flag_scope: str = "all", flag_format: str = "list"
    ) -> list[nn.Parameter] | torch.Tensor:
        """Get parameters of the neural net.

        Args:
            flag_scope: Specifies which parameters to return.
                Options: 'all', 'last_layer', 'except_last_layer'.
            flag_format: Specifies the format
                Options: 'list', 'tensor'.

        Returns:
            A list of parameters or a single tensor containing all parameters.

        Raises:
            ValueError: If an unknown flag_scope or flag_format is provided.
        """
        if flag_scope == "all":
            param_iter = super().parameters()
        elif flag_scope == "last_layer":
            param_iter = self.net.output_layer.parameters()
        elif flag_scope == "except_last_layer":
            param_iter = (
                param
                for name, param in self.named_parameters()
                if not name.startswith("net.output_layer")
            )

        else:
            raise ValueError(f"Unknown flag_scope: {flag_scope}")

        if flag_format == "list":
            return list(param_iter)
        elif flag_format == "tensor":
            return torch.nn.utils.parameters_to_vector(param_iter)
        else:
            raise ValueError(f"Unknown flag_format: {flag_format}")

    def set_parameters(self, new_params: torch.Tensor, flag_scope: str = "all"):
        """Set parameters.

        Args:
            new_params: new parameters.
            flag_scope: 'all', 'last_layer', 'except_last_layer'

        Raises:
            ValueError: If an unknown flag_scope is provided.
        """
        if flag_scope == "all":
            param_iter = super().parameters()
        elif flag_scope == "last_layer":
            param_iter = self.net.output_layer.parameters()
        elif flag_scope == "except_last_layer":
            param_iter = (
                param
                for name, param in self.named_parameters()
                if not name.startswith("net.output_layer")
            )
        else:
            raise ValueError(f"Unknown flag_scope: {flag_scope}")

        torch.nn.utils.vector_to_parameters(new_params, param_iter)

    def re_init_features(self, mean: float, std: float):
        """Reinitialize the weights of the `EnhancedFeatureNet` layer.

        Use a normal distribution with the specified mean and standard deviation.

        Args:
            mean: Mean value for the normal distribution.
            std: Standard deviation for the normal distribution.
        """
        self.features.re_init(mean, std)


class GenericFourierNet(GenericFeatureNet):
    """Combines Fourier feature transformations with a specified neural network.

    The network first generates enhanced features (such as Fourier features),
    concatenates them with the original input, and then passes the result through a
    user-specified network architecture.

    Args:
        in_size: The input dimension (number of features in the input tensor).
        out_size: The output dimension (number of features in the output tensor).
        **kwargs: Additional keyword arguments:

            - `nb_features` (:code:`int`, default=1): Number of features generated by
              EnhancedFeatureNet.
            - `type_feature` (:code:`str`, default="fourier"): Type of feature
              transformation
            - Other keyword arguments are passed to the `EnhancedFeatureNet` and to
              whichever network class is specified by the user.

    Learnable Parameters:

    - features (:code:`EnhancedFeatureNet`): A network that generates enhanced features
      such as Fourier features.
    - net: (:code:`ScimbaModule`): A neural network that processes the input and
      features.
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__(in_size, out_size, **kwargs)
        self.nb_features = kwargs.get("nb_features", 1)
        self.type_feature = kwargs.get("type_feature", "fourier")

        self.features = EnhancedFeatureNet(in_size=in_size, **kwargs)
        self.inputs_size = self.in_size + self.features.enhanced_dim

    def forward(self, x: torch.Tensor, with_last_layer: bool = True) -> torch.Tensor:
        """Compute the forward pass.

        Apply the feature transformation, concatenate the features with the original
        input, and pass the result through the neural network to produce the output.

        Args:
            x: Input tensor.
            with_last_layer: Whether to include the last layer in the forward pass.
                (default: True)

        Returns:
            Output tensor after passing through the neural network.
        """
        features = self.features.forward(x)
        inputs = torch.cat([x, features], dim=-1)
        return self.net.forward(inputs, with_last_layer)


class FourierMLP(GenericFourierNet):
    """Combines Fourier feature transformations with a Multi-Layer Perceptron (MLP).

    The network first generates enhanced features (such as Fourier features),
    concatenates them with the original input, and then passes the result through a
    fully connected MLP.

    Args:
        in_size: The input dimension (number of features in the input tensor).
        out_size: The output dimension (number of features in the output tensor).
        **kwargs: Additional keyword arguments:

            - `nb_features` (:code:`int`, default=1): Number of features generated by
              EnhancedFeatureNet.
            - `type_feature` (:code:`str`, default="fourier"): Type of feature
              transformation applied.
            - Other keyword arguments are passed to EnhancedFeatureNet and GenericMLP
              classes.
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__(in_size, out_size, **kwargs)
        self.net = GenericMLP(
            in_size=self.inputs_size, out_size=self.out_size, **kwargs
        )


class FourierResNet(GenericFourierNet):
    """Combines Fourier feature transformations with a ResNet architecture.

    The network first generates enhanced features (such as Fourier features),
    concatenates them with the original input, and then passes the result through a
    series of residual blocks. It is a specialization of `GenericFourierNet`.

    Args:
        in_size: The input dimension (number of features in the input tensor).
        out_size: The output dimension (number of features in the output tensor).
        **kwargs: Additional keyword arguments.
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__(in_size, out_size, **kwargs)
        self.net = GenericResNet(
            in_size=self.inputs_size, out_size=self.out_size, **kwargs
        )


class GenericPeriodicNet(GenericFeatureNet):
    """A neural network that appends a periodic embedding before the first layer.

    The network first generates periodic features, passes the input through it, and then
      passes the result through the chosen architecture.

    Args:
        in_size: The input dimension (number of features in the input tensor).
        out_size: The output dimension (number of features in the output tensor).
        **kwargs: Additional keyword arguments:

            - `domain_bounds` (:code:`required`): The bounds of the domain for the
              periodic features.
            - `nb_features` (:code:`optional`): The number of features generated by the
              `EnhancedFeatureNet`.
            - `type_feature` (:code:`optional`): The type of feature transformation
              applied (e.g., "periodic").
            - Other arguments passed to the `EnhancedFeatureNet` class and whichever
              network class is specified by the user.

    Raises:
        KeyError: If `domain_bounds` is not provided in `kwargs`.
        ValueError: If `domain_bounds` is not a `torch.Tensor` or has incorrect shape.

    Learnable Parameters:

    - features (:code:`EnhancedFeatureNet`): A network that generates enhanced features
      such as Fourier features.
    - net: (:code:`ScimbaModule`): A neural network that processes the input and
      features.
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__(in_size, out_size, **kwargs)
        layer_sizes = kwargs.get("layer_sizes", [20] * 6)

        if "domain_bounds" not in kwargs:
            raise KeyError("Domain bounds must be provided for periodic features.")

        assert "domain_bounds" in kwargs, (
            "Domain bounds must be provided for periodic features."
        )

        domain_bounds = kwargs["domain_bounds"]
        if not isinstance(domain_bounds, torch.Tensor):
            raise ValueError("domain_bounds argument must be a torch.Tensor")
        assert isinstance(domain_bounds, torch.Tensor)
        if not ((domain_bounds.shape[0] == 1) or (domain_bounds.shape[0] == in_size)):
            raise ValueError(
                "domain_bounds argument must be a (1,2) or (%d,2)-shaped torch.Tensor"
                % in_size
            )

        kwargs["nb_features"] = layer_sizes[0]
        kwargs["type_feature"] = "periodic"
        kwargs["periods"] = self.compute_periods(domain_bounds)

        self.features = EnhancedFeatureNet(in_size=in_size, **kwargs)
        self.inputs_size = self.features.enhanced_dim

        kwargs["layer_sizes"] = layer_sizes[1:]

    def compute_periods(self, domain_bounds: torch.Tensor) -> torch.Tensor:
        """Compute the periods for the periodic embedding from the domain bounds.

        Args:
            domain_bounds: The bounds of the domain for periodic features.

        Returns:
            torch.Tensor: The computed periods.
        """
        lower, upper = domain_bounds.T
        return upper - lower

    def forward(self, x: torch.Tensor, with_last_layer: bool = True) -> torch.Tensor:
        """Compute the forward pass.

        Apply the periodic transformation and pass the result through the MLP to produce
        the output.

        Args:
            x: Input tensor.
            with_last_layer: Whether to include the last layer in the forward pass.
                (default: True)

        Returns:
            Output tensor after passing through the neural network.
        """
        return self.net.forward(self.features.forward(x), with_last_layer)


class PeriodicMLP(GenericPeriodicNet):
    """A neural network that combines periodic feature transformations with an MLP.

    The network first generates periodic features, passes the input through it,
    and then passes the result through a fully connected MLP.

    Args:
        in_size: The input dimension (number of features in the input tensor).
        out_size: The output dimension (number of features in the output tensor).
        **kwargs: Other keyword arguments including:

            - `domain_bounds` (:code:`required`): The bounds of the domain for the
              periodic features.
            - `nb_features` (:code:`optional`): Number of features generated by
              EnhancedFeatureNet.
            - `type_feature` (:code:`optional`): Type of feature transformation applied
              (e.g., "periodic").
            - Other arguments passed to EnhancedFeatureNet and GenericMLP classes.
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__(in_size, out_size, **kwargs)
        self.net = GenericMLP(
            in_size=self.inputs_size, out_size=self.out_size, **kwargs
        )


class PeriodicResNet(GenericPeriodicNet):
    """Combine a periodic feature transformations with a ResNet architecture.

    The network first generates periodic features, passes the input through it,
    and then passes the result through a ResNet.

    Args:
        in_size: The input dimension (number of features in the input tensor).
        out_size: The output dimension (number of features in the output tensor).
        **kwargs: Other keyword arguments including:

            - `domain_bounds` (:code:`required`): The bounds of the domain for the
              periodic features.
            - `nb_features` (:code:`optional`): The number of features generated by the
              `EnhancedFeatureNet`.
            - `type_feature` (:code:`optional`): The type of feature transformation
              applied (e.g., "periodic").
            - Other arguments passed to the `EnhancedFeatureNet` and `GenericResNet`
              classes
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__(in_size, out_size, **kwargs)
        self.net = GenericResNet(
            in_size=self.inputs_size, out_size=self.out_size, **kwargs
        )


class FlippedMLP(GenericFeatureNet):
    """Combine flipping feature transformations with a Multi-Layer Perceptron (MLP).

    The network first generates flipped features, passes the input through it, and then
    passes the result through a fully connected MLP.

    This class is only available for 2D inputs on the unit square.

    Args:
        in_size: The input dimension (number of features in the input tensor).
        out_size: The output dimension (number of features in the output tensor).
        **kwargs: Other keyword arguments including:

            - `nb_features` (:code:`optional`): Number of features generated by
              EnhancedFeatureNet.
            - `type_feature` (:code:`optional`): Type of feature transformation applied
              (e.g., "flipped").
            - Other arguments passed to EnhancedFeatureNet and GenericMLP classes.
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        assert in_size == 2, "Flipped features are only available for 2D inputs."

        super().__init__(in_size, out_size, **kwargs)
        layer_sizes = kwargs.get("layer_sizes", [20] * 6)

        kwargs["nb_features"] = layer_sizes[0]
        kwargs["type_feature"] = "flipped"

        self.features = EnhancedFeatureNet(in_size=in_size, **kwargs)
        self.inputs_size = self.features.enhanced_dim

        kwargs["layer_sizes"] = layer_sizes[1:]

        self.net = GenericMLP(
            in_size=self.inputs_size, out_size=self.out_size, **kwargs
        )

    def forward(self, x: torch.Tensor, with_last_layer: bool = True) -> torch.Tensor:
        """Compute the forward pass.

        Apply the periodic transformation and pass the result through the MLP to produce
        the output.

        Args:
            x: Input tensor.
            with_last_layer: Whether to include the last layer in the forward pass
                (default: True)

        Returns:
            Output tensor after passing through the MLP.
        """
        return self.net.forward(self.features.forward(x), with_last_layer)


class GenericMultiScaleFourierNet(ScimbaModule):
    """Combines Fourier feature transformations with a specified neural network.

    The network first generates enhanced features (such as Fourier features),
    concatenates them with the original input, and then passes the result through a
    user-specified network architecture. The result is obtained as a linear combination
    of the Fourier networks.

    Args:
        in_size: int
        out_size: int
        **kwargs: Additional keyword arguments:

            - `means` (:code:`list[float]`, default=[0.0]): Initialize the weights of
              the EnhancedFeatureNet layers
            - `stds` (:code:`list[float]`, default=[1.0]): Initialize the weights of
              the EnhancedFeatureNet layers
            - `nb_features` (:code:`int`, default=1): The number of features generated
              by the EnhancedFeatureNet
            - `type_feature` (:code:`str`, default="fourier"): The type of feature
              transformation applied
            - Other keyword arguments are passed to the EnhancedFeatureNet and to
              whichever network class is specified by the user.

    Learnable Parameters:

    - features (:code:`EnhancedFeatureNet`): A network that generates enhanced features
      such as Fourier features.
    - net: (:code:`ScimbaModule`): A neural network that processes the input and
      features.
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__(in_size, out_size, **kwargs)
        self.nb_features = kwargs.get("nb_features", 1)
        self.type_feature = kwargs.get("type_feature", "fourier")

        self.means = kwargs.get("means", [0.0])
        self.stds = kwargs.get("stds", [1.0])

        self.features = [
            EnhancedFeatureNet(in_size=in_size, mean=mean, std=std, **kwargs)
            for mean, std in zip(self.means, self.stds)
        ]
        self.features = nn.ModuleList(self.features)

        self.inputs_size = self.in_size + self.features[0].enhanced_dim

        self.output_layer = nn.Linear(len(self.stds) * self.out_size, self.out_size)

    def re_init_features(self, means: list[float], stds: list[float]):
        """Reinitialize the weights of the `EnhancedFeatureNet` layer.

        Use a normal distribution with the specified mean and standard deviation.

        Args:
            means: List of mean values for the normal distribution.
            stds: List of standard deviations for the normal distribution.
        """
        for i, feat in enumerate(self.features):
            feat.re_init(means[i], stds[i])

    def forward(self, x: torch.Tensor, with_last_layer: bool = True) -> torch.Tensor:
        """Compute the forward pass.

        Apply the feature transformation, concatenate the features with the original
        input and pass the result through the neural network to produce the output.

        Args:
            x: Input tensor.
            with_last_layer: Whether to include the last layer in the forward pass.
                (default: True)

        Returns:
            Output tensor after passing through the neural network.
        """
        H = [
            net.forward(torch.cat([x, feat.forward(x)], dim=-1), with_last_layer=True)
            for feat, net in zip(self.features, self.nets)
        ]
        H = torch.cat(H, dim=-1)
        if with_last_layer:
            H = self.output_layer.forward(H)
        return H


class MultiScaleFourierMLP(GenericMultiScaleFourierNet):
    """A linear combination of Fourier feature transformations with MLP.

    The networks first generate enhanced features (such as Fourier features),
    concatenate them with the original input, and then passes the result through a
    fully connected MLP.

    The result is obtained as a linear combination of the Fourier networks.

    Args:
        in_size: The input dimension (number of features in the input tensor).
        out_size: The output dimension (number of features in the output tensor).
        **kwargs: Additional keyword arguments:

            - `means` (:code:`list[float]`, default=[0.0]): Initialize the weights of
              the EnhancedFeatureNet layers
            - `stds` (:code:`list[float]`, default=[1.0]): Initialize the weights of the
              EnhancedFeatureNet layers
            - `nb_features` (:code:`int`, default=1): The number of features generated
              by the EnhancedFeatureNet
            - `type_feature` (:code:`str`, default="fourier"): The type of feature
              transformation applied
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__(in_size, out_size, **kwargs)
        self.nets = [
            GenericMLP(in_size=self.inputs_size, out_size=self.out_size, **kwargs)
            for _ in self.stds
        ]
        self.nets = nn.ModuleList(self.nets)


class MultiScaleFourierResNet(GenericMultiScaleFourierNet):
    """Combine Fourier feature transformations with Residual Networks (ResNet).

    The networks first generate enhanced features (such as Fourier features),
    concatenate them with the original input, and then passes the result through a fully
    connected ResNet. The result is obtained as a linear combination of the Fourier
    networks. It is a specialization of the generic class `GenericMultiScaleFourierNet`.

    Args:
        in_size: The input dimension (number of features in the input tensor).
        out_size: The output dimension (number of features in the output tensor).
        **kwargs: Additional keyword arguments.
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__(in_size, out_size, **kwargs)
        self.nets = [
            GenericResNet(in_size=self.inputs_size, out_size=self.out_size, **kwargs)
            for _ in self.stds
        ]
        self.nets = nn.ModuleList(self.nets)

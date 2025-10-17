"""Defines the radial approximation space and its components."""

from typing import Callable

import torch
import torch.nn as nn
from torch.func import functional_call, jacrev, vmap

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.domain.meshless_domain.base import VolumetricDomain
from scimba_torch.integration.monte_carlo import DomainSampler, TensorizedSampler
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor


class NNxSpace(AbstractApproxSpace, nn.Module):
    """A nonlinear approximation space using a neural network model.

    This class represents a parametric approximation space, where the solution
    is modeled by a neural network. It integrates functionality for evaluating the
    network, setting/retrieving degrees of freedom, and computing the Jacobian.

    Args:
        nb_unknowns: Number of unknowns in the approximation problem.
        nb_parameters: Number of parameters in the input.
        net_type: The neural network class used to approximate the solution.
        spatial_domain: The spatial domain of the problem.
        integrator: Sampler used for integration over the spatial and parameter domains.
        **kwargs: Additional arguments passed to the neural network model.
    """

    def __init__(
        self,
        nb_unknowns: int,
        nb_parameters: int,
        net_type: torch.nn.Module,
        spatial_domain: VolumetricDomain,
        integrator: DomainSampler,
        **kwargs,
    ):
        super().__init__(nb_unknowns)
        #: Size of the input to the neural network (spatial dimension + parameters).
        self.in_size: int = spatial_domain.dim + nb_parameters
        #: Size of the output of the neural network (number of unknowns).
        self.out_size: int = nb_unknowns
        #: The spatial domain of the problem.
        self.spatial_domain: VolumetricDomain = spatial_domain
        #: Integrator combining the spatial and parameter domains.
        self.integrator: DomainSampler = integrator
        self.type_space: str = "space"

        def default_pre_processing(x: LabelTensor, mu: LabelTensor):
            return torch.cat([x.x, mu.x], dim=1)

        def default_post_processing(
            inputs: torch.Tensor, x: LabelTensor, mu: LabelTensor
        ):
            return inputs

        self.pre_processing = kwargs.get("pre_processing", default_pre_processing)
        self.post_processing = kwargs.get("post_processing", default_post_processing)
        #: Neural network used for the approximation.
        self.network: nn.Module = net_type(
            in_size=self.in_size,
            out_size=self.out_size,
            **kwargs,
        )
        #: Total number of degrees of freedom in the network.
        self.ndof: int = self.get_dof(flag_format="tensor").shape[0]

    def forward(
        self, features: torch.Tensor, with_last_layer: bool = True
    ) -> torch.Tensor:
        """Evaluate the parametric model for given input features.

        Args:
            features: Input tensor with concatenated spatial and parameter data.
            with_last_layer: Whether to include the last layer (Default value = True).

        Returns:
            Output tensor from the neural network.
        """
        return self.network(features, with_last_layer)

    def evaluate(
        self, x: LabelTensor, mu: LabelTensor, with_last_layer: bool = True
    ) -> MultiLabelTensor:
        """Evaluate the parametric model for given inputs and parameters.

        Return the result as a multi-label tensor.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.
            with_last_layer: Whether to include the last layer in computation.

        Returns:
            MultiLabelTensor with the evaluation results.
        """

    def set_dof(self, theta: torch.Tensor, flag_scope: str = "all") -> None:
        """Sets the degrees of freedom (DoF) for the neural network.

        Args:
            theta: A vector containing the network parameters.
            flag_scope: Scope of parameters to set (Default value = "all").
        """
        self.network.set_parameters(theta, flag_scope)

    def get_dof(
        self, flag_scope: str = "all", flag_format: str = "list"
    ) -> torch.Tensor:
        """Retrieves the degrees of freedom (DoF) of the neural network.

        Args:
            flag_scope: Scope of parameters to retrieve.
            flag_format: Format of the returned parameters.

        Returns:
            The network parameters as specified by the format.
        """
        res = self.network.parameters(flag_scope, flag_format)
        return res

    def jacobian(self, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        """Compute the Jacobian of the network with respect to its parameters.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.

        Returns:
            The Jacobian matrix after post-processing.
        """
        params = {k: v.detach() for k, v in self.named_parameters()}
        features = self.pre_processing(x, mu)

        def fnet(theta, features):
            return functional_call(self, theta, (features.unsqueeze(0))).squeeze(0)

        jac = vmap(jacrev(fnet), (None, 0))(params, features).values()
        jac_m = torch.cat(
            [j.reshape((features.shape[0], self.out_size, -1)) for j in jac], dim=-1
        )
        jac_mt = jac_m.transpose(1, 2)
        return self.post_processing(jac_mt, x, mu)


class NNxSpaceSplit(AbstractApproxSpace, nn.Module):
    """A nonlinear approximation space using a network split into separate components.

    Separate into spatial and parameter domains.

    This class is designed to handle problems where the input space can be split into
    spatial and parameter components, allowing for more efficient processing via
    separate neural networks for each component.

    Args:
        nb_unknowns: The number of unknowns in the approximation problem.
        nb_parameters: The number of parameters in the problem.
        net_type: The neural network model used to approximate the solution.
        spatial_domain: The domain representing the spatial component of the problem.
        integrator: The sampler used for integration over the spatial domain.
        **kwargs: Additional keyword arguments for configuring the neural network model.
    """

    def __init__(
        self,
        nb_unknowns: int,
        nb_parameters: int,
        net_type: torch.nn.Module,
        spatial_domain: VolumetricDomain,
        integrator: TensorizedSampler,
        **kwargs,
    ):
        super().__init__(nb_unknowns)
        #: The size of the inputs to the neural network.
        self.in_size: int = spatial_domain.dim + nb_parameters
        #: The size of the outputs from the neural network.
        self.out_size: int = nb_unknowns
        #: The spatial domain of the problem.
        self.spatial_domain: VolumetricDomain = spatial_domain
        #: The integrator for the spatial and parameter domains.
        self.integrator: TensorizedSampler = integrator
        self.type_space = "space"

        def default_pre_processing_x(x: LabelTensor):
            return x.x

        def default_pre_processing_mu(mu: LabelTensor):
            return mu.x

        def default_post_processing(
            inputs: torch.Tensor, x: LabelTensor, mu: LabelTensor
        ):
            return inputs

        self.pre_processing_out_size_x = kwargs.get(
            "pre_processing_out_size_x", spatial_domain.dim
        )
        #: Pre-processing function for spatial inputs.
        self.pre_processing_x: Callable = kwargs.get(
            "pre_processing_x", default_pre_processing_x
        )
        self.pre_processing_out_size_mu = kwargs.get(
            "pre_processing_out_size_mu", nb_parameters
        )
        #: Pre-processing function for parameter inputs.
        self.pre_processing_mu: Callable = kwargs.get(
            "pre_processing_mu", default_pre_processing_mu
        )
        self.post_processing_in_size: int = kwargs.get(
            "post_processing_in_size", self.out_size
        )
        #: Post-processing function for neural network outputs.
        self.post_processing: Callable = kwargs.get(
            "post_processing", default_post_processing
        )
        #: The dimensionality of the latent space for split networks.
        self.split_latent_space: int = kwargs.get("split_parameters_space", 1)
        #: Neural network for processing spatial inputs.
        self.network_x: torch.nn.Module = net_type(
            in_size=self.pre_processing_out_size_x,
            out_size=self.split_latent_space,
            **kwargs,
        )
        #: Neural network for processing parameter inputs.
        self.network_mu: torch.nn.Module = net_type(
            in_size=self.pre_processing_out_size_mu,
            out_size=self.split_latent_space,
            **kwargs,
        )
        #: Neural network for combining latent spaces from spatial and parameter inputs.
        self.network_cat: torch.nn.Module = net_type(
            in_size=2 * self.split_latent_space,
            out_size=self.post_processing_in_size,
            **kwargs,
        )
        self.network = nn.ModuleList(
            [self.network_x, self.network_mu, self.network_cat]
        )
        #: Number of degrees of freedom (DoF) for the entire network.
        self.ndof: int = self.get_dof(flag_format="tensor").shape[0]
        self.ndof_x: int = self.network_x.parameters(flag_format="tensor").shape[0]
        self.ndof_mu: int = self.network_mu.parameters(flag_format="tensor").shape[0]
        self.ndof_cat: int = self.network_cat.parameters(flag_format="tensor").shape[0]

    def forward(self, x: torch.Tensor, mu: torch.Tensor, with_last_layer: bool = True):
        """Evaluate the parametric model for given inputs and parameters.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.
            with_last_layer: Whether to include the last layer in computation
                (default: True).

        Returns:
            Output tensor from the neural network.
        """
        h_x = self.network_x(x)
        h_mu = self.network_mu(mu)
        res = self.network_cat(torch.cat([h_x, h_mu], dim=1), with_last_layer)
        return res

    def evaluate(
        self, x: LabelTensor, mu: LabelTensor, with_last_layer: bool = True
    ) -> MultiLabelTensor:
        """Evaluate the parametric model for given inputs and parameters.

        Return the result as a multi-label tensor.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.
            with_last_layer: Whether to include the last layer in computation
                (default: True).

        Returns:
            The result of the neural network evaluation.
        """
        self.x = x
        self.mu = mu
        x_pre = self.pre_processing_x(x)
        mu_pre = self.pre_processing_mu(mu)
        res = self.forward(x_pre, mu_pre, with_last_layer)
        if with_last_layer:
            res = self.post_processing(res, x, mu)
        return MultiLabelTensor(res, [x.labels, mu.labels])

    def set_dof(self, theta: torch.Tensor, flag_scope: str = "all") -> None:
        """Sets the degrees of freedom (DoF) for the neural network.

        Args:
            theta: A vector containing the network parameters.
            flag_scope: Scope of parameters to set (Default value = "all").
        """
        if flag_scope == "all" or flag_scope == "except_last_layer":
            self.network_x.set_parameters(
                theta[: self.ndof_x],
                flag_scope="all",
            )
            self.network_mu.set_parameters(
                theta[self.ndof_x : self.ndof_x + self.ndof_mu],
                flag_scope="all",
            )
            self.network_cat.set_parameters(
                theta[self.ndof_x + self.ndof_mu :], flag_scope=flag_scope
            )
        else:
            self.network_cat.set_parameters(theta, flag_scope)

    def get_dof(
        self, flag_scope: str = "all", flag_format: str = "list"
    ) -> torch.Tensor:
        """Retrieves the degrees of freedom (DoF) of the neural network.

        Args:
            flag_scope:  (Default value = "all")
            flag_format:  (Default value = "list")

        Returns:
            The network parameters in the specified format.
        """
        params_cat = self.network_cat.parameters(
            flag_scope=flag_scope, flag_format=flag_format
        )
        params_x = self.network_x.parameters(flag_scope="all", flag_format=flag_format)
        params_mu = self.network_mu.parameters(
            flag_scope="all", flag_format=flag_format
        )
        if flag_format == "list":
            params = params_x + params_mu + params_cat
        if flag_format == "tensor":
            params = torch.cat((params_x, params_mu, params_cat))

        return params

    def jacobian(self, x: LabelTensor, mu: LabelTensor):
        """Compute the Jacobian matrix of the model with respect to its inputs.

        Args:
            x: The input tensor for the spatial domain.
            mu: The input tensor for the parameter domain.

        Returns:
            The Jacobian matrix of the model.
        """
        params = {k: v.detach() for k, v in self.named_parameters()}
        x_pre = self.pre_processing_x(x)
        mu_pre = self.pre_processing_mu(mu)

        def fnet(theta, x, mu):
            return functional_call(
                self, theta, (x.unsqueeze(0), mu.unsqueeze(0))
            ).squeeze(0)

        jac = vmap(jacrev(fnet), (None, 0, 0))(params, x_pre, mu_pre).values()
        jac_m = torch.cat(
            [j.reshape((x.shape[0], self.nb_unknowns, -1)) for j in jac], axis=-1
        )
        jac_mt = jac_m.transpose(1, 2)
        jac_mt = self.post_processing(jac_mt, x, mu)
        return jac_mt


class SeparatedNNxSpace(AbstractApproxSpace, nn.Module):
    """A nonlinear approximation space using a neural network model.

    This class represents a parametric approximation space, where the solution
    is modeled by a neural network. It integrates functionality for evaluating the
    network, setting/retrieving degrees of freedom, and computing the Jacobian.

    Args:
        nb_unknowns: Number of unknowns in the approximation problem.
        nb_parameters: Number of parameters in the input.
        rank: The rank for the separated representation.
        net_type: The neural network class used to approximate the solution.
        spatial_domain: The spatial domain of the problem.
        integrator: Sampler used for integration over the spatial and parameter domains.
        **kwargs: Additional arguments passed to the neural network model.
    """

    def __init__(
        self,
        nb_unknowns: int,
        nb_parameters: int,
        rank: int,
        net_type: torch.nn.Module,
        spatial_domain: VolumetricDomain,
        integrator: DomainSampler,
        **kwargs,
    ):
        super().__init__(nb_unknowns)
        #: Size of the input to the neural network (spatial dimension + parameters).
        self.in_size: int = spatial_domain.dim + nb_parameters
        #: Size of the output of the neural network (number of unknowns).
        self.out_size: int = nb_unknowns
        #: The spatial domain of the problem.
        self.spatial_domain: VolumetricDomain = spatial_domain
        #: The integrator combining the spatial and parameter domains.
        self.integrator: DomainSampler = integrator
        self.rank: int = rank
        self.type_space: str = "space"

        def default_pre_processing(x: LabelTensor, mu: LabelTensor):
            return torch.cat([x.x, mu.x], dim=1)

        def default_post_processing(
            inputs: torch.Tensor, x: LabelTensor, mu: LabelTensor
        ):
            return inputs

        self.pre_processing = kwargs.get("pre_processing", default_pre_processing)
        self.post_processing = kwargs.get("post_processing", default_post_processing)
        #: The neural network used for the approximation.
        self.network: nn.ModuleList = nn.ModuleList(
            [
                net_type(
                    in_size=1,
                    out_size=self.out_size * self.rank,
                    **kwargs,
                )
                for i in range(0, self.in_size)
            ]
        )
        #: The total number of degrees of freedom in the network.
        self.ndof: int = self.get_dof(flag_scope="all", flag_format="tensor").shape[0]

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """Evaluate the parametric model for given input features.

        Args:
            features: Input tensor with concatenated spatial and parameter data.

        Returns:
            Output tensor from the neural network.
        """
        batch_size = features.shape[0]
        res_local = torch.zeros(batch_size, self.out_size, self.in_size, self.rank)
        res_local = []
        for i in range(0, self.in_size):
            output = (
                self.network[i]
                .forward(features[:, i][:, None])
                .view(batch_size, self.out_size, self.rank)
            )
            res_local.append(output)
        res_local = torch.stack(res_local, dim=2)

        # Product on the axe dimension
        res = res_local.prod(dim=2)  # Résultat : (batch, n, r)
        # Som on the axis rank
        res = res.sum(dim=2)  # Résultat : (batch, n)
        return res

    def evaluate(
        self, x: LabelTensor, mu: LabelTensor, with_last_layer: bool = True
    ) -> MultiLabelTensor:
        """Evaluate the parametric model for given inputs and parameters.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.
            with_last_layer:  (Default value = True)

        Returns:
            Output tensor from the neural network, wrapped with multi-label metadata.

        Raises:
            ValueError: If with_last_layer is False.
        """
        if not with_last_layer:
            raise ValueError("We cannot use only the last layer ")
        features = self.pre_processing(x, mu)
        res = self.forward(features)
        res = self.post_processing(res, x, mu)
        return MultiLabelTensor(res, [x.labels, mu.labels])

    def set_dof(self, theta: torch.Tensor, flag_scope: str = "all") -> None:
        """Sets the degrees of freedom (DoF) for the neural network.

        Args:
            theta: A vector containing the network parameters.
            flag_scope:  (Default value = "all")

        Raises:
            ValueError: If the flag_scope is not "all".
        """
        if not (flag_scope == "all"):
            raise ValueError("We can use this model only with the all the layers")
        torch.nn.utils.vector_to_parameters(theta, self.parameters())

    def get_dof(
        self, flag_scope: str = "all", flag_format: str = "list"
    ) -> torch.Tensor | list[nn.parameter.Parameter]:
        """Retrieves the degrees of freedom (DoF) of the neural network.

        Args:
            flag_scope:  (Default value = "all")
            flag_format:  (Default value = "list")

        Returns:
            The network parameters in the specified format.

        Raises:
            ValueError: If the flag_scope is not "all" or if the flag_format is unknown
                or if the flag_format is not "list" or "tensor".
        """
        if not (flag_scope == "all"):
            raise ValueError("We can use this model only with the all the layers")
        if flag_format == "list":
            res = list(self.parameters())
        elif flag_format == "tensor":
            res = torch.nn.utils.parameters_to_vector(self.parameters())
        else:
            raise ValueError(f"Unknown flag_format: {flag_format}")
        return res

    def jacobian(self, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        """Compute the Jacobian of the network with respect to its parameters.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.

        Returns:
            Jacobian matrix of shape `(num_samples, out_size, num_params)`.
        """
        params = {k: v.detach() for k, v in self.named_parameters()}
        features = self.pre_processing(x, mu)

        def fnet(theta, features):
            return functional_call(self, theta, (features.unsqueeze(0))).squeeze(0)

        jac = vmap(jacrev(fnet), (None, 0))(params, features).values()
        jac_m = torch.cat(
            [j.reshape((features.shape[0], self.out_size, -1)) for j in jac], dim=-1
        )
        jac_mt = jac_m.transpose(1, 2)
        return self.post_processing(jac_mt, x, mu)

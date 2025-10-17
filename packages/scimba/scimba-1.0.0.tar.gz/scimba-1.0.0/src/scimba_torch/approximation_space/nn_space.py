"""Defines the neural network approximation space and its components."""

from typing import Callable, cast

import torch
import torch.nn as nn
from torch.func import functional_call, jacrev, vmap

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.domain.meshless_domain.base import SurfacicDomain, VolumetricDomain
from scimba_torch.integration.monte_carlo import TensorizedSampler
from scimba_torch.neural_nets.coordinates_based_nets.discontinuous_mlp import (
    DiscontinuousMLP,
)
from scimba_torch.neural_nets.coordinates_based_nets.features import (
    FlippedMLP,
    PeriodicMLP,
    PeriodicResNet,
)
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor


class NNxSpace(AbstractApproxSpace, nn.Module):
    """A nonlinear approximation space using a neural network model.

    This class represents a parametric approximation space, where the solution
    is modeled by a neural network. It integrates functionality for evaluating the
    network, setting/retrieving degrees of freedom, and computing the Jacobian.

    Args:
        nb_unknowns: Number of unknowns in the approximation problem.
        nb_parameters: Number of parameters in the input.
        space_type: The neural network class used to approximate the solution.
        spatial_domain: The spatial domain of the problem.
        integrator: Sampler used for integration over the spatial and parameter domains.
        **kwargs: Additional arguments passed to the neural network model.

    Raises:
        KeyError: If parameters_bounds is not provided when using PeriodicMLP.
    """

    def __init__(
        self,
        nb_unknowns: int,
        nb_parameters: int,
        space_type: torch.nn.Module,
        spatial_domain: VolumetricDomain,
        integrator: TensorizedSampler,
        **kwargs,
    ):
        # super().__init__(nb_unknowns)
        nn.Module.__init__(self)
        AbstractApproxSpace.__init__(self, nb_unknowns)
        #: Size of the input to the neural network (spatial dimension + parameters).
        self.in_size: int = spatial_domain.dim + nb_parameters
        #: Size of the output of the neural network (number of unknowns).
        self.out_size: int = nb_unknowns
        #: The spatial domain of the problem.
        self.spatial_domain: VolumetricDomain = spatial_domain
        #: Integrator combining the spatial and parameter domains.
        self.integrator: TensorizedSampler = integrator
        #: Type of the approximation space.
        self.type_space: str = "space"

        def default_pre_processing(x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
            return torch.cat([x.x, mu.x], dim=1)

        def default_post_processing(
            inputs: torch.Tensor, x: LabelTensor, mu: LabelTensor
        ) -> torch.Tensor:
            return inputs

        #: Function to pre-process inputs.
        self.pre_processing: Callable = kwargs.get(
            "pre_processing", default_pre_processing
        )
        #: Function to post-process outputs.
        self.post_processing: Callable = kwargs.get(
            "post_processing", default_post_processing
        )

        # add domain bounds in case of periodicity
        if (space_type is PeriodicMLP) and ("parameters_bounds" not in kwargs):
            if nb_parameters >= 1:
                raise KeyError(
                    "parameters_bounds must be provided for periodic features "
                    "as it can not be deduced"
                )

        parameters_bounds = kwargs.get("parameters_bounds", torch.tensor([]))
        if not isinstance(parameters_bounds, torch.Tensor):
            parameters_bounds = torch.tensor(
                parameters_bounds, dtype=torch.get_default_dtype()
            )

        kwargs["domain_bounds"] = torch.cat(
            (spatial_domain.bounds, parameters_bounds), dim=0
        )

        # create the space
        self.pre_processing_out_size = kwargs.get(
            "pre_processing_out_size", spatial_domain.dim + nb_parameters
        )
        self.post_processing_in_size = kwargs.get(
            "post_processing_in_size", self.out_size
        )
        #: Neural network used for the approximation.
        self.network: torch.nn.Module = space_type(
            in_size=self.pre_processing_out_size,
            out_size=self.post_processing_in_size,
            **kwargs,
        )
        #: Total number of degrees of freedom in the network.
        self.ndof: int = self.get_dof(flag_format="tensor").shape[0]

    def forward(
        self, features: torch.Tensor, with_last_layer: bool = True
    ) -> torch.Tensor:
        """Evaluates the parametric model for given input features.

        Args:
            features: Input tensor with concatenated spatial and parameter data.
            with_last_layer: Whether to include the last layer in evaluation.
                (Default value = True)

        Returns:
            torch.Tensor: Output tensor from the neural network.
        """
        return self.network(features, with_last_layer)

    def evaluate(
        self, x: LabelTensor, mu: LabelTensor, with_last_layer: bool = True
    ) -> MultiLabelTensor:
        """Evaluates the parametric model for given inputs and parameters.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.
            with_last_layer: Whether to include the last layer in evaluation.
                (Default value = True)

        Returns:
            MultiLabelTensor: Output tensor from the neural network,
                wrapped with multi-label metadata.
        """
        features = self.pre_processing(x, mu)
        res = self.forward(features, with_last_layer)
        if with_last_layer:
            res = self.post_processing(res, x, mu)
        return MultiLabelTensor(res, [x.labels, mu.labels])

    def set_dof(self, theta: torch.Tensor, flag_scope: str = "all") -> None:
        """Sets the degrees of freedom (DoF) for the neural network.

        Args:
            theta: A vector containing the network parameters.
            flag_scope: Scope flag for setting degrees of freedom.
                (Default value = "all")
        """
        self.network.set_parameters(theta, flag_scope)

    def get_dof(
        self, flag_scope: str = "all", flag_format: str = "list"
    ) -> torch.Tensor:
        """Retrieves the degrees of freedom (DoF) of the neural network.

        Args:
            flag_scope: Specifies the parameters to return. (Default value = "all")
            flag_format: The format for returning the parameters.
                (Default value = "list")

        Returns:
            The network parameters in the specified format.
        """
        return self.network.parameters(flag_scope, flag_format)

    def jacobian(self, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        """Computes the Jacobian of the network with respect to its parameters.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.

        Returns:
            Jacobian matrix of shape `(num_samples, out_size, num_params)`.
        """
        # get the trainable parameters of the neural network
        params = {k: v.detach() for k, v in self.named_parameters()}
        # get the features, i.e., the pre-processed input (x, mu)
        features = self.pre_processing(x, mu)

        # turn the network into a function of its parameters and features
        def fnet(theta, features):
            return functional_call(self, theta, (features.unsqueeze(0))).squeeze(0)

        # (None, 0) means that:
        #   - the first argument (params) is not batched
        #   - the second argument (features) is batched along the first dimension
        jac = vmap(jacrev(fnet), (None, 0))(params, features).values()

        # jac is a dict of jagged tensors, we want to:
        #   - first reshape each jagged tensor
        #   - then concatenate them along the last dimension
        jac_m = torch.cat(
            [
                j.reshape((features.shape[0], self.post_processing_in_size, -1))
                for j in jac
            ],
            dim=-1,
        )

        # transpose the Jacobian matrix, and apply post-processing
        jac_mt = jac_m.transpose(1, 2)
        return self.post_processing(jac_mt, x[..., None], mu[..., None])


class NNxSpaceSplit(AbstractApproxSpace, nn.Module):
    """A nonlinear approximation space using a neural network split into components.

    It is designed to handle problems where the input space can be split into
    spatial and parameter components, allowing for more efficient processing via
    separate neural networks for each component.

    Args:
        nb_unknowns: The number of unknowns in the approximation problem.
        nb_parameters: The number of parameters in the problem.
        net_type: The neural network model used to approximate the solution.
        spatial_domain: The domain representing the spatial component of the problem.
        integrator: The sampler used for integration over the spatial domain.
        **kwargs: Additional keyword arguments for configuring the neural network model.

    Raises:
        ValueError: If the network type is not supported.
        KeyError: If parameters_bounds is not provided when using PeriodicMLP.
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
        # super().__init__(nb_unknowns)
        nn.Module.__init__(self)
        AbstractApproxSpace.__init__(self, nb_unknowns)
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

        if nb_parameters == 0:
            raise ValueError("NNxSpaceSplit approximation spaces with no parameters")
        # add domain bounds in case of periodicity
        self.domain_x_bounds = spatial_domain.bounds

        if (net_type is PeriodicMLP) and ("parameters_bounds" not in kwargs):
            if nb_parameters >= 1:
                raise KeyError(
                    "parameters_bounds must be provided for periodic features "
                    "as it can not be deduced"
                )

        parameters_bounds = kwargs.get("parameters_bounds", torch.tensor([]))
        if not isinstance(parameters_bounds, torch.Tensor):
            parameters_bounds = torch.tensor(
                parameters_bounds, dtype=torch.get_default_dtype()
            )

        self.domain_mu_bounds = parameters_bounds

        kwargs.pop("domain_bounds", None)

        self.pre_processing_out_size_x = kwargs.get(
            "pre_processing_out_size_x", spatial_domain.dim
        )
        self.pre_processing_x = kwargs.get("pre_processing_x", default_pre_processing_x)
        self.pre_processing_out_size_mu = kwargs.get(
            "pre_processing_out_size_mu", nb_parameters
        )
        self.pre_processing_mu = kwargs.get(
            "pre_processing_mu", default_pre_processing_mu
        )
        self.post_processing_in_size = kwargs.get(
            "post_processing_in_size", self.out_size
        )
        self.post_processing = kwargs.get("post_processing", default_post_processing)
        self.split_latent_space = kwargs.get("split_parameters_space", 1)

        kwargs["domain_bounds"] = self.domain_x_bounds
        #: The neural network for processing spatial inputs.
        self.network_x: torch.nn.Module = net_type(
            in_size=self.pre_processing_out_size_x,
            out_size=self.split_latent_space,
            **kwargs,
        )
        kwargs["domain_bounds"] = self.domain_mu_bounds
        #: The neural network for processing parameter inputs.
        self.network_mu: torch.nn.Module = net_type(
            in_size=self.pre_processing_out_size_mu,
            out_size=self.split_latent_space,
            **kwargs,
        )
        #: The neural network for processing concatenated inputs.
        self.network_cat: torch.nn.Module = net_type(
            in_size=2 * self.split_latent_space,
            out_size=self.post_processing_in_size,
            **kwargs,
        )
        self.network = nn.ModuleList(
            [self.network_x, self.network_mu, self.network_cat]
        )
        #: The number of degrees of freedom (DoF) in the neural network.
        self.ndof: int = self.get_dof(flag_format="tensor").shape[0]
        self.ndof_x: int = self.network_x.parameters(flag_format="tensor").shape[0]
        self.ndof_mu: int = self.network_mu.parameters(flag_format="tensor").shape[0]
        self.ndof_cat: int = self.network_cat.parameters(flag_format="tensor").shape[0]

    def forward(self, x: torch.Tensor, mu: torch.Tensor, with_last_layer: bool = True):
        """Evaluates the parametric model for given inputs and parameters.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.
            with_last_layer: Whether to include the last layer in evaluation.
                (Default value = True)

        Returns:
            Output tensor from the neural network.
        """
        h_x = self.network_x(x)
        h_x = h_x.reshape(h_x.shape[0], -1)  # add an axis in case of a PeriodicMLP
        h_mu = self.network_mu(mu)
        h_mu = h_mu.reshape(h_mu.shape[0], -1)  # add an axis in case of a PeriodicMLP
        res = self.network_cat(torch.cat([h_x, h_mu], dim=1), with_last_layer)
        return res

    def evaluate(self, x: LabelTensor, mu: LabelTensor, with_last_layer: bool = True):
        """Evaluates the parametric model for given inputs and parameters.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.
            with_last_layer: Whether to include the last layer in evaluation.
                (Default value = True)

        Returns:
            MultiLabelTensor: The result of the neural network evaluation.
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
            flag_scope: Scope flag for setting degrees of freedom.
                (Default value = "all")
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
            flag_scope: Specifies the parameters to return. (Default value = "all")
            flag_format: The format for returning the parameters.
                (Default value = "list")

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

    def jacobian(self, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        """Computes the Jacobian matrix of the model with respect to its inputs.

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
            [j.reshape((x.shape[0], self.post_processing_in_size, -1)) for j in jac],
            dim=-1,
        )
        jac_mt = jac_m.transpose(1, 2)
        return self.post_processing(jac_mt, x[..., None], mu[..., None])


class SeparatedNNxSpace(AbstractApproxSpace, nn.Module):
    """A nonlinear approximation space using a neural network model with components.

    This class represents a parametric approximation space, where the solution
    is modeled by a neural network with separated components for efficient computation.

    Args:
        nb_unknowns: Number of unknowns in the approximation problem.
        nb_parameters: Number of parameters in the input.
        rank: Rank of the separated tensor structure.
        net_type: The neural network class used to approximate the solution.
        spatial_domain: The spatial domain of the problem.
        integrator: Sampler used for integration over the spatial and parameter domains.
        **kwargs: Additional arguments passed to the neural network model.

    Raises:
        ValueError: If the network type is not supported.
    """

    def __init__(
        self,
        nb_unknowns: int,
        nb_parameters: int,
        rank: int,
        net_type: torch.nn.Module,
        spatial_domain: VolumetricDomain,
        integrator: TensorizedSampler,
        **kwargs,
    ):
        nn.Module.__init__(self)
        AbstractApproxSpace.__init__(self, nb_unknowns)
        #: Size of the input to the neural network (spatial dimension + parameters).
        self.in_size: int = spatial_domain.dim + nb_parameters
        #: Size of the output of the neural network (number of unknowns).
        self.out_size: int = nb_unknowns
        #: The spatial domain of the problem.
        self.spatial_domain: VolumetricDomain = spatial_domain
        #: Integrator for sampling over the spatial and parameter domains.
        self.integrator: TensorizedSampler = integrator
        self.rank: int = rank
        self.type_space: str = "space"

        if net_type in [PeriodicMLP, FlippedMLP, DiscontinuousMLP, PeriodicResNet]:
            raise ValueError(
                "PeriodicMLP, FlippedMLP, DiscontinuousMLP, "
                "PeriodicResNet are not supported"
            )

        def default_pre_processing(x: LabelTensor, mu: LabelTensor):
            return torch.cat([x.x, mu.x], dim=1)

        def default_post_processing(
            inputs: torch.Tensor, x: LabelTensor, mu: LabelTensor
        ):
            return inputs

        self.pre_processing = kwargs.get("pre_processing", default_pre_processing)
        self.post_processing = kwargs.get("post_processing", default_post_processing)
        self.pre_processing_out_size = kwargs.get(
            "pre_processing_out_size", spatial_domain.dim + nb_parameters
        )
        self.post_processing_in_size = kwargs.get(
            "post_processing_in_size", self.out_size
        )

        default_tensor_structure = [[1] * self.pre_processing_out_size] * self.rank
        self.tensor_structure = kwargs.get("tensor_structure", default_tensor_structure)

        #: list of neural network modules used for the approximation.
        self.network: nn.ModuleList = nn.ModuleList(
            [
                net_type(
                    in_size=tensor_structure_rank_dim,
                    out_size=self.post_processing_in_size,
                    **kwargs,
                )
                for tensor_structure_rank in self.tensor_structure
                for tensor_structure_rank_dim in tensor_structure_rank
            ]
        )

        # modify the tensor_structure_rank_dim list: [1, 1, 2] -> [0, 1, 2, 4]

        expanded_structure = []
        for i, tensor_structure_rank in enumerate(self.tensor_structure):
            expanded_structure.append([0])
            for t_ in tensor_structure_rank:
                expanded_structure[-1].append(expanded_structure[-1][-1] + t_)
        self.expanded_structure = expanded_structure

        #: Total number of degrees of freedom in the network.
        self.ndof: int = cast(
            torch.Tensor, self.get_dof(flag_scope="all", flag_format="tensor")
        ).shape[0]

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """Evaluates the parametric model for given input features.

        Args:
            features: Input tensor with concatenated spatial and parameter data.

        Returns:
            Output tensor from the neural network.
        """
        res = 0
        k = 0
        for local_structure in self.expanded_structure:
            res_local = 1
            for start, end in zip(local_structure[:-1], local_structure[+1:]):
                # multiply along input axes
                res_local *= self.network[k](features[:, start:end])
                k += 1
            # sum along rank
            res += res_local

        assert isinstance(res, torch.Tensor)
        return res

    def evaluate(
        self, x: LabelTensor, mu: LabelTensor, with_last_layer: bool = True
    ) -> MultiLabelTensor:
        """Evaluates the parametric model for given inputs and parameters.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.
            with_last_layer: Whether to include the last layer in evaluation.
                (Default value = True)

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
            flag_scope: Scope flag for setting degrees of freedom.
                (Default value = "all")

        Raises:
            ValueError: If the flag_scope is not "all".
        """
        if not (flag_scope == "all"):
            raise ValueError("We can use this model only with the all the layers")
        torch.nn.utils.vector_to_parameters(theta, self.parameters())

    def get_dof(
        self, flag_scope: str = "all", flag_format: str = "list"
    ) -> list | torch.Tensor:
        """Retrieves the degrees of freedom (DoF) of the neural network.

        Args:
            flag_scope: Specifies the parameters to return. (Default value = "all")
            flag_format: The format for returning the parameters.
                (Default value = "list")

        Returns:
            The network parameters in the specified format.

        Raises:
            ValueError: If the flag_scope is not "all" or
                If the flag_format is not "list" or "tensor".
        """
        if not (flag_scope == "all"):
            raise ValueError("We can use this model only with the all the layers")
        if flag_format == "list":
            res: list | torch.Tensor = list(self.parameters())
        elif flag_format == "tensor":
            res = torch.nn.utils.parameters_to_vector(self.parameters())
        else:
            raise ValueError(f"Unknown flag_format: {flag_format}")
        return res

    def jacobian(self, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        """Computes the Jacobian of the network with respect to its parameters.

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
            [
                j.reshape((features.shape[0], self.post_processing_in_size, -1))
                for j in jac
            ],
            dim=-1,
        )
        jac_mt = jac_m.transpose(1, 2)
        return self.post_processing(jac_mt, x[..., None], mu[..., None])


class NNxtSpace(AbstractApproxSpace, nn.Module):
    """A nonlinear approximation space using a neural network model for space-time data.

    It represents a parametric approximation space, where the solution
    is modeled by a neural network, integrating functionality for evaluating the
    network, setting/retrieving degrees of freedom, and computing the Jacobian.

    Args:
        nb_unknowns: Number of unknowns in the approximation problem.
        nb_parameters: Number of parameters in the input.
        net_type: The neural network class used to approximate the solution.
        spatial_domain: The spatial domain of the problem.
        integrator: Sampler used for integration over the spatial and parameter domains.
        **kwargs: Additional arguments passed to the neural network model.

    Raises:
        ValueError: If the network type is not supported.
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
        nn.Module.__init__(self)
        AbstractApproxSpace.__init__(self, nb_unknowns)
        #: Size of the input to the neural network
        #: (spatial dimension + parameters + time).
        self.in_size: int = spatial_domain.dim + nb_parameters + 1
        #: Size of the output of the neural network (number of unknowns).
        self.out_size: int = nb_unknowns
        #: The spatial domain of the problem.
        self.spatial_domain: VolumetricDomain = spatial_domain
        #: Integrator combining the spatial and parameter domains.
        self.integrator: TensorizedSampler = integrator
        self.type_space: str = "time_space"

        if net_type in [PeriodicMLP, FlippedMLP]:
            raise ValueError("PeriodicMLP, FlippedMLPare not supported in NNxtSpaces")

        def default_pre_processing(t: LabelTensor, x: LabelTensor, mu: LabelTensor):
            return torch.cat([t.x, x.x, mu.x], dim=1)

        def default_post_processing(
            inputs: torch.Tensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
        ):
            return inputs

        self.pre_processing = kwargs.get("pre_processing", default_pre_processing)
        self.post_processing = kwargs.get("post_processing", default_post_processing)
        #: Neural network used for the approximation.
        self.network: torch.nn.Module = net_type(
            in_size=self.in_size,
            out_size=self.out_size,
            **kwargs,
        )
        #: Total number of degrees of freedom in the network.
        self.ndof: int = self.get_dof(flag_format="tensor").shape[0]

    def forward(
        self, features: torch.Tensor, with_last_layer: bool = True
    ) -> torch.Tensor:
        """Evaluates the parametric model for given input features.

        Args:
            features: Input tensor with concatenated spatial and parameter data.
            with_last_layer: Whether to include the last layer in evaluation.
                (Default value = True)

        Returns:
            Output tensor from the neural network.
        """
        return self.network(features, with_last_layer)

    def evaluate(
        self,
        t: LabelTensor,
        x: LabelTensor,
        mu: LabelTensor,
        with_last_layer: bool = True,
    ) -> MultiLabelTensor:
        """Evaluates the parametric model for given inputs and parameters.

        Args:
            t: Input tensor from the time domain.
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.
            with_last_layer: Whether to include the last layer in evaluation.
                (Default value = True)

        Returns:
            Output tensor from the neural network, wrapped with multi-label metadata.
        """
        features = self.pre_processing(t, x, mu)
        res = self.forward(features, with_last_layer)
        if with_last_layer:
            res = self.post_processing(res, t, x, mu)
        return MultiLabelTensor(res, [x.labels, t.labels, mu.labels])

    def set_dof(self, theta: torch.Tensor, flag_scope: str = "all") -> None:
        """Sets the degrees of freedom (DoF) for the neural network.

        Args:
            theta: A vector containing the network parameters.
            flag_scope: Scope flag for setting degrees of freedom.
                (Default value = "all")
        """
        self.network.set_parameters(theta, flag_scope)

    def get_dof(
        self, flag_scope: str = "all", flag_format: str = "list"
    ) -> torch.Tensor:
        """Retrieves the degrees of freedom (DoF) of the neural network.

        Args:
            flag_scope: Specifies the parameters to return. (Default value = "all")
            flag_format: The format for returning the parameters.
                (Default value = "list")

        Returns:
            torch.Tensor: The network parameters in the specified format.

        """
        return self.network.parameters(flag_scope, flag_format)

    def jacobian(self, t: LabelTensor, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        """Computes the Jacobian of the network with respect to its parameters.

        Args:
            t: Input tensor from the time domain.
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.

        Returns:
            Jacobian matrix of shape `(num_samples, out_size, num_params)`.
        """
        params = {k: v.detach() for k, v in self.named_parameters()}
        features = self.pre_processing(t, x, mu)

        def fnet(theta, features):
            return functional_call(self, theta, (features.unsqueeze(0))).squeeze(0)

        jac = vmap(jacrev(fnet), (None, 0))(params, features).values()
        jac_m = torch.cat(
            [j.reshape((features.shape[0], self.out_size, -1)) for j in jac], dim=-1
        )
        jac_mt = jac_m.transpose(1, 2)
        return self.post_processing(jac_mt, t[..., None], x[..., None], mu[..., None])


class NNxvSpace(AbstractApproxSpace, nn.Module):
    """A nonlinear approximation space using a network model for phase space data.

    This class represents a parametric approximation space, where the solution
    is modeled by a neural network, integrating functionality for evaluating the
    network, setting/retrieving degrees of freedom, and computing the Jacobian.

    Args:
        nb_unknowns: Number of unknowns in the approximation problem.
        nb_parameters: Number of parameters in the input.
        net_type: The neural network class used to approximate the solution.
        spatial_domain: The spatial domain of the problem.
        velocity_domain: The velocity domain of the problem.
        integrator: Sampler used for integration over the spatial and parameter domains.
        **kwargs: Additional arguments passed to the neural network model.

    Raises:
        KeyError: If parameters_bounds is not provided when using PeriodicMLP or
            PeriodicResNet.
        ValueError: If the network type is not supported.
    """

    def __init__(
        self,
        nb_unknowns: int,
        nb_parameters: int,
        net_type: torch.nn.Module,
        spatial_domain: VolumetricDomain,
        velocity_domain: SurfacicDomain,
        integrator: TensorizedSampler,
        **kwargs,
    ):
        # super().__init__(nb_unknowns)
        nn.Module.__init__(self)
        AbstractApproxSpace.__init__(self, nb_unknowns)
        self.dim_x = spatial_domain.dim
        self.dim_v = velocity_domain.dim
        #: Size of the input to the neural network
        #: (spatial dimension + velocity dimension + parameters).
        self.in_size: int = self.dim_x + self.dim_v + nb_parameters
        #: Size of the output of the neural network (number of unknowns).
        self.out_size: int = nb_unknowns
        #: The spatial domain of the problem.
        self.spatial_domain: VolumetricDomain = spatial_domain
        #: The velocity domain of the problem.
        self.velocity_domain: SurfacicDomain = velocity_domain
        #: Sampler used for integration over the spatial and parameter domains.
        self.integrator: TensorizedSampler = integrator
        self.type_space = "phase_space"

        if net_type in [FlippedMLP]:
            raise ValueError("FlippedMLP is not supported in NNxvSpaces")

        # create post-processing

        def default_pre_processing(x: LabelTensor, v: LabelTensor, mu: LabelTensor):
            return torch.cat([x.x, v.x, mu.x], dim=1)

        def default_post_processing(
            inputs: torch.Tensor, x: LabelTensor, v: LabelTensor, mu: LabelTensor
        ):
            return inputs

        self.pre_processing = kwargs.get("pre_processing", default_pre_processing)
        self.post_processing = kwargs.get("post_processing", default_post_processing)

        # add domain bounds in case of periodicity

        if net_type in [PeriodicMLP, PeriodicResNet]:
            if "parameters_bounds" not in kwargs and nb_parameters >= 1:
                raise KeyError(
                    "parameters_bounds must be provided for periodic features "
                    "as it can not be deduced"
                )

            parameters_bounds = kwargs.get("parameters_bounds", torch.tensor([]))
            if not isinstance(parameters_bounds, torch.Tensor):
                parameters_bounds = torch.tensor(
                    parameters_bounds, dtype=torch.get_default_dtype()
                )

            kwargs["domain_bounds"] = torch.cat(
                (spatial_domain.bounds, velocity_domain.bounds, parameters_bounds),
                dim=0,
            )

        # create the network

        self.network = net_type(
            in_size=self.in_size,
            out_size=self.out_size,
            **kwargs,
        )
        #: Total number of degrees of freedom in the network.
        self.ndof: int = self.get_dof(flag_format="tensor").shape[0]

    def forward(
        self, features: torch.Tensor, with_last_layer: bool = True
    ) -> torch.Tensor:
        """Evaluates the parametric model for given input features.

        Args:
            features: Input tensor with concatenated spatial and parameter data.
            with_last_layer: Whether to include the last layer in evaluation.
                (Default value = True)

        Returns:
            Output tensor from the neural network.
        """
        return self.network(features, with_last_layer)

    def evaluate(
        self,
        x: LabelTensor,
        v: LabelTensor,
        mu: LabelTensor,
        with_last_layer: bool = True,
    ) -> MultiLabelTensor:
        """Evaluates the parametric model for given inputs and parameters.

        Args:
            x: Input tensor from the spatial domain.
            v: Input tensor from the velocities domain.
            mu: Input tensor from the parameter domain.
            with_last_layer: Whether to include the last layer in evaluation.
                (Default value = True)

        Returns:
            Output tensor from the neural network, wrapped with multi-label metadata.
        """
        features = self.pre_processing(x, v, mu)
        res = self.forward(features, with_last_layer)
        if with_last_layer:
            res = self.post_processing(res, x, v, mu)
        return MultiLabelTensor(res, [x.labels, v.labels, mu.labels])

    def set_dof(self, theta: torch.Tensor, flag_scope: str = "all") -> None:
        """Sets the degrees of freedom (DoF) for the neural network.

        Args:
            theta: A vector containing the network parameters.
            flag_scope: Scope flag for setting degrees of freedom.
                (Default value = "all")
        """
        self.network.set_parameters(theta, flag_scope)

    def get_dof(
        self, flag_scope: str = "all", flag_format: str = "list"
    ) -> torch.Tensor:
        """Retrieves the degrees of freedom (DoF) of the neural network.

        Args:
            flag_scope: Specifies the parameters to return. (Default value = "all")
            flag_format: The format for returning the parameters.
                (Default value = "list")

        Returns:
            The network parameters in the specified format.
        """
        return self.network.parameters(flag_scope, flag_format)

    def jacobian(self, x: LabelTensor, v: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        """Computes the Jacobian of the network with respect to its parameters.

        Args:
            x: Input tensor from the spatial domain.
            v: Input tensor from the velocities domain.
            mu: Input tensor from the parameter domain.

        Returns:
            Jacobian matrix of shape `(num_samples, out_size, num_params)`.
        """
        params = {k: lo.detach() for k, lo in self.named_parameters()}
        features = self.pre_processing(x, v, mu)

        def fnet(theta, features):
            return functional_call(self, theta, (features.unsqueeze(0))).squeeze(0)

        jac = vmap(jacrev(fnet), (None, 0))(params, features).values()
        jac_m = torch.cat(
            [j.reshape((features.shape[0], self.out_size, -1)) for j in jac], dim=-1
        )
        jac_mt = jac_m.transpose(1, 2)
        return self.post_processing(jac_mt, x[..., None], v[..., None], mu[..., None])

    def expand_hidden_layers(
        self, layer_sizes: list[int], set_to_zero: bool = True
    ) -> None:
        """Expands the hidden layers of the neural network to accommodate new sizes.

        Args:
            layer_sizes: list of sizes for the hidden layers.
            set_to_zero: If True, initializes the new layers to zero. Otherwise,
                uses small random numbers. Default is True.
        """
        self.network.expand_hidden_layers(layer_sizes)
        self.ndof = self.get_dof(flag_format="tensor").shape[0]

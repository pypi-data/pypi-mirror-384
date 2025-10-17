"""Defines the spectral approximation space and its components."""

import os

import torch

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import itertools

import torch.nn as nn
from torch.func import functional_call, jacrev, vmap

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.integration.monte_carlo import DomainSampler, TensorizedSampler
from scimba_torch.neural_nets.coordinates_based_nets.scimba_module import ScimbaModule
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor


class SpectralxSpace(AbstractApproxSpace, ScimbaModule):
    """A nonlinear approximation space using a neural network model.

    This class represents a parametric approximation space, where the solution
    is modeled by a neural network. It integrates functionality for evaluating the
    network, setting/retrieving degrees of freedom, and computing the Jacobian.

    Args:
        nb_unknowns: Number of unknowns in the approximation problem.
        basis_type: Type of basis functions used in the approximation
            (e.g., "sine", "cosine").
        nb_mods_by_direction: Number of modes in each spatial direction.
        bounds: list of tuples specifying the bounds for each spatial dimension.
        integrator: Integrator for the spatial and parameter domains.
        **kwargs: Additional arguments passed to the neural network model.
    """

    def __init__(
        self,
        nb_unknowns: int,
        basis_type: str,
        nb_mods_by_direction: int,
        bounds: list,
        integrator: DomainSampler,
        **kwargs,
    ):
        # Call the initializer of ScimbaModule
        ScimbaModule.__init__(
            self,
            in_size=len(bounds),
            out_size=nb_unknowns,
            **kwargs,
        )

        # Call the initializer of AbstractApproxSpace
        AbstractApproxSpace.__init__(self, nb_unknowns)
        self.bounds = bounds
        #: The integrator combining the spatial and parameter domains.
        self.integrator: DomainSampler = integrator
        self.L = torch.tensor([bounds[i][1] - bounds[i][0] for i in range(len(bounds))])
        self.basis_type = basis_type
        self.nb_mods_by_direction = nb_mods_by_direction
        self.type_space = "space"

        def default_pre_processing(x: LabelTensor, mu: LabelTensor):
            return torch.cat([x.x, mu.x], dim=1)

        def default_post_processing(
            inputs: torch.Tensor, x: LabelTensor, mu: LabelTensor
        ):
            return inputs

        self.pre_processing = kwargs.get("pre_processing", default_pre_processing)
        self.post_processing = kwargs.get("post_processing", default_post_processing)
        last_layer_has_bias = kwargs.get("last_layer_has_bias", False)
        # Vectorized initialization
        j = torch.arange(
            1, self.nb_mods_by_direction + 1, dtype=torch.get_default_dtype()
        ).view(1, -1)  # (1, nb_mod)
        L_inv = 1 / self.L.view(-1, 1)  # (d, 1)
        freq_init = 2 * torch.pi * j * L_inv  # Broadcast to (d, nb_mod)
        self.nb_mod_total = self.nb_mods_by_direction**self.in_size

        self.freq = nn.Parameter(freq_init)
        # Generate all possible combinations of frequency indices
        self.combinations = list(
            itertools.product(range(self.nb_mods_by_direction), repeat=self.in_size)
        )
        self.nb_combinations = len(self.combinations)  # nb_frequencies ** spatial_dim

        self.output_layer = torch.nn.Linear(
            self.nb_mod_total, self.out_size, bias=last_layer_has_bias
        )
        self.ndof = self.get_dof(flag_format="tensor").shape[0]

    def forward(
        self, features: torch.Tensor, with_last_layer: bool = True
    ) -> torch.Tensor:
        """Evaluate the parametric model for given input features.

        Args:
            features: Input tensor with concatenated spatial and parameter data.
            with_last_layer: whether to include the last layer in the evaluation
                (Default value = True)

        Returns:
            Output tensor from the neural network.
        """
        # Create the tensor containing the correct frequencies for each combination
        self.freq_combined = torch.stack(
            [self.freq[range(self.in_size), indices] for indices in self.combinations],
            dim=-1,
        )

        # Extend `features` to have the same structure
        proj = self.freq_combined.unsqueeze(0) * features.unsqueeze(
            -1
        )  # (batch_size, dim_physical, nb_combinations)

        if self.basis_type == "sine":
            tri_proj = torch.sin(proj)  # (batch_size, dim_physical, nb_combinations)
        else:
            tri_proj = torch.cos(proj)

        # Product over the physical dimensions
        fourier_basis = tri_proj.prod(dim=1)  # (batch_size, nb_combinations)

        if with_last_layer:
            res = self.output_layer(fourier_basis)
        else:
            res = fourier_basis
        return res

    def evaluate(
        self, x: LabelTensor, mu: LabelTensor, with_last_layer: bool = True
    ) -> MultiLabelTensor:
        """Evaluate the parametric model for given inputs and parameters.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.
            with_last_layer: whether to include the last layer in the evaluation
                (Default value = True)

        Returns:
            Output tensor from the neural network, wrapped with multi-label metadata.
        """
        features = self.pre_processing(x, mu)
        res = self.forward(features, with_last_layer=with_last_layer)
        if with_last_layer:
            res = self.post_processing(res, x, mu)
        return MultiLabelTensor(res, [x.labels, mu.labels])

    def set_dof(self, theta: torch.Tensor, flag_scope: str = "all") -> None:
        """Sets the degrees of freedom (DoF) for the neural network.

        Args:
            theta: A vector containing the network parameters.
            flag_scope: scope of the DoF (Default value = "all")
        """
        self.set_parameters(theta, flag_scope)

    def get_dof(
        self, flag_scope: str = "all", flag_format: str = "list"
    ) -> list[nn.parameter.Parameter] | torch.Tensor:
        """Retrieves the degrees of freedom (DoF) of the neural network.

        Args:
            flag_scope: scope of the DoF (Default value = "all")
            flag_format: format of the DoF (Default value = "list")

        Returns:
            Tensor containing the DoF of the network.
        """
        return self.parameters(flag_scope=flag_scope, flag_format=flag_format)

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


class SeparatedSpectralxSpace(AbstractApproxSpace, nn.Module):
    """A nonlinear approximation space using a neural network model.

    This class represents a parametric approximation space, where the solution
    is modeled by a neural network. It integrates functionality for evaluating the
    network, setting/retrieving degrees of freedom, and computing the Jacobian.


    Args:
        nb_unknowns: Number of unknowns in the approximation problem.
        basis_type: Type of basis functions used in the approximation
            (e.g., "sine", "cosine").
        nb_mods_by_direction: Number of modes in each spatial direction.
        bounds: list of tuples specifying the bounds for each spatial dimension.
        integrator: Integrator for the spatial and parameter domains.
        rank: Rank of the tensor structure.
        **kwargs: Additional arguments passed to the neural network model.
    """

    def __init__(
        self,
        nb_unknowns: int,
        basis_type: str,
        nb_mods_by_direction: int,
        bounds: list,
        integrator: TensorizedSampler,
        rank: int,
        **kwargs,
    ):
        nn.Module.__init__(self)
        AbstractApproxSpace.__init__(self, nb_unknowns)
        self.bound = bounds
        self.integrator = integrator
        self.L = torch.tensor([bounds[i][1] - bounds[i][0] for i in range(len(bounds))])
        self.basis_type = basis_type
        self.nb_mods_by_direction = nb_mods_by_direction
        self.rank = rank
        self.type_space = "space"

        def default_pre_processing(x: LabelTensor, mu: LabelTensor):
            return torch.cat([x.x, mu.x], dim=1)

        def default_post_processing(
            inputs: torch.Tensor, x: LabelTensor, mu: LabelTensor
        ):
            return inputs

        self.pre_processing = kwargs.get("pre_processing", default_pre_processing)
        self.post_processing = kwargs.get("post_processing", default_post_processing)
        self.pre_processing_out_size = kwargs.get(
            "pre_processing_out_size", len(bounds)
        )
        self.post_processing_in_size = kwargs.get(
            "post_processing_in_size", self.nb_unknowns
        )

        default_tensor_structure = [[1] * self.pre_processing_out_size] * self.rank
        self.tensor_structure = kwargs.get("tensor_structure", default_tensor_structure)

        # modify the tensor_structure_rank_dim list: [1, 1, 2] -> [0, 1, 2, 4]

        expanded_structure = []
        for i, tensor_structure_rank in enumerate(self.tensor_structure):
            expanded_structure.append([0])
            for t_ in tensor_structure_rank:
                expanded_structure[-1].append(expanded_structure[-1][-1] + t_)
        self.expanded_structure = expanded_structure

        # create structured bounds

        bounds_with_structure = []
        for local_structure in self.expanded_structure:
            bounds_with_structure.append([])
            for start, end in zip(local_structure[:-1], local_structure[+1:]):
                bounds_with_structure[-1].append(bounds[start:end])
        self.bounds_with_structure = bounds_with_structure

        # setup the network as a list of modules
        self.network = nn.ModuleList(
            [
                SpectralxSpace(
                    self.nb_unknowns,
                    basis_type,
                    nb_mods_by_direction,
                    bounds=bounds_with_structure_rank_dim,
                    integrator=integrator,
                    **kwargs,
                )
                for bounds_with_structure_rank in self.bounds_with_structure
                for bounds_with_structure_rank_dim in bounds_with_structure_rank
            ]
        )

        self.ndof = self.get_dof(flag_scope="all", flag_format="tensor").shape[0]

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """Evaluate the parametric model for given input features.

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

        return res

    def evaluate(
        self, x: LabelTensor, mu: LabelTensor, with_last_layer: bool = True
    ) -> MultiLabelTensor:
        """Evaluate the parametric model for given inputs and parameters.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.
            with_last_layer: whether to include the last layer in the evaluation
                (Default value = True)

        Returns:
            Output tensor from the neural network, wrapped with multi-label metadata.

        Raises:
            ValueError: If `with_last_layer` is False.
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
            flag_scope: (Default value = "all")

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
            flag_scope: (Default value = "all")
            flag_format:  (Default value = "list")

        Returns:
            The network parameters in the specified format.

        Raises:
            ValueError: If the flag_scope is not "all"
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
            [
                j.reshape((features.shape[0], self.post_processing_in_size, -1))
                for j in jac
            ],
            dim=-1,
        )
        jac_mt = jac_m.transpose(1, 2)
        return self.post_processing(jac_mt, x, mu)

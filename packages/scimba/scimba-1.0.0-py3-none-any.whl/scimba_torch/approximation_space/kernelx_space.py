"""Defines the Kernel-based approximation space and its components."""

from typing import Any

import torch
import torch.nn as nn
from torch.func import functional_call, jacrev, vmap

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.domain.meshless_domain.base import VolumetricDomain
from scimba_torch.integration.monte_carlo import TensorizedSampler
from scimba_torch.neural_nets.coordinates_based_nets.scimba_module import ScimbaModule
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor


class GaussianKernel(nn.Module):
    """Gaussian kernen approximation space.

    Args:
        **kwargs: Additional arguments for the Gaussian kernel.
    """

    def __init__(self, **kwargs: Any):
        super().__init__()

    def forward(self, vector_diff: torch.Tensor, aniso: torch.Tensor) -> torch.Tensor:
        """Compute the Gaussian kernel values.

        Args:
            vector_diff: Tensor of shape (num_samples, num_centers, input_dim)
                representing the difference between input points and kernel centers.
            aniso: Tensor of shape (num_centers, input_dim, input_dim) representing
                the anisotropic transformation matrices for each kernel center.

        Returns:
            Tensor of shape (num_samples, num_centers) containing the Gaussian kernel
                values.
        """
        distances = torch.einsum("nkd,kdd,nkd->nk", vector_diff, aniso, vector_diff)
        return torch.exp(-distances)


class ExponentialKernel(nn.Module):
    """Exponential kernel approximation space.

    Args:
        **kwargs: Additional arguments for the Exponential kernel.

            - beta: Shape parameter of the Exponential kernel (default: 2).
    """

    def __init__(self, **kwargs: Any):
        super().__init__()
        self.beta = kwargs.get("beta", 2)

    def forward(self, vector_diff: torch.Tensor, aniso: torch.Tensor) -> torch.Tensor:
        """Compute the Exponential kernel values.

        Args:
            vector_diff: Tensor of shape (num_samples, num_centers, input_dim)
                representing the difference between input points and kernel centers.
            aniso: Tensor of shape (num_centers, input_dim, input_dim) representing
                the anisotropic transformation matrices for each kernel center.

        Returns:
            Tensor of shape (num_samples, num_centers) containing the Exponential
                kernel values.
        """
        l1_norm = torch.sum(torch.abs(vector_diff), dim=-1)
        return torch.exp(-((l1_norm) ** self.beta))


class MultiquadraticKernel(nn.Module):
    """Multiquadratic kernel approximation space.

    Args:
        **kwargs: Additional arguments for the Multiquadratic kernel.

            - beta: Shape parameter of the Multiquadratic kernel (default: 2).
    """

    def __init__(self, **kwargs: Any):
        super().__init__()
        self.beta = kwargs.get("beta", 2)

    def forward(self, vector_diff: torch.Tensor, aniso: torch.Tensor) -> torch.Tensor:
        """Compute the Multiquadratic kernel values.

        Args:
            vector_diff: Tensor of shape (num_samples, num_centers, input_dim)
                representing the difference between input points and kernel centers.
            aniso: Tensor of shape (num_centers, input_dim, input_dim) representing
                the anisotropic transformation matrices for each kernel center.

        Returns:
            Tensor of shape (num_samples, num_centers) containing the Multiquadratic
                kernel values.
        """
        distances = torch.einsum("nkd,kdd,nkd->nk", vector_diff, aniso, vector_diff)
        return (1 + (distances) ** 2) ** self.beta


class KernelxSpace(AbstractApproxSpace, ScimbaModule):
    """A nonlinear approximation space using a neural network model.

    This class represents a parametric approximation space, where the solution
    is modeled by a neural network. It integrates functionality for evaluating the
    network, setting/retrieving degrees of freedom, and computing the Jacobian.

    Args:
        nb_unknowns: Number of unknowns in the approximation problem.
        nb_parameters: Number of parameters in the approximation problem.
        kernel_type: The type of kernel to use for the approximation.
        nb_centers: Number of centers for the kernel functions.
        spatial_domain: The spatial domain of the problem.
        integrator: Sampler used for integration over the spatial and parameter domains.
        **kwargs: Additional arguments passed to the neural network model.
    """

    def __init__(
        self,
        nb_unknowns: int,
        nb_parameters: int,
        kernel_type: nn.Module,
        nb_centers: int,
        spatial_domain: VolumetricDomain,
        integrator: TensorizedSampler,
        **kwargs,
    ):
        # Call the initializer of ScimbaModule
        ScimbaModule.__init__(
            self,
            in_size=spatial_domain.dim + nb_parameters,  # problem
            out_size=nb_unknowns,
            **kwargs,
        )

        # Call the initializer of AbstractApproxSpace
        AbstractApproxSpace.__init__(self, nb_unknowns)
        self.spatial_domain: VolumetricDomain = spatial_domain

        self.integrator: TensorizedSampler = integrator

        self.kernel_type: nn.Module = kernel_type
        self.anisotropic: bool = kwargs.get("anisotropic", False)
        self.type_space: str = "space"

        def default_pre_processing(x: LabelTensor, mu: LabelTensor):
            return torch.cat([x.x, mu.x], dim=1)

        def default_post_processing(
            inputs: torch.Tensor, x: LabelTensor, mu: LabelTensor
        ):
            return inputs

        self.pre_processing = kwargs.get("pre_processing", default_pre_processing)
        self.post_processing = kwargs.get("post_processing", default_post_processing)

        # self.centers = next(self.integrator.sample(nb_centers))
        self.centers_x, self.centers_mu = self.integrator.sample(nb_centers)

        self.centers: torch.nn.Parameter = nn.Parameter(
            torch.cat([self.centers_x.x, self.centers_mu.x], dim=1)
        )  #: Centers of the kernel functions, initialized as learnable parameters.

        self.kernel = kernel_type(**kwargs)
        #: Parameter for the kernel functions, controlling their shape and behavior.
        self.beta: float = kwargs.get("beta", 2)

        # Création d'une liste de matrice anistrope E pour le noyau anisotrope
        # E = M*M^T+ Id*eps      M: rdm
        if self.anisotropic:
            M = torch.randn(
                (self.centers.shape[0], self.centers.shape[1], self.centers.shape[1]),
                dtype=torch.get_default_dtype(),
            )
            E = (
                M @ M.transpose(-1, -2)
                + torch.eye(self.centers.shape[1], dtype=torch.get_default_dtype())
                * 1e-5
            )
            #: Anisotropic transformation matrix for the kernel functions,
            #: initialized as learnable parameters.
            self.M_aniso: torch.nn.Parameter = nn.Parameter(kwargs.get("eps", 1.0) * E)
        else:
            #: Epsilon parameters for the kernel functions,
            #: initialized as learnable parameters.
            self.eps: torch.nn.Parameter = nn.Parameter(
                torch.ones(nb_centers) * kwargs.get("eps", 1.0)
            )

        self.output_layer = torch.nn.Linear(nb_centers, self.out_size)
        #: Total number of degrees of freedom in the network.
        self.ndof: int = self.get_dof(flag_format="tensor").shape[0]
        self.Id = torch.eye(spatial_domain.dim + nb_parameters)

    def forward(
        self, features: torch.Tensor, with_last_layer: bool = True
    ) -> torch.Tensor:
        """Forward pass through the kernel model.

        Args:
            features: Input tensor with concatenated spatial and parameter data.
            with_last_layer: Whether to apply the final linear layer.

        Returns:
            Output tensor from the kernel model.
        """
        vect_diff = torch.zeros((features.shape[0], self.centers.shape[0], 2))
        vect_diff = features.unsqueeze(1) - self.centers.unsqueeze(0)

        if self.anisotropic:
            # Apply anisotropic transformation
            Aniso = self.M_aniso
        else:
            Aniso = self.eps[:, None, None] * self.Id
        basis = self.kernel(vect_diff, Aniso)  # (batch_size, nb_centers)

        if with_last_layer:
            res = self.output_layer(basis)
        else:
            res = basis

        return res

    def evaluate(
        self, x: LabelTensor, mu: LabelTensor, with_last_layer: bool = True
    ) -> MultiLabelTensor:
        """Evaluate the parametric model for given inputs and parameters.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor from the parameter domain.
            with_last_layer: Whether to apply the final linear layer.

        Returns:
            Output tensor from the neural network, wrapped with multi-label metadata.
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
            flag_scope: The scope of parameters to return.
        """
        self.set_parameters(theta, flag_scope)

    def get_dof(
        self, flag_scope: str = "all", flag_format: str = "list"
    ) -> torch.Tensor:
        """Retrieves the degrees of freedom (DoF) of the neural network.

        Args:
            flag_scope: The scope of parameters to return.
            flag_format: The format of the returned parameters.

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

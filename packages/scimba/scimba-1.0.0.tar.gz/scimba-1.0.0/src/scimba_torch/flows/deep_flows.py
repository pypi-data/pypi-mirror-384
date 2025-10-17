"""Discrete and continuous flow-based approximation spaces.

It includes functionality for evaluating the networks,
setting/retrieving degrees of freedom, and computing Jacobians.
"""

from typing import Any, Callable

import torch
import torch.nn as nn
from torch.func import functional_call, jacrev, vmap

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.neural_nets.coordinates_based_nets.mlp import GenericMLP
from scimba_torch.neural_nets.structure_preserving_nets.sympnet import SympNet


def identity(input: Any) -> Any:
    """Identity function that returns the input as is.

    Args:
        input: Any input.

    Returns:
        The input unchanged.
    """
    return input


class DiscreteFlowSpace(AbstractApproxSpace, nn.Module):
    """A nonlinear approximation space using a neural network model.

    This class represents a parametric approximation space, where the solution
    is modeled by a neural network. It integrates functionality for evaluating the
    network, setting/retrieving degrees of freedom, and computing the Jacobian.

    Args:
        nb_unknowns: Number of unknowns in the approximation problem.
        nb_parameters: Number of parameters in the input.
        flow_type: The neural network class used to approximate the solution.
        **kwargs: Additional arguments passed to the neural network model.
    """

    #: Size of the input to the neural network (spatial dimension + parameters).
    in_size: int
    out_size: int  #: Size of the output of the neural network (number of unknowns).
    param_dim: int  #: Number of parameters in the input.
    rollout: int  #: Number of rollout steps.
    post_processing: Callable  #: Post-processing function applied to outputs.
    apply_at_each_step: Callable  #: Function applied at each step during inference.
    network: torch.nn.Module  #: Neural network used for the approximation.
    ndof: int  #: Total number of degrees of freedom in the network.
    type_space: str  #: Type of the approximation space.

    def __init__(
        self,
        nb_unknowns: int,
        nb_parameters: int,
        flow_type: torch.nn.Module,
        **kwargs,
    ):
        # super().__init__(nb_unknowns)
        nn.Module.__init__(self)
        AbstractApproxSpace.__init__(self, nb_unknowns)
        self.in_size = nb_unknowns
        self.param_dim = nb_parameters
        self.out_size = nb_unknowns
        self.rollout = kwargs.get("rollout", 1)
        self.post_processing = kwargs.get("post_processing", identity)
        self.apply_at_each_step = kwargs.get("apply_at_each_step", identity)

        self.network = flow_type(
            in_size=self.in_size,
            out_size=self.out_size,
            param_dim=self.param_dim,
            **kwargs,
        )

        self.ndof = self.get_dof(flag_format="tensor").shape[0]
        self.type_space = "flow"

    def forward(
        self, x: torch.Tensor, mu: torch.Tensor, with_last_layer: bool = True
    ) -> torch.Tensor:
        """Evaluate the parametric model for given input features.

        Args:
            x: Input tensor representing the state.
            mu: Input tensor representing the parameters.
            with_last_layer: Whether to include the last layer in evaluation.

        Returns:
            Output tensor from the neural network.
        """
        outputs = self.network(x, mu)
        return self.post_processing(outputs)

    def evaluate(
        self, x: torch.Tensor, mu: torch.Tensor, with_last_layer: bool = True, **kwargs
    ) -> torch.Tensor:
        """Evaluate the model with optional rollout over multiple steps.

        Args:
            x: Input tensor representing the initial state.
            mu: Input tensor representing the parameters.
            with_last_layer: Whether to include the last layer in evaluation.
            **kwargs: Additional arguments (not used here).

        Returns:
            Output tensor after applying the model for the specified number of rollout
                steps.
        """
        for i in range(self.rollout):
            x = self.forward(x, mu, with_last_layer)
        return x

    def inference(
        self,
        x: torch.Tensor,
        mu: torch.Tensor,
        n: int = 1,
        with_last_layer: bool = True,
        **kwargs,
    ) -> torch.Tensor:
        """Perform inference over multiple steps and return the trajectory.

        Args:
            x: Input tensor representing the initial state.
            mu: Input tensor representing the parameters.
            n: Number of steps.
            with_last_layer: Whether to include the last layer in evaluation
                (default: True).
            **kwargs: Additional arguments (not used here).

        Returns:
            Tensor containing the trajectory of states over the steps.
        """
        trajectories = torch.zeros((n, x.shape[0] + mu.shape[0], x.shape[1]))
        for i in range(0, n):
            for j in range(self.rollout):
                x = self.forward(x, mu, with_last_layer)
                x = self.apply_at_each_step(x)
            trajectories[i] = x
        return trajectories

    def set_dof(self, theta: torch.Tensor, flag_scope: str = "all") -> None:
        """Sets the degrees of freedom (DoF) for the neural network.

        Args:
            theta: A vector containing the network parameters.
            flag_scope: Scope flag for setting degrees of freedom..
        """
        self.network.set_parameters(theta, flag_scope)

    def get_dof(
        self, flag_scope: str = "all", flag_format: str = "list"
    ) -> torch.Tensor:
        """Retrieves the degrees of freedom (DoF) of the neural network.

        Args:
            flag_scope: Scope flag for getting degrees of freedom.
            flag_format: The format for returning the parameters. Options are "list" or
                "tensor".

        Returns:
            The network parameters in the specified format.
        """
        return self.network.parameters(flag_scope, flag_format)

    # TODO change to have the jacobian of evaluate
    def jacobian(self, x: torch.Tensor, mu: torch.Tensor) -> torch.Tensor:
        """Compute the Jacobian of the network with respect to its parameters.

        Args:
            x: Input tensor from the spatial domain.
            mu: Input tensor representing the parameters.

        Returns:
            Jacobian matrix of shape `(num_samples, out_size, num_params)`.
        """
        params = {k: v.detach() for k, v in self.named_parameters()}

        def fnet(theta, x, mu):
            return functional_call(
                self, theta, (x.unsqueeze(0), mu.unsqueeze(0))
            ).squeeze(0)

        jac = vmap(jacrev(fnet), (None, 0, 0))(params, x, mu).values()
        jac_m = torch.cat(
            [j.reshape((x.shape[0], self.out_size, -1)) for j in jac],
            dim=-1,
        )
        jac_mt = jac_m.transpose(1, 2)
        return jac_mt


class ContinuousFlowSpace(nn.Module):
    """A continuous-time flow model that can be used for generating flows.

    This model computes a forward pass by combining time, state, and parameters using
    different architectures, such as MLP or SympNet.

    Args:
        size: The size of the input/output tensor.
        param_dim: The size of the parameters tensor.
        **kwargs: Additional keyword arguments that specify the type of flow model
            (e.g., "mlp" or "sympnet").
    """

    size: int  #: The size of the input/output tensor.
    param_dim: int  #: The size of the parameters tensor.
    flowtype: str  #: Type of the flow model, can be "mlp", "sympnet", etc.
    net: (
        nn.Module
    )  #: The neural network model used for transformations, either a MLP or a SympNet.

    def __init__(self, size: int, param_dim: int, **kwargs: Any):
        super().__init__()
        self.size = size
        self.param_dim = param_dim
        self.flowtype = kwargs.get("flowtype", "mlp")
        if self.flowtype == "mlp":
            self.net = GenericMLP(self.size + self.param_dim + 1, self.size, **kwargs)
        if self.flowtype == "sympnet":
            self.net = SympNet(
                dim=self.size,
                p_dim=self.param_dim + 1,
                parameters_scaling_number=-1,
                **kwargs,
            )

    def forward(
        self, t: torch.Tensor, x: torch.Tensor, mu: torch.Tensor
    ) -> torch.Tensor:
        """Computes the forward pass of the ContinuousFlow model.

        Args:
            t: The input tensor representing time, of shape `(batch_size, 1)`.
            x: The input tensor representing state, of shape `(batch_size, size)`.
            mu: The input tensor representing parameters, of shape
                `(batch_size, param_dim)`.

        Returns:
            The output tensor after applying the transformation.
        """
        inputs = torch.cat((x, mu, t), dim=1)
        outputs = self.net.forward(inputs)
        return outputs

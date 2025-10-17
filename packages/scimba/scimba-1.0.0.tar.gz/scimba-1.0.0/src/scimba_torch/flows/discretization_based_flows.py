"""Flows based on neural networks or classical discretization schemes.

These flows can be used to define neural ODEs or other types of flows.
"""

from typing import Any, Callable

import torch
import torch.nn as nn
from torch.func import vmap

from scimba_torch.neural_nets.coordinates_based_nets.features import (
    FourierMLP,
    MultiScaleFourierMLP,
)
from scimba_torch.neural_nets.coordinates_based_nets.mlp import GenericMLP, GenericMMLP
from scimba_torch.neural_nets.coordinates_based_nets.scimba_module import ScimbaModule
from scimba_torch.neural_nets.structure_preserving_nets.invertible_nn import (
    InvertibleNet,
)
from scimba_torch.neural_nets.structure_preserving_nets.sympnet import SympNet


class NeuralFlow(ScimbaModule):
    """Neural flow based on a given neural network.

    Args:
        in_size: Size of the input to the neural network.
        out_size: Size of the output of the neural network.
        param_dim: Number of parameters in the input.
        net_type: The neural network class used to approximate the solution.
        analytic_f: An optional analytic function to be added to the network output.
        **kwargs: Additional arguments passed to the neural network model.
    """

    def __init__(
        self,
        in_size: int,
        out_size: int,
        param_dim: int,
        net_type: nn.Module,
        analytic_f: Callable | None = None,
        **kwargs: Any,
    ):
        super().__init__(in_size, out_size)
        self.param_dim = param_dim
        self.analytic_f = analytic_f
        if net_type in [GenericMLP, GenericMMLP, FourierMLP, MultiScaleFourierMLP]:
            self.F = net_type(in_size + self.param_dim, out_size, **kwargs)
        if net_type in [SympNet, InvertibleNet]:
            self.F = net_type(dim=in_size, p_dim=self.param_dim, **kwargs)

    def forward(self, x: torch.Tensor, mu: torch.Tensor) -> torch.Tensor:
        """Forward pass of the neural flow.

        Args:
            x: Input tensor.
            mu: Parameter tensor.

        Returns:
            The output tensor after applying the neural network and optional analytic
            function.
        """
        res = self.F(torch.cat([x, mu], dim=-1))
        if self.analytic_f is not None:
            res = res + self.analytic_f(x, mu)
        return res


class ExplicitEulerFlow(ScimbaModule):
    """Explicit Euler flow based on a given neural network.

    Args:
        in_size: Size of the input to the neural network.
        out_size: Size of the output of the neural network.
        param_dim: Number of parameters in the input.
        net_type: The neural network class used to approximate the solution.
        dt: Time step for the Euler update.
        analytic_f: An optional analytic function to be added to the network output.
        **kwargs: Additional arguments passed to the neural network model.
    """

    def __init__(
        self,
        in_size: int,
        out_size: int,
        param_dim: int,
        net_type: nn.Module,
        dt: float = 0.01,
        analytic_f: Callable | None = None,
        **kwargs,
    ):
        super().__init__(in_size, out_size)
        self.dt = dt
        self.analytic_f = analytic_f
        self.param_dim = param_dim
        self.F = net_type(in_size + self.param_dim, out_size, **kwargs)

    def forward(self, x: torch.Tensor, mu: torch.Tensor) -> torch.Tensor:
        """Forward pass of the neural flow.

        Args:
            x: Input tensor.
            mu: Parameter tensor.

        Returns:
            The output tensor after applying the neural network
                and optional analytic function.
        """
        res = self.F(torch.cat([x, mu], dim=-1))
        if self.analytic_f is not None:
            res = res + self.analytic_f(x, mu)
        return x + self.dt * res  # Explicit Euler step


class ExplicitEulerHamiltonianFlow(ScimbaModule):
    """Explicit Euler flow for a Hamiltonian system based on a given neural network.

    Args:
        in_size: Size of the input to the neural network.
        out_size: Size of the output of the neural network.
        param_dim: Number of parameters in the input.
        net_type: The neural network class used to approximate the solution.
        dt: Time step for the Euler update.
        analytic_h: An optional analytic function to be added to the network output.
        **kwargs: Additional arguments passed to the neural network model.
    """

    def __init__(
        self,
        in_size: int,
        out_size: int,
        param_dim: int,
        net_type: nn.Module,
        dt: float = 0.01,
        analytic_h: Callable | None = None,
        **kwargs: Any,
    ):
        assert in_size % 2 == 0, "Input size must be even for Hamiltonian systems."

        super().__init__(in_size, out_size)

        self.dt = dt
        self.analytic_h = analytic_h
        self.param_dim = param_dim
        self.space_dim = in_size // 2

        self.H = net_type(in_size + self.param_dim, 1, **kwargs)

    def h_func(self, x: torch.Tensor, mu: torch.Tensor, params: dict) -> torch.Tensor:
        """Computes the Hamiltonian function using the neural network.

        Args:
            x: Input tensor.
            mu: Parameter tensor.
            params: Parameters of the neural network.

        Returns:
            The output tensor after applying the neural network.
        """
        return torch.func.functional_call(self.H, params, torch.cat([x, mu], dim=-1))

    def forward(self, x: torch.Tensor, mu: torch.Tensor) -> torch.Tensor:
        """Forward pass of the neural flow.

        Args:
            x: Input tensor.
            mu: Parameter tensor.

        Returns:
            The output tensor after applying the Explicit Euler Hamiltonian update.
        """
        params = {k: v for k, v in self.H.named_parameters()}

        dH_dx = vmap(torch.func.jacrev(self.h_func, 0), (0, 0, None))(x, mu, params)
        dHanalytic_dx = vmap(torch.func.jacrev(self.analytic_h, 0))(x, mu)

        dH_dq, dH_dp = (
            dH_dx[:, 0, : self.space_dim] + dHanalytic_dx[:, : self.space_dim],
            dH_dx[:, 0, self.space_dim :] + dHanalytic_dx[:, self.space_dim :],
        )

        F = torch.cat([dH_dp, -dH_dq], dim=1)

        return x + self.dt * F


class SymplecticEulerFlowSep(ScimbaModule):
    """Symplectic Euler flow for a Hamiltonian system based on a given neural network.

    Args:
        in_size: Size of the input to the neural network.
        out_size: Size of the output of the neural network.
        param_dim: Number of parameters in the input.
        net_type: The neural network class used to approximate the solution.
        dt: Time step for the Euler update.
        **kwargs: Additional arguments passed to the neural network model.
    """

    def __init__(
        self,
        in_size: int,
        out_size: int,
        param_dim: int,
        net_type: nn.Module,
        dt: float = 0.01,
        **kwargs: Any,
    ):
        assert in_size % 2 == 0, "Input size must be even for Hamiltonian systems."

        super().__init__(in_size, out_size)

        self.dt = dt
        self.param_dim = param_dim
        self.space_dim = in_size // 2

        self.K = net_type(
            self.space_dim + self.param_dim, 1, last_layer_has_bias=False, **kwargs
        )
        self.U = net_type(
            self.space_dim + self.param_dim, 1, last_layer_has_bias=False, **kwargs
        )

    def k_func(self, p: torch.Tensor, mu: torch.Tensor, params: dict) -> torch.Tensor:
        """Computes the kinetic energy term.

        Args:
            p: Momentum tensor.
            mu: Parameter tensor.
            params: Parameters of the neural network.

        Returns:
            The output tensor after applying the neural network.
        """
        return torch.func.functional_call(self.K, params, torch.cat([p, mu], dim=-1))

    def u_func(self, q: torch.Tensor, mu: torch.Tensor, params: dict) -> torch.Tensor:
        """Computes the potential energy term.

        Args:
            q: Position tensor.
            mu: Parameter tensor.
            params: Parameters of the neural network.

        Returns:
            The output tensor after applying the neural network.
        """
        return torch.func.functional_call(self.U, params, torch.cat([q, mu], dim=-1))

    def forward(self, x: torch.Tensor, mu: torch.Tensor) -> torch.Tensor:
        r"""Symplectic Euler update.

        ..math::
            q_{n+1} = q_n + dt \frac{\partial H}{\partial p}, \\
            p_{n+1} = p_n - dt \frac{\partial H}{\partial q}.

        Args:
            x: Input tensor.
            mu: Parameter tensor.

        Returns:
            The output tensor after applying the Symplectic Euler update.
        """
        m = x.shape[1] // 2
        params_u = {k: v for k, v in self.U.named_parameters()}
        params_k = {k: v for k, v in self.K.named_parameters()}
        q, p = x[:, :m], x[:, m:]

        dU_dq = vmap(torch.func.jacrev(self.u_func, 0), (0, 0, None))(q, mu, params_u)
        p = p - self.dt * dU_dq[:, 0, :]

        dK_dp = vmap(torch.func.jacrev(self.k_func, 0), (0, 0, None))(p, mu, params_k)
        q = q + self.dt * dK_dp[:, 0, :]

        return torch.cat([q, p], dim=1)


class VerletSymplecticEulerFlow(ScimbaModule):  # noqa: D101
    pass


class Rk2Flow(ScimbaModule):  # noqa: D101
    pass


class Rk4Flow(ScimbaModule):  # noqa: D101
    pass

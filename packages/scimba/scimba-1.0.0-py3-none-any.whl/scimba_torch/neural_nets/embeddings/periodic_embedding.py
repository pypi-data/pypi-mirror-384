"""Periodic and flipped embeddings."""

import torch


class PeriodicEmbedding(torch.nn.Module):
    """Creates a one-layer network to model a periodic embedding of the input data.

    The learnable parameters are the weights, phases and biases of the periodic
    functions.

    Args:
        in_size: dimension of inputs
        out_size: dimension of outputs
        periods: periods of the periodic functions
    """

    def __init__(self, in_size: int, out_size: int, periods: torch.Tensor):
        super().__init__()
        self.in_size = in_size
        self.out_size = out_size
        self.periods = periods

        weight = torch.randn(1, in_size, out_size)
        phase = torch.randn(1, in_size, out_size)
        bias = torch.randn(1, in_size, out_size)
        self.weight: torch.nn.Parameter = torch.nn.Parameter(
            weight
        )  #: the weights of the layer
        self.phase: torch.nn.Parameter = torch.nn.Parameter(
            phase
        )  #: the phase of the layer
        self.bias: torch.nn.Parameter = torch.nn.Parameter(
            bias
        )  #: the bias of the layer

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass of the periodic embedding layer.

        Args:
            x: input tensor

        Returns:
            output tensor
        """
        # ensures shape [N, p] (in case of natural gradient)
        x = x.reshape(-1, x.shape[-1])
        # [N, p, 1] + [1, p, d] => [N, p, d]
        arg = (2 * torch.pi * x / self.periods)[..., None] + self.phase
        # [1, p, d] * [N, p, d] + [1, p, d]
        out = self.weight * torch.cos(arg) + self.bias
        # sum over p → shape [N, d]
        out = out.sum(dim=1)
        # squeeze to remove the first dimension if it is 1
        return out.squeeze(0) if x.shape[0] == 1 else out


class FlippedEmbedding(torch.nn.Module):
    """Creates a one-layer network to model a flipped embedding of the input data.

    It is only available for 2D inputs on the unit square.

    Args:
        in_size: dimension of inputs
        out_size: dimension of outputs
    """

    def __init__(self, in_size: int, out_size: int):
        super().__init__()
        self.in_size = in_size
        self.out_size = out_size

        weight = 1 + torch.randn(1, in_size, out_size) / 10
        bias = 1.5 + torch.randn(1, in_size, out_size) / 5
        coeff_x1 = 2 + torch.randn(1, in_size, out_size) / 5
        coeff_x2 = 2 + torch.randn(1, in_size, out_size) / 5

        self.weight = torch.nn.Parameter(weight)
        self.bias = torch.nn.Parameter(bias)
        self.coeff_x1 = torch.nn.Parameter(coeff_x1)
        self.coeff_x2 = torch.nn.Parameter(coeff_x2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass of the flipped embedding layer.

        Args:
            x: input tensor

        Returns:
            output tensor
        """
        x1, x2 = x[..., 0, None, None], x[..., 1, None, None]
        x1_ = self.coeff_x1 * (x1 - 1 / 2)
        x2_ = self.coeff_x2 * (x2 - 1 / 2)
        return (self.weight * torch.tanh(x1_) * torch.tanh(x2_) + self.bias).sum(dim=1)

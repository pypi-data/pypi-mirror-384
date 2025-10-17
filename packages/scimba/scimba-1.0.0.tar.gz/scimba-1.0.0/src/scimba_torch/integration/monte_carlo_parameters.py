"""Parameter samplers for Monte Carlo simulations."""

from typing import Any, Sequence, cast

import torch

from scimba_torch.domain.meshless_domain.domain_1d import Segment1D
from scimba_torch.domain.meshless_domain.domain_2d import Circle2D, Square2D
from scimba_torch.domain.meshless_domain.domain_3d import Cube3D
from scimba_torch.utils.scimba_tensors import LabelTensor

PARAM_TYPE = int | float


def _is_param_type(arg: Any) -> bool:
    return isinstance(arg, int) or isinstance(arg, float)


def _is_param_domain_type(arg: Any) -> bool:
    return isinstance(arg, Sequence) and all(
        isinstance(a, Sequence)
        and (len(a) == 2)
        and _is_param_type(a[0])
        and _is_param_type(a[0])
        for a in arg
    )


def _check_and_cast_argument(bounds: Any) -> tuple[bool, list[tuple[float, float]]]:
    resT = []
    resB = _is_param_domain_type(bounds)
    if resB:
        arg = cast(Sequence, bounds)
        for a in arg:
            resT.append((float(a[0]), float(a[1])))

    return resB, resT


class UniformParametricSampler:
    """Sample uniformly from given bounds for each dimension.

    Args:
        bounds: A list of tuples where each tuple contains the lower and upper bounds
            for each dimension.

    Raises:
        TypeError: If parameters domain is not a list of tuples of two floats.
        ValueError: If any bound has lower value greater than upper value.
    """

    def __init__(self, bounds: list[tuple[float, float]]):
        check, nbounds = _check_and_cast_argument(bounds)
        if not check:
            raise TypeError("parameters domain must be a list of tuples of two floats")

        if not all(bound[0] <= bound[1] for bound in nbounds):
            raise ValueError(
                "can not create a time sampler for empty time domain " + str(nbounds)
            )

        #: A list of tuples where each tuple contains the lower and upper bounds
        #: for each dimension.
        self.bounds = nbounds
        self.dim = len(
            self.bounds
        )  #: The number of dimensions, inferred from the length of bounds.

    def sample(self, n: int) -> LabelTensor:
        """Generates samples uniformly within the specified bounds for each dimension.

        Args:
            n: The number of samples to generate.

        Returns:
            A tensor containing the generated samples and corresponding labels.

        Raises:
            TypeError: If argument is not an integer.
            ValueError: If argument is negative.
        """
        if not isinstance(n, int):
            raise TypeError("argument to sample method must be an integer")
        if n < 0:
            raise ValueError("argument to sample method must be non-negative")

        samples = torch.rand(n, self.dim)
        for i in range(self.dim):
            samples[:, i] = (
                samples[:, i] * (self.bounds[i][1] - self.bounds[i][0])
                + self.bounds[i][0]
            )
        samples.requires_grad_()
        labels = torch.zeros(n, dtype=torch.int32)
        data = LabelTensor(samples, labels)
        return data


class UniformVelocitySampler:
    """Sample uniformly the velocities in a circle of radius r.

    Args:
        velocity_domain: Velocity domain in which the velocity will be drawn.

    Raises:
        TypeError: If velocity domain is not an object of class Circle2D.
    """

    def __init__(self, velocity_domain: Circle2D):
        if not isinstance(velocity_domain, Circle2D):
            raise TypeError("velocity domain must be an object of class Circle2D")

        self.velocity_domain = (
            velocity_domain  #: Velocity domain in which the velocity will be drawn.
        )
        self.dim = velocity_domain.dim  #: The number of dimensions, here equal to 2.

    def sample(self, n: int) -> LabelTensor:
        """Generates samples uniformly within the specified bounds for each dimension.

        Args:
            n: The number of samples to generate.

        Returns:
            A tensor containing the generated samples and corresponding labels.

        Raises:
            TypeError: If argument is not an integer.
            ValueError: If argument is negative.
        """
        if not isinstance(n, int):
            raise TypeError("argument to sample method must be an integer")
        if n < 0:
            raise ValueError("argument to sample method must be non-negative")

        theta = torch.rand(n) * 2 * torch.pi - torch.pi

        samples = torch.zeros(n, self.dim)

        samples[:, 0] = self.velocity_domain.radius * torch.cos(theta[:])
        samples[:, 1] = self.velocity_domain.radius * torch.sin(theta[:])

        samples.requires_grad_()
        labels = torch.zeros(n, dtype=torch.int32)
        data = LabelTensor(samples, labels)
        return data


class UniformVelocitySamplerOnCuboid:
    """Sample uniformly the velocities in a cuboid.

    Args:
        velocity_domain: Velocity domain in which the velocity will be drawn.

    Raises:
        TypeError: If velocity domain is not an object of class Segment1D, Square2D
            or Cube3D.
    """

    def __init__(self, velocity_domain: Segment1D | Square2D | Cube3D):
        if not isinstance(velocity_domain, (Segment1D, Square2D, Cube3D)):
            raise TypeError(
                "velocity domain must be an object of class Segment1D, Square2D or "
                f"Cube3D, got {type(velocity_domain)}"
            )

        self.velocity_domain = (
            velocity_domain  #: Velocity domain in which the velocity will be drawn.
        )
        self.dim = velocity_domain.dim  #: The number of dimensions.

        self.domain_size = (
            self.velocity_domain.bounds[:, 1] - self.velocity_domain.bounds[:, 0]
        )  #: The size of the domain in each dimension.
        self.lower_bound = self.velocity_domain.bounds[
            :, 0
        ]  #: The lower bound of the domain.

    def sample(self, n: int) -> LabelTensor:
        """Generates samples uniformly within the specified bounds for each dimension.

        Args:
            n: The number of samples to generate.

        Returns:
            A tensor containing the generated samples and corresponding labels.

        Raises:
            TypeError: If argument is not an integer.
            ValueError: If argument is negative.
        """
        if not isinstance(n, int):
            raise TypeError("argument to sample method must be an integer")
        if n < 0:
            raise ValueError("argument to sample method must be non-negative")

        if self.dim == 1:
            random = torch.rand(n, requires_grad=True)
        else:
            random = torch.rand(n, self.dim, requires_grad=True)

        samples = random * self.domain_size + self.lower_bound

        if self.dim == 1:
            samples.unsqueeze_(1)

        labels = torch.zeros(n, dtype=torch.int32)

        return LabelTensor(samples, labels)

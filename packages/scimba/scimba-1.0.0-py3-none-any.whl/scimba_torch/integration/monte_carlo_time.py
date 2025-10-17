"""A uniform time sampler for Monte Carlo methods."""

from typing import Any, Sequence

import torch

from scimba_torch.utils.scimba_tensors import LabelTensor

TIME_TYPE = int | float


def _is_time_type(arg: Any) -> bool:
    return isinstance(arg, int) or isinstance(arg, float)


class UniformTimeSampler:
    """A class used to sample uniformly distributed time points within a given bound.

    Args:
        bound: A tuple representing the lower and upper bounds for sampling.

    Raises:
        TypeError: If time interval is not a Sequence of two int or float.
        ValueError: If lower bound is greater than upper bound.
    """

    def __init__(self, bound: tuple[float, float]):
        if not (
            isinstance(bound, Sequence)
            and (len(bound) == 2)
            and all(_is_time_type(b) for b in bound)
        ):
            raise TypeError("time interval must be a Sequence of two int or float")

        self.bound = (
            float(bound[0]),
            float(bound[1]),
        )  #: A tuple representing the lower and upper bounds for sampling.

        if self.bound[0] > self.bound[1]:
            raise ValueError(
                "can not create a time sampler for empty time interval [%f, %f]"
                % (self.bound[0], self.bound[1])
            )

    def sample(self, n: int) -> LabelTensor:
        """Generate a sample of random numbers within the specified bounds.

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

        samples = torch.rand(n, 1)
        samples[:, 0] = samples[:, 0] * (self.bound[1] - self.bound[0]) + self.bound[0]
        samples.requires_grad_()
        labels = torch.zeros(n, dtype=torch.int32)
        data = LabelTensor(samples, labels)
        return data

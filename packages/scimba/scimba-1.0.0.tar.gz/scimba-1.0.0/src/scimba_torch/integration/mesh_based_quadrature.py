"""Implements the rectangle method for cube-like domains."""

from typing import Any

from scimba_torch.domain.mesh_based_domain.cuboid import Cuboid
from scimba_torch.utils.scimba_tensors import LabelTensor


class RectangleMethod:
    """Implements the rectangle method for cube-like domains.

    This sampler manages a primary volumetric sampler.
    At the moment, boundary samplers are not supported.

    Args:
        domain: The volumetric domain to sample.
        **kwargs: Additional configuration options.
    """

    def __init__(self, domain: Cuboid, **kwargs: Any):
        self.domain = domain  #: The volumetric domain to be sampled.

    def sample(self, n: int) -> LabelTensor:
        """Get equidistant points in the domain.

        Args:
            n: The number of points.

        Returns:
            The points.
        """
        points = self.domain.uniform_mesh(n)
        points.x.requires_grad_()
        return points

    def bc_sample(self, n: int) -> LabelTensor:
        """Get equidistant points on the domain boundary.

        Args:
            n: The number of points.

        Returns:
            The points.

        Raises:
            NotImplementedError: Boundary sampling is not supported for the rectangle
                method.
        """
        raise NotImplementedError(
            "Boundary sampling is not supported for the rectangle method."
        )

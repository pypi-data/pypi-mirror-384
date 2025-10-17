"""Defines the signed distance function."""

from abc import ABC, abstractmethod
from typing import List, Tuple

import torch


class SignedDistance(ABC):
    """Describe the signed Distance function.

    Approximative or exact Signed distance function.

    Args:
        dim: dimension of the domain
        threshold: threshold to determinate how we sample inside the domain.
            We use signedDistance(x) < threshold
    """

    def __init__(self, dim: int, threshold: float = 0.0):
        super().__init__()
        self.dim = dim
        self.threshold = threshold
        self.sdf = (
            self.__call__
        )  # Alias for the __call__ method, to be able to use the object as before

    @abstractmethod
    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        # this make a SignedDistance object callable
        # so instead of doing sdf_obj.sdf(x), we can do sdf_obj(x)
        # magic methods in python often makes the code more readable :)
        """Returns the signed distance function at the points of x.

        Args:
            x: the ScimbaTensor

        Returns:
            the value of the sdf at the points of data
        """


class PolygonalApproxSignedDistance(SignedDistance):
    """Describe the approximate signed Distance function as described in [Sukumar2022]_.

    Args:
        dim: dimension of the domain
        points: coordinates of the vertices of the polygon
        threshold: threshold to determinate how we sample inside the domain. We use
            signedDistance(x) < threshold

    .. [Sukumar2022] N. Sukumar, Ankit Srivastava.
        Exact imposition of boundary conditions with distance functions in
        physics-informed deep neural networks.
        Computer Methods in Applied Mechanics and Engineering,
        Volume 389,
        2022,
        114333.
    """

    def __init__(
        self,
        dim: int,
        points: List[Tuple[float, float]] | torch.Tensor,
        threshold: float = 0.01,
    ):
        super().__init__(dim, threshold)
        self.points: torch.Tensor = (
            points
            if isinstance(points, torch.Tensor)
            else torch.tensor(points, dtype=torch.get_default_dtype())
        )

    def vectorial_product(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Returns the vectorial product between two batched vectors.

        Args:
            x: left tensor
            y: right tensor

        Returns:
            the vectorial product between x and y
        """
        if self.dim == 2:
            res = x[:, 0] * y[:, 1] - y[:, 0] * x[:, 1]
        return res

    def dot_product(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Returns the scalar product between two batched vectors.

        Args:
            x: left tensor
            y: right tensor

        Returns:
            the dot product between x and y
        """
        if self.dim == 2:
            res = x[:, 0] * y[:, 0] + y[:, 1] * x[:, 1]
        return res

    def vect_x_to_xi(self, x: torch.Tensor, i: int):
        """Returns the batched vector x-xi with xi vertices of the polygonal.

        Args:
            x: left tensor
            i: the number of the polygonal point

        Returns:
            the batched vector x-xi
        """
        n = x.shape[0]
        xi = self.points[i, :].repeat((n, 1))
        return xi - x

    def dist(self, y: torch.Tensor) -> torch.Tensor:
        """Returns the batched distance of a batched tensor of vector.

        Args:
            y: the tensor

        Returns:
            the batched norm of y
        """
        return torch.norm(y, dim=1)

    def phi(self, x: torch.Tensor) -> torch.Tensor:
        """Returns the batched function phi for a polygonal.

        Args:
            x: the tensor

        Returns:
            the value of phi at the point x
        """
        res = torch.zeros_like(x[:, 0])
        for i in range(0, len(self.points)):
            j = (i + 1) % len(self.points)
            ri = self.vect_x_to_xi(x, i)
            rj = self.vect_x_to_xi(x, j)
            di = self.dist(ri)
            dj = self.dist(rj)
            ti = self.vectorial_product(ri, rj) / (self.dot_product(ri, rj) + di * dj)
            res = res + (1.0 / di + 1.0 / dj) * ti
        return res[:, None]

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        """Returns the batched approximated signed distance for a polygonal.

        Args:
            x: the ScimbaTensor

        Returns:
            the value of the sdf at the points of data
        """
        return -self.dim / self.phi(x)

"""Defines the Cuboid domain and its components."""

from typing import Any

import torch

from scimba_torch.domain.meshless_domain.base import VolumetricDomain
from scimba_torch.domain.meshless_domain.domain_1d import Segment1D
from scimba_torch.domain.meshless_domain.domain_2d import Square2D
from scimba_torch.domain.meshless_domain.domain_3d import Cube3D
from scimba_torch.utils.scimba_tensors import LabelTensor


class Cuboid:
    """Cuboid domain in n dimensions.

    At the moment, boundaries, inclusions and holes are not supported.

    Args:
        bounds: The bounds of the cuboid.
        is_main_domain: Whether the domain is the main domain or not.
        **kwargs: Additional arguments.
    """

    def __init__(
        self,
        bounds: list[tuple[float, float]],
        is_main_domain: bool = True,
        **kwargs: Any,
    ):
        self.bounds: torch.Tensor = (
            bounds
            if isinstance(bounds, torch.Tensor)
            else torch.tensor(bounds, dtype=torch.get_default_dtype())
        )

        assert self.bounds.shape[1] == 2, "Bounds must be a list of pairs."

        self.dim = self.bounds.shape[0]

        self.lower_bounds, self.upper_bounds = self.bounds.T
        self.size = self.upper_bounds - self.lower_bounds

        self.domain_type = "MeshBasedCuboid"

        self.is_main_domain = is_main_domain

    def uniform_mesh(self, n: int | list | tuple, **kwargs: Any) -> LabelTensor:
        """Uniformly meshes the domain.

        Args:
            n: Total number of mesh points. If the same number of points is used in each
                dimension, equal to n ** (1 / dim). If list or tuple, the number of
                points in each dimension.
            **kwargs: Additional arguments.

        Returns:
            The mesh points.

        """
        if isinstance(n, int):
            n = [round(n ** (1 / self.dim))] * self.dim

        with torch.no_grad():
            points = []
            mesh_size = 1
            for i, n_ in enumerate(n):
                pts = torch.arange(0, 1, 1 / n_)
                pts = self.lower_bounds[i] + pts * self.size[i]
                points.append(pts)
                mesh_size *= n_

            mesh = torch.meshgrid(*points, indexing="ij")
            flat_mesh = self.flatten_mesh(mesh, mesh_size)
            return LabelTensor(flat_mesh)

    def flatten_mesh(
        self, mesh: tuple[torch.Tensor, ...], mesh_size: int
    ) -> torch.Tensor:
        """Flattens a mesh.

        Args:
            mesh: The mesh.
            mesh_size: The size of the mesh.

        Returns:
            The flattened mesh.
        """
        flat_mesh = torch.zeros((mesh_size, self.dim))
        for i in range(self.dim):
            flat_mesh[:, i] = mesh[i].flatten()
        return flat_mesh

    def to_volumetric_domain(self) -> VolumetricDomain:
        """Converts the cuboid to a volumetric domain.

        Returns:
            The volumetric domain.

        Raises:
            NotImplementedError: If the dimension is not supported.
        """
        if self.dim == 1:
            return Segment1D(self.bounds, self.is_main_domain)
        if self.dim == 2:
            return Square2D(self.bounds, self.is_main_domain)
        if self.dim == 3:
            return Cube3D(self.bounds, self.is_main_domain)

        raise NotImplementedError(
            "converting cuboid of dim %d in VolumetricDomain is not implemented yet"
            % self.dim
        )


if __name__ == "__main__":  # pragma: no cover
    n = 10
    n_2 = 5
    n_3 = 3

    # 1D Cuboid
    domain_1d = Cuboid([(0, 1)], is_main_domain=True)
    mesh_1d = domain_1d.uniform_mesh(n)
    assert mesh_1d.shape == (n, 1)

    V_domain_1d = domain_1d.to_volumetric_domain()
    assert isinstance(V_domain_1d, Segment1D)
    assert torch.all(domain_1d.bounds == V_domain_1d.bounds)

    # 2D Cuboid
    domain_2d = Cuboid([(0, 1), (-1, 2)], is_main_domain=True)
    mesh_2d = domain_2d.uniform_mesh(n**2)
    assert mesh_2d.shape == (n**2, 2)

    V_domain_2d = domain_2d.to_volumetric_domain()
    assert isinstance(V_domain_2d, Square2D)
    assert torch.all(domain_2d.bounds == V_domain_2d.bounds)

    # 2D Cuboid
    domain_2d = Cuboid([(0, 1), (-1, 2)], is_main_domain=True)
    mesh_2d = domain_2d.uniform_mesh((n, n_2))
    assert mesh_2d.shape == (n * n_2, 2)

    # 3D Cuboid
    domain_3d = Cuboid([(0, 1), (-1, 2), (-10, 10)], is_main_domain=True)
    mesh_3d = domain_3d.uniform_mesh(n**3)
    assert mesh_3d.shape == (n**3, 3)

    # 3D Cuboid
    domain_3d = Cuboid([(0, 1), (-1, 2), (-10, 10)], is_main_domain=True)
    mesh_3d = domain_3d.uniform_mesh((n, n_2, n_3))
    assert mesh_3d.shape == (n * n_2 * n_3, 3)

    V_domain_3d = domain_3d.to_volumetric_domain()
    assert isinstance(V_domain_3d, Cube3D)
    assert torch.all(domain_3d.bounds == V_domain_3d.bounds)

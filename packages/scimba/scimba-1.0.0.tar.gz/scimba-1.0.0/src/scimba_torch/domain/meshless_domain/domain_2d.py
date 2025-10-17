"""Basic Volumetric and Surfacic domains in 2D."""

from typing import Callable

import torch

from ...utils import Mapping
from ..sdf import PolygonalApproxSignedDistance, SignedDistance
from .base import SurfacicDomain, VolumetricDomain
from .domain_1d import Segment1D


################## Basic Surfacic domains in 2D ##################
class Segment2D(SurfacicDomain):
    """Segment2D domain.

    Args:
        pt1: First point of the segment.
        pt2: Second point of the segment.
    """

    def __init__(
        self,
        pt1: tuple[float, float] | torch.Tensor,
        pt2: tuple[float, float] | torch.Tensor,
    ):
        self.pt1: torch.Tensor = (
            pt1
            if isinstance(pt1, torch.Tensor)
            else torch.tensor(pt1, dtype=torch.get_default_dtype())
        )
        self.pt2: torch.Tensor = (
            pt2
            if isinstance(pt2, torch.Tensor)
            else torch.tensor(pt2, dtype=torch.get_default_dtype())
        )
        assert self.pt1.shape == (2,), "pt1 must be a tensor of shape (2,)"
        assert self.pt2.shape == (2,), "pt2 must be a tensor of shape (2,)"

        super().__init__(
            domain_type="Segment2D",
            parametric_domain=Segment1D(low_high=(0.0, 1.0)),
            surface=Mapping.segment(self.pt1, self.pt2),
        )

    def get_sdf(self) -> Callable[[torch.Tensor], torch.Tensor]:
        """Get the signed distance function of the segment.

        Returns:
            The signed distance function of the segment.
        """
        pc = (self.pt1 + self.pt2) / 2
        pt1_to_pt2 = self.pt2 - self.pt1
        L = torch.linalg.vector_norm(pt1_to_pt2)

        def func_f(x: torch.Tensor) -> torch.Tensor:
            x = x - self.pt1
            return (x[:, 0] * pt1_to_pt2[1] - x[:, 1] * pt1_to_pt2[0]) / L

        def func_t(x: torch.Tensor) -> torch.Tensor:
            return L / 4 - torch.sum((x - pc) ** 2, dim=-1) / L

        def phi(x: torch.Tensor) -> torch.Tensor:
            """Signed distance function of the segment.

            Args:
                x: Tensor of shape (N, 2) representing the points at which to evaluate
                    the SDF.

            Returns:
                Tensor of shape (N,) representing the signed distance to the segment.
            """
            f = func_f(x)
            t = func_t(x)
            phi_var = torch.sqrt(f**4 + t**2)
            return torch.sqrt(f**2 + (phi_var - t) ** 2 / 4)[:, None]

        return phi


class Circle2D(SurfacicDomain):
    """Circle2D domain.

    Args:
        center: Center of the circle.
        radius: Radius of the circle.
    """

    def __init__(
        self,
        center: tuple[float, float] | torch.Tensor,
        radius: float,
    ):
        t_center: torch.Tensor = (
            center
            if isinstance(center, torch.Tensor)
            else torch.tensor(center, dtype=torch.get_default_dtype())
        )
        assert t_center.shape == (2,), "center must be a tensor of shape (2,)"

        super().__init__(
            domain_type="Circle2D",
            parametric_domain=Segment1D(low_high=(0.0, 2 * torch.pi)),
            surface=Mapping.circle(t_center, radius),
        )
        self.center: torch.Tensor = t_center
        self.radius: float = radius

    def get_sdf(self) -> Callable[[torch.Tensor], torch.Tensor]:
        """Get the signed distance function of the circle.

        Returns:
            The signed distance function of the circle.
        """

        def phi(x: torch.Tensor) -> torch.Tensor:
            """Signed distance function of the circle.

            Args:
                x: Tensor of shape (N, 2) representing the points at which to evaluate
                    the SDF

            Returns:
                Tensor of shape (N, 1) representing the signed distance of the circle
            """
            return (
                (torch.sum((x - self.center) ** 2, dim=-1) - self.radius**2)
                / (2 * self.radius)
            )[:, None]

        return phi


class ArcCircle2D(SurfacicDomain):
    """ArcCircle2D domain.

    Args:
        center: Center of the circle.
        radius: Radius of the circle.
        theta1: Start angle of the arc in radians.
        theta2: End angle of the arc in radians.
    """

    def __init__(
        self,
        center: tuple[float, float] | torch.Tensor,
        radius: float,
        theta1: float,
        theta2: float,
    ):
        t_center: torch.Tensor = (
            center
            if isinstance(center, torch.Tensor)
            else torch.tensor(center, dtype=torch.get_default_dtype())
        )
        assert t_center.shape == (2,), "center must be a tensor of shape (2,)"

        super().__init__(
            domain_type="ArcCircle2D",
            parametric_domain=Segment1D(low_high=(theta1, theta2)),
            surface=Mapping.circle(t_center, radius),
        )
        self.center: torch.Tensor = t_center
        self.radius: float = radius
        self.theta1: float = theta1
        self.theta2: float = theta2

    def get_sdf(self):
        """Get the signed distance function of the arc.

        Returns:
            The signed distance function of the arc.
        """

        # they don't give the formula explicitly in the paper, i think this is the one.
        # TODO : check if it's a normalized sdf, i.e. \partial \phi / \partial \nu = 1
        # where \nu is the outward normal
        def func_f(x: torch.Tensor) -> torch.Tensor:
            return (self.radius**2 - torch.sum((x - self.center) ** 2, dim=-1)) / (
                2 * self.radius
            )

        pt1 = self.center + self.radius * torch.tensor(
            [torch.cos(self.theta1), torch.sin(self.theta1)]
        )
        pt2 = self.center + self.radius * torch.tensor(
            [torch.cos(self.theta2), torch.sin(self.theta2)]
        )
        pt1_to_pt2 = pt2 - pt1
        L = torch.linalg.vector_norm(pt1_to_pt2)

        def func_t(x: torch.Tensor) -> torch.Tensor:
            x = x - pt1
            return (x[:, 0] * pt1_to_pt2[1] - x[:, 1] * pt1_to_pt2[0]) / L

        def phi(x: torch.Tensor) -> torch.Tensor:
            """Signed distance function of the arc of the circle.

            Args:
                x: Tensor of shape (N, 2) representing the points at which to evaluate
                    the SDF

            Returns:
                Tensor of shape (N, 1) representing the signed distance of the arc
            """
            f = func_f(x)
            t = func_t(x)
            phi_var = torch.sqrt(f**4 + t**2)
            return torch.sqrt(f**2 + (phi_var - t) ** 2 / 4)[:, None]

        return phi


################## Basic Volumetric domains in 2D ##################
class Square2D(VolumetricDomain):
    """Square2D domain.

    Args:
        bounds: Bounds of the square in the form [(min_x, max_x), (min_y, max_y)].
        is_main_domain: Whether this domain is the main domain.

    Raises:
        ValueError: If bounds is not of shape (2, 2).
    """

    def __init__(
        self,
        bounds: list[tuple[float, float]],
        is_main_domain: bool = False,
    ):
        t_bounds: torch.Tensor = (
            bounds
            if isinstance(bounds, torch.Tensor)
            else torch.tensor(bounds, dtype=torch.get_default_dtype())
        )
        assert t_bounds.shape == (2, 2), "bounds must be a tensor of shape (2, 2)"

        if t_bounds.shape != (2, 2):
            raise ValueError("bounds must be a tensor of shape (2, 2)")

        class SquareSDF(SignedDistance):
            def __init__(self, tensor_bounds):
                super().__init__(2, threshold=0)
                self.mid_pt = torch.mean(tensor_bounds, dim=1)
                self.half_len = (tensor_bounds[:, 1] - tensor_bounds[:, 0]) / 2

            def __call__(self, x):
                x = x - self.mid_pt
                dist_dir = torch.abs(x) - self.half_len
                return (
                    torch.norm(torch.clamp(dist_dir, min=0), dim=1)
                    + torch.min(dist_dir.max(dim=1).values, torch.tensor(0.0))
                )[:, None]

        super().__init__(
            domain_type="Square2D",
            dim=2,
            sdf=SquareSDF(t_bounds),
            bounds=t_bounds,
            is_main_domain=is_main_domain,
        )

    def full_bc_domain(self) -> list[Segment2D]:
        """Return the full boundary domain of the Square2D.

        Returns:
            A list containing the four boundary Segment2D domains.
        """
        vertices = torch.tensor(
            [
                [self.bounds[0, 0], self.bounds[1, 0]],
                [self.bounds[0, 1], self.bounds[1, 0]],
                [self.bounds[0, 1], self.bounds[1, 1]],
                [self.bounds[0, 0], self.bounds[1, 1]],
            ]
        )
        res = [
            Segment2D(vertices[0], vertices[1]),
            Segment2D(vertices[1], vertices[2]),
            Segment2D(vertices[2], vertices[3]),
            Segment2D(vertices[3], vertices[0]),
        ]
        if self.is_mapped:
            for r in res:
                r._set_mapping(self.mapping)
        return res


class Polygon2D(VolumetricDomain):
    """Polygon2D domain.

    The vertices must be given in counter-clockwise order.

    Args:
        vertices: Vertices of the polygon.
        threshold: Threshold for the polygonal approximation.
        is_main_domain: Whether this domain is the main domain.
    """

    def __init__(
        self,
        vertices: list[tuple[float, float]],
        threshold: float = 0.01,
        is_main_domain: bool = False,
    ):
        tensor_vertices: torch.Tensor = (
            vertices
            if isinstance(vertices, torch.Tensor)
            else torch.tensor(vertices, dtype=torch.get_default_dtype())
        )

        assert tensor_vertices.shape[1] == 2, "vertices must be a list of 2D points"
        assert tensor_vertices.ndim == 2, "vertices must be a list of 2D points"
        assert tensor_vertices.shape[0] >= 3, "a polygon must have at least 3 vertices"

        minx = torch.min(tensor_vertices[:, 0])
        miny = torch.min(tensor_vertices[:, 1])
        maxx = torch.max(tensor_vertices[:, 0])
        maxy = torch.max(tensor_vertices[:, 1])

        super().__init__(
            domain_type="Polygon2D",
            dim=2,
            sdf=PolygonalApproxSignedDistance(2, vertices, threshold=threshold),
            bounds=[(minx, maxx), (miny, maxy)],
            is_main_domain=is_main_domain,
        )
        self.vertices = tensor_vertices

    def full_bc_domain(self) -> list[SurfacicDomain]:
        """Return the full boundary domain of the Polygon2D.

        Returns:
            A list containing the boundary Segment2D domains.
        """
        res = []
        for v1, v2 in zip(self.vertices, torch.roll(self.vertices, shifts=-1, dims=0)):
            res.append(Segment2D(v1, v2))

        if self.is_mapped:
            for r in res:
                r._set_mapping(self.mapping)

        return res


class Disk2D(VolumetricDomain):
    """Disk2D domain.

    Args:
        center: Center of the disk.
        radius: Radius of the disk.
        is_main_domain: Whether this domain is the main domain.
    """

    def __init__(
        self,
        center: torch.Tensor,
        radius: float,
        is_main_domain: bool = False,
    ):
        t_center = (
            center
            if isinstance(center, torch.Tensor)
            else torch.tensor(center, dtype=torch.get_default_dtype())
        )
        assert t_center.shape == (2,), "center must be a tensor of shape (2,)"

        class DiskSDF(SignedDistance):
            def __init__(self, center: torch.Tensor, radius: float):
                super().__init__(2, threshold=0)
                self.center = center
                self.radius = radius

            def __call__(self, x):
                return (torch.norm(x - self.center, dim=1) - self.radius)[:, None]

        super().__init__(
            domain_type="Disk2D",
            dim=2,
            sdf=DiskSDF(t_center, radius),
            bounds=[
                (t_center[0] - radius, t_center[0] + radius),
                (t_center[1] - radius, t_center[1] + radius),
            ],
            is_main_domain=is_main_domain,
        )
        self.center = t_center
        self.radius = radius

    def full_bc_domain(self) -> list[SurfacicDomain]:
        """Return the full boundary domain of the Disk2D.

        Returns:
            A list containing the boundary Circle2D domain.
        """
        res = Circle2D(self.center, self.radius)
        if self.is_mapped:
            res._set_mapping(self.mapping)
        return [res]

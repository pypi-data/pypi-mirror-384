"""Basic Volumetric and Surfacic domains in 3D."""

from typing import Callable

import torch

from scimba_torch.domain.meshless_domain.base import SurfacicDomain, VolumetricDomain
from scimba_torch.domain.meshless_domain.domain_1d import Segment1D
from scimba_torch.domain.meshless_domain.domain_2d import Square2D
from scimba_torch.domain.meshless_domain.domain_nd import CartesianProduct
from scimba_torch.domain.sdf import SignedDistance
from scimba_torch.utils import Mapping


################## Basic Volumetric domains in 3D ##################
class Cube3D(VolumetricDomain):
    """Cube3D domain.

    Args:
        bounds: Bounds of the cube in the form
            [(min_x, max_x), (min_y, max_y), (min_z, max_z)]
        is_main_domain: Whether this domain is the main domain.
    """

    def __init__(
        self,
        bounds: list[tuple[float, float]] | torch.Tensor,
        is_main_domain: bool = False,
    ):
        t_bounds = (
            bounds
            if isinstance(bounds, torch.Tensor)
            else torch.tensor(bounds, dtype=torch.get_default_dtype())
        )
        assert t_bounds.shape == (3, 2), "bounds must be a tensor of shape (3, 2)"

        class CubeSDF(SignedDistance):
            def __init__(self, bounds: torch.Tensor):
                super().__init__(3, threshold=0)
                self.mid_pt = torch.mean(bounds, dim=1)
                self.half_len = (bounds[:, 1] - bounds[:, 0]) / 2

            def __call__(self, x: torch.Tensor) -> torch.Tensor:
                x = x - self.mid_pt
                dist_dir = torch.abs(x) - self.half_len
                return (
                    torch.norm(torch.clamp(dist_dir, min=0), dim=1)
                    + torch.min(dist_dir.max(dim=1).values, torch.tensor(0.0))
                )[:, None]

        super().__init__(
            domain_type="Cube3D",
            dim=3,
            sdf=CubeSDF(t_bounds),
            bounds=t_bounds,
            is_main_domain=is_main_domain,
        )

    def full_bc_domain(self) -> list[SurfacicDomain]:
        """Return the full boundary domain of the Cube3D.

        Returns:
            A list containing the six boundary Square3D domains:
                (bottom, front, left, top, back, right).
        """
        # here self.bounds is the attribute of the super class VolumetricDomain
        x_len = torch.tensor(
            [self.bounds[0, 1] - self.bounds[0, 0], 0, 0],
            dtype=torch.get_default_dtype(),
        )
        y_len = torch.tensor(
            [0, self.bounds[1, 1] - self.bounds[1, 0], 0],
            dtype=torch.get_default_dtype(),
        )
        z_len = torch.tensor(
            [0, 0, self.bounds[2, 1] - self.bounds[2, 0]],
            dtype=torch.get_default_dtype(),
        )

        res: list[SurfacicDomain] = [
            Square3D(self.bounds[:, 0], y_len, x_len),  # bottom
            Square3D(self.bounds[:, 0], x_len, z_len),  # front
            Square3D(self.bounds[:, 0], z_len, y_len),  # left
            Square3D(self.bounds[:, 1], -x_len, -y_len),  # top
            Square3D(self.bounds[:, 1], -z_len, -x_len),  # back
            Square3D(self.bounds[:, 1], -y_len, -z_len),  # right
        ]
        if self.is_mapped:
            for r in res:
                r._set_mapping(self.mapping)
        return res


class Disk3D(VolumetricDomain):
    """Disk3D domain.

    Args:
        center: Center of the disk.
        radius: Radius of the disk.
        is_main_domain: Whether this domain is the main domain.
    """

    def __init__(
        self,
        center: tuple[float, float, float] | torch.Tensor,
        radius: float,
        is_main_domain: bool = False,
    ):
        t_center = (
            center
            if isinstance(center, torch.Tensor)
            else torch.tensor(center, dtype=torch.get_default_dtype())
        )
        assert t_center.shape == (3,), "center must be a tensor of shape (3,)"

        class SphereSDF(SignedDistance):
            def __init__(self, center: torch.Tensor, radius: float):
                super().__init__(3, threshold=0)
                self.center = center
                self.radius = radius

            def __call__(self, x: torch.Tensor) -> torch.Tensor:
                return (torch.norm(x - self.center, dim=1) - self.radius)[:, None]

        super().__init__(
            domain_type="Sphere3D",
            dim=3,
            sdf=SphereSDF(t_center, radius),
            bounds=[
                (t_center[i].item() - radius, t_center[i].item() + radius)
                for i in range(3)
            ],
            is_main_domain=is_main_domain,
        )
        self.center = t_center
        self.radius = radius

    def full_bc_domain(self) -> list[SurfacicDomain]:
        """Return the full boundary domain of the Disk3D.

        Returns:
            A list containing the boundary Sphere3D domain.
        """
        res = Sphere3D(self.center, self.radius)
        if self.is_mapped:
            res._set_mapping(self.mapping)
        return [res]


class Cylinder3D(VolumetricDomain):
    """A Cylinder3D domain around :math:`z` axis.

    Args:
        radius: Radius of the cylinder
        length: Length of the cylinder
        is_main_domain: Whether the domain is the main domain or not
    """

    def __init__(
        self,
        radius: float,
        length: float,
        is_main_domain: bool = False,
    ):
        class CylinderSDF(SignedDistance):
            def __init__(self, radius, length):
                super().__init__(3, threshold=0)
                self.radius = radius
                self.length = length

            def __call__(self, x):
                x1, x2, x3 = x[..., 0], x[..., 1], x[..., 2]
                disk = x1**2 + x2**2 - self.radius**2
                return (disk * x3)[:, None]

        bounds_disk = [(-radius, radius)] * 2
        bounds_z = [(0.0, length)]

        super().__init__(
            domain_type="Cylinder3D",
            dim=3,
            sdf=CylinderSDF(radius, length),
            bounds=bounds_disk + bounds_z,
            is_main_domain=is_main_domain,
        )
        self.radius = radius
        self.length = length

    def full_bc_domain(self) -> list[SurfacicDomain]:
        """Return the full boundary domain of the Cylinder3D.

        Returns:
            A list containing the three boundary domains:
                (lower disk, body, upper disk).
        """
        from scimba_torch.domain.meshless_domain.domain_2d import Disk2D

        disk2d = Disk2D(
            center=torch.tensor([0.0, 0.0], dtype=torch.get_default_dtype()),
            radius=self.radius,
        )

        map2d_to_3d = Mapping(
            2,
            3,
            map=lambda x: torch.cat((x, torch.zeros_like(x[..., :1])), dim=-1),
            jac=lambda x: torch.broadcast_to(
                torch.tensor([[1, 0], [0, 1], [0, 0]], dtype=torch.get_default_dtype()),
                (x.shape[0], 3, 2),
            ),
        )

        lower_disk = SurfacicDomain(
            domain_type="LowerDisk2D",
            parametric_domain=disk2d,
            surface=Mapping.compose(
                map2d_to_3d,
                Mapping.rot_3d(
                    axis=torch.tensor([1.0, 0.0, 0.0], dtype=torch.get_default_dtype()),
                    angle=torch.tensor(torch.pi, dtype=torch.get_default_dtype()),
                ),
            ),
        )
        upper_disk = SurfacicDomain(
            domain_type="UpperDisk2D",
            parametric_domain=disk2d,
            surface=Mapping.compose(
                map2d_to_3d,
                Mapping.translate(
                    torch.tensor(
                        [0.0, 0.0, self.length], dtype=torch.get_default_dtype()
                    )
                ),
            ),
        )

        map_body = Mapping(
            2,
            3,
            map=lambda x: torch.stack(
                (
                    self.radius * torch.cos(x[..., 0]),
                    self.radius * torch.sin(x[..., 0]),
                    x[..., 1],
                ),
                dim=-1,
            ),
            jac=lambda x: torch.stack(
                [
                    torch.stack(
                        [
                            -self.radius * torch.sin(x[..., 0]),
                            torch.zeros_like(x[..., 0]),
                        ],
                        dim=-1,
                    ),
                    torch.stack(
                        [
                            self.radius * torch.cos(x[..., 0]),
                            torch.zeros_like(x[..., 0]),
                        ],
                        dim=-1,
                    ),
                    torch.stack(
                        [torch.zeros_like(x[..., 0]), torch.ones_like(x[..., 0])],
                        dim=-1,
                    ),
                ],
                dim=-2,
            ),
        )

        body = SurfacicDomain(
            domain_type="BodyCylinder3D",
            parametric_domain=Square2D([(0.0, 2 * torch.pi), (0.0, self.length)]),
            surface=map_body,
        )

        if self.is_mapped:
            lower_disk._set_mapping(self.mapping)
            body._set_mapping(self.mapping)
            upper_disk._set_mapping(self.mapping)
        return [lower_disk, body, upper_disk]


class Torus3D(VolumetricDomain):
    """Torus3D domain around :math: `z` axis.

    Args:
        radius: Radius of the torus (distance from the center to the center of the tube
        tube_radius: Radius of the tube.
        center: Center of the torus.
        is_main_domain: Whether the domain is the main domain or not
    """

    def __init__(
        self,
        radius: float,
        tube_radius: float,
        center: torch.Tensor | tuple[float, float, float] = (0, 0, 0),
        is_main_domain: bool = True,
    ):
        center = torch.as_tensor(center, dtype=torch.get_default_dtype())
        assert center.shape == (3,), "center must be a tensor of shape (3,)"
        assert radius > 0, "radius must be positive"
        assert tube_radius > 0, "tube_radius must be positive"

        self.center = center
        self.radius = radius
        self.tube_radius = tube_radius

        class TorusSDF(SignedDistance):
            def __init__(sdf):  # noqa: N805
                super(TorusSDF, sdf).__init__(3, threshold=0)

            def __call__(sdf, x):  # noqa: N805
                x = x - self.center
                x, y, z = x[..., 0], x[..., 1], x[..., 2]
                return (
                    (torch.sqrt(x**2 + y**2) - self.radius) ** 2
                    + z**2
                    - self.tube_radius**2
                )[:, None]

        super(Torus3D, self).__init__(
            domain_type="Torus3D",
            dim=3,
            sdf=TorusSDF(),
            bounds=[
                (center[i] - radius - tube_radius, center[i] + radius + tube_radius)
                for i in range(2)
            ]
            + [(center[2] - tube_radius, center[2] + tube_radius)],
            is_main_domain=is_main_domain,
        )

    def full_bc_domain(self) -> list[SurfacicDomain]:
        """Returns the boundary condition domain of the torus.

        Returns:
            A list with a single SurfaceTorus3D domain.
        """
        res = SurfaceTorus3D(self.radius, self.tube_radius, self.center)
        if self.is_mapped:
            res._set_mapping(self.mapping)
        return [res]


class TorusFrom2DVolume(VolumetricDomain):
    """Torus from 2D volume domain.

    Creates a Torus by revolving a 2D VolumetricDomain around the :math:`z` axis.

    Args:
        base_volume: A 2D VolumetricDomain to be revolved around the :math:`z` axis.
        radius: Radius of the torus.
        is_main_domain: Whether this domain is the main domain.

    Raises:
        TypeError: If base_volume is not a VolumetricDomain instance.
        ValueError: If base_volume is not a 2D domain.
            If base_volume does not have an invertible mapping.

    """

    def _map_to_base_volume(self, x):
        x, y, z = x[..., 0], x[..., 1], x[..., 2]
        r = torch.sqrt(x**2 + y**2 + z**2)
        phi = torch.pi / 2 - torch.arccos(z / r)  # angle from (x,y) plane

        XY = torch.stack(
            (
                r * torch.cos(phi) - self.radius,
                r * torch.sin(phi),
            ),
            dim=-1,
        )
        if self.base_volume.is_mapped:
            XY = self.base_volume.mapping.inv(XY)

        return XY

    def __init__(
        self,
        base_volume: VolumetricDomain,
        radius: float,
        is_main_domain: bool = True,
    ):
        if not isinstance(base_volume, VolumetricDomain):
            raise TypeError("base_volume must be a VolumetricDomain instance")
        if base_volume.dim != 2:
            raise ValueError("base_volume must be a 2D domain")

        self.base_volume = base_volume
        self.radius = radius

        class TorusFrom2DVolumeSDF(SignedDistance):
            def __init__(sdf):  # noqa: N805
                super(TorusFrom2DVolumeSDF, sdf).__init__(3, threshold=0)

            def __call__(sdf, x):  # noqa: N805
                return self.base_volume.sdf(self._map_to_base_volume(x))

        if base_volume.is_mapped:
            if not base_volume.mapping.is_invertible:
                msg = "base_volume must have an invertible mapping"
                raise ValueError(msg)
            base_bounds = base_volume.bounds_postmap
        else:
            base_bounds = base_volume.bounds
        super(TorusFrom2DVolume, self).__init__(
            domain_type="Torus_from2DVolume",
            dim=3,
            sdf=TorusFrom2DVolumeSDF(),
            bounds=[
                (-base_bounds[0, 1] - self.radius, base_bounds[0, 1] + self.radius),
                (-base_bounds[0, 1] - self.radius, base_bounds[0, 1] + self.radius),
                (base_bounds[1, 0], base_bounds[1, 1]),
            ],
            is_main_domain=is_main_domain,
        )
        # print(f"Torus_from2DVolume created with bounds: {self.bounds}")

    def is_inside(self, x: torch.Tensor) -> torch.Tensor:  # noqa: D102
        return self.base_volume.is_inside(self._map_to_base_volume(x))

    def is_outside(self, x):  # noqa: D102
        return self.base_volume.is_outside(self._map_to_base_volume(x))

    def is_on_boundary(self, x, tol=1e-4):  # noqa: D102
        return self.base_volume.is_on_boundary(self._map_to_base_volume(x), tol=tol)

    def full_bc_domain(self) -> list[SurfacicDomain]:
        """Return the full boundary domain of the Torus_from2DVolume.

        Returns:
            A list with a SurfaceTorus_from2DSurface domain for each boundary
            of the base_volume.
        """
        return [
            SurfaceTorusFrom2DSurface(self.radius, surface)
            for surface in self.base_volume.full_bc_domain()
        ]

    # TODO check if their is other function to override
    # it might be better to build it with a CartesianProduct that's always mapped ?


################## Basic Surfacic domains in 3D ##################
class SurfaceTorus3D(SurfacicDomain):
    """SurfaceTorus3D domain around :math: `z` axis.

    Args:
        radius: Radius of the torus
            (distance from the center to the center of the tube).
        tube_radius: Radius of the tube.
        center: Center of the torus.

    """

    def __init__(
        self,
        radius: float,
        tube_radius: float,
        center: torch.Tensor = (0, 0, 0),
    ):
        center = torch.as_tensor(center, dtype=torch.get_default_dtype())
        self.center = center
        self.radius = radius
        self.tube_radius = tube_radius

        super(SurfaceTorus3D, self).__init__(
            domain_type="SurfaceTorus3D",
            parametric_domain=Square2D([(0.0, 2 * torch.pi), (0.0, 2 * torch.pi)]),
            surface=Mapping.surface_torus_3d(radius, tube_radius, center),
        )


class SurfaceTorusFrom2DSurface(SurfacicDomain):
    """Surface Torus from 2D surface domain.

    Creates a Torus Surface by revolving a 2D SurfacicDomain around the :math:`z` axis.

    Args:
        radius: Radius of the torus.
        base_surface: A 2D SurfacicDomain to be revolved around the :math:`z` axis.

    Raises:
        TypeError: If base_surface is not a SurfacicDomain instance.
        ValueError: If base_surface is not a 2D domain.
    """

    def __init__(
        self,
        radius: float,
        base_surface: SurfacicDomain,
    ):
        if not isinstance(base_surface, SurfacicDomain):
            raise TypeError("base_volume must be a SurfacicDomain instance")
        if base_surface.dim != 2:
            raise ValueError("base_volume must be a 2D domain")
        self.radius = radius
        self.base_surface = base_surface

        parametric_domain = CartesianProduct(
            [base_surface.parametric_domain, Segment1D((0, 2 * torch.pi))]
        )

        def map(x):
            res_base = self.base_surface.surface_o_mapping(x[..., 0].unsqueeze(-1))
            res = torch.stack(
                [
                    res_base[..., 0] + self.radius,
                    torch.zeros_like(res_base[..., 0]),
                    res_base[..., 1],
                ],
                dim=-1,
            )

            rot_mat = torch.stack(
                [
                    torch.stack(
                        [
                            torch.cos(x[..., 1]),
                            -torch.sin(x[..., 1]),
                            torch.zeros_like(x[..., 1]),
                        ],
                        dim=-1,
                    ),
                    torch.stack(
                        [
                            torch.sin(x[..., 1]),
                            torch.cos(x[..., 1]),
                            torch.zeros_like(x[..., 1]),
                        ],
                        dim=-1,
                    ),
                    torch.stack(
                        [
                            torch.zeros_like(x[..., 1]),
                            torch.zeros_like(x[..., 1]),
                            torch.ones_like(x[..., 1]),
                        ],
                        dim=-1,
                    ),
                ],
                dim=-2,
            )
            res_rot = torch.einsum("bij,bi->bj", rot_mat, res)
            return res_rot

        surface_map = Mapping(2, 3, map)

        super(SurfaceTorusFrom2DSurface, self).__init__(
            f"SurfaceTorus_from_{base_surface.domain_type}",
            parametric_domain=parametric_domain,
            surface=surface_map,
        )


class Sphere3D(SurfacicDomain):
    """3D sphere domain.

    Args:
        center: Center of the sphere.
        radius: Radius of the sphere.
    """

    def __init__(
        self,
        center: tuple[float, float, float] | torch.Tensor,
        radius: float,
    ):
        t_center = (
            center
            if isinstance(center, torch.Tensor)
            else torch.tensor(center, dtype=torch.get_default_dtype())
        )
        assert t_center.shape == (3,), "center must be a tensor of shape (3,)"

        super().__init__(
            domain_type="Sphere3D",
            parametric_domain=Square2D([(0.0, 1.0), (0.0, 2 * torch.pi)]),
            surface=Mapping.sphere(t_center, radius),
        )
        self.center = t_center
        self.radius = radius

    def get_sdf(self) -> Callable[[torch.Tensor], torch.Tensor]:
        """Returns the signed distance function (SDF) for the sphere.

        Returns:
            A function that computes the signed distance from the sphere surface.
        """

        def phi(x: torch.Tensor) -> torch.Tensor:
            """Signed distance function for a sphere.

            Args:
                x: Tensor of shape (N, 3) representing the points at which to evaluate
                    the SDF

            Returns:
                Tensor of shape (N, 1) representing the signed distance of the sphere
            """
            return (
                (torch.sum((x - self.center) ** 2, dim=-1) - self.radius**2)
                / (2 * self.radius)
            )[:, None]

        return phi


class Square3D(SurfacicDomain):
    """Square3D domain.

    Args:
        origin: Vector defining the origin of the square
        x_dir: Vector defining the x direction
        y_dir: Vector defining the y direction
    """

    def __init__(
        self,
        origin: tuple[float, float, float] | torch.Tensor,
        x_dir: tuple[float, float, float] | torch.Tensor,
        y_dir: tuple[float, float, float] | torch.Tensor,
    ):
        self.origin = (
            origin
            if isinstance(origin, torch.Tensor)
            else torch.tensor(origin, dtype=torch.get_default_dtype())
        )
        assert self.origin.shape == (3,), "origin must be a tensor of shape (3,)"

        self.x_dir = (
            x_dir
            if isinstance(x_dir, torch.Tensor)
            else torch.tensor(x_dir, dtype=torch.get_default_dtype())
        )
        assert self.x_dir.shape == (3,), "x_dir must be a tensor of shape (3,)"

        self.y_dir = (
            y_dir
            if isinstance(y_dir, torch.Tensor)
            else torch.tensor(y_dir, dtype=torch.get_default_dtype())
        )
        assert self.y_dir.shape == (3,), "y_dir must be a tensor of shape (3,)"

        super().__init__(
            domain_type="Square3D",
            parametric_domain=Square2D([(0.0, 1.0), (0.0, 1.0)]),
            surface=Mapping.square(self.origin, self.x_dir, self.y_dir),
        )

    # TODO :
    # def get_sdf(self):
    #     pass

"""Define and compose mappings between spaces."""

from __future__ import annotations

import torch

from scimba_torch.utils.typing_protocols import FUNC_TYPE


class Mapping:
    """A class to represent a mapping between two spaces.

    Args:
        from_dim: The dimension of the input space.
        to_dim: The dimension of the output space.
        map: The mapping function.
        jac: The Jacobian of the mapping (optional, default=None).
        inv: The inverse of the mapping (optional, default=None).
        jac_inv: The Jacobian of the inverse of the mapping
            (optional, default=None).

    .. note::

        The map/inv/jac/jac_inv functions must accept batched inputs,
        i.e. Tensor of shape (batch_size, from_dim/to_dim). If you don't
        want to write a version of the function, you can use
        torch.func.vmap to vectorize it.
    """

    def __init__(
        self,
        from_dim: int,
        to_dim: int,
        map: FUNC_TYPE,
        jac: FUNC_TYPE | None = None,
        inv: FUNC_TYPE | None = None,
        jac_inv: FUNC_TYPE | None = None,
    ):
        self.from_dim = from_dim  #: The dimension of the input space
        self.to_dim = to_dim  #: The dimension of the output space
        self.is_invertible = (
            inv is not None
        )  #: A flag to indicate if the mapping is invertible

        self.map: FUNC_TYPE = map  #: The mapping function

        #: The Jacobian of the mapping
        self.jac: FUNC_TYPE
        if jac is None:
            # map_ takes (from_dim,) shape and returns (to_dim,) shape
            # map_ = lambda x, **kwargs: self.map(x[None, :], **kwargs)[0]

            def map_(x, **kwargs):
                return self.map(x[None, :], **kwargs)[0]

            self.jac = torch.func.vmap(torch.func.jacrev(map_))
        else:
            self.jac = jac

        #: The inverse of the mapping (ONLY IF is_invertible=True)
        self.inv: FUNC_TYPE = Mapping._dummy_error
        #: The Jacobian of the inverse of the mapping (ONLY IF is_invertible=True)
        self.jac_inv: FUNC_TYPE = Mapping._dummy_error
        if self.is_invertible:
            assert inv is not None
            self.inv = inv

            if jac_inv is None:

                def inv_map_(x, **kwargs):
                    return self.inv(x[None, :], **kwargs)[0]

                self.jac_inv = torch.func.vmap(torch.func.jacrev(inv_map_))
            else:
                self.jac_inv = jac_inv

    def __call__(self, x: torch.Tensor, **kwargs) -> torch.Tensor:
        """To make an object mapping callable.

        So that we don't have to make `map_obj.map(x)` but `map_obj(x)`.

        Args:
            x: The input tensor of shape (batch_size, from_dim).
            **kwargs: Additional arguments to pass to the mapping function.

        Returns:
            The output tensor of shape (batch_size, to_dim).
        """
        return self.map(x, **kwargs)

    @staticmethod
    def _dummy_error(x: torch.Tensor, **kwargs) -> torch.Tensor:
        raise ValueError("The mapping is not invertible")

    @staticmethod
    def compose(map1: Mapping, map2: Mapping) -> Mapping:
        r"""Compose two mappings.

        Args:
            map1: The first mapping.
            map2: The second mapping.

        Returns:
            The composed mapping :math: `map2 \circ map1`
                (invertible if both map1 and map2 are invertible).

        Raises:
            ValueError: If the dimensions of the mappings are not compatible.
        """
        if not map1.to_dim == map2.from_dim:
            raise ValueError(
                f"map1.to_dim = {map1.to_dim} != ({map2.from_dim}) = map2.from_dim"
            )

        def map(x: torch.Tensor, **kwargs) -> torch.Tensor:
            kwargs1 = {
                k: v for k, v in kwargs.items() if k in map1.map.__code__.co_varnames
            }
            kwargs2 = {
                k: v for k, v in kwargs.items() if k in map2.map.__code__.co_varnames
            }

            return map2(map1(x, **kwargs1), **kwargs2)

        def jac(x: torch.Tensor, **kwargs) -> torch.Tensor:
            kwargs1 = {
                k: v for k, v in kwargs.items() if k in map1.map.__code__.co_varnames
            }
            kwargs2 = {
                k: v for k, v in kwargs.items() if k in map2.map.__code__.co_varnames
            }

            return torch.bmm(
                map2.jac(map1(x, **kwargs1), **kwargs2),
                map1.jac(x, **kwargs1),
            )

        if map1.is_invertible and map2.is_invertible:

            def inv(x: torch.Tensor, **kwargs) -> torch.Tensor:
                kwargs1 = {
                    k: v
                    for k, v in kwargs.items()
                    if k in map1.map.__code__.co_varnames
                }
                kwargs2 = {
                    k: v
                    for k, v in kwargs.items()
                    if k in map2.map.__code__.co_varnames
                }

                return map1.inv(map2.inv(x, **kwargs2), **kwargs1)

            def jac_inv(x: torch.Tensor, **kwargs) -> torch.Tensor:
                kwargs1 = {
                    k: v
                    for k, v in kwargs.items()
                    if k in map1.map.__code__.co_varnames
                }
                kwargs2 = {
                    k: v
                    for k, v in kwargs.items()
                    if k in map2.map.__code__.co_varnames
                }

                return torch.bmm(
                    map1.jac_inv(map2.inv(x, **kwargs2), **kwargs1),
                    map2.jac_inv(x, **kwargs2),
                )

            return Mapping(map1.from_dim, map2.to_dim, map, jac, inv, jac_inv)

        else:
            return Mapping(map1.from_dim, map2.to_dim, map, jac)

    @staticmethod
    def invert(map: Mapping) -> Mapping:
        r"""Invert a mapping.

        From :math:`f: \mathbb{R}^n \to \mathbb{R}^m` get :math:`f^{-1}: \mathbb{R}^m
        \to \mathbb{R}^n`.

        Args:
            map: The mapping to invert.

        Returns:
            The inverse mapping.

        Raises:
            ValueError: If the mapping is not invertible.
        """
        if not map.is_invertible:
            raise ValueError("Trying to invert a not invertible mapping")

        return Mapping(map.to_dim, map.from_dim, map.inv, map.jac_inv, map.map, map.jac)

    ##################### Some Basic Examples of mappings #####################
    @staticmethod
    def identity(dim: int) -> Mapping:
        """Identity mapping in dimension dim.

        Args:
            dim: The dimension of the identity mapping.

        Returns:
            The identity mapping.
        """

        def map(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return x

        def jac(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return torch.eye(dim, dtype=torch.get_default_dtype()).broadcast_to(
                x.shape[0], dim, dim
            )

        def inv(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return x

        def jac_inv(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return torch.eye(dim, dtype=torch.get_default_dtype()).broadcast_to(
                x.shape[0], dim, dim
            )

        return Mapping(
            dim,
            dim,
            map,
            jac,
            inv,
            jac_inv,
        )

    @staticmethod
    def inv_identity(dim: int) -> Mapping:
        r"""Inverse identity mapping in dimension dim.

        :math:`f: \mathbb{R}^n \to \mathbb{R}^n` defined by :math:`f(x) = -x`.

        Args:
            dim: The dimension of the inverse identity mapping.

        Returns:
            The inverse identity mapping.
        """

        def map(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return -x

        def jac(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return -torch.eye(dim, dtype=torch.get_default_dtype()).broadcast_to(
                x.shape[0], dim, dim
            )

        def inv(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return -x

        def jac_inv(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return -torch.eye(dim, dtype=torch.get_default_dtype()).broadcast_to(
                x.shape[0], dim, dim
            )

        return Mapping(
            dim,
            dim,
            map,
            jac,
            inv,
            jac_inv,
        )

    @staticmethod
    def circle(center: torch.Tensor, radius: float) -> Mapping:
        r"""Mapping from :math:`(0, 2\pi)` to the circle.

        Args:
            center: The center of the circle.
            radius: The radius of the circle.

        Returns:
            The mapping of the circle (non-invertible).
        """
        # TODO add a return for the parametric space (input, a segment \sub R^1)
        center = center.flatten()
        assert center.shape == (2,), f"center.shape = {center.shape} != (2,)"

        def map(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return center + torch.cat([torch.cos(x), torch.sin(x)], dim=-1) * radius

        def jac(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return torch.stack([-torch.sin(x), torch.cos(x)], dim=-2) * radius

        return Mapping(1, 2, map, jac, None, None)

    @staticmethod
    def sphere(center: torch.Tensor, radius: float) -> Mapping:
        r"""Mapping from :math:`(0, 1) \times (0, 2\pi)` to the sphere.

        Args:
            center: The center of the sphere.
            radius: The radius of the sphere.

        Returns:
            The mapping of the sphere (non-invertible).
        """
        center = center.flatten()
        assert center.shape == (3,), f"center.shape = {center.shape} != (3,)"

        def map(x: torch.Tensor, **kwargs) -> torch.Tensor:
            theta = torch.acos(1 - 2 * x[..., 0])
            return (
                center
                + torch.stack(
                    [
                        torch.cos(theta),
                        torch.sin(theta) * torch.cos(x[..., 1]),
                        torch.sin(theta) * torch.sin(x[..., 1]),
                    ],
                    dim=-1,
                )
                * radius
            )

        def jac(x: torch.Tensor, **kwargs) -> torch.Tensor:
            theta = torch.acos(1 - 2 * x[..., 0])
            d_theta_dx0 = 2 / torch.sqrt(1 - (1 - 2 * x[..., 0]) ** 2)
            dt1 = torch.stack(
                [
                    -torch.sin(theta),
                    torch.cos(theta) * torch.cos(x[..., 1]),
                    torch.cos(theta) * torch.sin(x[..., 1]),
                ],
                dim=-1,
            ) * d_theta_dx0.unsqueeze(-1)

            dt2 = torch.stack(
                [
                    torch.zeros_like(theta),
                    -torch.sin(theta) * torch.sin(x[..., 1]),
                    torch.sin(theta) * torch.cos(x[..., 1]),
                ],
                dim=-1,
            )

            south = torch.isclose(theta, torch.zeros_like(theta))
            north = torch.isclose(theta, torch.full_like(theta, torch.pi))
            dt1[south] = torch.tensor([0.0, 1.0, 0.0], dtype=dt1.dtype)
            dt2[south] = torch.tensor([0.0, 0.0, 1.0], dtype=dt2.dtype)
            dt1[north] = torch.tensor([0.0, -1.0, 0.0], dtype=dt1.dtype)
            dt2[north] = torch.tensor([0.0, 0.0, 1.0], dtype=dt2.dtype)

            return radius * torch.stack(
                [dt1, dt2],
                dim=-1,
            )

        return Mapping(2, 3, map, jac, None, None)

    @staticmethod
    def segment(pt1: torch.Tensor, pt2: torch.Tensor) -> Mapping:
        r"""Maps :math:`(0, 1)` to (point1, point2).

        Args:
            pt1: The first point of the segment.
            pt2: The second point of the segment.

        Returns:
            The mapping from point1 to point2.
        """
        to_dim = pt1.shape[0]
        assert pt1.shape == pt2.shape == (to_dim,), (
            f"pt1.shape = {pt1.shape} != pt2.shape = {pt2.shape} != ({to_dim},)"
        )

        def map(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return pt1 + x * (pt2 - pt1)

        def jac(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return (pt2 - pt1)[None, :, None].broadcast_to(x.shape[0], to_dim, 1)

        # TODO: add tests for inv and jac_inv
        def inv(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return (x - pt1) / (pt2 - pt1)

        def jac_inv(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return (1 / (pt2 - pt1))[None, None, :].broadcast_to(x.shape[0], 1, to_dim)

        return Mapping(1, to_dim, map, jac, inv, jac_inv)

    @staticmethod
    def square(
        origin: torch.Tensor, x_dir: torch.Tensor, y_dir: torch.Tensor
    ) -> Mapping:
        r"""Maps :math:`(0, 1) \times (0, 1)` to the square.

        Args:
            origin: Vector defining the origin of the square.
            x_dir: Vector defining the x direction.
            y_dir: Vector defining the y direction.

        Returns:
            The mapping from :math:`(0, 1) \times (0, 1)` to the square
                (non-invertible).

        .. note::

            - The vectors x_dir and y_dir must be orthogonal.
            - Changing the roles of x_dir and y_dir will change the orientation
              of the square but not the square itself.
        """
        to_dim = origin.shape[0]

        assert origin.shape == x_dir.shape == y_dir.shape == (to_dim,), (
            f"origin.shape = {origin.shape} != x_dir.shape = {x_dir.shape}, "
            f"!= y_dir.shape = {y_dir.shape} != ({to_dim},)"
        )
        assert torch.allclose(torch.dot(x_dir, y_dir), torch.zeros(to_dim)), (
            "x_dir and y_dir must be orthogonal"
        )

        base_jac = torch.stack([x_dir, y_dir], dim=-1).unsqueeze(0)

        def map(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return (
                origin
                + x[..., 0].unsqueeze(-1) * x_dir
                + x[..., 1].unsqueeze(-1) * y_dir
            )

        def jac(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return base_jac.broadcast_to(x.shape[0], to_dim, 2)

        return Mapping(2, to_dim, map, jac, None, None)

    @staticmethod
    def rot_2d(angle: float, center: torch.Tensor | None = None) -> Mapping:
        r"""2D rotation of angle about center.

        Args:
            angle: The angle.
            center: The center of the rotation; if None then use origin.
                Defaults to None.

        Returns:
            The 2D rotation of angle about center.
        """
        if center is None:
            centerT = torch.zeros(2)
        elif isinstance(center, torch.Tensor):
            centerT = center
        else:
            centerT = torch.tensor(center)
        angleT = angle if isinstance(angle, torch.Tensor) else torch.tensor(angle)
        rot_mat = torch.tensor(
            [
                [torch.cos(angleT), -torch.sin(angleT)],
                [torch.sin(angleT), torch.cos(angleT)],
            ],
            dtype=torch.get_default_dtype(),
        )

        def map(x: torch.Tensor, **kwargs) -> torch.Tensor:
            x = x - centerT
            return (rot_mat @ x.T).T + centerT

        def jac(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return rot_mat.broadcast_to(x.shape[0], 2, 2)

        def inv(x: torch.Tensor, **kwargs) -> torch.Tensor:
            x = x - centerT
            return (rot_mat.T @ x.T).T + centerT

        def jac_inv(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return rot_mat.T.broadcast_to(x.shape[0], 2, 2)

        return Mapping(2, 2, map, jac, inv, jac_inv)

    @staticmethod
    def rot_3d(
        axis: torch.Tensor, angle: float, center: torch.Tensor | None = None
    ) -> Mapping:
        r"""3D rotation of angle around invariant axis about center.

        Args:
            axis: The invariant axis of the rotation.
            angle: The angle.
            center: The center of the rotation.

        Returns:
            The 3D rotation of angle around invariant axis about center.
        """
        if center is None:
            centerT = torch.zeros(3)
        elif isinstance(center, torch.Tensor):
            centerT = center
        else:
            centerT = torch.tensor(center)
        angleT = angle if isinstance(angle, torch.Tensor) else torch.tensor(angle)
        axis = axis / torch.linalg.norm(axis)
        c = torch.cos(angleT)
        s = torch.sin(angleT)
        # REMI: this formula does not seem to be correct; use the latter:
        # rot_mat = (
        #     torch.eye(3, dtype=torch.get_default_dtype())
        #     + s * torch.cross(torch.eye(3, dtype=torch.get_default_dtype()),
        #                       axis[None, ...], dim = -1)
        #     + (1 - c) * torch.outer(axis, axis)
        # )
        # REMI: debug:
        Id = torch.eye(3, dtype=torch.get_default_dtype())
        Q = torch.tensor(
            [
                [0.0, -axis[..., 2], axis[..., 1]],
                [axis[..., 2], 0.0, -axis[..., 0]],
                [-axis[..., 1], axis[..., 0], 0.0],
            ]
        )
        # first formula
        # R = Id + s * Q + (1-c) * Q@Q
        # second formula
        P = torch.outer(axis, axis)
        #
        Q2 = P - Id
        # assert torch.allclose( Q2, Q@Q)
        rot_mat = P + c * -Q2 + s * Q
        # assert torch.allclose(rot_mat, R)
        # END

        def map(x: torch.Tensor, **kwargs) -> torch.Tensor:
            x = x - centerT
            return (rot_mat @ x.T).T + centerT

        def jac(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return rot_mat.broadcast_to(x.shape[0], 3, 3)

        def inv(x: torch.Tensor, **kwargs) -> torch.Tensor:
            x = x - centerT
            return (rot_mat.T @ x.T).T + centerT

        def jac_inv(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return rot_mat.T.broadcast_to(x.shape[0], 3, 3)

        return Mapping(3, 3, map, jac, inv, jac_inv)

    @staticmethod
    def translate(translation_vector: torch.Tensor) -> Mapping:
        """Translation mapping in an arbitrary dimension.

        Args:
            translation_vector: The translation vector.

        Returns:
            The translation mapping.

        """
        assert translation_vector.ndim == 1, "translation_vector must be a 1D tensor"
        to_dim = translation_vector.shape[0]

        def map(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return x + translation_vector

        def jac(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return torch.eye(to_dim, dtype=torch.get_default_dtype()).broadcast_to(
                x.shape[0], to_dim, to_dim
            )

        def inv(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return x - translation_vector

        def jac_inv(x: torch.Tensor, **kwargs) -> torch.Tensor:
            return torch.eye(to_dim, dtype=torch.get_default_dtype()).broadcast_to(
                x.shape[0], to_dim, to_dim
            )

        return Mapping(to_dim, to_dim, map, jac, inv, jac_inv)

    @staticmethod
    def surface_torus_3d(
        radius: float, tube_radius: float, center: torch.Tensor = torch.zeros(3)
    ) -> Mapping:
        r"""Mapping from :math:`(0, 2\pi) \times (0, 2\pi)` to the surface of the torus.

        Maps :math:`(0, 2\pi) \times (0, 2\pi)` to the surface of a
            torus of major radius :math:`R` and minor radius :math:`r`.

        Args:
            radius: The major radius of the torus.
            tube_radius: The minor radius of the torus.
            center: The center of the torus.

        Returns:
            The mapping to the surface of the torus (non-invertible).
        """

        def map(x: torch.Tensor, **kwargs) -> torch.Tensor:
            theta, phi = x[..., 0], x[..., 1]
            return center + torch.stack(
                [
                    (radius + tube_radius * torch.sin(theta)) * torch.cos(phi),
                    (radius + tube_radius * torch.sin(theta)) * torch.sin(phi),
                    tube_radius * torch.cos(theta),
                ],
                dim=-1,
            )

        def jac(x: torch.Tensor, **kwargs) -> torch.Tensor:
            theta, phi = x[..., 0], x[..., 1]
            dtheta = torch.stack(
                [
                    tube_radius * torch.cos(theta) * torch.cos(phi),
                    tube_radius * torch.cos(theta) * torch.sin(phi),
                    -tube_radius * torch.sin(theta),
                ],
                dim=-1,
            )
            dphi = torch.stack(
                [
                    (radius + tube_radius * torch.sin(theta)) * -torch.sin(phi),
                    (radius + tube_radius * torch.sin(theta)) * torch.cos(phi),
                    torch.zeros_like(theta),
                ],
                dim=-1,
            )
            return torch.stack([dtheta, dphi], dim=-1)

        return Mapping(2, 3, map, jac, None, None)

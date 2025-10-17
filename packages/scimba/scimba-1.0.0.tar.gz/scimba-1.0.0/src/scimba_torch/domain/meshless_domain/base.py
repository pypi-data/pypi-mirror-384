"""Base module for meshless domains."""

from __future__ import annotations

from typing import Any, Callable, cast

import numpy as np
import torch

from scimba_torch.domain.sdf import SignedDistance
from scimba_torch.utils import Mapping


##################### Volumetric domain #####################
class VolumetricDomain:
    r"""Base class for the volumetric meshless domains.

    .. math::

        \Omega = \{ x \in \text{bounds} \subset \mathbb{R}^n \, | \,
        \text{sdf}(x) < - \text{sdf.threshold} \}

    Note:
        - Mapped domain is only allowed on the main domain.
        - You should only call the domain.set_mapping once on the main domain
          (it will be applied to all subdomains and bc_domain).
        - For holes, if you want them unmapped you should use :code:`copy_mapping=False`
          when adding the hole.
        - If some holes are already added, you can specified :code:`to_holes=False`
          when setting the mapping to the main domain, it wont be applied to any of the
          holes already added.
        - The best pratices is to create the main domain, set the mapping if any,
          then add subdomains/holes/boundary domains.
        - If you want to change the mapping, it will be applied only to the holes that
          were mapped if you pass :code:`to_holes=False`.
        - So basically a hole will always have the main domain mapping or never be
          mapped

    Args:
        domain_type: Type of the domain.
        dim: Dimension of the domain.
        sdf: Signed distance function that defines the domain.
        bounds: Tensor of shape (dim, 2) representing an hypercube that contains
            the domain.
        is_main_domain: A flag to indicate if the domain can have subdomains and holes.
    """

    def __init__(
        self,
        domain_type: str,
        dim: int,
        sdf: SignedDistance,
        bounds: list[tuple[float, float]] | torch.Tensor,
        is_main_domain: bool = False,
    ):
        self.domain_type: str = domain_type  #: Type of the domain.
        self.dim: int = dim  #: Dimension of the domain (before mapping).
        self.sdf: SignedDistance = (
            sdf  #: Signed distance function that defines the domain.
        )

        # so that it accepts list and stuff as before
        self.bounds: torch.Tensor = (
            bounds
            if isinstance(bounds, torch.Tensor)
            else torch.tensor(bounds, dtype=torch.get_default_dtype())
        )

        assert self.bounds.shape == (
            self.dim,
            2,
        ), f"Bounds shape mismatch: got {self.bounds.shape}, expected {(self.dim, 2)}"

        #: The list of boundary domains specified by the user.
        self.list_bc_domains: list[SurfacicDomain] = []

        self.is_mapped: bool = False  #: Flag to indicate if the domain is mapped.
        self.dim_postmap: int = (
            self.dim
        )  #: The dimension of the domain (after mapping).
        self.mapping: None | Mapping = Mapping.identity(
            self.dim
        )  #: The mapping of the domain (if any).
        #: Tensor of shape (dim_postmap, 2) representing a box that contains the domain
        #: (after mapping).
        self.bounds_postmap: torch.Tensor = self.bounds

        # managing main domain
        #: A flag to indicate if the domain can have subdomains and holes.
        self.is_main_domain: bool = is_main_domain

        if is_main_domain:
            # if the domain is a main domain, we can add subdomains and holes
            #: A list of subdomains that are inside the main domain
            #: (ONLY IF is_main_domain is True).
            self.list_subdomains: list[VolumetricDomain] = []
            #: A list of holes that are inside the main domain
            #: (ONLY IF is_main_domain is True).
            self.list_holes: list[VolumetricDomain] = []

    def is_inside(self, x: torch.Tensor) -> torch.Tensor:
        """Test if N points x are inside the domain (before mapping if any).

        Args:
            x: Tensor of shape (N, dim) representing the points to test.

        Returns:
            Boolean tensor of shape (N,) indicating if the points are inside the domain.
        """
        res = self.sdf(x).squeeze(1) < -self.sdf.threshold
        if self.is_main_domain:
            for hole in self.list_holes:
                temp = None
                if self.is_mapped and not hole.is_mapped:
                    temp = self.mapping(x) if temp is None else temp
                    res &= hole.is_outside(temp)
                else:
                    res &= hole.is_outside(x)
        return res

    def is_outside(self, x: torch.Tensor) -> torch.Tensor:
        """Test if N points x are outside the domain (before mapping if any).

        Args:
            x: Tensor of shape (N, dim) representing the points to test.

        Returns:
            Boolean tensor of shape (N,) indicating if the points are outside
                the domain.
        """
        res = self.sdf(x).squeeze(1) > 0.0
        if self.is_main_domain:
            for hole in self.list_holes:
                temp = None
                if self.is_mapped and not hole.is_mapped:
                    # if the hole is not mapped but the domain is
                    # we need to check if the mapped points are inside the domain !
                    temp = self.mapping(x) if temp is None else temp
                    res |= hole.is_inside(temp)
                else:
                    res |= hole.is_inside(x)

        return res

    def is_outside_np(self, x: np.ndarray) -> np.ndarray:
        """Test if N points x are outside the domain (before mapping if any).

        Args:
            x: Tensor of shape (N, dim) representing the points to test.

        Returns:
            Boolean tensor of shape (N,) indicating if the points are outside
                the domain.
        """
        return (
            self.is_outside(torch.tensor(x, dtype=torch.get_default_dtype()))
            .detach()
            .cpu()
            .numpy()
        )

    def is_on_boundary(self, x: torch.Tensor, tol: float = 1e-4) -> torch.Tensor:
        """Test if N points x are on the boundary of the domain (before mapping if any).

        Args:
            x: Tensor of shape (N, dim) representing the points to test.
            tol: Tolerance for the test (Default value = 1e-4).

        Returns:
            Boolean tensor of shape (N,) indicating if the points are on the boundary.
        """
        res = torch.abs(self.sdf(x).squeeze(1)) < tol
        if self.is_main_domain:
            for hole in self.list_holes:
                temp = None
                if self.is_mapped and not hole.is_mapped:
                    temp = self.mapping(x) if temp is None else temp
                    res |= hole.is_on_boundary(temp, tol)
                else:
                    res |= hole.is_on_boundary(x, tol)
        return res

    def is_inside_postmap(self, x: torch.Tensor) -> torch.Tensor:
        """Test if N points x are inside the domain (after mapping if any).

        Args:
            x: Tensor of shape (N, dim_postmap) representing the points to test.

        Returns:
            Boolean tensor of shape (N,) indicating if the points are inside the domain.
        """
        x = self._map_to_pre_map(x)
        return self.is_inside(x)

    def is_inside_postmap_np(self, x: np.ndarray) -> np.ndarray:
        """Test if N points x are inside the domain (after mapping if any).

        Args:
            x: Tensor of shape (N, dim_postmap) representing the points to test.

        Returns:
            Boolean tensor of shape (N,) indicating if the points are inside the domain.
        """
        return (
            self.is_inside_postmap(torch.tensor(x, dtype=torch.get_default_dtype()))
            .detach()
            .cpu()
            .numpy()
        )

    def is_outside_postmap(self, x: torch.Tensor) -> torch.Tensor:
        """Test if N points x are outside the domain (after mapping if any).

        Args:
            x: Tensor of shape (N, dim_postmap) representing the points to test.

        Returns:
            Boolean tensor of shape (N,) indicating if the points are outside
                the domain.
        """
        x = self._map_to_pre_map(x)
        return self.is_outside(x)

    def is_outside_postmap_np(self, x: np.ndarray) -> np.ndarray:
        """Test if N points x are outside the domain (after mapping if any).

        Args:
            x: Array of shape (N, dim_postmap) representing the points to test.

        Returns:
            Boolean array of shape (N,) indicating if the points are outside the domain.
        """
        return (
            self.is_outside_postmap(torch.tensor(x, dtype=torch.get_default_dtype()))
            .detach()
            .cpu()
            .numpy()
        )

    def is_on_boundary_postmap(
        self, x: torch.Tensor, tol: float = 1e-4
    ) -> torch.Tensor:
        """Test if N points x are on the boundary of the domain (after mapping if any).

        Args:
            x: Tensor of shape (N, dim_postmap) representing the points to test.
            tol: Tolerance for the test. (Default value = 1e-4)

        Returns:
            Boolean tensor of shape (N,) indicating if the points are on the boundary
                of the domain.
        """
        x = self._map_to_pre_map(x)
        return self.is_on_boundary(x, tol)

    def set_mapping(
        self,
        map: Mapping,
        bounds_postmap: torch.Tensor,
        to_holes: bool = True,
    ):
        """Set the mapping of the main domain.

        The mapping is applied to the main domain, subdomains, holes and boundary
        domains.

        If to_holes is False, the mapping is also applied to none of the holes.

        Args:
            map: The mapping to apply to the domain.
            bounds_postmap: Tensor of shape (dim_postmap, 2) representing a box
                that contains the main domain after the mapping.
            to_holes: A flag to indicate if we apply the mapping to the holes.
                (Default value = True)
        """
        assert self.is_main_domain, "only the main domain can be mapped !"
        self._set_mapping(map, bounds_postmap, to_holes)

    def _set_mapping(
        self,
        map: Mapping,
        bounds_postmap: list[tuple[float, float]] | torch.Tensor,
        to_holes: bool = True,
    ):
        self.is_mapped = True
        self.dim_postmap = map.to_dim
        self.mapping = map

        self.bounds_postmap = (
            bounds_postmap
            if isinstance(bounds_postmap, torch.Tensor)
            else torch.tensor(bounds_postmap, dtype=torch.get_default_dtype())
        )

        for bc in self.list_bc_domains:
            bc._set_mapping(map)

        if self.is_main_domain:
            for subdomain in self.list_subdomains:
                subdomain._set_mapping(map, bounds_postmap)
            for hole in self.list_holes:
                if to_holes or hole.is_mapped:
                    hole._set_mapping(map, bounds_postmap)

    def del_mapping(self):
        """Delete the mapping of the domain.

        The mapping is removed from the domain and the boundary domains.

        When working on a main domain, the mapping is also removed from the subdomains.
        """
        self.is_mapped = False
        self.dim_postmap = self.dim
        self.mapping = Mapping.identity(self.dim)
        self.bounds_postmap = self.bounds

        for bc in self.list_bc_domains:
            bc.del_mapping()

        if self.is_main_domain:
            for subdomain in self.list_subdomains:
                subdomain.del_mapping()
            for hole in self.list_holes:
                hole.del_mapping()

    def add_bc_domain(self, bc_domain: SurfacicDomain):
        """Add a boundary domain to the domain.

        If the domain is mapped, the boundary domain will have the same mapping.

        Args:
            bc_domain: The boundary domain to add.
        """
        if self.is_mapped:
            bc_domain._set_mapping(self.mapping)

        self.list_bc_domains.append(bc_domain)

    def add_subdomain(self, subdomain: VolumetricDomain):
        """Add a subdomain to the domain.

        If the domain is mapped, the subdomain will have the same mapping.

        Args:
            subdomain: The subdomain to add.
        """
        assert self.is_main_domain, (
            "trying to add a subdomain to a domain that have been constructed with "
            "is_main_domain=False"
        )
        assert not subdomain.is_main_domain, (
            "trying to add a subdomain that have been constructed with "
            "is_main_domain=True"
        )
        assert subdomain.dim == self.dim, (
            f"Dimension mismatch, got {subdomain.dim}, expected {self.dim}"
        )

        if self.is_mapped:
            subdomain._set_mapping(self.mapping, self.bounds_postmap)

        self.list_subdomains.append(subdomain)

    def add_hole(self, hole: VolumetricDomain, copy_mapping: bool = True):
        """Add a hole to the domain.

        Args:
            hole: The hole to add.
            copy_mapping: A flag to indicate if we copy the mapping of the domain to the
                hole. (Default value = True)
        """
        assert self.is_main_domain, (
            "trying to add a hole to a domain that have been constructed with "
            "is_main_domain=False"
        )
        assert not hole.is_main_domain, (
            "trying to add a hole that have been constructed with is_main_domain=True"
        )
        assert hole.dim == self.dim, (
            f"Dimension mismatch, got {hole.dim}, expected {self.dim}"
        )

        if copy_mapping and self.is_mapped:
            hole._set_mapping(self.mapping, self.bounds_postmap)

        assert hole.dim_postmap == self.dim_postmap, (
            f"Postmap dimension mismatch, got {hole.dim_postmap}, ",
            f"expected {self.dim_postmap}",
        )

        self.list_holes.append(hole)

    def full_bc_domain(self) -> list[SurfacicDomain]:
        """Return a list of boundary domains that make up the full domain boundary.

        Returns:
            The list of boundary subdomains.

        Raises:
            NotImplementedError: If the method is not implemented for the specific
                class.
        """
        raise NotImplementedError(
            f"full_bc_domain is not implemented for {self.__class__.__name__}"
        )

    @property
    def has_bc_domain(self) -> bool:
        """Check if the domain has boundary domains.

        Returns:
            True if the domain has boundary domains, False otherwise.
        """
        return self.list_bc_domains != []

    def get_all_bc_domains(
        self,
    ) -> tuple[list[SurfacicDomain], list[SurfacicDomain], list[SurfacicDomain]]:
        """Return the lists containing all boundary domains.

        Returns:
            The list of boundary domains of the main domain, the holes and the
            subdomains (if called on the main domain).
            Otherwise, just the list of boundary domains.
        """
        if self.has_bc_domain:
            res = self.list_bc_domains
        else:
            res = self.full_bc_domain()

        if not self.is_main_domain:
            return res

        res_subdomains: list[SurfacicDomain] = []
        for subdomain in self.list_subdomains:
            res_subdomain = cast(list[SurfacicDomain], subdomain.get_all_bc_domains())
            res_subdomains += res_subdomain

        res_holes: list[SurfacicDomain] = []
        for hole in self.list_holes:
            res_hole = cast(list[SurfacicDomain], hole.get_all_bc_domains())
            res_holes += res_hole

        return res, res_holes, res_subdomains

    # a litle utility function
    def _map_to_pre_map(self, x: torch.Tensor) -> torch.Tensor:
        if self.is_mapped:
            if not self.mapping.is_invertible:
                raise ValueError("Mapping is not invertible.")
            return self.mapping.inv(x)
        return x

    def get_extended_bounds(self, factor: float = 0.05) -> np.ndarray:
        r"""Return extended bounds of the domain (before mapping if any).

        Args:
            factor: The factor by which to extend the bounds. (Default value = 0.05)

        Returns:
            The extended bounds as a numpy array of shape (dim, 2).
        """
        bb = self.bounds
        maxwidth = torch.max(bb[:, 1] - bb[:, 0])
        res = torch.ones_like(bb) * (factor / 2.0) * maxwidth
        res[:, 0] = bb[:, 0] - res[:, 0]
        res[:, 1] = bb[:, 1] + res[:, 1]
        return res.detach().cpu().numpy()

    def get_extended_bounds_postmap(self, factor: float = 0.05) -> np.ndarray:
        """Return extended bounds of the domain (after mapping if any).

        Args:
            factor: The factor by which to extend the bounds. (Default value = 0.05)

        Returns:
            The extended bounds as a numpy array of shape (dim_postmap, 2).
        """
        bb = self.bounds_postmap
        maxwidth = torch.max(bb[:, 1] - bb[:, 0])
        res = torch.ones_like(bb) * (factor / 2.0) * maxwidth
        res[:, 0] = bb[:, 0] - res[:, 0]
        res[:, 1] = bb[:, 1] + res[:, 1]
        return res.detach().cpu().numpy()


##################### Surfacic domain #####################
class SurfacicDomain:
    r"""Base class for representing the boundary of a domain.

    .. math::
        \partial \Omega = \text{surface}(\text{parametric_domain})

    Args:
        domain_type: Type of the domain.
        parametric_domain: The parametric domain.
        surface: Mapping from the parametric domain to the domain.
    """

    def __init__(
        self,
        domain_type: str,
        parametric_domain: VolumetricDomain,
        surface: Mapping,
    ):
        self.domain_type: str = domain_type  #: Type of the domain.
        self.parametric_domain: VolumetricDomain = (
            parametric_domain  #: The parametric domain.
        )
        self.surface: Mapping = (
            surface  #: Mapping from the parametric domain to the domain.
        )

        assert not self.parametric_domain.is_main_domain, (
            "parametric domain can't be a main domain."
        )
        assert not self.parametric_domain.is_mapped, (
            "parametric domain can't be a mapped domain."
        )

        #: Dimension of the parametric domain.
        self.dim_parametric: int = parametric_domain.dim
        #: Dimension of the domain (before mapping, =dim_parametric+1).
        self.dim: int = self.dim_parametric + 1

        assert surface.from_dim == self.dim_parametric and surface.to_dim == self.dim, (
            f"Surface mapping dimension mismatch, got {surface.from_dim} -> "
            f"{surface.to_dim}, expected {self.dim_parametric} -> {self.dim}"
        )

        # when creating the domain, it's not mapped
        self.is_mapped: bool = False  # ; Flag to indicate if the domain is mapped.
        self.dim_postmap: int = self.dim  #: Dimension of the domain (after mapping).
        self.mapping: Mapping | None = Mapping.identity(
            self.dim
        )  #: The mapping of the domain (if any).
        self.surface_o_mapping: Mapping = (
            self.surface
        )  #: The composition of the surface and the mapping.

    def _set_mapping(self, mapping: Mapping):
        """Set the mapping of the domain.

        Args:
            mapping: The mapping to apply to the domain.
        """
        self.is_mapped = True
        self.dim_postmap = mapping.to_dim
        self.mapping = mapping
        self.surface_o_mapping = Mapping.compose(self.surface, self.mapping)

    def del_mapping(self):
        """Delete the mapping of the domain."""
        self.is_mapped = False
        self.dim_postmap = self.dim
        self.mapping = Mapping.identity(self.dim)
        self.surface_o_mapping = self.surface

    def compute_normals(self, t: torch.Tensor, **kwargs: Any) -> torch.Tensor:
        """Compute the normals of the surface at the points t in the parametric domain.

        Args:
            t: Tensor of shape (N, dim_parametric) representing the points in the
                parametric domain.
            **kwargs: Additional arguments for the mapping.

        Returns:
            Tensor of shape (N, dim_postmap) representing the normals.
        """
        assert self.dim == 1 or self.dim == 2 or self.dim == 3, (
            f"Dimension {self.dim} not supported for normals computation."
        )

        jac = self.surface_o_mapping.jac(t, **kwargs)

        if self.dim == 1:
            normal = torch.sign(jac.squeeze(2))
        elif self.dim == 2:
            normal = torch.concatenate([jac[..., 1, :], -jac[..., 0, :]], dim=-1)
        elif self.dim == 3:
            normal = torch.cross(jac[..., :, 0], jac[..., :, 1], dim=-1)
        return normal / torch.linalg.norm(normal, dim=-1, keepdim=True)

    def get_sdf(self) -> Callable[[torch.Tensor], torch.Tensor]:
        """Return the signed distance function of the domain.

        Returns:
            The signed distance function of the domain.

        Raises:
            NotImplementedError: the domain does not support this method.
        """
        raise NotImplementedError(
            f"get_sdf is not implemented for {self.__class__.__name__}"
        )

    def is_valid_parametric_point_np(self, x: np.ndarray | Any) -> bool:
        """Check wether tensor is a valid (batch of) point(s) in the parametric domain.

        Args:
            x: input point

        Returns:
            True if and only if x is a valid point not outside the parametric domain.

        Raises:
            ValueError: if the input value can not be broadcasted to a valid shape.
        """
        xx = x if isinstance(x, np.ndarray) else np.array(x, dtype=np.float64)

        if (xx.ndim == 0) and (
            (self.dim_parametric == 1) or (self.domain_type == "Point1D")
        ):
            xx = xx[None]

        if (xx.ndim == 1) and (
            (len(xx) == self.dim_parametric)
            or ((self.domain_type == "Point1D") and len(xx) == 1)
        ):
            xx = xx[None, ...]

        res = False

        if (xx.ndim == 2) and (
            (xx.shape[1] == self.dim_parametric)
            or ((self.domain_type == "Point1D") and xx.shape[1] == 1)
        ):
            res = not np.any(self.parametric_domain.is_outside_np(xx))

        else:
            dim = 1 if self.domain_type == "Point1D" else self.dim_parametric
            message = "input has incorrect shape: must be (any,%d)" % (dim)
            raise ValueError(message)

        return res

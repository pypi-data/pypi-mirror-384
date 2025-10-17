"""nD domains."""

import torch

from scimba_torch.domain.meshless_domain.base import VolumetricDomain
from scimba_torch.domain.sdf import SignedDistance

dtype = torch.get_default_dtype()


################## Basic Volumetric domains in nD ##################
class HypercubeND(VolumetricDomain):
    """Hypercube n-dimensional domain.

    Args:
        bounds: A list of tuples representing the bounds of the cube in each dimension.
        is_main_domain: A flag to indicate if the domain can have subdomains and holes.
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
        assert (t_bounds.dim() == 2) and (t_bounds.shape[1] == 2), (
            "bounds must be a tensor of shape (n, 2)"
        )

        dim = t_bounds.shape[0]

        class HypercubeSDF(SignedDistance):
            def __init__(self, bounds: torch.Tensor):
                super().__init__(dim, threshold=0)
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
            domain_type=f"Hypercube_{dim}D",
            dim=dim,
            sdf=HypercubeSDF(t_bounds),
            bounds=t_bounds,
            is_main_domain=is_main_domain,
        )

    def full_bc_domain(self):
        """Returns the full boundary condition domain for the Hypercube_nD.

        Raises:
            NotImplementedError: Hypercube_nD does not have a full boundary condition
                domain implemented.
        """
        raise NotImplementedError(
            "Hypercube_nD does not have a full boundary condition domain"
        )


class CartesianProduct(VolumetricDomain):
    """Cartesian product of multiple domains.

    Args:
        domains: list of domains to be combined
        is_main_domain: Whether the domain is the main domain or not

    Raises:
        ValueError: If any of the domains have non-invertible mappings
    """

    def __init__(
        self,
        domains: list[VolumetricDomain],
        is_main_domain: bool = False,
    ):
        assert len(domains) > 0, "At least one domain must be provided"
        if any(d.is_mapped and not d.mapping.is_invertible for d in domains):
            msg = "All mappings in CartesianProduct must be invertible"
            raise ValueError(msg)

        bounds = torch.cat([domain.bounds_postmap for domain in domains], dim=0)
        # print(bounds)
        self.base_domains = domains

        self.dim_cumsum = torch.cumsum(
            torch.tensor([0] + [d.dim for d in domains]), dim=0
        )
        dim = self.dim_cumsum[-1]

        class CartesianProductSDF(SignedDistance):
            def __init__(sdf):  # noqa: N805
                super(CartesianProductSDF, sdf).__init__(dim, threshold=0)

            def __call__(sdf, x):  # noqa: N805
                # Compute the SDF for each domain and combine them
                x_pre = self._map_to_pre_map(x)
                sdf_values = torch.cat(
                    [
                        domain.sdf(x_pre[..., i : i + domain.dim])
                        for i, domain in zip(self.dim_cumsum[:-1], self.base_domains)
                    ],
                    dim=-1,
                )
                # res = sdf_values.max(dim=-1, keepdim=True)
                res = torch.max(sdf_values, dim=-1).values[..., None]
                return res

        super(CartesianProduct, self).__init__(
            domain_type="CartesianProduct("
            + ", ".join(d.domain_type for d in domains)
            + ")",
            dim=dim,
            sdf=CartesianProductSDF(),
            bounds=bounds,
            is_main_domain=is_main_domain,
        )

        self.domains = domains

    def _map_to_pre_map_sub(self, x):
        return torch.stack(
            [
                domain._map_to_pre_map(x[..., i : i + domain.dim])
                for i, domain in zip(self.dim_cumsum[:-1], self.base_domains)
            ],
            dim=-1,
        )

    def is_inside(self, x: torch.Tensor) -> torch.Tensor:  # noqa: D102
        return torch.stack(
            [
                domain.is_inside_postmap(x[..., i : i + domain.dim])
                for i, domain in zip(self.dim_cumsum[:-1], self.base_domains)
            ],
            dim=-1,
        ).all(dim=-1)

    def is_outside(self, x):  # noqa: D102
        return torch.stack(
            [
                domain.is_outside_postmap(x[..., i : i + domain.dim])
                for i, domain in zip(self.dim_cumsum[:-1], self.base_domains)
            ],
            dim=-1,
        ).any(dim=-1)

    def full_bc_domain(self):
        """Returns the full boundary condition domain for the CartesianProduct.

        Raises:
            NotImplementedError: CartesianProduct does not have a full boundary
                condition domain implemented.
        """
        raise NotImplementedError(
            "CartesianProduct does not have a full boundary condition domain"
        )

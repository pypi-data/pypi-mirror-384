"""Monte Carlo integration methods for volumetric and surfacic domains."""

from __future__ import annotations

from typing import cast
from warnings import warn

import numpy as np
import torch
from torch.distributions.uniform import Uniform

from scimba_torch.domain.meshless_domain.base import SurfacicDomain, VolumetricDomain
from scimba_torch.integration.monte_carlo_parameters import (
    UniformParametricSampler,
    UniformVelocitySampler,
)
from scimba_torch.integration.monte_carlo_time import UniformTimeSampler
from scimba_torch.utils import Mapping
from scimba_torch.utils.scimba_tensors import LabelTensor


class VolumetricSampler:
    """Samples points uniformly within a volumetric domain.

    Args:
        domain: The volumetric domain being sampled.

    Raises:
        TypeError: If domain is not an object of class VolumetricDomain.
        ValueError: If the estimated volume of the domain is too small.
    """

    def __init__(self, domain: VolumetricDomain):
        if not isinstance(domain, VolumetricDomain):
            raise TypeError("domain must be an object of class VolumetricDomain")

        self.domain = domain  #: The volumetric domain being sampled.
        self.base_sampler = Uniform(
            domain.bounds[:, 0], domain.bounds[:, 1]
        )  #: Uniform sampler for the domain bounds.

        # Estimate the proportion of the bounding box occupied by the domain
        N = 10_000
        pts = self.base_sampler.sample((N,))
        percent_in = domain.is_inside(pts).sum().item() / N
        self.percent_in: float = (
            percent_in * 0.95 if percent_in < 1.0 else 1.0
        )  #: Estimated percentage of the bounds occupied by the domain.

        if self.percent_in == 0:  # otherwise division by zero
            raise ValueError("the estimated volume of the domain is too small ")

        if self.percent_in < 0.1:  # warn if less than 10% of surrounding box
            msg = (
                f"the domain {domain.domain_type} is very small compared to the bounds"
            )
            warn(msg, UserWarning, stacklevel=2)

        # If the domain is mapped and the mapping is invertible
        self.percent_in_postmap: float = (
            1.0  #: Percentage for the mapped domain if applicable.
        )
        if self.domain.is_mapped:
            assert isinstance(self.domain.mapping, Mapping)
            if self.domain.mapping.is_invertible:
                self.base_sampler_postmap = Uniform(
                    domain.bounds_postmap[:, 0], domain.bounds_postmap[:, 1]
                )  #: Uniform sampler for the mapped domain bounds.

                # Estimate the percentage for the mapped domain
                pts = self.base_sampler_postmap.sample((N,))
                percent_in = domain.is_inside_postmap(pts).sum().item() / N
                self.percent_in_postmap = min(1.0, percent_in * 1.1)

    def sample(self, n: int, apply_map: bool = True) -> torch.Tensor:
        """Samples points within the volumetric domain.

        Args:
            n: Number of points to sample.
            apply_map: Whether to apply the domain mapping if it exists.
                Defaults to True.

        Returns:
            An array of sampled points of shape (n, d).

        Raises:
            TypeError: If argument is not an integer.
            ValueError: If argument is negative.
        """
        if not isinstance(n, int):
            raise TypeError("argument to sample method must be an integer")
        if n < 0:
            raise ValueError("argument to sample method must be non-negative")

        n_pts = int(n / self.percent_in)
        pts = self.base_sampler.sample((n_pts,))

        # Filter points inside the domain, if necessary
        if not self.percent_in == 1.0:
            pts_inside = self.domain.is_inside(pts)
            pts = pts[pts_inside, :]

        # Sample additional points if the required number is not met
        n_pts = int((n - pts.shape[0]) / self.percent_in)
        while n_pts > 0:
            opts = self.base_sampler.sample((n_pts,))
            opts_inside = self.domain.is_inside(opts)
            opts = opts[opts_inside, :]

            pts = torch.cat([pts, opts], dim=0)
            n_pts = int((n - pts.shape[0]) / self.percent_in)

        # Map the points if the domain is mapped
        if self.domain.is_mapped and apply_map:
            assert isinstance(self.domain.mapping, Mapping)
            pts = self.domain.mapping(pts)

        return pts[:n, :]

    def sample_postmap(self, n: int) -> torch.Tensor:
        """Samples points in the mapped domain.

        Args:
            n: Number of points to sample.

        Returns:
            An array of sampled points of shape (n, d).

        Raises:
            TypeError: If argument is not an integer.
            ValueError: If argument is negative.
        """
        if not isinstance(n, int):
            raise TypeError("argument to sample_postmap method must be an integer")
        if n < 0:
            raise ValueError("argument to sample_postmap method must be non-negative")

        assert self.domain.is_mapped, "This domain is not mapped"
        assert isinstance(self.domain.mapping, Mapping)
        assert self.domain.mapping.is_invertible, (
            "This domain mapping is not invertible"
        )

        n_pts = int(n / self.percent_in_postmap)
        pts = self.base_sampler_postmap.sample((n_pts,))

        # Filter points inside the mapped domain
        pts = pts[self.domain.is_inside_postmap(pts), :]
        n_pts = n - pts.shape[0]
        if n_pts > 0:
            pts = torch.cat([pts, self.sample_postmap(n_pts)], dim=0)

        return pts[:n, :]


class SurfacicSampler:
    """A sampler designed for surfaces defined by a parametric domain.

    This sampler generates points on a surface using a volumetric sampler
    on the associated parametric domain and maps them onto the surface.

    Args:
        domain: The surface domain to be sampled.

    Raises:
        TypeError: If domain is not an object of class SurfacicDomain.
    """

    def __init__(self, domain: SurfacicDomain):
        if not isinstance(domain, SurfacicDomain):
            raise TypeError("domain must be an object of class SurfacicDomain")

        self.domain = domain  #: The surface domain to sample from.

        # Create a volumetric sampler for the parametric domain of the surface
        self.base_sampler = VolumetricSampler(
            self.domain.parametric_domain
        )  #: A sampler for the parametric domain.

    def sample(
        self, n: int, compute_normals: bool = False
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]:
        """Samples points on the surface.

        Args:
            n: The number of points to sample.
            compute_normals: If True, compute and return surface normals.
                Defaults to False.

        Returns:
            Points on the surface of shape (n, d), or a tuple of (points, normals)
            if compute_normals is True.

        Raises:
            TypeError: If argument is not an integer.
            ValueError: If argument is negative.
        """
        if not isinstance(n, int):
            raise TypeError("argument to sample method must be an integer")
        if n < 0:
            raise ValueError("argument to sample method must be non-negative")

        # Sample points in the parametric domain
        parametric_pts = self.base_sampler.sample(n)

        # Map the sampled points from the parametric domain to the surface
        pts = self.domain.surface_o_mapping(parametric_pts)

        # If requested, compute surface normals at the sampled points
        if compute_normals:
            normals = self.domain.compute_normals(parametric_pts)
            return pts, normals

        # Return the sampled points on the surface
        return pts


class DomainSampler:
    """A sampler for volumetric domains with support for subdomains, holes, and BCs.

    This sampler manages a primary volumetric sampler and additional samplers for
    boundary conditions, holes, and subdomains.

    Args:
        domain: The volumetric domain to sample.
        **kwargs: Additional configuration options including:

            - pre_sampling: Enable pre-sampling for the volumetric domain.
            - bc_pre_sampling: Enable pre-sampling for boundary condition domains.
            - npoint_pre_sampling: Number of pre-sampled points for the volumetric
              domain.

    Raises:
        TypeError: If domain is not an object of class VolumetricDomain, or if
            npoints_pre_sampling or bc_npoints_pre_sampling are not integers.
        ValueError: If npoints_pre_sampling or bc_npoints_pre_sampling are not positive.
    """

    def __init__(self, domain: VolumetricDomain, **kwargs):
        if not isinstance(domain, VolumetricDomain):
            raise TypeError("domain must be an object of class VolumetricDomain")

        self.domain = domain

        # Initialize sampler for the main domain
        self.vol_sampler = VolumetricSampler(domain)

        try:
            # Initialize sub-domains, holes, and boundary conditions
            self.bc_domains, self.bc_holes, self.bc_subdomains = (
                domain.get_all_bc_domains()
            )

            # Initialize sub-domains, holes, and boundary conditions samplers
            self.bc_sampler = [SurfacicSampler(domain) for domain in self.bc_domains]
            self.bc_holes_sampler = [
                SurfacicSampler(domain) for domain in self.bc_holes
            ]
            self.bc_subdomains_sampler = [
                SurfacicSampler(domain) for domain in self.bc_subdomains
            ]

        except NotImplementedError:
            print()
            print("⚠" * 9)
            print("⚠WARNING⚠: The domain does not have boundary conditions")
            print("⚠" * 9)
            print()
            self.bc_domains, self.bc_holes, self.bc_subdomains = [], [], []

        # Pre-sampling configurations
        self.pre_sampling = kwargs.get("pre_sampling", False)
        self.bc_pre_sampling = kwargs.get("bc_pre_sampling", False)
        self.npoints_pre_sampling = kwargs.get("npoint_pre_sampling", 100000)
        self.bc_npoints_pre_sampling = kwargs.get("bc_npoint_pre_sampling", 100000)

        if not isinstance(self.npoints_pre_sampling, int):
            raise TypeError("keyword argument npoints_pre_sampling must be an integer")
        if self.npoints_pre_sampling <= 0:
            raise ValueError("keyword argument npoints_pre_sampling must be positive")

        if not isinstance(self.bc_npoints_pre_sampling, int):
            raise TypeError(
                "keyword argument bc_npoints_pre_sampling must be an integer"
            )
        if self.bc_npoints_pre_sampling <= 0:
            raise ValueError(
                "keyword argument bc_npoints_pre_sampling must be positive"
            )

        # Perform pre-sampling if enabled
        if self.pre_sampling:
            self.pts = self.sample_new_points(self.npoints_pre_sampling)
            self.sample_func = self.sample_pre_sampled_points
        else:
            self.sample_func = self.sample_new_points

        if self.bc_pre_sampling:
            self.bc_pts, self.bc_nrs = self.bc_sample_new_points(
                self.bc_npoints_pre_sampling
            )
            self.bc_sample_func = self.bc_sample_pre_sampled_points
        else:
            self.bc_sample_func = self.bc_sample_new_points

    def sample(self, n: int) -> LabelTensor:
        """Samples `n` points from the volumetric domain and labels them by subdomains.

        Possibly uses pre-sampled points.

        Args:
            n: Number of points to sample.

        Returns:
            LabelTensor: A tensor of sampled points with their subdomain labels.

        Raises:
            TypeError: If argument is not an integer.
            ValueError: If argument is negative.
        """
        if not isinstance(n, int):
            raise TypeError("argument to sample method must be an integer")
        if n < 0:
            raise ValueError("argument to sample method must be non-negative")

        return self.sample_func(n)

    def bc_sample(self, n: int | list[int]) -> tuple[LabelTensor, LabelTensor]:
        """Samples `n` points from the boundary domains.

        Args:
            n: Number of points to sample. If a list, then samples specific number
                of points for each bc domain.

        Returns:
            A tuple of tensors of sampled points.

        Raises:
            TypeError: If argument is not an integer or a list of integers.
            ValueError: If argument is negative.s
        """
        if not (
            isinstance(n, int)
            or (isinstance(n, list) and all(isinstance(nn, int) for nn in n))
        ):
            raise TypeError(
                "argument to sample method must be an integer or a sequence of integer"
            )
        if (isinstance(n, int) and (n < 0)) or (
            isinstance(n, list) and any(nn < 0 for nn in n)
        ):
            raise ValueError(
                "argument to sample method must be a non-negative int or a list of "
                "non-negative int"
            )

        return self.bc_sample_func(n)

    def sample_pre_sampled_points(self, n: int) -> LabelTensor:
        """Samples `n` points from the pre-sampled volumetric points.

        Args:
            n: Number of points to sample.

        Returns:
            LabelTensor: A tensor of sampled points.
        """
        if n <= self.npoints_pre_sampling:
            indices = torch.randperm(self.npoints_pre_sampling)[:n]
        else:
            f = int(np.ceil(n / self.npoints_pre_sampling))
            indices = torch.remainder(
                torch.randperm(self.npoints_pre_sampling * f)[:n],
                self.npoints_pre_sampling,
            ).type(torch.int)
        data = self.pts[indices]
        return data

    def sample_new_points(self, n: int) -> LabelTensor:
        """Samples new points from the volumetric domain and labels them by subdomains.

        Args:
            n: Number of points to sample.

        Returns:
            A tensor of sampled points with their subdomain labels.
        """
        pts = self.vol_sampler.sample(n, apply_map=False)
        labels = torch.zeros(n, dtype=torch.int32)

        # Label points based on subdomains
        for i, subdomain in enumerate(self.domain.list_subdomains):
            condition = subdomain.is_inside(pts)
            labels[condition] = i + 1

        if self.domain.is_mapped:
            assert isinstance(self.domain.mapping, Mapping)
            pts = self.domain.mapping(pts)

        # Wrap the points and labels in a ScimbaTensor
        data = LabelTensor(pts, labels)
        data.x.requires_grad_()
        return data

    def bc_sample_pre_sampled_points(
        self, n: int | list[int]
    ) -> tuple[LabelTensor, LabelTensor]:
        """Samples points from the pre-sampled boundary condition points.

        Args:
            n: Number of points to sample.

        Returns:
            A tensor of sampled points.

        Raises:
            TypeError: If argument is not an integer.
            ValueError: If argument is negative.
        """
        if not isinstance(n, int):
            raise TypeError(
                "argument to bc_sample_pre_sampled_points method must be an integer"
            )
        if n < 0:
            raise ValueError(
                "argument to bc_sample_pre_sampled_points method must be non-negative"
            )

        if n <= self.bc_npoints_pre_sampling:
            indices = torch.randperm(self.bc_npoints_pre_sampling)[:n]
        else:
            f = int(np.ceil(n / self.bc_npoints_pre_sampling))
            indices = torch.remainder(
                torch.randperm(self.bc_npoints_pre_sampling * f)[:n],
                self.bc_npoints_pre_sampling,
            ).type(torch.int)

        return self.bc_pts[indices], self.bc_nrs[indices]

    def bc_sample_new_points(
        self, n: int | list[int]
    ) -> tuple[LabelTensor, LabelTensor]:
        """Samples new points from the boundary domains.

        The boundary domains includes the main domain, holes, and subdomains.

        Note:
            Don't we want to sample bc points for subdomains in a separate function...?

        Args:
            n: Number of points to sample. If a list, then samples specific number of
                points for each bc domain.

        Returns:
            A tensor of sampled points with their labels.

        Raises:
            ValueError: If the number of points to sample doesn't match the number of
                BC domains.
        """
        n_bc_main = len(self.bc_domains)
        n_bc_holes = len(self.bc_holes)
        n_bc_subdomains = len(self.bc_subdomains)
        if isinstance(n, int):
            m = int(n / (n_bc_main + n_bc_holes + n_bc_subdomains))
            n_list_main = [m] * n_bc_main
            n_list_holes = [m] * n_bc_holes
            n_list_subdomains = [m] * n_bc_subdomains
            # add points on the first bc domain if needed
            n_list_main[0] += n - m * (n_bc_main + n_bc_holes + n_bc_subdomains)
        else:
            if len(n) != n_bc_main + n_bc_holes + n_bc_subdomains:
                msg = (
                    "The number of points to sample must match the number "
                    f"of BC domains. Got {len(n)} points, expected {n_bc_main} + "
                    f"{n_bc_holes} + {n_bc_subdomains}"
                )
                raise ValueError(msg)
            n_list_main = n[:n_bc_main]
            n_list_holes = n[n_bc_main : n_bc_main + n_bc_holes]
            n_list_subdomains = n[n_bc_main + n_bc_holes :]

        list_data_p: list[LabelTensor] = []
        list_data_n: list[LabelTensor] = []
        i = 0

        # Sample points for boundary condition domains
        for subsampler, m in zip(self.bc_sampler, n_list_main):
            pts, normals = subsampler.sample(m, compute_normals=True)
            labels = torch.ones(m, dtype=torch.int32) * i
            data_p = LabelTensor(pts, labels)
            data_n = LabelTensor(normals, labels)
            data_p.x.requires_grad_()
            data_n.x.requires_grad_()
            list_data_p.append(data_p)
            list_data_n.append(data_n)
            i += 1

        # Sample points for the BC of the holes
        for subsampler, m in zip(self.bc_holes_sampler, n_list_holes):
            pts, normals = subsampler.sample(m, compute_normals=True)
            labels = torch.ones(m, dtype=torch.int32) * i
            data_p = LabelTensor(pts, labels)
            data_n = LabelTensor(normals, labels)
            data_p.x.requires_grad_()
            data_n.x.requires_grad_()
            list_data_p.append(data_p)
            list_data_n.append(data_n)
            i += 1

        # Sample points for the BC of the subdomains
        i = 100  # Unique label offset for subdomains
        for subsampler, m in zip(self.bc_subdomains_sampler, n_list_subdomains):
            pts, normals = subsampler.sample(m, compute_normals=True)
            labels = torch.ones(m, dtype=torch.int32) * i
            data_p = LabelTensor(pts, labels)
            data_n = LabelTensor(normals, labels)
            data_p.x.requires_grad_()
            data_n.x.requires_grad_()
            list_data_p.append(data_p)
            list_data_n.append(data_n)
            i += 1

        # Concatenate all sampled data into a single tensor
        data_p = LabelTensor.cat(list_data_p)
        data_n = LabelTensor.cat(list_data_n)
        return data_p, data_n


SAMPLER_TYPE = (
    DomainSampler
    | UniformParametricSampler
    | UniformTimeSampler
    | UniformVelocitySampler
)


class TensorizedSampler:
    """A sampler that combines multiple samplers for tensorized sampling.

    This class allows sampling from multiple samplers, with options to handle
    boundary condition (BC) samplings selectively.

    Args:
        list_sampler: A tuple of samplers, where each sampler implements
            sample and bc_sample methods.
    """

    def __init__(self, list_sampler: tuple[SAMPLER_TYPE, ...]):
        self.list_sampler = list_sampler  #: A tuple of samplers to combine.
        self.n_sampler = len(list_sampler)  #: Number of samplers in the tuple.

    def sample(self, n: int) -> tuple[LabelTensor, ...]:
        """Samples points using each sampler in the list.

        Args:
            n: The number of points to sample per sampler.

        Returns:
            A generator yielding sampled points from each sampler.
        """
        # Loop through each sampler and call its `sample` method
        return tuple(self.list_sampler[i].sample(n) for i in range(self.n_sampler))

    def bc_sample(
        self, n: int, index_bc: int = -1
    ) -> tuple[LabelTensor | tuple[LabelTensor, LabelTensor], ...]:
        """Samples points with special handling for boundary conditions (BC).

        Args:
            n: The number of points to sample per sampler.
            index_bc: The index of the sampler to prioritize for BC sampling.
                Defaults to -1 (no priority).

        Returns:
            A generator yielding BC-sampled points for the prioritized sampler
            and regular samples for the others.

        Raises:
            TypeError: If samplers are not domain samplers when expected.
        """
        res: tuple[LabelTensor | tuple[LabelTensor, LabelTensor], ...] = tuple()
        if index_bc == -1:
            # Special case where the BC sampler corresponds to the last sampler
            if any(
                not isinstance(self.list_sampler[i], DomainSampler)
                for i in range(self.n_sampler)
            ):
                raise TypeError("index_bc==-1: all samplers must be domain samplers")
            res = tuple(
                cast(DomainSampler, self.list_sampler[i]).bc_sample(n)
                for i in range(self.n_sampler)
            )
        else:
            # General case: BC sampling for the specified index,
            # regular sampling otherwise
            if not isinstance(self.list_sampler[index_bc], DomainSampler):
                raise TypeError(
                    "index_bc argument must be the index of a domain sampler"
                )
            res = tuple(
                (
                    cast(DomainSampler, self.list_sampler[index_bc]).bc_sample(n)
                    if i == index_bc
                    else self.list_sampler[i].sample(n)
                )
                for i in range(self.n_sampler)
            )
        return res

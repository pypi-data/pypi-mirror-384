"""1D domains.

In 1D we only have the Segment1D domain (VolumetricDomain)

We don't define a surface in 1D because it's the degenerate case, the parametric domain
is of dim 0...
We let the user handle this case, it should be ok giving that a surface in 1D is just a
point, with normal = -/+1 depending on the side.
"""

import torch

from ...utils import Mapping
from ..sdf import SignedDistance
from .base import SurfacicDomain, VolumetricDomain


class Segment1D(VolumetricDomain):
    """Segment1D domain.

    Args:
        low_high: Bounds of the segment
        is_main_domain: A flag to indicate if the domain can have subdomains and holes.
    """

    def __init__(
        self,
        low_high: tuple[float, float] | list[tuple[float, float]] | torch.Tensor,
        is_main_domain: bool = False,
    ):
        t_bounds: torch.Tensor = (
            low_high
            if isinstance(low_high, torch.Tensor)
            else torch.tensor(low_high, dtype=torch.get_default_dtype())
        )
        if t_bounds.shape == (2,):
            t_bounds = t_bounds[None]
        assert t_bounds.shape == (1, 2), "bounds must be a tensor of shape (1, 2)"

        class SegmentSDF(SignedDistance):
            def __init__(self, bounds: torch.Tensor):
                super().__init__(dim=1, threshold=0.0)
                self.mid_pt = (bounds[0] + bounds[1]) / 2
                self.half_len = (bounds[1] - bounds[0]) / 2

            def __call__(self, x: torch.Tensor) -> torch.Tensor:
                x = x.flatten()
                return (torch.abs(x - self.mid_pt) - self.half_len)[:, None]

        super().__init__(
            domain_type="Segment1D",
            dim=1,
            sdf=SegmentSDF(t_bounds[0]),
            bounds=t_bounds,
            is_main_domain=is_main_domain,
        )

    def full_bc_domain(self) -> list[SurfacicDomain]:
        """Return the full boundary domain of the Segment1D.

        Returns:
            A list containing the two boundary Point1D domains.
        """
        # self.bounds is the attribute of the super class VolumetricDomain
        return [
            Point1D(float(self.bounds[0, 0]), True),
            Point1D(float(self.bounds[0, 1]), False),
        ]


class Point1D(SurfacicDomain):
    """Point1D domain.

    Args:
        value: The position of the point.
        low_value: Whether the point is at the lower bound.
        tol: A small tolerance value for the point.
    """

    def __init__(self, value: float | torch.Tensor, low_value: bool, tol: float = 1e-6):
        if isinstance(value, torch.Tensor):
            assert value.dim() == 0, "value must be a scalar"
        if low_value:
            surface = Mapping.inv_identity(1)
            parametric_domain = Segment1D(
                torch.tensor(
                    (-value - tol, -value + tol), dtype=torch.get_default_dtype()
                )
            )
        else:
            surface = Mapping.identity(1)
            parametric_domain = Segment1D(
                torch.tensor(
                    (value - tol, value + tol), dtype=torch.get_default_dtype()
                )
            )

        surface.from_dim = 0
        parametric_domain.dim = 0

        super().__init__(
            "Point1D", parametric_domain=parametric_domain, surface=surface
        )

        # surface.from_dim = 1
        # parametric_domain.dim = 1

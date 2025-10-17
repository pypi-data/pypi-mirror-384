"""Utility functions to handle velocity domains and values."""

from typing import TYPE_CHECKING, Any, Sequence

import numpy as np
import torch

from scimba_torch.domain.meshless_domain.base import SurfacicDomain, VolumetricDomain

# from scimba_torch.plots.utilities import is_Sequence_float


# if domain_v is a surfacic domain, check if val is in the parametric space
# else ? check if it is in the space?
def is_velocity_value(val: Any, domain_v: SurfacicDomain | VolumetricDomain) -> bool:
    """Check if argument is a valid value in a Surfacic or Volumetric domain.

    Args:
        val: the arg to be checked
        domain_v: a velocity domain

    Returns:
        True if OK
    """
    if isinstance(domain_v, SurfacicDomain):
        return domain_v.is_valid_parametric_point_np(val)
    else:
        if TYPE_CHECKING:
            assert isinstance(domain_v, VolumetricDomain)

        # raise NotImplementedError(
        #     "Volumetric domains for velocities are not supported yet"
        # )
        xx = val if isinstance(val, np.ndarray) else np.array(val, dtype=np.float64)
        # print("xx: ", xx)
        return not domain_v.is_outside_np(xx)


def is_velocity_values(
    val: Any, domain_v: SurfacicDomain | VolumetricDomain | None
) -> bool:
    """Check if argument is a valid value in a Surfacic or Volumetric domain.

    Args:
        val: the arg to be checked
        domain_v: a velocity domain possibly None

    Returns:
        if domain_v is None, True if val is an empty list
        otherwise, True if val is a non-empty list of valid velocity values in domain_v
    """
    if domain_v is None:
        return (
            (not isinstance(val, str)) and isinstance(val, Sequence) and (len(val) == 0)
        )

    if isinstance(val, str) or not isinstance(val, Sequence):
        return False

    if TYPE_CHECKING:
        assert isinstance(domain_v, SurfacicDomain | VolumetricDomain)
        assert isinstance(val, Sequence)

    if len(val) == 0:
        return False

    for v in val:
        if not is_velocity_value(v, domain_v):
            return False

    return True


def get_velocity_value(
    velocity_value: Any, velocity_domain: SurfacicDomain | VolumetricDomain
) -> np.ndarray:
    """Format argument to be a valid velocity value for the sequel.

    Args:
        velocity_value: a (valid) velocity value
        velocity_domain: a (valid) velocity domain

    Returns:
        velocity value as a Sequence[np.ndarray]
    """
    if isinstance(velocity_domain, SurfacicDomain):
        val_t = torch.tensor(velocity_value)[None]
        return velocity_domain.surface(val_t).detach().cpu().numpy()

    else:
        # TODO check if it is a velocity value?
        # raise NotImplementedError(
        #     "Volumetric domains for velocities are not supported yet"
        # )
        return np.array([velocity_value], dtype=np.float64)


def get_velocity_values(
    velocity_values: Any, velocity_domain: SurfacicDomain | VolumetricDomain | None
) -> list[np.ndarray]:
    """Format argument to be a valid list of velocity values for the sequel.

    Args:
        velocity_values: a (valid) velocity values
        velocity_domain: a (valid) velocity domain, possibly None

    Returns:
        if velocity_domain is None, an empty list
        otherwise, velocity values as a list[np.ndarray]
    """
    res: list[np.ndarray] = []

    if velocity_domain is None:
        return res

    if TYPE_CHECKING:
        assert velocity_domain is not None
        assert isinstance(velocity_values, Sequence)

    for velocity_value in velocity_values:
        res.append(get_velocity_value(velocity_value, velocity_domain))

    return res


def is_sequence_of_one_or_n_velocity_values(
    l_velocity_values: Any,
    velocity_domains: Sequence[None | SurfacicDomain | VolumetricDomain],
    n: int,
) -> bool:
    """Check if argument is a sequence of 1 or n points in velocity domains.

    Args:
        l_velocity_values: the arg to be checked
        velocity_domains: a sequence of 1 or n valid velocity domain
        n: n

    Returns:
        if len(velocity_domains)==1,
            True if and l_velocity_values is a sequence of 1 or n points in the domain
        else (len(velocity_domains)==n),
            True if l_velocity_values is 1 valid point in all domains
                 or is n points, the i-th point being a valid point in i-th domain

    Raises:
        ValueError: if velocity_domains is empty
    """
    if len(velocity_domains) == 0:
        raise ValueError("list of velocity domains should not be empty")

    v_index = (lambda i: 0) if len(velocity_domains) == 1 else (lambda i: i)
    return (
        isinstance(l_velocity_values, Sequence)
        and ((len(l_velocity_values) == 1) or (len(l_velocity_values) == n))
        and all(
            is_velocity_values(vv, velocity_domains[v_index(i)])
            for i, vv in enumerate(l_velocity_values)
        )
    )


def get_v_v_str(
    phase_values: np.ndarray, length: int, v_repr: str = ""
) -> tuple[np.ndarray, str]:
    """Compute vector of angles v and string representation v_str.

    Args:
        phase_values: velocity value(s).
        length: Length of the output v array.
        v_repr: string; if not empty, then this is output as v_str

    Returns:
        v : v array.
        v_str : v string representation.
    """
    # print("phase_values.shape: ", phase_values.shape)
    dimv = phase_values.size
    v_shape = (length, dimv)
    # print("v_shape: ", v_shape)
    v = np.ones(v_shape, dtype=np.float64)
    v.shape = v_shape  # in case where phase_values is empty
    if dimv > 0:
        v *= phase_values
    v_str = str(v_repr)
    if len(v_str) == 0:
        if dimv == 1:
            v_str = str(round(phase_values[0].item(), 2))
            # mu_str = "%.2e" % (parameters_values[0].item())
        elif dimv > 1:
            # print(phase_values)
            v_str = str(tuple([round(phase_values[i].item(), 2) for i in range(dimv)]))
    return v, v_str

"""Utility functions to handle time domains and values."""

from typing import Any, Sequence, cast

import numpy as np

from scimba_torch.plots._utils.utilities import (
    _is_sequence_float,
)


def is_time_domain(time_domain: Any) -> bool:
    """Check if argument is a valid time domain.

    Args:
        time_domain: the value to be checked

    Returns:
        True if OK

    """
    return _is_sequence_float(time_domain) and (
        (len(time_domain) == 0)
        or ((len(time_domain) == 2) and (time_domain[0] <= time_domain[1]))
    )


def is_time_domain_empty(time_domain: Any) -> bool:
    """Check if argument is a valid non empty time domain.

    Args:
        time_domain: the value to be checked

    Returns:
        True if OK

    """
    return is_time_domain(time_domain) and (len(time_domain) == 0)


def is_time_values(time_values: Any, time_domain: Sequence[float]) -> bool:
    """Check if argument is a valid (sequence of) time(s) in a time domain.

    Args:
        time_values: the arg to be checked
        time_domain: a (valid) parameters domain

    Returns:
        True if OK

    """
    if is_time_domain_empty(time_domain):
        return (
            (time_values == []) or (time_values == tuple()) or (time_values == "final")
        )

    return (
        (isinstance(time_values, int) and (time_values >= 2))
        or (time_values in ["initial", "final"])
        or (time_values == ["initial", "final"])
        or (
            isinstance(time_values, float)
            # and (time_values >= time_domain[0]) #should only produce a warning?
            # and (time_values <= time_domain[1])
        )
        or (
            _is_sequence_float(time_values)  # should only produce a warning?
            # and all(
            #     ((tv >= time_domain[0]) and (tv <= time_domain[1]))
            #     for tv in time_values
            # )
        )
    )


def get_time_values(
    time_values: Any, time_domain: Sequence[float]
) -> Sequence[np.ndarray]:
    """Format argument to be a valid time values for the sequel.

    Args:
        time_values: a (valid) time values
        time_domain: a (valid) time domain

    Returns:
        time values as a Sequence[np.ndarray]

    """
    res: Sequence[float] = []
    if not is_time_domain_empty(time_domain):
        if isinstance(time_values, int):
            res = cast(
                Sequence[float],
                np.linspace(time_domain[0], time_domain[1], num=time_values).tolist(),
            )
        if time_values == "initial":
            res = [time_domain[0]]
        if time_values == "final":
            res = [time_domain[1]]
        if time_values == ["initial", "final"]:
            res = [time_domain[0], time_domain[1]]
        if isinstance(time_values, float):
            res = [time_values]
        if _is_sequence_float(time_values):
            res = time_values

    return [np.array(t) for t in res]


def is_sequence_of_one_or_n_time_domain(l_time: Any, n: int) -> bool:
    """Check if argument is a sequence of 1 or n valid time domain.

    Args:
        l_time: the value to be checked
        n: n

    Returns:
        True if OK

    """
    return (
        isinstance(l_time, Sequence)
        and ((len(l_time) == 1) or (len(l_time) == n))
        and all(is_time_domain(L) for L in l_time)
    )


def is_one_time_values(time_values: Any, time_domain: Sequence[float]) -> bool:
    """Check if argument is 1 valid time in a time domain.

    Args:
        time_values: the arg to be checked
        time_domain: a (valid) time domain

    Returns:
        True if OK
    """
    if is_time_domain_empty(time_domain):
        return (
            (time_values == []) or (time_values == tuple()) or (time_values == "final")
        )

    return (
        (time_values in ["initial", "final"])
        or (isinstance(time_values, float))
        or (_is_sequence_float(time_values) and (len(time_values) == 1))
    )


def is_sequence_of_one_or_n_time_values(
    l_time_values: Any,
    time_domains: Sequence[Sequence[float]],
    n: int,
) -> bool:
    """Check if argument is a sequence of 1 or n time(s) in time domains.

    Args:
        l_time_values: the arg to be checked
        time_domains: a sequence of 1 or n valid time domains
        n: n

    Returns:
        if len(time_domains)==1,
            True if and l_time_values is a sequence of 1 or n times in the domain
        else (len(time_domains)==n),
            True if l_time_values is 1 valid point in all domains
                 or is n times, the i-th time being a valid time in i-th domain

    """
    t_index = (lambda i: 0) if len(time_domains) == 1 else (lambda i: i)
    # print("l_time_values: ", l_time_values)
    # print("isinstance(l_time_values, Sequence): ",
    #       isinstance(l_time_values, Sequence))
    # print("len(l_time_values): ", len(l_time_values))
    return (
        isinstance(l_time_values, Sequence)
        and ((len(l_time_values) == 1) or (len(l_time_values) == n))
        and all(
            is_one_time_values(L, time_domains[t_index(i)])
            for i, L in enumerate(l_time_values)
        )
    )


def get_t_t_str(time_value: np.ndarray, length: int) -> tuple[np.ndarray, str]:
    """Compute vector of times t and string representation t_str.

    Args:
        time_value: time values
        length: Length of the output t array

    Returns:
        t: t array.
        t_str: t string representation.
    """
    # print("time_value.shape: ", time_value.shape)
    has_time = time_value.size
    t_shape = (length, has_time)
    # print("t_shape: ", t_shape)
    t = np.ones(t_shape, dtype=np.float64)
    t.shape = (length, has_time)
    # print("t_shape: ", t_shape)
    t *= time_value
    # t_str = str(round(time_value.item(), 2))
    t_str = ""
    if has_time:
        t_str = "%.2e" % cast(float, time_value.item())
    return t, t_str

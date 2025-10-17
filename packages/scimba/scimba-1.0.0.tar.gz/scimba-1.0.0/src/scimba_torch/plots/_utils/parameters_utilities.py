"""Utility functions to handle parameters domains and values."""

from typing import Any, Sequence

import numpy as np

from scimba_torch.plots._utils.utilities import (
    _is_sequence_float,
)


def is_parameters_domain(parameters_domain: Any) -> bool:
    """Check if argument is a valid parameters domain.

    Args:
        parameters_domain: the value to be checked

    Returns:
        True if OK
    """
    return isinstance(parameters_domain, Sequence) and all(
        _is_sequence_float(interval)
        and (len(interval) == 2)
        and (interval[0] <= interval[1])
        for interval in parameters_domain
    )


def is_parameters_domain_empty(parameters_domain: Any) -> bool:
    """Check if argument is a valid non empty parameters domain.

    Args:
        parameters_domain: the value to be checked

    Returns:
        True if OK
    """
    return is_parameters_domain(parameters_domain) and (len(parameters_domain) == 0)


def is_parameters_values(
    parameters_values: Any, parameters_domain: Sequence[Sequence[float]]
) -> bool:
    """Check if argument is a valid (sequence of) point(s) in a parameters domain.

    Args:
        parameters_values: the arg to be checked
        parameters_domain: a (valid) parameters domain

    Returns:
        True if OK
    """
    if is_parameters_domain_empty(parameters_domain):
        return (
            (parameters_values == [])
            or (parameters_values == tuple())
            or (parameters_values == "mean")
            or (parameters_values == "random")
        )

    return (
        # (isinstance(parameters_values, int) and (parameters_values >= 2))
        # or
        (parameters_values in ["random", "mean"])
        or (
            _is_sequence_float(parameters_values)
            and len(parameters_values) == len(parameters_domain)
        )
        or (
            isinstance(parameters_values, Sequence)
            and all(
                (
                    _is_sequence_float(parameters_value)
                    and len(parameters_value) == len(parameters_domain)
                )
                for parameters_value in parameters_values
            )
        )
    )


def get_parameters_values(
    parameters_values: Any, parameters_domain: Sequence[Sequence[float]]
) -> Sequence[np.ndarray]:
    """Format argument to be a valid parameters value for the sequel.

    Args:
        parameters_values: a (valid) parameters value
        parameters_domain: a (valid) parameters domain

    Returns:
        parameters values as a Sequence[np.ndarray]
    """
    res = []
    if not is_parameters_domain_empty(parameters_domain):
        if parameters_values == "mean":
            domain_np = np.array(parameters_domain)
            res = [np.mean(np.array(domain_np), axis=-1).tolist()]
        elif parameters_values == "random":
            domain_np = np.array(parameters_domain)
            res = [np.random.uniform(domain_np[:, 0], domain_np[:, 1]).tolist()]
        elif _is_sequence_float(parameters_values):
            res = [parameters_values]
        else:
            res = parameters_values
    return [np.array(t) for t in res]


def is_sequence_of_one_or_n_parameters_domain(l_parameters: Any, n: int) -> bool:
    """Check if argument is a sequence of 1 or n valid parameters domain.

    Args:
        l_parameters: the value to be checked
        n: n

    Returns:
        True if OK
    """
    return (
        isinstance(l_parameters, Sequence)
        and ((len(l_parameters) == 1) or (len(l_parameters) == n))
        and all(is_parameters_domain(L) for L in l_parameters)
    )


def is_one_parameters_values(
    parameters_values: Any, parameters_domain: Sequence[Sequence[float]]
) -> bool:
    """Check if argument is 1 valid point in a parameters domain.

    Args:
        parameters_values: the arg to be checked
        parameters_domain: a (valid) parameters domain

    Returns:
        True if OK
    """
    if is_parameters_domain_empty(parameters_domain):
        return (
            (parameters_values == [])
            or (parameters_values == tuple())
            or (parameters_values == "mean")
            or (parameters_values == "random")
        )

    return (parameters_values in ["random", "mean"]) or (
        _is_sequence_float(parameters_values)
        and len(parameters_values) == len(parameters_domain)
    )


def is_sequence_of_one_or_n_parameters_values(
    l_parameters_values: Any,
    parameters_domains: Sequence[Sequence[Sequence[float]]],
    n: int,
) -> bool:
    """Check if argument is a sequence of 1 or n points in parameters domains.

    Args:
        l_parameters_values: the arg to be checked
        parameters_domains: a sequence of 1 or n valid parameters domain
        n: n

    Returns:
        if len(parameters_domains)==1,
            True if and l_parameters_values is a sequence of 1 or n points in the domain
        else (len(parameters_domains)==n),
            True if l_parameters_values is 1 valid point in all domains
                 or is n points, the i-th point being a valid point in i-th domain
    """
    p_index = (lambda i: 0) if len(parameters_domains) == 1 else (lambda i: i)
    # print("l_parameters_values: ", l_parameters_values)
    # print("isinstance(l_parameters_values, Sequence): ",
    # isinstance(l_parameters_values, Sequence))
    # print("len(l_parameters_values): ", len(l_parameters_values))
    return (
        isinstance(l_parameters_values, Sequence)
        and ((len(l_parameters_values) == 1) or (len(l_parameters_values) == n))
        and all(
            is_one_parameters_values(L, parameters_domains[p_index(i)])
            for i, L in enumerate(l_parameters_values)
        )
    )


def get_mu_mu_str(parameters_values: np.ndarray, length: int) -> tuple[np.ndarray, str]:
    """Compute vector of parameters mu and string representation mu_str.

    Args:
        parameters_values: Parameter values.
        length: Length of the output mu array.

    Returns:
        mu: Mu array.
        mu_str: Mu string representation.
    """
    # print("parameters_values.shape: ", parameters_values.shape)
    nb_parameters = parameters_values.size
    mu_shape = (length, nb_parameters)
    # print("mu_shape: ", mu_shape)
    mu = np.ones(mu_shape, dtype=np.float64)
    mu.shape = (length, nb_parameters)
    if nb_parameters > 0:
        mu *= parameters_values
    mu_str = ""
    if nb_parameters == 1:
        mu_str = str(round(parameters_values[0].item(), 2))
        # mu_str = "%.2e" % (parameters_values[0].item())
    elif nb_parameters > 1:
        mu_str = str(
            tuple([round(parameters_values[i].item(), 2) for i in range(nb_parameters)])
        )
    return mu, mu_str

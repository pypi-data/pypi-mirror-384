"""Private utility functions for checking types of arguments."""

from typing import Any, Sequence

import numpy as np


def _is_sequence_float(i_elem: Any) -> bool:
    """Check if the input is a sequence of floats.

    This function verifies whether the input is a sequence and whether all elements
    within the sequence are floats.

    Args:
        i_elem: The element to check.

    Returns:
        True if the input is a sequence of floats, False otherwise.
    """
    return isinstance(i_elem, Sequence) and all(
        isinstance(elem, float) for elem in i_elem
    )


def _is_list_sequence_float(l_elems: Any) -> bool:
    """Check if the input is a list of sequences of floats.

    This function verifies whether the input is a list and whether all elements
    within the list are sequences of floats.

    Args:
        l_elems: The element to check.

    Returns:
        True if the input is a list of sequences of floats, False otherwise.
    """
    return isinstance(l_elems, list) and all(
        _is_sequence_float(elem) for elem in l_elems
    )


def _is_sequence_list_sequence_float(i_elems: Any) -> bool:
    """Check if the input is a sequence of lists of sequences of floats.

    This function verifies whether the input is a sequence and whether all elements
    within the sequence are lists of sequences of floats.

    Args:
        i_elems: The element to check.

    Returns:
        True if the input is a sequence of lists of sequences of floats,
            False otherwise.
    """
    return isinstance(i_elems, Sequence) and all(
        _is_list_sequence_float(elem) for elem in i_elems
    )


def _is_list_float(i_elem: Any) -> bool:
    """Check if the input is a list of floats.

    This function verifies whether the input is a list and whether all elements
    within the list are floats.

    Args:
        i_elem: The element to check.

    Returns:
        True if the input is a list of floats, False otherwise.
    """
    return isinstance(i_elem, list) and all(isinstance(elem, float) for elem in i_elem)


def _is_sequence_list_float(l_elems: Any) -> bool:
    """Check if the input is a sequence of lists of floats.

    This function verifies whether the input is a sequence and whether all elements
    within the sequence are lists of floats.

    Args:
        l_elems: The element to check.

    Returns:
        True if the input is a sequence of lists of floats, False otherwise.
    """
    return isinstance(l_elems, Sequence) and all(
        _is_list_float(elem) for elem in l_elems
    )


def _is_sequence_str(i_elem: Any) -> bool:
    """Check if the input is a sequence of strings.

    This function verifies whether the input is a sequence and whether all elements
    within the sequence are strings.

    Args:
        i_elem: The element to check.

    Returns:
        True if the input is a sequence of strings, False otherwise.
    """
    return isinstance(i_elem, Sequence) and all(
        isinstance(elem, str) for elem in i_elem
    )


def _is_sequence_str_or_none(i_elem: Any) -> bool:
    """Check if the input is a sequence of strings.

    This function verifies whether the input is a sequence and whether all elements
    within the sequence are strings.

    Args:
        i_elem: The element to check.

    Returns:
        True if the input is a sequence of strings, False otherwise.
    """
    return (
        isinstance(i_elem, Sequence)
        and not isinstance(i_elem, str)
        and all((elem is None) or (isinstance(elem, str)) for elem in i_elem)
    )


def _is_sequence_nparray(l_elem: Any) -> bool:
    """Check if the input is a sequence of Numpy arrays.

    This function verifies whether the input is a sequence and whether all elements
    within the sequence are Numpy arrays.

    Args:
        l_elem: The element to check.

    Returns:
        True if the input is a sequence of Numpy arrays, False otherwise.
    """
    return isinstance(l_elem, Sequence) and all(
        isinstance(L, np.ndarray) for L in l_elem
    )

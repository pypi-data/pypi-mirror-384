"""Utility functions for plot functions."""

from typing import Any, Sequence

import numpy as np

###############################################################
#  utility functions independent from torch and scimba_torch  #
###############################################################


def get_regular_mesh_as_np_meshgrid(
    box: np.ndarray, n_visu: int, indexing: str = "xy"
) -> tuple[np.ndarray[tuple[int, ...], np.dtype[Any]], ...]:
    """Compute a regular mesh in the given box.

    Args:
        box: Box limits.
        n_visu: Number of visualization points per dimension.
        indexing: Indexing scheme to use. Defaults to "xy".

    Returns:
        meshgrid: Regular mesh in the given box.
    """
    dim = box.shape[0]
    linspaces = [np.linspace(box[i, 0], box[i, 1], n_visu) for i in range(dim)]
    return np.meshgrid(*linspaces, indexing=indexing)


def get_regular_mesh_as_np_array(
    box: np.ndarray, n_visu: int, indexing: str = "xy"
) -> np.ndarray:
    """Compute a regular mesh in the given box.

    Args:
        box: Box limits.
        n_visu: Number of visualization points per dimension.
        indexing: Indexing scheme to use. Defaults to "xy".

    Returns:
        meshgrid: Regular mesh in the given box.
    """
    ndim = len(box)
    np_meshgrid = get_regular_mesh_as_np_meshgrid(box, n_visu, indexing=indexing)
    return np.stack(np_meshgrid, axis=-1).reshape((n_visu**ndim, ndim))


def get_np_meshgrid_from_np_array(
    vec_meshgrid: np.ndarray, nvisu: int
) -> tuple[np.ndarray, ...]:
    """Convert a mesh given in a vector to a np.meshgrid object.

    Args:
        vec_meshgrid: Vectorized meshgrid.
        nvisu: Number of visualization points per dimension.

    Returns:
        meshgrid: Regular mesh in the given box.
    """
    ndim = vec_meshgrid.shape[-1]

    return tuple(
        vec_meshgrid.reshape((nvisu,) * ndim + (ndim,))[..., i] for i in range(ndim)
    )


COLORS_LIST = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]
LINESTYLE_LIST = [
    "solid",
    "dotted",
    "dashed",
    "dashdot",
    (0, (1, 1)),  # "densely dotted",
    (0, (5, 1)),  # "densely dashed",
    (0, (3, 1, 1, 1)),  # "densely dashdotted",
    (0, (1, 10)),  # "loosely dotted",
    (0, (5, 10)),  # "loosely dashed",
    (0, (3, 10, 1, 10)),  # "loosely dashdotted",
]


def get_objects_nblines_nbcols(
    xdim: int,
    oneline: bool,
    parameters_values: Sequence[np.ndarray],
    time_values: Sequence[np.ndarray],
    phase_values: Sequence[np.ndarray],
    components: Sequence[int],
    **kwargs,
) -> tuple[list[str], int, int, bool]:
    """Outputs the number of lines and columns and the objects dictionary.

    Args:
        xdim: the geometric dim
        oneline: whether the plot is one line per approximation space
        parameters_values: one or more points in parameters domains
        time_values: one or more time in times domains
        phase_values: one or more points in velocity domains
        components: the indices of the components of the space to be plot
        **kwargs: a dictionary with objects to be plot

    Returns:
        the object dictionary, the number of lines and columns of the plot grid
        and wether the loss history is plot only on the first line or not
    """
    sequences = [parameters_values, time_values, phase_values, components]
    for seq in sequences:
        if len(seq) > 1:
            for seq2 in sequences:
                assert seq2 is seq or len(seq2) <= 1

    nb_max_cols = kwargs.get("nb_max_cols", 4)
    nbcols = 1
    nblines = 1
    objects = ["approximation"]
    nb_axes = 1

    for key in kwargs:
        if key in ["loss"]:
            nb_axes += 1
        if key in ["residual"]:
            nb_axes += 1
        if (key in ["solution"]) and (xdim >= 2):
            nb_axes += 1  # in dim 1 on the same axe as approximation
        if (key in ["error"]) and ((xdim >= 2) or ("residual" not in kwargs)):
            nb_axes += 1
        if (key in ["cuts"]) and (xdim >= 2):
            nb_axes += len(kwargs[key])
        if key in ["derivatives"]:  # non empty dict of the form {"ux":True,"uxx":False}
            if xdim == 1:
                nb_axes += 1  # in dim 1 all derivatives on the same axis
            else:
                nb_axes += len(kwargs["derivatives"])

        if key in ["residual", "solution", "error"]:
            objects.append(key)
        if key == "derivatives":
            if kwargs["derivatives"] is not None:
                for der in kwargs["derivatives"]:
                    if der is not None:
                        objects.append(der)

    # print("nb_axes:", nb_axes)
    if oneline:
        nbcols = nb_axes
        nblines = max(
            len(time_values),
            len(parameters_values),
            len(phase_values),
            len(components),
            1,
        )
    else:
        nbcols = min(nb_max_cols, nb_axes)
        nblines = int(np.ceil(nb_axes / nbcols))

    loss_only_on_first_line = (
        (len(parameters_values) > 1)
        or (len(time_values) > 1)
        or (len(phase_values) > 1)
        or (len(components) > 1)
    )
    return objects, nblines, nbcols, loss_only_on_first_line


if __name__ == "__main__":  # pragma: no cover

    def _get_ith_component_of_meshgrid(
        i: int, box: np.ndarray, n_visu: int, indexing: str = "xy"
    ):
        """Compute ith component of meshgrid.

        Args:
            i: Index of the component.
            box: Box limits.
            n_visu: Number of visualization points per dimension.
            indexing: Indexing scheme to use. Defaults to "xy".

        Returns:
            ith_component: Ith component of meshgrid.

        Raises:
            ValueError: in case of bad indexing arguments
        """
        ndim = len(box)
        s0 = (1,) * ndim
        reshape_arg = s0[:i] + (-1,) + s0[i + 1 :]
        # print("reshape_arg: ", reshape_arg)
        if indexing not in ["xy", "ij"]:
            raise ValueError("Valid values for `indexing` are 'xy' and 'ij'.")
        if ndim > 1 and indexing == "xy":
            reshape_arg_l = list(reshape_arg)
            reshape_arg_l[0], reshape_arg_l[1] = reshape_arg_l[1], reshape_arg_l[0]
            reshape_arg = tuple(reshape_arg_l)
            # print("reshape_arg: ", reshape_arg)
        return np.ones((n_visu,) * ndim) * np.linspace(
            box[i, 0], box[i, 1], n_visu
        ).reshape(reshape_arg)

    interval = np.array([[0.0, 1.0]])
    n_visu = 3
    x = get_regular_mesh_as_np_array(interval, n_visu)
    # print(x)
    (x1,) = get_regular_mesh_as_np_meshgrid(interval, n_visu)
    (y1,) = get_np_meshgrid_from_np_array(x, n_visu)
    assert np.all(x1 == y1)

    box = np.array([[0.0, 1.0], [1.0, 2.0]])
    n_visu = 3
    x = get_regular_mesh_as_np_array(box, n_visu)
    x1, x2 = get_regular_mesh_as_np_meshgrid(box, n_visu, indexing="xy")
    y1 = _get_ith_component_of_meshgrid(0, box, n_visu)
    y2 = _get_ith_component_of_meshgrid(1, box, n_visu)
    assert np.all(y1 == x1) and np.all(y2 == x2)
    x = get_regular_mesh_as_np_array(box, n_visu)
    (y1, y2) = get_np_meshgrid_from_np_array(x, n_visu)
    assert np.all(y1 == x1) and np.all(y2 == x2)

    box = np.array([[0.0, 1.0], [1.0, 2.0], [2.0, 3.0]])
    n_visu = 3
    x = get_regular_mesh_as_np_array(box, n_visu)
    x1, x2, x3 = get_regular_mesh_as_np_meshgrid(box, n_visu, indexing="xy")
    y1 = _get_ith_component_of_meshgrid(0, box, n_visu)
    y2 = _get_ith_component_of_meshgrid(1, box, n_visu)
    y3 = _get_ith_component_of_meshgrid(2, box, n_visu)
    assert np.all(y1 == x1) and np.all(y2 == x2) and np.all(y3 == x3)
    x = get_regular_mesh_as_np_array(box, n_visu)
    (y1, y2, y3) = get_np_meshgrid_from_np_array(x, n_visu)
    assert np.all(y1 == x1) and np.all(y2 == x2) and np.all(y3 == x3)

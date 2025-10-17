"""Utility functions for 2D plot functions."""

from typing import Any, cast

import numpy as np

from scimba_torch.plots._utils.plots_utilities import COLORS_LIST, LINESTYLE_LIST


def _get_np_vect_from_cut_2d(
    box: np.ndarray, point: np.ndarray, normal: np.ndarray, n_visu: int
) -> np.ndarray:
    """Generate a 2D vector representation of a line segment within a specified box.

    This function calculates the coordinates of a line segment that passes through a
    given point and is perpendicular to a specified normal vector. The line segment is
    constrained within a rectangular box defined by its minimum and maximum coordinates.

    Args:
        box: A 2x2 array representing the bounding box. The first row contains the
            minimum and maximum x-coordinates, and the second row contains the minimum
            and maximum y-coordinates.
        point: A 1D array of length 2 representing the (x, y) coordinates of the point
            through which the line segment passes.
        normal: A 1D array of length 2 representing the normal vector to the line
            segment. This vector must be a unit vector (i.e., have a norm of 1).
        n_visu: The number of points to generate along the line segment for
            visualization purposes.

    Returns:
        A 2D array of shape (n_visu, 2) containing the (x, y) coordinates of the
        points along the line segment.

    Raises:
        ValueError: If the normal vector is not a unit vector.

    Note:
        The function parameterizes the line segment by either x or y, depending on
        which component of the normal vector has the larger absolute value. The
        coordinates are flipped if necessary to ensure they are in the correct order.
    """
    # verify that normal has norm +/- 1.
    if not np.isclose(np.linalg.norm(normal), 1.0):
        raise ValueError(
            "in get_np_vect_from_cut_2d: normal vector must be a unit vector"
        )
    if np.abs(normal[1]) > np.abs(normal[0]):  # parameterize by x
        x = np.linspace(box[0, 0], box[0, 1], n_visu)
        y = point[1] - (normal[0] / normal[1]) * (x - point[0])
    else:  # parameterize by y
        y = np.linspace(box[1, 0], box[1, 1], n_visu)
        x = point[0] - (normal[1] / normal[0]) * (y - point[1])
    if (np.isclose(x[0], x[-1]) and y[0] > y[-1]) or (x[0] > x[-1]):
        x = np.flip(x)
        y = np.flip(y)
    return np.stack((x, y), axis=-1)


def _plot_2d_contourf(
    fig,
    axe,
    mesh: tuple[np.ndarray[tuple[int, ...], np.dtype[Any]], ...],
    vals: np.ndarray,
    mask: np.ndarray,
    object: str,
    t_str: str,
    v_str: str,
    mu_str: str,
    **kwargs,
):
    n_visu = kwargs.get("n_visu", 512)
    limit_residual = kwargs.get("limit_residual", 1.0)
    colormap = kwargs.get("colormap", "turbo")
    n_contour = kwargs.get("n_contour", 256)
    draw_contours = kwargs.get("draw_contours", False)
    n_drawn_contours = kwargs.get("n_drawn_contours", 10)

    aspect = kwargs.get("aspect", "equal")

    cuts_data = kwargs.get("cuts_data", [])
    linestyle_dict = kwargs.get("linestyle_dict", {"approximation": LINESTYLE_LIST[0]})

    vals = vals.reshape((n_visu, n_visu))
    values = np.ma.array(vals, mask=mask)

    # title = object + ", params: " + mu_str
    title = object
    if len(t_str) > 0:
        title += r", $t$=" + t_str
    if len(v_str) > 0:
        title += r", $v$=" + v_str
    if len(mu_str) > 0:
        title += r", $\mu$=" + mu_str

    if object in ["error", "residual"]:
        values = cast(np.ma.MaskedArray, values)
        norm = (values**2).mean() ** 0.5
        # print("nb of non masked elements: ", values.count())
        title += ", $L^2$ norm: %.2e" % norm
    # if colormap == "custom":
    #    colormap = make_colormap()
    vmax = values.max() * limit_residual if object == "residual" else None

    im = axe.contourf(
        mesh[0],
        mesh[1],
        values,
        n_contour,
        vmax=vmax,
        cmap=colormap,
        zorder=-9,
    )
    if draw_contours:
        axe.contour(
            im,
            levels=im.levels[:: n_contour // n_drawn_contours],
            zorder=-9,
            colors="white",
            alpha=0.5,
            linewidths=0.8,
        )

    for i, cut_data in enumerate(cuts_data):
        cut_mesh, cut_mask = cut_data[0], cut_data[2]
        cut_mask = np.stack((cut_mask, cut_mask), axis=-1)
        cut_mesh = np.ma.array(cut_mesh, mask=cut_mask)
        axe.plot(
            cut_mesh[:, 0],
            cut_mesh[:, 1],
            color=COLORS_LIST[i],
            linestyle=linestyle_dict[object],
        )

    fig.colorbar(im, ax=axe)
    axe.set_title(f"{title}")
    axe.set_aspect(aspect)


def _plot_2d_cut_values(fig, axe, cut_data, color, index, linestyles_dict, **kwargs):
    cut_vals, cut_mask = cut_data[1], cut_data[2]
    for key in cut_vals:
        y_vals = np.ma.array(cut_vals[key], mask=cut_mask)
        x_vals = np.linspace(0, 1, cut_vals[key].shape[0])

        axe.plot(
            x_vals,
            y_vals,
            color=color,
            linestyle=linestyles_dict[key],
            label=key,
        )
    axe.set_xlabel("")
    axe.set_xticks([])
    # axe.legend()
    axe.set_title("cut %d" % (index + 1))


if __name__ == "__main__":  # pragma: no cover
    box = np.array([[0.0, 1.0], [0.0, 1.0]])
    n_visu = 10
    x = _get_np_vect_from_cut_2d(
        box, np.array([0.0, 0.5]), np.array([0.0, 1.0]), n_visu
    )
    print("x: ", x)
    x = _get_np_vect_from_cut_2d(
        box, np.array([0.5, 0.0]), np.array([1.0, 0.0]), n_visu
    )
    print("x: ", x)
    x = _get_np_vect_from_cut_2d(
        box, np.array([0.0, 0.5]), np.array([1.0, 1.0]) / np.sqrt(2.0), n_visu
    )
    print("x: ", x)

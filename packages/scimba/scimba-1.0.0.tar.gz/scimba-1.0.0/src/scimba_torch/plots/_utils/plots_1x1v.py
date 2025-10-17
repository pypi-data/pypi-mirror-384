"""Plot functions for 2D (1 geometric 1 velocity) spaces."""

import warnings
from typing import Any, Sequence

import matplotlib.pyplot as plt
import numpy as np

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.domain.meshless_domain.base import VolumetricDomain
from scimba_torch.plots._utils.eval_utilities import eval_on_np_tensors
from scimba_torch.plots._utils.parameters_utilities import get_mu_mu_str
from scimba_torch.plots._utils.plots_2d_utilities import (
    _get_np_vect_from_cut_2d,
    _plot_2d_contourf,
    _plot_2d_cut_values,
)
from scimba_torch.plots._utils.plots_utilities import (
    COLORS_LIST,
    LINESTYLE_LIST,
    get_objects_nblines_nbcols,
    get_regular_mesh_as_np_array,
    get_regular_mesh_as_np_meshgrid,
)
from scimba_torch.plots._utils.time_utilities import get_t_t_str


def _get_mesh_and_mask_and_labels_for_1x1v_plot(
    spatial_domain: VolumetricDomain,
    velocity_domain: VolumetricDomain,  # TODO: accept Surfacic Parameterized Domains
    # parameters_values: list[float],
    n_visu: int,
) -> tuple[
    tuple[np.ndarray, np.ndarray],
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    ebbs = spatial_domain.get_extended_bounds_postmap(0.05)
    ebbv = velocity_domain.get_extended_bounds_postmap(0.05)
    ebb = np.concatenate((ebbs, ebbv), axis=0)

    x_mesh, y_mesh = get_regular_mesh_as_np_meshgrid(ebb, n_visu)
    # get xy vector and mask
    xy = get_regular_mesh_as_np_array(ebb, n_visu)

    labels = np.zeros(n_visu**2, dtype=np.int32)

    if spatial_domain.is_mapped or velocity_domain.is_mapped:
        raise NotImplementedError(
            "mapped spatial_domain or velocity_domain not implemented yet"
        )

    else:
        mask_spatial = spatial_domain.is_outside_postmap_np(xy[:, 0])
        mask_velocity = velocity_domain.is_outside_postmap_np(xy[:, 1])
        mask = mask_spatial | mask_velocity
        for i, subdomain in enumerate(spatial_domain.list_subdomains):
            condition = subdomain.is_inside_postmap_np(xy[:, 0])
            labels[condition] = i + 1

    return ((x_mesh, y_mesh), xy, mask, labels)


def _get_meshes_and_masks_for_1x1v_cuts(
    spatial_domain: VolumetricDomain,
    velocity_domain: VolumetricDomain,  # TODO: accept Surfacic Parameterized Domains
    # parameters_values: list[float],
    cuts: np.ndarray,
    n_visu: int,
):
    points, normals = cuts[:, 0, :], cuts[:, 1, :]
    norms = np.linalg.norm(normals, axis=-1)
    if np.any(np.isclose(norms, 0.0)):
        raise ValueError("2 norm of normal vector must be not close to 0")
    normals /= norms[:, None]

    # tol = 5e-2
    # KDT_l: list[Any] = []
    # m_is_empty = np.vectorize(lambda lis: len(lis) == 0)
    if spatial_domain.is_mapped or velocity_domain.is_mapped:
        raise NotImplementedError(
            "mapped spatial_domain or velocity_domain not implemented yet"
        )

    ebbs = spatial_domain.get_extended_bounds_postmap(0.05)
    ebbv = velocity_domain.get_extended_bounds_postmap(0.05)
    ebb = np.concatenate((ebbs, ebbv), axis=0)
    meshes_and_masks = []
    for i in range(len(cuts)):
        mesh = _get_np_vect_from_cut_2d(ebb, points[i, ...], normals[i, ...], n_visu)
        # if spatial_domain.is_mapped:
        #     assert spatial_domain.mapping is not None  # for type checking
        #     if not spatial_domain.mapping.is_invertible:
        #         # create the mask from the KDTree
        #         indexes = KDT_l[0].query_ball_point(mesh, tol)
        #         mask = m_is_empty(indexes)
        #         # print("mask.shape: ", mask.shape)
        #     else:
        #         mask = spatial_domain.is_outside_postmap_np(mesh)
        # else:

        mask_spatial = spatial_domain.is_outside_postmap_np(mesh[:, 0])
        mask_velocity = velocity_domain.is_outside_postmap_np(mesh[:, 1])
        mask = mask_spatial | mask_velocity
        meshes_and_masks.append((mesh, mask))

    return meshes_and_masks


def _get_cut_object_linestyle_dict(objects: list[str]) -> dict:
    res = {"approximation": LINESTYLE_LIST[0]}
    if len(objects) > len(LINESTYLE_LIST):
        warnings.warn(
            "in plots_1x1v.py: no more than %d objects can be plot on cuts "
            "(%d asked); only the first %d will be plotted on cuts"
            % (len(LINESTYLE_LIST), len(objects), len(LINESTYLE_LIST)),
            UserWarning,
        )
    for i, object in enumerate(objects):
        if i < len(LINESTYLE_LIST):
            res[object] = LINESTYLE_LIST[i]
    return res


def __plot_1x1v_abstract_approx_space(
    fig,
    space: AbstractApproxSpace,
    spatial_domain: VolumetricDomain,
    velocity_domain: VolumetricDomain,
    parameters_values: Sequence[np.ndarray],
    time_values: Sequence[np.ndarray],
    components: Sequence[int],
    oneline: bool,
    **kwargs,
):
    objects, nblines, nbcols, loss_only_on_first_line = get_objects_nblines_nbcols(
        2,  # dimension
        oneline,
        parameters_values,
        time_values,
        [],
        components,
        **kwargs,
    )

    # print("oneline: ", oneline)
    # print("parameters_values: ", parameters_values)
    # print("loss_only_on_first_line: ", loss_only_on_first_line)
    # print("nblines: %d, nbcols: %d" % (nblines, nbcols))
    # print("objects: ", objects)
    # print("input kwargs: ", kwargs)

    # dictionary of symbols for eval and derivatives
    symb_dict = {
        "components": ["u"],
        "space_variables": ["x"],
        "phase_variables": ["v"],
    }

    time_discrete = kwargs.get("time_discrete", False)
    assert (len(time_values) == 0) or time_discrete
    # if len(time_values) > 0: #NotImplemented
    # symb_dict["time_variable"] = ["t"]

    if len(parameters_values) == 0:
        parameters_values = [np.array([])]
    if len(time_values) == 0:
        time_values = [np.array([])]

    # default_velocity_strs = ["" for _ in velocity_values]
    # velocity_strs = kwargs.get("velocity_strs", default_velocity_strs)
    # velocity_strs = []

    list_to_explore = parameters_values
    if len(time_values) > 1:
        list_to_explore = time_values
    if len(components) > 1:
        list_to_explore = components

    n_visu = kwargs.get("n_visu", 512)
    mesh_and_mask_and_labels = _get_mesh_and_mask_and_labels_for_1x1v_plot(
        spatial_domain, velocity_domain, n_visu
    )

    mus_mu_strs = [
        get_mu_mu_str(parameters_values[i], n_visu**2)
        for i in range(len(parameters_values))
    ]
    # print(mus_mu_strs)
    ts_t_strs = [
        get_t_t_str(time_values[i], n_visu**2) for i in range(len(time_values))
    ]
    # vs_v_strs = [ ]
    # p_index = (lambda i: 0) if len(parameters_values) == 1 else (lambda i: i)
    m_index = (lambda i: 0) if len(mus_mu_strs) == 1 else (lambda i: i)
    t_index = (lambda i: 0) if len(ts_t_strs) == 1 else (lambda i: i)
    # v_index = (lambda i: 0) if len(vs_v_strs) == 1 else (lambda i: i)
    c_index = (lambda i: 0) if len(components) == 1 else (lambda i: i)

    kwargs_for_eval = {}
    for key in ["solution", "error", "residual"]:
        if key in kwargs and kwargs[key] is not None:
            kwargs_for_eval[key] = kwargs[key]
    for key in ["derivatives"]:
        if key in kwargs and kwargs[key] is not None:
            kwargs_for_eval[key] = []
            for der in kwargs[key]:
                if der is not None:
                    kwargs_for_eval[key].append(der)
    if "time_discrete" in kwargs:
        kwargs_for_eval["time_discrete"] = True

    evals = [
        eval_on_np_tensors(
            space,
            ts_t_strs[t_index(i)][0],
            mesh_and_mask_and_labels[1][:, 0:1],
            mesh_and_mask_and_labels[1][:, 1:2],
            mus_mu_strs[m_index(i)][0],
            symb_dict,
            components[c_index(i)],
            labelsx=mesh_and_mask_and_labels[-1],
            **kwargs_for_eval,
        )
        for i in range(len(list_to_explore))
    ]

    cuts_data_for_plots: Sequence[Any] = [[] for _ in range(len(list_to_explore))]
    cut_object_linestyle_dict = _get_cut_object_linestyle_dict(objects)
    if "cuts" in kwargs:
        cuts = np.array(kwargs["cuts"])
        if cuts.ndim == 2:
            cuts = cuts[None, :, :]
        cuts_meshes_and_masks = _get_meshes_and_masks_for_1x1v_cuts(
            spatial_domain, velocity_domain, cuts, n_visu
        )
        mu_cuts = [
            get_mu_mu_str(parameters_values[i], n_visu)[0]
            for i in range(len(parameters_values))
        ]
        t_cuts = [
            get_t_t_str(time_values[i], n_visu)[0] for i in range(len(time_values))
        ]
        # v_cuts = [ ]
        # if len(t_cuts) == 0:
        #     t_cuts.append(np.array([]))
        for i in range(len(list_to_explore)):
            for j in range(len(cuts_meshes_and_masks)):
                eval = eval_on_np_tensors(
                    space,
                    t_cuts[t_index(i)],
                    cuts_meshes_and_masks[j][0][:, 0:1],
                    cuts_meshes_and_masks[j][0][:, 1:2],
                    mu_cuts[m_index(i)],
                    symb_dict,
                    components[c_index(i)],
                    **kwargs_for_eval,
                )
                data = (
                    cuts_meshes_and_masks[j][0],
                    eval,
                    cuts_meshes_and_masks[j][1],
                )
                cuts_data_for_plots[i].append(data)

    axe_index = 1
    for i in range(len(list_to_explore)):
        if "loss" in kwargs:
            if (i == 0) or (not loss_only_on_first_line):
                if kwargs["loss"] is not None:
                    axe_losses = fig.add_subplot(nblines, nbcols, axe_index)
                    losses = kwargs["loss"]
                    losses.plot(axe_losses, **kwargs)
            axe_index += 1

        for key in objects:
            if key in evals[i]:
                # print("axe_index: ", axe_index)
                n_axe = fig.add_subplot(nblines, nbcols, axe_index)
                _plot_2d_contourf(
                    fig,
                    n_axe,
                    mesh_and_mask_and_labels[0],
                    evals[i][key],
                    mesh_and_mask_and_labels[2],
                    key,
                    ts_t_strs[t_index(i)][1],
                    "",
                    mus_mu_strs[m_index(i)][1],
                    cuts_data=cuts_data_for_plots[i],
                    linestyle_dict=cut_object_linestyle_dict,
                    **kwargs,
                )
                n_axe.set_xlabel("$x$")
                n_axe.set_ylabel("$v$")
            axe_index += 1

        for j in range(len(cuts_data_for_plots[i])):
            axe_cut = fig.add_subplot(nblines, nbcols, axe_index)
            _plot_2d_cut_values(
                fig,
                axe_cut,
                cuts_data_for_plots[i][j],
                COLORS_LIST[j],
                j,
                cut_object_linestyle_dict,
            )
            axe_index += 1

    plt.gca().set_rasterization_zorder(-1)

    # fig.tight_layout()

"""Plot functions for 2D (geometric dim) spaces."""

import warnings
from typing import Any, Sequence

# import torch
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import KDTree

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.domain.meshless_domain.base import VolumetricDomain
from scimba_torch.integration.monte_carlo import DomainSampler
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
from scimba_torch.plots._utils.velocity_utilities import get_v_v_str


def _get_mesh_and_mask_and_labels_for_2d_plot(
    spatial_domain: VolumetricDomain,
    # parameters_values: list[float],
    n_visu: int,
) -> tuple[
    tuple[np.ndarray, np.ndarray],
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    ebb = spatial_domain.get_extended_bounds_postmap(0.05)
    x_mesh, y_mesh = get_regular_mesh_as_np_meshgrid(ebb, n_visu)
    # get xy vector and mask
    xy = get_regular_mesh_as_np_array(ebb, n_visu)

    labels = np.zeros(n_visu**2, dtype=np.int32)

    if spatial_domain.is_mapped:
        assert spatial_domain.mapping is not None  # for type checking
        if not spatial_domain.mapping.is_invertible:
            tol = 1e-2
            m_is_empty = np.vectorize(lambda lis: len(lis) == 0)
            # construct a KDTree from a point cloud sampled on the domain
            sampler = DomainSampler(spatial_domain)
            sample = sampler.sample(n_visu * n_visu)
            p_cloud = sample.x.detach().cpu().numpy()
            labels = sample.labels.detach().cpu().numpy()
            # plt.scatter(p_cloud[:, 0], p_cloud[:, 1], marker=".")
            # plt.show()
            KDT = KDTree(p_cloud)
            indexes = KDT.query_ball_point(xy, tol)
            mask = m_is_empty(indexes)
            # print("mask.shape: ", mask.shape)
        else:
            mask = spatial_domain.is_outside_postmap_np(xy)
            for i, subdomain in enumerate(spatial_domain.list_subdomains):
                condition = subdomain.is_inside_postmap_np(xy)
                labels[condition] = i + 1

    # alternative: construct a mesh of the not mapped domain, get mask,
    # then map the mesh
    # ebb = spatial_domain.get_extended_bounds(0.05)
    # xy = get_regular_mesh_as_np_array(ebb, n_visu)
    # mask = spatial_domain.is_outside_np(xy)
    # xy = (
    #    spatial_domain.mapping(torch.tensor(xy, dtype=torch.get_default_dtype()))
    #    .detach()
    #    .cpu()
    #    .numpy()
    # )
    # xyr = xy.reshape((n_visu, n_visu, 2), copy=True)
    # x_mesh = xyr[:, :, 0]
    # y_mesh = xyr[:, :, 1]

    else:
        mask = spatial_domain.is_outside_postmap_np(xy)
        for i, subdomain in enumerate(spatial_domain.list_subdomains):
            condition = subdomain.is_inside_postmap_np(xy)
            labels[condition] = i + 1

    return ((x_mesh, y_mesh), xy, mask, labels)


def _get_meshes_and_masks_for_2d_cuts(
    spatial_domain: VolumetricDomain,
    # parameters_values: list[float],
    cuts: np.ndarray,
    n_visu: int,
):
    points, normals = cuts[:, 0, :], cuts[:, 1, :]
    norms = np.linalg.norm(normals, axis=-1)
    if np.any(np.isclose(norms, 0.0)):
        raise ValueError(
            "in get_meshes_and_masks_for_2d_cuts: 2 norm of normal vector must be not "
            "close to 0"
        )
    normals /= norms[:, None]

    tol = 5e-2
    KDT_l: list[Any] = []
    m_is_empty = np.vectorize(lambda lis: len(lis) == 0)
    if spatial_domain.is_mapped:
        assert spatial_domain.mapping is not None  # for type checking
        if not spatial_domain.mapping.is_invertible:
            # construct a KDTree from a point cloud sampled on the domain
            sampler = DomainSampler(spatial_domain)
            p_cloud = (sampler.sample(n_visu * n_visu)).x.detach().cpu().numpy()
            KDT_l.append(KDTree(p_cloud))

    ebb = spatial_domain.get_extended_bounds_postmap(0.05)
    meshes_and_masks = []
    for i in range(len(cuts)):
        mesh = _get_np_vect_from_cut_2d(ebb, points[i, ...], normals[i, ...], n_visu)
        if spatial_domain.is_mapped:
            assert spatial_domain.mapping is not None  # for type checking
            if not spatial_domain.mapping.is_invertible:
                # create the mask from the KDTree
                indexes = KDT_l[0].query_ball_point(mesh, tol)
                mask = m_is_empty(indexes)
                # print("mask.shape: ", mask.shape)
            else:
                mask = spatial_domain.is_outside_postmap_np(mesh)
        else:
            mask = spatial_domain.is_outside_postmap_np(mesh)
        meshes_and_masks.append((mesh, mask))

    return meshes_and_masks


def _get_cut_object_linestyle_dict(objects: list[str]) -> dict:
    res = {"approximation": LINESTYLE_LIST[0]}
    if len(objects) > len(LINESTYLE_LIST):
        warnings.warn(
            f"in plots_2d.py: no more than {len(LINESTYLE_LIST)} objects can be plot "
            f"on cuts ({len(objects)} asked); only the first {len(LINESTYLE_LIST)} "
            f"will be plotted on cuts",
            UserWarning,
        )
    for i, object in enumerate(objects):
        if i < len(LINESTYLE_LIST):
            res[object] = LINESTYLE_LIST[i]
    return res


def __plot_2x_abstract_approx_space(
    fig,
    space: AbstractApproxSpace,
    spatial_domain: VolumetricDomain,
    parameters_values: Sequence[np.ndarray],
    time_values: Sequence[np.ndarray],
    velocity_values: Sequence[np.ndarray],
    components: Sequence[int],
    oneline: bool,
    **kwargs,
):
    objects, nblines, nbcols, loss_only_on_first_line = get_objects_nblines_nbcols(
        spatial_domain.dim,
        oneline,
        parameters_values,
        time_values,
        velocity_values,
        components,
        **kwargs,
    )

    # print("oneline: ", oneline)
    # print("parameters_values: ", parameters_values)
    # print("velocity_values: ", velocity_values)
    # print("loss_only_on_first_line: ", loss_only_on_first_line)
    # print("nblines: %d, nbcols: %d" % (nblines, nbcols))
    # print("objects: ", objects)
    # print("input kwargs: ", kwargs)

    # dictionary of symbols for eval and derivatives
    symb_dict = {
        "components": ["u"],
        "space_variables": ["x", "y"],
    }
    if len(time_values) > 0:
        symb_dict["time_variable"] = ["t"]
    if len(velocity_values) > 0:
        nbvelocity_variables = velocity_values[0].shape[-1]
        velocity_variables = ["v" + str(i) for i in range(nbvelocity_variables)]
        symb_dict["phase_variables"] = velocity_variables
    # print("symb_dict: ", symb_dict)

    if len(parameters_values) == 0:
        parameters_values = [np.array([])]
    if len(time_values) == 0:
        time_values = [np.array([])]
    if len(velocity_values) == 0:
        velocity_values = [np.array([])]

    default_velocity_strs = ["" for _ in velocity_values]
    velocity_strs = kwargs.get("velocity_strs", default_velocity_strs)

    # assert not (
    #     ((len(parameters_values) > 1) and (len(time_values) > 1))
    #     or ((len(parameters_values) > 1) and (len(velocity_values) > 1))
    #     or ((len(time_values) > 1) and (len(velocity_values) > 1))
    # )

    list_to_explore = parameters_values
    if len(time_values) > 1:
        list_to_explore = time_values
    if len(velocity_values) > 1:
        list_to_explore = velocity_values
    if len(components) > 1:
        list_to_explore = components

    n_visu = kwargs.get("n_visu", 512)
    mesh_and_mask_and_labels = _get_mesh_and_mask_and_labels_for_2d_plot(
        spatial_domain, n_visu
    )

    mus_mu_strs = [
        get_mu_mu_str(parameters_values[i], n_visu**2)
        for i in range(len(parameters_values))
    ]
    # print(mus_mu_strs)
    ts_t_strs = [
        get_t_t_str(time_values[i], n_visu**2) for i in range(len(time_values))
    ]
    vs_v_strs = [
        get_v_v_str(velocity_values[i], n_visu**2, velocity_strs[i])
        for i in range(len(velocity_values))
    ]
    # p_index = (lambda i: 0) if len(parameters_values) == 1 else (lambda i: i)
    m_index = (lambda i: 0) if len(mus_mu_strs) == 1 else (lambda i: i)
    t_index = (lambda i: 0) if len(ts_t_strs) == 1 else (lambda i: i)
    v_index = (lambda i: 0) if len(vs_v_strs) == 1 else (lambda i: i)
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
            mesh_and_mask_and_labels[1],
            vs_v_strs[v_index(i)][0],
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
        cuts_meshes_and_masks = _get_meshes_and_masks_for_2d_cuts(
            spatial_domain, cuts, n_visu
        )
        mu_cuts = [
            get_mu_mu_str(parameters_values[i], n_visu)[0]
            for i in range(len(parameters_values))
        ]
        t_cuts = [
            get_t_t_str(time_values[i], n_visu)[0] for i in range(len(time_values))
        ]
        v_cuts = [
            get_v_v_str(velocity_values[i], n_visu)[0]
            for i in range(len(velocity_values))
        ]
        # if len(t_cuts) == 0:
        #     t_cuts.append(np.array([]))
        for i in range(len(list_to_explore)):
            for j in range(len(cuts_meshes_and_masks)):
                eval = eval_on_np_tensors(
                    space,
                    t_cuts[t_index(i)],
                    cuts_meshes_and_masks[j][0],
                    v_cuts[v_index(i)],
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
                    vs_v_strs[v_index(i)][1],
                    mus_mu_strs[m_index(i)][1],
                    cuts_data=cuts_data_for_plots[i],
                    linestyle_dict=cut_object_linestyle_dict,
                    **kwargs,
                )
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


# def get_objects_nblines_nbcols(
#     spaces: list[AbstractApproxSpace],
#     parameters_values: list[np.ndarray],
#     **kwargs,
# ) -> tuple[list[str], int, int]:
#     nb_max_cols = kwargs.get("nb_max_cols", 4)
#     nbcols = 1
#     nblines = 1
#     objects = ["approximation"]
#     nb_axes_per_line = 1

#     if "loss" in kwargs:
#         nb_axes_per_line += 1
#     if "residual" in kwargs:
#         nb_axes_per_line += 1
#         objects.append("residual")
#     if "solution" in kwargs:
#         nb_axes_per_line += 1
#         objects.append("solution")
#     if "error" in kwargs:
#         nb_axes_per_line += 1
#         objects.append("error")
#     if "cuts" in kwargs:
#         nb_axes_per_line += len(kwargs["cuts"])
#     if "derivatives" in kwargs:
#         nb_axes_per_line += len(kwargs["derivatives"])
#         objects += kwargs["derivatives"]

#     if (len(spaces) == 1) and (len(parameters_values) == 1):
#         nbcols = min(nb_max_cols, nb_axes_per_line)
#         nblines = int(np.ceil(nb_axes_per_line / nbcols))
#     else:
#         nbcols = nb_axes_per_line
#         nblines = len(spaces)
#         if (nblines == 1) and (len(parameters_values) > 1):
#             nblines = len(parameters_values)

#     loss_only_on_first_line = (len(spaces) == 1) and (len(parameters_values) > 1)

#     return objects, nblines, nbcols, loss_only_on_first_line

# def __plot_2x_AbstractApproxSpaces(
#     spaces: list[AbstractApproxSpace],
#     spatial_domains: list[VolumetricDomain],
#     parameters_values: list[np.ndarray],
#     **kwargs,
# ):
#     objects, nblines, nbcols, loss_only_on_first_line = get_objects_nblines_nbcols(
#         spaces, parameters_values, **kwargs
#     )
#     sizeofobjects = [4, 3]

#     # dictionary of symbols for eval and derivatives
#     symb_dict = {
#         "components": ["u"],
#         # "time_variable": ["t"],
#         "space_variables": ["x", "y"],
#     }

#     list_to_explore = spaces
#     if (len(spaces) == 1) and (len(parameters_values) > 1):
#         list_to_explore = parameters_values

#     # print(parameters_domains)
#     # parameters_values = get_parameters_values(parameters_domains, **kwargs)
#     # print("parameters values: ", parameters_values)

#     s_index = (lambda i: 0) if len(spaces) == 1 else (lambda i: i)
#     # check len of parameters_values ? need an nb_parameters attribute in
#     # abstract_approx_space...
#     p_index = (lambda i: 0) if len(parameters_values) == 1 else (lambda i: i)

#     n_visu = kwargs.get("n_visu", 512)
#     meshes_and_masks = [
#         get_mesh_and_mask_for_2d_plot(spatial_domains[i], n_visu)
#         for i in range(len(spatial_domains))
#     ]
#     mus_mu_strs = [
#         get_mu_mu_str(parameters_values[i], n_visu**2)
#         for i in range(len(parameters_values))
#     ]
#     # print("mu.shape: ", mus_mu_strs[0][0].shape)
#     d_index = (lambda i: 0) if len(spatial_domains) == 1 else (lambda i: i)
#     x_index = (lambda i: 0) if len(meshes_and_masks) == 1 else (lambda i: i)
#     m_index = (lambda i: 0) if len(mus_mu_strs) == 1 else (lambda i: i)

#     list_of_kwargs_for_eval = []
#     for i in range(0, len(list_to_explore)):
#         list_of_kwargs_for_eval.append({})
#         for key in ["solution", "error", "residual"]:
#             if key in kwargs:
#                 if isinstance(kwargs[key], Iterable):
#                     if len(kwargs[key]) == 1:
#                         list_of_kwargs_for_eval[-1][key] = kwargs[key][0]
#                     elif kwargs[key][i] is not None:
#                         list_of_kwargs_for_eval[-1][key] = kwargs[key][i]
#                 else:
#                     list_of_kwargs_for_eval[-1][key] = kwargs[key]
#         if "derivatives" in kwargs:
#             key = "derivatives"
#             list_of_kwargs_for_eval[-1][key] = kwargs[key]

#     evals = [
#         eval_on_npTensors(
#             spaces[s_index(i)],
#             meshes_and_masks[x_index(i)][1],
#             mus_mu_strs[m_index(i)][0],
#             symb_dict,
#             **(list_of_kwargs_for_eval[i]),
#         )
#         for i in range(len(list_to_explore))
#     ]

#     # cuts_meshes_and_masks = [[] for i in range(len(spatial_domains))]
#     cuts_data_for_plots = [[] for _ in range(len(list_to_explore))]
#     # print("cuts_data_for_plots: ", cuts_data_for_plots)
#     cut_object_linestyle_dict = get_cut_object_linestyle_dict(objects)
#     if "cuts" in kwargs:
#         cuts = np.array(kwargs["cuts"])
#         if cuts.ndim == 2:
#             cuts = cuts[None, :, :]
#         cuts_meshes_and_masks = [
#             get_meshes_and_masks_for_2d_cuts(spatial_domains[i], cuts, n_visu)
#             for i in range(len(spatial_domains))
#         ]
#         mu_cuts = [
#             get_mu_mu_str(parameters_values[i], n_visu)[0]
#             for i in range(len(parameters_values))
#         ]
#         for i in range(len(list_to_explore)):
#             for j in range(len(cuts_meshes_and_masks[d_index(i)])):
#                 eval = eval_on_npTensors(
#                     spaces[s_index(i)],
#                     cuts_meshes_and_masks[d_index(i)][j][0],
#                     mu_cuts[p_index(i)],
#                     symb_dict,
#                     **(list_of_kwargs_for_eval[i]),
#                 )
#                 data = (
#                     cuts_meshes_and_masks[d_index(i)][j][0],
#                     eval,
#                     cuts_meshes_and_masks[d_index(i)][j][1],
#                 )
#                 cuts_data_for_plots[i].append(data)

#     fig = plt.figure(figsize=(sizeofobjects[0] * nbcols, sizeofobjects[1] * nblines))

#     axe_index = 1
#     for i in range(len(list_to_explore)):
#         if "loss" in kwargs:
#             if (i == 0) or (not loss_only_on_first_line):
#                 if kwargs["loss"][i] is not None:
#                     axe_losses = fig.add_subplot(nblines, nbcols, axe_index)
#                     losses = kwargs["loss"][i]
#                     losses.plot(axe_losses)
#             axe_index += 1

#         for key in objects:
#             if key in evals[i]:
#                 # print("axe_index: ", axe_index)
#                 n_axe = fig.add_subplot(nblines, nbcols, axe_index)
#                 plot_2d_contourf(
#                     fig,
#                     n_axe,
#                     meshes_and_masks[x_index(i)][0],
#                     evals[i][key],
#                     meshes_and_masks[x_index(i)][2],
#                     key,
#                     mus_mu_strs[m_index(i)][1],
#                     cuts_data=cuts_data_for_plots[i],
#                     linestyle_dict=cut_object_linestyle_dict,
#                     **kwargs,
#                 )
#             axe_index += 1

#         for j in range(len(cuts_data_for_plots[i])):
#             axe_cut = fig.add_subplot(nblines, nbcols, axe_index)
#             plot_2d_cut_values(
#                 fig,
#                 axe_cut,
#                 cuts_data_for_plots[i][j],
#                 COLORS_LIST[j],
#                 j,
#                 cut_object_linestyle_dict,
#             )
#             axe_index += 1

#     plt.gca().set_rasterization_zorder(-1)
#     fig.tight_layout()

# def plot_2x_AbstractApproxSpaces(
#     spaces: AbstractApproxSpace | Sequence[AbstractApproxSpace],
#     spatial_domains: VolumetricDomain | Sequence[VolumetricDomain],
#     parameters_domains: list[Sequence[float], Sequence[list[Sequence[float]]]],
#     **kwargs,
# ) -> None:

#     nspaces = [spaces] if not isinstance(spaces, Iterable) else spaces
#     if isinstance(spatial_domains, Iterable) and not (
#         (len(spatial_domains) == 1) or (len(spatial_domains) == len(nspaces))
#     ):
#         raise ValueError(
#             "second argument must be either a VolumetricDomain, or a list of "
#             "VolumetricDomain of length 1 or %d"
#             % len(nspaces)
#         )
#     nspatial_domains = (
#         [spatial_domains]
#         if not isinstance(spatial_domains, Iterable)
#         else spatial_domains
#     )
#     nparameters_domains = format_and_check_parameters_domains(parameters_domains)

#     if not (
#         (len(nparameters_domains) == 1) or (len(nparameters_domains) == len(nspaces))
#     ):
#         raise ValueError(
#             "third argument must be either a list[list[float]], or an "
#             "Iterable(list[list[float]]) of length 1 or %d"
#             % len(nspaces)
#         )

#     parameters_values = kwargs.get("parameters_values", "mean")
#     if isinstance(parameters_values, str):
#         nparameters_values = get_parameters_values(nparameters_domains, **kwargs)

#     elif isinstance(parameters_values, Sequence):
#         nparameters_values = check_and_format_Sequence_of_parameters_values(
#             parameters_values, nparameters_domains[0]
#         )
#     else:
#         raise ValueError(
#             "third argument must be a string or a list of floats or a Sequence of "
#             "lists of floats"
#         )

#     if len(nspaces) > 1 and not (
#         len(nparameters_values) == 1 or len(nparameters_values) == len(nspaces)
#     ):
#         raise ValueError(
#             "plotting several spaces and several parameters_values are incompatible"
#         )

#     nkwargs = {}
#     for kwarg in kwargs:
#         if kwarg in ["loss", "residual", "error", "solution"]:
#             if isinstance(kwargs[kwarg], Iterable) and not (
#                 (len(kwargs[kwarg]) == 1) or (len(kwargs[kwarg]) == len(spaces))
#             ):
#                 raise ValueError(
#                     "if argument %s is Iterable it must be of length 1 or %d"
#                     % (kwarg, len(spaces))
#                 )
#             nkwargs[kwarg] = (
#                 [kwargs[kwarg]]
#                 if not isinstance(kwargs[kwarg], Iterable)
#                 else kwargs[kwarg]
#             )
#         elif kwarg in ["derivatives"]:
#             nkwargs[kwarg] = (
#                 [kwargs[kwarg]]
#                 if not isinstance(kwargs[kwarg], Iterable)
#                 else kwargs[kwarg]
#             )
#         elif kwarg in ["cuts"]:
#             cuts = np.array(kwargs[kwarg])
#             if cuts.ndim == 2:
#                 cuts = cuts[None, :, :]
#             nkwargs[kwarg] = cuts
#         else:
#             nkwargs[kwarg] = kwargs[kwarg]

#     nkwargs.pop("parameters_values", None)

#     return __plot_2x_AbstractApproxSpaces(
#         nspaces, nspatial_domains, nparameters_values, **nkwargs
#     )

if __name__ == "__main__":  # pragma: no cover
    pass

# OLD
# def get_cut_data(
#    space: AbstractApproxSpace,
#    spatial_domain: VolumetricDomain,
#    parameters_values: list[list[float]],
#    **kwargs,
# ):
#    n_visu = kwargs.get("n_visu", 512)
#    # assume "cuts" is in kwargs
#    cuts = np.array(kwargs["cuts"])
#    if cuts.ndim == 2:
#        cuts = cuts[None, :, :]
#    if len(cuts) > len(COLORS_LIST):
#        warnings.warn(
#            "in plot_2x_AbstractApproxSpace: only the first %d cuts are taken into "
#            "account (%d provided)"
#            % (len(COLORS_LIST), len(cuts))
#        )
#    cuts_meshes_and_masks = get_meshes_and_masks_for_2d_cuts(
#        spatial_domain, cuts, n_visu
#    )
#    mu_cuts, _ = get_mu_mu_str(parameters_values, n_visu)
#    data = [
#        (
#            cuts_meshes_and_masks[i][0],
#            eval_on_npTensors(space, cuts_meshes_and_masks[i][0], mu_cuts, **kwargs),
#            cuts_meshes_and_masks[i][1],
#        )
#        for i in range(len(cuts_meshes_and_masks))
#    ]
#
#    return data

# def plot_2x_AbstractApproxSpace(
#    space: AbstractApproxSpace,
#    spatial_domain: VolumetricDomain,
#    parameters_domain: list[list[float]],
#    **kwargs,
# ):
#
#    nbobjs = 1
#
#    if "loss" in kwargs:
#        nbobjs += 1
#    if "residual" in kwargs:
#        nbobjs += 1
#    if "solution" in kwargs:
#        nbobjs += 1
#    if "error" in kwargs:
#        nbobjs += 1
#    if "cuts" in kwargs:
#        cuts = np.array(kwargs["cuts"])
#        if cuts.ndim == 2:
#            cuts = cuts[None, :, :]
#        nbobjs += len(cuts)
#    if "derivatives" in kwargs:
#        nbobjs += len(kwargs["derivatives"])
#
#    nbcols = min(3, nbobjs)
#    nblines = int(np.ceil(nbobjs / 3))
#    sizeofobjects = [4, 3]
#
#    parameters_values = get_parameters_values([parameters_domain], **kwargs)[0]
#
#    n_visu = kwargs.get("n_visu", 512)
#    (x1, x2), x, mask = get_mesh_and_mask_for_2d_plot(spatial_domain, n_visu)
#    mu, mu_str = get_mu_mu_str(parameters_values, n_visu**2)
#
#    evals = eval_on_npTensors(space, x, mu, **kwargs)
#
#    cuts_data_for_plots = []
#    cut_object_linestyle_dict = get_cut_object_linestyle_dict(kwargs)
#    if "cuts" in kwargs:
#        cuts_data_for_plots = get_cut_data(
#            space,
#            spatial_domain,
#            parameters_values,
#            **kwargs,
#        )
#
#    fig = plt.figure(figsize=(sizeofobjects[0] * nbcols, sizeofobjects[1] * nblines))
#
#    axe_index = 1
#    if "loss" in kwargs:
#        axe_losses = fig.add_subplot(nblines, nbcols, axe_index)
#        losses = kwargs["loss"]
#        losses.plot(axe_losses)
#        axe_index += 1
#
#    for key in evals:
#        n_axe = fig.add_subplot(nblines, nbcols, axe_index)
#        plot_2d_contourf(
#            fig,
#            n_axe,
#            (x1, x2),
#            evals[key],
#            mask,
#            key,
#            mu_str,
#            cuts_data=cuts_data_for_plots,
#            linestyle_dict=cut_object_linestyle_dict,
#            **kwargs,
#        )
#        axe_index += 1
#
#    for i in range(len(cuts_data_for_plots)):
#        axe_cut = fig.add_subplot(nblines, nbcols, axe_index)
#        plot_2d_cut_values(
#            fig,
#            axe_cut,
#            cuts_data_for_plots[i],
#            COLORS_LIST[i],
#            i,
#            cut_object_linestyle_dict,
#        )
#        axe_index += 1
#
#    plt.gca().set_rasterization_zorder(-1)
#    fig.tight_layout()

# faire une fct plus générale (pas que pour pinns)
# puis faire une fct pour différentes méthodes de résolution:
# - pinns
# - FEM
# - FDM ...
# def plot_2x_pinns(
#    pinn: PinnsElliptic,
#    spatial_domain: VolumetricDomain,
#    parameters_domain: list[list[float]],
#    **kwargs,
# ):
#
#    nbcols = 2
#    nblines = 2
#
#    solution = kwargs.get("solution", None)
#    if solution is not None:
#        nblines += 1
#
#    parameters_value = kwargs.get("parameters_value", "mean")
#
#    parameters_domain_np = np.array(parameters_domain)
#    if parameters_value == "mean":
#        parameters_values = np.mean(parameters_domain_np, axis=1)
#    elif parameters_value == "random":
#        parameters_values = np.random.uniform(
#            parameters_domain_np[:, 0], parameters_domain_np[:, 1]
#        )
#    else:
#        raise ValueError(
#            "parameters_value (%s) should be mean or random" % parameters_value
#        )
#    parameters_values = parameters_values.tolist()
#    # print("parameters_values: ", parameters_values)
#
#    fig = plt.figure(figsize=(5 * nbcols, 4 * nblines))
#
#    axe_losses = fig.add_subplot(nblines, nbcols, 1)
#    pinn.losses.plot(axe_losses)
#
#    axe_approx_sol = fig.add_subplot(nblines, nbcols, 3)
#
#    plot_2d_contourf(
#        fig, axe_approx_sol, pinn.space, spatial_domain, parameters_values, **kwargs
#    )
#
#    cut = ([0.0, 0.5], [-0.5, 0.5])
#    draw_cut_on_axe(fig, axe_approx_sol, spatial_domain, cut, **kwargs)
#    axe_cut = fig.add_subplot(nblines, nbcols, 2)
#    plot_object_on_line_cut(
#        fig, axe_cut, pinn.space, spatial_domain, cut, parameters_values, **kwargs
#    )
#
#    axe_residual = fig.add_subplot(nblines, nbcols, 4)
#
#    plot_2d_contourf(
#        fig,
#        axe_residual,
#        pinn.space,
#        spatial_domain,
#        parameters_values,
#        object="residual",
#        pde=pinn.pde,
#        **kwargs,
#    )
#
#    if solution is not None:
#        axe_solution = fig.add_subplot(nblines, nbcols, 5)
#        plot_2d_contourf(
#            fig,
#            axe_solution,
#            pinn.space,
#            spatial_domain,
#            parameters_values,
#            object="solution",
#            **kwargs,
#        )
#        axe_error = fig.add_subplot(nblines, nbcols, 6)
#        plot_2d_contourf(
#            fig,
#            axe_error,
#            pinn.space,
#            spatial_domain,
#            parameters_values,
#            object="error",
#            **kwargs,
#        )
#
#    plt.gca().set_rasterization_zorder(-1)

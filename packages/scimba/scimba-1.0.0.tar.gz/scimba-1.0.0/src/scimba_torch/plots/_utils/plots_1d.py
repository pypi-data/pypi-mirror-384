"""Plot functions for 1D (geometric dim) spaces."""

from typing import Any, Sequence

import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import KDTree

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.domain.meshless_domain.base import VolumetricDomain
from scimba_torch.integration.monte_carlo import DomainSampler
from scimba_torch.plots._utils.eval_utilities import eval_on_np_tensors
from scimba_torch.plots._utils.parameters_utilities import get_mu_mu_str

# from scimba_torch.optimizers.losses import GenericLosses
from scimba_torch.plots._utils.plots_utilities import (
    COLORS_LIST,
    LINESTYLE_LIST,
    get_objects_nblines_nbcols,
    get_regular_mesh_as_np_array,
    get_regular_mesh_as_np_meshgrid,
)
from scimba_torch.plots._utils.time_utilities import get_t_t_str
from scimba_torch.plots._utils.velocity_utilities import get_v_v_str


def _get_mesh_and_mask_for_1d_plot(
    spatial_domain: VolumetricDomain,
    n_visu: int,
) -> tuple[
    tuple[np.ndarray[tuple[int, ...], np.dtype[Any]], ...],
    np.ndarray,
    np.ndarray,
]:
    ebb = spatial_domain.get_extended_bounds_postmap(0.05)
    (x_mesh,) = get_regular_mesh_as_np_meshgrid(ebb, n_visu)
    # get x vector and mask
    x = get_regular_mesh_as_np_array(ebb, n_visu)

    if spatial_domain.is_mapped:
        assert spatial_domain.mapping is not None  # for type checking
        if not spatial_domain.mapping.is_invertible:
            tol = 1e-2
            m_is_empty = np.vectorize(lambda lis: len(lis) == 0)
            # construct a KDTree from a point cloud sampled on the domain
            sampler = DomainSampler(spatial_domain)
            p_cloud = (sampler.sample(n_visu)).x.detach().cpu().numpy()
            # print("p_cloud: ", p_cloud)
            KDT = KDTree(p_cloud)
            indexes = KDT.query_ball_point(x, tol)
            mask = m_is_empty(indexes)
            # print("mask.shape: ", mask.shape)
        else:
            mask = spatial_domain.is_outside_postmap_np(x)

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
        mask = spatial_domain.is_outside_postmap_np(x)

    return ((x_mesh,), x, mask)


def _plot_1d_curve(
    fig,
    axe,
    mesh: tuple[np.ndarray[tuple[int, ...], np.dtype[Any]], ...],
    vals: dict[str, np.ndarray],
    mask: np.ndarray,
    objects: list[str],
    t_str: str,
    v_str: str,
    mu_str: str,
    color_dict: dict[str, str],
    linestyle_dict: dict[str, Any],
    **kwargs,
):
    title = ""
    if len(t_str) > 0:
        title += r", $t$=" + t_str if len(title) > 0 else r"$t$=" + t_str
    if len(v_str) > 0:
        title += r", $v$=" + v_str if len(title) > 0 else r"$v$=" + v_str
    if len(mu_str) > 0:
        title += r", $\mu$=" + mu_str if len(title) > 0 else r"$\mu$=" + mu_str

    vmin = np.inf
    vmax = -np.inf
    for object in objects:
        values = np.ma.array(vals[object], mask=mask)
        vmin = min(vmin, values.min())
        vmax = max(vmax, values.max())
        linewidth = 1
        if object == "solution":
            linewidth = 2
        label = object
        if object in ["error", "residual"]:
            norm = (values**2).mean() ** 0.5
            label += ", $L^2$ norm: %.2e" % norm

        axe.plot(
            mesh[0],
            values,
            color=color_dict[object],
            label=label,
            linestyle=linestyle_dict[object],
            linewidth=linewidth,
        )

    if "error" in objects or "residual" in objects:
        axe.set_yscale("log", base=10)
        axe.set_ylim(ymax=vmax)
    axe.set_title(f"{title}")
    axe.set_aspect("auto")
    axe.legend(loc="best")
    axe.set_xlabel("x")


default_color_dict = {
    "approximation": COLORS_LIST[0],
    "solution": COLORS_LIST[1],
    "residual": COLORS_LIST[4],
    "error": COLORS_LIST[3],
}
default_linestyle_dict = {
    "approximation": LINESTYLE_LIST[0],
    "solution": LINESTYLE_LIST[1],
    "residual": LINESTYLE_LIST[0],
    "error": LINESTYLE_LIST[0],
}


def __plot_1x_abstract_approx_space(
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
    # if len(components) == 0:
    #     components = list(range(space.nb_unknowns))
    # print("components: ", components)

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
    # print("time_values: ", time_values)
    # print("loss_only_on_first_line: ", loss_only_on_first_line)
    # print("nblines: %d, nbcols: %d" % (nblines, nbcols))
    # print("objects: ", objects)
    # print("input kwargs: ", kwargs)

    # dictionary of symbols for eval and derivatives
    symb_dict = {
        "components": ["u"],
        "space_variables": ["x"],
    }
    if len(time_values) > 0:
        symb_dict["time_variable"] = ["t"]
    if len(velocity_values) > 0:
        nbvelocity_variables = velocity_values[0].shape[-1]
        velocity_variables = ["v" + str(i) for i in range(nbvelocity_variables)]
        symb_dict["phase_variables"] = velocity_variables
    # print("symb_dict: ", symb_dict)
    # print("symb_dict: ", symb_dict)

    if "derivatives" in kwargs:
        for i, der in enumerate(
            kwargs["derivatives"]
        ):  # append it even if its None to preserve color scheme
            default_color_dict[der] = COLORS_LIST[i]
            default_linestyle_dict[der] = LINESTYLE_LIST[0]

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
    mesh_and_mask = _get_mesh_and_mask_for_1d_plot(spatial_domain, n_visu)

    mus_mu_strs = [
        get_mu_mu_str(parameters_values[i], n_visu)
        for i in range(len(parameters_values))
    ]
    ts_t_strs = [get_t_t_str(time_values[i], n_visu) for i in range(len(time_values))]
    vs_v_strs = [
        get_v_v_str(velocity_values[i], n_visu, velocity_strs[i])
        for i in range(len(velocity_values))
    ]
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

    # print("kwargs_for_eval: ", kwargs_for_eval)

    evals = [
        eval_on_np_tensors(
            space,
            ts_t_strs[t_index(i)][0],
            mesh_and_mask[1],
            vs_v_strs[v_index(i)][0],
            mus_mu_strs[m_index(i)][0],
            symb_dict,
            components[c_index(i)],
            **kwargs_for_eval,
        )
        for i in range(len(list_to_explore))
    ]

    group_dict = {"approximation": 0, "solution": 0, "residual": 1, "error": 1}
    if "derivatives" in kwargs:
        for derivative in kwargs["derivatives"]:
            if derivative is not None:
                group_dict[derivative] = 2

    groups: Sequence[Any] = [[], [], []]
    for key in objects:
        groups[group_dict[key]].append(key)

    # print("groups: ", groups)

    axe_index = 1
    for i in range(len(list_to_explore)):
        if "loss" in kwargs:
            if (i == 0) or (not loss_only_on_first_line):
                if kwargs["loss"] is not None:
                    axe_losses = fig.add_subplot(nblines, nbcols, axe_index)
                    losses = kwargs["loss"]
                    losses.plot(axe_losses)
            axe_index += 1

        # form groups
        groups_i: Sequence[Any] = [[], [], []]
        for key in evals[i]:
            groups_i[group_dict[key]].append(key)

        # print("i: %d, groups_i: " % i, groups_i)

        for j, group in enumerate(groups):
            if len(groups_i[j]) > 0:
                n_axe = fig.add_subplot(nblines, nbcols, axe_index)
                _plot_1d_curve(
                    fig,
                    n_axe,
                    mesh_and_mask[0],
                    evals[i],
                    mesh_and_mask[2],
                    groups_i[j],
                    ts_t_strs[t_index(i)][1],
                    vs_v_strs[v_index(i)][1],
                    mus_mu_strs[m_index(i)][1],
                    default_color_dict,
                    default_linestyle_dict,
                    **kwargs,
                )
            if len(group) > 0:
                axe_index += 1

    plt.gca().set_rasterization_zorder(-1)


# DEPRECATED
# def __plot_1x_AbstractApproxSpaces(
#     spaces: list[AbstractApproxSpace],
#     spatial_domains: list[VolumetricDomain],
#     parameters_values: list[np.ndarray],
#     **kwargs,
# ):
#     objects, nblines, nbcols, loss_only_on_first_line = get_objects_nblines_nbcols(
#         spaces, parameters_values, **kwargs
#     )
#     sizeofobjects = [4, 3]

#     print("input kwargs: ", kwargs)
#     # dictionary of symbols for eval and derivatives
#     symb_dict = {
#         "components": ["u"],
#         # "time_variable": ["t"],
#         "space_variables": ["x"],
#     }

#     if "derivatives" in kwargs:
#         for derivative in kwargs["derivatives"]:
#             if derivative is not None:
#                 for i, obj in enumerate(derivative):
#                     default_color_dict[obj] = COLORS_LIST[i]
#                     default_linestyle_dict[obj] = LINESTYLE_LIST[0]

#     # print(
#     #     "nblines: %d, nbcols: %d"
#     #     % (
#     #         nblines,
#     #         nbcols,
#     #     )
#     # )

#     list_to_explore = spaces
#     if (len(spaces) == 1) and (len(parameters_values) > 1):
#         list_to_explore = parameters_values

#     s_index = (lambda i: 0) if len(spaces) == 1 else (lambda i: i)
#     # check len of parameters_values ? need an nb_parameters attribute in
#     # abstract_approx_space...
#     # p_index = (lambda i: 0) if len(parameters_values) == 1 else (lambda i: i)

#     n_visu = kwargs.get("n_visu", 512)
#     meshes_and_masks = [
#         get_mesh_and_mask_for_1d_plot(spatial_domains[i], n_visu)
#         for i in range(len(spatial_domains))
#     ]
#     mus_mu_strs = [
#         get_mu_mu_str(parameters_values[i], n_visu)
#         for i in range(len(parameters_values))
#     ]
#     # print("mesh.shape: ", meshes_and_masks[0][0][0].shape)
#     # print("x.shape:    ", meshes_and_masks[0][1].shape)
#     # print("mask.shape: ", meshes_and_masks[0][2].shape)
#     # print("mu.shape:   ", mus_mu_strs[0][0].shape)

#     # d_index = (lambda i: 0) if len(spatial_domains) == 1 else (lambda i: i)
#     x_index = (lambda i: 0) if len(meshes_and_masks) == 1 else (lambda i: i)
#     m_index = (lambda i: 0) if len(mus_mu_strs) == 1 else (lambda i: i)

#     list_of_kwargs_for_eval = []
#     for i in range(0, len(list_to_explore)):
#         list_of_kwargs_for_eval.append({})
#         for key in ["solution", "error", "residual", "derivatives"]:
#             if key in kwargs:
#                 # print("key: ", key)
#                 # print("kwargs[key]: ", kwargs[key])
#                 # if isinstance(kwargs[key], Iterable):
#                 if len(kwargs[key]) == 1:
#                     list_of_kwargs_for_eval[-1][key] = kwargs[key][0]
#                 elif kwargs[key][i] is not None:
#                     list_of_kwargs_for_eval[-1][key] = kwargs[key][i]
#                 # else:
#                 #     list_of_kwargs_for_eval[-1][key] = kwargs[key]
#         # if "derivatives" in kwargs:
#         #     key = "derivatives"
#         #     list_of_kwargs_for_eval[-1][key] = kwargs[key]

#     # print("list_of_kwargs_for_eval: ", list_of_kwargs_for_eval)

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

#     fig = plt.figure(figsize=(sizeofobjects[0] * nbcols, sizeofobjects[1] * nblines))

#     group_dict = {"approximation": 0, "solution": 0, "residual": 1, "error": 1}
#     if "derivatives" in kwargs:
#         for derivative in kwargs["derivatives"]:
#             if derivative is not None:
#                 for der in derivative:
#                     group_dict[der] = 2

#     groups = [[], [], []]
#     for key in objects:
#         groups[group_dict[key]].append(key)

#     # print("groups: ", groups)

#     axe_index = 1
#     for i in range(len(list_to_explore)):
#         if "loss" in kwargs:
#             if (i == 0) or (not loss_only_on_first_line):
#                 if kwargs["loss"][i] is not None:
#                     axe_losses = fig.add_subplot(nblines, nbcols, axe_index)
#                     losses = kwargs["loss"][i]
#                     losses.plot(axe_losses)
#             axe_index += 1

#         # form groups
#         groups_i = [[], [], []]
#         for key in evals[i]:
#             groups_i[group_dict[key]].append(key)

#         # print("i: %d, groups_i: " % i, groups_i)

#         for j, group in enumerate(groups):
#             if len(groups_i[j]) > 0:
#                 n_axe = fig.add_subplot(nblines, nbcols, axe_index)
#                 plot_1d_curve(
#                     fig,
#                     n_axe,
#                     meshes_and_masks[x_index(i)][0],
#                     evals[i],
#                     meshes_and_masks[x_index(i)][2],
#                     groups_i[j],
#                     mus_mu_strs[m_index(i)][1],
#                     default_color_dict,
#                     default_linestyle_dict,
#                     **kwargs,
#                 )
#             if len(group) > 0:
#                 axe_index += 1

#     plt.gca().set_rasterization_zorder(-1)
#     fig.tight_layout()

# def get_nblines_nbcols(xdim: int, oneline: bool, **kwargs):
#     nb_max_cols = kwargs.get("nb_max_cols", 4)
#     nb_axes = 1
#     # nbcols = 1
#     # nblines = 1
#     for key in kwargs:
#         if key in ["loss"]:
#             nb_axes += 1
#         if key in ["residual"]:
#             nb_axes += 1
#         if (key in ["solution"]) and (xdim >= 2):
#             nb_axes += 1  # in dim 1 on the same axe as approximation
#         if (key in ["error"]) and ((xdim >= 2) or ("residual" not in kwargs)):
#             nb_axes += 1
#         # non empty dict of the form {"ux": True,"uxx": False}
#         if key in ["derivatives"]:
#             if xdim == 1:
#                 nb_axes += 1  # in dim 1 all derivatives on the same axis
#             else:
#                 nb_axes += len(kwargs["derivatives"])

#     if oneline:
#         nb_axes = min(nb_axes, nb_max_cols)
#     else:
#         nbcols = min(nb_max_cols, nb_axes)
#         nblines = int(np.ceil(nb_axes / nbcols))
#     return nblines, nbcols

# def plot_1x_AbstractApproxSpaces(
#     spaces: AbstractApproxSpace | Sequence[AbstractApproxSpace],
#     spatial_domains: VolumetricDomain | Sequence[VolumetricDomain],
#     parameters_domains: list[Sequence[float], Sequence[list[Sequence[float]]]],
#     **kwargs,
# ) -> None:

#     # spaces: AbstractApproxSpace | Sequence[AbstractApproxSpace]
#     nspaces = [spaces] if not isinstance(spaces, Iterable) else list(spaces)
#     # spatial_domains: VolumetricDomain | Sequence[VolumetricDomain]
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
#         else list(spatial_domains)
#     )

#     # parameters_domains: list[list[float]] | Sequence[list[float]]
#     nparameters_domains = format_and_check_parameters_domains(parameters_domains)
#     if not (
#         (len(nparameters_domains) == 1) or (len(nparameters_domains) == len(nspaces))
#     ):
#         raise ValueError(
#             "third argument must be either a list[list[float]], "
#             "or an Iterable(list[list[float]]) of length 1 or %d"
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

#     # nkwargs = {}
#     for key in kwargs:
#         if key in ["derivatives"]:
#             if isinstance(kwargs[key], str):
#                 kwargs[key] = [kwargs[key]]
#             if is_Sequence_str(kwargs[key]):
#                 kwargs[key] = [kwargs[key]]

#         if key in ["residual", "error", "solution", "derivatives"]:
#             if isinstance(kwargs[key], Iterable) and not (
#                 (len(kwargs[key]) == 1) or (len(kwargs[key]) == len(spaces))
#             ):
#                 raise ValueError(
#                     "if argument %s is Iterable it must be of length 1 or %d"
#                     % (key, len(spaces))
#                 )
#         if key in ["loss", "residual", "error", "solution", "derivatives"]:
#             if key == "error":
#                 print("is error iterable: ", isinstance(kwargs[key], Iterable))
#             kwargs[key] = (
#                 [kwargs[key]]
#                 if not isinstance(kwargs[key], Iterable)
#                 else list(kwargs[key])
#             )
#             if key == "error":
#                 print("nkwargs[key]: ", kwargs[key])
#         if key in ["loss"]:  # fill with Nones
#             while len(kwargs[key]) < len(nspaces):
#                 kwargs[key].append(None)
#         # elif key in ["derivatives"]:
#         #     nkwargs[key] = (
#         #         [kwargs[key]]
#         #         if not isinstance(kwargs[key], Iterable)
#         #         else kwargs[key]
#         #     )
#         # elif key in ["cuts"]:
#         #     cuts = np.array(kwargs[key])
#         #     if cuts.ndim == 2:
#         #         cuts = cuts[None, :, :]
#         #     nkwargs[key] = cuts
#         else:
#             kwargs[key] = kwargs[key]

#     kwargs.pop("parameters_values", None)

#     return __plot_1x_AbstractApproxSpaces(
#         nspaces, nspatial_domains, nparameters_values, **kwargs
#     )

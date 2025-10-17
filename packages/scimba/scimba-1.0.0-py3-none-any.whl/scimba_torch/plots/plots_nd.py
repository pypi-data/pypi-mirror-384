"""Plotting functions (generic in geometric dimension) for approximation spaces."""

from collections.abc import Sequence
from typing import Any, cast

import matplotlib.pyplot as plt
import numpy as np

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.domain.mesh_based_domain.cuboid import Cuboid
from scimba_torch.domain.meshless_domain.base import SurfacicDomain, VolumetricDomain
from scimba_torch.plots._utils.parameters_utilities import (
    get_parameters_values,
    is_parameters_domain,
    is_parameters_values,
    is_sequence_of_one_or_n_parameters_domain,
    is_sequence_of_one_or_n_parameters_values,
)
from scimba_torch.plots._utils.plots_1d import __plot_1x_abstract_approx_space
from scimba_torch.plots._utils.plots_1x1v import __plot_1x1v_abstract_approx_space
from scimba_torch.plots._utils.plots_2d import __plot_2x_abstract_approx_space
from scimba_torch.plots._utils.plots_utilities import get_objects_nblines_nbcols
from scimba_torch.plots._utils.time_utilities import (
    get_time_values,
    is_sequence_of_one_or_n_time_domain,
    is_sequence_of_one_or_n_time_values,
    is_time_domain,
    is_time_values,
)
from scimba_torch.plots._utils.utilities import (
    _is_sequence_str,
    _is_sequence_str_or_none,
)
from scimba_torch.plots._utils.velocity_utilities import (
    get_velocity_values,
    is_sequence_of_one_or_n_velocity_values,
    is_velocity_values,
)


def plot_abstract_approx_space(
    space: AbstractApproxSpace,
    spatial_domain: VolumetricDomain | Cuboid,
    parameters_domain: Sequence[Sequence[float]] = [],
    time_domain: Sequence[float] = [],
    velocity_domain: SurfacicDomain | VolumetricDomain | None = None,
    **kwargs,
):
    """Plot an AbstractApproxSpace on its domain.

    Args:
        space: the space to be plot
        spatial_domain: the geometric domain on which space is defined
        parameters_domain: the domain of parameters of space, [] meaning no parameters,
        time_domain: the time domain of space, [] meaning space is time-independent,
        velocity_domain: the velocity domain of space,
            None meaning space has no velocity arguments,
        **kwargs: arbitrary keyword arguments

    Keyword Args:
        parameters_values: a (list of) point(s) in the parameters domain,
            or "mean" or "random", defaults to "mean",
        time_values: a (list of) time(s) in the time domain,
            or "initial" or "final", defaults to "final",
        velocity_values: a (list of) point(s) in the velocity domain,
        components: the list of components of the space to be plot,
            defaults to the list of all the components,
        loss: a GenericLosses object to be plot,
        residual: an AbstractPDE object with a residual attribute,
        derivatives: a list of strings representing the derivatives to be plot,
            for instance "uxx"; defaults to [],
        solution: a callable depending on the same args as space to be plot,
        error: plot the absolute error with respect to the given solution,
        cuts: for 2D geometric dim, a list of affine spaces of dimension 1,
              each given as a tuple of 1 point and a basis
        title: a str
        ...: see examples

    Implemented only for 1 and 2 dimensional spaces.

    Raises:
        ValueError: some input arguments are not correctly formated
        KeyError: bad key in :code:`**kwargs`
        NotImplementedError: some option combinations are not implemented yet

    Examples:
        >>> import matplotlib.pyplot as plt
        >>> from scimba_torch.plots.plots_nd import plot_AbstractApproxSpace
        >>> ...
        >>> def exact_sol(x: LabelTensor, mu: LabelTensor):
                x1, x2 = x.get_components()
                mu1 = mu.get_components()
                return mu1 * torch.sin(2.0 * torch.pi * x1) *
                             torch.sin(2.0 * torch.pi * x2)
        >>> plot_AbstractApproxSpace(
                pinns.space,                   #the approximation space
                domain_x,                      #the geometric domain
                [[1.0, 2.0]],                  #the parameters domain
                loss=pinns.losses,             #the loss
                residual=pde,                  #the residual
                solution=exact_sol,            #the reference solution
                error=exact_sol,               #the ref. sol. to plot absolute error
                derivatives=["ux", "uy"],      #a list of string for derivatives
                cuts=[                         #a list of 2 1D cuts
                    ([0.0, 0.0], [-0.5, 0.5]),
                    ([0.0, 0.2], [0.0, 1.0]),
                ],
                draw_contours=True,            #whether to draw level lines
                n_drawn_contours=20,           #number of level lines
                title="Learned solution to 2D Laplacian in strong
                form with weak boundary conditions",
            )
        >>> plt.show()
    """
    if not isinstance(space, AbstractApproxSpace):
        raise ValueError("first argument (space) must be an AbstractApproxSpace")
    if not (
        isinstance(spatial_domain, VolumetricDomain)
        or isinstance(spatial_domain, Cuboid)
    ):
        raise ValueError(
            "second argument (spatial domain) must be a VolumetricDomain or a Cuboid"
        )
    nspatial_domain = (
        spatial_domain.to_volumetric_domain()
        if isinstance(spatial_domain, Cuboid)
        else spatial_domain
    )
    if not is_parameters_domain(parameters_domain):
        raise ValueError(
            "third argument (parameters domain) must be a possibly empty Sequence of "
            "intervals"
        )
    if not is_time_domain(time_domain):
        raise ValueError(
            "fourth argument (time domain) argument must be either [] or a Sequence of "
            "2 floats"
        )
    if not (
        (velocity_domain is None)
        or isinstance(velocity_domain, SurfacicDomain)
        or isinstance(velocity_domain, VolumetricDomain)
    ):
        raise ValueError(
            "fifth argument (velocity domain) must be None or a SurfacicDomain or a "
            "VolumetricDomain"
        )

    parameters_values = kwargs.get("parameters_values", "mean")
    if not is_parameters_values(parameters_values, parameters_domain):
        raise ValueError(
            f'argument parameters_values must be "mean", "random", a Sequence of '
            f"{len(parameters_domain)} float or a Sequence of Sequences of "
            f"{len(parameters_domain)} float"
        )
    nparameters_values = get_parameters_values(parameters_values, parameters_domain)
    kwargs.pop("parameters_values", None)

    time_values = kwargs.get("time_values", "final")
    if not is_time_values(time_values, time_domain):
        raise ValueError(
            'argument time_values must be "initial", "final", ["initial", "final"], '
            "an integer >=2, a float or a Sequence of float"
        )
    ntime_values = get_time_values(time_values, time_domain)
    kwargs.pop("time_values", None)

    nvelocity_values: Sequence[np.ndarray] = []
    if velocity_domain is not None:
        default_velocity_values = [0.0]
        velocity_values = kwargs.get("velocity_values", default_velocity_values)
        # error if not a list?
        # print(velocity_values)
        if not is_velocity_values(velocity_values, velocity_domain):
            raise ValueError("invalid list of velocity values")
        nvelocity_values = get_velocity_values(velocity_values, velocity_domain)
    kwargs.pop("velocity_values", None)

    assemble_labels_default = [0]
    assemble_labels = kwargs.get("assemble_labels", assemble_labels_default)
    default_components = list(range(0, space.nb_unknowns, len(assemble_labels)))
    components = kwargs.get("components", default_components)

    # if (
    #     ((len(nparameters_values) > 1) and (len(ntime_values) > 1))
    #     or ((len(nparameters_values) > 1) and (len(nvelocity_values) > 1))
    #     or ((len(ntime_values) > 1) and (len(nvelocity_values) > 1))
    # ):
    #     raise ValueError(
    #         "plotting one space with several parameters values and/or several time "
    #         "values and/or several velocity values is not supported"
    #     )
    sequences = [nparameters_values, ntime_values, nvelocity_values, components]
    for seq in sequences:
        if len(seq) > 1:
            for seq2 in sequences:
                if (seq2 is not seq) and (len(seq2) > 1):
                    raise ValueError(
                        "plotting one space with several components and/or several "
                        "parameters values and/or several time values and/or several "
                        "velocity values is not supported"
                    )

    for key in kwargs:
        if key in ["parameters_value"]:
            raise KeyError(
                "parameters_value is deprecated; use parameters_values instead"
            )
        if key in ["cuts"]:
            cuts = np.array(kwargs[key])
            if cuts.ndim == 2:  # 1 cut -> list of 1 cut
                kwargs[key] = [kwargs[key]]

    suptitle = kwargs.pop("title", "")

    sizeofobjects = [4, 3]
    if (
        len(nparameters_values) > 1
        or len(ntime_values) > 1
        or len(nvelocity_values) > 1
        or len(components) > 1
    ):
        oneline = True
    else:
        oneline = False

    _, nblines, nbcols, _ = get_objects_nblines_nbcols(
        nspatial_domain.dim,
        oneline,
        nparameters_values,
        ntime_values,
        nvelocity_values,
        components,
        **kwargs,
    )
    fig = plt.figure(
        figsize=(sizeofobjects[0] * nbcols, sizeofobjects[1] * nblines),
        layout="constrained",
    )
    if nspatial_domain.dim == 1:  # call plot_1x_AbstractApproxSpace
        if (velocity_domain is not None) and (velocity_domain.dim == 1):
            __plot_1x1v_abstract_approx_space(
                fig,
                space,
                nspatial_domain,
                velocity_domain,
                nparameters_values,
                ntime_values,
                components,
                oneline,
                **kwargs,
            )
        else:
            __plot_1x_abstract_approx_space(
                fig,
                space,
                nspatial_domain,
                nparameters_values,
                ntime_values,
                nvelocity_values,
                components,
                oneline,
                **kwargs,
            )
    elif nspatial_domain.dim == 2:  # call plot_2x_AbstractApproxSpace
        __plot_2x_abstract_approx_space(
            fig,
            space,
            nspatial_domain,
            nparameters_values,
            ntime_values,
            nvelocity_values,
            components,
            oneline,
            **kwargs,
        )
    else:
        raise NotImplementedError("Only 1d and 2d are supported")

    if len(suptitle):
        fig.suptitle(suptitle, fontsize="xx-large", ha="center")


def _is_sequence_abstract_approx_space(l_spaces: Any) -> bool:
    return isinstance(l_spaces, Sequence) and all(
        isinstance(L, AbstractApproxSpace) for L in l_spaces
    )


def _is_sequence_of_one_or_n_volumetric_domain_or_cuboid(
    l_domains: Any, n: int
) -> bool:
    return (
        isinstance(l_domains, Sequence)
        and ((len(l_domains) == 1) or (len(l_domains) == n))
        and all(
            (isinstance(L, VolumetricDomain) or isinstance(L, Cuboid))
            for L in l_domains
        )
    )


def _is_sequence_of_one_or_n_none_or_surfacic_or_volumetric_domain(
    l_domains: Any, n: int
) -> bool:
    return (
        isinstance(l_domains, Sequence)
        and ((len(l_domains) == 1) or (len(l_domains) == n))
        and all(
            (
                isinstance(L, SurfacicDomain)
                or isinstance(L, VolumetricDomain)
                or (L is None)
            )
            for L in l_domains
        )
    )


def _is_sequence_of_one_or_n_derivatives(l_der: Any, n: int) -> bool:
    return (
        isinstance(l_der, Sequence)
        and ((len(l_der) == 1) or (len(l_der) == n))
        and all(_is_sequence_str_or_none(L) for L in l_der)
    )


def _process_velocity_domain_s(
    velocity_domains: SurfacicDomain
    | None
    | Sequence[SurfacicDomain | VolumetricDomain | None],
    nbspaces: int,
) -> Sequence[SurfacicDomain | VolumetricDomain | None]:
    nvelocity_domains = (
        (velocity_domains,)
        if (velocity_domains is None or isinstance(velocity_domains, SurfacicDomain))
        else velocity_domains
    )
    if not _is_sequence_of_one_or_n_none_or_surfacic_or_volumetric_domain(
        nvelocity_domains, nbspaces
    ):
        raise ValueError(
            "fifth argument must of type T or list[T] which length is 1 or matches the "
            "length of the first argument, with T being None | SurfacicDomain | "
            "VolumetricDomain"
        )
    if len(nvelocity_domains) == 1:
        nvelocity_domains = [nvelocity_domains[0] for _ in range(nbspaces)]
    return nvelocity_domains


def _process_velocity_values_s(
    velocity_domains: Sequence[SurfacicDomain | VolumetricDomain | None],
    nbspaces: int,
    kwargs,
) -> Sequence[Sequence[np.ndarray]]:
    default_velocity_values = []
    for velocity_domain in velocity_domains:
        if velocity_domain is not None:
            if isinstance(velocity_domain, VolumetricDomain):
                default_velocity_values.append([0.0] * velocity_domain.dim)
            else:
                default_velocity_values.append([0.0] * velocity_domain.dim_parametric)
        else:
            default_velocity_values.append([])

    nvelocity_values = kwargs.pop("velocity_values", default_velocity_values)
    # print(nvelocity_values)
    # if (velocity_domains[0] is not None) and is_velocity_values(
    #     nvelocity_values, velocity_domains[0]
    # ):
    #     nvelocity_values = (nvelocity_values,)

    if nbspaces > 1:
        # print(nvelocity_values)
        if not is_sequence_of_one_or_n_velocity_values(
            nvelocity_values, velocity_domains, nbspaces
        ):
            raise ValueError("velocity_values")
        v_index = (lambda i: 0) if len(velocity_domains) == 1 else (lambda i: i)
        nvelocity_values = tuple(
            get_velocity_values(val, velocity_domains[v_index(i)])
            for i, val in enumerate(nvelocity_values)
        )
        if len(nvelocity_values) == 1:
            nvelocity_values = [nvelocity_values[0] for _ in range(nbspaces)]
    else:
        nvelocity_values = nvelocity_values[0]

    return nvelocity_values


def plot_abstract_approx_spaces(
    spaces: AbstractApproxSpace | Sequence[AbstractApproxSpace],
    spatial_domains: VolumetricDomain | Cuboid | Sequence[VolumetricDomain | Cuboid],
    parameters_domains: Sequence[Sequence[float]]
    | Sequence[Sequence[Sequence[float]]] = ([],),
    time_domains: Sequence[float] | Sequence[Sequence[float]] = ([],),
    velocity_domains: SurfacicDomain | None | Sequence[SurfacicDomain | None] = None,
    **kwargs,
) -> None:
    """Plot a sequence of AbstractApproxSpaces on their domains.

    Args:
        spaces: the (sequence of) space(s) to be plot
        spatial_domains: the (sequence of) geometric domain(s)
            on which spaces are defined
        parameters_domains: the (sequence of) domain(s) of parameters of space(s),
            ([],) meaning no parameters,
        time_domains: the (sequence of) time domain(s) of space(s),
            ([],) meaning spaces is time-independent,
        velocity_domains: the the (sequence of) velocity domain(s) of space(s),
            None meaning space has no velocity arguments,
        **kwargs: arbitrary keyword arguments

    Keyword Args:
        title: the main title of the figure
        titles: a sequence of titles (1 for each approximation space)
        ...: same keyword arguments as in plot_AbstractApproxSpace,
            are to be given as sequences of n values, where n is the number of spaces;
            sequences of n same values can be shortcut by the value

    Implemented only for 1 and 2 dimensional spaces

    Raises:
        ValueError: some input arguments are not correctly formated
        KeyError: bad key in :code:`**kwargs`
        NotImplementedError: some option combinations are not implemented yet

    Examples:
        >>> import matplotlib.pyplot as plt
        >>> from scimba_torch.plots.plots_nd import plot_AbstractApproxSpaces
        >>> ...
        >>> def exact_sol(x: LabelTensor, mu: LabelTensor):
                x1, x2 = x.get_components()
                mu1 = mu.get_components()
                return mu1 * torch.sin(2.0 * torch.pi * x1) *
                             torch.sin(2.0 * torch.pi * x2)
        >>> plot_AbstractApproxSpaces(
                (pinns.space, pinns2.space, pinns3.space,),# a sequence of AbstractSpace
                domain_x,               # shortcut for (domain_x,domain_x,domain_x,)
                ((1.0, 1.0 + 1e-5),),   # the same parameters domain for the 3 spaces
                loss=( pinns.losses, pinns2.losses, pinns3.losses, ),
                residual=( pinns.pde, pinns2.pde, pinns3.pde, ),
                error=exact_sol,
                draw_contours=True,
                n_drawn_contours=20,
                parameters_values="random",
            )
        >>> plt.show()
    """
    nspaces = (spaces,) if isinstance(spaces, AbstractApproxSpace) else spaces
    if not _is_sequence_abstract_approx_space(nspaces):
        raise ValueError(
            "first argument must be a AbstractApproxSpace or a Sequence of "
            "AbstractApproxSpaces"
        )
    nbspaces = len(nspaces)

    # if nbspaces > 1:
    #     for space in nspaces:
    #         if space.nb_unknowns > 1:
    #             raise ValueError(
    #                 "plotting several spaces of which one or more has more than one "
    #                 "unknown is not supported yet"
    #             )

    assemble_labels_default = list([0] for _space in nspaces)
    assemble_labels = kwargs.get("assemble_labels", assemble_labels_default)
    # print("assemble_labels: ", assemble_labels)
    default_components = list(
        list(range(0, space.nb_unknowns, len(al)))
        for space, al in zip(nspaces, assemble_labels)
    )
    components = kwargs.get("components", default_components)
    # print("components: ", components)

    # TODO check components

    nspatial_domains = (
        (spatial_domains,)
        if (
            isinstance(spatial_domains, VolumetricDomain)
            or isinstance(spatial_domains, Cuboid)
        )
        else spatial_domains
    )
    if not _is_sequence_of_one_or_n_volumetric_domain_or_cuboid(
        nspatial_domains, nbspaces
    ):
        raise ValueError(
            "second argument must be a VolumetricDomain, a Cuboid or a Sequence of "
            "VolumetricDomains or Cuboids which length is 1 or matches the length of "
            "the first argument"
        )
    nspatial_domains = cast(Sequence[VolumetricDomain | Cuboid], nspatial_domains)
    nspatial_domains = tuple(
        (dom.to_volumetric_domain() if isinstance(dom, Cuboid) else dom)
        for dom in nspatial_domains
    )
    nspatial_domains = cast(Sequence[VolumetricDomain], nspatial_domains)
    if len(nspatial_domains) == 1:
        nspatial_domains = [nspatial_domains[0] for _ in range(nbspaces)]
    nspatial_domains = cast(Sequence[VolumetricDomain], nspatial_domains)

    nparameters_domains = (
        (parameters_domains,)
        if is_parameters_domain(parameters_domains)
        else parameters_domains
    )
    if not is_sequence_of_one_or_n_parameters_domain(nparameters_domains, nbspaces):
        raise ValueError(
            "third argument must be a parameters domain or a Sequence of parameters "
            "domains which length is 1 or matches the length of the first argument"
        )
    nparameters_domains = cast(Sequence[Sequence[Sequence[float]]], nparameters_domains)
    nparameters_values = kwargs.get("parameters_values", "mean")
    parameters_values = kwargs.pop("parameters_values", "mean")
    if (not isinstance(nparameters_values, Sequence)) or isinstance(
        nparameters_values, str
    ):
        nparameters_values = (nparameters_values,)
    if nbspaces > 1:
        if not is_sequence_of_one_or_n_parameters_values(
            nparameters_values, nparameters_domains, nbspaces
        ):
            raise ValueError("parameters_values")
        p_index = (lambda i: 0) if len(nparameters_domains) == 1 else (lambda i: i)
        nparameters_values = tuple(
            get_parameters_values(val, nparameters_domains[p_index(i)])
            for i, val in enumerate(nparameters_values)
        )
    else:
        if (
            not is_parameters_values(parameters_values, nparameters_domains[0])
        ) and isinstance(parameters_values, Sequence):
            parameters_values = parameters_values[0]

    if len(nparameters_domains) == 1:
        nparameters_domains = [nparameters_domains[0] for _ in range(nbspaces)]
    if len(nparameters_values) == 1:
        nparameters_values = [nparameters_values[0] for _ in range(nbspaces)]

    ntime_domains = (time_domains,) if is_time_domain(time_domains) else time_domains
    if not is_sequence_of_one_or_n_time_domain(ntime_domains, nbspaces):
        raise ValueError(
            "fourth argument must be a time domain or a Sequence of time domains "
            "which length is 1 or matches the length of the first argument"
        )
    ntime_domains = cast(Sequence[Sequence[float]], ntime_domains)
    ntime_values = kwargs.get("time_values", "final")
    time_values = kwargs.pop("time_values", "final")
    if (not isinstance(ntime_values, Sequence)) or isinstance(ntime_values, str):
        ntime_values = (ntime_values,)
    if nbspaces > 1:
        if not is_sequence_of_one_or_n_time_values(
            ntime_values, ntime_domains, nbspaces
        ):
            raise ValueError("time_values")
        t_index = (lambda i: 0) if len(ntime_domains) == 1 else (lambda i: i)
        ntime_values = tuple(
            get_time_values(val, ntime_domains[t_index(i)])
            for i, val in enumerate(ntime_values)
        )
        # print("ntime_values: ", ntime_values)
    else:
        if (not is_time_values(time_values, ntime_domains[0])) and isinstance(
            time_values, Sequence
        ):
            time_values = time_values[0]

    if len(ntime_domains) == 1:
        ntime_domains = [ntime_domains[0] for _ in range(nbspaces)]
    if len(ntime_values) == 1:
        ntime_values = [ntime_values[0] for _ in range(nbspaces)]

    nvelocity_domains = _process_velocity_domain_s(velocity_domains, nbspaces)
    nvelocity_values = _process_velocity_values_s(nvelocity_domains, nbspaces, kwargs)
    # print("nvelocity_values: ", nvelocity_values)

    # print("nparameters_values: ", nparameters_values)
    # print("ntime_values: ", ntime_values)
    if not isinstance(kwargs.get("title", ""), str):
        raise ValueError("argument title must be a str")
    suptitle: str = kwargs.pop("title", "")
    if not _is_sequence_str_or_none(kwargs.get("titles", [])):
        raise ValueError("argument titles must be a Sequence of str or None")
    suptitles_temp: list[str | None] = list(kwargs.pop("titles", []))
    for i, s in enumerate(suptitles_temp):
        if s is None:
            suptitles_temp[i] = ""
    while len(suptitles_temp) < nbspaces:
        suptitles_temp.append("")
    suptitles: list[str] = cast(list[str], suptitles_temp)

    lkwargs: Sequence[dict] = [{} for _ in range(nbspaces)]
    for key in kwargs:
        if key in ["parameters_value"]:
            raise KeyError(
                "parameters_value is deprecated; use parameters_values instead"
            )

        if key in ["derivatives"]:
            if kwargs[key] is None or isinstance(kwargs[key], str):
                kwargs[key] = (kwargs[key],)
            if _is_sequence_str_or_none(kwargs[key]):
                kwargs[key] = (kwargs[key],)
            if not _is_sequence_of_one_or_n_derivatives(kwargs[key], nbspaces):
                raise ValueError("derivatives")

        elif key in ["cuts"]:
            # here all cuts must be of the same dim... handle several dims?
            cuts = np.array(kwargs[key])
            if cuts.ndim == 2:  # 1 cut -> list of list of 1 cut
                kwargs[key] = [[kwargs[key]]]
            if cuts.ndim == 3:  # list of cuts -> list of list of cuts
                kwargs[key] = [kwargs[key]]

        elif key in ["velocity_strs"]:
            if _is_sequence_str(kwargs[key]):
                kwargs[key] = [kwargs[key]]

        elif key in ["loss_groups"]:
            if _is_sequence_str(kwargs[key]):
                kwargs[key] = [kwargs[key]]

        elif (not isinstance(kwargs[key], Sequence)) or isinstance(kwargs[key], str):
            kwargs[key] = [kwargs[key]]

        if key in ["loss"]:  # fill with Nones
            if not (len(kwargs[key]) == nbspaces):
                raise ValueError(
                    f"{key} must be a sequence of {nbspaces} {key}; "
                    f"put None if necessary."
                )

        else:
            if not (len(kwargs[key]) == nbspaces or len(kwargs[key]) == 1):
                raise ValueError(
                    f"{key} must be a sequence of {nbspaces} or 1 {key}; "
                    f"put None if necessary."
                )

            if len(kwargs[key]) == 1:
                kwargs[key] *= nbspaces

        for i, _ in enumerate(nspaces):
            (lkwargs[i])[key] = (kwargs[key])[i]

    if nbspaces == 1:
        (lkwargs[0])["parameters_values"] = parameters_values
        (lkwargs[0])["time_values"] = time_values
        (lkwargs[0])["velocity_values"] = nvelocity_values
        (lkwargs[0])["title"] = suptitle
        plot_abstract_approx_space(
            nspaces[0],
            nspatial_domains[0],
            nparameters_domains[0],
            ntime_domains[0],
            nvelocity_domains[0],
            **(lkwargs[0]),
        )
    else:
        nvelocity_values = cast(Sequence[Sequence[np.ndarray]], nvelocity_values)
        oneline = True
        sizeofobjects = [4, 3]

        nbmaxcols = 0
        for i, space in enumerate(nspaces):
            _, nblines, nbcols, _ = get_objects_nblines_nbcols(
                nspatial_domains[i].dim,
                oneline,
                nparameters_values[i],
                ntime_values[i],
                nvelocity_values[i],
                components[i],
                **(lkwargs[i]),
            )
            nbmaxcols = max(nbmaxcols, nbcols)
            # print("nblines: ", nblines)

        nblines = nbspaces
        fig = plt.figure(
            figsize=(sizeofobjects[0] * nbcols, sizeofobjects[1] * nblines),
            layout="constrained",
        )

        subfigs = fig.subfigures(nbspaces, 1, wspace=0.07)
        for i, space in enumerate(nspaces):
            if nspatial_domains[i].dim == 1:  # call plot_1x_AbstractApproxSpace
                if (nvelocity_domains[i] is not None) and (
                    nvelocity_domains[i].dim == 1
                ):
                    __plot_1x1v_abstract_approx_space(
                        subfigs[i],
                        space,
                        nspatial_domains[i],
                        nvelocity_domains[i],
                        nparameters_values[i],
                        ntime_values[i],
                        components[i],
                        oneline,
                        **(lkwargs[i]),
                    )
                else:
                    __plot_1x_abstract_approx_space(
                        subfigs[i],
                        space,
                        nspatial_domains[i],
                        nparameters_values[i],
                        ntime_values[i],
                        nvelocity_values[i],
                        components[i],
                        oneline,
                        **(lkwargs[i]),
                    )
            elif nspatial_domains[i].dim == 2:  # call plot_2x_AbstractApproxSpace
                __plot_2x_abstract_approx_space(
                    subfigs[i],
                    space,
                    nspatial_domains[i],
                    nparameters_values[i],
                    ntime_values[i],
                    nvelocity_values[i],
                    components[i],
                    oneline,
                    **(lkwargs[i]),
                )
            else:
                raise NotImplementedError("Only 1d and 2d are supported")
            if len(suptitles[i]):
                subfigs[i].suptitle(suptitles[i], fontsize="x-large", x=0.01, ha="left")

        if len(suptitle):
            fig.suptitle(suptitle, fontsize="xx-large", ha="center")

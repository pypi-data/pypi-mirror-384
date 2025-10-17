"""Plotting functions (generic in geometric dimension) for time-discrete schemes."""

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.domain.mesh_based_domain.cuboid import Cuboid
from scimba_torch.domain.meshless_domain.base import SurfacicDomain, VolumetricDomain
from scimba_torch.integration.monte_carlo import TensorizedSampler
from scimba_torch.integration.monte_carlo_parameters import UniformParametricSampler
from scimba_torch.numerical_solvers.temporal_pde.time_discrete import (
    ExplicitTimeDiscreteScheme,
)
from scimba_torch.plots.plots_nd import plot_abstract_approx_spaces


def plot_time_discrete_scheme(
    scheme: ExplicitTimeDiscreteScheme,
    **kwargs,
) -> None:
    """Plot an approximation space obtained with a time-discrete solver.

    Args:
        scheme: the time-discrete solver
        **kwargs: arbitrary keyword arguments

    Keyword Args:
        parameters_values: a (list of) point(s) in the parameters domain,
            or "mean" or "random", defaults to "mean",
        velocity_values: a list of point(s) in the velocity domain,
        derivatives: a list of strings representing the derivatives to be plot,
            for instance "uxx"; defaults to [],
        solution: a callable depending on the same args as space to be plot,
        error: plot the absolute error with respect to the given solution,
        title: a str
        ...: see examples

    Implemented only for 1 and 2 dimensional spaces

    Raises:
        AttributeError: some arguments are missing necessary attributes
        NotImplementedError: some option combinations are not implemented yet

    Examples:
        >>> import matplotlib.pyplot as plt
        >>> from scimba_torch.plots.plot_time_discrete_scheme
                import plot_time_discrete_scheme
        >>> ...
        >>> def exact(t: LabelTensor, x: LabelTensor, mu: LabelTensor):
                ...
        >>> plot_time_discrete_scheme(
                scheme,
                solution=exact,
                error=exact,
                derivatives=["ux"],
            )
        >>> plt.show()
    """
    spaces = (
        (scheme.initial_space,)
        + tuple(space for space in scheme.saved_spaces)
        + (scheme.projector.space,)
    )

    #
    if not hasattr(scheme.pde, "space"):
        raise AttributeError("scheme.pde must have an attribute space")
    assert hasattr(scheme.pde, "space")
    assert isinstance(scheme.pde.space, AbstractApproxSpace)

    lspace: AbstractApproxSpace = scheme.pde.space

    if not hasattr(lspace, "spatial_domain"):
        raise AttributeError("scheme.pde.space must have an attribute spatial_domain")
    assert hasattr(lspace, "spatial_domain")
    assert isinstance(lspace.spatial_domain, VolumetricDomain) or isinstance(
        lspace.spatial_domain, Cuboid
    )

    if not hasattr(lspace, "type_space"):
        raise AttributeError("scheme.pde.space must have an attribute type_space")
    assert hasattr(lspace, "type_space")

    if lspace.type_space not in ["space", "phase_space"]:
        raise NotImplementedError(
            "plot_time_discrete_scheme not implemented for type_space %s"
            % lspace.type_space
        )

    spatial_domain: VolumetricDomain | Cuboid = lspace.spatial_domain
    velocity_domain: SurfacicDomain | VolumetricDomain | None = None
    if lspace.type_space == "phase_space":
        if not hasattr(lspace, "velocity_domain"):
            raise AttributeError(
                "scheme.pde.space must have an attribute velocity_domain"
            )
        assert hasattr(lspace, "velocity_domain")
        assert isinstance(lspace.velocity_domain, SurfacicDomain) or isinstance(
            lspace.velocity_domain, VolumetricDomain
        )
        velocity_domain = (lspace.velocity_domain,)

    if not hasattr(lspace, "integrator"):
        raise AttributeError("scheme.pde.space must have an attribute integrator")
    assert hasattr(lspace, "integrator")
    assert isinstance(lspace.integrator, TensorizedSampler)

    parameters_domain: list[tuple[float, float]] = []
    for sam in lspace.integrator.list_sampler:
        if isinstance(sam, UniformParametricSampler):
            parameters_domain = sam.bounds

    # print("spaces: ", spaces)
    # print("spatial_domain: ", spatial_domain)

    time_domain = [float(scheme.initial_time), float(scheme.final_time)]
    time_values = (
        (float(scheme.initial_time),)
        + tuple(tval for tval in scheme.saved_times)
        + (float(scheme.final_time),)
    )
    # print("time_domain: ", time_domain)
    # print("time_values: ", time_values)
    # kwargs.pop("time_values", None)

    losses = (
        (scheme.projector.losses,) + tuple(None for _ in scheme.saved_spaces) + (None,)
    )
    kwargs.pop("loss", None)

    # print("kwargs: ", kwargs)
    plot_abstract_approx_spaces(
        spaces,
        spatial_domain,
        parameters_domain,
        time_domain,
        velocity_domain,
        loss=losses,
        time_values=time_values,
        time_discrete=True,
        **kwargs,
    )

"""Create solutions using various ODE integrators."""

from typing import Callable

import torch

from scimba_torch.flows.integrators_ode import (
    euler_midpoint,
    euler_symplectic,
    rk4,
    rk4_symplectic,
    verlet_explicit,
    verlet_implicit,
)


def create_solution(
    x0: torch.Tensor,
    mu: torch.Tensor,
    m: int,
    dt: float,
    f: list[Callable],
    solver: str = "RK4",
) -> tuple[tuple[torch.Tensor, torch.Tensor, torch.Tensor], torch.Tensor]:
    """Create a solution using the specified solver.

    Args:
        x0: initial condition,
        mu: parameter of the equation,
        m: number of time steps,
        dt: time step,
        f: list of functions defining the ODE,
        solver: the solver to use (default: "RK4").

    Returns:
        A tuple containing:
            - A tuple of tensors (t, mu, res) where:
                - t: time steps,
                - mu: parameters repeated for each time step,
                - res: solution at each time step.
            - The solution tensor res.
    """
    # res shape : (nbr_traj, time, pos/mom)
    # x0 shape : (nbr_traj, 2)
    # mu shape : (nbr_traj, nbr_params)
    # nbr_traj = nbr CI * nbr mu
    t = torch.linspace(0, (m - 1) * dt, m)

    # f[0]=DpH, f[1]=DqH
    if solver == "RK4":
        res = rk4(f, mu, x0, t)
        mu_ = torch.repeat_interleave(mu, t.shape[0], dim=1)[..., None]
        t_ = torch.repeat_interleave(t[None, :], x0.shape[0], dim=0)[..., None]
    else:
        mu_ = torch.repeat_interleave(mu, t.shape[0], dim=1)[..., None]
        t_ = torch.repeat_interleave(t[None, :], x0.shape[0], dim=0)[..., None]
        mu_ = torch.repeat_interleave(mu_[:, None, ...], x0.shape[1], dim=1)
        t_ = torch.repeat_interleave(t_[:, None, ...], x0.shape[1], dim=2)

        if solver == "Verlet_explicit":
            res = verlet_explicit(f[0], f[1], mu, x0, t)
        elif solver == "Verlet_implicit":
            res = verlet_implicit(f[0], f[1], mu, x0, t)
        elif solver == "Euler_symplectic":
            res = euler_symplectic(f[0], f[1], mu, x0, t)
        elif solver == "Euler_midpoint":
            res = euler_midpoint(f[0], f[1], mu, x0, t)
        elif solver == "RK4_symplectic":
            res = rk4_symplectic(f[0], f[1], mu, x0, t)
        else:
            print("Erreur !")

    return (t_[..., :-1, :], mu_[..., :-1, :], res[..., :-1, :]), res[..., 1:, :]


def solution_to_training_format(
    data: torch.Tensor, solver: str = "RK4"
) -> torch.Tensor:
    """Convert solution data to training format based on the solver used.

    Args:
        data: The solution tensor to be converted.
        solver: The solver used to generate the solution (default: "RK4").

    Returns:
        The reshaped solution tensor suitable for training.
    """
    if solver == "RK4":
        return data.reshape(data.shape[0] * data.shape[1], data.shape[2])
    else:
        return data.permute(0, 2, 1, 3).reshape(
            data.shape[0] * data.shape[2], data.shape[1] * data.shape[3]
        )

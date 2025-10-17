"""ODE integrators for geometric numerical integration.

This module provides various numerical integrators for ordinary differential equations,
with a focus on structure-preserving (symplectic) methods for Hamiltonian systems.

.. note::
   The implementations are based on the following references: [Hair03]_ and
   [Raz18]_.

.. [Hair03] E. Hairer, C. Lubich, and G. Wanner.
   Geometric numerical integration illustrated by the Störmer-Verlet method.
   Cambridge University Press, 2003.

.. [Raz18] Razafindralandy, D., Hamdouni, A. & Chhay, M.
   A review of some geometric integrators.
   Adv. Model. and Simul. in Eng. Sci. 5, 16 (2018).
   https://doi.org/10.1186/s40323-018-0110-y
"""

from typing import Any, Callable

import scipy as sp
import torch


def rk4(f: Callable, mu: Any, x0: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
    """Generic Runge-Kutta 4th order integrator.

    Args:
        f: Function defining the ODE, of the form f(t, mu, x).
        mu: Additional parameters for the function f.
        x0: Initial condition tensor.
        t: 1D tensor of time points where the solution is computed.

    Returns:
        Tensor containing the solution at each time point in t.
    """
    res_shape = list(x0.shape)
    res_shape.insert(-1, len(t))
    res = torch.zeros(
        res_shape
    )  # res.shape même que x0.shape avec temps (m) ajouté en avant-dernière dim
    print(res.shape)
    res[..., 0, :] = x0

    for i in range(1, len(t)):
        dt = t[i] - t[i - 1]
        k1 = f(t[i - 1], mu, res[..., i - 1, :])
        k2 = f(t[i - 1] + dt / 2, mu, res[..., i - 1, :] + dt * k1 / 2)
        k3 = f(t[i - 1] + dt / 2, mu, res[..., i - 1, :] + dt * k2 / 2)
        k4 = f(t[i - 1] + dt, mu, res[..., i - 1, :] + dt * k3)
        res[..., i, :] = res[..., i, :] + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6

    return res


## EXPLICIT STORMER-VERLET (SEPARATED HAMILTONIANS)
def verlet_explicit(
    d_p_h: Callable, d_q_h: Callable, mu: Any, x0: torch.Tensor, t: torch.Tensor
) -> torch.Tensor:
    """Verlet explicit integrator for separated Hamiltonians.

    Args:
        d_p_h: Function computing the derivative of the Hamiltonian with respect to p.
        d_q_h: Function computing the derivative of the Hamiltonian with respect to q.
        mu: Additional parameters for the functions DpH and DqH.
        x0: Initial condition tensor.
        t: 1D tensor of time points where the solution is computed.

    Returns:
        Tensor containing the solution at each time point in t.
    """
    res_shape = list(x0.shape)
    res_shape.insert(-1, len(t))
    res = torch.zeros(res_shape)
    res[..., 0, :] = x0

    demi = torch.zeros_like(x0[..., 0])

    for i in range(1, len(t)):
        dt = t[i] - t[i - 1]
        demi = res[..., i - 1, 0] + (dt / 2) * d_p_h(res[..., i - 1, 1], mu)
        res[..., i, 1] = res[..., i - 1, 1] - dt * d_q_h(demi, mu)
        res[..., i, 0] = demi + (dt / 2) * d_p_h(res[..., i, 1], mu)

    return res


## IMPLICIT STORMER-VERLET (ALSO FOR NON-SEPARATED HAMILTONIANS)
def verlet_implicit(
    d_p_h: Callable, d_q_h: Callable, mu: Any, x0: torch.Tensor, t: torch.Tensor
) -> torch.Tensor:
    """Verlet implicit integrator for non-separated Hamiltonians.

    Args:
        d_p_h: Function computing the derivative of the Hamiltonian with respect to p.
        d_q_h: Function computing the derivative of the Hamiltonian with respect to q.
        mu: Additional parameters for the functions d_p_h and d_q_h.
        x0: Initial condition tensor.
        t: 1D tensor of time points where the solution is computed.

    Returns:
        Tensor containing the solution at each time point in t.
    """
    res_shape = list(x0.shape)
    res_shape.insert(-1, len(t))
    res = torch.zeros(
        res_shape
    )  # res.shape même que x0.shape avec temps (m) ajouté en avant-dernière dim
    res[..., 0, :] = x0

    demi = torch.zeros_like(x0[..., 0])

    for i in range(1, len(t)):
        dt = t[i] - t[i - 1]

        def f_q(q):
            return res[..., i - 1, 0] + (dt / 2) * d_p_h(q, res[..., i - 1, 1], mu) - q

        demi = sp.optimize.newton(
            f_q,
            res[..., i - 1, 0]
            + (dt / 2) * d_p_h(res[..., i - 1, 0], res[..., i - 1, 1], mu),
            maxiter=1000,
            tol=1e-3,
            disp=False,
        )

        def f_p(p):
            return (
                res[..., i - 1, 1]
                - (dt / 2) * (d_q_h(demi, res[..., i - 1, 1], mu) + d_q_h(demi, p, mu))
                - p
            )

        res[..., i, 1] = sp.optimize.newton(
            f_p,
            res[..., i - 1, 1] - dt * d_q_h(demi, res[..., i - 1, 1], mu),
            maxiter=1000,
            tol=1e-3,
            disp=False,
        )

        res[..., i, 0] = demi + (dt / 2) * d_p_h(demi, res[..., i, 1], mu)

    return res


## SYMPLECTIC EULER
def euler_symplectic(
    d_p_h: Callable, d_q_h: Callable, mu: Any, x0: torch.Tensor, t: torch.Tensor
) -> torch.Tensor:
    """Symplectic Euler integrator for Hamiltonian systems.

    Args:
        d_p_h: Function computing the derivative of the Hamiltonian with respect to p.
        d_q_h: Function computing the derivative of the Hamiltonian with respect to q.
        mu: Additional parameters for the functions d_p_h and d_q_h.
        x0: Initial condition tensor.
        t: 1D tensor of time points where the solution is computed.

    Returns:
        Tensor containing the solution at each time point in t.
    """
    res_shape = list(x0.shape)
    res_shape.insert(-1, len(t))
    res = torch.zeros(
        res_shape
    )  # res.shape même que x0.shape avec temps (m) ajouté en avant-dernière dim
    res[..., 0, :] = x0

    for i in range(1, len(t)):
        dt = t[i] - t[i - 1]

        def f_p(p):
            return res[..., i - 1, 1] - dt * d_q_h(res[..., i - 1, 0], p, mu) - p

        res[..., i, 1] = sp.optimize.newton(
            f_p,
            res[..., i - 1, 1] - dt * d_q_h(res[..., i - 1, 0], res[..., i - 1, 1], mu),
            maxiter=1000,
            tol=1e-3,
            disp=False,
        )
        res[..., i, 0] = res[..., i - 1, 0] + dt * d_p_h(
            res[..., i - 1, 0], res[..., i, 1], mu
        )

    return res


## MIDPOINT EULER
def euler_midpoint(
    d_p_h: Callable, d_q_h: Callable, mu: Any, x0: torch.Tensor, t: torch.Tensor
) -> torch.Tensor:
    """Midpoint Euler integrator for Hamiltonian systems.

    Args:
        d_p_h: Function computing the derivative of the Hamiltonian with respect to p.
        d_q_h: Function computing the derivative of the Hamiltonian with respect to q.
        mu: Additional parameters for the functions d_p_h and d_q_h.
        x0: Initial condition tensor.
        t: 1D tensor of time points where the solution is computed.

    Returns:
        Tensor containing the solution at each time point in t.
    """
    res_shape = list(x0.shape)
    res_shape.insert(-1, len(t))
    res = torch.zeros(
        res_shape
    )  # res.shape same as x0.shape with time (m) added in the second-to-last dimension
    res[..., 0, :] = x0

    for i in range(1, len(t)):
        dt = t[i] - t[i - 1]

        def func(x):
            return (
                res[..., i - 1, :]
                + torch.stack(
                    [
                        dt
                        * d_p_h(
                            (x[:, 0] + res[..., i - 1, 0]) / 2,
                            (x[:, 1] + res[..., i - 1, 1]) / 2,
                            mu,
                        ),
                        -dt
                        * d_q_h(
                            (x[:, 0] + res[..., i - 1, 0]) / 2,
                            (x[:, 1] + res[..., i - 1, 1]) / 2,
                            mu,
                        ),
                    ],
                    axis=-1,
                )
                - x
            )

        res[..., i, :] = sp.optimize.newton(
            func, res[..., i - 1, :], maxiter=1000, tol=1e-3, disp=False
        )

    return res


## GAUSS-LEGENDRE
def gauss_legendre(
    d_p_h: Callable, d_q_h: Callable, mu: Any, x0: torch.Tensor, t: torch.Tensor
) -> torch.Tensor:
    """Gauss-Legendre integrator for Hamiltonian systems.

    Args:
        d_p_h: Function computing the derivative of the Hamiltonian with respect to p.
        d_q_h: Function computing the derivative of the Hamiltonian with respect to q.
        mu: Additional parameters for the functions d_p_h and d_q_h.
        x0: Initial condition tensor.
        t: 1D tensor of time points where the solution is computed.

    Returns:
        Tensor containing the solution at each time point in t.
    """
    res_shape = list(x0.shape)
    res_shape.insert(-1, len(t))
    res = torch.zeros(
        res_shape
    )  # res.shape same as x0.shape with time (m) added in the second-to-last dimension
    res[..., 0, :] = x0

    for i in range(1, len(t)):
        dt = t[i] - t[i - 1]
        start = torch.stack(
            [
                res[..., i - 1, 0],
                res[..., i - 1, 0],
                res[..., i - 1, 1],
                res[..., i - 1, 1],
            ]
        )

        def func(y):
            return y - torch.stack(
                [
                    res[..., i - 1, 0]
                    + dt
                    * (
                        d_p_h(y[0], y[2], mu) / 4
                        + (3 - 2 * torch.sqrt(3)) * d_p_h(y[1], y[3], mu) / 12
                    ),
                    res[..., i - 1, 0]
                    + dt
                    * (
                        (3 + 2 * torch.sqrt(3)) * d_p_h(y[0], y[2], mu) / 12
                        + d_p_h(y[1], y[3], mu) / 4
                    ),
                    res[..., i - 1, 1]
                    - dt
                    * (
                        d_q_h(y[0], y[2], mu) / 4
                        + (3 - 2 * torch.sqrt(3)) * d_q_h(y[1], y[3], mu) / 12
                    ),
                    res[..., i - 1, 1]
                    - dt
                    * (
                        (3 + 2 * torch.sqrt(3)) * d_q_h(y[0], y[2], mu) / 12
                        + d_q_h(y[1], y[3], mu) / 4
                    ),
                ]
            )

        Y = sp.optimize.newton(func, start, maxiter=1000, tol=1e-3, disp=False)
        res[..., i, 1] = (
            res[..., i - 1, 1]
            - dt * (d_q_h(Y[0], Y[2], mu) + d_q_h(Y[1], Y[3], mu)) / 2
        )
        res[..., i, 0] = (
            res[..., i - 1, 0]
            + dt * (d_p_h(Y[0], Y[2], mu) + d_p_h(Y[1], Y[3], mu)) / 2
        )

    return res


## RK4 SYMPLECTIC
def rk4_symplectic(
    d_p_h: Callable, d_q_h: Callable, mu: Any, x0: torch.Tensor, t: torch.Tensor
) -> torch.Tensor:
    """RK4 symplectic integrator for Hamiltonian systems.

    Args:
        d_p_h: Function computing the derivative of the Hamiltonian with respect to p.
        d_q_h: Function computing the derivative of the Hamiltonian with respect to q.
        mu: Additional parameters for the functions d_p_h and d_q_h.
        x0: Initial condition tensor.
        t: 1D tensor of time points where the solution is computed.

    Returns:
        Tensor containing the solution at each time point in t.
    """
    res_shape = list(x0.shape)
    res_shape.insert(-1, len(t))
    res = torch.zeros(
        res_shape
    )  # res.shape same as x0.shape with time (m) added in the second-to-last dimension
    res[..., 0, :] = x0

    b = (2 + 2 ** (1 / 2) + 2 ** (-1 / 3)) / 3

    for i in range(1, len(t)):
        dt = t[i] - t[i - 1]

        def func(y):
            return y - torch.stack(
                [
                    res[..., i - 1, 0] + dt * b * d_p_h(y[0], y[1], mu) / 2,
                    res[..., i - 1, 1] - dt * b * d_q_h(y[0], y[1], mu) / 2,
                ]
            )

        PQ1 = sp.optimize.newton(
            func,
            torch.stack([res[..., i - 1, 0], res[..., i - 1, 1]]),
            maxiter=1000,
            tol=1e-3,
            disp=False,
        )

        def func(y):
            return y - torch.stack(
                [
                    res[..., i - 1, 0]
                    + dt
                    * (
                        b * d_p_h(PQ1[0], PQ1[1], mu)
                        + (1 / 2 - b) * d_p_h(y[0], y[1], mu)
                    ),
                    res[..., i - 1, 1]
                    - dt
                    * (
                        b * d_q_h(PQ1[0], PQ1[1], mu)
                        + (1 / 2 - b) * d_q_h(y[0], y[1], mu)
                    ),
                ]
            )

        PQ2 = sp.optimize.newton(func, PQ1, maxiter=1000, tol=1e-3, disp=False)

        def func(y):
            return y - torch.stack(
                [
                    res[..., i - 1, 0]
                    + dt
                    * (
                        b * d_p_h(PQ1[0], PQ1[1], mu)
                        + (1 - 2 * b) * d_p_h(PQ2[0], PQ2[1], mu)
                        + b * d_p_h(y[0], y[1], mu) / 2
                    ),
                    res[..., i - 1, 1]
                    - dt
                    * (
                        b * d_q_h(PQ1[0], PQ1[1], mu)
                        + (1 - 2 * b) * d_q_h(PQ2[0], PQ2[1], mu)
                        + b * d_q_h(y[0], y[1], mu) / 2
                    ),
                ]
            )

        PQ3 = sp.optimize.newton(func, PQ2, maxiter=1000, tol=1e-3, disp=False)

        res[..., i, 1] = res[..., i - 1, 1] - dt * (
            b * d_q_h(PQ1[0], PQ1[1], mu)
            + (1 - 2 * b) * d_q_h(PQ2[0], PQ2[1], mu)
            + b * d_q_h(PQ3[0], PQ3[1], mu)
        )
        res[..., i, 0] = res[..., i - 1, 0] + dt * (
            b * d_p_h(PQ1[0], PQ1[1], mu)
            + (1 - 2 * b) * d_p_h(PQ2[0], PQ2[1], mu)
            + b * d_p_h(PQ3[0], PQ3[1], mu)
        )

    return res

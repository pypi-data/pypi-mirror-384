"""Linesearch functions."""

from typing import Callable

import torch


def logarithmic_grid_line_search(
    loss: Callable[[torch.Tensor], torch.Tensor],
    theta: torch.Tensor,  # shape (1,p)
    dsearch: torch.Tensor,  # shape (p,)
    m: int = 10,
    interval: list[float] = [0.0, 1.0],
    log_basis: float = 2.0,
    **kwargs,
) -> torch.Tensor:
    """Line search algorithm based on a logarithmic grid.

    Args:
        loss: The loss function.
        theta: The current parameters of the loss.
        dsearch: The search direction.
        m: The number of points in the logarithmic grid.
        interval: The interval of the logarithmic grid.
        log_basis: The logarithmic basis to generate the grid.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        An eta minimizing the loss along the search direction from theta.

    Raises:
        ValueError: when log_basis <= 0.
    """
    # print("M: ", M, "interval: ", interval, "log_basis: ", log_basis)

    if log_basis <= 0.0:
        raise ValueError("log_basis in logarithmic_grid_line_search has to be >0")

    # get the interval
    a, b = interval
    # get the logarithmic grid etas
    etas = a + (b - a) * torch.pow(
        log_basis, torch.tensor(range(-m + 1, 1), dtype=torch.int, requires_grad=False)
    )
    # print("etas", etas)
    # get the parameters grid thetas
    thetas = theta - etas[:, None] * dsearch
    # get the loss values
    loss_values = loss(thetas)
    # print("loss_values", loss_values)
    # get the index of the minimum loss
    idx_min = torch.argmin(loss_values)
    # return the eta minimizing the loss
    return etas[idx_min]


def backtracking_armijo_line_search_with_loss_theta_grad_loss_theta(
    loss: Callable[[torch.Tensor], torch.Tensor],
    theta: torch.Tensor,  # shape (p)
    loss_theta: torch.Tensor,  # shape (1,)
    grad_loss_theta: torch.Tensor,  # shape (p,)
    dsearch: torch.Tensor,  # shape (p,)
    alpha: float = 0.01,
    beta: float = 0.5,
    n_step_max: int = 10,
    **kwargs,
) -> torch.Tensor:
    """Line search algorithm based on the Armijo condition.

    Args:
        loss: The loss function.
        theta: The current parameters of the loss.
        loss_theta: The loss at theta.
        grad_loss_theta: The gradient of the loss at theta.
        dsearch: The search direction.
        alpha: The Armijo condition parameter.
        beta: The Armijo condition parameter.
        n_step_max: The maximum number of steps in the backtracking algorithm.
        **kwargs: Arbitrary keyword arguments.

    Returns:
            An eta minimizing the loss along the search direction from theta.
    """
    # print("n_step_max: ", n_step_max, "alpha: ", alpha, "beta: ", beta)
    eta = torch.tensor(1.0)
    dL = torch.dot(grad_loss_theta, dsearch)
    nbsteps = 0
    while (loss(theta - eta * dsearch) > loss_theta - alpha * eta * dL) and (
        nbsteps < n_step_max
    ):
        eta *= beta
        nbsteps += 1
    return eta


def backtracking_armijo_line_search(
    loss: Callable[[torch.Tensor], torch.Tensor],
    grad_loss: Callable[[torch.Tensor], torch.Tensor],
    theta: torch.Tensor,  # shape (1,p)
    dsearch: torch.Tensor,  # shape (p)
    alpha: float = 0.1,
    beta: float = 0.5,
    n_step_max: int = 10,
    **kwargs,
) -> torch.Tensor:
    """Line search algorithm based on the Armijo condition.

    Args:
        loss: The loss function.
        grad_loss: The gradient function of the loss function.
        theta: The current parameters of the loss.
        dsearch: The search direction.
        alpha: The Armijo condition parameter.
        beta: The Armijo condition parameter.
        n_step_max: The maximum number of steps in the backtracking algorithm.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        An eta minimizing the loss along the search direction from theta.
    """
    Ltheta = loss(theta)
    gradltheta = grad_loss(theta[0, :])
    return backtracking_armijo_line_search_with_loss_theta_grad_loss_theta(
        loss, theta, Ltheta, gradltheta, dsearch, alpha, beta, n_step_max
    )


if __name__ == "__main__":  # pragma: no cover
    from scimba_torch.approximation_space.nn_space import NNxSpace
    from scimba_torch.domain.meshless_domain.domain_2d import Disk2D, Square2D
    from scimba_torch.integration.monte_carlo import DomainSampler, TensorizedSampler
    from scimba_torch.integration.monte_carlo_parameters import UniformParametricSampler
    from scimba_torch.neural_nets.coordinates_based_nets.mlp import GenericMLP
    from scimba_torch.numerical_solvers.elliptic_pde.deep_ritz import DeepRitzElliptic
    from scimba_torch.numerical_solvers.elliptic_pde.pinns import PinnsElliptic
    from scimba_torch.optimizers.losses import GenericLosses
    from scimba_torch.optimizers.optimizers_data import OptimizerData
    from scimba_torch.physical_models.elliptic_pde.laplacians import (
        Laplacian2DDirichletRitzForm,
        Laplacian2DDirichletStrongForm,
    )
    from scimba_torch.utils.scimba_tensors import LabelTensor

    print(" ######################################################## ")
    print(" # line_search with a pinn with weak boundary condition # ")
    print(" ######################################################## ")

    def f_rhs(x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        """For tests.

        Args:
            x: test.
            mu: test.

        Returns:
            test.
        """
        x1, x2 = x.get_components()
        mu1 = mu.get_components()
        return (
            mu1
            * 8.0
            * torch.pi
            * torch.pi
            * torch.sin(2.0 * torch.pi * x1)
            * torch.sin(2.0 * torch.pi * x2)
        )

    def f_bc(x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        """For tests.

        Args:
            x: test.
            mu: test.

        Returns:
            test.
        """
        x1, _ = x.get_components()
        return x1 * 0.0

    domain_x = Square2D([(0.0, 1), (0.0, 1)], is_main_domain=True)
    sampler = TensorizedSampler(
        [DomainSampler(domain_x), UniformParametricSampler([(1.0, 2.0)])]
    )
    space = NNxSpace(
        1,
        1,
        GenericMLP,
        domain_x,
        sampler,
        layer_sizes=[60] * 3,
    )
    pde = Laplacian2DDirichletStrongForm(space, f=f_rhs, g=f_bc)
    losses = GenericLosses(
        [
            ("residual", torch.nn.MSELoss(), 1.0),
            ("bc", torch.nn.MSELoss(), 40.0),
        ],
    )
    opt_1 = {
        "name": "adam",
        "optimizer_args": {"lr": 2.5e-2, "betas": (0.9, 0.999)},
    }
    opt = OptimizerData(opt_1)
    pinns = PinnsElliptic(pde, bc_type="weak", optimizers=opt, losses=losses)
    n_collocation = 2000
    n_bc_collocation = 1500
    # get current parameters of the nn
    params_vect = pinns.space.get_dof(flag_scope="all", flag_format="tensor")
    # get func and derivative
    Lpinn, GradLpinn = pinns.get_loss_grad_loss(
        n_collocation=n_collocation, n_bc_collocation=n_bc_collocation
    )
    loss = Lpinn(params_vect)
    print("loss at theta = initial parameters: ", loss)
    theta = params_vect.clone().detach().requires_grad_(False)
    loss = Lpinn(theta)
    gradltheta = GradLpinn(theta)
    loss2 = Lpinn(theta)
    gradltheta2 = GradLpinn(theta)
    assert torch.equal(loss, loss2)
    assert torch.equal(gradltheta, gradltheta2)
    # perform a linesearch along gradLTheta
    print("Lpinn(theta): ", Lpinn(theta))
    eta = backtracking_armijo_line_search_with_loss_theta_grad_loss_theta(
        Lpinn, theta, loss, gradltheta, gradltheta, alpha=0.2, beta=0.5, n_step_max=1000
    )
    print("eta with Armijo : ", eta)
    print("Lpinn(theta): ", Lpinn(theta))
    print("Lpinn(theta - eta * dsearch): ", Lpinn(theta - eta * gradltheta))
    assert torch.all(Lpinn(theta) > Lpinn(theta - eta * gradltheta))
    print("\n")

    eta = logarithmic_grid_line_search(
        Lpinn, theta, gradltheta, m=10, interval=[0.0, 1.0]
    )
    print("eta with logarithmic grid : ", eta)
    print("Lpinn(theta): ", Lpinn(theta))
    print("Lpinn(theta - eta * dsearch): ", Lpinn(theta - eta * gradltheta))
    assert torch.all(Lpinn(theta) > Lpinn(theta - eta * gradltheta))
    print("\n")

    # get func and derivative with new sampling points
    loss = Lpinn(theta)
    Lpinn, GradLpinn = pinns.get_loss_grad_loss(
        n_collocation=n_collocation, n_bc_collocation=n_bc_collocation
    )
    assert not torch.equal(Lpinn(theta), loss)
    # actualize theta
    theta = theta - eta * gradltheta
    loss = Lpinn(theta)
    gradltheta = GradLpinn(theta)
    # perform a linesearch along gradLTheta
    print("Lpinn(theta): ", Lpinn(theta))
    eta = backtracking_armijo_line_search_with_loss_theta_grad_loss_theta(
        Lpinn, theta, loss, gradltheta, gradltheta, alpha=0.2, beta=0.5, n_step_max=1000
    )
    print("eta with Armijo : ", eta)
    print("Lpinn(theta): ", Lpinn(theta))
    print("Lpinn(theta - eta * dsearch): ", Lpinn(theta - eta * gradltheta))
    assert torch.all(Lpinn(theta) > Lpinn(theta - eta * gradltheta))
    print("\n")
    # get func and derivative with new sampling points
    loss = Lpinn(theta)
    Lpinn, GradLpinn = pinns.get_loss_grad_loss(
        n_collocation=n_collocation, n_bc_collocation=n_bc_collocation
    )
    assert not torch.equal(Lpinn(theta), loss)
    # actualize theta
    theta = theta - eta * gradltheta
    loss = Lpinn(theta)
    gradltheta = GradLpinn(theta)
    # perform a linesearch along gradltheta
    print("Lpinn(theta): ", Lpinn(theta))
    eta = backtracking_armijo_line_search_with_loss_theta_grad_loss_theta(
        Lpinn, theta, loss, gradltheta, gradltheta, alpha=0.2, beta=0.5, n_step_max=1000
    )
    print("eta with Armijo : ", eta)
    print("Lpinn(theta): ", Lpinn(theta))
    print("Lpinn(theta - eta * dsearch): ", Lpinn(theta - eta * gradltheta))
    assert torch.all(Lpinn(theta) > Lpinn(theta - eta * gradltheta))
    print("\n")

    print(" ############################################################ ")
    print(" # line_search with a deep_ritz with weak boundary condition # ")
    print(" ############################################################ ")

    domain_x = Disk2D(torch.tensor([0.0, 0.0]), radius=1, is_main_domain=True)
    sampler = TensorizedSampler(
        [DomainSampler(domain_x), UniformParametricSampler([(1.0, 1.0001)])]
    )
    space = NNxSpace(
        1,
        1,
        GenericMLP,
        domain_x,
        sampler,
        layer_sizes=[30] * 3,
    )
    pde = Laplacian2DDirichletRitzForm(space, f=f_rhs, g=f_bc)
    losses = GenericLosses(
        [
            ("residual", torch.nn.MSELoss(), 1.0),
            ("bc", torch.nn.MSELoss(), 40.0),
        ],
    )
    opt_1 = {
        "name": "adam",
        "optimizer_args": {"lr": 2.5e-2, "betas": (0.9, 0.999)},
    }
    opt = OptimizerData(opt_1)
    ritz = DeepRitzElliptic(pde, bc_type="weak", optimizers=opt, losses=losses)
    n_collocation = 2000
    n_bc_collocation = 1500

    # get current parameters of the nn
    params_vect = ritz.space.get_dof(flag_scope="all", flag_format="tensor")
    # get func and derivative
    Lritz, GradLritz = ritz.get_loss_grad_loss(
        n_collocation=n_collocation, n_bc_collocation=n_bc_collocation
    )
    loss = Lritz(params_vect)
    print("loss at theta = initial parameters: ", loss)
    theta = params_vect.clone().detach().requires_grad_(False)
    loss = Lritz(theta)
    gradltheta = GradLritz(theta)
    loss2 = Lritz(theta)
    gradltheta2 = GradLritz(theta)
    assert torch.equal(loss, loss2)
    assert torch.equal(gradltheta, gradltheta2)
    # perform a linesearch along gradLTheta
    print("Lritz(theta): ", Lritz(theta))
    eta = backtracking_armijo_line_search_with_loss_theta_grad_loss_theta(
        Lritz, theta, loss, gradltheta, gradltheta, alpha=0.2, beta=0.5, n_step_max=1000
    )
    print("eta with Armijo : ", eta)
    print("Lritz(theta): ", Lritz(theta))
    print("Lritz(theta - eta * dsearch): ", Lritz(theta - eta * gradltheta))
    assert torch.all(Lritz(theta) > Lritz(theta - eta * gradltheta))
    print("\n")

    eta = logarithmic_grid_line_search(
        Lritz, theta, gradltheta, m=10, interval=[0.0, 1.0]
    )
    print("eta with logarithmic grid : ", eta)
    print("Lritz(theta): ", Lritz(theta))
    print("Lritz(theta - eta * dsearch): ", Lritz(theta - eta * gradltheta))
    # assert torch.all(Lritz(theta) > Lritz(theta - eta * gradltheta))
    print("\n")

    # get func and derivative with new sampling points
    loss = Lritz(theta)
    Lritz, GradLritz = ritz.get_loss_grad_loss(
        n_collocation=n_collocation, n_bc_collocation=n_bc_collocation
    )
    assert not torch.equal(Lritz(theta), loss)
    # actualize theta
    theta = theta - eta * gradltheta
    loss = Lritz(theta)
    gradltheta = GradLritz(theta)
    # perform a linesearch along gradLTheta
    print("Lritz(theta): ", Lritz(theta))
    eta = backtracking_armijo_line_search_with_loss_theta_grad_loss_theta(
        Lritz, theta, loss, gradltheta, gradltheta, alpha=0.2, beta=0.5, n_step_max=1000
    )
    print("eta with Armijo : ", eta)
    print("Lritz(theta): ", Lritz(theta))
    print("Lritz(theta - eta * dsearch): ", Lritz(theta - eta * gradltheta))
    assert torch.all(Lritz(theta) > Lritz(theta - eta * gradltheta))
    print("\n")

    eta = logarithmic_grid_line_search(
        Lritz, theta, gradltheta, m=10, interval=[0.0, 1.0]
    )
    print("eta with logarithmic grid : ", eta)
    print("Lritz(theta): ", Lritz(theta))
    print("Lritz(theta - eta * dsearch): ", Lritz(theta - eta * gradltheta))
    # assert torch.all(Lritz(theta) > Lritz(theta - eta * gradltheta))
    print("\n")

    # get func and derivative with new sampling points
    loss = Lritz(theta)
    Lritz, GradLritz = ritz.get_loss_grad_loss(
        n_collocation=n_collocation, n_bc_collocation=n_bc_collocation
    )
    assert not torch.equal(Lritz(theta), loss)
    # actualize theta
    theta = theta - eta * gradltheta
    loss = Lritz(theta)
    gradltheta = GradLritz(theta)
    # perform a linesearch along gradLTheta
    print("Lritz(theta): ", Lritz(theta))
    eta = backtracking_armijo_line_search_with_loss_theta_grad_loss_theta(
        Lritz, theta, loss, gradltheta, gradltheta, alpha=0.2, beta=0.5, n_step_max=1000
    )
    print("eta with Armijo : ", eta)
    print("Lritz(theta): ", Lritz(theta))
    print("Lritz(theta - eta * dsearch): ", Lritz(theta - eta * gradltheta))
    assert torch.all(Lritz(theta) > Lritz(theta - eta * gradltheta))
    print("\n")

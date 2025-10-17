"""Differents activation layers and adaptive activation layers.

All the activation functions take `**kwargs` for the initialization in order
to have the same signature for all activation functions.
"""

from typing import Any

import torch


class AdaptativeTanh(torch.nn.Module):
    """Class for tanh activation function with adaptive parameter.

    Args:
        **kwargs: Keyword arguments including:

            * `mu` (:code:`float`): the mean of the Gaussian law. Defaults to 0.0.
            * `sigma` (:code:`float`): std of the Gaussian law. Defaults to 0.1.
    """

    def __init__(self, **kwargs: Any):
        super().__init__()
        mu = kwargs.get("mu", 0.0)
        sigma = kwargs.get("sigma", 0.1)
        self.a = torch.nn.Parameter(
            torch.randn(()) * sigma + mu
        )  #: The parameter of the tanh.

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the activation function to a tensor x.

        Args:
            x: Input tensor.

        Returns:
            The tensor after the application of the tanh function.
        """
        exp_p = torch.exp(self.a * x)
        exp_m = 1 / exp_p
        return (exp_p - exp_m) / (exp_p + exp_m)


class Hat(torch.nn.Module):
    """Class for Hat activation function.

    Args:
        **kwargs: Keyword arguments (not used here).
    """

    def __init__(self, **kwargs: Any):
        super().__init__()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the activation function to a tensor x.

        Args:
            x: Input tensor.

        Returns:
            The tensor after the application of the activation function.
        """
        left_part = torch.relu(1 + x) * (x <= 0)
        right_part = torch.relu(1 - x) * (x > 0)
        return left_part + right_part


class RegularizedHat(torch.nn.Module):
    """Class for Regularized Hat activation function.

    Args:
        **kwargs: Keyword arguments (not used here).
    """

    def __init__(self, **kwargs: Any):
        super().__init__()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the activation function to a tensor x.

        Args:
            x: Input tensor.

        Returns:
            The tensor after the application of the activation function.
        """
        return torch.exp(-12 * torch.tanh(x**2 / 2))


class Sine(torch.nn.Module):
    """Class for Sine activation function.

    Args:
        **kwargs: Keyword arguments including:
            - freq: The frequency of the sinus. Defaults to 1.0.
    """

    def __init__(self, **kwargs: Any):
        super().__init__()
        self.freq = kwargs.get("freq", 1.0)  #: The frequency of the sinus.

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the activation function to a tensor x.

        Args:
            x: Input tensor.

        Returns:
            The tensor after the application of the sine function.
        """
        return torch.sin(self.freq * x)


class Cosin(torch.nn.Module):
    """Class for Cosine activation function.

    Args:
        **kwargs: Keyword arguments including:

            * `freq` (:code:`float`): The frequency of the cosine. Defaults to 1.0.
    """

    def __init__(self, **kwargs: Any):
        super().__init__()
        self.freq = kwargs.get("freq", 1.0)  #: The frequency of the cosine.

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the activation function to a tensor x.

        Args:
            x: Input tensor.

        Returns:
            The tensor after the application of the cosine function.
        """
        return torch.cos(self.freq * x)


class Heaviside(torch.nn.Module):
    r"""Class for Regularized Heaviside activation function.

    .. math::
        H_k(x) &= 1/(1+e^{-2 k x}) \\
        k >> 1,  \quad H_k(x) &= H(x)

    Args:
        **kwargs: Keyword arguments including:

            * `k` (:code:`float`): the regularization parameter. Defaults to 100.0.
    """

    def __init__(self, **kwargs: Any):
        super().__init__()
        self.k = kwargs.get("k", 100.0)  #: The regularization parameter.

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the activation function to a tensor x.

        Args:
            x: Input tensor.

        Returns:
            The tensor after the application to the sigmoid function.
        """
        return 1.0 / (1.0 + torch.exp(-2.0 * self.k * x))


class Tanh(torch.nn.Module):
    """Tanh activation function.

    Args:
        **kwargs: Keyword arguments (not used here).
    """

    def __init__(self, **kwargs: Any):
        super().__init__()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the activation function to a tensor x.

        Args:
            x: Input tensor.

        Returns:
            The tensor after the application to the tanh function.
        """
        return torch.tanh(x)


class Id(torch.nn.Module):
    r"""Identity activation function."""

    def __init__(self):
        super().__init__()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the activation function to a tensor x.

        Args:
            x: Input tensor.

        Returns:
            The input tensor unchanged (identity function).
        """
        return x


class SiLU(torch.nn.Module):
    """SiLU activation function.

    Args:
        **kwargs: Keyword arguments (not used here).
    """

    def __init__(self, **kwargs: Any):
        super().__init__()
        self.ac = torch.nn.SiLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the activation function to a tensor x.

        Args:
            x: Input tensor.

        Returns:
            The tensor after the application of the SiLU function.
        """
        return self.ac.forward(x)


class Swish(torch.nn.Module):
    """Swish activation function.

    Args:
        **kwargs: Keyword arguments including:

            - learnable: Whether the beta parameter is learnable. Defaults to False.
            - beta: The beta parameter. Defaults to 1.0.
    """

    def __init__(self, **kwargs: Any):
        super().__init__()
        self.learnable = kwargs.get("learnable", False)  #: Whether beta is learnable.
        self.beta = kwargs.get("beta", 1.0)  #: The beta parameter.
        if self.learnable:
            self.beta = self.a = torch.nn.Parameter(1.0 + torch.randn(()) * 0.1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the activation function to a tensor x.

        Args:
            x: Input tensor.

        Returns:
            The tensor after the application of the Swish function.
        """
        return x / (1 + torch.exp(-self.beta * x))


class Sigmoid(torch.nn.Module):
    """Sigmoid activation function.

    Args:
        **kwargs: Keyword arguments (not used here).
    """

    def __init__(self, **kwargs: Any):
        super().__init__()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the activation function to a tensor x.

        Args:
            x: Input tensor.

        Returns:
            The tensor after the application of the sigmoid function.
        """
        return torch.sigmoid(x)


class Wavelet(torch.nn.Module):  # noqa: D101
    pass


class RbfSinus(torch.nn.Module):  # noqa: D101
    pass


# Activation function non local to the dimension (we do not apply the same
# transformation at each dimension)


class IsotropicRadial(torch.nn.Module):
    r"""Isotropic radial basis activation.

    It is of the form: :math:`\phi(x,m,\sigma)` with :math:`m` the center of the
    function and :math:`\sigma` the shape parameter.

    Currently implemented:
        -  :math:`\phi(x,m,\sigma)= exp^{-\mid x-m \mid^2 \sigma^2}`
        -  :math:`\phi(x,m,\sigma)= 1/\sqrt(1+(\mid x-m\mid \sigma^2)^2)`

    we use the Lp norm.

    Args:
        in_size: Size of the inputs.
        m: Center tensor for the radial basis function.
        **kwargs: Keyword arguments including:

            * `norm` (:code:`int`): Number of norm. Defaults to 2.
            * `type_rbf` (:code:`str`): Type of RBF ("gaussian" or other).
              Defaults to "gaussian".

    Learnable Parameters:
        mu: The list of the center of the radial basis function (size= in_size).
        sigma: The shape parameter of the radial basis function.
    """

    def __init__(self, in_size: int, m: torch.Tensor, **kwargs):
        super().__init__()
        self.dim = in_size
        self.norm = kwargs.get("norm", 2)
        m_no_grad = m.detach()
        self.m = torch.nn.Parameter(m_no_grad)
        self.sig = torch.nn.Parameter(torch.abs(10 * torch.randn(()) * 0.1 + 0.01))
        self.type_rbf = kwargs.get("type_rbf", "gaussian")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the activation function to a tensor x.

        Args:
            x: Input tensor.

        Returns:
            The tensor after the application of the radial basis function.
        """
        norm = torch.norm(x - self.m, p=self.norm, dim=1) ** self.norm
        norm = norm[:, None]
        if self.type_rbf == "gaussian":
            exp_m = torch.exp(-norm / self.sig**2)
        else:
            exp_m = 1.0 / (1.0 + (norm * self.sig**2) * 2.0) ** 0.5
        return exp_m


class AnisotropicRadial(torch.nn.Module):
    r"""Anisotropic radial basis activation.

    It is of the form: :math:`\phi(x,m,\sigma)` with :math:`m` the center of the
    function and :math:`\Sigma=A A^t + 0.01 I_d` the matrix shape parameter.

    Currently implemented:

    -  :math:`\phi(x,m,\Sigma)= exp^{- ((x-m),\Sigma(x-m))}`
    -  :math:`\phi(x,m,\Sigma)= 1/\sqrt(1+((x-m,\Sigma(x-m)))^2)`

    we use the Lp norm.

    Args:
        in_size: Size of the inputs.
        m: Center tensor for the radial basis function.
        **kwargs: Keyword arguments including `type_rbf` (:code:`str`): Type of RBF
          ("gaussian" or other). Defaults to "gaussian".

    Learnable Parameters:

    - :code:`mu`: The list of the center of the radial basis function (size= in_size).
    - :code:`A`: The shape matrix of the radial basis function (size= in_size*in_size).
    """

    def __init__(self, in_size: int, m: torch.Tensor, **kwargs):
        super().__init__()
        self.dim = in_size
        m_no_grad = m.detach()
        self.m = torch.nn.Parameter(m_no_grad)
        self.A = torch.nn.Parameter((torch.rand((self.dim, self.dim))))
        self.type_rbf = kwargs.get("type_rbf", "gaussian")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the activation function to a tensor x.

        Args:
            x: Input tensor.

        Returns:
            The tensor after the application of the anisotropic radial basis function.
        """
        sid = 0.01 * torch.eye(self.dim, self.dim)
        sig2 = torch.matmul(torch.transpose(self.A, 0, 1), self.A) + sid
        norm = torch.linalg.vecdot(torch.mm(x - self.m, sig2), x - self.m, dim=1)
        norm = norm[:, None]
        if self.type_rbf == "gaussian":
            exp_m = torch.exp(-norm)
        else:
            exp_m = 1.0 / (1.0 + norm**2) ** 0.5
        return exp_m


class Rational(torch.nn.Module):
    r"""Class for a rational activation function with adaptive parameters.

    The function takes the form :math:`P(x) / Q(x)`,
    with :math:`P` a degree 3 polynomial and :math:`Q` a degree 2 polynomial.
    It is initialized as the best approximation of the ReLU function on
    :math:`[- 1, 1]`.
    The polynomials take the form:

    -  :math:`P(x) = p_0 + p_1 x + p_2 x^2 + p_3 x^3`
    -  :math:`Q(x) = q_0 + q_1 x + q_2 x^2`.

    ``p0``, ``p1``, ``p2``, ``p3``, ``q0``, ``q1``, ``q2`` are learnable parameters

    Args:
        **kwargs: Additional keyword arguments (not used here).
    """

    def __init__(self, **kwargs: Any):
        super().__init__()
        # REMI: use torch.tensor instead of torch.Tensor to have it on appropriated
        # device
        self.p0 = torch.nn.Parameter(
            torch.tensor([0.0218])
        )  #: Coefficient :math:`p_0` of the polynomial :math:`P`.
        self.p1 = torch.nn.Parameter(
            torch.tensor([0.5])
        )  #: Coefficient :math:`p_1` of the polynomial :math:`P`.
        self.p2 = torch.nn.Parameter(
            torch.tensor([1.5957])
        )  #: Coefficient :math:`p_2` of the polynomial :math:`P`.
        self.p3 = torch.nn.Parameter(
            torch.tensor([1.1915])
        )  #: Coefficient :math:`p_3` of the polynomial :math:`P`.
        self.q0 = torch.nn.Parameter(
            torch.tensor([1.0])
        )  #: Coefficient :math:`q_0` of the polynomial :math:`Q`.
        self.q1 = torch.nn.Parameter(
            torch.tensor([0.0])
        )  #: Coefficient :math:`q_1` of the polynomial :math:`Q`.
        self.q2 = torch.nn.Parameter(
            torch.tensor([2.3830])
        )  #: Coefficient :math:`q_2` of the polynomial :math:`Q`.

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the activation function to a tensor x.

        Args:
            x: Input tensor.

        Returns:
            The tensor after the application of the rational function.
        """
        P = self.p0 + x * (self.p1 + x * (self.p2 + x * self.p3))
        Q = self.q0 + x * (self.q1 + x * self.q2)
        return P / Q


def activation_function(ac_type: str, in_size: int = 1, **kwargs):
    r"""Function to choose the activation function.

    Args:
        ac_type: The name of the activation function.
        in_size: The dimension (useful for radial basis). Defaults to 1.
        **kwargs: Additional keyword arguments passed to the activation function.

    Returns:
        The activation function instance.
    """
    if ac_type == "adaptative_tanh":
        return AdaptativeTanh(**kwargs)
    elif ac_type == "sine":
        return Sine(**kwargs)
    elif ac_type == "cosin":
        return Cosin(**kwargs)
    elif ac_type == "silu":
        return SiLU(**kwargs)
    elif ac_type == "swish":
        return Swish(**kwargs)
    elif ac_type == "tanh":
        return Tanh(**kwargs)
    elif ac_type == "isotropic_radial":
        return IsotropicRadial(in_size, **kwargs)
    elif ac_type == "anisotropic_radial":
        return AnisotropicRadial(in_size, **kwargs)
    elif ac_type == "sigmoid":
        return Sigmoid(**kwargs)
    elif ac_type == "rational":
        return Rational(**kwargs)
    elif ac_type == "hat":
        return Hat(**kwargs)
    elif ac_type == "regularized_hat":
        return RegularizedHat(**kwargs)
    elif ac_type == "heaviside":
        return Heaviside(**kwargs)
    else:
        return Id()

"""Module for abstract temporal PDEs."""

from abc import ABC, abstractmethod
from typing import Generator, cast

import torch

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor


class TemporalPDE(ABC):
    """Base class for representing elliptic Partial Differential Equations (PDEs).

    Args:
        space: Approximation space used for the PDE
        linear: Whether the PDE is linear
        **kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        linear: bool = False,
        **kwargs,
    ):
        super().__init__()
        self.space = space
        self.linear = linear

        # handle kwargs
        self.exact_solution = kwargs.get("exact_solution", None)

    def grad(
        self,
        w: torch.Tensor | MultiLabelTensor,
        y: torch.Tensor | LabelTensor,
    ) -> torch.Tensor | tuple[torch.Tensor, ...]:
        """Compute the gradient of the tensor `w` with respect to the tensor `y`.

        Args:
            w: Input tensor
            y: Tensor with respect to which the gradient is computed

        Returns:
            Gradient tensor
        """
        res = self.space.grad(w, y)
        if isinstance(res, Generator):
            return tuple(res)
        return res

    @abstractmethod
    def rhs(
        self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor | tuple[torch.Tensor, ...]:
        """Compute the right-hand side (RHS) of the PDE.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            RHS tensor
        """

    @abstractmethod
    def space_operator(
        self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor | tuple[torch.Tensor, ...]:
        """Apply the PDE operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            Operator tensor
        """

    @abstractmethod
    def time_operator(
        self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor | tuple[torch.Tensor, ...]:
        """Apply the PDE operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            Operator tensor
        """

    def operator(
        self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor | tuple[torch.Tensor, ...]:
        """Apply the PDE operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            Operator tensor
        """
        space = self.space_operator(w, t, x, mu)
        time = self.time_operator(w, t, x, mu)
        error_message = (
            "space and time operators must be both Tensors of tuple of Tensors"
        )
        if isinstance(space, tuple):
            assert isinstance(time, tuple), error_message
            return tuple(sp + ti for sp, ti in zip(space, time))
        else:
            assert isinstance(time, torch.Tensor), error_message
            return space + time

    @abstractmethod
    def bc_rhs(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> torch.Tensor:
        """Compute the boundary condition RHS.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            Boundary condition RHS tensor
        """

    @abstractmethod
    def bc_operator(
        self,
        w: MultiLabelTensor,
        t: LabelTensor,
        x: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> torch.Tensor:
        """Apply the boundary condition operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            Boundary condition operator tensor
        """

    @abstractmethod
    def initial_condition(
        self, x: LabelTensor, mu: LabelTensor
    ) -> tuple[torch.Tensor, ...]:
        """Compute the initial condition.

        Args:
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            Initial condition tensor
        """


class FirstOrderTemporalPDE(TemporalPDE):
    """Base class for representing elliptic Partial Differential Equations (PDEs).

    Args:
        space: Approximation space used for the PDE
        linear: Whether the PDE is linear
        **kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        linear: bool = False,
        **kwargs,
    ):
        super().__init__(space, linear, **kwargs)

    def time_operator(
        self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor | tuple[torch.Tensor, ...]:
        """Apply the PDE operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            Operator tensor
        """
        u = w.get_components()
        if isinstance(u, torch.Tensor):
            return self.grad(u, t)
        else:
            return tuple(cast(torch.Tensor, self.grad(ui, t)) for ui in u)


class SecondOrderTemporalPDE(TemporalPDE):
    """Base class for representing elliptic Partial Differential Equations (PDEs).

    Args:
        space: Approximation space used for the PDE
        linear: Whether the PDE is linear
        **kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        linear: bool = False,
        **kwargs,
    ):
        super().__init__(space, linear)

    def time_operator(
        self, w: MultiLabelTensor, t: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor | tuple[torch.Tensor, ...]:
        """Apply the PDE operator.

        Args:
            w: Solution tensor
            t: Temporal coordinate tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            Operator tensor
        """
        # list_var = w.get_components()
        # list_var_res = []
        # for i in range(len(list_var)):
        #     list_var_res.append(self.grad(list_var[i], t))
        # for i in range(len(list_var)):
        #     list_var_res[i] = self.grad(list_var_res[i], t)
        # return tuple(list_var_res)

        u = w.get_components()
        if isinstance(u, torch.Tensor):
            dudt = self.grad(u, t)
            assert isinstance(dudt, torch.Tensor)
            d2ud2t = self.grad(dudt, t)
        else:
            dudt = tuple(cast(torch.Tensor, self.grad(ui, t)) for ui in u)
            d2ud2t = tuple(cast(torch.Tensor, self.grad(duidt, t)) for duidt in dudt)
        return d2ud2t


### TODO: comment faire le splitting avec plusieurs espace et plusieurs RHS ?
### Des listes de temporal PDE avec une méthode pour que le W soit toutes les variables
### de tous les espaces ?

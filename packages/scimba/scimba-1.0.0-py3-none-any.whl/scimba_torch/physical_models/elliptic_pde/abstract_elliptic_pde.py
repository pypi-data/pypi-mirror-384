"""Abstract classes for elliptic PDEs."""

from abc import ABC, abstractmethod
from typing import Generator

import torch

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.utils.scimba_tensors import LabelTensor, MultiLabelTensor


class EllipticPDE(ABC):
    """Base class for representing elliptic Partial Differential Equations (PDEs).

    Args:
        space: Approximation space used for the PDE
        linear: Indicates if the PDE is linear
        **kwargs: Additional keyword arguments

    """

    def __init__(self, space: AbstractApproxSpace, linear: bool = False, **kwargs):
        super().__init__()
        self.space = space
        self.linear = linear

    def grad(
        self,
        w: torch.Tensor | MultiLabelTensor,
        y: torch.Tensor | LabelTensor,
    ) -> torch.Tensor | Generator[torch.Tensor, None, None]:
        """Compute the gradient of the tensor `w` with respect to the tensor `y`.

        Args:
            w: Input tensor
            y: Tensor with respect to which the gradient is computed

        Returns:
            Gradient tensor
        """
        return self.space.grad(w, y)


class StrongFormEllipticPDE(EllipticPDE):
    """Strong form of an elliptic PDE.

    Args:
        space: Approximation space used for the PDE
        linear: Indicates if the PDE is linear
        residual_size: Size of the residual, defaults to space.nb_unknowns
        bc_residual_size: Size of the boundary condition residual, defaults to 0
        **kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        linear: bool = False,
        residual_size: int | None = None,
        bc_residual_size: int = 0,
        **kwargs,
    ):
        super().__init__(space, linear, **kwargs)
        if residual_size is None:
            residual_size = space.nb_unknowns
        self.residual_size = residual_size
        self.bc_residual_size = bc_residual_size

    @abstractmethod
    def rhs(self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor) -> torch.Tensor:
        """Compute the right-hand side (RHS) of the PDE.

        Args:
            w: Solution tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            The right-hand side of the PDE.
        """

    @abstractmethod
    def operator(
        self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Apply the PDE operator.

        Args:
            w: Solution tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            The result of the PDE operator.
        """

    @abstractmethod
    def bc_rhs(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the boundary condition RHS.

        Args:
            w: Solution tensor
            x: Spatial coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            The boundary condition RHS.
        """

    @abstractmethod
    def bc_operator(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Apply the boundary condition operator.

        Args:
            w: Solution tensor
            x: Spatial coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            The result of the boundary condition operator.
        """


class WeakFormEllipticPDE(EllipticPDE):
    """Weak form of an elliptic PDE.

    Args:
        space: Approximation space used for the PDE
        residual_size: Size of the weak form, defaults to space.nb_unknowns
        linear: Indicates if the PDE is linear
        **kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        residual_size: int | None = None,
        linear: bool = False,
        **kwargs,
    ):
        super().__init__(space, linear, **kwargs)
        if residual_size is None:
            residual_size = space.nb_unknowns
        self.residual_size = residual_size

    @abstractmethod
    def linearform(
        self, w: MultiLabelTensor, v: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> LabelTensor:
        """Compute the linear form of the weak formulation.

        Args:
            w: Solution tensor
            v: Test function tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            The linear form of the weak formulation.
        """

    @abstractmethod
    def bilinearform(
        self, w: MultiLabelTensor, v: LabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> LabelTensor:
        """Compute the bilinear form of the weak formulation.

        Args:
            w: Solution tensor
            v: Test function tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            The bilinear form of the weak formulation.
        """

    @abstractmethod
    def bc_linearform(
        self,
        w: MultiLabelTensor,
        v: LabelTensor,
        x: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> LabelTensor:
        """Compute the boundary condition linear form.

        Args:
            w: Solution tensor
            v: Test function tensor
            x: Spatial coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            The boundary condition linear form.
        """

    @abstractmethod
    def bc_bilinearform(
        self,
        w: MultiLabelTensor,
        v: LabelTensor,
        x: LabelTensor,
        n: LabelTensor,
        mu: LabelTensor,
    ) -> LabelTensor:
        """Compute the boundary condition bilinear form.

        Args:
            w: Solution tensor
            v: Test function tensor
            x: Spatial coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            The boundary condition bilinear form.
        """


class RitzFormEllipticPDE(EllipticPDE):
    """Ritz form of an elliptic PDE.

    Args:
        space: Approximation space used for the PDE
        linear: Indicates if the PDE is linear
        residual_size: Size of the weak form, defaults to space.nb_unknowns
        bc_residual_size: Size of the boundary condition residual, defaults to 0
        **kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        space: AbstractApproxSpace,
        linear: bool = False,
        residual_size: int | None = None,
        bc_residual_size: int = 0,
        **kwargs,
    ):
        super().__init__(space, linear, **kwargs)
        if residual_size is None:
            residual_size = space.nb_unknowns
        self.residual_size = residual_size
        self.bc_residual_size = bc_residual_size

    @abstractmethod
    def linearform(
        self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the linear form of the Ritz formulation.

        Args:
            w: Solution tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            The linear form of the Ritz formulation.
        """

    @abstractmethod
    def quadraticform(
        self, w: MultiLabelTensor, x: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the bilinear form of the Ritz formulation.

        Args:
            w: Solution tensor
            x: Spatial coordinate tensor
            mu: Parameter tensor

        Returns:
            The bilinear form of the Ritz formulation.
        """

    @abstractmethod
    def bc_rhs(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Compute the boundary condition RHS.

        Args:
            w: Solution tensor
            x: Spatial coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            The boundary condition RHS.
        """

    @abstractmethod
    def bc_operator(
        self, w: MultiLabelTensor, x: LabelTensor, n: LabelTensor, mu: LabelTensor
    ) -> torch.Tensor:
        """Apply the boundary condition operator.

        Args:
            w: Solution tensor
            x: Spatial coordinate tensor
            n: Normal vector tensor
            mu: Parameter tensor

        Returns:
            The result of the boundary condition operator.
        """

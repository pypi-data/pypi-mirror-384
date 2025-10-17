"""Preconditioner projectors and their components."""

from abc import abstractmethod

import torch

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.numerical_solvers.abstract_preconditioner import (
    AbstractPreconditioner,
)
from scimba_torch.utils.scimba_tensors import LabelTensor


class MatrixPreconditionerProjector(AbstractPreconditioner):
    """Abstract base class for matrix-based preconditioner projectors.

    This class provides a structure for implementing preconditioners that use a matrix
    to precondition the gradients in projection problems.

    Args:
        space: The approximation space where the projection takes place.
        **kwargs: Additional keyword arguments for configuring the preconditioner.
    """

    @abstractmethod
    def compute_preconditioning_matrix(
        self, *args: LabelTensor, **kwargs
    ) -> torch.Tensor:
        """Computes the preconditioning matrix.

        Args:
            *args: Input tensors for computing the preconditioning matrix.
            **kwargs: Additional keyword arguments.

        Returns:
            The computed preconditioning matrix.
        """

    def get_preconditioning_matrix(
        self, data: tuple[LabelTensor, ...], **kwargs
    ) -> torch.Tensor:
        """Retrieves the preconditioning matrix based on the input data.

        Args:
            data: The input data for computing the preconditioning matrix.
            **kwargs: Additional keyword arguments.

        Returns:
            The preconditioning matrix.
        """
        if self.space.type_space == "flow":
            args = [data[0], data[1]]  # only compute the matrix on the data at time t^n
        elif self.space.type_space == "space":
            args = [data[0], data[1]]
        elif self.space.type_space == "phase_space":
            args = [data[0], data[1], data[2]]
            # raise NotImplementedError("phase_space")
        else:
            args = [data[0], data[1], data[2]]

        return self.compute_preconditioning_matrix(*args, **kwargs)

    def get_preconditioning_matrix_bc(self, data: tuple, **kwargs) -> torch.Tensor:
        """Retrieves the BC preconditioning matrix based on the input data.

        Args:
            data: The input data for computing the boundary condition preconditioning
                matrix.
            **kwargs: Additional keyword arguments.

        Returns:
            The boundary condition preconditioning matrix.
        """
        if self.space.type_space == "space":
            args = [data[2], data[4]]  # do not need the normals
        elif self.space.type_space == "phase_space":
            args = [data[3], data[4], data[6]]  # do not need the normals
            # raise NotImplementedError("phase_space")
        else:
            args = [data[3], data[4], data[6]]  # do not need the normals
            # raise NotImplementedError("time_space")
        return self.compute_preconditioning_matrix(*args, **kwargs)


class EnergyNaturalGradientPreconditionerProjector(MatrixPreconditionerProjector):
    """Energy natural gradient preconditioner projector.

    This class implements a preconditioner using the energy natural gradient method.

    Args:
        space: The approximation space where the projection takes place.
        **kwargs: Additional keyword arguments for configuring the preconditioner.
    """

    def __init__(self, space: AbstractApproxSpace, **kwargs):
        super().__init__(space, **kwargs)
        self.matrix_regularization = kwargs.get("matrix_regularization", 1e-6)

    def metric_matrix(self, *args: LabelTensor, **kwargs) -> torch.Tensor:
        """Computes the metric matrix for the given input tensors.

        Args:
            *args: Input tensors for computing the metric matrix.
            **kwargs: Additional keyword arguments.

        Returns:
            The computed metric matrix.
        """
        N = args[0].shape[0]
        jacobian = self.space.jacobian(*args)
        M = torch.einsum(
            "ijk,ilk->jl", jacobian, jacobian
        ) / N + self.matrix_regularization * torch.eye(self.space.ndof)
        return M

    def compute_preconditioning_matrix(
        self, *args: LabelTensor, **kwargs
    ) -> torch.Tensor:
        """Computes the preconditioning matrix using the metric matrix.

        Args:
            *args: Input tensors for computing the preconditioning matrix.
            **kwargs: Additional keyword arguments.

        Returns:
            The computed preconditioning matrix.
        """
        return self.metric_matrix(*args, **kwargs)

    def __call__(
        self,
        epoch: int,
        data: tuple,
        grads: torch.Tensor,
        res_l: tuple,
        res_r: tuple,
        **kwargs,
    ) -> torch.Tensor:
        """Applies the energy natural gradient preconditioner to the gradients.

        Args:
            epoch: The current epoch number.
            data: The data used for computing the preconditioner.
            grads: The gradients to precondition.
            res_l: The left residuals.
            res_r: The right residuals.
            **kwargs: Additional keyword arguments.

        Returns:
            The preconditioned gradients.
        """
        M = self.get_preconditioning_matrix(data, **kwargs)
        if self.has_bc:
            Mb = self.get_preconditioning_matrix_bc(data, **kwargs)
            M += self.bc_weight * Mb

        preconditioned_grads = torch.linalg.lstsq(M, grads).solution
        return preconditioned_grads


class AnagramPreconditionerProjector(MatrixPreconditionerProjector):
    """Anagram preconditioner projector.

    This class implements a preconditioner using the Anagram method.


    Args:
        space: The approximation space where the projection takes place.
        **kwargs: Additional keyword arguments for configuring the preconditioner.
    """

    def __init__(self, space: AbstractApproxSpace, **kwargs):
        super().__init__(space, **kwargs)
        self.svd_threshold = kwargs.get("svd_threshold", 1e-6)
        self.nb_components = kwargs.get("nb_components", 1)
        # if self.space.nb_unknowns > 1:
        #     raise ValueError(
        #         "Anagram preconditioner is only implemented for scalar problems."
        #     )

    def compute_preconditioning_matrix(
        self, *args: LabelTensor, **kwargs
    ) -> torch.Tensor:
        """Computes the preconditioning matrix using the Jacobian of the space.

        Args:
            *args: Input tensors for computing the preconditioning matrix.
            **kwargs: Additional keyword arguments.

        Returns:
            The computed preconditioning matrix.
        """
        return self.space.jacobian(*args).squeeze(-1)

    def assemble_right_member(
        self, data: tuple, res_l: tuple, res_r: tuple
    ) -> torch.Tensor:
        """Assembles the right member for the preconditioning.

        Args:
            data: The input data for assembling the right member.
            res_l: The left residuals.
            res_r: The right residuals.

        Returns:
            The assembled right member.
        """
        in_tup = tuple(left - right for left, right in zip(res_l, res_r))
        return torch.cat(in_tup, dim=0)

    def __call__(
        self,
        epoch: int,
        data: tuple,
        grads: torch.Tensor,
        res_l: tuple,
        res_r: tuple,
        **kwargs,
    ) -> torch.Tensor:
        """Applies the Anagram preconditioner to the gradients.

        Args:
            epoch: The current epoch number.
            data: The data used for computing the preconditioner.
            grads: The gradients to precondition.
            res_l: The left residuals.
            res_r: The right residuals.
            **kwargs: Additional keyword arguments.

        Returns:
            The preconditioned gradients.
        """
        phi = self.get_preconditioning_matrix(data, **kwargs)
        if phi.ndim > 2:
            phi = torch.cat(
                tuple(phi[:, :, i, ...] for i in range(phi.shape[2])), dim=0
            )
        if self.has_bc:
            phib = self.get_preconditioning_matrix_bc(data, **kwargs)
            if phib.ndim > 2:
                phib = torch.cat(
                    tuple(phib[:, :, i, ...] for i in range(phib.shape[2])), dim=0
                )
            phi = torch.cat((phi, phib), dim=0)

        ### compute pseudo inverse via svd... with full matrices: slower
        # U, Delta, Vt = torch.linalg.svd(
        #     phi,
        #     full_matrices=True,
        # )
        # Vt = Vt[:, : Delta.shape[0]]  # On garde seulement les r premières colonnes
        # U = U[:, : Delta.shape[0]]  # On garde seulement les r premières colonnes
        ### compute pseudo inverse via svd... without full matrices: a bit faster
        U, Delta, Vt = torch.linalg.svd(
            phi,
            full_matrices=False,
        )
        mask = Delta > self.svd_threshold  # Mask pour ne garder que les grandes valeurs
        # print(
        #     "nb sv : %d, kept: %d, max: %.2e, threshold: %.2e, relative: %.2e"
        #     % (
        #         Delta.shape[0],
        #         torch.sum(mask),
        #         torch.max(Delta).item(),
        #         self.svd_threshold,
        #         torch.max(Delta).item() * self.svd_threshold,
        #     )
        # )
        Delta_inv = torch.zeros_like(Delta)
        Delta_inv[mask] = 1.0 / Delta[mask]  # Seulement les valeurs au-dessus du seuil
        # phi_plus = Vt @ torch.diag(Delta_inv) @ U.T #incorrect?
        phi_plus = Vt.T @ torch.diag(Delta_inv) @ U.T  # correct

        # ### compute pseudo inverse with torch.linalg.pinv using atol...
        # # phi_plus = torch.linalg.pinv(phi, atol=self.svd_threshold)

        # res = res_l[0] - res_r[0]
        res = self.assemble_right_member(
            data, res_l[0 : self.nb_components], res_r[0 : self.nb_components]
        )

        if self.has_bc:
            resb = self.assemble_right_member(
                data,
                res_l[self.nb_components : 2 * self.nb_components],
                res_r[self.nb_components : 2 * self.nb_components],
            )
            res = torch.cat((res, resb), dim=0)

        preconditioned_grads = phi_plus @ res

        return preconditioned_grads

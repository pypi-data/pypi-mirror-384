"""Base module for Scimba neural networks."""

import torch
import torch.nn as nn


class ScimbaModule(nn.Module):
    """Abstract class for Scimba neural networks.

    Args:
        in_size: Input dimension.
        out_size: Output dimension.
        **kwargs: Additional keyword arguments.
    """

    def __init__(self, in_size: int, out_size: int, **kwargs):
        super().__init__()
        self.in_size = in_size  #: Input dimension.
        self.out_size = out_size  #: Output dimension.
        self.output_layer = None  #: Output layer module (to be set by subclasses).

    def parameters(self, flag_scope: str = "all", flag_format: str = "list"):
        """Get parameters of the neural net.

        Args:
            flag_scope: Specifies which parameters to return.
                Options: 'all', 'last_layer', 'except_last_layer'.
            flag_format: Specifies the format
                Options: 'list', 'tensor'.

        Returns:
            list[nn.Parameter] or torch.Tensor

        Raises:
            ValueError: If flag_scope is not one of the supported options.
        """
        if flag_scope == "all":
            param_iter = super().parameters()
        elif flag_scope == "last_layer":
            param_iter = self.output_layer.parameters()
        elif flag_scope == "except_last_layer":
            param_iter = (
                param
                for name, param in self.named_parameters()
                if not name.startswith("output_layer")
            )

        else:
            raise ValueError(f"Unknown flag_scope: {flag_scope}")

        if flag_format == "list":
            return list(param_iter)
        elif flag_format == "tensor":
            return torch.nn.utils.parameters_to_vector(param_iter)
        else:
            raise ValueError(f"Unknown flag_format: {flag_format}")

    def set_parameters(self, new_params: torch.Tensor, flag_scope: str = "all"):
        """Set parameters.

        Args:
            new_params: new parameters.
            flag_scope: 'all', 'last_layer', 'except_last_layer'

        Raises:
            ValueError: If flag_scope is not one of the supported options.
        """
        if flag_scope == "all":
            param_iter = super().parameters()
        elif flag_scope == "last_layer":
            param_iter = self.output_layer.parameters()
        elif flag_scope == "except_last_layer":
            param_iter = (
                param
                for name, param in self.named_parameters()
                if not name.startswith("output_layer")
            )
        else:
            raise ValueError(f"Unknown flag_scope: {flag_scope}")

        torch.nn.utils.vector_to_parameters(new_params, param_iter)

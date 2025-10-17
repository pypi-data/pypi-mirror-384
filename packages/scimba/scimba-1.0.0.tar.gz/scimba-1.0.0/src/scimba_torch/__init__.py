"""Scimba package configuration.

At the loading of the scimba_torch module, torch is configured as follows:
    >>> device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    >>> torch.set_default_device(device)
    >>> torch.set_default_dtype(torch.double)

This configuration can be printed with:
    >>> scimba_torch.print_torch_setting()

To change device and or default floating point arithmetic precision:
    >>> torch.set_default_dtype(torch.float32)
    >>> torch.set_default_device("mps")

Notice that natural gradient preconditionning used in scimba_torch does not work well
with simple floating point precision.

At this time, basic routines of linear algebra required in natural gradient descent
preconditioning are not implemented in torch for "mps"
(a.k.a. Metal Performance Shaders) and we discourage its use.
"""

from math import pi as PI  # noqa: F401 N812

import torch

from scimba_torch.utils.verbosity import (  # noqa: F401
    get_verbosity,
    print_torch_setting,
    set_verbosity,
)

__version__ = "1.0.0"

# Export the imported utilities for backward compatibility
__all__ = [
    "PI",
    "device",
]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.set_default_device(device)
torch.set_default_dtype(torch.double)

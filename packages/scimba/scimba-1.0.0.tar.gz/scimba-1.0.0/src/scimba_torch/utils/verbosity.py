"""Verbosity utilities for scimba_torch."""

import re
from pathlib import Path

import torch


def _get_version_from_init(path):
    if not Path(path).is_file():
        raise FileNotFoundError(f"No such file or directory: {path}")
    content = Path(path).read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError(f"__version__ not found in {path}")
    return match.group(1)


SCIMBA_IS_VERBOSE = False


def print_torch_setting() -> None:
    """Print torch device and default floating point format."""
    print(f"torch device: {torch.get_default_device()}")
    print(f"torch floating point format: {torch.get_default_dtype()}")

    if torch.cuda.is_available():
        print(f"cuda devices:        {torch.cuda.device_count()}")
        print(f"cuda current device: {torch.cuda.current_device()}")
        print(f"cuda device name:    {torch.cuda.get_device_name(0)}")


def get_verbosity() -> bool:
    """Get the verbosity level of scimba.

    Returns:
        the current verbosity.
    """
    return SCIMBA_IS_VERBOSE


def set_verbosity(verbose: bool) -> None:
    """Set the verbosity level of scimba.

    Args:
        verbose: the wanted verbosity
    """
    global SCIMBA_IS_VERBOSE
    SCIMBA_IS_VERBOSE = verbose

    init_path = Path(__file__).parent.parent / "__init__.py"
    version = _get_version_from_init(init_path)

    if SCIMBA_IS_VERBOSE:
        print(f"\n/////////////// Scimba {version} ////////////////")
        print_torch_setting()
        print("\n")

"""Common typing protocols to replace mypy_extensions usage.

This module provides type-safe alternatives to mypy_extensions constructs
using the standard library's typing.Protocol.
"""

from typing import Any, Protocol

import torch


class VarArgCallable(Protocol):
    """Protocol for callable with variable torch.Tensor arguments.

    Replaces: Callable[[VarArg(torch.Tensor)], torch.Tensor]
    """

    def __call__(self, *args: torch.Tensor) -> torch.Tensor: ...  # noqa: D102


class VarArgAnyCallable(Protocol):
    """Protocol for callable with variable arguments of any type.

    Replaces: Callable[[VarArg(Any)], torch.Tensor]
    """

    def __call__(self, *args: Any) -> torch.Tensor: ...  # noqa: D102


class FuncTypeCallable(Protocol):
    """Protocol for functions taking a tensor x and keyword arguments.

    Replaces: Callable[[Arg(torch.Tensor, "x"), KwArg(Any)], torch.Tensor]
    """

    def __call__(self, x: torch.Tensor, **kwargs: Any) -> torch.Tensor:  # noqa: D102
        ...


class FuncFuncArgsCallable(Protocol):
    """Protocol for higher-order functions.

    This function takes another function and additional args.

    Replaces: Callable[[TYPE_FUNC_ARGS, VarArg(TYPE_ARGS)], torch.Tensor]
    """

    def __call__(self, func: VarArgCallable, *args: torch.Tensor) -> torch.Tensor: ...  # noqa: D102


# Convenient type aliases for backward compatibility
FUNC_TYPE = FuncTypeCallable
TYPE_FUNC_ARGS = VarArgCallable
TYPE_FUNC_FUNC_ARGS = FuncFuncArgsCallable

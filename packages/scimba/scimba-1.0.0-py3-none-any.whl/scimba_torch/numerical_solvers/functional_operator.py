"""Functional operators for PDEs with multiple labels."""

from collections import OrderedDict
from typing import Callable, Sequence

import torch

from scimba_torch.physical_models.elliptic_pde.abstract_elliptic_pde import (
    EllipticPDE,
)
from scimba_torch.physical_models.elliptic_pde.linear_order_2 import (
    LinearOrder2PDE,
)
from scimba_torch.physical_models.kinetic_pde.abstract_kinetic_pde import KineticPDE
from scimba_torch.physical_models.temporal_pde.abstract_temporal_pde import TemporalPDE
from scimba_torch.utils.typing_protocols import VarArgAnyCallable

# for python >= 3.12
# type func_args = VarArgCallable
# type func_func_args = Callable[[func_args, *Any], torch.Tensor]
# for python < 3.12
TYPE_THETA = dict[str, torch.nn.parameter.Parameter]
TYPE_ARGS = torch.Tensor | TYPE_THETA
TYPE_FUNC_ARGS = VarArgAnyCallable
TYPE_FUNC_FUNC_ARGS = Callable[[TYPE_FUNC_ARGS, VarArgAnyCallable], torch.Tensor]

TYPE_KEYS = int | tuple[int]

TYPE_SPLIT = OrderedDict[TYPE_KEYS, tuple[Sequence[torch.Tensor], torch.Tensor]]

TYPE_DICT_OF_FUNC_ARGS = OrderedDict[TYPE_KEYS, TYPE_FUNC_ARGS]
TYPE_DICT_OF_FUNC_FUNC_ARGS = OrderedDict[TYPE_KEYS, TYPE_FUNC_FUNC_ARGS]

TYPE_VMAPS = VarArgAnyCallable
TYPE_DICT_OF_VMAPS = OrderedDict[TYPE_KEYS, TYPE_VMAPS]


# assume all args and label have the same lenght
def split_label_tensors_to_dict_of_tensors_with_indexes(
    splitting_scheme: Sequence[TYPE_KEYS], labels: torch.Tensor, *args: torch.Tensor
) -> TYPE_SPLIT:
    """Split LabelTensors to a dict of tensors with indexes.

    Args:
        splitting_scheme: Sequence of keys to split the labels.
        labels: Tensor of labels to be split.
        *args: Tensors to be split according to the labels.

    Returns:
        A dictionary where each key from the splitting scheme maps to a tuple.
        The first element of the tuple is a list of tensors corresponding to the key,
        and the second element is a tensor of indexes.
    """
    tensor_of_indexes = torch.arange(0, len(labels), dtype=torch.long)
    masks = tuple(
        (
            torch.isin(labels, torch.tensor(el, dtype=torch.long))
            if isinstance(el, tuple)
            else labels == el
        )
        for el in splitting_scheme
    )
    # print("masks: ", masks)
    split_indexes = tuple(tensor_of_indexes[mask] for mask in masks)
    # print("split_indexes: ", split_indexes)
    res: TYPE_SPLIT = OrderedDict()
    for i, el in enumerate(splitting_scheme):
        res[el] = (
            [torch.index_select(arg, 0, split_indexes[i]) for arg in args],
            split_indexes[i],
        )
    return res


# assume all tensors have the same shape except in the dimension dim
def cat_dict_of_tensors_with_indexes(input: TYPE_SPLIT) -> list[torch.Tensor]:
    """Concatenate a dict of tensors with indexes.

    Args:
        input: A dictionary where each key maps to a tuple containing a list of tensors
                and a tensor of indexes.

    Returns:
        A list of concatenated tensors.
    """
    dim = 0
    ndim = sum(input[key][0][0].shape[dim] for key in input)
    fkey = list(input.keys())[0]
    nshapes = [(ndim,) + t.shape[1:] for t in input[fkey][0]]
    # print("nshapes: ", nshapes)

    res = [torch.zeros(nshape, dtype=torch.get_default_dtype()) for nshape in nshapes]

    for key in input:
        for i, t in enumerate(input[key][0]):
            res[i][input[key][1], ...] = t.transpose(0, dim)

    return res


def compose_funcs(func1: TYPE_FUNC_FUNC_ARGS, func2: TYPE_FUNC_ARGS) -> TYPE_FUNC_ARGS:
    """Compose two functions.

    Args:
        func1: A function that takes another function and additional arguments.
        func2: A function to be passed as an argument to func1.

    Returns:
        A new function that represents the composition of func1 and func2.
    """

    def composed_func(*args):
        return func1(func2, *args)

    return composed_func


def apply_dict_of_func_to_func(
    dict_of_func: TYPE_DICT_OF_FUNC_FUNC_ARGS, func: TYPE_FUNC_ARGS
) -> TYPE_DICT_OF_FUNC_ARGS:
    """Apply a dict of functions to a function.

    Args:
        dict_of_func: A dictionary where each key maps to a function that takes another
                      function and additional arguments.
        func: A function to be passed as an argument to each function in the dictionary.

    Returns:
        A dictionary where each key maps to the result of composing the corresponding
    """
    res: TYPE_DICT_OF_FUNC_ARGS = OrderedDict()
    for key in dict_of_func:
        res[key] = compose_funcs(dict_of_func[key], func)
    return res


def apply_func_to_dict_of_func(
    func: TYPE_FUNC_FUNC_ARGS, dict_of_func: TYPE_DICT_OF_FUNC_ARGS
) -> TYPE_DICT_OF_FUNC_ARGS:
    """Apply a function to a dict of functions.

    Args:
        func: A function that takes another function and additional arguments.
        dict_of_func: A dictionary where each key maps to a function to be passed as an
                      argument to func.

    Returns:
        A dictionary where each key maps to the result of composing func with the
        corresponding function in dict_of_func.
    """
    res: TYPE_DICT_OF_FUNC_ARGS = OrderedDict()
    for key in dict_of_func:
        res[key] = compose_funcs(func, dict_of_func[key])
    return res


def vectorize_dict_of_func(
    vectorizing_scheme: tuple[int | None, ...],
    dict_of_func: TYPE_DICT_OF_FUNC_ARGS,
) -> TYPE_DICT_OF_VMAPS:
    """Vectorize a dict of functions.

    Args:
        vectorizing_scheme: A tuple specifying the vectorization scheme.
        dict_of_func: A dictionary where each key maps to a function to be vectorized.

    Returns:
        A dictionary where each key maps to the vectorized version of the corresponding
        function in dict_of_func.
    """
    res: TYPE_DICT_OF_VMAPS = OrderedDict()
    for key in dict_of_func:
        res[key] = torch.func.vmap(dict_of_func[key], vectorizing_scheme)
    return res


def apply_dict_of_vmap_to_label_tensors(
    splitting_scheme: Sequence[TYPE_KEYS],
    vmdict: TYPE_DICT_OF_VMAPS,
    theta: TYPE_THETA,
    labels: torch.Tensor,
    *args: torch.Tensor,
) -> torch.Tensor:
    """Apply a dict of vmaps to LabelTensors.

    Args:
        splitting_scheme: Sequence of keys to split the labels.
        vmdict: A dictionary where each key maps to a vectorized function.
        theta: A dictionary of parameters to be passed to the functions.
        labels: Tensor of labels to be split.
        *args: Tensors to be passed as arguments to the functions.

    Returns:
        The result of applying the appropriate vectorized function to the split tensors.
    """
    if len(vmdict) == 1:
        for key in vmdict:
            return vmdict[key](*args, theta)

    mdict: TYPE_SPLIT = split_label_tensors_to_dict_of_tensors_with_indexes(
        splitting_scheme, labels, *args
    )

    evals: TYPE_SPLIT = OrderedDict()
    for key in mdict:
        evals[key] = (
            [vmdict[key](*mdict[key][0], theta)],
            mdict[key][1],
        )
    cat_eval = cat_dict_of_tensors_with_indexes(evals)
    return cat_eval[0]


class FunctionalOperator:
    """Handle functional operators for PDEs with multiple labels.

    Args:
        pde: An instance of a PDE class.
        name: The name of the operator method in the PDE class.
        **kwargs: Additional keyword arguments.

    Raises:
        AttributeError: If the specified operator method does not exist in the PDE
            class or is not callable.
    """

    def __init__(
        self,
        pde: EllipticPDE | TemporalPDE | KineticPDE | LinearOrder2PDE,
        name: str,
        **kwargs,
    ):
        if not (hasattr(pde, name)):
            raise AttributeError("input PDE must have an attribute %s" % name)
        assert hasattr(pde, name)
        self.operator = getattr(pde, name)
        if not callable(self.operator):
            raise AttributeError("attribute %s of input pde must be a method" % name)

        self.dict_of_operators: TYPE_DICT_OF_FUNC_FUNC_ARGS = OrderedDict()
        try:
            self.dict_of_operators = self.operator()
            # print("self.dict_of_operators: ", self.dict_of_operators)
        except TypeError:
            # in case where only one function is given, the key does not matter:
            # the same operator will be applied wathever the label
            self.dict_of_operators = OrderedDict([(0, self.operator)])

        self.keys = [key for key in self.dict_of_operators]

    def split_label_tensors(
        self, labels: torch.Tensor, *args: torch.Tensor
    ) -> TYPE_SPLIT:
        """Split LabelTensors to a dict of tensors with indexes.

        Args:
            labels: Tensor of labels to be split.
            *args: Tensors to be split according to the labels.

        Returns:
            A dictionary where each key from the operator keys maps to a tuple.
            The first element of the tuple is a list of tensors corresponding to the
            key, and the second element is a tensor of indexes.
        """
        return split_label_tensors_to_dict_of_tensors_with_indexes(
            self.keys, labels, *args
        )

    def cat_dict_of_tensors(self, input: TYPE_SPLIT) -> list[torch.Tensor]:
        """Concatenate a dict of tensors with indexes.

        Args:
            input: A dictionary where each key maps to a tuple containing a list of
                tensors and a tensor of indexes.

        Returns:
            A list of concatenated tensors.
        """
        return cat_dict_of_tensors_with_indexes(input)

    def apply_dict_of_vmap_to_label_tensors(
        self,
        vmdict: TYPE_DICT_OF_VMAPS,
        theta: TYPE_THETA,
        labels: torch.Tensor,
        *args: torch.Tensor,
    ) -> torch.Tensor:
        """Apply a dict of vmaps to LabelTensors.

        Args:
            vmdict: A dictionary where each key maps to a vectorized function.
            theta: A dictionary of parameters to be passed to the functions.
            labels: Tensor of labels to be split.
            *args: Tensors to be passed as arguments to the functions.

        Returns:
            The result of applying the appropriate vectorized function to the split
            tensors.
        """
        return apply_dict_of_vmap_to_label_tensors(
            self.keys, vmdict, theta, labels, *args
        )

    def apply_to_func(self, func: TYPE_FUNC_ARGS) -> TYPE_DICT_OF_FUNC_ARGS:
        """Apply the functional operator to a function.

        Args:
            func: A function to be passed as an argument to each function in the
                operator dictionary.

        Returns:
            A dictionary where each key maps to the result of composing the
            corresponding function in the operator dictionary with func.
        """
        return apply_dict_of_func_to_func(self.dict_of_operators, func)

    def apply_func_to_dict_of_func(
        self, func: TYPE_FUNC_FUNC_ARGS, dict_of_func: TYPE_DICT_OF_FUNC_ARGS
    ) -> TYPE_DICT_OF_FUNC_ARGS:
        """Apply a function to a dict of functions.

        Args:
            func: A function that takes another function and additional arguments.
            dict_of_func: A dictionary where each key maps to a function to be passed as
                an argument to func.

        Returns:
            A dictionary where each key maps to the result of composing func with the
            corresponding function in dict_of_func.
        """
        return apply_func_to_dict_of_func(func, dict_of_func)

    def cat_tuple_of_tensors(
        self, input: tuple[torch.Tensor, ...], labels: torch.Tensor, *args: torch.Tensor
    ) -> torch.Tensor:
        """Concatenate a tuple of tensors with indexes.

        Args:
            input: A tuple of tensors to be concatenated.
            labels: Tensor of labels to be split.
            *args: Tensors to be split according to the labels.

        Returns:
            A tensor resulting from concatenating the input tensors according to the
            split indexes derived from the labels.
        """
        mdict = self.split_label_tensors(labels, *args)
        for i in range(len(input)):
            key = self.keys[i]
            mdict[key] = ([input[i]], mdict[key][1])
        mdict_cat = self.cat_dict_of_tensors(mdict)
        return mdict_cat[0]

"""Utility functions to evaluate an AbstractApproxSpace and its derivatives."""

from typing import Any, Sequence

import numpy as np
import torch

from scimba_torch.approximation_space.abstract_space import AbstractApproxSpace
from scimba_torch.utils.scimba_tensors import LabelTensor


def _common_prefix_len(str1: str, str2: str) -> tuple[int, str]:
    prelen = 0
    while (
        (len(str1) > prelen) and (len(str2) > prelen) and (str1[prelen] == str2[prelen])
    ):
        prelen += 1
    return prelen, str1[0:prelen]


def _get_key_with_longest_common_prefix(s: str, d: dict[str, Any]) -> tuple[int, str]:
    prelen, prefix = 0, ""
    for key in d:
        if len(key) <= len(s):
            le, pe = _common_prefix_len(s, key)
            if le > prelen:
                prelen, prefix = le, pe
    return prelen, prefix


def _first_variable_symbol(
    symstr: str, symb_dict: dict[str, list[str]]
) -> tuple[str, str]:
    for variable_type in symb_dict:
        if variable_type == "components":
            continue

        for symbol in symb_dict[variable_type]:
            if symstr.startswith(symbol):
                return (symbol, variable_type)

    raise ValueError(f"could not find variable symbol for {symstr}")


def _compute_derivative_from_str_dict(
    space: AbstractApproxSpace,
    eval_args: Sequence[LabelTensor],  # (t, x,)
    derstr: str,
    d: dict[str, torch.Tensor],
    symb_dict: dict[str, list[str]],
    time_discrete=False,
) -> None:
    # get key in d with longest common prefix with derstr:
    le, key = _get_key_with_longest_common_prefix(derstr, d)
    # assume le>=1, in worst case, key is one of component symbols
    # compute derivatives while storing intermediate results in d
    while le < len(derstr):
        u = d[key]
        # parse derstr[le:] to get next variable symbol
        symbol, var_type = _first_variable_symbol(derstr[le:], symb_dict)
        if var_type == "time_variable":
            if time_discrete:
                raise ValueError(
                    "can not evaluate derivative with respect to time for a "
                    "time-discrete scheme"
                )
            # print("symbol: ", symbol)
            d[key + symbol] = space.grad(u, eval_args[0])
        if var_type == "space_variables":
            index_of_space_var_in_args = (
                1 if (("time_variable" in symb_dict) and not time_discrete) else 0
            )
            res_tup = space.grad(u, eval_args[index_of_space_var_in_args])
            if len(symb_dict["space_variables"]) == 1:  # res_tup is a tensor
                d[key + symb_dict["space_variables"][0]] = res_tup
            else:  # res_tup is a generator
                for _, symb in enumerate(symb_dict["space_variables"]):
                    d[key + symb] = next(res_tup)
        if var_type == "phase_variables":
            index_of_phase_var_in_args = 0
            assert "time_variable" not in symb_dict
            # if "time_variable" in symb_dict and not time_discrete:
            # index_of_phase_var_in_args += 1
            if "space_variables" in symb_dict:
                index_of_phase_var_in_args += 1
            res_tup = space.grad(u, eval_args[index_of_phase_var_in_args])
            if len(symb_dict["phase_variables"]) == 1:  # res_tup is a tensor
                d[key + symb_dict["phase_variables"][0]] = res_tup
            else:  # res_tup is a generator
                for _, symb in enumerate(symb_dict["phase_variables"]):
                    d[key + symb] = next(res_tup)

        le += len(symbol)
        key = derstr[0:le]


def _compute_derivatives_from_list_of_str(
    space: AbstractApproxSpace,
    us: Sequence[torch.Tensor],
    eval_args: Sequence[LabelTensor],
    derstrs: Sequence[str],
    symb_dict: dict[str, list[str]],
    time_discrete=False,
) -> dict[str, torch.Tensor]:
    # initialize derdict
    derdict = {}
    for i, comp in enumerate(symb_dict["components"]):
        derdict[comp] = us[i]

    for s in derstrs:
        _compute_derivative_from_str_dict(
            space, eval_args, s, derdict, symb_dict, time_discrete
        )
    # remove spirious entries?
    tobedeleted = []
    for key in derdict:
        if key not in derstrs:
            tobedeleted.append(key)
    for key in tobedeleted:
        del derdict[key]
    return derdict


def eval_on_np_tensors(
    space: AbstractApproxSpace,
    t: np.ndarray,
    x: np.ndarray,
    v: np.ndarray,
    mu: np.ndarray,
    symb_dict: dict[str, list[str]],
    component: int = 0,
    **kwargs,
) -> dict[str, np.ndarray]:
    """Evaluates an AbstractApproxSpace and its derivatives at np args.

    Args:
        space: the space to evaluate
        t: the time values, possibly empty array when space is not a time space
        x: the x values of shape (batch, geometric dim)
        v: the velocity values, possibly empty array when space is not a phase space
        mu: the parameters values, possibly empty array when space no parameters
        symb_dict: a dictionary of symbols (for parsing derivatives strings)
        component: if space takes values in R^n, the component to be evaluated
            default value 0
        **kwargs: a dictionary of arguments

    Returns:
        a dictionary {"approximation":space(t,x,v,mu)}
            with more keys if asked in input kwargs

    Raises:
        ValueError: "can not evaluate residual for a time-discrete scheme"

    can also raise ValueError if derivative w.r.t.
    time is asked for a time-discrete scheme
    """
    labelsx = kwargs.get("labelsx", np.zeros((x.shape[0],), dtype=np.int32))
    # print("x.shape: ", x.shape)
    # print("mu.shape: ", mu.shape)
    tt = torch.tensor(t, dtype=torch.get_default_dtype())
    tl = LabelTensor(tt)
    xt = torch.tensor(x, dtype=torch.get_default_dtype())
    xl = LabelTensor(
        xt,
        labels=torch.tensor(labelsx, dtype=torch.int32),
    )

    vt = torch.tensor(v, dtype=torch.get_default_dtype())
    vl = LabelTensor(vt)
    mut = torch.tensor(mu, dtype=torch.get_default_dtype())
    mul = LabelTensor(mut)

    if ("residual" in kwargs) or ("derivatives" in kwargs):
        xl.x.requires_grad_()
        if tl.shape[1] > 0:
            tl.x.requires_grad_()
        if vl.shape[1] > 0:
            vl.x.requires_grad_()

    # args_for_eval = [xl, mul]
    # args_for_deri = [xl]
    # if tl.shape[1] > 0:
    #     # print(t.shape)
    #     args_for_eval = [tl, xl, mul]
    #     args_for_deri = [tl, xl]
    # if vl.shape[1] > 0:
    #     # print(t.shape)
    #     args_for_eval = [tl, xl, vl, mul]
    #     args_for_deri = [tl, xl, vl]

    time_discrete = kwargs.get("time_discrete", False)

    args_for_eval = []
    args_for_eval_with_t = []
    args_for_deri = []
    if tl.shape[1] > 0:
        if not time_discrete:
            args_for_eval.append(tl)
            args_for_deri.append(tl)
        args_for_eval_with_t.append(tl)
    args_for_eval.append(xl)
    args_for_eval_with_t.append(xl)
    args_for_deri.append(xl)
    if vl.shape[1] > 0:
        args_for_eval.append(vl)
        args_for_eval_with_t.append(vl)
        args_for_deri.append(vl)
    args_for_eval.append(mul)
    args_for_eval_with_t.append(mul)

    # get prediction at args_for_eval and add it in the eval dict
    w_pred = space.evaluate(*args_for_eval)
    # evals = {"approximation": w_pred.w[:, component].detach().cpu().numpy()}
    # assemble with respect to labels
    listOflabels = np.unique(labelsx)  # this list is sorted!
    ncomponent = len(listOflabels) * component
    # print("component: ", component)
    # print("len(listOflabels): ", len(listOflabels))
    approx = w_pred.w[:, ncomponent].detach().cpu().numpy()
    if len(listOflabels) > 1:
        for i, lab in enumerate(listOflabels):
            condition = labelsx == lab
            approxi = w_pred.w[:, ncomponent + i].detach().cpu().numpy()
            approx[condition] = approxi[condition]
    evals = {"approximation": approx}

    if "solution" in kwargs:
        solution = kwargs["solution"]
        s = solution(*args_for_eval_with_t)[:, component]
        evals["solution"] = s.detach().cpu().numpy()

    if "error" in kwargs:
        solution = kwargs["error"]
        s = solution(*args_for_eval_with_t)[:, component]
        evals["error"] = torch.abs(s - w_pred.w[:, component]).detach().cpu().numpy()

    if "residual" in kwargs:
        if time_discrete:
            raise ValueError("can not evaluate residual for a time-discrete scheme")
        pde = kwargs["residual"]

        try:
            Lo = pde.operator(w_pred, *args_for_eval_with_t)
        except AttributeError:
            L_space = pde.space_operator(w_pred, *args_for_eval_with_t)  # tuple
            L_time = pde.time_operator(w_pred, *args_for_eval_with_t)  # tuple
            if isinstance(L_space, tuple):
                assert isinstance(L_time, tuple) and len(L_space) == len(L_time), (
                    "space operator and time operator must retrieve tuple of tensors "
                    "of the same length"
                )
                Lo = tuple(L_s + L_t for L_s, L_t in zip(L_space, L_time))
            else:
                assert (
                    isinstance(L_space, torch.tensor)
                    and isinstance(L_time, torch.tensor)
                    and (L_space.shape == L_time.shape)
                ), (
                    "space operator and time operator must retrieve tensors of the "
                    "same shape"
                )
                Lo = L_space + L_time

        f = pde.rhs(w_pred, *args_for_eval_with_t)
        if not isinstance(Lo, tuple):
            Lo = (Lo,)
        if not isinstance(f, tuple):
            f = (f,)

        if len(listOflabels) == 1:
            evals["residual"] = (Lo[component] - f[component]).detach().cpu().numpy()

        else:
            resi = np.ones_like(approx) * np.inf
            if len(listOflabels) > 1:
                for i, lab in enumerate(listOflabels):
                    condition = torch.tensor((labelsx == lab), dtype=torch.bool)
                    condition = (
                        torch.tensor((labelsx == lab), dtype=torch.bool)
                        .detach()
                        .cpu()
                        .numpy()
                    )

                    resii = (
                        (Lo[ncomponent + i] - f[ncomponent + i]).detach().cpu().numpy()
                    )
                    resi[condition] = resii.squeeze()
            evals["residual"] = resi

    if "derivatives" in kwargs:
        derivatives = kwargs["derivatives"]
        u = w_pred.get_components()
        if isinstance(u, torch.Tensor):
            u = (u,)
        uarg = [u[ncomponent + i] for i in range(len(listOflabels))]
        derdict = _compute_derivatives_from_list_of_str(
            space, uarg[0:1], args_for_deri, derivatives, symb_dict, time_discrete
        )

        for i in range(1, len(listOflabels)):
            lab = listOflabels[i]
            derdicti = _compute_derivatives_from_list_of_str(
                space,
                uarg[i : i + 1],
                args_for_deri,
                derivatives,
                symb_dict,
                time_discrete,
            )
            condition = labelsx == lab
            for key in derdict:
                derdict[key][condition] = derdicti[key][condition]

        # print("keys in derdict: ")
        for key in derdict:
            # print(key)
            evals[key] = derdict[key].detach().cpu().numpy()

    return evals


if __name__ == "__main__":  # pragma: no cover
    prelen, prefix = _common_prefix_len("Bonjour", "Bonsoir")
    print("Bonjour, Bonsoir: ", prelen, ", ", prefix)

    s = "uxxy"
    d = {
        "ux": torch.ones((1)),
        "uy": torch.ones((1)),
        "uxy": torch.ones((1)),
    }

    le, ke = _get_key_with_longest_common_prefix(s, d)
    print("le, ke: ", le, ", ", ke)

    d["uxxyx"] = torch.ones((1))

    le, ke = _get_key_with_longest_common_prefix(s, d)
    print("le, ke: ", le, ", ", ke)

    d["uxxy"] = torch.ones((1))

    le, ke = _get_key_with_longest_common_prefix(s, d)
    print("le, ke: ", le, ", ", ke)

# DEPRECATED
# def compute_derivative_from_str_dict(
#     space: AbstractApproxSpace, x: torch.Tensor, derstr: str,
#     d: dict[str,torch.Tensor]
# ) -> None:
#     # get key in d with longest common prefix with derstr:
#     le, key = get_key_with_longest_common_prefix(derstr, d)
#     # assume le>=1, if le==1 then key == "u"
#     # compute derivatives while storing intermediate results in d
#     while le < len(derstr):
#         u = d[key]
#         d[key + "x"], d[key + "y"] = space.grad(u, x)
#         le += 1
#         key = derstr[0:le]

# def compute_derivatives_from_list_of_str(
#     space: AbstractApproxSpace, u: torch.Tensor, x: torch.Tensor, derstrs: list[str]
# ) -> dict[str, torch.Tensor]:
#     derdict = {"u": u}
#     for s in derstrs:
#         compute_derivative_from_str_dict(space, x, s, derdict)
#     # remove spirious entries?
#     tobedeleted = []
#     for key in derdict:
#         if key not in derstrs:
#             tobedeleted.append(key)
#     for key in tobedeleted:
#         del derdict[key]
#     return derdict

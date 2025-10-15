"""Collection of operators working on several datatypes."""

import functools as ft
import math

import numpy as np

from ..typing import ArrayType, TensorType
from ..util.indextricks import findfirst
from .binops import _inprod
from .core import frob, mtkrprod, tmprod
from .deferred_residual import DeferredResidual
from .partial import PartialTensor
from .polyadic import PolyadicTensor
from .tensor import Tensor
from .tensortrain import TensorTrainTensor
from .tucker import TuckerTensor

_CACHED_FROBS: dict[int, float] = {}


def _clear_frob_cache():
    global _CACHED_FROBS
    _CACHED_FROBS.clear()


@frob.register
def _frob_deferred_array(T: DeferredResidual, squared: bool = False) -> float:
    if T._use_cached_frob and not T.T2.flags["WRITEABLE"]:
        # setdefault cannot be used as it computes the default value anyway.
        frob_T2 = _CACHED_FROBS.get(id(T.T2), None)
        if frob_T2 is None:
            frob_T2 = frob(T.T2, squared=True)
            _CACHED_FROBS[id(T.T2)] = frob_T2
    else:
        frob_T2 = frob(T.T2, squared=True)
    nrm2 = frob(T.T1, squared=True) - 2 * np.real(_inprod(T.T1, T.T2)) + frob_T2
    nrm2 = abs(nrm2)  # numerical errors can cause negative values for small residuals
    return nrm2 if squared else math.sqrt(nrm2)


def _final_product_shape(
    left: TensorTrainTensor, right: TensorTrainTensor, axis: int
) -> tuple[int, ...]:
    shape: tuple[int, ...] = left.cores3[axis].shape[:2] + (
        right.cores3[axis].shape[-1],
    )
    if axis == 0:
        shape = shape[1:]
    elif axis == left.ndim - 1:
        shape = shape[:-1]
    return shape


def tensor_left_right_interface_product(
    a: Tensor,
    left: TensorTrainTensor,
    axis: int,
    right: TensorTrainTensor | None = None,
) -> ArrayType:
    """Compute the product of a tensor and the left and right interface matrices.

    The product of the left interface matrix ``L``, the reshaped tensor `a` and the
    right interface matrix ``R``::

        L = left.left_interface_matrix(axis)
        R = right.right_interface_matrix(axis)
        a3 = a.reshape((math.prod(a.shape[:axis]), a.shape[axis], -1))
        res = contract_trail_lead(L.T, a3) @ R.T

    The shape of the `res` is the same as the shape of the core tensor.

    Depending on the type of `a`, a structure specific implementation can be selected.

    Parameters
    ----------
    a : Tensor
        Array which is multiplied with the left/right interface matrices.
    left : TensorTrainTensor
        The first `axis` cores of `left` are used to build the left interface matrix.
    axis : int
        The axis
    right : TensorTrainTensor, optional
        The final ``a.ndim - axis - 1`` cores of `right` are used to build the right
        interface matrix. If not provided, `right` is set to `left`.

    Returns
    -------
    res : ArrayType
        The product of `a` and the left and right interface matrices.

    Notes
    -----
    This product is commonly used when computing a TT core gradient contraction.
    """
    if not -a.ndim <= axis < a.ndim:
        raise ValueError(
            f"axis is out of bounds: expected {-a.ndim} <= axis < {a.ndim}, "
            f"but got {axis}"
        )
    if axis < 0:
        axis += a.ndim
    if left.shape[:axis] != a.shape[:axis]:
        i = findfirst(i != j for i, j in zip(left.shape[:axis], a.shape[:axis]))
        raise ValueError(
            f"shape of left does not match shape of a in axis {i}:"
            f"expected {a.shape[i]} but got {left.shape[i]}"
        )
    if right is None:
        right = left
    if right.shape[axis + 1 :] != a.shape[axis + 1 :]:
        i = findfirst(
            i != j for i, j in zip(right.shape[axis + 1 :], a.shape[axis + 1 :])
        )
        i += axis + 1
        raise ValueError(
            f"shape of right does not match shape of a in axis {i}:"
            f"expected {a.shape[i]} but got {right.shape[i]}"
        )
    return _tensor_left_right_interface_product(a, left, axis, right)


@ft.singledispatch
def _tensor_left_right_interface_product(
    a: TensorType, left: TensorTrainTensor, axis: int, right: TensorTrainTensor
) -> ArrayType:
    return _tensor_left_right_interface_product_array(np.asarray(a), left, axis, right)


@_tensor_left_right_interface_product.register
def _tensor_left_right_interface_product_array(
    a: np.ndarray, L: TensorTrainTensor, axis: int, R: TensorTrainTensor
) -> ArrayType:
    res = a.copy()[None, ..., None]
    for core in L.cores3[:axis]:
        r, i, s = core.shape
        res = core.reshape((r * i, s)).T @ res.reshape((r * i, -1))
    for core in reversed(R.cores3[axis + 1 :]):
        r, i, s = core.shape
        res = res.reshape((-1, i * s)) @ core.reshape((r, i * s)).T

    return res.reshape(_final_product_shape(L, R, axis))


@_tensor_left_right_interface_product.register
def _tensor_left_right_interface_product_polyadic(
    a: PolyadicTensor,
    L: TensorTrainTensor,
    axis: int,
    R: TensorTrainTensor,
) -> ArrayType:
    rank = a.nterm
    if axis > 0:
        left = L.cores[0].T @ a.factors[0]
        rank = left.shape[1]
        for core, factor in zip(L.cores3[1:axis], a.factors[1:axis]):
            factors = [left, factor, np.empty((core.shape[2], rank))]
            left = mtkrprod(core, factors, 2, conjugate=False)
    else:
        left = np.ones((1, rank), dtype=a.dtype)
    if axis < a.ndim - 1:
        right = R.cores[-1] @ a.factors[-1]

        N = a.ndim - 1
        for core, factor in zip(
            R.cores3[N - 1 : axis : -1], a.factors[N - 1 : axis : -1]
        ):
            factors = [np.empty((core.shape[0], rank)), factor, right]
            right = mtkrprod(core, factors, 0, conjugate=False)
    else:
        right = np.ones((1, rank), dtype=a.dtype)

    res = np.array(PolyadicTensor((left, a.factors[axis], right)))
    return res.reshape(_final_product_shape(L, R, axis))


@_tensor_left_right_interface_product.register
def _tensor_left_right_interface_product_tucker(
    a: TuckerTensor,
    L: TensorTrainTensor,
    axis: int,
    R: TensorTrainTensor,
) -> ArrayType:
    res = a.core.copy()[None, ..., None]

    for core, factor in zip(L.cores3[:axis], a.factors[:axis]):
        tmp = tmprod(core, factor, 1, "T")
        r, i, s = tmp.shape
        res = tmp.reshape((r * i, s)).T @ res.reshape((r * i, -1))

    for core, factor in zip(
        reversed(R.cores3[axis + 1 :]), reversed(a.factors[axis + 1 :])
    ):
        tmp = tmprod(core, factor, 1, "T")
        r, i, s = tmp.shape
        res = res.reshape((-1, i * s)) @ tmp.reshape((r, i * s)).T

    shape = (L.cores3[axis].shape[0], a.core.shape[axis], R.cores3[axis].shape[2])
    res = tmprod(res.reshape(shape), a.factors[axis], 1)
    return res.reshape(_final_product_shape(L, R, axis))


@_tensor_left_right_interface_product.register
def _tensor_left_right_interface_product_tt(
    a: TensorTrainTensor, L: TensorTrainTensor, axis: int, R: TensorTrainTensor
) -> ArrayType:
    left = np.ones((1, 1), dtype=a.dtype)
    for core0, core1 in zip(a.cores3[:axis], L.cores3[:axis]):
        r0, i, s0 = core0.shape
        r1, _, s1 = core1.shape

        if r0 > r1:
            core0 = left.T @ core0.reshape((r0, i * s0))
        else:
            core1 = left @ core1.reshape((r1, i * s1))
        left = core0.reshape((-1, s0)).T @ core1.reshape((-1, s1))

    right = np.ones((1, 1), dtype=a.dtype)
    for core0, core1 in zip(
        reversed(a.cores3[axis + 1 :]), reversed(R.cores3[axis + 1 :])
    ):
        r0, i, s0 = core0.shape
        r1, _, s1 = core1.shape

        if s0 > s1:
            core0 = core0 @ right
        else:
            core1 = core1 @ right.T
        right = core0.reshape((r0, -1)) @ core1.reshape((r1, -1)).T

    res = a.cores3[axis] @ right
    res = left.T @ res.reshape((a.cores3[axis].shape[0], -1))
    return res.reshape(_final_product_shape(L, R, axis))


@_tensor_left_right_interface_product.register
def _tensor_left_right_interface_product_partial(
    a: PartialTensor, L: TensorTrainTensor, axis: int, R: TensorTrainTensor
) -> ArrayType:
    left = a.data[None, :]
    for index, core in zip(a.indices[:axis], L.cores3[:axis]):
        left = (left[:, :, None] * core[:, index, :]).sum(0).T

    right = np.ones((1, 1), dtype=a.dtype)
    for index, core in zip(
        reversed(a.indices[axis + 1 :]), reversed(R.cores3[axis + 1 :])
    ):
        right = (right * core[:, index, :]).sum(2).T

    shape = L.cores3[axis].shape[:2] + (R.cores3[axis].shape[2],)
    res = np.zeros(shape, dtype=a.dtype)
    for i in range(L.shape[axis]):
        sel = a.indices[axis] == i
        if sum(sel) == 0:
            continue
        if axis < a.ndim - 1:
            res[:, i, :] = left[:, sel] @ right[sel, :]
        else:
            res[:, i, :] = left[:, sel].sum(1)[:, None]

    return res.reshape(_final_product_shape(L, R, axis))


@_tensor_left_right_interface_product.register
def _tensor_left_right_interface_product_residual(
    a: DeferredResidual,
    L: TensorTrainTensor,
    axis: int,
    R: TensorTrainTensor,
) -> ArrayType:
    prod1 = _tensor_left_right_interface_product(a.T1, L, axis, R)
    prod2 = _tensor_left_right_interface_product(a.T2, L, axis, R)
    return prod1 - prod2

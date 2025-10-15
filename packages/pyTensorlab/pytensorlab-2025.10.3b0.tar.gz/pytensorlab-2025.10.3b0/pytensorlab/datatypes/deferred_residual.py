"""Computation of the residual between two tensors.

Compute the difference ``T1 - T2`` between two tensors ``T1`` and ``T2`` as
:func:`.residual`. To defer the computation of the difference, use ``residual(T1, T2,
defer=True)``. If both or any tensors possess structure, then any operation applied to
this deferred residual will be computed efficiently by exploiting this structure.
"""

import sys
from collections.abc import Sequence
from operator import sub
from typing import (
    Any,
    Literal,
    cast,
)

import numpy as np
from numpy.typing import DTypeLike

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


import pytensorlab.backends.numpy as tlb
from pytensorlab.typing import (
    ArrayType,
    Axis,
    AxisLike,
    IndexType,
    MatrixType,
    NumberType,
    TensorType,
    VectorType,
    isint,
)
from pytensorlab.typing.core import ShapeLike

from ..util.indextricks import normalize_axes
from .core import (
    _mtkronprod_all,
    _mtkronprod_single,
    _mtkrprod_all,
    _mtkrprod_single,
    _tmprod,
    _tvprod,
    getitem,
)
from .tensor import Tensor


class DeferredResidual(Tensor):
    """Tensor representing the difference between two tensors.

    The difference ``T1 - T2`` is not computed explicitly; instead `T1` and `T2` are
    stored. Linear operations on a `DeferredResidual` are performed on both `T1` and
    `T2` separately, after which the subtraction is performed. Hence, the computation of
    the subtraction is deferred. To compute the explicit difference, :func:`numpy.array`
    can be used.

    Parameters
    ----------
    T1 : TensorType
        First tensor in the residual.
    T2 : TensorType
        Second tensor in the residual.
    _use_cached_frob : bool, default = False
        Cache the squared Frobenius norm of `T2`, such that it can be reused to save
        computation time. Note that accuracy can be lost due to the squaring. If the
        residual is small, large values that are approximately equal will be subtracted,
        leading to numerical errors. By squaring the norm, the maximum achievable
        accuracy then becomes the square root of machine precision.

    Raises
    ------
    ValueError
        If `T1` and `T2` have a different number of dimensions.
    ValueError
        If `T1` and `T2` do not have the same shape.

    Attributes
    ----------
    T1 : TensorType
        First tensor in the residual.
    T2 : TensorType
        Second tensor in the residual.
    ndim : int
        Number of dimensions of the residual.
    shape : Shape
        Shape of the residual.

    See Also
    --------
    :func:`pytensorlab.datatypes.binops.residual`
    """

    def __init__(self, T1: TensorType, T2: TensorType, _use_cached_frob: bool = False):
        if T1.ndim != T2.ndim:
            raise ValueError(
                f"T1 and T2 have a different number of dimensions: {T1.ndim} != "
                f"{T2.ndim}"
            )
        if T1.shape != T2.shape:
            raise ValueError(
                f"dimensions of the tensors do not match: T1 has dimensions "
                f"{T1.shape} and T2 has dimensions {T2.shape}"
            )

        self.T1 = T1
        self.T2 = T2
        super().__init__(T1.shape)
        self._use_cached_frob = _use_cached_frob

    def setflags(self, write: bool) -> None:
        """Set tensor flag WRITEABLE.

        This flag determines whether or not `T1` and `T2` of a `DeferredResidual` can be
        written to.

        Parameters
        ----------
        write : bool
            Describes whether or not `T1` and `T2` can be written to.
        """
        super().setflags(write)
        self.T1.setflags(write=write)
        self.T2.setflags(write=write)

    def transpose(self, axes: AxisLike | None = None) -> "DeferredResidual":
        """Return a residual for tensors with permuted axes.

        Parameters
        ----------
        axes : AxisLike, optional
            If specified, it must be a permutation of ``range(self.ndim)``. The i-th
            axis of the returned tensor will correspond to the axis ``axes[i]`` of the
            input tensors. Negative indexing of these axes is allowed. If `axes` does
            not include all values in ``range(self.ndim)``, the remaining axes are
            appended in decreasing order.

        Returns
        -------
        Self
            A new `DeferredResidual` with permuted axes.
        """
        axes = normalize_axes(axes, self.ndim, fill=True, fillreversed=True)
        return DeferredResidual(self.T1.transpose(axes), self.T2.transpose(axes))

    def __array__(self, dtype: DTypeLike = None, copy: bool | None = None) -> ArrayType:
        return np.asarray(self.T1) - np.asarray(self.T2)

    def __neg__(self) -> "DeferredResidual":
        return DeferredResidual(self.T2, self.T1)

    def _getitem_sliced(self, key):
        T1, T2 = getitem(self.T1, key), getitem(self.T2, key)
        if all(isint(k) for k in key):
            return cast(float, T1) - cast(float, T2)

        return DeferredResidual(cast(TensorType, T1), cast(TensorType, T2))

    def _entry(self, indices: Sequence[IndexType]) -> ArrayType:
        return self.T1[indices] - self.T2[indices]  # type:ignore

    def reshape(self, shape: ShapeLike) -> Self:
        return type(self)(self.T1.reshape(shape), self.T2.reshape(shape))

    @property
    def dtype(self) -> np.dtype[Any]:
        """Datatype of the tensor elements.

        Returns
        -------
        numpy.dtype[Any]
            The datatype of the tensor elements.
        """
        return np.result_type(self.T1.dtype, self.T2.dtype)

    def copy(self) -> Self:
        """Create copy of tensor.

        Returns
        -------
        Self
            Copy of the tensor.
        """
        return type(self)(self.T1, self.T2)

    def iscomplex(self) -> bool:
        """Test if the tensor elements are complex.

        Returns
        -------
        bool
            If the tensor elements are complex.
        """
        return tlb.iscomplexobj(self.T1) or tlb.iscomplexobj(self.T2)

    def conj(self) -> Self:
        """Compute complex conugate tensor.

        Returns
        -------
        Self
            `DeferredResidual` for complex conjugate tensors.
        """
        if self.iscomplex():
            return type(self)(self.T1.conj(), self.T2.conj())
        return self


@_mtkrprod_single.register
def _mtkrprod_single_deferred(
    T: DeferredResidual, U: Sequence[MatrixType], axis: int, conjugate: bool = True
) -> MatrixType:
    return _mtkrprod_single(T.T1, U, axis) - _mtkrprod_single(T.T2, U, axis)


@_mtkrprod_all.register
def _mtkrprod_all_deferred(
    T: DeferredResidual, U: Sequence[MatrixType], conjugate: bool = True
) -> Sequence[MatrixType]:
    return [M1 - M2 for M1, M2 in zip(_mtkrprod_all(T.T1, U), _mtkrprod_all(T.T2, U))]


@_tmprod.register
def _tmprod_deferred_array(
    T: DeferredResidual, matrices: Sequence[MatrixType], axes: Axis
) -> DeferredResidual:
    return DeferredResidual(
        _tmprod(T.T1, matrices, axes), _tmprod(T.T2, matrices, axes)
    )


@_tvprod.register
def _tvprod_deferred_array(
    T: DeferredResidual, vectors: Sequence[VectorType], axes: Axis
) -> DeferredResidual | NumberType:
    res1 = _tvprod(T.T1, vectors, axes)
    res2 = _tvprod(T.T2, vectors, axes)
    number_types = (int, float, complex)
    if not isinstance(res1, number_types) and not isinstance(res2, number_types):
        return DeferredResidual(res1, res2)
    return cast(NumberType, np.array(res1) - np.array(res2))


@_mtkronprod_single.register
def _mtkronprod_single_deferred_array(
    T: DeferredResidual,
    U: Sequence[MatrixType],
    axis: int,
    transpose: Literal["T", "H"] | None = None,
) -> MatrixType:
    M1 = _mtkronprod_single(T.T1, U, axis, transpose)
    M2 = _mtkronprod_single(T.T2, U, axis, transpose)
    return M1 - M2


@_mtkronprod_all.register
def _mtkronprod_all_deferred_array(
    T: DeferredResidual,
    U: Sequence[MatrixType],
    transpose: Literal["T", "H"] | None = None,
) -> Sequence[MatrixType]:
    M1 = _mtkronprod_all(T.T1, U, transpose=transpose)
    M2 = _mtkronprod_all(T.T2, U, transpose=transpose)
    return list(map(sub, M1, M2))

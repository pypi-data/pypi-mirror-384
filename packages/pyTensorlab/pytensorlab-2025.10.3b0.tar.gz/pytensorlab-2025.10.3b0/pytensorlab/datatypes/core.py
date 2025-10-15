"""Definitions of general tensor operations.

This module defines useful operations for working with tensors. The operations work for
any subtype of :class:`.Tensor` and on :class:`numpy.ndarray`. The former represents
structured tensors and the latter represents dense tensors, that is, multidimensional
arrays. The operations involve computing the Frobenius norm of a tensor using
:func:`frob`, retrieving elements from tensors using :func:`.getitem`, reshaping
matrices or tensors, such as :func:`.mat2tens`, :func:`.tens2mat`, :func:`.matricize`,
:func:`.tens2vec`, and :func:`.vectorize`, and computing products between a tensor and
matrices, such as :func:`.mtkrprod`, :func:`.mtkronprod`, :func:`.tmprod`, and between a
tensor and a vector using :func:`.tvprod`.

Routines
--------
frob
    Computes the Frobenius norm of a tensor.
getitem
    Return items T[key].
mat2tens
    Tensorize a matrix.
matricize
    Reshape the tensor into a matrix.
mtkronprod
    Compute the matricized tensor times Kronecker products.
mtkrprod
    Compute the matricized tensor times Khatri--Rao products.
tens2mat
    Reshape the tensor into a matrix.
tens2vec
    Reshape the tensor into a vector.
tmprod
    Compute the tensor-matrix product.
tvprod
    Compute the tensor-vector product.
vectorize
    Reshape the tensor into a vector.
"""

import math
from collections.abc import Sequence
from functools import singledispatch
from typing import (
    TYPE_CHECKING,
    Literal,
    TypeVar,
    cast,
    overload,
)

import numpy as np

from pytensorlab.typing import (
    ArrayType,
    Axis,
    AxisLike,
    IndexLike,
    MatrixLike,
    MatrixType,
    NumberType,
    Shape,
    SparseMatrix,
    TensorType,
    VectorType,
)

from ..util.indextricks import _ensure_mutex_axis_permutation, findfirst, normalize_axes

if TYPE_CHECKING:
    from .deferred_residual import DeferredResidual
    from .partial import IncompleteTensor, PartialTensor, SparseTensor
    from .tensor import DenseTensor, Tensor
else:
    PartialTensor = type["PartialTensor"]
    SparseTensor = type["SparseTensor"]
    IncompleteTensor = type["IncompleteTensor"]
    Tensor = type["Tensor"]
    DenseTensor = type["DenseTensor"]
    DeferredResidual = type["DeferredResidual"]


@overload
def mtkrprod(
    T: TensorType, U: Sequence[MatrixType], *, conjugate: bool = True
) -> Sequence[MatrixType]: ...


@overload
def mtkrprod(
    T: TensorType, U: Sequence[MatrixType], axis: int, *, conjugate: bool = True
) -> MatrixType: ...


def mtkrprod(
    T: TensorType,
    U: Sequence[MatrixType],
    axis: int | None = None,
    conjugate: bool = True,
) -> MatrixType | Sequence[MatrixType]:
    """Compute the matricized tensor times Khatri--Rao products.

    The matricized tensor times Khatri--Rao products (mtkrprod) can be computed as::

        tens2mat(T, axis) @ kr(*tuple(U[i].conj() for i in range(T.ndim) if i != axis))

    without permuting the tensor `T`. If `axis` is given, only one mtkrprod is computed,
    otherwise the mtkrprod is computed for all `axis`, i.e., ``axis in range(T.ndim)``.

    Parameters
    ----------
    T : TensorType
        The tensor to be matricized.
    U : Sequence[MatrixType]
        List of factor matrices.
    axis : int, optional
        Axis to exclude. By default, all axes are excluded once.
    conjugate : bool, default = True
        Take the complex conjugate of the factor matrices in `U` before computing the
        matricized tensor times Khatri--Rao product.

    Returns
    -------
    MatrixType | Sequence[MatrixType]
        Matrix containing the matricized tensor times Khatri--Rao product (if `axis` is
        given.) List of matrix containing the matricized tensor times Khatri--Rao
        products w.r.t. all axes (only if no `axis` parameter is given.)

    Raises
    ------
    ValueError
        If not all factors have the same number of columns.
    ValueError
        If the number of factors is smaller than ``T.ndim``.
    ValueError
        If the column dimension of a factor does not match the corresponding dimension
        of `T`.
    ValueError
        If any factor in ``factors[T.ndim:]`` is not a row vector.
    ValueError
        If `axis` is not within ``range(-T.ndim, T.ndim)``.

    Notes
    -----
    For improved performance, it is advisable for the largest dimension to be the first
    or last axis of `T`.

    A permutation-free variant is implemented [1]_.

    References
    ----------
    .. [1] N. Vannieuwenhoven, K. Meerbergen, R. Vandebril, "Computing the
       gradient in optimization algorithms for the CP decomposition in constant memory
       through tensor blocking," SIAM Journal on Scientific Computing 37(3):C415--C438,
       2015.
    """
    if any(f.ndim != 2 for f in U):
        idx = next(i for i, f in enumerate(U) if f.ndim != 2)
        raise ValueError(
            f"factors is not a sequence of matrices: factor {idx} has "
            f"{U[idx].ndim} dimensions while expected 2"
        )
    if any(f.shape[1] != U[0].shape[1] for f in U):
        idx = next(i for i, f in enumerate(U) if f.shape[1] != U[0].shape[1])
        raise ValueError(
            f"not all factors have the same number of columns: factor {idx} has "
            f"{U[idx].shape[1]} columns while expected {U[0].shape[1]}"
        )

    if len(U) < T.ndim:
        raise ValueError(
            f"the number of factors is smaller than the number of dimensions of T: "
            f"len(factors) is {len(U)} while expected at least {T.ndim}"
        )
    shape_factors = [f.shape[0] for f in U]
    if any(s1 != s2 for s1, s2 in zip(T.shape, shape_factors)):
        idx = next(
            i for i, (s1, s2) in enumerate(zip(T.shape, shape_factors)) if s1 != s2
        )
        raise ValueError(
            f"shape[0] of factor {idx} not match the corresponding dimension of T: "
            f"{U[idx].shape[0]} while expected {T.shape[idx]}"
        )
    if any(s != 1 for s in shape_factors[T.ndim :]):
        idx = next(i for i, s in enumerate(shape_factors[T.ndim :]) if s != 1)
        raise ValueError(
            f"factor {idx} should be a row vector: number of rows is "
            f"{U[idx].shape[0]} while expected 1"
        )
    if axis is not None:
        if not (-len(U) <= axis < len(U)):
            raise ValueError(
                f"axis is out of bounds w.r.t. the number of factors: axis is {axis} "
                f"while expected {-len(U)} <= axis < {len(U)}"
            )
        axis = axis if axis >= 0 else len(U) + axis
        return _mtkrprod_single(T, U, axis, conjugate)
    return _mtkrprod_all(T, U, conjugate)


@singledispatch
def _mtkrprod_single(
    T: TensorType, U: Sequence[MatrixType], axis: int, conjugate: bool = True
) -> MatrixType:
    raise NotImplementedError


@singledispatch
def _mtkrprod_all(
    T: TensorType, U: Sequence[MatrixType], conjugate: bool = True
) -> Sequence[MatrixType]:
    return [_mtkrprod_single(T, U, n, conjugate) for n in range(len(U))]


@overload
def mtkronprod(
    T: TensorType,
    U: Sequence[MatrixType],
    *,
    transpose: Literal["T", "H"] | None = None,
) -> Sequence[MatrixType]: ...


@overload
def mtkronprod(
    T: TensorType,
    U: Sequence[MatrixType],
    axis: int,
    transpose: Literal["T", "H"] | None = None,
) -> MatrixType: ...


def mtkronprod(
    T: TensorType,
    U: Sequence[MatrixType],
    axis: int | None = None,
    transpose: Literal["T", "H"] | None = None,
) -> MatrixType | Sequence[MatrixType]:
    """Compute the matricized tensor times Kronecker products.

    The matricized tensor times Kronecker products (mtkronprod) can be computed as::

        Uc = tuple(u.conj() for i, u in enumerate(U) if i != axis)
        tens2mat(T, axis) @ kron(*Uc)

    without permuting the tensor `T`. If `axis` is given, only one mtkronprod is
    computed, otherwise the mtkronprod is computed for all `axis`, i.e., ``axis in
    range(T.ndim)``. The `transpose` option can be used to apply a transpose or
    conjugated transpose to the matrices `U` before computing the product.

    Parameters
    ----------
    T : TensorType
        The tensor to be matricized.
    U : Sequence[MatrixType]
        List of ``T.ndim`` matrices.
    axis : int, optional
        Axis to exclude. By default, all modes are excluded once.
    transpose : "T" | "H", optional
        Whether to transpose or conjugate transpose the factor matrices before computing
        the matricized tensor times Kronecker product.

    Returns
    -------
    MatrixType | Sequence[MatrixType]
        Matrix containing the matricized tensor times Kronecker product. (If `axis` is
        given.) List of matrices containing the matricized tensor times Kronecker
        products w.r.t. all axes. (Only if `axis` is not given.)

    Raises
    ------
    ValueError
        If the number of factors does not equal ``T.ndim``.
    ValueError
        If the column dimension of a factor does not match the corresponding dimension
        of `T`.
    ValueError
         If `axis` is not within ``range(-T.ndim, T.ndim)``.
    """
    if any(f.ndim != 2 for f in U):
        idx = next(i for i, f in enumerate(U) if f.ndim != 2)
        raise ValueError(
            f"factors is not a sequence of matrices: factor {idx} has "
            f"{U[idx].ndim} dimensions while expected 2"
        )

    if len(U) < T.ndim:
        raise ValueError(
            f"the number of factors does not match the order of the tensor T: "
            f"len(factors) is {len(U)} while expected at least {T.ndim}"
        )

    i = int(transpose in ("T", "H"))
    mismatch = tuple(f.shape[i] != s for f, s in zip(U, T.shape))
    if any(mismatch):
        idx = mismatch.index(True)
        raise ValueError(
            f"shape[{i}] of factor {idx} not match the corresponding dimension of T: "
            f"{U[idx].shape[i]} while expected {T.shape[idx]}"
        )

    if axis is not None:
        if not (-len(U) <= axis < len(U)):
            raise ValueError(
                f"axis is out of bounds w.r.t. the number of factors: axis is {axis} "
                f"while expected {-len(U)} <= axis < {len(U)}"
            )
        axis = axis if axis >= 0 else len(U) + axis
        return _mtkronprod_single(T, U, axis, transpose)
    else:
        return _mtkronprod_all(T, U, transpose)


@singledispatch
def _mtkronprod_single(
    T: TensorType,
    U: Sequence[MatrixType],
    axis: int,
    transpose: Literal["T", "H"] | None = None,
) -> MatrixType:
    raise NotImplementedError


@singledispatch
def _mtkronprod_all(
    T: TensorType,
    U: Sequence[MatrixType],
    transpose: Literal["T", "H"] | None = None,
) -> Sequence[MatrixType]:
    return [_mtkronprod_single(T, U, n, transpose) for n in range(len(U))]


@singledispatch
def frob(T: TensorType, squared=False) -> float:
    """Compute the Frobenius norm of a tensor.

    Parameters
    ----------
    T : ArrayType
        The tensor to compute the Frobenius norm of.
    squared : bool, default = False
        If true, return the squared Frobenius norm of the tensor.

    Returns
    -------
    float
        Frobenius norm of the tensor.
    """
    raise NotImplementedError


@overload
def tens2mat(
    T: ArrayType, row: AxisLike = 0, col: AxisLike | None = None
) -> MatrixType: ...


@overload
def tens2mat(
    T: PartialTensor, row: AxisLike = 0, col: AxisLike | None = None
) -> SparseMatrix: ...


@overload
def tens2mat(
    T: DenseTensor, row: AxisLike = 0, col: AxisLike | None = None
) -> MatrixType: ...


@overload
def tens2mat(
    T: Tensor, row: AxisLike = 0, col: AxisLike | None = None
) -> MatrixLike: ...


def tens2mat(
    T: TensorType, row: AxisLike = 0, col: AxisLike | None = None
) -> MatrixLike:
    """Reshape the tensor into a matrix.

    Reshapes the tensor `T` into a matrix, in which the rows contain the axes in the
    order of `row` and the columns contain the axes in the order of `col`, i.e.::

        shape = (np.prod(T.shape[i] for i in row), np.prod(T.shape[i] for i in col))
        M = np.reshape(np.transpose(np.asarray(T), row + col), shape)

    Parameters
    ----------
    T : TensorType
        The tensor to matricize.
    row : AxisLike, default = 0
        The axes of the tensor in the rows of the matrix unfolding in order.
    col : AxisLike, optional
        The axes of the tensor in the columns of the matrix unfolding in order. The axes
        in ``range(T.ndim)`` that are not in `row` or `col` are appended to `col` in
        ascending order.

    Returns
    -------
    MatrixType
        Matricization of `T`.

    Raises
    ------
    ValueError
        If `row` and `col` share at least one axis.

    Notes
    -----
    If `T` is an instance of :class:`.Tensor`, the full array is constructed and
    subsequently permuted and reshaped such that its requested matricization is
    obtained.

    Examples
    --------
    >>> import numpy as np
    >>> import pytensorlab as tl

    >>> T = np.reshape(np.arange(8), (2, 2, 2))
    >>> tl.tens2mat(T, 0)
    array([[0, 1, 2, 3],
           [4, 5, 6, 7]])

    >>> tl.tens2mat(T, (2, 0), 1)
    array([[0, 2],
           [4, 6],
           [1, 3],
           [5, 7]])
    """
    row, col = _ensure_mutex_axis_permutation(row, col, T.ndim)
    return _tens2mat(T, row, col)


@singledispatch
def _tens2mat(T: TensorType, row: Axis, col: Axis) -> MatrixLike:
    shape: tuple[int, ...] = (math.prod(T.shape[i] for i in row),)
    if len(col) > 0:
        shape += (math.prod(T.shape[i] for i in col),)
    else:
        shape += (1,)
    return np.reshape(np.asarray(T.transpose(tuple(row) + tuple(col))), shape)


def matricize(
    T: TensorType, row: AxisLike = 0, col: AxisLike | None = None
) -> MatrixLike:
    """Reshape the tensor into a matrix.

    Alias of :func:`tens2mat`. Refer to :func:`tens2mat` for full
    documentation.

    Parameters
    ----------
    T : TensorType
        The tensor to matricize.
    row : AxisLike, default = 0
        The axes of the tensor in the rows of the matrix unfolding in order.
    col : AxisLike, optional
        The axes of the tensor in the columns of the matrix unfolding in order. The
        axes in ``range(T.ndim)`` that are not in `row` or `col` are appended to
        `col` in ascending order.

    Returns
    -------
    MatrixType
        Matricization of `T`.
    """
    return tens2mat(T, row, col)


def tens2vec(T: TensorType, axes: AxisLike | None = None) -> VectorType:
    """Reshape the tensor into a vector.

    Reshapes the tensor `T` into a vector, after permuting its axes in the order `axes`,
    i.e. ``np.transpose(np.asarray(T), axes).ravel()``.

    Parameters
    ----------
    T : TensorType
        The tensor to vectorize.
    axes : AxisLike, optional
        Transpose `T` before vectorization using `axes`, which is a subset of
        ``range(T.ndim)``. Unspecified axes are appended in ascending order.

    Returns
    -------
    VectorType
        Vectorization of `T`.

    Raises
    ------
    ValueError
        If `axes` contains repeated axes.
    ValueError
        If any axis is not within ``range(-T.ndim, T.ndim)``.

    Notes
    -----
    If `T` is an instance of :class:`.Tensor`, the full array is constructed and
    subsequently permuted and reshaped such that its requested vectorization is
    obtained.

    Examples
    --------
    >>> import numpy as np
    >>> import pytensorlab as tl

    >>> T = np.reshape(np.arange(8), (2, 2, 2))
    >>> tl.tens2vec(T)
    array([0, 1, 2, 3, 4, 5, 6, 7])
    >>> tl.tens2vec(T, (2, 0, 1))
    array([0, 2, 4, 6, 1, 3, 5, 7])
    """
    axes = normalize_axes(axes, T.ndim)
    return np.asarray(T.transpose(axes)).ravel()


def vectorize(T: TensorType, axes: AxisLike | None = None) -> VectorType:
    """Reshape the tensor into a vector.

    Alias of :func:`tens2vec`. Refer to :func:`tens2vec` for full documentation.

    Parameters
    ----------
    T : TensorType
        The tensor to vectorize.
    axes : AxisLike, optional
        Transpose `T` before vectorization using `axes`, which is a subset of
        ``range(T.ndim)``. Unspecified axes are appended in ascending order.

    Returns
    -------
    VectorType
        Vectorization of `T`.
    """
    return tens2vec(T, axes)


@overload
def mat2tens(
    matrix: MatrixType,
    shape: Shape,
    row: AxisLike = 0,
    col: AxisLike | None = None,
) -> ArrayType: ...


@overload
def mat2tens(
    matrix: SparseMatrix,
    shape: Shape,
    row: AxisLike = 0,
    col: AxisLike | None = None,
) -> SparseTensor: ...


def mat2tens(
    matrix: MatrixLike,
    shape: Shape,
    row: AxisLike = 0,
    col: AxisLike | None = None,
) -> TensorType:
    """Tensorize a matrix.

    Reshapes `matrix` into a tensor with shape `shape`, given that 'row' contains the
    axis of the tensor corresponding to the rows of `matrix` and that `col` contains the
    axis of the tensor corresponding to the columns of the matrix::

        rowshape = tuple(shape[i] for i in row)
        colshape = tuple(shape[i] for i in col)
        T = np.transpose(matrix.reshape(rowshape + colshape), np.argsort(row + col))

    Parameters
    ----------
    matrix : MatrixType
        The matrix to tensorize.
    shape : Shape
        The shape of the resulting reshaped tensor.
    row : AxisLike, default = 0
        The axes of the tensor in the rows of `matrix` in order.
    col : AxisLike, optional
        The axes of the tensor in the columns of `matrix` in order. The axes in
        ``range(len(shape))`` that are not in `row` or `col` are appended to `col` in
        ascending order.

    Returns
    -------
    ArrayType
        The tensorization of `matrix`.

    Raises
    ------
    ValueError
        If `matrix` has more than two dimensions.
    ValueError
        If the number of elements of `matrix` does not match `shape`.
    ValueError
        If `row` and `col` share an axis.
    """
    if matrix.ndim > 2:
        raise ValueError("matrix has more than two dimensions")
    if math.prod(matrix.shape) != math.prod(shape):
        raise ValueError(
            f"number of elements in matrix does not match shape: matrix has "
            f"{math.prod(matrix.shape)} elements while expecting {math.prod(shape)}"
        )
    row, col = _ensure_mutex_axis_permutation(row, col, len(shape))

    return _mat2tens(matrix, shape, row, col)


@singledispatch
def _mat2tens(matrix: MatrixLike, shape: Shape, row: Axis, col: Axis) -> TensorType:
    raise NotImplementedError


_DenseTensor = TypeVar("_DenseTensor", bound=DenseTensor)


@overload
def tmprod(
    T: SparseTensor,
    matrices: MatrixType | Sequence[MatrixType],
    axes: AxisLike,
    transpose: Literal["T", "H"] | None = None,
) -> ArrayType | SparseTensor:
    # Returns the SparseTensor T itself if axes are empty and ArrayType otherwise
    ...


@overload
def tmprod(
    T: IncompleteTensor,
    matrices: MatrixType | Sequence[MatrixType],
    axes: AxisLike,
    transpose: Literal["T", "H"] | None = None,
) -> IncompleteTensor: ...


@overload
def tmprod(
    T: ArrayType,
    matrices: MatrixType | Sequence[MatrixType],
    axes: AxisLike,
    transpose: Literal["T", "H"] | None = None,
) -> ArrayType: ...


@overload
def tmprod(
    T: _DenseTensor,
    matrices: MatrixType | Sequence[MatrixType],
    axes: AxisLike,
    transpose: Literal["T", "H"] | None = None,
) -> _DenseTensor: ...


@overload
def tmprod(
    T: DeferredResidual,
    matrices: MatrixType | Sequence[MatrixType],
    axes: AxisLike,
    transpose: Literal["T", "H"] | None = None,
) -> DeferredResidual: ...


@overload
def tmprod(
    T: Tensor,
    matrices: MatrixType | Sequence[MatrixType],
    axes: AxisLike,
    transpose: Literal["T", "H"] | None = None,
) -> TensorType: ...


def tmprod(
    T: TensorType,
    matrices: MatrixType | Sequence[MatrixType],
    axes: AxisLike,
    transpose: Literal["T", "H"] | None = None,
) -> TensorType:
    """Compute the tensor-matrix product.

    Computes the tensor-matrix product of the tensor `T` with `matrices` along the axes
    specified in `axes`. A tensor-matrix product results in a new tensor `S` in which
    the vectors along an axis in `axes` of the given tensor `T` are premultiplied by the
    corresponding matrix in `matrices`::

        S = T
        for n, m in zip(axes, matrices):
            S = m @ tens2mat(S, n)
            S = mat2tens(S, n)

    Parameters
    ----------
    T : TensorType
        Tensor to compute the tensor-matrix product with.
    matrices : MatrixType | Sequence[MatrixType]
        Matrix or list of matrices to be multiplied with the tensor.
    axes : AxisLike
        List of distinct axes along which the multiplications are executed.
    transpose : "T" | "H", optional
        Perform the tensor-matrix product with the transposed ("T") or conjugated
        transposed ("H") matrices. By default, the product is performed without
        transposing or conjugating the matrices first.

    Returns
    -------
    S : TensorType
        Resulting tensor of the tensor-matrix products.

    Raises
    ------
    ValueError
        If any axis in `axes` is not within ``range(-T.ndim, T.ndim)``.
    ValueError
        If the number of matrices does not match the number of axes.
    ValueError
        If the row dimension of a matrix does not match the dimension of `T` along the
        corresponding axis.

    See Also
    --------
    tvprod
    """
    axes = normalize_axes(axes, T.ndim, fill=False)
    if not axes:
        return T
    if not isinstance(matrices, Sequence):
        matrices = (matrices,)
    if len(axes) != len(matrices):
        raise ValueError(
            f"number of matrices ({len(matrices)}) does not match number of axes "
            f"({len(axes)})"
        )
    nonmat = [m.ndim != 2 for m in matrices]
    if any(nonmat):
        idx = findfirst(nonmat)
        raise ValueError(
            f"matrices[{idx}] has {matrices[idx].ndim} dimension(s) instead of 2"
        )
    if transpose is not None:
        if transpose not in ["T", "H"]:
            raise ValueError(
                'invalid value for transpose, correct values are "T" or "H"'
            )
        matrices = [m.T if transpose == "T" else m.conj().T for m in matrices]
    dimmismatch = [m.shape[1] != T.shape[a] for m, a in zip(matrices, axes)]
    if any(dimmismatch):
        idx = findfirst(dimmismatch)
        raise ValueError(
            f"matrix row dimension (={matrices[idx].shape[1]}) does not "
            f"match the dimension of the tensor (="
            f"{T.shape[axes[idx]]}) along axis {axes[idx]}"
        )
    # Sort ascendingly on axis
    matrices, axes = cast(
        tuple[Sequence[MatrixType], Axis],
        tuple(zip(*sorted(zip(matrices, axes), key=lambda x: x[1]))),
    )

    return _tmprod(T, matrices, axes)


@singledispatch
def _tmprod(T: TensorType, matrices: Sequence[MatrixType], axes: Axis) -> TensorType:
    raise NotImplementedError


@overload
def tvprod(
    T: SparseTensor, vectors: VectorType | Sequence[VectorType], axes: AxisLike
) -> ArrayType | NumberType: ...


@overload
def tvprod(
    T: IncompleteTensor,
    vectors: VectorType | Sequence[VectorType],
    axes: AxisLike,
) -> IncompleteTensor | NumberType: ...


@overload
def tvprod(
    T: ArrayType, vectors: VectorType | Sequence[VectorType], axes: AxisLike
) -> ArrayType | NumberType: ...


@overload
def tvprod(
    T: _DenseTensor, vectors: VectorType | Sequence[VectorType], axes: AxisLike
) -> _DenseTensor | NumberType: ...


@overload
def tvprod(
    T: DeferredResidual,
    vectors: VectorType | Sequence[VectorType],
    axes: AxisLike,
) -> DeferredResidual | NumberType: ...


def tvprod(
    T: TensorType, vectors: VectorType | Sequence[VectorType], axes: AxisLike
) -> TensorType | NumberType:
    """Compute the tensor-vector product.

    Computes the product of the tensor `T` with `vectors` along the axes specified in
    `axes`. For each vector in `vectors`, the inner product between this vector and the
    vectors in `T` along the corresponding axis is computed. The number of dimensions of
    the resulting tensor `S` equals the number of dimensions of `T` minus the number
    of vectors in `vectors`, since each multiplication of `T` with a vector reduces the
    dimension of this axis to one, effectively removing it from the resulting tensor::

        S = T
        for n, v in zip(axes, vectors):
            S = v @ tens2mat(S, n)
            S = mat2tens(S, n)
        S = np.squeeze(S, axes)

    Parameters
    ----------
    T : TensorType
        Tensor to compute the tensor-vector product with.
    vectors : VectorType | Sequence[VectorType]
        Vector or list of vectors to be multiplied with the tensor.
    axes : AxisLike
        Axis or list of distinct axes along which the multiplications are executed.

    Returns
    -------
    S: TensorType | NumberType
        A scalar value is returned if the tensor is multiplied in each axis with a
        vector, that is, ``axis in range(T.ndim)``. Otherwise, a tensor is returned.

    Raises
    ------
    ValueError
        If the number of vectors does not match the number of axes.

    See Also
    --------
    .tmprod
    """
    axes = normalize_axes(axes, T.ndim, fill=False)
    if not axes:
        return T
    if not isinstance(vectors, Sequence):
        vectors = (vectors,)
    if len(axes) != len(vectors):
        raise ValueError(
            f"number of vectors ({len(vectors)}) does not match number of axes "
            f"({len(axes)})"
        )
    nonvec = [v.ndim != 1 for v in vectors]
    if any(nonvec):
        if any(sum(s > 1 for s in v.shape) > 1 for v in vectors):
            idx = findfirst(nonvec)
            raise ValueError(
                f"vectors[{idx}] has {vectors[idx].ndim} dimension(s) instead of 1"
            )
        else:  # transform into vectors
            vectors = tuple(v.ravel() for v in vectors)
    dimmismatch = [v.shape[0] != T.shape[a] for v, a in zip(vectors, axes)]
    if any(dimmismatch):
        idx = findfirst(dimmismatch)
        raise ValueError(
            f"vector dimension (={vectors[idx].shape[0]}) does not "
            f"match the dimension of the tensor (="
            f"{T.shape[axes[idx]]}) along axis {axes[idx]}"
        )
    # Sort ascendingly on axis
    vectors, axes = cast(
        tuple[Sequence[VectorType], Axis],
        tuple(zip(*sorted(zip(vectors, axes), key=lambda x: x[1]))),
    )
    return _tvprod(T, vectors, axes)


@singledispatch
def _tvprod(
    T: TensorType, vectors: Sequence[VectorType], axes: Axis
) -> TensorType | NumberType:
    raise NotImplementedError


@singledispatch
def getitem(T: TensorType, key: IndexLike) -> TensorType | float:
    """Return items T[key].

    pyTensorlab indexing works in the same way as NumPy indexing, except for tuple
    indices. In NumPy, advanced (i.e. element-wise) indexing is used for tuples, while
    basic indexing (i.e. slicing) is performed for tuples in pyTensorlab.

    Parameters
    ----------
    T : ArrayType
        Array to perform pyTensorlab indexing on.
    key : IndexLike
        Indices of the elements to be returned.

    Returns
    -------
    TensorType | float
        Array containing the elements of `T` as specified by the indices in `key`.

    Raises
    ------
    IndexError
        If `key` contains more indices than the number of dimensions of `T`.
    IndexError
        If an index is out of bounds.

    Examples
    --------
    >>> import pytensorlab as tl
    >>> import numpy as np

    >>> T = np.random.randn(3, 4, 5)
    >>> key = ((0, 1), (3, 1), slice(3))
    >>> T[key].shape
    (2, 3)
    >>> tl.getitem(T, key).shape
    (2, 2, 3)
    """
    raise NotImplementedError

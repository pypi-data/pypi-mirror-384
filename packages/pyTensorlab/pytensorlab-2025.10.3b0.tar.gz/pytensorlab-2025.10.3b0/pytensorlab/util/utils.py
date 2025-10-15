"""Collection of computational utility functions.

Routines
--------
hadamard
    Element-wise (Hadamard) product of a sequence of arrays.
hadamard_all
    Element-wise product of each combination of a sequence of arrays.
kr
    Khatri--Rao product of a sequence of matrices.
krr
    Row-wise Khatri--Rao product of a sequence of matrices.
kron
    Kronecker product of a sequence of matrices.
inprod_kr
    Inner product of the Khatri--Rao products of two sets of matrices.
noisy
    Noisy version of a given array.
"""

import itertools as it
import math
import operator
from collections.abc import Iterable, Sequence, Sized
from functools import reduce, singledispatch
from typing import (
    Any,
    Protocol,
    TypeAlias,
    TypeGuard,
    TypeVar,
    cast,
    runtime_checkable,
)

import numba as nb  # type:ignore
import numpy as np
import scipy.sparse as sps
from numpy import ndarray, newaxis

import pytensorlab.backends.numpy as tlb
from pytensorlab.random.rng import get_rng
from pytensorlab.typing import (
    ArrayType,
    MatrixLike,
    MatrixType,
    Sequenceable,
)
from pytensorlab.typing.core import VectorType

from ..util.indextricks import findfirst
from .indextricks import _ensure_sequence

_USE_NUMBA = True


def set_numba(flag: bool) -> None:
    """Set whether or not to use Numba for computations.

    Enables or disables the use of the package Numba for computations.

    Parameters
    ----------
    flag : bool
        Select Numba implementation for some computational routines if True.

    See Also
    --------
    numba_activated, kron, kr

    Notes
    -----
    With the use of Numba, some functions like `kron` and `kr` may be accelerated, but
    require compilation the first time they are used.
    """
    global _USE_NUMBA
    _USE_NUMBA = flag


def is_numba_enabled() -> bool:
    """Query whether or not to use Numba for computations.

    Return whether or not the package Numba is used for computations.

    Returns
    -------
    bool
        Whether or not Numba is used for computations.

    See Also
    --------
    set_numba, kron, kr

    Notes
    -----
    With the use of Numba, some functions like `kron` and `kr` may be accelerated, but
    require compilation the first time they are used.
    """
    global _USE_NUMBA
    return _USE_NUMBA


def kron(*arrays: MatrixType) -> MatrixType:
    """Compute the Kronecker product of two or more matrices.

    For two matrices `A` and `B` with shapes ``(I, J)`` and ``(K, L)``,
    ``C = kr(A, B)`` has shape ``(I * J, K * L)``. Each entry is defined as
    ``C[i * I + k, j * J + l] = A[i, j] * B[k, l]``.

    Parameters
    ----------
    arrays : MatrixType
        Two or more matrices.

    Returns
    -------
    MatrixType
        The Kronecker product of the given matrices.

    See Also
    --------
    numpy.kron, kr

    Notes
    -----
    This function is equivalent to :func:`numpy.kron`, except that

    - this implementation also supports more than two matrices and
    - this implementation only supports matrices (arrays with two dimensions).

    The Kronecker product is associative, meaning that ``kron(A, B, C)`` is equal to
    ``kron(kron(A, B), C)`` or ``kron(A, kron(B, C))``.

    Examples
    --------
    >>> import numpy as np
    >>> A = np.array([[1, 0],
    ...               [0, 2]])
    >>> B = np.array([[1, 3],
    ...               [2, 4]])
    >>> kron(A, B)
    array([[1, 3, 0, 0],
           [2, 4, 0, 0],
           [0, 0, 2, 6],
           [0, 0, 4, 8]])
    """
    if not arrays:
        return np.array([])
    if any(a.ndim != 2 for a in arrays):
        i = findfirst(a.ndim != 2 for a in arrays)
        raise ValueError(f"array at index {i} is not a matrix: ndim = {arrays[i].ndim}")

    return _kron(*arrays)


@nb.njit(parallel=True, cache=True)
def _kron_numba(A: MatrixType, B: MatrixType, dtype: np.dtype) -> MatrixType:
    C = np.empty((A.shape[0], B.shape[0], A.shape[1], B.shape[1]), dtype=dtype)
    for i in nb.prange(A.shape[0]):
        for j in nb.prange(B.shape[0]):
            for m in nb.prange(A.shape[1]):
                for n in nb.prange(B.shape[1]):
                    C[i, j, m, n] = A[i, m] * B[j, n]
    return C.reshape((-1, A.shape[1] * B.shape[1]))


def _kron(*arrays: MatrixType) -> MatrixType:
    if is_numba_enabled():
        dtype = np.result_type(*arrays)
        return reduce(lambda A, B: _kron_numba(A, B, dtype), arrays)
    else:  # Broadcasting based.
        N = len(arrays)
        arrays = tuple(reversed(arrays))
        result = np.ones_like(arrays[0], shape=(1,))
        for n in argsort([array.size for array in arrays]):
            shape = (
                (slice(None),) + (N - 1) * (newaxis,) + (slice(None),) + n * (newaxis,)
            )
            result = result * arrays[n][shape]
        return result.reshape((math.prod(result.shape[:N]), -1))


def kr(*arrays: MatrixType) -> MatrixType:
    """Compute the Khatri--Rao product of two or more matrices.

    The Khatri--Rao or column-wise Kronecker product of the matrices in `arrays` is
    computed.

    For two matrices `A` and `B` with shapes ``(I, K)`` and ``(J, K)``,
    ``C = kr(A, B)`` has shape ``(I * J, K)``. Each entry is defined as::

        C[i * I + j, k] = A[i, k] * B[j, k]

    Parameters
    ----------
    arrays: MatrixType
        Two or more matrices with the same number of columns.

    Returns
    -------
    MatrixType
        The Khatri--Rao product of the given matrices.

    See Also
    --------
    scipy.linalg.khatri_rao, kron, krr

    Notes
    -----
    This function is equivalent to :func:`scipy.linalg.khatri_rao`, except that this
    implementation also supports more than two matrices.

    The Khatri--Rao product is associative, meaning that ``kr(A, B, C)`` is equal to
    ``kr(kr(A, B), C)`` or ``kr(A, kr(B, C))``.

    Examples
    --------
    >>> import numpy as np
    >>> A = np.array([[1, 0],
    ...               [0, 2]])
    >>> B = np.array([[1, 3],
    ...               [2, 4]])
    >>> kr(A, B)
    array([[1, 0],
           [2, 0],
           [0, 6],
           [0, 8]])
    """
    if not arrays:
        return np.array([])
    if len(arrays) == 1:
        return arrays[0].copy()
    arrays = tuple(a[:, np.newaxis] if a.ndim == 1 else a for a in arrays)
    if any(a.ndim != 2 for a in arrays):
        i = findfirst(a.ndim != 2 for a in arrays)
        raise ValueError(f"array at index {i} is not a matrix: ndim = {arrays[i].ndim}")
    if any(a.shape[1] != arrays[0].shape[1] for a in arrays):
        i = findfirst(a.shape[1] != arrays[0].shape[1] for a in arrays)
        raise ValueError(
            f"array {i} should have the same number of columns as the first array: got "
            f"{arrays[i].shape[1]} but expected {arrays[0].shape[1]}"
        )
    return _kr(*arrays)


@nb.njit(parallel=True, cache=True)
def _kr_numba(A: MatrixType, B: MatrixType, dtype: np.dtype) -> MatrixType:
    C = np.empty((A.shape[0], B.shape[0], A.shape[1]), dtype=dtype)
    for i in nb.prange(A.shape[0]):
        for j in nb.prange(B.shape[0]):
            for k in nb.prange(A.shape[1]):
                C[i, j, k] = A[i, k] * B[j, k]
    return C.reshape((-1, A.shape[1]))


def _kr(*arrays: MatrixType) -> MatrixType:
    if is_numba_enabled():
        dtype = np.result_type(*arrays)
        return reduce(lambda A, B: _kr_numba(A, B, dtype), arrays)
    else:  # Broadcasting based.
        arrays = tuple(reversed(arrays))
        result = np.ones_like(arrays[0], shape=(1,))
        for n in argsort([array.size for array in arrays]):
            result = (
                result * arrays[n][(slice(None),) + n * (newaxis,) + (slice(None),)]
            )
        return result.reshape((-1, result.shape[-1]))


def krr(*arrays: MatrixType) -> MatrixType:
    """Compute the row-wise Khatri--Rao product of two or more matrices.

    The row-wise Khatri--Rao product of the matrices in `arrays` is computed. For
    matrices `A` and `B` with shapes ``(I, J)`` and ``(I, K)``, the result
    ``krr(A, B)`` has shape ``(I, J * K)`` and is equal to ``kr(A.T, B.T).T``.

    Parameters
    ----------
    arrays: MatrixType
        Two or more matrices with the same number of rows.

    Returns
    -------
    MatrixType
        The row-wise Khatri--Rao product of the given matrices.

    See Also
    --------
    scipy.linalg.khatri_rao, kron, kr

    Examples
    --------
    >>> import numpy as np
    >>> A = np.array([[1, 0],
    ...               [0, 2]])
    >>> B = np.array([[1, 3],
    ...               [2, 4]])
    >>> krr(A, B)
    array([[1, 3, 0, 0],
           [0, 0, 4, 8]])
    """
    if not arrays:
        return np.array([])
    arrays = tuple(a[:, np.newaxis] if a.ndim == 1 else a for a in arrays)
    if any(a.ndim != 2 for a in arrays):
        i = findfirst(a.ndim != 2 for a in arrays)
        raise ValueError(f"array at index {i} is not a matrix: ndim = {arrays[i].ndim}")
    if any(a.shape[0] != arrays[0].shape[0] for a in arrays):
        i = findfirst(a.shape[0] != arrays[0].shape[0] for a in arrays)
        raise ValueError(
            f"array {i} should have the same number rows columns as the first array: "
            f"got {arrays[i].shape[0]} but expected {arrays[0].shape[0]}"
        )
    arrays = tuple(np.transpose(a) for a in arrays)
    return np.transpose(_kr(*arrays))


def inprod_kr(
    a: Sequence[MatrixType],
    b: Sequence[MatrixType],
    exclude: Sequenceable[int] = (),
) -> MatrixType:
    """Compute the inner product of the Khatri--Rao products of two sets of matrices.

    The inner product of matrices ``A`` and ``B`` is computed, where the matrices
    ``A`` and ``B`` are defined as the Khatri--Rao product of the matrices in `a` and
    `b`, respectively. This is equivalent to computing ``kr(a[i]).conj().T @ kr(b[i])``,
    where ``i`` contains all indices not in `exclude`, but is computed in a more
    efficient way.

    Parameters
    ----------
    a : Sequence[MatrixType]
        Sequence of matrices with the same number of columns.
    b : Sequence[MatrixType]
        Sequence of matrices with the same number of columns.
    exclude : Sequenceable[int], default = ()
        Indices of matrices to be excluded from the inner product.

    Returns
    -------
    MatrixType
        The inner product of the Khatri--Rao product of two sets of matrices.
    """
    exclude = _ensure_sequence(exclude)
    return np.multiply.reduce(
        [a.conj().T @ b for n, (a, b) in enumerate(zip(a, b)) if n not in exclude]
    )


_T = TypeVar("_T", bound=ArrayType)


def hadamard(a: Sequence[_T], exclude: Sequenceable[int] = ()) -> _T:
    """Compute the Hadamard or element-wise product.

    The Hadamard or element-wise product of two or more arrays is computed.

    Parameters
    ----------
    a : Sequence[ArrayType]
        Arrays of the same shape that are multiplied.
    exclude: Sequenceable[int], default = ()
        Index or sequence of indices of arrays in `a` that are excluded from the result.

    Returns
    -------
    ArrayType
        Element-wise product of the arrays in `a` that are not excluded.

    Notes
    -----
    For reasons of speed, the compatibility of the shapes of the arrays is not checked.
    """
    exclude = _ensure_sequence(exclude)
    return np.multiply.reduce([a for n, a in enumerate(a) if n not in exclude])


def hadamard_all(a: Sequence[_T], nexclude: int = 0) -> Sequence[_T]:
    """Compute the Hadamard product for all combinations of arrays.

    This function computes the Hadamard product for combinations of the input arrays in
    `a`. If `nexclude` is 0, it returns the Hadamard product of all arrays. If
    `nexclude` is greater than 0, it returns the Hadamard products of all combinations
    where exactly `nexclude` arrays are excluded from the product.

    The resulting products are returned in the order defined by C-style lexicographic
    ordering, the same order `itertools.combinations` returns all possible combinations.

    Parameters
    ----------
    a : Sequence[ArrayType]
        Arrays of the same shape that are multiplied.
    nexclude : int, default = 0
        Number of arrays to exclude in each product.

    Returns
    -------
    Sequence[ArrayType]
        Sequence of Hadamard products of all arrays except `nexclude`.

    Notes
    -----
    For reasons of speed, the compatibility of the shapes of the arrays is not checked.
    """
    if nexclude < 0:
        raise ValueError(f"nexclude must be nonnegative, but is {nexclude}")
    return [
        hadamard(a, exclude=ind) for ind in it.combinations(range(len(a)), nexclude)
    ]


def _subspace_error(A: MatrixType, B: MatrixType) -> float:
    """Compute the error between two subspaces.

    This function computes the maximal canonical angle between the two subspaces spanned
    by the columns of the matrices `A` and `B`. Results will only be accurate if these
    columns are orthonormal.

    Parameters
    ----------
    A : MatrixType
        Matrix of which the columns span the first subspace.
    B : MatrixType
        Matrix of which the columns span the second subspace.

    Returns
    -------
    float
        The subspace angle.

    See Also
    --------
    scipy.linalg.subspace_angles

    Notes
    -----
    This function only returns the largest subspace angle, which corresponds with
    ``scipy.linalg.subspace_angles(...)[0]``. In this sense, it is consistent with
    MATLAB's ``subspace`` function.

    This may be slightly less precise than :func:`scipy.linalg.subspace_angles`,
    especially when the angle is large (almost pi/2).

    See :cite:`bjorck1973numerical` for more information.
    """
    if B.shape[1] > A.shape[1]:
        A, B = B, A

    B = B - np.matmul(A, np.matmul(A.T.conj(), B))
    return math.asin(min(1, tlb.norm(B, 2)))


@singledispatch
def noisy(a: Any, snr: float, _rng: np.random.Generator | int | None = None) -> Any:
    """Generate a noisy version of a given array.

    A noisy version of `a` is constructed as ``b = a + n``, where the noise term ``n``
    is generated as ``sigma * randn(a.shape)`` if `a` is real and as
    ``sigma * (randn(a.shape) + randn(a.shape) * 1j)`` if `a` is complex. The scalar
    ``sigma`` is chosen such that ``10 * log10(np.dot(a, a)) / np.dot(n, n)`` is equal
    to `snr`.

    Parameters
    ----------
    a : Any
        Array or list of arrays to which the noise is added.
    snr : float
        Signal-to-noise ratio (in dB) used to determine ``sigma``.
    _rng : numpy.random.Generator | int, optional
        Seed or random number generator used for all random operations in this
        function. If an integer is given, a new generator is created with that seed. If
        a generator is provided, it is used directly. If None, the global generator
        (set via `set_rng`) is used.
    """
    raise NotImplementedError()


@noisy.register
def _noisy_list(
    arrays: list,
    snr: float,
    _rng: np.random.Generator | int | None = None,
) -> list:
    """Apply noisy to each entry in the list."""
    _rng = get_rng(_rng)
    return [noisy(a, snr, _rng=_rng) for a in arrays]


@noisy.register
def _noisy_tuple(
    arrays: tuple,
    snr: float,
    _rng: np.random.Generator | int | None = None,
) -> tuple:
    """Apply noisy to each entry in the tuple."""
    _rng = get_rng(_rng)
    return tuple([noisy(a, snr, _rng=_rng) for a in arrays])


cumsum = it.accumulate


def argmax(a: Iterable[Any]) -> int:
    """Return the index of the maximum value.

    Parameters
    ----------
    a : Iterable
        List/tuple/generator of which the index of the largest element is returned.

    Returns
    -------
    int
        Index of the largest element in `a`.

    Raises
    ------
    ValueError
        If the iterable is empty.
    """
    it = iter(a)
    try:
        best_val = next(it)
    except StopIteration:
        raise ValueError("argmax received an empty iterator")
    best_idx = 0
    for idx, val in enumerate(it, start=1):
        if val > best_val:
            best_val = val
            best_idx = idx
    return best_idx


def argmin(a: Iterable[Any]) -> int:
    """Return the index of the minimum value.

    Parameters
    ----------
    a : Iterable
        List/tuple/generator of which the index of the smallest element is returned.

    Returns
    -------
    int
        Index of the smallest element in `a`.

    Raises
    ------
    ValueError
        If the iterable is empty.
    """
    it = iter(a)
    try:
        best_val = next(it)
    except StopIteration:
        raise ValueError("argmin received an empty iterator")
    best_idx = 0
    for idx, val in enumerate(it, start=1):
        if val < best_val:
            best_val = val
            best_idx = idx
    return best_idx


def argsort(a: Sequence[Any]) -> list[int]:
    """Return a list of indices that would sort the input.

    Parameters
    ----------
    a : Sequence
        List/tuple of which a list of indices should be returned that sorts it.

    Returns
    -------
    list
        List of indices that sorts `a`.
    """
    return sorted(range(len(a)), key=a.__getitem__)


_ScalarType = TypeVar("_ScalarType")


def sumprod(a: Sequence[_ScalarType], b: Sequence[_ScalarType]) -> _ScalarType:
    """Compute the sum of the product of entries.

    Parameters
    ----------
    a : Sequence[_ScalarType]
        First sequence of numbers.
    b : Sequence[_ScalarType]
        Second sequence of numbers.

    Returns
    -------
    _ScalarType
        The sum of the element-wise product of `a` and `b`.
    """
    return cast(_ScalarType, sum(map(operator.mul, a, b)))


@runtime_checkable
class HasRavel(Protocol):
    """Class that implements ravel."""

    def ravel(self) -> ArrayType: ...


@runtime_checkable
class HasData(Protocol):
    """Class having an internal _data field."""

    _data: ArrayType


@runtime_checkable
class Serializable(HasData, HasRavel, Sized, Protocol):
    """Class that can be serialized."""

    ...


SerializableT: TypeAlias = Sequence[HasRavel] | HasData | HasRavel
"""Serializable type."""


def _serialize(z: SerializableT) -> ArrayType:
    if isinstance(z, HasData):
        return z._data
    if isinstance(z, HasRavel):
        return z.ravel()
    elif isinstance(z, Sequence):
        return np.concatenate([z.ravel() for z in z])
    raise ValueError(f"could not serialize {z}")


def is_serializable(z: Any) -> TypeGuard[SerializableT]:
    """Check if an object is serializable."""
    return isinstance(z, HasData | HasRavel) or (
        isinstance(z, Sequence) and all(isinstance(elem, HasRavel) for elem in z)
    )


def get_name(a: Any) -> str:
    """Return the name of the given object."""
    try:
        return a.__name__
    except AttributeError:
        try:
            return a.func.__name__
        except AttributeError:
            try:
                return type(a).__name__
            except AttributeError:
                raise AttributeError("a has no (derived) __name__ attribute")


def pretty_repr(x: Any) -> str:
    """Return more readable repr for specific types."""
    if isinstance(x, ndarray):
        return f"ndarray of shape {x.shape}"
    elif isinstance(x, Sequence):
        if not x:
            return "[]"
        if all([isinstance(f, ndarray) for f in x]):
            return f"[ndarray of shape {x[0].shape},...]"
    return repr(x)


def _mapC2R(u: VectorType) -> VectorType:
    return np.concatenate((u.real, u.imag), axis=0)


def _mapR2C(u: VectorType) -> VectorType:
    n_half = len(u) // 2
    return u[:n_half] + 1j * u[n_half:]


def _mapC2Rmatrix(A: MatrixType) -> MatrixType:
    return np.block([[A.real, -A.imag], [A.imag, A.real]])


@singledispatch
def matrix_like_to_array(x: MatrixLike) -> MatrixType:
    """Transform matrix to a numpy array."""
    raise TypeError(f"Unsupported type: {type(x)}")


@matrix_like_to_array.register
def _matrix_like_to_array_dense(x: np.ndarray) -> MatrixType:
    """Transform matrix to a numpy array."""
    return np.array(x, copy=False)


@matrix_like_to_array.register
def _matrix_like_to_array_sparse(x: sps.coo_matrix) -> MatrixType:
    """Transform matrix to a numpy array."""
    return x.toarray()

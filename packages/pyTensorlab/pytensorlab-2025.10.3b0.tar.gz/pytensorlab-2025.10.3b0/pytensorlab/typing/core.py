"""Custom types for pyTensorlab.

This module contains type aliases for pyTensorlab-specific typing. This includes types
for dense vectors (:class:`VectorType`) and matrices (:class:`MatrixType`), as well as
tensors (:class:`TensorType`), which unifies (NumPy) arrays and pyTensorlab classes for
structured or sparse/incomplete tensors. This module additionally contains protocols for
specifying types with certain characteristics such as sparse matrices
(:class:`SparseMatrix`).
"""

from __future__ import annotations

import numbers
from collections.abc import Sequence
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Protocol,
    TypeAlias,
    TypeGuard,
    TypeVar,
    overload,
    runtime_checkable,
)

import numpy as np
import numpy.typing as npt

from .validators import PositiveInt

if TYPE_CHECKING:
    # Imports to satisfy typing and avoid circular imports.
    from pytensorlab import Tensor
    from pytensorlab.datatypes.tensor import DenseTensor

    # Explicitly specify generic type to avoid mypy complaints. It is known at runtime.
    ArrayType: TypeAlias = np.ndarray[tuple[int, ...], Any]

else:
    ArrayType: TypeAlias = np.ndarray[tuple[int, ...], Any]
    """Dense higher-order array.

    See Also
    --------
    numpy.ndarray
    """

    Tensor = type["Tensor"]
    DenseTensor = type["DenseTensor"]


NumberType: TypeAlias = int | float | complex
"""Scalar number."""

IntArray: TypeAlias = npt.NDArray[np.int_]
"""Array of integers."""

TensorType: TypeAlias = ArrayType | Tensor
"""Higher-order tensor.

This can be a dense array (:class:`numpy.ndarray`) or a structured, sparse or incomplete
tensor.

See Also
--------
numpy.ndarray, .Tensor
"""

DenseTensorType: TypeAlias = ArrayType | DenseTensor
"""Dense tensor."""

MatrixType: TypeAlias = np.ndarray[tuple[int, int], Any]
"""Dense matrix.

The number of dimensions is currently not enforced by type checkers, but can be enforced
at runtime.
"""

VectorType: TypeAlias = np.ndarray[tuple[int], Any]
"""Dense vector.

The number of dimensions is currently not enforced by type checkers, but can be enforced
at runtime.
"""

Array3Type: TypeAlias = np.ndarray[tuple[int, int, int], np.dtype[Any]]
"""Third-order array."""


class ellipsis(Enum):
    """Ellipsis enum for typing."""

    Ellipsis = "..."


Shape: TypeAlias = Sequence[PositiveInt]
"""Shape of an array."""

ShapeLike: TypeAlias = Shape | PositiveInt
"""Shape of an array or int that can be coerced into a shape."""

Axis: TypeAlias = Sequence[int]
"""Sequence of axis integers."""

AxisLike: TypeAlias = Axis | int
"""Integer axis or sequence of integer axes."""


BasicIndex: TypeAlias = (
    int | slice | tuple[int, ...] | tuple[bool, ...] | ellipsis | None
)
"""Index types for basic NumPy indexing."""

NonBasicIndex: TypeAlias = ArrayType | list[int] | list[bool]
"""Index types that do not allow basic NumPy indexing."""

AdvancedIndex: TypeAlias = int | ArrayType | list[int] | list[bool] | ellipsis
"""Index types for advanced NumPy indexing."""

SimpleIndex: TypeAlias = int | tuple[int, ...] | tuple[bool, ...]
"""Index types for simple indices."""

IndexType: TypeAlias = BasicIndex | AdvancedIndex
"""Index types for both basic and advanced NumPy indexing."""

IndexLike: TypeAlias = IndexType | tuple[IndexType, ...]
"""Index types for basic and advanced indexing or type that can be coerced into this."""

NormalizedIndexType: TypeAlias = (
    int | slice | tuple[int, ...] | list[int] | None | IntArray
)
"""Normalized index type."""

NormalizedBasicIndexType: TypeAlias = int | slice | tuple[int, ...] | None
"""Normalized index type for basic NumPy indexing."""

NormalizedAdvancedIndexType: TypeAlias = int | slice | list[int] | None | IntArray
"""Normalized index type for advanced NumPy indexing."""

BOOL_TYPES = (bool, np.bool_)
"""Boolean type."""

_T = TypeVar("_T")


def is_single_type_tuple(a: Any, t: type[_T]) -> TypeGuard[tuple[_T, ...]]:
    """Check if a tuple contains entries of the same (sub)type.

    Parameters
    ----------
    a : Any
        Tuple to be checked.
    t : Type[_T]
        Expected datatype of all tuple elements.

    Returns
    -------
    TypeGuard[tuple[_T, ...]]
        Whether the tuple elements are all of the same (sub)type.
    """
    if not isinstance(a, tuple):
        return False
    return all(isinstance(elem, t) for elem in a)


def is_basic_key(
    key: tuple[NormalizedIndexType, ...],
) -> TypeGuard[tuple[NormalizedBasicIndexType]]:
    """Check if all keys are basic keys.

    Parameters
    ----------
    key : tuple[NormalizedIndexType, ...]
        Keys to be checked.

    Returns
    -------
    TypeGuard[tuple[NormalizedBasicIndexType]]
        Whether all keys are basic keys.

    See Also
    --------
    .getitem
    """
    for k in key:
        if k is None or isinstance(k, slice) or isint(k):
            continue
        if is_single_type_tuple(k, int) or is_single_type_tuple(k, bool):
            continue
        return False
    return True


T = TypeVar("T")


@runtime_checkable
class TensorLike(Protocol):
    """Prototype for objects behaving like tensors."""

    @property
    def shape(self) -> tuple[int, ...]: ...

    @property
    def ndim(self) -> int: ...

    @property
    def size(self) -> int: ...

    def transpose(self: T, axes: AxisLike | None = None) -> T: ...

    def __neg__(self: T) -> T: ...

    def __getitem__(self, indices: IndexType) -> TensorType: ...


class SupportsArrayFromShape(Protocol):
    """Return array of given shape."""

    def __call__(self, shape: ShapeLike, /) -> ArrayType: ...


class SupportsArrayFromShapeLike(Protocol):
    """Return array of given type and shape."""

    def __call__(
        self, array: ArrayType, /, *, shape: ShapeLike | None = None
    ) -> ArrayType: ...


class SupportsMtkrprod(Protocol):
    """Define matricized tensor times Khatri-Rao product operation."""

    @overload
    def __call__(
        self, T: TensorType, factors: Sequence[MatrixType]
    ) -> Sequence[MatrixType]: ...

    @overload
    def __call__(
        self, T: TensorType, factors: Sequence[MatrixType], axis: int
    ) -> MatrixType: ...


def isint(i: Any) -> bool:
    """Check if the object is an integer.

    Parameters
    ----------
    i : Any
        Object to be checked.

    Returns
    -------
    bool
        Whether the given object is an integer.
    """
    return isinstance(i, numbers.Integral | np.integer)


def isbool(b: Any) -> bool:
    """Check if the object is a boolean.

    Parameters
    ----------
    b : Any
        Object to be checked.

    Returns
    -------
    bool
        Whether the given object is a boolean.
    """
    return isinstance(b, BOOL_TYPES)


Sequenceable: TypeAlias = Sequence[T] | T
"""Type that can be made into a Sequence."""


class SparseMatrix(Protocol):
    """Typing template for a sparse matrix."""

    ndim: int

    def getnnz(self, axis: int | None = None) -> int | ArrayType: ...

    def toarray(
        self,
        order: str | None = None,
        out: ArrayType | None = None,
        sparse_ok: bool = False,
    ) -> ArrayType: ...

    def transpose(
        self, axes: tuple[int, int] | None = None, copy: bool = False
    ) -> SparseMatrix: ...

    @property
    def T(self) -> SparseMatrix: ...

    def conj(self) -> SparseMatrix: ...

    def copy(self) -> SparseMatrix: ...

    def reshape(
        self, shape: tuple[int, int], order: str | None = None
    ) -> SparseMatrix: ...

    def dot(self, other: MatrixLike) -> MatrixLike: ...

    def tocoo(self, copy: bool = False) -> coo_matrix: ...

    @property
    def nnz(self) -> int: ...

    @property
    def shape(self) -> tuple[int, int]: ...

    @overload
    def __matmul__(self, other: ArrayType) -> ArrayType:
        pass

    @overload
    def __matmul__(self, other: SparseMatrix) -> SparseMatrix:
        pass


class coo_matrix(SparseMatrix, Protocol):
    """Typing template for a COO matrix."""

    data: ArrayType
    row: ArrayType
    col: ArrayType

    def __init__(
        self,
        arg1: tuple[ArrayType, tuple[ArrayType, ArrayType]],
        shape: Axis | None = None,
    ): ...


MatrixLike: TypeAlias = MatrixType | SparseMatrix

MinfOptimizationMethod: TypeAlias = (
    Literal["l-bfgs-b"] | Literal["cg"] | Literal["bfgs"]
)

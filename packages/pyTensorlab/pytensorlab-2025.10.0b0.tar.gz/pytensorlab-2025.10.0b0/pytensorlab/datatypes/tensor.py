"""Definition of the base class which represents special types of tensors.

Each special type of tensor is represented by a specific subclass of `Tensor`. Such
special types encompass tensor decompositions and sparse or incomplete tensors. These
types are divided into two subtypes, namely `DenseTensor` and `PartialTensor`.

`DenseTensor` consists of tensor subtypes for which each element is defined. Tensor
decompositions belong to this subtype, as the value of each element can be computed
using the parameters of the decomposition.

`PartialTensor` consist of tensor types for which only a limited number of its elements
are defined. The value of undefined elements is equal to a default value. Sparse tensors
(default value 0) and incomplete tensors (default value nan) belong to this subtype.

All functions in the core module can be applied to subtypes of `Tensor`. Additionally,
they are compatible with many NumPy functions.

See Also
--------
.PartialTensor
"""

import itertools as it
import math
import sys
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator, Iterator, MutableMapping, Sequence
from typing import (
    Any,
    Literal,
    NoReturn,
    Protocol,
    TypeGuard,
    TypeVar,
    cast,
    overload,
)

import numpy as np
from numpy.typing import ArrayLike, DTypeLike

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


from pytensorlab.typing import (
    ArrayType,
    Axis,
    AxisLike,
    IndexLike,
    MatrixLike,
    NormalizedAdvancedIndexType,
    NormalizedBasicIndexType,
    NormalizedIndexType,
    Shape,
    TensorType,
    VectorType,
    ellipsis,
    is_basic_key,
)
from pytensorlab.typing.core import ShapeLike

from ..util.indextricks import (
    compute_indexed_shape,
    isadvanced,
    isbasic,
    normalize_index,
)
from .core import frob, getitem, matricize, vectorize

HANDLED_FUNCTIONS: MutableMapping[Callable[..., Any], Callable[..., Any]] = {}


_OutT = TypeVar("_OutT")
SelfT = TypeVar("SelfT", bound="Tensor")


class _HasData(Protocol):
    _data: ArrayType


def _has_data(self: Any) -> TypeGuard[_HasData]:
    return hasattr(self, "_data")


class Tensor(ABC):
    """Base class of special tensor types.

    A `Tensor` is a special type of tensor that also functions similarly to a
    :class:`numpy.ndarray` from NumPy. It has similar properties, such as `shape` and
    `ndim`, and is compatible with NumPy functions, such as :func:`numpy.transpose`,
    :func:`numpy.reshape`, :func:`numpy.take`...

    Parameters
    ----------
    shape : Shape
        The dimensions of the tensor.

    Attributes
    ----------
    flags : dict[str, bool]
        Information about the stored data of the tensor.
    """

    _REPR_MODE: Literal["str"] | Literal["repr"] = "str"
    """Determine the output of __repr__.
     
    For the convenience of the user, a more readable string representation can be
    returned by __repr__ instead of the more complicated representation allowing the
    object to be reconstructed. Valid values are "str" and "repr".
    """

    def __init__(self, shape: Shape):
        self._shape = shape
        self.flags: dict[str, bool] = {"WRITEABLE": True}

    def setflags(self, write: bool) -> None:
        """Set tensor flag WRITEABLE.

        This flag determines whether or not the data of a tensor can be written to.

        Parameters
        ----------
        write : bool
            Describes whether or not the data of the tensor can be written to.
        """
        self.flags["WRITEABLE"] = write
        if _has_data(self):
            self._data.setflags(write=write)

    @property
    def shape(self) -> Shape:
        """Tuple of tensor dimensions.

        Returns
        -------
        Shape
            Dimensions of the tensor.
        """
        return self._shape

    @property
    def dtype(self) -> np.dtype[Any]:
        """Type of the data contained in the tensor.

        Returns
        -------
        numpy.dtype[Any]
            The datatype of the tensor elements.
        """
        raise NotImplementedError()

    @property
    def size(self) -> int:
        """Number of elements in the tensor.

        Returns
        -------
        int
            The number of elements in the tensor.
        """
        return math.prod(self.shape)

    @property
    def ndim(self) -> int:
        """Number of tensor dimensions or order.

        Returns
        -------
        int
            The number of dimensions of the tensor.
        """
        return len(self._shape)

    @abstractmethod
    def transpose(self, axes: Axis | None = None) -> Self:
        """Return a tensor with permuted axes.

        Parameters
        ----------
        axes : Axis, optional
            If specified, it must be a permutation of ``range(self.ndim)``. The i-th
            axis of the returned tensor will correspond to the axis ``axes[i]`` of the
            input tensor. Negative indexing of these axes is allowed. If `axes` does not
            include all values in ``range(self.ndim)``, the remaining axes are appended
            in decreasing order.

        Returns
        -------
        Self
            A new tensor with permuted axes.
        """
        raise NotImplementedError()

    def matricize(
        self: Self, row: AxisLike = 0, col: AxisLike | None = None
    ) -> MatrixLike:
        """Reshape the tensor into a matrix.

        Refer to :func:`.matricize` for full documentation.
        """
        return matricize(self, row, col)

    def vectorize(self, axes: AxisLike | None = None) -> VectorType:
        """Reshape the tensor into a vector.

        Refer to :func:`.vectorize` for full documentation.
        """
        return vectorize(self, axes)

    def __array_function__(
        self,
        func: Callable[..., _OutT],
        types: Sequence[type[Self]],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> _OutT:
        if func not in HANDLED_FUNCTIONS:
            return NotImplemented
        # Note: this allows subclasses that don't override
        # __array_function__ to handle Tensor objects
        if not all(issubclass(t, self.__class__) for t in types):
            return NotImplemented
        return HANDLED_FUNCTIONS[func](*args, **kwargs)

    def __getitem__(self, key: IndexLike) -> Self | ArrayType | float:
        normalized_key = normalize_index(key, self.shape)

        if is_basic_key(normalized_key):
            return self._getitem_sliced(normalized_key)
        else:
            normalized_key = cast(tuple[NormalizedIndexType, ...], normalized_key)
            return self._getitem_indexed(normalized_key)

    def _getitem_indexed(self, key: Sequence[NormalizedIndexType]) -> float | ArrayType:
        # Check if advanced indices should be moved to first position
        perm2first = sum([k for k, _ in it.groupby(key, isadvanced)]) > 1
        # Compute new shape
        shape, broadcast_shape = compute_indexed_shape(key, perm2first)

        # perform slice operations
        def replace_advanced(key) -> Generator[NormalizedBasicIndexType, None, None]:
            for k in key:
                if k is None:
                    continue
                yield k if isbasic(k) else slice(None)

        T = self._getitem_sliced(tuple(replace_advanced(key)))
        T = cast(Tensor, T)

        # Compute new (broadcasted) indices
        def replace_basic(key) -> Generator[NormalizedAdvancedIndexType, None, None]:
            for k in key:
                if not isbasic(k):
                    yield np.broadcast_to(k, broadcast_shape).ravel()
                elif isinstance(k, slice | tuple):
                    yield slice(None)

        newkey = tuple(replace_basic(key))

        # Correct order of dimensions if not consecutive
        if perm2first:
            axes = tuple(i for i, k in enumerate(newkey) if isadvanced(k))
            axes += tuple(i for i, k in enumerate(newkey) if not isadvanced(k))
            T = T.transpose(axes)
            newkey = tuple(newkey[i] for i in axes)

        # create new polyadic tensor and convert to tensor
        return np.reshape(T._entry(newkey), shape)

    @abstractmethod
    def _entry(self, indices: Sequence[NormalizedAdvancedIndexType]) -> ArrayType:
        raise NotImplementedError()

    @abstractmethod
    def _getitem_sliced(self, key: Sequence[NormalizedBasicIndexType]) -> Self | float:
        raise NotImplementedError()

    def __setitem__(self, key: IndexLike, value: Any) -> NoReturn:
        raise NotImplementedError("setting values is not supported")

    @abstractmethod
    def __array__(self, dtype: DTypeLike = None, copy: bool | None = None) -> ArrayType:
        raise NotImplementedError("converting this tensor to an array is not supported")

    def ravel(self, *args: Any, **kwargs: Any) -> VectorType:
        """Return a flattened version of this tensor.

        Parameters
        ----------
        *args
            Options to be passed to :func:`numpy.ravel`.
        **kwargs
            Options to be passed to :func:`numpy.ravel`.

        Returns
        -------
        VectorType
            Flattened version of this tensor.

        Notes
        -----
        This function is similar to :func:`.tens2vec`, but without the ability to
        permute the axes of the tensor first.

        See Also
        --------
        numpy.ravel, .tens2vec
        """
        return np.ravel(self, *args, **kwargs)

    def __neg__(self) -> Self | NoReturn:
        raise NotImplementedError

    @abstractmethod
    def copy(self) -> Self:
        """Return a copy of this tensor.

        The data arrays of the new tensor are array copies of the data arrays of this
        tensor.

        Returns
        -------
        Self
            A copy of this tensor.
        """
        raise NotImplementedError()

    @overload
    def take(
        self,
        indices: ArrayLike,
        axis: None,
        mode: Literal["raise"] = "raise",
        **ignored_kwargs: Any,
    ) -> float | ArrayType: ...

    @overload
    def take(
        self,
        indices: ArrayLike,
        axis: int,
        mode: Literal["raise"] = "raise",
        **ignored_kwargs: Any,
    ) -> Self: ...

    def take(
        self: Self,
        indices: ArrayLike,
        axis: int | None = None,
        mode: Literal["raise"] = "raise",
        **ignored_kwargs: Any,
    ) -> Self | float | ArrayType:
        """Take elements from a tensor along an axis.

        Parameters
        ----------
        indices : ArrayLike
            The indices of the elements to extract.
        axis : int, optional
            The axis over which to select elements. By default, the vectorized tensor is
            used.
        mode : "raise", default = "raise"
            Specifies how out-of-bounds indices will behave. Only "raise" can be used.
        **ignored_kwargs
            Unused.

        Returns
        -------
        Union[Self, float, ArrayType]
            Tensor with the selected `indices` along `axis`.

        See Also
        --------
        numpy.take
        """
        if mode != "raise":
            raise ValueError(f"mode {mode} is not supported; only 'raise' can be used")
        key: tuple[VectorType | slice | ellipsis, ...]
        if axis is None:
            key = np.unravel_index(np.asarray(indices) % self.size, self.shape)
        else:
            if not isinstance(indices, Sequence):
                indices = np.asarray(indices)
            axis += self.ndim if axis < 0 else 0
            key = (slice(None),) * axis + (indices, ...)  # type:ignore
        return self[key]

    @abstractmethod
    def iscomplex(self) -> bool:
        """Check whether this tensor has any complex elements.

        Returns
        -------
        bool
            Indicates whether the tensor has any complex elements.
        """
        raise NotImplementedError()

    @abstractmethod
    def conj(self) -> Self:
        """Return the complex conjugate of this tensor.

        If the tensor does not contain any complex values, the tensor itself is
        returned. Otherwise, a new tensor is returned which contains the complex
        conjugate data of this tensor.

        Returns
        -------
        Self
            The complex conjugate of the tensor.
        """
        raise NotImplementedError()

    def __iter__(self) -> Iterator[Self]:
        # Not needed per se, but mypy work.
        index = 0
        while True:
            try:
                yield self[index]  # type:ignore
            except IndexError:
                return
            index += 1

    def reshape(self, shape: ShapeLike) -> Self:
        raise NotImplementedError()


class DenseTensor(Tensor):
    """Tensor for which a value can be computed for each element.

    Notes
    -----
    This is essentially the opposite of `PartialTensor`, for which only a limited number
    of elements have a defined value.
    """

    ...


@getitem.register
def _getitem_tensor(T: Tensor, key: IndexLike) -> TensorType | float:
    return T[key]


def implements(numpy_function: Callable) -> Callable:
    """Register an `__array_function__` implementation for `Tensor` objects.

    Parameters
    ----------
    numpy_function : Callable
        Function to be registered.

    Returns
    -------
    Callable
        Function that operates on `Tensor` objects.
    """

    def decorator(func):
        HANDLED_FUNCTIONS[numpy_function] = func
        return func

    return decorator


@implements(np.take)
def _take(
    a: SelfT,
    indices: ArrayLike,
    axis: int | None = None,
    mode: Literal["raise"] = "raise",
    **ignored_kwargs,
) -> SelfT | float | ArrayType:
    return a.take(indices, axis, mode)


@implements(np.nanmin)
def _nanmin(a: Tensor, *args, **kwargs):
    return np.nanmin(np.asarray(a), *args, **kwargs)


@implements(np.nanmax)
def _nanmax(a: Tensor, *args, **kwargs):
    return np.nanmax(np.asarray(a), *args, **kwargs)


@implements(np.ravel)
def _ravel(a: Tensor, *args, **kwargs):
    return np.ravel(np.asarray(a), *args, **kwargs)


@implements(np.iscomplexobj)
def _iscomplexobj(a: Tensor):
    return a.iscomplex()


@implements(np.transpose)
def _transpose(a: Tensor, axes: Axis | None = None) -> Tensor:
    return a.transpose(axes)


@implements(np.shape)
def _shape(a: Tensor) -> Shape:
    return a.shape


@implements(np.size)
def _size(a: Tensor, axis: int | None = None) -> int:
    if axis is None:
        return a.size
    else:
        return a.shape[axis]


@implements(np.ndim)
def _ndim(a: Tensor) -> int:
    return a.ndim


@implements(np.linalg.norm)
def _norm(
    a: Tensor,
    ord: float | Literal["fro"] | None = None,
    axis: int | None = None,
    keepdims: bool = False,
) -> float:
    if (ord is None or ord == "fro") and axis is None and not keepdims:
        return frob(a)
    else:
        raise NotImplementedError(
            "only the computation of the Frobenius norm of tensors is supported"
        )

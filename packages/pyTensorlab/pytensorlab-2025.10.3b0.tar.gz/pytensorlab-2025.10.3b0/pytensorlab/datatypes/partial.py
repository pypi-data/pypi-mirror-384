"""Sparse and incomplete tensor formats and implementation of core operations.

This module provides the classes :class:`.SparseTensor` and :class:`.IncompleteTensor`
for representing sparse and incomplete tensors, respectively. Additionally, it provides
the implementations of the core operations for these tensor formats.

Notes
-----
An incomplete tensor can be created in a similar way to a sparse tensor, namely by
providing the values and indices of its known elements. See :class:`.SparseTensor` and
:class:`.IncompleteTensor` for more ways to construct sparse and incomplete tensors.

Examples
--------
A sparse tensor can be created by providing the values of its nonzero elements, the
corresponding indices and the shape of the tensor:

>>> import pytensorlab as tl
>>> import numpy as np
>>> indices = (np.array([0, 1]), np.array([2, 3]))
>>> data = np.array([1, 2])
>>> T = tl.SparseTensor(data, indices, (5, 5))

Alternatively, a sparse tensor can be created by providing flat indices instead of
(multi-)indices:

>>> flat_indices = np.array([2, 8])
>>> T = tl.SparseTensor(data, flat_indices=flat_indices, shape=(5, 5))
"""

import math
import sys
from abc import abstractmethod
from collections.abc import Generator, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    TypeAlias,
    cast,
)

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

import numpy as np
import numpy.typing as npt
from numpy.typing import ArrayLike, DTypeLike
from scipy.sparse import coo_matrix

import pytensorlab.backends.numpy as tlb
from pytensorlab.typing import MatrixType, NonnegativeInt, VectorType
from pytensorlab.typing.core import SupportsArrayFromShape

from ..random._utils import _random, _random_like
from ..random.rng import get_rng
from ..typing.core import (
    ArrayType,
    Axis,
    IntArray,
    NormalizedAdvancedIndexType,
    NormalizedBasicIndexType,
    NumberType,
    Shape,
    ShapeLike,
    isint,
)
from ..util.indextricks import (
    _complement_indices,
    _ensure_positive_advanced_index,
    _ensure_positive_basic_index,
    _ensure_sequence,
    findfirst,
    normalize_axes,
)
from ..util.utils import argsort, noisy
from .core import (
    _mat2tens,
    _mtkronprod_all,
    _mtkronprod_single,
    _mtkrprod_all,
    _mtkrprod_single,
    _tens2mat,
    _tmprod,
    _tvprod,
    frob,
    tens2mat,
    tmprod,
)
from .ndarray import _frob_array
from .tensor import Tensor

if TYPE_CHECKING:
    from pytensorlab.typing.core import SparseMatrix
else:
    from scipy.sparse import spmatrix

    SparseMatrix: TypeAlias = spmatrix


class PartialTensor(Tensor):
    """Represent a tensor by a limited number of elements in the coordinate format.

    A `PartialTensor` represents a `Tensor` by only storing the values of the specified
    elements and their corresponding indices and flat indices. Examples of a
    `PartialTensor` are a `SparseTensor` and an `IncompleteTensor`. In a `SparseTensor`,
    the nonzero elements are specified using their values and indices. The remaining
    elements are assumed to be zero. Similarly, in an `IncompleteTensor`, the known
    elements are specified and the remaining elements are assumed to be unknown.

    Parameters
    ----------
    data : ArrayLike
        Values of the stored elements.
    indices : tuple[ArrayLike, ...], optional
        Indices of the stored elements stored as `ndim` vectors. Either `indices` or
        `flat_indices` must be provided.
    shape: ShapeLike, optional
        Shape of the tensor. If `shape` is not provided when `indices` are provided,
        the shape of the tensor will be inferred from `indices`. When only
        `flat_indices` are provided, `shape` must also be provided.
    flat_indices : ArrayLike, optional
        Flat, or linear, indices of the stored elements. Either `indices` or
        `flat_indices` must be provided. If both `indices` and `flat_indices` are
        provided, only the former will be used.
    _check_unique_ind : bool, default = True
        Check whether `indices` correspond to unique tensor elements. If they are
        guaranteed to be unique, this option can be set to False to save time.
    _check_bounds : bool, default = True
        Perform bounds check on `indices` if True.
    """

    def __init__(
        self,
        data: ArrayLike,
        indices: tuple[ArrayLike, ...] | None = None,
        shape: ShapeLike | None = None,
        flat_indices: ArrayLike | None = None,
        _check_unique_ind: bool = True,
        _check_bounds: bool = True,
        _sorted_indices: bool = False,
    ):
        """Represent a tensor by a limited number of elements in the coordinate format.

        A `PartialTensor` represents a `Tensor` by only storing the values of the
        specified elements and their corresponding indices and flat indices. Examples of
        a `PartialTensor` are a `SparseTensor` or an `IncompleteTensor`. In a
        `SparseTensor`, the nonzero elements are specified using their values and
        indices. The remaining elements are assumed to be zero. Similarly, in an
        `IncompleteTensor`, the known elements are specified and the remaining elements
        are assumed to be unknown.

        Parameters
        ----------
        data : ArrayLike
            Values of the stored elements.
        indices : tuple[ArrayLike, ...], optional
            Indices of the stored elements stored as `ndim` vectors. Either `indices` or
            `flat_indices` must be provided.
        shape: ShapeLike, optional
            Shape of the tensor. If `shape` is not provided when `indices` are provided,
            the shape of the tensor will be inferred from `indices`. When only
            `flat_indices` are provided, `shape` must also be provided.
        flat_indices : ArrayLike, optional
            Flat, or linear, indices of the stored elements. Either `indices` or
            `flat_indices` must be provided. If both `indices` and `flat_indices` are
            provided, only the former will be used.
        _check_unique_ind : bool, default = True
            Check whether `indices` correspond to unique tensor elements. If they are
            guaranteed to be unique, this option can be set to False to save time.
        _check_bounds : bool, default = True
            Perform bounds check on `indices` if True.
        _sorted_indices : bool = False
            Whether the provided indices are sorted. If False, the indices and data
            will be sorted. Note that providing unsorted indices and setting
            `_sorted_indices` to True might result in incorrect results for several
            methods.

        Raises
        ------
        ValueError
            If neither `indices` nor `flat_indices` are provided.
        ValueError
            If `shape` is not provided when only `flat_indices` are provided.
        ValueError
            If an element is specified more than once.

        See Also
        --------
        SparseTensor, IncompleteTensor
        """
        # Check data.
        if not isinstance(data, np.ndarray):
            data = np.asarray(data)
        if data.ndim > 1:
            raise ValueError(f"data is a {data.ndim}D array instead of a vector")

        shape = _ensure_sequence(shape) if shape is not None else None

        if indices is not None:
            if any(not isinstance(sub, np.ndarray) for sub in indices):
                indices = tuple(np.asarray(sub) for sub in indices)
            indices = cast(tuple[VectorType, ...], indices)
            if any(sub.ndim > 1 for sub in indices):
                raise ValueError("indices should be a sequence of vectors")
            if any(sub.shape[0] != data.shape[0] for sub in indices):
                raise ValueError(
                    "each vector in indices should contain a number of elements equal "
                    "to the number of elements in data"
                )

            # Check shape.
            if shape is not None:
                if len(indices) != len(shape):
                    raise ValueError(
                        f"the number of elements in shape (={len(shape)}) must equal "
                        f"the number of vectors in indices (={len(indices)})"
                    )

                # Check for negative indices.
                if _check_bounds:
                    min_ind = (np.min(sub) if len(sub) > 0 else 0 for sub in indices)
                    negative_indices = (mi < 0 for mi in min_ind)
                    if any(negative_indices):
                        indices = tuple(
                            np.where(i < 0, i + s, i) for i, s in zip(indices, shape)
                        )
                        indices = cast(tuple[VectorType, ...], indices)

            # Compute shape if not given.
            else:
                if _check_bounds:
                    min_ind = (np.min(sub) if len(sub) > 0 else 0 for sub in indices)
                    negative_indices = (mi < 0 for mi in min_ind)
                    if any(negative_indices):
                        raise ValueError(
                            "shape must be provided in case indices contains negative "
                            "values"
                        )
                max_ind = (np.max(sub) if len(sub) > 0 else 0 for sub in indices)
                shape = tuple(i + 1 for i in max_ind)

            # Compute flat indices and check bounds.
            if flat_indices is None or _check_bounds:
                try:
                    flat_indices = np.ravel_multi_index(indices, shape)
                except ValueError as exception:
                    # Check too large indices.
                    max_ind_list = [
                        np.max(sub) if len(sub) > 0 else 0 for sub in indices
                    ]
                    out_of_bounds_indices = tuple(
                        i >= s for i, s in zip(max_ind_list, shape)
                    )
                    if any(out_of_bounds_indices):
                        axis = findfirst(out_of_bounds_indices)
                        raise ValueError(
                            f"index {max_ind_list[axis]} in axis {axis} exceeds "
                            f"dimension {shape[axis]}"
                        )

                    # Check too small indices.
                    min_ind_list = [
                        np.min(sub) if len(sub) > 0 else 0 for sub in indices
                    ]
                    negative_indices_list = [mi < 0 for mi in min_ind_list]
                    if any(negative_indices_list):
                        axis = findfirst(negative_indices_list)
                        raise ValueError(
                            f"index {min_ind_list[axis] - shape[axis]} in axis {axis} "
                            f"smaller than dimension {-shape[axis]}"
                        )

                    # Should never arrive here.
                    raise exception

            if not _sorted_indices:
                if not isinstance(flat_indices, np.ndarray):
                    flat_indices = np.asarray(flat_indices)
                order = np.argsort(flat_indices)
                flat_indices = flat_indices[order]
                indices = tuple(sub[order] for sub in indices)
                data = data[order]

        elif flat_indices is not None:
            if not isinstance(flat_indices, np.ndarray):
                flat_indices = np.asarray(flat_indices)
            if flat_indices.ndim > 1:
                raise ValueError("flat_indices should be a vector")
            if flat_indices.shape[0] != data.shape[0]:
                raise ValueError(
                    "flat_indices should contain a number of elements equal to the "
                    "number of elements in data"
                )

            # Check shape.
            if not shape:
                raise ValueError(
                    "shape must be provided in case flat_indices is provided"
                )
            if len(flat_indices) > 0 and np.max(flat_indices) > math.prod(shape):
                raise ValueError(
                    "flat index can not exceed the number of elements in the tensor"
                )

            if not _sorted_indices:
                order = np.argsort(flat_indices)
                flat_indices = flat_indices[order]
                data = data[order]
            indices = np.unravel_index(flat_indices, shape)

        else:
            raise ValueError("either indices or flat_indices should be provided")

        # To satisfy type checking.
        assert indices is not None and flat_indices is not None
        flat_indices = cast(VectorType, flat_indices)

        # Check for elements that are specified multiple times.
        if _check_unique_ind:
            if len(set(flat_indices)) < len(flat_indices):
                raise ValueError("an element can not be specified more than once")

        super().__init__(tuple(shape))
        self._data: VectorType = data
        self._indices: tuple[VectorType, ...] = cast(tuple[VectorType, ...], indices)
        self._flat_indices: VectorType = flat_indices

    @classmethod
    @abstractmethod
    def from_dense(cls, T: ArrayType) -> Self:
        """Create a `PartialTensor` from a dense tensor.

        Parameters
        ----------
        T : ArrayType
            Dense tensor to create a `PartialTensor` from.

        Returns
        -------
        PartialTensor
            The `PartialTensor` corresponding to `T`.
        """

    @classmethod
    def random(
        cls,
        shape: Shape,
        data_size: NonnegativeInt,
        /,
        real: SupportsArrayFromShape | None = None,
        imag: SupportsArrayFromShape | bool | None = None,
    ) -> Self:
        """Generate a `PartialTensor` with random elements.

        By default, real elements are generated, drawn from a uniform distribution.
        The distribution can be changed by providing an alternative random number
        generating function to `real`. Complex elements can be generated by
        providing a random number generating function to `imag`.

        Parameters
        ----------
        shape : Shape
            The shape of the tensor.
        data_size : NonnegativeInt
            The number of stored elements.
        real : SupportsArrayFromShape, default = tl.get_rng().random
            Random number generating function for generating the real part of the
            factors.
        imag : SupportsArrayFromShape | bool, optional
            If this argument is provided, complex elements are generated. If `imag` is
            True, the function provided to `real` is also used to generate the imaginary
            part of the elements. If a random number generating function is provided,
            this function is used for generating the imaginary part of the elements.

        Returns
        -------
        Self
            A `.PartialTensor` with random elements.

        See Also
        --------
        randn, rand, random_like, randn_like, rand_like
        """
        data = _random(data_size, real, imag)
        flat_indices = get_rng().choice(math.prod(shape), data_size, replace=False)
        return cls(data, shape=shape, flat_indices=flat_indices)

    @classmethod
    def random_like(
        cls,
        array: ArrayLike,
        data_size: NonnegativeInt,
        /,
        real: SupportsArrayFromShape | None = None,
        imag: SupportsArrayFromShape | bool | None = None,
    ) -> Self:
        """Generate a `PartialTensor` with random elements.

        By default, real elements are generated, drawn from a uniform distribution.
        The distribution can be changed by providing an alternative random number
        generating function to `real`. Complex elements can be generated by
        providing a random number generating function to `imag`.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        data_size : NonnegativeInt
            The number of stored elements.
        real : SupportsArrayFromShape, default = tl.get_rng().random
            Random number generating function for generating the real part of the
            factors.
        imag : SupportsArrayFromShape | bool, optional
            If this argument is provided, complex elements are generated. If `imag` is
            True, the function provided to `real` is also used to generate the imaginary
            part of the elements. If a random number generating function is provided,
            this function is used for generating the imaginary part of the elements.

        Returns
        -------
        Self
            A partial tensor with random elements.
        """
        shape = np.shape(array)
        data = _random_like(array, data_size, real, imag)
        flat_indices = get_rng().choice(math.prod(shape), data_size, replace=False)
        return cls(data, shape=shape, flat_indices=flat_indices)

    @classmethod
    def randn(
        cls,
        shape: Shape,
        data_size: NonnegativeInt,
        /,
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random elements, drawn from a standard normal distribution.

        Parameters
        ----------
        shape : Shape
            The shape of the tensor.
        data_size : NonnegativeInt
            The number of stored elements.
        imag : bool, optional
            If True, the elements are complex, with the imaginary part also drawn from
            a standard normal distribution.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        Self
            A partial tensor with random elements, drawn from a standard normal
            distribution.
        """
        _rng = get_rng(_rng)
        return cls.random(shape, data_size, real=_rng.standard_normal, imag=imag)

    @classmethod
    def randn_like(
        cls,
        array: ArrayLike,
        data_size: NonnegativeInt,
        /,
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random elements, drawn from a standard normal distribution.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        data_size : NonnegativeInt
            The number of stored elements.
        imag : bool, optional
            If True, the elements are complex, with the imaginary part also drawn from
            a standard normal distribution.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        Self
            A partial tensor with random elements, drawn from a standard normal
            distribution.
        """
        _rng = get_rng(_rng)
        return cls.random_like(array, data_size, real=_rng.standard_normal, imag=imag)

    @classmethod
    def rand(
        cls,
        shape: Shape,
        data_size: NonnegativeInt,
        /,
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random elements, drawn from a uniform distribution.

        Parameters
        ----------
        shape : Shape
            The shape of the tensor.
        data_size : NonnegativeInt
            The number of stored elements.
        imag : bool, optional
            If True, the elements are complex, with the imaginary part also drawn from
            a uniform distribution.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        Self
            A partial tensor with random elements, drawn from a uniform distribution.
        """
        _rng = get_rng(_rng)
        return cls.random(shape, data_size, real=_rng.random, imag=imag)

    @classmethod
    def rand_like(
        cls,
        array: ArrayLike,
        data_size: NonnegativeInt,
        /,
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random elements, drawn from a uniform distribution.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        data_size : NonnegativeInt
            The number of stored elements.
        imag : bool, optional
            If True, the elements are complex, with the imaginary part also drawn from
            a uniform distribution.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        Self
            A partial tensor with random elements, drawn from a uniform distribution.
        """
        _rng = get_rng(_rng)
        return cls.random_like(array, data_size, real=_rng.random, imag=imag)

    def __array__(self, dtype: DTypeLike = None, copy: bool | None = None) -> ArrayType:
        T = self._empty_array(self.shape, dtype=self._data.dtype)
        T[self._indices] = self._data
        return T

    @abstractmethod
    def _empty_array(
        self, shape: ShapeLike, dtype: npt.DTypeLike | None = None
    ) -> ArrayType:
        """Create an empty `PartialTensor`."""
        ...

    def _entry(self, indices: Sequence[NormalizedAdvancedIndexType]) -> ArrayType:
        # Convert lists to numpy arrays
        indices = tuple(np.array(k) if isinstance(k, list) else k for k in indices)

        # Repeat the indices in key to obtain the indices of all indexed elements. Note
        # that integers and Nones in the key have already been handled in tensor.
        # Therefore, key now consists only of numpy arrays and slice(None).
        arrays: list[ArrayType] = [k for k in indices if isinstance(k, np.ndarray)]
        array_axes = [i for i, k in enumerate(indices) if isinstance(k, np.ndarray)]

        def _repetition_shape(
            shape: Shape, array_axes: list[int]
        ) -> Generator[int, None, None]:
            for i, s in enumerate(shape):
                if i == array_axes[0]:
                    yield len(arrays[0])
                elif i in array_axes[1:]:
                    yield 1
                else:
                    yield s

        repetition_shape = tuple(_repetition_shape(self.shape, array_axes))

        def _repeat_indices(
            key: Sequence[NormalizedAdvancedIndexType],
        ) -> Generator[VectorType, None, None]:
            for i, k in enumerate(key):
                ind = k if isinstance(k, np.ndarray) else np.arange(repetition_shape[i])
                axis = i if i not in array_axes[1:] else array_axes[0]
                ind = np.repeat(ind, math.prod(repetition_shape[axis + 1 :]))
                yield np.tile(ind, math.prod(repetition_shape[:axis]))

        repeated_indices = tuple(
            _repeat_indices(_ensure_positive_advanced_index(indices, self.shape))
        )

        # Compute the corresponding flat indices from the repeated indices and match
        # them with flat_indices in self.
        flat_indices = np.ravel_multi_index(repeated_indices, self.shape)
        selection = np.searchsorted(self._flat_indices, flat_indices)
        present_indices = (
            self._flat_indices[np.minimum(selection, len(self._flat_indices) - 1)]
            == flat_indices
        )
        selection = selection[present_indices]
        result = self._empty_array(len(flat_indices), dtype=self.dtype)
        result[present_indices] = self._data[selection]
        return result

    def _getitem_sliced(self, key: Sequence[NormalizedBasicIndexType]) -> Self | float:
        key = _ensure_positive_basic_index(key, self.shape)
        if all(isint(k) for k in key):
            tmp = self._entry(tuple(np.array([k]) for k in key))
            return tmp[0]
        int_axes = [i for i, k in enumerate(key) if isint(k)]

        def _convert_to_array(
            key: tuple[NormalizedBasicIndexType, ...], shape: Shape
        ) -> Generator[ArrayType | None, None, None]:
            for k, s in zip(key, shape):
                if k is None:
                    yield None
                elif isinstance(k, slice):
                    yield np.array(range(*k.indices(s)))
                elif isint(k):
                    # Separate if needed since np.array yields a 0-D array for integers
                    yield np.array([k])
                else:
                    yield np.array(k)

        # Convert key to tuple of numpy arrays and Nones
        shape_iter = iter(self.shape)
        shape = tuple(1 if k is None else next(shape_iter) for k in key)
        array_key = tuple(_convert_to_array(key, shape))

        # Add zeros to indices for Nones in key
        indices_iter = iter(self.indices)
        indices: MatrixType = np.stack(
            [
                (
                    np.zeros(len(self.data), dtype=int)
                    if k is None
                    else next(indices_iter)  # type:ignore
                )
                for k in key
            ]
        )

        def _expand_indices(
            groups: Sequence[IntArray], key: IntArray
        ) -> Generator[tuple[IntArray, IntArray], None, None]:
            """Yield new indices and corresponding positions in the old index vector."""
            selected_groups: list[IntArray] = [groups[k] for k in key]
            for i, group in enumerate(selected_groups):
                yield np.ones(group.shape, dtype=int) * i, group

        data = self.data
        for axis, k in enumerate(array_key):
            if k is None:
                continue
            # Sort for speed.
            sort_ind = indices[axis].argsort()
            # Find the positions where all possible indices, i.e. from 0 to shape[axis],
            # can be found in the indices along mode axis.
            split_ind = np.searchsorted(indices[axis, sort_ind], np.arange(shape[axis]))
            groups = np.split(sort_ind, split_ind)[1:]
            # Select the indices and data that correspond to k.
            new_ind, selection = map(np.hstack, zip(*_expand_indices(groups, k)))
            indices = indices[:, selection]
            indices[axis] = new_ind
            data = data[selection]

        # Compute shape of indexed tensor.
        shape = tuple(1 if k is None else len(k) for k in array_key)
        # Remove axes indexed by integers.
        shape = tuple(shape[i] for i in range(len(key)) if i not in int_axes)
        subscripts = tuple(indices[i] for i in range(len(key)) if i not in int_axes)
        return type(self)(data, subscripts, shape, _check_unique_ind=False)

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
        PartialTensor
            A new `PartialTensor` with permuted axes.
        """
        axes = normalize_axes(axes, self.ndim, fill=True, fillreversed=True)
        indices = tuple(self._indices[ax] for ax in axes)
        shape = tuple(self.shape[ax] for ax in axes)
        return type(self)(self._data, indices, shape, _check_unique_ind=False)

    @property
    def dtype(self) -> np.dtype[Any]:
        """Datatype of the specified elements.

        Returns
        -------
        numpy.dtype[Any]
            The datatype of the specified tensor elements.
        """
        return self._data.dtype

    @property
    def data(self) -> VectorType:
        """Values of the specified elements.

        Returns
        -------
        VectorType
            The values of the specified tensor elements.
        """
        return self._data

    @property
    def indices(self) -> tuple[VectorType, ...]:
        """Indices of the specified elements.

        Returns
        -------
        tuple[VectorType, ...]
            The indices of the specified tensor elements.
        """
        return self._indices

    @property
    def flat_indices(self) -> VectorType:
        """Flat indices of the specified elements.

        Returns
        -------
        VectorType
            The flat indices of the specified tensor elements.
        """
        return self._flat_indices

    def __repr__(self) -> str:
        if Tensor._REPR_MODE != "repr":
            return str(self)
        with np.printoptions(threshold=50, linewidth=88, precision=3, edgeitems=2):
            return (
                f"{self.__class__.__name__}(\n"
                f"{self.data!r},\n"
                f"<list of {len(self.indices)} arrays>,\n"
                f"{self.shape!r},\n)"
            )

    def iscomplex(self) -> bool:
        """Test if the specified elements are complex-valued.

        Returns
        -------
        bool
            If the specified tensor elements are complex-valued.
        """
        return tlb.iscomplexobj(self._data)

    def conj(self) -> Self:
        """Compute complex conugate tensor.

        Returns
        -------
        Self
            Complex conjugate partial tensor.
        """
        if self.iscomplex():
            return type(self)(
                self._data.conj(),
                self._indices,
                self.shape,
                _check_unique_ind=False,
                _check_bounds=False,
                _sorted_indices=True,
            )
        else:
            return self

    def copy(self) -> Self:
        """Create copy of tensor.

        Returns
        -------
        Self
            Copy of the tensor.
        """
        new_indices = tuple(i.copy() for i in self._indices)
        return type(self)(
            self._data.copy(),
            new_indices,
            self.shape,
            _check_unique_ind=False,
            _check_bounds=False,
            _sorted_indices=True,
        )

    def __neg__(self) -> Self:
        new_indices = tuple(i.copy() for i in self._indices)
        return type(self)(
            -self._data,
            new_indices,
            self.shape,
            _check_unique_ind=False,
            _check_bounds=False,
            _sorted_indices=True,
        )

    def reshape(self, shape: ShapeLike) -> Self:
        """Return a `PartialTensor` containing the same data with a new shape `shape`.

        Parameters
        ----------
        shape : Shape
            The new shape should be compatible with the original shape, that is,
            ``math.prod(shape)`` should equal ``math.prod(self.shape)``.

        Returns
        -------
        Self
            New `PartialTensor` containing the same data with shape `shape`.

        Raises
        ------
        ValueError
            If the number of elements in the new shape does not equal the number of
            elements of the original shape.
        """
        shape = _ensure_sequence(shape)
        if math.prod(self.shape) != math.prod(shape):
            raise ValueError(
                f"the number of elements in the new shape {shape} does not equal "
                f"the number of elements in the original shape {self.shape}"
            )
        return type(self)(
            self._data.copy(),
            flat_indices=self._flat_indices.copy(),
            shape=shape,
            _check_unique_ind=False,
            _check_bounds=False,
            _sorted_indices=True,
        )


class IncompleteTensor(PartialTensor):
    """Incomplete tensor storing only known elements in the coordinate format.

    Only the indices (coordinates) and values of the known elements are stored. The
    remaining elements are assumed to be unknown. If an incomplete tensor is converted
    into an array, the unknown elements are represented by nans.

    Parameters
    ----------
    data : ArrayLike
        Values of the stored elements.
    indices : tuple[ArrayLike, ...], optional
        Indices of the stored elements stored as `ndim` vectors. Either `indices` or
        `flat_indices` must be provided.
    shape: ShapeLike, optional
        Shape of the tensor. If `shape` is not provided when `indices` are provided,
        the shape of the tensor will be inferred from `indices`. When only
        `flat_indices` are provided, `shape` must also be provided.
    flat_indices : ArrayLike, optional
        Flat, or linear, indices of the stored elements. Either `indices` or
        `flat_indices` must be provided. If both `indices` and `flat_indices` are
        provided, only the former will be used.
    _check_unique_ind : bool, default = True
        Check whether `indices` correspond to unique tensor elements. If they are
        guaranteed to be unique, this option can be set to False to save time.
    _check_bounds : bool, default = True
        Perform bounds check on `indices` if True.

    Notes
    -----
    Several operations, namely :func:`.frob`, :func:`.inprod`, :func:`.matdot`, and
    :func:`.mtkrprod`, would generally result in (an array of) nans when applied to an
    `IncompleteTensor`. In order to provide results that may still be useful, the
    unknown elements are set to zero for these operations. For the other operations,
    they are considered to be nans.

    Since there is no incomplete matrix format, :func:`.tens2mat` applied to an
    incomplete tensor returns a sparse matrix in coordinate format instead.

    Examples
    --------
    Create an incomplete tensor by providing the values of its known elements and the
    corresponding indices:

    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> indices = (np.array([0, 1]), np.array([2, 3]))
    >>> data = np.array([1, 2])
    >>> T = tl.IncompleteTensor(data, indices)

    The shape of the tensor is inferred from the maximal index in each array in
    `indices`, which corresponds to (3, 4) in this case. The shape can also explicitly
    be provided:

    >>> T = tl.IncompleteTensor(data, indices, (5, 5))

    Alternatively, the known elements can also be specified by providing flat or
    linear indices:

    >>> T = tl.IncompleteTensor(data, flat_indices=np.array([2, 8]), shape=(5, 5))

    An incomplete tensor can also be constructed from a dense tensor, in which the
    unknown elements are represented by nans:

    >>> T0 = T = np.full((3, 4), np.nan)
    >>> T0[indices] = data
    >>> T = tl.IncompleteTensor.from_dense(T)

    An `IncompleteTensor` with random elements can be created by providing the shape and
    the number of known elements:

    >>> T = tl.IncompleteTensor.randn((2, 3, 4), 10)

    Here the standard normal distribution is used to generate the elements. Other
    distributions are also available, and :func:`IncompleteTensor.random` can be used to
    specify any distribution. Complex elements can be generated by using the optional
    `imag` argument.

    See Also
    --------
    from_dense, random, randn, rand, random_like, randn_like, rand_like
    """

    @classmethod
    def from_dense(cls, T: ArrayType) -> Self:
        """Create an `IncompleteTensor` from a dense tensor.

        In the dense tensor `T`, unknown elements are represented by nans.

        Parameters
        ----------
        T : ArrayType
            Dense tensor to create an `IncompleteTensor` from.

        Returns
        -------
        IncompleteTensor
            The incomplete tensor corresponding to `T`.
        """
        indices = tuple(sub for sub in np.argwhere(~np.isnan(T)).T)
        return cls(
            T[indices],
            indices,
            T.shape,
            _check_unique_ind=False,
            _check_bounds=False,
            _sorted_indices=T.flags.c_contiguous,
        )

    def _empty_array(
        self, shape: ShapeLike, dtype: npt.DTypeLike | None = None
    ) -> ArrayType:
        if np.issubdtype(dtype, np.integer):
            # nan has no integer representation
            dtype = np.float64
        # Using np.full(shape, np.nan, dtype=dtype) fills the array with random values
        arr = np.zeros(shape, dtype=dtype)
        arr.fill(np.nan)
        return arr

    @property
    def nke(self) -> int:
        """Number of known elements.

        Returns
        -------
        int
            The number of known tensor elements.
        """
        return self._data.shape[0]

    def __str__(self) -> str:
        return (
            f"Incomplete tensor of shape {self.shape} with {self.nke} known elements."
        )

    @classmethod
    def random(
        cls,
        shape: Shape,
        nke: NonnegativeInt,
        real: SupportsArrayFromShape | None = None,
        imag: SupportsArrayFromShape | bool | None = None,
    ) -> Self:
        """Generate an `IncompleteTensor` with random elements.

        By default, real elements are generated. Complex elements can be generated by
        providing a random number generating function to `imag`.

        Parameters
        ----------
        shape : Shape
            The dimensions of the tensor.
        nke : NonnegativeInt
            The number of known elements.
        real : SupportsArrayFromShape, default = tl.get_rng().random
            Random number generating function for generating the real part of the
            factors.
        imag : SupportsArrayFromShape | bool, optional
            If this argument is provided, complex elements are generated. If `imag` is
            True, the function provided to `real` is also used to generate the imaginary
            part of the elements. If a random number generating function is provided,
            this function is used for generating the imaginary part of the elements.

        Returns
        -------
        IncompleteTensor
            An `IncompleteTensor` with random elements.

        See Also
        --------
        randn, rand, random_like, randn_like, rand_like
        """
        if real is None:
            real = get_rng().random

        return super().random(shape, nke, real, imag)

    @classmethod
    def random_like(
        cls,
        array: ArrayLike,
        nke: NonnegativeInt,
        real: SupportsArrayFromShape | None = None,
        imag: SupportsArrayFromShape | bool | None = None,
    ) -> Self:
        """Generate an `IncompleteTensor` with random elements.

        By default, real elements are generated. Complex elements can be generated by
        providing a random number generating function to `imag`.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        nke : NonnegativeInt
            The number of known elements.
        real : SupportsArrayFromShape, default = tl.get_rng().random
            Random number generating function for generating the real part of the
            factors.
        imag : SupportsArrayFromShape | bool, optional
            If this argument is provided, complex elements are generated. If `imag` is
            True, the function provided to `real` is also used to generate the imaginary
            part of the elements. If a random number generating function is provided,
            this function is used for generating the imaginary part of the elements.

        Returns
        -------
        IncompleteTensor
            An `IncompleteTensor` with random elements.
        """
        if real is None:
            real = get_rng().random

        return super().random_like(array, nke, real, imag)

    @classmethod
    def randn(
        cls,
        shape: Shape,
        nke: NonnegativeInt,
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random elements, drawn from a standard normal distribution.

        Parameters
        ----------
        shape : Shape
            The dimensions of the tensor.
        nke : NonnegativeInt
            The number of known elements.
        imag : bool, optional
            If True, the elements are complex, with the imaginary part also drawn from
            a standard normal distribution.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        IncompleteTensor
            An `IncompleteTensor` with random elements, drawn from a standard normal
            distribution.
        """
        _rng = get_rng(_rng)

        return super().randn(shape, nke, imag, _rng)

    @classmethod
    def randn_like(
        cls,
        array: ArrayLike,
        nke: NonnegativeInt,
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random elements, drawn from a standard normal distribution.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        nke : NonnegativeInt
            The number of known elements.
        imag : bool, optional
            If True, the elements are complex, with the imaginary part also drawn from
            a standard normal distribution.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        IncompleteTensor
            An `IncompleteTensor` with random elements, drawn from a standard normal
            distribution.
        """
        _rng = get_rng(_rng)

        return super().randn_like(array, nke, imag, _rng)

    @classmethod
    def rand(
        cls,
        shape: Shape,
        nke: NonnegativeInt,
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random elements, drawn from a uniform distribution.

        Parameters
        ----------
        shape : Shape
            The dimensions of the tensor.
        nke : NonnegativeInt
            The number of known elements.
        imag : bool, optional
            If True, the elements are complex, with the imaginary part also drawn from
            a uniform distribution.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        IncompleteTensor
            An `IncompleteTensor` with random elements, drawn from a uniform
            distribution.
        """
        _rng = get_rng(_rng)

        return super().rand(shape, nke, imag, _rng)

    @classmethod
    def rand_like(
        cls,
        array: ArrayLike,
        nke: NonnegativeInt,
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random elements, drawn from a uniform distribution.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        nke : NonnegativeInt
            The number of known elements.
        imag : bool, optional
            If True, the elements are complex, with the imaginary part also drawn from
            a uniform distribution.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        IncompleteTensor
            An `IncompleteTensor` with random elements, drawn from a uniform
            distribution.
        """
        _rng = get_rng(_rng)

        return super().rand_like(array, nke, imag, _rng)


class SparseTensor(PartialTensor):
    """Sparse tensor stored in the coordinate format.

    Only the indices (coordinates) and values of the nonzero elements are stored.

    Parameters
    ----------
    data : ArrayLike
        Values of the stored elements.
    indices : tuple[ArrayLike, ...], optional
        Indices of the stored elements stored as `ndim` vectors. Either `indices` or
        `flat_indices` must be provided.
    shape: ShapeLike, optional
        Shape of the tensor. If `shape` is not provided when `indices` are provided,
        the shape of the tensor will be inferred from `indices`. When only
        `flat_indices` are provided, `shape` must also be provided.
    flat_indices : ArrayLike, optional
        Flat, or linear, indices of the stored elements. Either `indices` or
        `flat_indices` must be provided. If both `indices` and `flat_indices` are
        provided, only the former will be used.
    _check_unique_ind : bool, default = True
        Check whether `indices` correspond to unique tensor elements. If they are
        guaranteed to be unique, this option can be set to False to save time.
    _check_bounds : bool, default = True
        Perform bounds check on `indices` if True.

    Notes
    -----
    When reshaping a sparse tensor into a matrix using :func:`.tens2mat`, a sparse
    matrix in coordinate format is returned.

    Examples
    --------
    Create a sparse tensor by providing the values of its nonzero elements and the
    corresponding indices:

    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> indices = (np.array([0, 1]), np.array([2, 3]))
    >>> data = np.array([1, 2])
    >>> T = tl.SparseTensor(data, indices)

    The shape of the tensor is inferred from the maximal index in each array in
    `indices`, which corresponds to (3, 4) in this case. The shape can also explicitly
    be provided:

    >>> T = tl.SparseTensor(data, indices, (5, 5))

    Alternatively, the nonzero elements can also be specified by providing flat, or
    linear, indices:

    >>> T = tl.SparseTensor(data, flat_indices=np.array([2, 8]), shape=(5, 5))

    A sparse tensor can also be constructed from a dense tensor:

    >>> T0 = np.zeros((3, 4))
    >>> T0[indices] = data
    >>> T = tl.SparseTensor.from_dense(T0)

    Optionally, a tolerance can be provided such that each element of ``T0`` that is
    smaller then this tolerance is considered to be zero.

    A sparse tensor can also be constructed from any scipy sparse array format:

    >>> import scipy
    >>> sparse_mat = scipy.sparse.coo_matrix(T0)
    >>> T = tl.SparseTensor.from_sparse_matrix(sparse_mat)

    A `SparseTensor` with random elements can be created by providing the shape and the
    number of nonzeros:

    >>> T = tl.SparseTensor.randn((2, 3, 4), 10)

    Here the standard normal distribution is used to generate the elements. Other
    distributions are also available, and `SparseTensor.random` can be used to
    specify any distribution. Complex elements can be generated by using the optional
    `imag` argument.

    See Also
    --------
    from_dense, from_sparse_matrix, random, randn, rand, random_like, randn_like,
    rand_like
    """

    @classmethod
    def from_dense(cls, T: ArrayType, tol: float | None = None) -> Self:
        """Create a `SparseTensor` from a dense tensor.

        Parameters
        ----------
        T : ArrayType
            Dense tensor to derive a `SparseTensor` from.
        tol : float, optional
            Array elements smaller than this tolerance are considered to be zero.

        Returns
        -------
        SparseTensor
            The sparse tensor corresponding to `T`.
        """
        if tol:
            indices = np.asarray(np.abs(T) > tol).nonzero()
        else:
            indices = np.nonzero(T)
        # `np.nonzero` may return unsorted indices if T is not C-contiguous.
        return cls(
            T[indices],
            indices,
            T.shape,
            _check_unique_ind=False,
            _check_bounds=False,
            _sorted_indices=T.flags.c_contiguous,
        )

    @classmethod
    def from_sparse_matrix(
        cls, matrix: SparseMatrix, _check_unique_ind: bool = False
    ) -> Self:
        """Create a `SparseTensor` from a sparse matrix.

        Parameters
        ----------
        matrix : SparseMatrix
            Sparse matrix to derive a `PartialTensor` from.
        _check_unique_ind : bool, default = False
            Check whether indices of sparse tensor correspond to unique tensor elements.

        Returns
        -------
        SparseTensor
            The sparse tensor corresponding to `matrix`.
        """
        matrix = matrix.tocoo()
        return cls(
            matrix.data,
            (matrix.row, matrix.col),
            matrix.shape,
            _check_unique_ind=_check_unique_ind,
            _check_bounds=False,
        )

    @classmethod
    def _from_incomplete(cls, T: IncompleteTensor, copy=True) -> Self:
        # Used for weighted operations on an Incompletetensor
        if copy:
            new_indices = tuple(i.copy() for i in T._indices)
            new_flat_indices = T._flat_indices.copy()
            new_data = T._data.copy()
            return cls(
                new_data,
                new_indices,
                T.shape,
                new_flat_indices,
                _check_unique_ind=False,
                _check_bounds=False,
                _sorted_indices=True,
            )
        else:
            return cls(
                T._data,
                T._indices,
                T.shape,
                T._flat_indices,
                _check_unique_ind=False,
                _check_bounds=False,
                _sorted_indices=True,
            )

    def _empty_array(
        self, shape: ShapeLike, dtype: npt.DTypeLike | None = None
    ) -> ArrayType:
        return np.zeros(shape, dtype=dtype)

    @property
    def nnz(self) -> int:
        """Number of nonzero elements.

        Returns
        -------
        int
            The number of nonzero elements of the sparse tensor.
        """
        return self._data.shape[0]

    def __str__(self) -> str:
        return f"Sparse tensor of shape {self.shape} with {self.nnz} nonzeros."

    @classmethod
    def random(
        cls,
        shape: Shape,
        nnz: NonnegativeInt,
        real: SupportsArrayFromShape | None = None,
        imag: SupportsArrayFromShape | bool | None = None,
    ) -> Self:
        """Generate a `SparseTensor` with random elements.

        By default, real elements are generated. Complex elements can be generated by
        providing a random number generating function to `imag`.

        Parameters
        ----------
        shape : Shape
            The dimensions of the tensor.
        nnz : NonnegativeInt
            The number of nonzero elements.
        real : SupportsArrayFromShape, default = tl.get_rng().random
            Random number generating function for generating the real part of the
            factors.
        imag : SupportsArrayFromShape | bool, optional
            If this argument is provided, complex elements are generated. If `imag` is
            True, the function provided to `real` is also used to generate the imaginary
            part of the elements. If a random number generating function is provided,
            this function is used for generating the imaginary part of the elements.

        Returns
        -------
        SparseTensor
            A `SparseTensor` with random elements.

        See Also
        --------
        randn, rand, random_like, randn_like, rand_like
        """
        if real is None:
            real = get_rng().random

        return super().random(shape, nnz, real, imag)

    @classmethod
    def random_like(
        cls,
        array: ArrayLike,
        nnz: NonnegativeInt,
        real: SupportsArrayFromShape | None = None,
        imag: SupportsArrayFromShape | bool | None = None,
    ) -> Self:
        """Generate a `SparseTensor` with random elements.

        By default, real elements are generated. Complex elements can be generated by
        providing a random number generating function to `imag`.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        nnz : NonnegativeInt
            The number of nonzero elements.
        real : SupportsArrayFromShape, default = tl.get_rng().random
            Random number generating function for generating the real part of the
            factors.
        imag : SupportsArrayFromShape | bool, optional
            If this argument is provided, complex elements are generated. If `imag` is
            True, the function provided to `real` is also used to generate the imaginary
            part of the elements. If a random number generating function is provided,
            this function is used for generating the imaginary part of the elements.

        Returns
        -------
        SparseTensor
            A `SparseTensor` with random elements.
        """
        if real is None:
            real = get_rng().random

        return super().random_like(array, nnz, real, imag)

    @classmethod
    def randn(
        cls,
        shape: Shape,
        nnz: NonnegativeInt,
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random elements, drawn from a standard normal distribution.

        Parameters
        ----------
        shape : Shape
            The dimensions of the tensor.
        nnz : NonnegativeInt
            The number of nonzero elements.
        imag : bool, optional
            If True, the elements are complex, with the imaginary part also drawn from
            a standard normal distribution.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        SparseTensor
            A `SparseTensor` with random elements, drawn from a standard normal
            distribution.
        """
        _rng = get_rng(_rng)

        return super().randn(shape, nnz, imag, _rng)

    @classmethod
    def randn_like(
        cls,
        array: ArrayLike,
        nnz: NonnegativeInt,
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random elements, drawn from a standard normal distribution.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        nnz : NonnegativeInt
            The number of nonzero elements.
        imag : bool, optional
            If True, the elements are complex, with the imaginary part also drawn from
            a standard normal distribution.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        SparseTensor
            A `SparseTensor` with random elements, drawn from a standard normal
            distribution.
        """
        _rng = get_rng(_rng)

        return super().randn_like(array, nnz, imag, _rng)

    @classmethod
    def rand(
        cls,
        shape: Shape,
        nnz: NonnegativeInt,
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random elements, drawn from a uniform distribution.

        Parameters
        ----------
        shape : Shape
            The dimensions of the tensor.
        nnz : NonnegativeInt
            The number of nonzero elements.
        imag : bool, optional
            If True, the elements are complex, with the imaginary part also drawn from
            a uniform distribution.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        SparseTensor
            A `SparseTensor` with random elements, drawn from a uniform
            distribution.
        """
        _rng = get_rng(_rng)

        return super().rand(shape, nnz, imag, _rng)

    @classmethod
    def rand_like(
        cls,
        array: ArrayLike,
        nnz: NonnegativeInt,
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random elements, drawn from a uniform distribution.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        nnz : NonnegativeInt
            The number of nonzero elements.
        imag : bool, optional
            If True, the elements are complex, with the imaginary part also drawn from
            a uniform distribution.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        SparseTensor
            A `SparseTensor` with random elements, drawn from a uniform distribution.
        """
        _rng = get_rng(_rng)

        return super().rand_like(array, nnz, imag, _rng)


@frob.register
def _frob_partial(T: PartialTensor, squared: bool = False) -> float:
    return _frob_array(T._data, squared)


# coo_matrix from scipy does not match coo_matrix stub according to pyright
@_tens2mat.register  # type: ignore
def _tens2mat_partial(T: PartialTensor, row: Axis, col: Axis) -> coo_matrix:
    indices = (
        np.ravel_multi_index([T._indices[i] for i in row], [T.shape[i] for i in row]),
        np.ravel_multi_index([T._indices[i] for i in col], [T.shape[i] for i in col]),
    )
    matshape = (
        math.prod(T.shape[i] for i in row),
        math.prod(T.shape[i] for i in col),
    )
    return coo_matrix((T._data, indices), matshape)


@_mat2tens.register
def _mat2tens_sparsemat(
    matrix: SparseMatrix, shape: Shape, row: Axis, col: Axis
) -> SparseTensor:
    perm = tuple(row) + tuple(col)
    matrix = matrix.tocoo()
    flat_indices = np.ravel_multi_index((matrix.row, matrix.col), matrix.shape)
    indices = np.unravel_index(flat_indices, tuple(shape[i] for i in perm))
    iperm = argsort(perm)
    return SparseTensor(
        matrix.data,
        tuple(indices[i] for i in iperm),
        shape,
        _check_unique_ind=False,
        _check_bounds=False,
    )


@_tmprod.register
def _tmprod_sparse(
    T: SparseTensor, matrices: Sequence[MatrixType], axes: Axis
) -> ArrayType:
    # Multiply with first matrix, which returns a dense result.
    mat = matrices[0] @ tens2mat(T, axes[0])
    shape = tuple(mat.shape[0] if i == axes[0] else s for i, s in enumerate(T.shape))
    col = _complement_indices(axes[0], T.ndim)
    array = _mat2tens(mat, tuple(shape), (axes[0],), col)

    # Perform remaining products.
    result = _tmprod(array, matrices[1:], axes[1:])
    # Satisfy type checking. Using _tmprod_array is not possible, since its return type
    # is overwritten by the return type of _tmprod.
    assert isinstance(result, np.ndarray)
    return result


@_tvprod.register
def _tvprod_sparse(
    T: SparseTensor, vectors: Sequence[VectorType], axes: Axis
) -> ArrayType | float:
    row_vectors = [v[np.newaxis, :] for v in vectors]
    res = np.squeeze(_tmprod_sparse(T, row_vectors, axes), axes)
    if len(axes) == T.ndim and hasattr(res, "__getitem__"):
        return res.item()
    return res


@_tmprod.register
def _tmprod_incomplete(
    T: IncompleteTensor, matrices: Sequence[MatrixType], axes: Axis
) -> IncompleteTensor:
    # Compute resulting shape.
    shape = list(T.shape)
    for i, ax in enumerate(axes):
        shape[ax] = matrices[i].shape[0]

    # Find which elements are in fully known slices.
    other_axes = [ax for ax in range(T.ndim) if ax not in axes]
    shape_other_axes = [T.shape[ax] for ax in other_axes]
    indices_other_axes = [T._indices[ax] for ax in other_axes]

    flat_indices_other_axes = np.ravel_multi_index(indices_other_axes, shape_other_axes)
    unique_flat_indices, unique_inverse, unique_cnt = np.unique(
        flat_indices_other_axes, return_counts=True, return_inverse=True
    )
    elements_per_slice = math.prod(T.shape[ax] for ax in axes)
    full_slices = unique_cnt == elements_per_slice
    if not np.any(full_slices):
        empty_index = np.array([], dtype=np.int64)
        return IncompleteTensor(np.array([]), (empty_index,) * T.ndim, shape)
    indices_in_full_slices = full_slices[unique_inverse]

    # Permute other_axes to end and ensure indices are sorted.
    indices_full = [T._indices[ax][indices_in_full_slices] for ax in axes] + [
        T._indices[ax][indices_in_full_slices] for ax in other_axes
    ]
    flat_indices_full = np.ravel_multi_index(
        indices_full, [T.shape[ax] for ax in axes] + [T.shape[ax] for ax in other_axes]
    )
    order = np.argsort(flat_indices_full)

    # Make dense tensor and perform tmprod.
    Tdense_flat = T._data[indices_in_full_slices][order]
    Tdense = Tdense_flat.reshape(*(T.shape[ax] for ax in axes), -1)
    TMdense = tmprod(Tdense, matrices, range(len(axes)))

    # Form indices.
    indices = np.mgrid[tuple(slice(0, i) for i in TMdense.shape)]
    indices = indices.reshape(TMdense.ndim, -1)
    full_indices = [indices[0]] * T.ndim
    unique_indices = np.unravel_index(unique_flat_indices, shape_other_axes)
    for i, ax in enumerate(axes):
        full_indices[ax] = indices[i]
    for i, ax in enumerate(other_axes):
        full_indices[ax] = unique_indices[i][full_slices][indices[-1]]

    return IncompleteTensor(
        TMdense.ravel(),
        indices=tuple(full_indices),
        shape=shape,
        _check_unique_ind=False,
        _check_bounds=False,
    )


@_tvprod.register
def _tvprod_incomplete(
    T: IncompleteTensor, vectors: Sequence[VectorType], axes: Axis
) -> IncompleteTensor | NumberType:
    row_vectors = [v[np.newaxis, :] for v in vectors]
    res = _tmprod_incomplete(T, row_vectors, axes)
    if len(axes) == T.ndim and hasattr(res, "__getitem__"):
        return cast(NumberType, np.squeeze(np.array(res)).item())
    # the return type of _tmprod_incomplete is IncompleteTensor, but this gets
    # overwritten by the dispatcher
    assert isinstance(res, IncompleteTensor)
    shape = tuple(s for a, s in enumerate(T.shape) if a not in axes)
    return res.reshape(shape)


@_mtkrprod_single.register
def _mtkrprod_single_sparse(
    T: SparseTensor, U: Sequence[MatrixType], axis: int, conjugate: bool = True
) -> MatrixType:
    if conjugate:
        U = [u.conj() for u in U]
    # Multiplication with the first matrix in U, which returns a dense matrix.
    init_axis = 0 if axis != 0 else 1
    tmp: ArrayType = U[init_axis].T @ tens2mat(T, init_axis, axis)
    # Split into rows
    rows: list[ArrayType] = np.vsplit(tmp, tmp.shape[0])

    # Contractions with the remaining matrices in U.
    def _contract(rows: list[ArrayType], U: ArrayType, shape: Shape) -> list[ArrayType]:
        return [row.reshape(shape).dot(vec) for row, vec in zip(rows, U.T)]

    axes = tuple(i for i in range(T.ndim) if i not in (axis, init_axis))
    if axes:
        for ax in reversed(axes):
            shape = (-1, T.shape[ax])
            rows = _contract(rows, U[ax], shape)

    rows = [r.flatten() for r in rows]
    return np.stack(rows).T


@_mtkrprod_single.register
def _mtkrprod_single_incomplete(
    T: IncompleteTensor, U: Sequence[MatrixType], axis: int, conjugate: bool = True
) -> MatrixType:
    return _mtkrprod_single_sparse(
        SparseTensor._from_incomplete(T, copy=False), U, axis, conjugate
    )


@_mtkrprod_all.register
def _mtkrprod_all_partial(
    T: PartialTensor, U: Sequence[MatrixType], conjugate: bool = True
) -> Sequence[MatrixType]:
    # Can probably be done in a tree approach like for array
    return [_mtkrprod_single(T, U, axis, conjugate) for axis in range(T.ndim)]


@_mtkronprod_single.register
def _mtkronprod_single_sparse(
    T: SparseTensor,
    U: Sequence[MatrixType],
    axis: int,
    transpose: Literal["T", "H"] | None = None,
) -> MatrixType:
    other_axes = tuple(a for a in range(T.ndim) if a != axis)
    if transpose == "T":
        U = tuple(f.conj() for i, f in enumerate(U) if i != axis)
    elif transpose == "H":
        U = tuple(f for i, f in enumerate(U) if i != axis)
    else:
        U = tuple(f.conj().T for i, f in enumerate(U) if i != axis)
    tmp = tmprod(T, U, other_axes)
    # other axes is not empty, so tmprod returns ArrayType
    assert not isinstance(tmp, SparseTensor)
    return tens2mat(tmp, axis)


@_mtkronprod_single.register
def _mtkronprod_single_incomplete(
    T: IncompleteTensor,
    U: Sequence[MatrixType],
    axis: int,
    transpose: Literal["T", "H"] | None = None,
) -> MatrixType:
    return _mtkronprod_single_sparse(
        SparseTensor._from_incomplete(T, copy=False), U, axis, transpose
    )


@_mtkronprod_all.register
def _mtkronprod_all_partial(
    T: PartialTensor,
    U: Sequence[MatrixType],
    transpose: Literal["T", "H"] | None = None,
) -> Sequence[MatrixType]:
    # Can probably be done in a tree approach like for array
    return [_mtkronprod_single(T, U, axis, transpose) for axis in range(T.ndim)]


@noisy.register
def _noisy_partial(array: PartialTensor, snr: float, _rng=None):
    _rng = get_rng(_rng)

    return type(array)(
        noisy(array.data, snr, _rng=_rng),
        array.indices,
        array.shape,
        array.flat_indices,
        _check_unique_ind=False,
        _check_bounds=False,
        _sorted_indices=True,
    )

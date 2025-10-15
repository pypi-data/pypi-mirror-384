"""Hankelized tensor format and implementations of core operations.

A :class:`.HankelTensor` represents the Hankelized version of an array. If the array has
more than one dimension, then Hankelization is applied to all vectors along one axis of
the array. A :class:`.HankelTensor` only stores the original array, but it behaves as
the Hankelized version of this array when any tensor operation is used on it.

While :class:`.HankelTensor` provides a memory-efficient representation of a Hankel
tensor, :func:`.hankelize` returns an array that is equivalent to ``numpy.array(H)`` of
a :class:`.HankelTensor` ``H``. This avoids the efficient operations at a higher memory
cost, but can be more accurate if full precision results are needed.

The reverse operation, :func:`.dehankelize`, extracts the data generating a
:class:`.HankelTensor`. This data can be a dense array or a :class:`.Tensor`, as the
data can be extracted more efficiently in some cases such as for a
:class:`.PolyadicTensor`. :class:`.HankelTensor` has similar methods
(:meth:`.HankelTensor.from_array` and :meth:`.HankelTensor.from_polyadic`) that return a
:class:`.HankelTensor` instead of only the generating data. (The generating data can be
extracted using ``H._data`` if needed.)

Classes
-------
AxisSummaryFcn
    Take a summary along an axis.
HankelTensor
    Represent a tensor that is Hankelized along one axis.

Routines
--------
dehankelize
    Extract generators of a Hankel tensor.
dehankelize_terms
    Extract generators of rank-1 terms representing Hankel tensors.
hankelize
    Hankelize data.

Examples
--------
Construct a Hankel matrix from a vector:

>>> import numpy as np
>>> import pytensorlab as tl

>>> H = tl.HankelTensor([0, 1, 2])
>>> np.array(H)
array([[0, 1],
       [1, 2]])

See :class:`.HankelTensor` for more examples.
"""

import math
import sys
from collections.abc import Generator, Sequence
from functools import singledispatch
from itertools import accumulate, groupby, product
from math import ceil, prod
from typing import (
    Any,
    Literal,
    Protocol,
    cast,
)

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

import numpy as np
from numpy.fft import fft, ifft
from numpy.typing import ArrayLike, DTypeLike

from pytensorlab.datatypes.ndarray import _getitem_array, _tmprod_array
from pytensorlab.datatypes.polyadic import PolyadicTensor
from pytensorlab.datatypes.tensor import DenseTensor
from pytensorlab.typing import (
    Axis,
    NormalizedAdvancedIndexType,
    NormalizedBasicIndexType,
)
from pytensorlab.typing.core import (
    ArrayType,
    IndexLike,
    MatrixType,
    NormalizedIndexType,
    ShapeLike,
    TensorType,
)
from pytensorlab.typing.validators import NonnegativeInt, PositiveInt
from pytensorlab.util.indextricks import (
    _reshape_axes,
    compute_indexed_shape,
    find_sequence,
    findfirst,
    isadvanced,
    normalize_axes,
    normalize_index,
    partition_range,
)
from pytensorlab.util.utils import argsort, krr

from .core import (
    _mtkronprod_single,
    _mtkrprod_all,
    _mtkrprod_single,
    _tmprod,
    frob,
    getitem,
)
from .ndarray import _mtkrprod_single_for_array
from .tensor import Tensor  # noqa: F401 # sphinx


class AxisSummaryFcn(Protocol):
    """Take a summary along an axis."""

    def __call__(self, array: ArrayType, /, axis: int) -> ArrayType:
        """Compute a summary along an axis.

        Parameters
        ----------
        array : ArrayType
            The array to compute summaries of.
        axis : int
            The axis along which to compute the summary.

        Returns
        -------
        ArrayType
            Summarized array.

        See Also
        --------
        numpy.mean
        """
        ...


class HankelTensor(DenseTensor):
    """Represent a tensor that is Hankelized along one axis.

    A Hankel tensor is a generalization of a Hankel matrix to higher orders, i.e., two
    or more axes. For the second-order case, i.e., a Hankel matrix, the anti-diagonals
    are constant, while for the higher-order case the 'anti-diagonal hyperplanes' are
    constant. For example, for a third-order Hankelization ``H`` of a generating vector
    `data`, it holds that::

        H[i, j, k] = data[i +j + k - 3].

    A :class:`.HankelTensor` provides an efficient representation of the tensor, by
    storing only the generating vector, as well as efficient operations that avoid
    construction of the array itself. Several signals can be Hankelized simultaneously
    along an axis `axis` by providing a generating array `data`, i.e., all mode-`axis`
    vectors are converted into Hankel tensors with `order` dimensions.

    Parameters
    ----------
    data : ArrayType
        The array to Hankelize.
    order : PositiveInt, default = 2
        Hankelization order of each vector.
    axis : int, default = 0
        The axis along which Hankelization is performed.
    breakpoints : int | tuple[int, ...], optional
        The ``order - 1`` break points for the Hankelization process. Let ``v`` be a
        mode-`axis` vector of `data`, and ``H`` its Hankelization, then::

            H[:, 0, ..., 0] = v[: breakpoints[0] + 1]
            H[-1, :, 0, ..., 0] = v[breakpoints[0] : breakpoints[1] + 1]
            ...
            H[-1, ..., -1, :] = v[breakpoints[-1] :]

        By default, the break points are chosen to make ``H`` as square/cubical as
        possible with the smaller dimensions at most 1 smaller than the larger ones.
    prepend_zeros : NonnegativeInt, default = 0
        Number of zeros to add before each vector in `data` along axis `axis`.
    append_zeros : NonnegativeInt, default = 0
        Number of zeros to add after each vector in `data` along axis `axis`.
    copy : bool, default = True
        If True, a copy of the array `data` is stored. Otherwise, `data` itself is
        stored.

    Examples
    --------
    Construct a Hankel matrix from a vector:

    >>> import numpy as np
    >>> import pytensorlab as tl

    >>> H = tl.HankelTensor([0, 1, 2])
    >>> np.array(H)
    array([[0, 1],
           [1, 2]])

    Construct a third-order Hankel tensor from a vector:

    >>> H = tl.HankelTensor([0, 1, 2, 3], order=3)
    >>> np.array(H)
    array([[[0, 1],
            [1, 2]],
    <BLANKLINE>
           [[1, 2],
            [2, 3]]])

    By default, Hankelization is performed along the first axis of `data`. Another axis
    can be specified:

    >>> H = tl.HankelTensor([[0,1,2], [3,4,5]], axis=1)
    >>> np.array(H)
    array([[[0, 1],
            [1, 2]],
    <BLANKLINE>
           [[3, 4],
            [4, 5]]])

    The shape of the resulting Hankelization can be altered using `breakpoints`. For
    example, by default the Hankel matrix of a vector is (close to) square. This can be
    changed by specifying `breakpoints`:

    >>> H = tl.HankelTensor(list(range(9)))
    >>> np.array(H)
    array([[0, 1, 2, 3, 4],
           [1, 2, 3, 4, 5],
           [2, 3, 4, 5, 6],
           [3, 4, 5, 6, 7],
           [4, 5, 6, 7, 8]])
    >>> H = tl.HankelTensor(list(range(9)), breakpoints=2)
    >>> np.array(H)
    array([[0, 1, 2, 3, 4, 5, 6],
           [1, 2, 3, 4, 5, 6, 7],
           [2, 3, 4, 5, 6, 7, 8]])
    >>> H = tl.HankelTensor(list(range(9)), order=3, breakpoints=(2,3))
    >>> np.array(H)
    array([[[0, 1, 2, 3, 4, 5],
            [1, 2, 3, 4, 5, 6]],
    <BLANKLINE>
           [[1, 2, 3, 4, 5, 6],
            [2, 3, 4, 5, 6, 7]],
    <BLANKLINE>
           [[2, 3, 4, 5, 6, 7],
            [3, 4, 5, 6, 7, 8]]])
    """

    def __init__(
        self,
        data: ArrayLike,
        order: PositiveInt = 2,
        axis: int = 0,
        breakpoints: int | tuple[int, ...] | None = None,
        prepend_zeros: NonnegativeInt = 0,
        append_zeros: NonnegativeInt = 0,
        copy: bool = True,
    ):
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        data = cast(ArrayType, data)
        if order < 2:
            raise ValueError("order should be at least 2")
        if not (-data.ndim <= axis < data.ndim):
            raise ValueError("axis should be in range -data.ndim <= axis < data.ndim")
        if axis < 0:
            axis += data.ndim
        if copy and not prepend_zeros and not append_zeros:
            data = np.copy(data)
        if prepend_zeros:
            dim = (s if n != axis else prepend_zeros for n, s in enumerate(data.shape))
            extra = np.zeros(tuple(dim))
            data = cast(ArrayType, np.concatenate((extra, data), axis=axis))
        if append_zeros:
            dim = (s if n != axis else append_zeros for n, s in enumerate(data.shape))
            extra = np.zeros(tuple(dim))
            data = cast(ArrayType, np.concatenate((data, extra), axis=axis))

        N = data.shape[axis]
        if breakpoints is None:
            breakpoints = tuple(ceil((n + 1) * N / order) - 1 for n in range(order - 1))
        if isinstance(breakpoints, int):
            breakpoints = (breakpoints,)
        if len(breakpoints) != order - 1:
            raise ValueError(
                f"number of breakpoints does not equal order minus one; "
                f"expected {order-1}, but got {len(breakpoints)}"
            )
        if any(b >= N for b in breakpoints):
            raise ValueError("all breakpoints should be smaller than data.shape[axis]")
        if any(b1 > b2 for b1, b2 in zip(breakpoints, breakpoints[1:])):
            raise ValueError("breakpoints should be ordered ascendingly")

        self.order: PositiveInt = order
        self.axis: NonnegativeInt = axis
        self._data: ArrayType = data
        self.breakpoints: tuple[int, ...] = breakpoints
        self.hankel_shape: tuple[int, ...] = tuple(
            b2 - b1 + 1 for b1, b2 in zip((0,) + breakpoints, breakpoints + (N - 1,))
        )
        shape = data.shape[:axis] + self.hankel_shape + data.shape[axis + 1 :]
        super().__init__(shape)

    def __array__(self, dtype: DTypeLike = None, copy: bool | None = None) -> ArrayType:
        subscripts = np.meshgrid(
            *tuple(range(s) for s in self.hankel_shape), indexing="ij"
        )
        indices = np.add.reduce(subscripts)
        return np.take(self._data, indices, axis=self.axis)

    @classmethod
    def from_data_like(
        cls,
        other: Self,
        data: ArrayType,
        order: PositiveInt | None = None,
        axis: int | None = None,
        breakpoints: tuple[int, ...] | None = None,
        copy: bool = True,
    ) -> Self:
        """Hankelize an array along one axis.

        Parameters
        ----------
        other : HankelTensor
            If the arguments `order`, `axis` and `breakpoints` are not specified, then
            ``other.order``, ``other.axis``  and ``other.breakpoints`` are used.
        data : ArrayType
            The array to Hankelize.
        order : PositiveInt, optional
            By default, a Hankel tensor of order ``other.order`` is produced for each
            vector in `data` along axis `axis`. If `order` is specified, then this value
            is used as the order of the Hankelization.
        axis : int, optional
            By default, Hankelization is performed along axis ``other.axis``. If `axis`
            is specified, then Hankelization is performed along this axis.
        breakpoints : int | tuple[int, ...], optional
            By default, ``other.breakpoints`` is used. By specifying `breakpoints`, the
            shape of the Hankel tensor for each vector can be altered. Specifically, the
            shape becomes ``tuple(b2 - b1 + 1 for b1, b2 in zip((0,) + breakpoints,
            breakpoints + (N - 1,)))``.
        copy : bool, default = True
            If True, a copy of the array `data` is stored. Otherwise, `data` itself is
            stored.

        Returns
        -------
        HankelTensor
            The Hankelized version of `data`.
        """
        if order is None:
            order = other.order
        if axis is None:
            axis = other.axis
        if breakpoints is None:
            breakpoints = other.breakpoints
        return cls(data, order, axis, breakpoints, copy=copy)

    @classmethod
    def from_array(
        cls,
        data: ArrayType,
        axis: int = 0,
        order: PositiveInt = 2,
        method: Literal["fiber"] | AxisSummaryFcn = "fiber",
    ) -> Self:
        """Construct the Hankel representation of an array.

        Get the Hankel representation of `data`, which is assumed to be a Hankelized
        array. If `data` is not a Hankelized array, then the :class:`.HankelTensor`
        representation constructed by this function will not be exactly equal to the
        array `data`.

        Parameters
        ----------
        data : ArrayType
            Array to construct the Hankel representation of.
        axis : int, default = 0
            Axis along which Hankelization is performed. Default is 0.
        order : PositiveInt, default = 2
            Order of Hankelization. Default is 2.
        method : "fiber" | AxisSummaryFcn, default = "fiber"
            Method used to extract the generating values of a Hankel tensor. The method
            ``"fiber"`` extracts the vectors ::

                data[:, 0, ..., 0] data[-1, :, 0, ..., 0] data[-1, -1, :, 0, ..., 0] ...
                data[-1, ..., -1, :]

            to reconstruct the generating values. (Assuming `axis` equals ``0`` and
            `order` equals ``data.ndim``, if not this is repeated for every subtensor.)
            If an axis summary function is provided, each 'anti-diagonal hyperplane' to
            `method` as an array with ``ndim = data.ndim - order + 1``. See
            :class:`AxisSummaryFcn` for more details.

        Returns
        -------
        Self
            The Hankel representation of `data`.

        See Also
        --------
        AxisSummaryFcn, HankelTensor.from_polyadic
        """
        result = dehankelize(data, axis, order, method)
        shape = data.shape[axis : axis + order]
        breakpoints = tuple(b - n - 1 for n, b in enumerate(accumulate(shape[:-1])))
        return cls(result, order, axis, breakpoints)

    @classmethod
    def from_polyadic(
        cls,
        data: PolyadicTensor,
        axis: int = 0,
        order: int = 2,
        mode: Literal["full"] | Literal["terms"] = "full",
    ) -> Self:
        """Construct the Hankel representation of a :class:`.PolyadicTensor`.

        Parameters
        ----------
        data : PolyadicTensor
            `PolyadicTensor` to construct the Hankel representation of.
        axis : int
            Axis along which Hankelization is performed.
        order : int
            Order of Hankelization.
        mode : "full" | "terms", default = "full"
            Treat `data` as a representation for the entire term if ``"full"``. If
            ``"terms"``, each rank 1 term is dehankelized separately; see
            :func:`.dehankelize_terms`.

        Returns
        -------
        HankelTensor
            The Hankel representation of `data`.

        See Also
        --------
        :func:`.dehankelize`, :func:`.dehankelize_terms`.

        """
        result = dehankelize(data, axis, order)
        shape = data.shape[axis : axis + order]
        breakpoints = tuple(b - n - 1 for n, b in enumerate(accumulate(shape[:-1])))
        return cls(result, order, axis, breakpoints)

    @property
    def data(self) -> ArrayType:
        """Values of the specified elements."""
        return self._data

    def transpose(self, axes: Axis | None = None) -> Self:
        """Return a `HankelTensor` with transposed axes.

        Parameters
        ----------
        axes : Axis, optional
            If specified, it must be a permutation of ``range(self.ndim)``. The ith axis
            of the returned tensor will correspond to the axis ``axes[i]`` of the input
            tensor. Negative indexing of these axes is allowed. If `axes` does not
            include all values in ``range(self.ndim)``, the remaining axes are appended
            descendingly.

        Returns
        -------
        Self
            A new :class:`.HankelTensor` with transposed axes.

        Raises
        ------
        ValueError
            Changing the order of Hankel axes is not allowed.
        """
        axes = normalize_axes(axes, self.ndim, fill=True, fillreversed=True)
        new_hankel_axes = tuple(
            i for i, n in enumerate(axes) if self.axis <= n < self.axis + self.order
        )
        if any(n1 + 1 != n2 for n1, n2 in zip(new_hankel_axes, new_hankel_axes[1:])):
            raise ValueError("splitting the Hankel axes is not allowed")
        hankel_axis = new_hankel_axes[0]
        old_hankel_axes = tuple(axes[i] for i in new_hankel_axes)
        new_breakpoints = accumulate(self.shape[i] - 1 for i in old_hankel_axes[:-1])
        # if any(n1 + 1 != n2 for n1, n2 in zip(old_hankel_axes, old_hankel_axes[1:])):
        #     raise ValueError("changing the order of the Hankel axes is not allowed")

        new_axes = tuple(
            n for n in axes if n <= self.axis or n >= self.axis + self.order
        )
        new_axes = tuple(n if n <= self.axis else n - self.order + 1 for n in new_axes)
        return type(self).from_data_like(
            self,
            np.transpose(self._data, new_axes),
            axis=hankel_axis,
            breakpoints=tuple(new_breakpoints),
        )

    def __getitem__(self, key: IndexLike) -> Self | ArrayType | float:
        try:
            return super().__getitem__(key)
        except ValueError as err:
            if "order" in str(err):
                normalized_key = normalize_index(key, self.shape)
                normalized_key = cast(tuple[NormalizedIndexType, ...], normalized_key)
                return self._getitem_indexed(normalized_key)
            raise err

    def _getitem_indexed(self, key: Sequence[NormalizedIndexType]) -> float | ArrayType:
        normal_key = tuple(k for k in key if k is not None)
        pre_key = normal_key[: self.axis]
        hankel_key = normal_key[self.axis : self.axis + self.order]
        post_key = normal_key[self.axis + self.order :]
        hankel_shape = self.shape[self.axis : self.axis + self.order]

        # Check if advanced indices should be moved to first position.
        perm2first = sum([k for k, _ in groupby(key, isadvanced)]) > 1
        # Compute new shape.
        shape, broadcast_shape = compute_indexed_shape(key, perm2first)

        # Convert Hankel keys to advanced indices.
        hankel_index = np.zeros(broadcast_shape, dtype=int)
        for k, s in zip(reversed(hankel_key), reversed(hankel_shape)):
            if isinstance(k, slice | tuple):
                if isinstance(k, slice):
                    k = np.arange(s, dtype=int)[k]
                elif isinstance(k, tuple):
                    k = np.array(tuple(i if i >= 0 else i + s for i in k), dtype=int)
                hankel_index = np.add.outer(k, hankel_index)
            else:
                k = np.asarray(k, dtype=int)
                hankel_index = hankel_index + k + (k < 0) * s

        new_key = pre_key + (hankel_index,) + post_key
        result = _getitem_array(self._data, new_key)
        if isinstance(result, float):
            return result

        # As Hankel modes are always indexed, indices might have moved to the first
        # position regardless of perm2first. Reorder axes if needed.
        new_perm2first = sum([k for k, _ in groupby(new_key, isadvanced)]) > 1

        hankel_slice = self.order - sum(map(isadvanced, hankel_key))
        pre_slice = self.axis - sum(map(isadvanced, pre_key))
        post_slice = self.ndim - sum(map(isadvanced, post_key)) - self.axis - self.order
        if new_perm2first:
            hankel_ind, index_ind, pre_ind, post_ind = partition_range(
                (hankel_slice, len(broadcast_shape), pre_slice, post_slice)
            )
        else:
            pre_ind, hankel_ind, index_ind, post_ind = partition_range(
                (pre_slice, hankel_slice, len(broadcast_shape), post_slice)
            )
        position = 0 if perm2first else findfirst(map(isadvanced, normal_key))
        index = pre_ind + hankel_ind + post_ind
        index = index[:position] + index_ind + index[position:]

        return np.reshape(np.transpose(result, index), shape)

    def _entry(self, indices: Sequence[NormalizedAdvancedIndexType]) -> ArrayType:
        raise NotImplementedError("use tl.getitem or normal indexing instead")

    def _getitem_sliced(self, key: Sequence[NormalizedBasicIndexType]) -> Self | float:
        normal_key_position = tuple(n for n, k in enumerate(key) if k is not None)
        none_before = normal_key_position[self.axis] - self.axis
        hankel_key = tuple(
            k
            for n, k in enumerate(key)
            if self.axis <= n - none_before < self.axis + self.order
        )
        if any(k is None for k in hankel_key):
            raise IndexError("newaxis is not allowed for Hankel axes")

        def get_step(
            key: Sequence[NormalizedBasicIndexType],
        ) -> Generator[int, None, None]:
            for k in key:
                if isinstance(k, slice):
                    yield k.step
                if isinstance(k, tuple) and len(k) > 1:
                    step = k[1] - k[0]
                    if step <= 0:
                        raise IndexError(
                            f"entries of key should be increasing for Hankel axes: {k}"
                        )
                    if any(k2 - k1 != step for k1, k2 in zip(k, k[1:])):
                        raise IndexError(
                            f"entries of key should be spaced equally for Hankel axes: "
                            f"{k}"
                        )
                    yield step

        steps = tuple(get_step(hankel_key))
        if not steps:
            steps = (1,)
        if any(step != steps[0] for step in steps):
            raise IndexError("the step should be equal for all Hankel axes")

        # Prepare slicing for Hankel axis in the data.
        hankel_shape = self.shape[self.axis : self.axis + self.order]
        int_key = tuple(k for k in hankel_key if isinstance(k, int))
        offset = sum(int_key)
        indices = tuple(
            np.arange(s)[(k,)]
            for s, k in zip(hankel_shape, hankel_key)
            if not isinstance(k, int)
        )
        min_index = sum(index[0] for index in indices) + offset
        max_index = sum(index[-1] for index in indices) + offset
        hankel_slice = slice(min_index, max_index + 1, steps[0])

        # Create Hankel tensor with sliced data.
        before_axis_key = tuple(key[: self.axis + none_before])
        new_key = (
            before_axis_key
            + (hankel_slice,)
            + tuple(key[self.axis + self.order + none_before :])
        )
        breakpoints = tuple(accumulate(len(index) - 1 for index in indices[:-1]))
        new_axis = sum(not isinstance(k, int) for k in before_axis_key)
        return type(self)(
            cast(ArrayType, getitem(self._data, new_key)),
            self.order - len(int_key),
            new_axis,
            breakpoints,
        )

    def reshape(self, shape: ShapeLike) -> Self:
        axes = _reshape_axes(self.shape, shape)
        new_axis = find_sequence(axes, [(self.axis + n,) for n in range(self.order)])
        if new_axis < 0:
            raise ValueError(
                f"cannot reshape Hankel axes in range({self.axis}, "
                f"{self.axis + self.order}); convert to array first if this is desired"
            )

        pre = (math.prod(self.shape[n] for n in ax) for ax in axes[:new_axis])
        post = (
            math.prod(self.shape[n] for n in ax) for ax in axes[new_axis + self.order :]
        )
        shape = (*pre, -1, *post)
        return type(self)(
            self._data.reshape(shape), self.order, new_axis, self.breakpoints
        )

    @property
    def dtype(self) -> np.dtype[Any]:
        return self._data.dtype

    def copy(self) -> Self:
        return type(self).from_data_like(self, self._data)

    def iscomplex(self) -> bool:
        return np.iscomplexobj(self._data)

    def conj(self) -> Self:
        if self.iscomplex():
            return type(self).from_data_like(self, self._data.conj())
        return self

    def __str__(self) -> str:
        return (
            f"Hankel tensor of shape {self.shape} with Hankel axis {self.axis} and "
            f"order {self.order}."
        )

    def __repr__(self) -> str:
        if Tensor._REPR_MODE != "repr":
            return str(self)
        return (
            f"Hankel tensor of shape {self.shape} with Hankel axis {self.axis} and "
            f"order {self.order}."
        )


@_mtkrprod_single.register
def _mtkrprod_single_for_hankel(
    T: HankelTensor, U: Sequence[MatrixType], axis: int, conjugate: bool = True
) -> MatrixType:
    N = T._data.shape[T.axis]
    if T.axis <= axis < T.axis + T.order:
        factors = tuple(u for n, u in enumerate(U) if not T.axis < n < T.axis + T.order)
        if len(factors) > 1:
            tmp = _mtkrprod_single_for_array(T._data, factors, T.axis, conjugate)
        else:
            tmp = T._data.reshape((-1, 1))
        tmp = fft(tmp, axis=0)
        for n in range(T.axis, T.axis + T.order):
            if n == axis:
                continue
            u = U[n][::-1, :].conj() if conjugate else U[n][::-1, :]
            tmp = tmp * fft(u, N, axis=0)
        M = ifft(tmp, axis=0)[-U[axis].shape[0] :]
        if not np.iscomplexobj(U[0]) and not np.iscomplexobj(T._data):
            M = np.real(M)
        return M
    else:
        factor = fft(U[T.axis], N, axis=0)
        for u in U[T.axis + 1 : T.axis + T.order]:
            factor *= fft(u, N, axis=0)
        factor = ifft(factor, N, axis=0)
        if not np.iscomplexobj(U[0]) and not np.iscomplexobj(T._data):
            factor = np.real(factor)
        factors = tuple(U[: T.axis]) + (factor,) + tuple(U[T.axis + T.order :])
        n = axis if axis < T.axis else axis - T.order + 1
        return _mtkrprod_single_for_array(T._data, factors, n, conjugate)


@_mtkrprod_all.register
def _mtkrprod_all_for_hankel(
    T: HankelTensor, U: Sequence[MatrixType], conjugate: bool = True
) -> Sequence[MatrixType]:
    N = T._data.shape[T.axis]

    # For the Hankel modes, the FFT of the reversed signal is needed. To avoid FFTs, we
    # perform the time reversal in the FFT domain for the non-Hankel modes here. By
    # combining all shifts, the shift becomes 1.
    Ufft = tuple(fft(u[::-1, :], N, axis=0) for u in U[T.axis : T.axis + T.order])
    factor = np.conj(np.multiply.reduce(Ufft))
    factor *= np.reshape(np.exp(2j * np.pi * np.arange(N) / N), (-1, 1))
    factor = np.conj(ifft(factor, N, axis=0))
    if not np.iscomplexobj(U[0]) and not np.iscomplexobj(T._data):
        factor = np.real(factor)
    factors = tuple(U[: T.axis]) + (factor,) + tuple(U[T.axis + T.order :])

    if len(factors) > 1:
        results = _mtkrprod_all(T._data, factors, conjugate=conjugate)
    else:
        results = (T._data.reshape((-1, 1)),)

    def fix_hankel_modes(
        results: Sequence[MatrixType],
    ) -> Generator[MatrixType, None, None]:
        for n, M in enumerate(results):
            if n != T.axis:
                yield M
                continue
            Mfft = fft(M.conj() if conjugate else M, N, axis=0)
            for i in range(T.order):
                factor = np.multiply.reduce(Ufft[:i] + Ufft[i + 1 :])
                factor = ifft(Mfft * factor, N, axis=0)
                if not np.iscomplexobj(U[0]) and not np.iscomplexobj(T._data):
                    factor = np.real(factor)
                result = factor[-U[n + i].shape[0] :]
                yield result.conj() if conjugate else result

    return list(fix_hankel_modes(results))


@frob.register
def _frob_for_hankel(T: HankelTensor, squared=False) -> float:
    hankel_shape = T.shape[T.axis : T.axis + T.order]
    N = T._data.shape[T.axis]
    fft_ones = tuple(fft(np.ones((s,)), N) for s in hankel_shape)
    weights = np.round(np.real(ifft(np.multiply.reduce(fft_ones))))

    data2 = np.abs(T._data) ** 2
    norm = np.sum(np.tensordot(data2, weights, (T.axis, 0)))
    return cast(float, norm if squared else np.sqrt(norm))


@_mtkronprod_single.register
def _mtkronprod_single_for_hankel(
    T: HankelTensor,
    U: Sequence[MatrixType],
    axis: int,
    transpose: Literal["T", "H"] | None = None,
) -> MatrixType:
    if transpose:
        if transpose == "T":
            U = tuple(u.T for u in U)
        else:
            U = tuple(u.conj().T for u in U)

    N = T._data.shape[T.axis]
    if T.axis <= axis < T.axis + T.order:
        factors = tuple(u for n, u in enumerate(U) if not T.axis < n < T.axis + T.order)
        tmp = _mtkronprod_single(T._data, factors, T.axis)
        tmp = fft(tmp, axis=0)
        for n in reversed(range(T.axis, T.axis + T.order)):
            if n == axis:
                continue
            tmp = krr(fft(U[n][::-1, :].conj(), N, axis=0), tmp)
        M = ifft(tmp, axis=0)[-U[axis].shape[0] :]
        if not np.iscomplexobj(U[0]) and not np.iscomplexobj(T._data):
            M = np.real(M)
        if T.axis != 0:
            order = (
                (0,)
                + tuple(range(T.order, T.order + T.axis))
                + tuple(range(1, T.order))
                + tuple(range(T.order + T.axis, T.ndim))
            )
            M_shape = (T.shape[axis],) + tuple(
                u.shape[1] for n, u in enumerate(U) if n != axis
            )
            shape = tuple(M_shape[i] for i in argsort(order))
            M = np.reshape(M, shape)
            M = np.transpose(M, order)
            M = np.reshape(M, (M.shape[0], -1))
        return M
    else:
        factor = fft(U[T.axis], N, axis=0)
        for u in U[T.axis + 1 : T.axis + T.order]:
            factor = krr(factor, fft(u, N, axis=0))
        factor = ifft(factor, N, axis=0)
        if not np.iscomplexobj(U[0]) and not np.iscomplexobj(T._data):
            factor = np.real(factor)
        factors = tuple(U[: T.axis]) + (factor,) + tuple(U[T.axis + T.order :])
        n = axis if axis < T.axis else axis - T.order + 1
        return _mtkronprod_single(T._data, factors, n)


def _is_hankel_axis(T: HankelTensor, axis: int) -> bool:
    """Return True if axis is a Hankelized axis."""
    return T.axis <= axis < T.axis + T.order


def _tmprod_hankel_mode(T, matrices, axes: Axis) -> ArrayType:
    """Tensor-matrix products in Hankel modes."""
    if len(axes) < T.order - 1:
        return cast(ArrayType, _tmprod(np.array(T), matrices, axes))

    if len(axes) == T.order:
        selected_axes = axes[:-1]
        selected_matrices = matrices[:-1]
        fft_axis = axes[-1]
    else:
        selected_axes = axes
        selected_matrices = matrices
        fft_axis = tuple(set(range(T.axis, T.axis + T.order)) - set(axes))[0]

    N = T._data.shape[T.axis]
    Ufft = tuple(fft(u[:, ::-1], N, axis=1) for u in selected_matrices)
    result = np.expand_dims(fft(T._data, N, axis=T.axis), selected_axes)
    for n, u in zip(axes, Ufft):
        extra_dims = tuple(set(range(T.ndim)) - set({n, fft_axis}))
        if n < fft_axis:
            result = result * np.expand_dims(u, extra_dims)
        else:
            result = result * np.expand_dims(u.T, extra_dims)
    result = ifft(result, N, axis=fft_axis)
    result = np.take(result, range(-T.shape[fft_axis], 0), axis=fft_axis)
    if not np.iscomplexobj(matrices[0]) and not np.iscomplexobj(T._data):
        result = np.real(result)

    if len(axes) == T.order:
        return cast(ArrayType, _tmprod_array(result, (matrices[-1],), (axes[-1],)))
    return result


@_tmprod.register
def _tmprod_hankel(
    T: HankelTensor, matrices: Sequence[MatrixType], axes: Axis
) -> TensorType:
    normal_axes = tuple(n for n in axes if not _is_hankel_axis(T, n))
    hankel_axes = tuple(n for n in axes if _is_hankel_axis(T, n))

    if not hankel_axes:
        axes = tuple(n if n < T.axis else n - T.order + 1 for n in axes)
        data = cast(ArrayType, _tmprod(T._data, matrices, axes))
        return HankelTensor.from_data_like(T, data)

    if not normal_axes:
        return _tmprod_hankel_mode(T, matrices, axes)

    old_shape = tuple(T.shape[n] for n in axes if not _is_hankel_axis(T, n))
    new_shape = tuple(
        m.shape[0] for n, m in zip(axes, matrices) if not _is_hankel_axis(T, n)
    )

    if prod(new_shape) < prod(old_shape):
        U = tuple(u for n, u in zip(axes, matrices) if not _is_hankel_axis(T, n))
        normal_axes = tuple(n if n < T.axis else n - T.order + 1 for n in normal_axes)
        data = cast(ArrayType, _tmprod(T._data, U, normal_axes))
        result = HankelTensor(data, order=T.order, axis=T.axis)

        Uhankel = tuple(u for n, u in zip(axes, matrices) if _is_hankel_axis(T, n))
        return _tmprod_hankel_mode(result, Uhankel, hankel_axes)

    Uhankel = tuple(u for n, u in zip(axes, matrices) if _is_hankel_axis(T, n))
    array = _tmprod_hankel_mode(T, Uhankel, hankel_axes)
    U = tuple(u for n, u in zip(axes, matrices) if not _is_hankel_axis(T, n))
    return _tmprod(array, U, normal_axes)


def hankelize(
    data: ArrayType,
    order: PositiveInt = 2,
    axis: int = 0,
    breakpoints: int | tuple[int, ...] | None = None,
    prepend_zeros: NonnegativeInt = 0,
    append_zeros: NonnegativeInt = 0,
) -> ArrayType:
    """Hankelize data.

    A Hankel tensor is a generalization of a Hankel matrix to higher orders, i.e., two
    or more axes. For the second-order case, i.e., a Hankel matrix, the anti-diagonals
    are constant, while for the higher-order case the 'anti-diagonal hyperplanes' are
    constant. For example, for a third-order Hankelization ``H`` of a generating vector
    `data`, it holds that::

        H[i, j, k] = data[i +j + k - 3].

    Several signals can be Hankelized simultaneously along an axis `axis` by providing a
    generating array `data`, i.e., all mode-`axis` vectors are converted into Hankel
    tensors with `order` dimensions.

    Parameters
    ----------
    data : ArrayType
        The array to Hankelize.
    order : PositiveInt, default = 2
        Hankelization order of each vector.
    axis : int, default = 0
        The axis along which Hankelization is performed.
    breakpoints : int | tuple[int, ...], optional
        The ``order - 1`` break points for the Hankelization process. Let ``v`` be a
        mode-`axis` vector of `data`, and ``H`` its Hankelization, then::

            H[:, 0, ..., 0] = v[: breakpoints[0] + 1]
            H[-1, :, 0, ..., 0] = v[breakpoints[0] : breakpoints[1] + 1]
            ...
            H[-1, ..., -1, :] = v[breakpoints[-1] :]

        By default, the break points are chosen to make ``H`` as square/cubical as
        possible with the smaller dimensions at most 1 smaller than the larger ones.
    prepend_zeros : NonnegativeInt, default = 0
        Number of zeros to add before each vector in `data` along axis `axis`.
    append_zeros : NonnegativeInt, default = 0
        Number of zeros to add after each vector in `data` along axis `axis`.

    Returns
    -------
    ArrayType
        The Hankelized data.

    See Also
    --------
    HankelTensor

    Notes
    -----
    This function is equivalent to ``np.array(HankelTensor(...))``. To improve memory
    and computational efficiency, it is advised to use :class:`.HankelTensor` directly.
    """
    return np.array(
        HankelTensor(data, order, axis, breakpoints, prepend_zeros, append_zeros)
    )


def dehankelize(
    data: TensorType,
    axis: int = 0,
    order: PositiveInt = 2,
    method: Literal["fiber"] | AxisSummaryFcn = "fiber",
) -> ArrayType:
    """Extract generators of a Hankel tensor.

    The signal generating the given `data` is extracted, assuming that `data` is a
    Hankelized array. If `data` is not a Hankelized array, then the Hankel tensor
    generated using the extracted generator will not be exactly equal to `data`.

    From some tensor types, such as :class:`.PolyadicTensor` the generating signal can
    be extracted without constructing the array first.

    Parameters
    ----------
    data : TensorType
        Array from which the generating signal is extracted.
    axis : int, default = 0
        First of the Hankelized axes. Default is 0.
    order : PositiveInt, default = 0
        Order of the Hankelization. Default is 2.
    method : "fiber" | AxisSummaryFcn, default = "fiber"
        Method used to extract the generating values of a Hankel tensor. This is only
        supported for `data` of type :class:`numpy.ndarray` and ignored otherwise. The
        method ``"fiber"`` extracts the vectors ::

            data[:, 0, ..., 0]
            data[-1, :, 0, ..., 0]
            data[-1, -1, :, 0, ..., 0]
            ...
            data[-1, ..., -1, :]

        to reconstruct the generating values. (Assuming ``axis = 0`` and ``order =
        data.ndim``, if not, this is repeated for every subtensor.) If an axis summary
        function is provided, each 'anti-diagonal hyperplane' is passed to `method` as
        an array of order ``data.ndim - order + 1``. See :class:`AxisSummaryFcn` for
        more details.

    Returns
    -------
    ArrayType
        The signal (array) generating the Hankel tensor `data`.

    See Also
    --------
    HankelTensor.from_array, HankelTensor.from_polyadic

    Examples
    --------
    >>> import numpy as np
    >>> import pytensorlab as tl

    >>> data = np.array([[1, 2, 3], [2, 3, 4]])
    >>> tl.dehankelize(data)
    array([1, 2, 3, 4])

    >>> data = np.array([[[1, 2, 3], [2, 3, 4]], [[5, 6, 7], [6, 7, 8]]])
    >>> tl.dehankelize(data, axis=1, method=np.mean)
    array([[1., 2., 3., 4.],
           [5., 6., 7., 8.]])

    >>> factors = ([[1, 1], [2, 0.5], [4, 0.25]],) * 3
    >>> data = tl.PolyadicTensor(factors)
    >>> tl.dehankelize(data, order=3)
    array([ 2.      ,  2.5     ,  4.25    ,  8.125   , 16.0625  , 32.03125 ,
           64.015625])
    """
    if order < 2:
        raise ValueError("order should be at least 2")
    if axis >= 0:
        if axis > data.ndim - order:
            raise ValueError("axis should be between 0 <= axis <= data.ndim - order")
    elif axis < 0:
        axis += data.ndim
        if axis > data.ndim - order:
            raise ValueError("axis should be between -data.ndim <= axis <= -order")
    return _dehankelize(data, axis, order, method)


@singledispatch
def _dehankelize(
    data: TensorType, axis: int = 0, order: PositiveInt = 2, _: Any = None
) -> ArrayType:
    return _dehankelize_ndarray(np.array(data), axis, order)


@_dehankelize.register
def _dehankelize_ndarray(
    data: np.ndarray,
    axis: int = 0,
    order: PositiveInt = 2,
    method: Literal["fiber"] | AxisSummaryFcn = "fiber",
) -> ArrayType:

    pre = (slice(None),) * axis
    shape = data.shape[axis : axis + order]
    if method == "fiber":
        indices = tuple(tuple(range(min(n, 1), s)) for n, s in enumerate(shape))
        indices = tuple(
            (0,) * sum(map(len, indices[:n]))
            + index
            + (-1,) * sum(map(len, indices[n + 1 :]))
            for n, index in enumerate(indices)
        )
        result = data[pre + indices]
    else:  # Use a custom function on every 'anti-diagonal' (can be an array)
        ind = product(*tuple(range(s) for s in shape))
        subs = groupby(iter(sorted(ind, key=sum)), key=sum)
        hdata = (method(data[pre + tuple(zip(*sub))], axis=axis) for _, sub in subs)
        result = np.stack(tuple(hdata), axis=axis)

    return result


@_dehankelize.register
def _dehankelize_polyadic(
    data: PolyadicTensor,
    axis: int = 0,
    order: PositiveInt = 2,
    _: Any = None,
) -> ArrayType:
    shape = data.shape[axis : axis + order]
    N = sum(shape) - order + 1
    hankel_factors = data.factors[axis : axis + order]
    new_factor = np.multiply.reduce(tuple(fft(u, N, 0) for u in hankel_factors))
    new_factor = ifft(new_factor, N, 0)
    if not np.iscomplexobj(data):
        new_factor = np.real(new_factor)
    # Take counts of each entry into account.
    fft_ones = tuple(fft(np.ones((s,)), N) for s in shape)
    weights = np.round(np.real(ifft(np.multiply.reduce(fft_ones))))
    new_factor = new_factor / np.reshape(weights, (-1, 1))

    new_factors = data.factors[:axis] + (new_factor,) + data.factors[axis + order :]
    return np.array(PolyadicTensor(new_factors))


def dehankelize_terms(
    data: PolyadicTensor, axis: int = 0, order: PositiveInt = 2
) -> PolyadicTensor:
    """Extract generators of rank-1 terms representing Hankel tensors.

    Given a polyadic tensor, each rank-1 term is dehankelized separately; see
    :func:`.dehankelize` for more details. The generators are returned as a
    :class:`.PolyadicTensor` in which the factor ``generator.factors[axis]`` contains
    the generators for the Hankelized axes ``range(axis, axis + order)``. All other
    factors are identical to the corresponding (non-Hankelized) factors in `data`.

    Parameters
    ----------
    data : PolyadicTensor
        Polyadic tensor from which the generating signal is extracted.
    axis : int, default = 0
        First of the Hankelized axes. Default is 0.
    order : PositiveInt, default = 2
        Order of the Hankelization. Default is 2.

    Returns
    -------
    generator : PolyadicTensor
        The signal and mixing matrices generating the Hankel tensor `data`.

    See Also
    --------
    dehankelize

    Examples
    --------
    Consider a mixture ``X = S @ M.T`` in which ``S`` is a matrix containing exponential
    signals in the columns and ``M.T`` is the unknown mixing matrix. Via Hankelization,
    a canonical polyadic decomposition, and dehankelization, ``S`` can be recovered from
    ``X``:

    >>> import numpy as np
    >>> import pytensorlab as tl

    >>> t = np.arange(0, 1.1, 0.1)  # time points
    >>> S = np.exp(np.outer(t, np.array([1, 2, 3, 4])))  # four exponentials
    >>> print(S)
    [[ 1.          1.          1.          1.        ]
     [ 1.10517092  1.22140276  1.34985881  1.4918247 ]
     [ 1.22140276  1.4918247   1.8221188   2.22554093]
     [ 1.34985881  1.8221188   2.45960311  3.32011692]
     [ 1.4918247   2.22554093  3.32011692  4.95303242]
     [ 1.64872127  2.71828183  4.48168907  7.3890561 ]
     [ 1.8221188   3.32011692  6.04964746 11.02317638]
     [ 2.01375271  4.05519997  8.16616991 16.44464677]
     [ 2.22554093  4.95303242 11.02317638 24.5325302 ]
     [ 2.45960311  6.04964746 14.87973172 36.59823444]
     [ 2.71828183  7.3890561  20.08553692 54.59815003]]
    >>> M = tl.random.randn((3, 4))  # mixing matrix
    >>> X = S @ M.T  # mixed signal
    >>> H = tl.hankelize(X)
    >>> Hres, _ = tl.cpd(H, 4, print_steps=False)
    >>> generator = tl.dehankelize_terms(Hres)  # random
    >>> generator.factors[0] / generator.factors[0][0, :]  # random
    array([[ 1.        ,  1.        ,  1.        ,  1.        ],
           [ 1.4918247 ,  1.34985881,  1.22140276,  1.10517092],
           [ 2.22554093,  1.8221188 ,  1.4918247 ,  1.22140276],
           [ 3.32011692,  2.45960311,  1.8221188 ,  1.34985881],
           [ 4.95303242,  3.32011692,  2.22554093,  1.4918247 ],
           [ 7.3890561 ,  4.48168907,  2.71828183,  1.64872127],
           [11.02317638,  6.04964746,  3.32011692,  1.8221188 ],
           [16.44464677,  8.16616991,  4.05519997,  2.01375271],
           [24.5325302 , 11.02317638,  4.95303242,  2.22554093],
           [36.59823444, 14.87973172,  6.04964746,  2.45960311],
           [54.59815003, 20.08553692,  7.3890561 ,  2.71828183]])

    Note that the signal is recovered up to scaling and permutation of the columns.
    """
    if order < 2:
        raise ValueError("order should be at least 2")
    if axis >= 0:
        if data.ndim < order:
            raise ValueError(f"order should be at most {data.ndim}")
        if axis > data.ndim - order:
            raise ValueError("axis should be between 0 <= axis <= data.ndim - order")
    elif axis < 0:
        axis += data.ndim
        if axis > data.ndim - order:
            raise ValueError("axis should be between -data.ndim <= axis <= -order")

    ST = PolyadicTensor(data.factors[axis : axis + order])
    S = np.vstack(
        tuple(_dehankelize_polyadic(term, 0, order) for term in ST.term_iter())
    )
    factors = (
        tuple(f for f in data.factors[:axis])
        + (S.T,)
        + tuple(f for f in data.factors[axis + order :])
    )
    if len(factors) == 1:
        factors += (np.ones((1, ST.nterm), dtype=factors[0].dtype),)
    return PolyadicTensor(factors)

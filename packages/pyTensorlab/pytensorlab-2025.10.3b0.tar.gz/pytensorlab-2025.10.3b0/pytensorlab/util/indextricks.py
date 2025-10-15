"""Manipulate and normalize indices and axes."""

import itertools as it
import math
import numbers
import warnings
from collections.abc import Generator, Iterable, Sequence
from typing import Any, TypeVar, cast

import numpy as np

from ..typing.core import (
    Axis,
    AxisLike,
    BasicIndex,
    IndexLike,
    IndexType,
    NonBasicIndex,
    NormalizedAdvancedIndexType,
    NormalizedBasicIndexType,
    NormalizedIndexType,
    Sequenceable,
    Shape,
    ShapeLike,
)

T = TypeVar("T")


def findfirst(array: Iterable[bool]) -> int:
    """Find index of first True entry.

    Parameters
    ----------
    array : Iterable[bool]
            Boolean array to loop over.

    Returns
    -------
    int
        Index of first True entry.

    Raises
    ------
    KeyError
        None of the entries of array is True.
    """
    res = next((i for i, a in enumerate(array) if a), None)
    if res is None:
        raise KeyError("no entry is True")
    return res


def _ensure_sequence(seq: Sequenceable[T]) -> Sequence[T]:
    """Ensure that the result is a sequence.

    If a single element of a sequence is given as such, and is therefore not iterable,
    convert it to tuple with only that element.

    Returns
    -------
    Sequence[T]
        seq if seq is iterable, otherwise (seq,).
    """
    try:
        iter(seq)  # type: ignore
    except TypeError:
        seq = (cast(T, seq),)
    return cast(Sequence[T], seq)


def _ensure_tuple(seq: Sequenceable[T]) -> tuple[T, ...]:
    """Ensure that the result is a tuple.

    If a single element of a sequence is given as such, and is therefore not iterable,
    convert it to tuple with only that element.

    Returns
    -------
    tuple[T, ...]
        seq if seq is iterable, otherwise (seq,).
    """
    try:
        seq = tuple(seq)  # type:ignore
    except TypeError:
        seq = (cast(T, seq),)
    return cast(tuple[T, ...], seq)


def _ensure_positive_sequence(
    seq: Sequenceable[int], upperbound: int
) -> tuple[int, ...]:
    """Return a sequence of positive numbers.

    A number or a sequence of numbers is converted into a sequence with only positive
    entries. If an entry is negative, `upperbound` is added. The value or all
    entries in `seq` should be in ``range(-upperbound, upperbound)``.

    Parameters
    ----------
    seq : Sequenceable[int]
        Integer or sequence of integers.
    upperbound : int
        Maximal allowed value for any sequence element.

    Returns
    -------
    tuple[int,...]
        Tuple of positive numbers.

    Examples
    --------
    Create a positive index for selecting items in a list with 10 entries:
    >>> _ensure_positive_sequence((-5, 2), 10)
    (5, 2)

    Notes
    -----
    Input arguments are not checked for performance reasons.
    """
    return tuple(i if i >= 0 else upperbound + i for i in _ensure_sequence(seq))


def _ensure_positive_basic_index(
    key: Sequence[NormalizedBasicIndexType], shape: Shape
) -> tuple[NormalizedBasicIndexType, ...]:
    """Return a sequence of indices that are positive.

    Parameters
    ----------
    key : Sequence[NormalizedIndexType, ...]
        Sequence of indices to be made positive.
    shape : Shape
        Shape of the tensor on which the indexing is performed.

    Returns
    -------
    tuple[NormalizedIndexType, ...]
        Sequence of positive indices.

    Examples
    --------
    The following sequence of indices is transformed to the corresponding positive
    indices:

    >>> _ensure_positive_basic_index((-1, (-1, -2), (-2, -4)), (3, 4, 5))
    (2, (3, 2), (3, 1))
    """

    def _make_positive() -> Generator[NormalizedBasicIndexType, None, None]:
        """Return the positive version of an index."""
        shape_iter = iter(shape)
        for k in key:
            if k is not None:
                s = next(shape_iter)
            else:
                yield None
                continue
            if isinstance(k, int):
                yield k + s if k < 0 else k
            elif isinstance(k, tuple):
                yield tuple(i if i >= 0 else i + s for i in k)
            else:
                yield k

    return tuple(_make_positive())


def _ensure_positive_advanced_index(
    key: Sequence[NormalizedAdvancedIndexType], shape: Shape
) -> tuple[NormalizedAdvancedIndexType, ...]:
    def _make_positive() -> Generator[NormalizedAdvancedIndexType, None, None]:
        """Return the positive version of an index."""
        shape_iter = iter(shape)
        for k in key:
            if k is not None:
                s = next(shape_iter)
            else:
                yield None
                continue
            if isinstance(k, int):
                yield k + s if k < 0 else k
            elif isinstance(k, np.ndarray):
                yield np.where(k < 0, k + s, k)
            elif isinstance(k, list):
                yield [i if i >= 0 else i + s for i in k]
            else:
                yield k

    return tuple(_make_positive())


def _ensure_mutex_axis_permutation(
    row: Sequenceable[int], col: Sequenceable[int] | None, ndim: int
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Ensure mutually exclusive axis permutation.

    The axes in `row` and `col` are normalized such that all axes are in
    ``range(ndim)``. Exceptions are raised when `row` and `col` share indices or the
    their combination is not a permutation of ``range(ndim)``. If
    ``len(row) + len(col) < ndim``, `col` is extended with the remaining axes in
    ``range(ndim)``.

    Parameters
    ----------
    row : Sequenceable[int]
        Axis or sequence of axes.
    col : Sequenceable[int], optional
        Axis or sequence of axes.
    ndim : int
        Number of axes.

    Raises
    ------
    ValueError
        `row` and `col` share at least one axis.
    ValueError
        Together, `row` and `col` are not a permutation of ``range(ndim)``.
    """
    row = _ensure_positive_sequence(row, ndim)
    col = () if col is None else col
    col = _ensure_positive_sequence(col, ndim)
    col = col + tuple(i for i in range(ndim) if i not in row + col)
    idx = next((i for i in row if i in col), None)
    if idx is not None:
        raise ValueError(f"row and col both contain axis {idx}")
    if len(row) + len(col) != ndim or any(
        i != j for i, j in zip(sorted(row + col), range(ndim))
    ):
        raise ValueError(
            f"the row and col axes are not a permutation of 0:ndim with ndim = {ndim}"
        )

    return row, col


def normalize_axes(
    axes: AxisLike | None,
    ndim: int,
    *,
    norepeat: bool = True,
    ispermutation: bool = False,
    fill: bool = True,
    fillreversed: bool = False,
) -> Axis:
    """Normalize sequence of axes.

    The given axes are normalized such that the result is a (potentially empty) tuple of
    integers in ``range(ndim)``. Negative axes are converted to positive ones before any
    checks are done.

    Parameters
    ----------
    axes : AxisLike, optional
        Axes to be normalized.
    ndim : int
        The maximal (potential) value for any axis in `axes`. This typically is the
        number of dimensions of an array.
    norepeat : bool, default = True
        Raise a ValueError if `axes` contains repeated axes.
    ispermutation : bool, default = False
        Raise a ValueError if `axes` is not a permutation of ``range(ndim)``.
    fill : bool, default = True
        Append axes not in ``range(ndim)`` for smallest to largest.
    fillreversed : bool, default = False
        If fill is True, append axes not in ``range(ndim)`` from largest to smallest.

    Returns
    -------
    Axis
        Normalized axes.

    Raises
    ------
    ValueError
        If `norepeat` is True and `axes` contains repeated axes.
    ValueError
        If `ispermutation` is True and `axes` is not a permutation of ``range(ndim)``.
    ValueError
        If any axis is not within ``range(-ndim, ndim)``.
    """
    if axes is None:
        axes = ()
    if not isinstance(axes, Sequence):
        axes = (axes,)
    axes = tuple(ax if ax >= 0 else ndim + ax for ax in axes)

    uniqueaxes = set(axes)
    if norepeat and len(uniqueaxes) < len(axes):
        raise ValueError("axes cannot contain repeated indices")
    if ispermutation and sorted(axes) != list(range(ndim)):
        raise ValueError(f"axes is not a permutation of range({ndim})")
    if any(not 0 <= ax < ndim for ax in axes):
        idx = findfirst(not 0 <= ax < ndim for ax in axes)
        raise ValueError(
            f"entry {idx} of axes is out of bounds: {axes[idx]} is not in range({ndim})"
        )
    if fill:
        allaxes: Iterable[int] = reversed(range(ndim)) if fillreversed else range(ndim)
        axes += tuple(cast(int, ax) for ax in allaxes if ax not in uniqueaxes)
    return axes


def _complement_indices(ind: AxisLike, max: int) -> Axis:
    ind = normalize_axes(ind, max, fill=False)
    return tuple(i for i in range(max) if i not in ind)


def _handle_bools(key) -> Generator[Any, None, None]:
    for k, idx in enumerate(key):
        if isinstance(idx, np.ndarray):
            if np.issubdtype(idx.dtype, bool):
                yield from idx.nonzero()
            else:
                yield idx
        elif isinstance(idx, tuple):
            if all(isinstance(i, bool) for i in idx):
                yield tuple(i for i, b in enumerate(idx) if b)
            else:
                yield idx
        elif isinstance(idx, Iterable):
            warnings.filterwarnings("error")
            try:
                arr = np.asarray(idx)
                if np.issubdtype(arr.dtype, bool):
                    yield from arr.nonzero()
                else:
                    yield idx
            except Warning:
                warnings.resetwarnings()
                raise IndexError(
                    f"index {k} is an invalid index: only integers, slices (`:`), "
                    f"ellipsis (`...`), numpy.newaxis (`None`) and integer or "
                    f"boolean arrays are valid indices"
                )
            else:
                warnings.resetwarnings()
        else:
            yield idx


def normalize_index(key: IndexLike, shape: Shape) -> tuple[NormalizedIndexType, ...]:
    """Normalize the indexing format."""
    if not isinstance(key, tuple):
        key = cast(IndexType, (key,))

    key = tuple(_handle_bools(key))

    # Ellipsis, np.newaxes (= None) result in a number of additional axes
    nb_none = sum(idx is None for idx in key)
    has_ellipsis = any(isinstance(k, type(...)) for k in key)
    nb_extra_axes = len(shape) - len(key) + nb_none + has_ellipsis

    if nb_extra_axes < 0:
        raise IndexError(
            f"too many indices for array: array has {len(shape)} dimensions, "
            f"but {len(shape) - nb_extra_axes} are indexed"
        )

    def normalize_key(key, shape: Shape) -> Generator[NormalizedIndexType, None, None]:
        dimension = iter(enumerate(shape))
        for k in key:
            if k is None:
                yield None
                continue
            if isinstance(k, slice):
                # make slices explicit
                _, dim = next(dimension)
                yield slice(*k.indices(dim))
            elif isinstance(k, type(...)):
                # convert ellipsis to explicit slices
                for _ in range(nb_extra_axes):
                    _, dim = next(dimension)
                    yield slice(0, dim, 1)
            else:
                # return int, tuple and list after checking values
                axis, dim = next(dimension)
                k_raveled = np.array(k).ravel()
                if np.max(k_raveled) >= dim or np.min(k_raveled) < -dim:
                    out_of_bounds = [i for i in k_raveled if not -dim <= i < dim]
                    raise IndexError(
                        f"index {out_of_bounds[0]} is out of bounds for axis {axis} "
                        f"with dimension {dim}"
                    )
                yield k
        # return remaining slices in the case ellipsis is last
        for _axis, dim in dimension:
            yield slice(0, dim, 1)

    return tuple(normalize_key(key, shape))


def isbasic(k: Any) -> bool:
    """Check whether an index is basic.

    Parameters
    ----------
    k : Any
        Index to check.

    Returns
    -------
    bool
        Boolean indicating whether the index is basic.
    """
    return isinstance(
        k, slice | numbers.Integral | tuple | type(...) | type(np.newaxis)
    )


def isadvanced(k: Any) -> bool:
    """Check whether an index is advanced.

    A separate function from :func:`isbasic` is needed, since integers are considered
    to be advanced indices when both basic and advanced indices are used simultaneously.

    Parameters
    ----------
    k : Any
        Index to check.

    Returns
    -------
    bool
        Boolean indicating whether the index is advanced.
    """
    return not isinstance(k, type(...) | type(np.newaxis) | slice | tuple)


def split_key_basic(
    key: Sequence[NormalizedIndexType],
) -> tuple[tuple[BasicIndex, ...], tuple[NonBasicIndex, ...]]:
    """Split key in basic and non-basic keys.

    Parameters
    ----------
    key : Sequence[NormalizedIndexType]
        Keys to be split.

    Returns
    -------
    basic_keys : tuple[BasicIndex, ...]
        Basic keys.
    other_keys : tuple[NonBasicKeys, ...]
        Non-basic keys.

    Note
    ----
    Non-basic keys are not identical to advanced keys, hence the terminology non-basic
    keys.
    """
    groups: dict[bool, tuple[Any, ...]] = {True: (), False: ()}
    for k, g in it.groupby(key, isbasic):
        groups[k] += tuple(g)
    return groups[True], groups[False]


def get_advanced_position(key: Sequence[NormalizedIndexType], perm2first: bool) -> int:
    """Determine position of advanced keys.

    Depending on whether advanced indices are contiguous, the advanced indices are moved
    to the beginning (if not) or remain in the same place (if contiguous).
    """
    if perm2first:
        return 0
    for i, k in enumerate(key):
        if not isbasic(k):
            return i
    return 0


def compute_indexed_shape(
    key: Sequence[NormalizedIndexType], perm2first: bool = False
) -> tuple[Shape, Shape]:
    """Compute shape of result after indexing."""
    basic_key, advanced_key = split_key_basic(key)
    broadcast_shape = np.broadcast(*advanced_key).shape
    advanced_idx = get_advanced_position(key, perm2first)

    def shapemap(it: Iterable[Any]) -> Generator[int, None, None]:
        for k in it:
            if isinstance(k, slice):
                yield len(range(k.start, k.stop, k.step))
            elif isinstance(k, tuple):
                yield len(k)
            elif k is None:
                yield 1
            # integers are dropped

    shape = tuple(shapemap(basic_key[:advanced_idx]))
    shape += broadcast_shape
    shape += tuple(shapemap(basic_key[advanced_idx:]))

    return shape, broadcast_shape


def partition_range(lengths: Sequence[int]) -> tuple[tuple[int, ...], ...]:
    """Return subsequent ranges of specified lengths.

    Parameters
    ----------
    lengths : Sequence[int]
        Length of each range.

    Returns
    -------
    tuple[tuple[int, ...], ...]
        Tuple of ranges (as a tuple) starting from the end of the previous range.

    Examples
    --------
    >>> partition_range((2, 3, 1))
    ((0, 1), (2, 3, 4), (5,))
    """
    return tuple(
        tuple(range(start, start + length))
        for start, length in zip(it.accumulate((0,) + tuple(lengths)), lengths)
    )


def _reshape_axes(
    old_shape: Shape, new_shape: ShapeLike
) -> tuple[tuple[int, ...], ...]:
    new_shape = _ensure_sequence(new_shape)
    missing_dim = math.prod(old_shape) // math.prod(new_shape)
    new_shape = tuple(s if s != -1 else -missing_dim for s in new_shape)
    combined_axes: list[tuple[int, ...]] = []
    n: int = 0
    for dim in new_shape:
        current = old_shape[n]
        axes = [n]
        while current < dim:
            n += 1
            current *= old_shape[n]
            axes.append(n)
            if current > dim:
                raise ValueError("reshape only supports combining axes")

        if current != dim:
            raise ValueError("reshape only supports combining axes")

        n += 1
        combined_axes.append(tuple(axes))
    return tuple(combined_axes)


def find_sequence(seq: Sequence[T], subseq: Sequence[T]) -> int:
    """Find sequence in another sequence.

    Parameters
    ----------
    seq : Sequence[T]
        Sequence in which the subsequence is sought.
    subseq : Sequence[T]
        Sequence to look for.

    Returns
    -------
    int
        Index at which `subseq` starts in `seq`. If not found, return -1.
    """
    n = len(subseq)
    for i in range(len(seq) - n + 1):
        if all(a == b for a, b in zip(seq[i : i + n], subseq)):
            return i
    return -1

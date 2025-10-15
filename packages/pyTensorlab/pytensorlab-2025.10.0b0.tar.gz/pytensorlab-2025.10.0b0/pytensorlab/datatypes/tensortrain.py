"""Tensor-train datatype and core operations.

The :class:`TensorTrainTensor` class implements an efficient representation of a tensor
given in the tensor-train (TT) format, also known as Matrix Product States (MPS). In
this format, each entry of a tensor ``T`` is computed as the product of ``T.ndim``
slices from the ``T.ndim`` core tensors ``T.cores``. Let ``N = T.ndim - 1``, then::

    T[i0, i1, i2, ..., iN] = T.cores[0][i0, :] @ T.cores[1][:, i1, :].squeeze()
                             @ T.cores[:, i2, :].squeeze() @ ... @ T.cores[N][:, iN]

Hence, by storing two matrices and ``T.ndim - 2`` third-order tensors, every entry can
be constructed. These cores can be accessed via :meth:`.TensorTrainTensor.cores` or
:meth:`.TensorTrainTensor.cores3`, where the latter represents the first and last matrix
as third-order tensors with the first and last dimension are 1, respectively.

Notes
-----
Refer to the TT routines in the :mod:`pytensorlab.algorithms` module for the computation
of a TT.

See Also
--------
.tt_svd, .tt_eig

Examples
--------
Create a random tensor-train tensor:

>>> import pytensorlab as tl
>>> T = tl.TensorTrainTensor.randn((10, 11, 12, 13), (3, 4, 5))
tensor-train tensor of shape (10, 11, 12, 13) with ranks (3, 4, 5)

The cores can be inspected as matrices and tensors, or as tensors:

>>> [core.shape for core in T.cores]
[(10, 3), (3, 11, 4), (4, 12, 5), (5, 13)]
>>> [core.shape for core in T.cores3]
[(1, 10, 3), (3, 11, 4), (4, 12, 5), (5, 13, 1)]

:meth:`~TensorTrainTensor.cores` and :meth:`~TensorTrainTensor.cores3` are the main ways
to interact with the underlying data directly. The tensor can be normalized from left to
right or from right to left such that all but the last (first) core are orthonormal.
This normalization can be done in-place.

>>> T.normalize() # by default in-place and from right to left.
>>> T.cores[-1] @ T.cores[-1].T
array([[ 1.00000000e+00,  3.43499408e-17,  3.24748635e-17,
        -1.44608580e-16, -1.19155921e-16],
       [ 3.43499408e-17,  1.00000000e+00,  4.45473987e-17,
        -2.05990428e-17, -1.23451675e-17],
       [ 3.24748635e-17,  4.45473987e-17,  1.00000000e+00,
         1.04344484e-16, -6.49473791e-18],
       [-1.44608580e-16, -2.05990428e-17,  1.04344484e-16,
         1.00000000e+00,  1.97539216e-16],
       [-1.19155921e-16, -1.23451675e-17, -6.49473791e-18,
         1.97539216e-16,  1.00000000e+00]])

Standard tensor operations such as indexing and slicing, norms, various tensor products
etc. are supported.

>>> T[(1, 3, 7), :, :, np.newaxis, (3, 4)]
tensor-train tensor of shape (3, 11, 12, 1, 2) with ranks (3, 4, 5, 5)
>>> tl.frob(T)
np.float64(1049.0382076434478) # random
>>> tl.inprod(T, T)
1100481.1610957775 # random
>>> T.contract()
np.float64(229.19640513877357) # random

Tensor rounding to a given TT rank or tolerance can be performed via the
:meth:`TensorTrainTensor.round` method:

>>> T.round((2, 3, 4))
tensor-train tensor of shape (10, 11, 12, 13) with ranks (2, 3, 4)

To ease implementation of algorithms, the left and right interface matrices can be
computed as

>>> T.left_interface_matrix(1)
array([[ -52.15335048,   34.71680028, -198.73936544],
       [ -62.69626123,  203.85089766,   64.70217217],
       [ 163.33138332,   48.45093082,  147.8893153 ],
       [-141.39395021, -367.02739225, -483.11572475],
       [ 165.84336371,  134.9625354 ,  149.00319354],
       [-261.69021199, -331.60597228,   14.58841939],
       [  17.53863923,  242.6494112 ,   93.72903562],
       [  32.41009799,  100.53399734,   65.81638155],
       [-131.05587772, -118.08536435,  190.91206235],
       [ 260.71032851,  217.26048243, -235.81822065]]) # random
>>> T.right_interface_matrix(-1)
array([1.]) # random

The product of a tensor unfolding and these interface matrices can be computed directly
using :func:`.tensor_left_right_interface_product`:

>>> a = tl.PolyadicTensor.random(T.shape, nterm=7)
>>> res = tl.tensor_left_right_interface_product(a, T, 2)
>>> res.shape
(4, 12, 5)
"""

import functools as ft
import math
import sys
from collections.abc import Sequence
from typing import (
    Any,
    Literal,
    cast,
    overload,
)

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


import numpy as np
from numpy.typing import ArrayLike, DTypeLike

import pytensorlab.backends.numpy as tlb
from pytensorlab.datatypes.polyadic import PolyadicTensor
from pytensorlab.typing import (
    ArrayType,
    Axis,
    AxisLike,
    NormalizedBasicIndexType,
    NormalizedIndexType,
    Shape,
    SupportsArrayFromShape,
    VectorType,
    isint,
)
from pytensorlab.typing.core import (
    Array3Type,
    MatrixType,
    NumberType,
)
from pytensorlab.typing.validators import PositiveInt
from pytensorlab.util.indextricks import _ensure_sequence, findfirst, normalize_axes

from ..random._utils import _random, _random_like
from ..random.rng import get_rng
from ..util.utils import cumsum, noisy
from .core import (
    _mtkronprod_all,
    _mtkronprod_single,
    _mtkrprod_all,
    _mtkrprod_single,
    _tmprod,
    _tvprod,
    frob,
    tens2mat,
    tmprod,
    tvprod,
)
from .tensor import DenseTensor, Tensor, implements


class TensorTrainTensor(DenseTensor):
    """Represents a tensor as a tensor-train.

    In the tensor-train (TT) format, also known as Matrix Product States (MPS), each
    entry of a tensor ``T`` is computed as the product of ``T.ndim`` slices from the
    ``T.ndim`` core tensors ``T.cores``. Let ``N = T.ndim - 1``, then::

        T[i0, i1, i2, ..., iN] = T.cores[0][i0, :] @ T.cores[1][:, i1, :].squeeze()
                                 @ T.cores[:, i2, :].squeeze() @ ... @ T.cores[N][:, iN]

    Parameters
    ----------
    cores : Sequence[ArrayType]
        Core matrices and tensors or core tensors of the TT tensor.

    Attributes
    ----------
    tt_rank : tuple[PositiveInt, ...]
        tensor-train rank.

    See Also
    --------
    from_vector
        Return a new TT tensor using the cores in vectorized format.
    from_polyadic
        Return a new TT tensor representing a polyadic tensor.
    random
        Generate a TT tensor with random cores.
    randn
        Generate a TT tensor with random cores via the standard normal distribution.
    rand
        Generate a TT tensor with random cores via the uniform distribution.
    zeros
        Create a TT tensor with cores containing all zeros.
    empty
        Create a TT tensor with empty cores.
    random_like
        Generate a TT tensor with random cores with the same shape and type as a given
        array.
    randn_like
        Generate a TT tensor with random cores via the standard normal distribution with
        the same shape and type as a given array.
    rand_like
        Generate a TT tensor with random cores via the uniform distribution with the
        same shape and type as a given array.
    zeros_like
        Create a TT tensor with cores containing all zeros with the same shape and type
        as a given array.
    empty_like
        Create a TT tensor with empty cores with the same shape and type as a given
        array.

    Examples
    --------
    Create a fourth-order tensor with TT ranks `(2, 3, 4)` from a random matrix, two
    random core tensors and a random matrix:

    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> randn = tl.get_rng(31415).standard_normal
    >>> cores = (randn((10, 2)), randn((2, 11, 3)), randn((3, 12, 4)), randn((4, 13)))
    >>> tl.TensorTrainTensor(cores)
    tensor-train tensor of shape (10, 11, 12, 13) with TT ranks (2, 3, 4)

    Alternatively, the first and last matrix can be given as a third-order tensor, which
    makes several operations easier to implement:

    >>> cores = (randn((1, 5, 2)), randn((2, 6, 3)), randn((3, 7, 4)), randn((4, 8, 1)))
    >>> tl.TensorTrainTensor(cores)
    tensor-train tensor of shape (5, 6, 7, 8) with ranks (2, 3, 4)
    """

    def __init__(self, cores: Sequence[ArrayType]) -> None:
        if len(cores) < 1:
            raise ValueError(
                f"too few cores: got {len(cores)}, but expected at least 1"
            )
        if any(not isinstance(f, np.ndarray) for f in cores):
            cores = [np.asarray(core) for core in cores]

        if len(cores) == 1:
            if cores[0].ndim == 1:
                core_shapes = [cores[0].shape]
                shape = [cores[0].shape[0]]
            else:
                raise ValueError(
                    f"core 0 should be a vector for len(cores) == 1: "
                    f"shape is {cores[0].shape}"
                )
        elif cores[0].ndim == 3 and cores[0].shape[0] == 1:
            core_shapes = [cores[0].shape[1:]]
            shape = [cores[0].shape[1]]
        elif cores[0].ndim == 2:
            core_shapes = [cores[0].shape]
            shape = [cores[0].shape[0]]
        else:
            raise ValueError(f"core 0 is not a matrix: shape is {cores[0].shape}")

        for n, core in enumerate(cores[1:-1]):
            if core.ndim != 3:
                raise ValueError(
                    f"core {n + 1} is not a third-order tensor: shape is {core.shape}"
                )
            core_shapes.append(core.shape)
            shape.append(core.shape[1])

        if len(cores) > 1:
            if (cores[-1].ndim == 3 and cores[-1].shape[-1] == 1) or cores[
                -1
            ].ndim == 2:
                core_shapes.append(cores[-1].shape[:2])
                shape.append(cores[-1].shape[1])
            else:
                raise ValueError(
                    f"core {len(cores) - 1} is not a matrix: shape is {cores[-1].shape}"
                )

        # If this passes, `core_shapes` is a valid tensor-train
        _validate_core_shapes(core_shapes=core_shapes)

        super().__init__(tuple(shape))
        self._data: VectorType = np.concatenate(tuple(core.ravel() for core in cores))

        tt_rank = tuple(core.shape[0] for core in cores[1:])
        self.tt_rank = tt_rank

        self._core_shapes: tuple[Shape, ...] = tuple(core_shapes)
        self._compute_core_views()

    @classmethod
    def from_vector(
        cls,
        data: ArrayType,
        shape: Shape,
        tt_rank: Sequence[PositiveInt],
        copy: bool = True,
    ) -> Self:
        """Return a new TT tensor using the cores in vectorized format.

        Parameters
        ----------
        data : ArrayLike
            The vectorized core matrices and tensors, concatenated in a vector.
        shape: Shape
            Shape of the new TT tensor.
        tt_rank: Sequence[PositiveInt]
            TT rank of the new TT tensor.
        copy: bool
            If True, the new TT tensor stores an array copy of `data`. Otherwise, it
            stores a view to `data`.

        Returns
        -------
        TensorTrainTensor
            A TT tensor of the given shape and TT rank with cores determined by `data`.
        """
        shape = _ensure_sequence(shape)
        tt_rank = _ensure_sequence(tt_rank)
        core_shapes = _validate_and_compute_shape_and_tt_rank(
            shape=shape, tt_rank=tt_rank
        )

        _validate_core_shapes(core_shapes=core_shapes)

        obj = cls.__new__(cls)
        super().__init__(obj, tuple(shape))

        obj._data = np.asarray(data, copy=copy if copy else None).ravel()
        if isinstance(data, np.ndarray):
            obj.setflags(write=copy or data.flags["WRITEABLE"])

        if obj._data.size != sum(math.prod(core) for core in core_shapes):
            raise ValueError(
                f"size of data does not match the expected number of parameters: size "
                f"is {obj._data.size} while expected "
                f"{sum(math.prod(core) for core in core_shapes)}"
            )

        obj.tt_rank = tuple(tt_rank)
        obj._core_shapes = tuple(core_shapes)
        obj._compute_core_views()
        return obj

    @classmethod
    def from_polyadic(cls, T: PolyadicTensor) -> Self:
        """Return a new TT tensor representing a polyadic tensor.

        Parameters
        ----------
        T : PolyadicTensor
            The polyadic tensor being converted to a TT tensor.

        Returns
        -------
        TensorTrainTensor
            New TT tensor representing the same array as the given polyadic tensor.

        See Also
        --------
        round
            Round to a given TT rank or tolerance.

        Notes
        -----
        All TT ranks are equal to the number of terms ``T.nterm``, which can be
        suboptimal. :meth:`round` can potentially be used to reduce the TT ranks.

        Examples
        --------
        >>> import pytensorlab as tl
        >>> T = tl.PolyadicTensor.random((3, 4, 5), 2)
        >>> tl.TensorTrainTensor.from_polyadic(T)
        tensor-train tensor of shape (3, 4, 5) with TT ranks (2, 2)
        """
        if T.ndim == 1:
            return cls((np.sum(T.factors[0], axis=1),))
        cores = [T.factors[0]]
        eye = np.eye(T.nterm)[:, None, :]
        for factor in T.factors[1:-1]:
            cores.append(factor.T[:, :, None] * eye)
        cores.append(T.factors[-1].T)
        return cls(cores)

    @property
    def dtype(self) -> np.dtype[Any]:
        """Return the data type of the TT tensor.

        Returns
        -------
        numpy.dtype[Any]
            The data type of the TT tensor.
        """
        return self._data.dtype

    @classmethod
    def empty(cls, shape: Shape, tt_rank: Sequence[PositiveInt]) -> Self:
        """Create a TT tensor with empty cores.

        Parameters
        ----------
        shape: Shape
            The dimension of the full tensor.
        tt_rank: Sequence[PositiveInt]
            The TT rank of the tensor-train.

        Returns
        -------
        TensorTrainTensor
            A `TensorTrainTensor` with empty cores.

        See Also
        --------
        numpy.empty
        """
        return cls.random(shape=shape, tt_rank=tt_rank, real=np.empty)

    @classmethod
    def zeros(cls, shape: Shape, tt_rank: Sequence[PositiveInt]) -> Self:
        """Create a TT tensor with cores containing all zeros.

        Parameters
        ----------
        shape: Shape
            The dimension of the full tensor.
        tt_rank: Sequence[PositiveInt]
            The TT rank of the tensor-train.

        Returns
        -------
        TensorTrainTensor
            A `TensorTrainTensor` with cores containing all zeros.

        See Also
        --------
        numpy.zeros
        """
        return cls.random(shape=shape, tt_rank=tt_rank, real=np.zeros)

    @classmethod
    def random(
        cls,
        shape: Shape,
        tt_rank: Sequence[PositiveInt],
        real: SupportsArrayFromShape | None = None,
        imag: SupportsArrayFromShape | bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate a TT tensor with random cores.

        By default, real cores are generated with entries drawn from the uniform
        distribution. The distribution can be changed by providing an alternative random
        number generating function to `real`. Complex factors can be generated by
        setting `imag` to True or by providing a random number generating function to
        `imag`.

        Parameters
        ----------
        shape: Shape
            The shape of the resulting tensor.
        tt_rank: Sequence[PositiveInt]
            The TT rank of the resulting tensor.
        real : SupportsArrayFromShape, optional
            Function that generates random numbers and is used to generate the real part
            of the entries in the core tensors of the resulting tensor. If not given or
            None, the standard uniform distribution is used.
        imag : SupportsArrayFromShape | bool, optional
            Function that generates random numbers and is used to generate the imaginary
            part of the entries in the core tensors of the resulting tensor. If True,
            the imaginary part is generated using the same random number generating
            function as `real`. If not provided, False or None, the entries of the cores
            of the resulting tensor have no imaginary part.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that
            seed. If a generator is provided, it is used directly. If None, the global
            generator (set via :func:`.set_rng`) is used.

        Returns
        -------
        TensorTrainTensor
            A `TensorTrainTensor` with random cores, in which each element is sampled
            from `real` (with an optional imaginary part sampled from `imag`).

        See Also
        --------
        randn
        rand
        random_like
        randn_like
        rand_like
        """
        if real is None:
            real = get_rng(_rng).random

        core_shapes = _validate_and_compute_shape_and_tt_rank(
            shape=shape, tt_rank=tt_rank
        )
        size = sum(math.prod(core) for core in core_shapes)
        data = _random(size, real, imag)
        return cls.from_vector(data=data, shape=shape, tt_rank=tt_rank)

    @classmethod
    def randn(
        cls,
        shape: Shape,
        tt_rank: Sequence[PositiveInt],
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate a TT tensor with random cores via the standard normal distribution.

        Parameters
        ----------
        shape : Shape
            The shape of the tensor.
        tt_rank: Sequence[PositiveInt]
            The TT rank of the resulting tensor.
        imag : bool, optional
            If True, the cores are complex, with the imaginary part also independently
            drawn from a standard normal distribution.
        _rng : numpy.random.Generator | int, default = tl.get_rng()
            Random number generator or random seed to be used.

        Returns
        -------
        TensorTrainTensor
            Random `TensorTrainTensor` with random cores, in which the real and possibly
            imaginary parts of each element are drawn from a standard normal
            distribution.
        """
        _rng = get_rng(_rng)
        return cls.random(shape, tt_rank, real=_rng.standard_normal, imag=imag)

    @classmethod
    def rand(
        cls,
        shape: Shape,
        tt_rank: Sequence[PositiveInt],
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate a TT tensor with random cores via the uniform distribution.

        Parameters
        ----------
        shape : Shape
            The shape of the tensor.
        tt_rank: Sequence[PositiveInt]
            The TT rank of the resulting tensor.
        imag : bool, optional
            If True, the cores are complex, with the imaginary part also independently
            drawn from a standard uniform distribution.
        _rng : numpy.random.Generator | int, default = tl.get_rng()
            Random number generator or random seed to be used.

        Returns
        -------
        TensorTrainTensor
            Random `TensorTrainTensor` with random cores, in which the real and possibly
            imaginary parts of each element are drawn from a standard uniform
            distribution.
        """
        _rng = get_rng(_rng)
        return cls.random(shape, tt_rank, real=_rng.random, imag=imag)

    @classmethod
    def random_like(
        cls,
        array: ArrayLike,
        tt_rank: Sequence[PositiveInt],
        real: SupportsArrayFromShape | None = None,
        imag: SupportsArrayFromShape | bool | None = None,
    ) -> Self:
        """Generate a TT tensor with random cores.

        The shape, dtype and whether the data is complex is inferred from `array`. By
        default, real cores are generated with entries drawn from a uniform
        distribution. The distribution can be changed by providing an alternative random
        number generating function to `real`. Complex factors can be generated by
        setting `imag` to True or by providing a random number generating function to
        `imag`.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too, unless this is
            overruled by `imag`.
        tt_rank: Sequence[PositiveInt]
            The TT rank of the resulting tensor.
        real : SupportsArrayFromShape, optional
            Function that generates random numbers and is used to generate the real part
            of the entries in the core tensors of the resulting tensor. If not given or
            None, the standard uniform distribution is used.
        imag : SupportsArrayFromShape | bool, optional
            Function that generates random numbers and is used to generate the imaginary
            part of the entries in the core tensors of the resulting tensor. If True,
            the imaginary part is generated using the same random number generating
            function as `real`. If not provided, False or None, the entries of the cores
            of the resulting tensor have no imaginary part.

        Returns
        -------
        TensorTrainTensor
            A TT tensor with random cores, in which each element is sampled from `real`
            (with an optional imaginary part sampled from `imag`).

        See Also
        --------
        random
        randn
        rand
        randn_like
        rand_like
        """
        shape = np.shape(array)
        tt_rank_ext = (1,) + tuple(tt_rank) + (1,)
        size = sum(r * i * s for r, i, s in zip(tt_rank_ext, shape, tt_rank_ext[1:]))
        data = _random_like(array, size, real, imag)
        return cls.from_vector(data, shape, tt_rank)

    @classmethod
    def randn_like(
        cls,
        array: ArrayLike,
        tt_rank: Sequence[PositiveInt],
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate a TT tensor with random cores via the standard normal distribution.

        The shape, dtype and whether the data is complex is inferred from `array`. The
        cores are generated with entries drawn from a standard normal distribution.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too, unless this is
            overruled by `imag`.
        tt_rank: Sequence[PositiveInt]
            The TT rank of the resulting tensor.
        imag : bool, optional
            Determine whether the elements of the core tensors have an imaginary part
            which is drawn randomly from the standard normal distribution. If not given,
            the resulting tensor has complex entries if `array` has complex entries.
        _rng : numpy.random.Generator | int, default = tl.get_rng()
            Random number generator or random seed to be used.

        Returns
        -------
        TensorTrainTensor
            A TT tensor with random cores, in which each element is sampled from the
            standard normal distribution (with an optional imaginary part).

        See Also
        --------
        random
        randn
        rand
        random_like
        rand_like
        """
        _rng = get_rng(_rng)
        return cls.random_like(array, tt_rank, real=_rng.standard_normal, imag=imag)

    @classmethod
    def rand_like(
        cls,
        array: ArrayLike,
        tt_rank: Sequence[PositiveInt],
        imag: bool | None = None,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate a TT tensor with random cores via the uniform distribution.

        The shape, dtype and whether the data is complex is inferred from `array`. The
        cores are generated with entries drawn from a uniform distribution.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too, unless this is
            overruled by `imag`.
        tt_rank: Sequence[PositiveInt]
            The TT rank of the resulting tensor.
        imag : bool, optional
            Determine whether the elements of the core tensors have an imaginary part
            which is drawn randomly from the uniform distribution. If not given, the
            resulting tensor has complex entries if `array` has complex entries.
        _rng : numpy.random.Generator | int, default = tl.get_rng()
            Random number generator or random seed to be used.

        Returns
        -------
        TensorTrainTensor
            A TT tensor with random cores, in which each element is sampled from the
            uniform distribution (with an optional imaginary part).

        See Also
        --------
        random
        randn
        rand
        random_like
        randn_like
        """
        _rng = get_rng(_rng)
        return cls.random_like(array, tt_rank, real=_rng.random, imag=imag)

    @classmethod
    def zeros_like(
        cls,
        array: ArrayLike,
        tt_rank: Sequence[PositiveInt],
    ) -> Self:
        """Create a TT tensor with cores containing all zeros.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        tt_rank: Sequence[PositiveInt]
            The TT rank of the resulting tensor.

        Returns
        -------
        TensorTrainTensor
            A TT tensor with cores containing all zeros.

        See Also
        --------
        numpy.zeros_like
        """
        return cls.random_like(array, tt_rank, real=np.zeros)

    @classmethod
    def empty_like(
        cls,
        array: ArrayLike,
        tt_rank: Sequence[PositiveInt],
    ) -> Self:
        """Create a TT tensor with empty cores.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        tt_rank: Sequence[PositiveInt]
            The TT rank of the resulting tensor.

        Returns
        -------
        TensorTrainTensor
            A TT tensor with empty cores.

        See Also
        --------
        numpy.empty_like
        """
        return cls.random_like(array, tt_rank, real=np.empty)

    def _compute_core_views(self) -> None:
        """Compute views of the tensor-train cores.

        Stores views of the different cores.
        """
        bounds = [0] + list(
            cumsum(math.prod(core_shape) for core_shape in self._core_shapes)
        )

        self._cores = tuple(
            self._data[i:j].reshape(*core_shape)
            for (i, j, core_shape) in zip(bounds[:-1], bounds[1:], self._core_shapes)
        )
        core3_shapes: tuple[Shape, ...]
        if len(self._core_shapes) == 1:
            core3_shapes = ((1, self.shape[0], 1),)
        else:
            core3_shapes = (
                ((1, *self._core_shapes[0]),)
                + self._core_shapes[1:-1]
                + ((*self._core_shapes[-1], 1),)
            )
        self._cores3 = tuple(
            self._data[i:j].reshape(*core_shape)
            for (i, j, core_shape) in zip(bounds[:-1], bounds[1:], core3_shapes)
        )

    @property
    def cores(self) -> tuple[ArrayType, ...]:
        """Core matrices and tensors.

        The cores are returned as a tuple of views of the underlying data.

        Returns
        -------
        tuple[ArrayType, ...]
            The cores of the `TensorTrainTensor`, where the first and last core are
            matrices and the remaining cores are third-order arrays.

        See Also
        --------
        cores3
        """
        return self._cores

    @property
    def cores3(
        self,
    ) -> tuple[Array3Type, ...]:
        """Core tensors.

        The cores are returned as a tuple of views of the underlying data. In contrast
        to `cores`, the first and last core are returned as third-order tensors.

        Returns
        -------
        tuple[Array3Type, ...]
            The cores of the `TensorTrainTensor` as third-order arrays.

        See Also
        --------
        cores
        """
        return self._cores3

    @ft.singledispatchmethod
    def __add__(self, T: Any) -> Any:
        return NotImplemented

    def __neg__(self) -> Self:
        T = self.copy()
        T.cores[0][:] *= -1
        return T

    def __sub__(self, other: Any) -> Any:
        return self + (-other)

    def copy(self) -> Self:
        """Return a TensorTrainTensor copy of the given tensor.

        Returns
        -------
        Self
            A copy of the given tensor with the same shape, TT ranks and a copy of the
            data.
        """
        return type(self).from_vector(
            data=self._data, shape=self.shape, tt_rank=self.tt_rank
        )

    def __repr__(self) -> str:
        if Tensor._REPR_MODE != "repr":
            return str(self)
        with np.printoptions(threshold=50, linewidth=88, precision=3, edgeitems=2):
            cores = ",\n".join(map(repr, self.cores))
            return f"{self.__class__.__name__}(\n({cores}),\n)"

    def __str__(self) -> str:
        return f"Tensor-train tensor of shape {self.shape} with TT ranks {self.tt_rank}"

    def transpose(self, axes: AxisLike | None = None) -> Self:
        """Return a tensor with permuted axes.

        Parameters
        ----------
        axes : AxisLike, optional
            If specified, it must be a permutation of ``range(self.ndim)``. The i-th
            axis of the returned tensor will correspond to the axis ``axes[i]`` of the
            input tensor. Negative indexing of these axes is allowed. If `axes` does not
            include all values in ``range(self.ndim)``, the remaining axes are appended
            in decreasing order.

        Returns
        -------
        TensorTrainTensor
            A new TT tensor with permuted axes.

        Notes
        -----
        Due to rounding when swapping core tensors, the resulting TT tensor might not be
        exactly equal to the original tensor compared to the case when the dense array
        would be transposed.
        """
        axes = normalize_axes(axes, self.ndim, fill=True, fillreversed=True)
        swaps_orig = _compute_transpose_swap_order_bubble(axes)
        swaps_reversed = _compute_transpose_swap_order_bubble(axes[::-1])
        if len(swaps_reversed) < len(swaps_orig):
            cores = [core.T for core in self.cores3[::-1]]
            swaps = swaps_reversed
        else:
            cores = list(self.cores3)
            swaps = swaps_orig
        if swaps:
            tol = 1e-15 * frob(self) / len(swaps)
            for axis in swaps:
                cores = _swap_core(cores, axis, tol)
        return type(self)(cores)

    def __array__(self, dtype: DTypeLike = None, copy: bool | None = None) -> ArrayType:
        return _tt_gen(self.cores3, (slice(None),) * self.ndim)

    def _entry(self, indices: Sequence[NormalizedIndexType]) -> ArrayType:
        return _tt_gen(self.cores3, indices)

    def _getitem_sliced(self, key: Sequence[NormalizedBasicIndexType]) -> float | Self:
        # Return a scalar if all indices are integers.
        if all(isint(k) for k in key):
            return _tt_gen(self.cores3, key).item()

        # Build new tensor-train.
        new_cores: list[ArrayType] = []
        dtype = self.dtype
        core_iter = iter(self.cores3)
        for k in key:
            if k is None:
                if new_cores:
                    s = new_cores[-1].shape[-1]
                    new_cores.append(np.eye(s, dtype=dtype)[:, np.newaxis, :])
                else:
                    new_cores.append(np.ones((1, 1, 1), dtype))
            else:
                core = next(core_iter)
                r, _, s = core.shape
                new_cores.append(core[:, k, :].reshape((r, -1, s)))

        # Remove modes if selected using integer.
        squeeze_axes = tuple(i for i, k in enumerate(key) if isint(k))
        final_cores = _squeeze_tt(new_cores, squeeze_axes)
        # The following is always True because the all ints case has been handled above.
        assert isinstance(final_cores, Sequence)
        return type(self)(final_cores)

    def squeeze(self, axes: AxisLike | None = None) -> NumberType | Self:
        """Remove axes of length one.

        Parameters
        ----------
        axes : AxisLike, optional
            Select a subset of axes with length one in the shape. If an axis is selected
            with shape entry greater than one, an exception is raised.

        Returns
        -------
        NumberType | TensorTrainTensor
            Copy of the tensor with all or a subset of the dimensions of length one
            removed. Note that even if no dimensions have been removed, a copy is
            returned, in contrast to :func:`numpy.squeeze`. If all axes are removed, a
            scalar is returned.
        """
        cores_or_number = _squeeze_tt(self.cores3, axes)
        if isinstance(cores_or_number, Sequence):
            return type(self)(cores_or_number)
        return cores_or_number

    def iscomplex(self) -> bool:
        """Check if this tensor has complex elements.

        Returns
        -------
        bool
            True if this tensor has complex elements.
        """
        return tlb.iscomplexobj(self._data)

    def conj(self) -> Self:
        """Return the complex conjugate.

        Returns
        -------
        Self
            If this tensor is complex, a copy with conjugated entries is returned.
            Otherwise, the same tensor is returned.
        """
        if self.iscomplex():
            return type(self).from_vector(
                data=self._data.conj(), shape=self.shape, tt_rank=self.tt_rank
            )
        return self

    def contract(self) -> NumberType:
        """Contract along all axes.

        This tensor is contracted along all axis, i.e., the sum of all entries is
        computed.

        Returns
        -------
        NumberType
            The sum of all tensor entries.
        """
        return ft.reduce(np.matmul, (np.sum(core, 1) for core in self.cores3))[0, 0]

    @overload
    def __mul__(self, T: Self) -> Self: ...

    @overload
    def __mul__(self, T: Tensor) -> ArrayType | Self: ...

    @overload
    def __mul__(self, T: ArrayType) -> ArrayType: ...

    @overload
    def __mul__(self, T: NumberType) -> ArrayType: ...

    @overload
    def __mul__(self, T: Any) -> ArrayType | Self: ...

    @implements(np.multiply)
    def __mul__(self, T: Any) -> ArrayType | Self:
        if not isinstance(T, TensorTrainTensor):
            return np.multiply(self, T)
        if not self.shape == T.shape:
            raise ValueError(
                f"invalid shape of T: got {T.shape} but expected {self.shape}"
            )

        def _products():
            for a, b in zip(self.cores3, T.cores3):
                r, i, s = a.shape
                t, _, u = b.shape
                product = a[:, None, :, :, None] * b[None, :, :, None, :]
                yield product.reshape((r * t, i, s * u))

        return type(self)(list(_products()))

    @overload
    def normalize(
        self, inplace: Literal[True] = ..., left2right: bool = ...
    ) -> Self: ...
    @overload
    def normalize(
        self, inplace: Literal[False] = ..., left2right: bool = ...
    ) -> Self: ...

    def normalize(
        self,
        inplace: bool = True,
        left2right: bool = False,
        stop_at: int | None = None,
    ) -> Self:
        """Normalize by orthogonalizing cores.

        The cores are normalized by orthogonalizing from left to right or from right to
        left.

        Parameters
        ----------
        inplace : bool, default = True
            If True, the data of this tensor is overwritten. Otherwise, a new TT tensor
            is created.
        left2right : bool, default = False
            Orthogonalize from left to right if True; otherwise orthogonalize from right
            to left.
        stop_at : int, optional
            Orthogonalize all cores right (left) of this axis, depending on
            `left2right`. If not given, all except the first (last) are orthogonalized,
            i.e., `stop_at` is ``self.ndim - 1`` if `left2right` is True and ``0``
            otherwise.

        Returns
        -------
        TensorTrainTensor
            If `inplace` is True, the data of the current :class:`TensorTrainTensor` is
            overwritten and the same tensor is returned. If False, a copy is taken and
            the original data remains unchanged.
        """
        if left2right:
            if stop_at is None:
                stop_at = -1
            return self._normalize_left2right(inplace, stop_at=stop_at)
        if stop_at is None:
            stop_at = 0
        return self._normalize_right2left(inplace, stop_at=stop_at)

    def _normalize_right2left(self, inplace: bool = True, stop_at: int = 0) -> Self:
        if stop_at < 0:
            stop_at += self.ndim
        if stop_at == self.ndim - 1:
            return self if inplace else self.copy()
        cores: list[ArrayType] = []  # only used if not inplace
        R = np.ones((1, 1), dtype=self.dtype)
        for core in reversed(self.cores3[stop_at + 1 :]):
            r, i = core.shape[:2]
            s: int = R.shape[0]
            G: ArrayType = (core @ R.T).reshape((r, i * s))
            Q, R = tlb.qr(np.asarray(G.T))
            if inplace and i * s < r:  # tt rank is too high
                Q = np.pad(Q, ((0, 0), (0, r - i * s)))
                R = np.pad(R, ((0, r - i * s), (0, 0)))
            Gorth = Q.T.reshape((Q.shape[1], i, -1))

            if inplace:
                core[:] = Gorth[:]
            else:
                cores.append(Gorth)

        if inplace:
            self.cores[stop_at][:] = contract_trail_lead(self.cores[stop_at], R.T)[:]
            return self
        else:
            cores.append(contract_trail_lead(self.cores[stop_at], R.T))
            for core in reversed(self.cores3[:stop_at]):
                cores.append(core)
            return type(self)(cores[::-1])

    def _normalize_left2right(self, inplace: bool = True, stop_at: int = -1) -> Self:
        if stop_at < 0:
            stop_at += self.ndim
        if stop_at == 0:
            return self if inplace else self.copy()
        cores: list[ArrayType] = []  # only used if not inplace
        R = np.ones((1, 1), dtype=self.dtype)
        for core in self.cores3[:stop_at]:
            r: int = R.shape[1]
            i, s = core.shape[1:]
            G: ArrayType = (R @ core.reshape(r, i * s)).reshape((r * i, s))
            Q, R = tlb.qr(np.asarray(G))
            if inplace and r * i < s:  # tt rank is too high
                Q = np.pad(Q, ((0, 0), (0, s - r * i)))
                R = np.pad(R, ((0, s - r * i), (0, 0)))
            Gorth = Q.reshape((-1, i, Q.shape[1]))

            if inplace:
                core[:] = Gorth[:]
            else:
                cores.append(Gorth)

        if inplace:
            self.cores[stop_at][:] = contract_trail_lead(R, self.cores[stop_at])[:]
            return self
        else:
            cores.append(contract_trail_lead(R, self.cores[stop_at]))
            for core in self.cores3[stop_at + 1 :]:
                cores.append(core)
            return type(self)(cores)

    def left_interface_matrix(self, axis: int) -> ArrayType:
        """Compute the left interface matrix.

        The partial product of the first `axis` core tensors is computed, resulting in
        an array of shape ``(math.prod(shape[:axis]), tt_rank[axis - 1])``. Let
        ``contract(a, b)`` denote the contraction of the last axis of ``a`` and the
        first axis of ``b``, then the computed product is the flattening of::

            contract(...(contract(cores[0], cores[1]), ...), cores[axis - 1])

        Parameters
        ----------
        axis : int
            The first core to exclude, i.e., the product of cores 0 to `axis` minus 1
            (included) is computed.

        Returns
        -------
        ArrayType
            The partial product of the first `axis` minus 1 left cores.
        """
        if axis < 0:
            axis = axis + self.ndim
        if not 0 <= axis < self.ndim:
            raise ValueError(
                f"axis is out of bounds: expected 0 <= axis < {self.ndim}, "
                f"but got {axis}"
            )
        if axis == 0:
            return np.ones((1,), dtype=self.dtype)
        left = self.cores[0]
        for core, r in zip(self.cores[1:axis], self.tt_rank):
            left = left.reshape((-1, r)) @ core.reshape((r, -1))
        return left.reshape((-1, self.tt_rank[axis - 1]))

    def right_interface_matrix(self, axis: int) -> ArrayType:
        """Compute the right interface matrix.

        The partial product of the last core tensors is computed, resulting in
        an array of shape ``(tt_rank[axis], math.prod(shape[axis + 1 :]))``. Let
        ``contract(a, b)`` denote the contraction of the last axis of ``a`` and the
        first axis of ``b``, then the computed product is the flattening of::

            contract(cores[axis + 1], contract(..., contract(cores[-2], cores[-1])))

        Parameters
        ----------
        axis : int
            The last core to exclude, i.e., the product of cores `axis` plus 1 to
            ``self.ndim`` (excluded) is computed.

        Returns
        -------
        ArrayType
            The partial product of the cores starting from `axis` plus 1.
        """
        if axis < 0:
            axis = axis + self.ndim
        if not 0 <= axis < self.ndim:
            raise ValueError(
                f"axis is out of bounds: expected 0 <= axis < {self.ndim}, "
                f"but got {axis}"
            )
        if axis == self.ndim - 1:
            return np.ones((1,), dtype=self.dtype)
        right = self.cores[-1]
        for core in reversed(self.cores[axis + 1 : -1]):
            right = core @ right.reshape((right.shape[0], -1))
        return right.reshape((self.tt_rank[axis], -1))

    def round(
        self,
        rank: Sequence[PositiveInt] | None = None,
        tol: float | None = None,
    ) -> Self:
        """Round to a given TT rank or tolerance.

        An approximation of this tensor is computed based on a given rank or tolerance.

        Parameters
        ----------
        rank : Sequence[PositiveInt], optional
            Upper bound on the TT rank of the rounded result. The TT rank of the output
            can be lower because of theoretical bounds or if the requested `rank` is
            higher than the TT rank of this tensor. If both `rank` and `tol` are not
            provided, the maximal theoretical TT rank is taken.
        tol : float, optional
            Tolerance on the relative Frobenius norm of the error between this tensor
            and the approximation. Ignored if `rank` is given.

        Returns
        -------
        TensorTrainTensor
            Approximation of this tensor rounded to the given `rank` or `tolerance`.
        """
        T = self.normalize(inplace=False)
        cores: tuple[ArrayType, ...] = tuple()
        factor = np.ones((1, 1), dtype=T.dtype)
        if tol is not None:
            tol = tol / math.sqrt(T.ndim - 1) * frob(T)
        if rank is None:
            rank = (math.prod(self.shape),) * (self.ndim - 1)
        else:
            if len(rank) != self.ndim - 1:
                raise ValueError(
                    f"expected {self.ndim - 1} TT ranks, but got {len(rank)}"
                )
            if any(r <= 0 for r in rank):
                raise ValueError(f"expected nonnegative TT ranks, but got {rank}")
            rank = tuple(min(r, s) for r, s in zip(rank, self.tt_rank))
            tol = None
        for core, target_rank in zip(T.cores3[:-1], rank):
            r0, r1 = factor.shape
            i = core.shape[1]
            tmp = (factor @ core.reshape((r1, -1))).reshape((r0 * i, -1))
            U, sv, Vh = tlb.svd(tmp, full_matrices=False)
            if tol is None:
                new_rank = len(sv)
            else:
                new_rank = len(sv) - findfirst(np.cumsum(sv[::-1] ** 2) > tol**2)
            new_rank = min(new_rank, target_rank)
            cores += (U[:, :new_rank].reshape((r0, i, new_rank)),)
            factor = sv[:new_rank, None] * Vh[:new_rank, :]

        cores += ((factor @ T.cores[-1]).reshape((-1, T.cores3[-1].shape[1])),)

        return type(self)(cores)


def _validate_and_compute_shape_and_tt_rank(
    shape: Shape, tt_rank: Sequence[PositiveInt]
) -> Sequence[Shape]:
    """Compute the core shapes if the shape and TT ranks are valid."""
    if len(shape) < 1:
        raise ValueError(f"expected at least a vector, got order {len(shape)}")
    if len(tt_rank) != len(shape) - 1:
        raise ValueError(
            f"expected {len(shape) -1} tensor rank values, got {len(tt_rank)}"
        )
    if 0 in shape:
        raise ValueError(f"shape {shape} contains a zero dimension")
    if 0 in tt_rank:
        raise ValueError(f"TT rank {tt_rank} contains a zero value")

    if len(shape) == 1:
        return ((shape[0],),)

    core_shapes = (
        ((shape[0], tt_rank[0]),)
        + tuple(
            (r1, s, r2) for r1, s, r2 in zip(tt_rank[:-1], shape[1:-1], tt_rank[1:])
        )
        + ((tt_rank[-1], shape[-1]),)
    )
    return core_shapes


def _validate_core_shapes(core_shapes: Sequence[Shape]) -> bool:
    """Check if a sequence of core shapes is valid."""
    if len(core_shapes) == 1 and len(core_shapes[0]) != 1:
        raise ValueError("for 1 dimensional tensor-trains, the tt_rank should be empty")
    if any(0 in r for r in core_shapes):
        idx = findfirst(0 in r for r in core_shapes)
        raise ValueError(
            f"rank {idx} with shape {core_shapes[idx]} contains zero dimension"
        )
    if any(r1[-1] != r2[0] for r1, r2 in zip(core_shapes[:-1], core_shapes[1:])):
        idx = findfirst(
            r1[-1] != r2[0] for r1, r2 in zip(core_shapes[:-1], core_shapes[1:])
        )
        raise ValueError(
            f"ranks {idx}, {idx+1} do not match: "
            f"first dimension of rank {idx+1} is {core_shapes[idx+1][0]}, "
            f"but expected {core_shapes[idx][-1]}"
        )
    return True


def _tt_gen(
    cores: Sequence[ArrayType],
    key: Sequence[NormalizedIndexType],
) -> ArrayType:

    def _new_cores():
        for k, core in zip(key, cores):
            if isinstance(k, slice):
                yield core  # TODO check if this is correct for non slice(None)
            else:
                r, _, s = core.shape
                yield core[:, k, :].reshape((r, -1, s))

    new_cores = _new_cores()
    res = next(new_cores)

    if any(isinstance(k, slice) for k in key):
        for core in new_cores:  # TODO back to front might be more efficient
            r, i, s = core.shape
            res = (res @ core.reshape((r, i * s))).reshape((*res.shape[:-1], i, s))
        return res.reshape(res.shape[1:-1])

    res = res.reshape(res.shape[-2:])
    for core in new_cores:
        res = np.sum(res.T[:, :, None] * core, 0)

    return res.squeeze()


def _squeeze_tt(
    cores: Sequence[ArrayType], axes: AxisLike | None = None
) -> NumberType | Sequence[ArrayType]:
    if axes is None:
        shape = tuple(core.shape[1] for core in cores)
        axes = tuple(k for k, s in enumerate(shape) if s == 1)
    axes = cast(Axis, sorted(_ensure_sequence(axes)))

    prev_core: MatrixType | None = None
    new_cores: list[ArrayType] = []
    for n, core in enumerate(cores):
        if n in axes:
            if core.shape[1] != 1:
                raise ValueError(
                    f"shape[{n}] should be equal to 1; got {core.shape[1]}"
                )
            tmp = core.reshape(core.shape[0], core.shape[2])
            prev_core = tmp if prev_core is None else prev_core @ tmp
        elif prev_core is None:
            new_cores.append(core)
        else:
            tmp = prev_core @ core.reshape(core.shape[0], -1)
            new_cores.append(tmp.reshape((-1, *core.shape[1:])))
            prev_core = None
    if not new_cores:
        assert prev_core is not None
        return prev_core.item()
    if prev_core is not None:
        new_cores[-1] = new_cores[-1] @ prev_core.reshape((-1,))
    return new_cores


@_mtkrprod_single.register
def _mtkrprod_single_tensortrain(
    T: TensorTrainTensor, U: Sequence[MatrixType], axis: int, conjugate: bool = True
) -> MatrixType:
    U, axes = zip(*((u, ax) for ax, u in enumerate(U) if ax != axis))
    R = U[0].shape[1]

    TU = tmprod(T, U, axes, "H" if conjugate else "T")

    left = np.ones((R, 1))
    for core in TU.cores3[:axis]:
        left = np.sum(left.T[:, :, None] * core, axis=0)

    right = np.ones((1, R))
    for core in reversed(TU.cores3[axis + 1 :]):
        right = np.sum(right.T * core, axis=-1)

    return np.sum((TU.cores3[axis] @ right) * left.T[:, None, :], axis=0)


# @_mtkrprod_single.register
def _mtkrprod_single_small_shape_tensortrain(
    T: TensorTrainTensor, U: Sequence[MatrixType], axis: int, conjugate: bool = True
) -> MatrixType:
    # This version is a bit more memory efficient when the shapes are smaller than R.
    U, axes = zip(*((u, ax) for ax, u in enumerate(U) if ax != axis))
    R = U[0].shape[1]

    result = np.empty((T.shape[axis], R), dtype=np.result_type(T.dtype, U[0].dtype))
    for r in range(R):
        Ur = [u[:, r].conj() if conjugate else u[:, r] for u in U]
        result[:, r] = tvprod(T, Ur, axes)

    return result


@_mtkrprod_all.register
def _mtkrprod_all_tensortrain(
    T: TensorTrainTensor, U: Sequence[MatrixType], conjugate: bool = True
) -> Sequence[MatrixType]:
    R = U[0].shape[1]
    TU = tmprod(T, U, range(len(U)), "H" if conjugate else "T")

    left = [np.ones((R, 1))]
    for core in TU.cores3[:-1]:
        left.append(np.sum(left[-1].T[:, :, None] * core, axis=0))

    right = [np.ones((1, R))]
    for core in reversed(TU.cores3[1:]):
        right.append(np.sum(right[-1].T * core, axis=-1))

    return [
        np.sum((T.cores3[n] @ right[-n - 1]) * left[n].T[:, None, :], axis=0)
        for n in range(len(U))
    ]


@_mtkronprod_single.register
def _mtkronprod_single_tensortrain(
    T: TensorTrainTensor,
    U: Sequence[MatrixType],
    axis: int,
    transpose: Literal["T", "H"] | None = None,
) -> MatrixType:
    U, axes = zip(*((u.conj().T, ax) for ax, u in enumerate(U) if ax != axis))
    # Convert to array because `transpose()` does not work yet
    return tens2mat(np.array(tmprod(T, U, axes, transpose)), axis)


@_mtkronprod_all.register
def _mtkronprod_all_tensortrain(
    T: TensorTrainTensor,
    U: Sequence[MatrixType],
    transpose: Literal["T", "H"] | None = None,
) -> Sequence[MatrixType]:
    UH = [u.conj().T for u in U]
    TU = tmprod(T, UH, range(T.ndim), transpose)

    def _products():
        for n in range(T.ndim):
            cores = TU.cores[:n] + (T.cores[n],) + TU.cores[n + 1 :]
            yield tens2mat(np.array(TensorTrainTensor(cores)), n)

    return list(_products())


@_tmprod.register
def _tmprod_tensortrain(
    T: TensorTrainTensor,
    matrices: Sequence[MatrixType],
    axes: Axis,
) -> TensorTrainTensor:
    matiter = iter(matrices)
    cores = [
        tmprod(core, next(matiter), 0 if n == 0 else 1) if n in axes else core
        for n, core in enumerate(T.cores)
    ]
    return TensorTrainTensor(cores)


@_tvprod.register
def _tvprod_tensortrain(
    T: TensorTrainTensor, vectors: Sequence[VectorType], axes: Axis
) -> TensorTrainTensor | VectorType | NumberType:

    def _generate_cores():
        vectoriter = iter(vectors)
        for n, core in enumerate(T.cores3):
            if n in axes:
                yield np.tensordot(core, next(vectoriter), axes=(1, 0))[:, None, :]
            else:
                yield core

    res = _squeeze_tt(tuple(_generate_cores()), axes)
    if len(axes) == T.ndim:
        assert not isinstance(res, Sequence)
        return res
    assert isinstance(res, Sequence)
    if len(axes) == T.ndim - 1:
        return res[0].squeeze()
    return TensorTrainTensor(res)


def _normalize_frob(T: TensorTrainTensor) -> MatrixType:
    """Left to right normalization for Frobenius norm computation.

    Parameters
    ----------
    T : TensorTrainTensor
        The tensor-train tensor to be normalized.

    Returns
    -------
    MatrixType
        The final core of the normalized tensor `T`.

    Notes
    -----
    This is a simplified method only returning the final core.
    """
    R = np.ones((1, 1), dtype=T.dtype)
    for core in T.cores3[:-1]:
        r: int = R.shape[1]
        i, s = core.shape[1:]
        G: ArrayType = (R @ core.reshape(r, i * s)).reshape((-1, s))
        _, R = tlb.qr(np.asarray(G))

    return R @ T.cores[-1]


@frob.register
def _frob_tensortrain(T: TensorTrainTensor, squared: bool = False) -> float:
    core = _normalize_frob(T)
    return frob(core, squared)


def _frob_tensortrain_memory(T: TensorTrainTensor, squared: bool = False) -> float:
    """Compute the Frobenius norm without creating a copy.

    This is an alternative implementation that does not perform normalization first.

    See Also
    --------
    _frob_tensortrain
    """
    res = T.cores[-1] @ T.cores[-1].conj().T
    for core in reversed(T.cores3[:-1]):
        res = (core.conj() @ res.T).reshape(core.shape[0], -1)
        res = core.reshape(core.shape[0], -1) @ res.T
    norm2 = abs(res.item())
    return norm2 if squared else np.sqrt(norm2)


@noisy.register
def _noisy_tensortrain(array: TensorTrainTensor, snr: float, _rng=None):
    return TensorTrainTensor(cores=noisy(array.cores, snr, _rng=_rng))


def contract_trail_lead(a: ArrayType, b: ArrayType) -> ArrayType:
    """Compute a contraction along the trailing and leading axes of two arrays.

    This product is equivalent to::

        numpy.tensordot(a, b, axes=(-1, 0))

    Parameters
    ----------
    a : ArrayType
        First array to multiply.
    b : ArrayType
        Second array to multiply.

    Returns
    -------
    ArrayType
        The contraction along the trailing axis of `a` and the leading axis of `b`.

    See Also
    --------
    numpy.tensordot
    """
    res = a @ b.reshape(b.shape[0], -1)
    return res.reshape(a.shape[:-1] + b.shape[1:])


def _compute_transpose_swap_order_bubble(axes: Axis) -> list[int]:
    """Compute swap order for TT transpose based on bubble sort.

    Parameters
    ----------
    axes : Axis
        Target order for the axes. `axes` should be a permutation of
        ``range(len(axes))``.

    Returns
    -------
    list[int]
        Indices of the first element of adjacent swaps between axis ``i`` and ``i + 1``
        to be performed.
    """
    swaps = []
    axes = list(axes)

    for i in reversed(range(len(axes))):
        if axes[i] == i:
            continue

        for j in range(0, i):
            if axes[j] > axes[j + 1]:
                axes[j], axes[j + 1] = axes[j + 1], axes[j]
                swaps.append(j)
    return swaps


def _swap_core(
    cores: list[Array3Type], axis: int, tol: float | None = None
) -> list[Array3Type]:
    """Swap two adjacent cores keeping the tensor-train structure intact.

    Parameters
    ----------
    cores : list[Array3Type]
        All core tensors given as third-order arrays.
    axis : int
        Index of the core tensor that is swapped with the next core tensor to the right.
    tol : float, optional
        Tolerance on the singular values to determine the new TT rank after swapping. If
        not given, the maximal rank is used.

    Returns
    -------
    list[Array3Type]
        List of new cores where cores ``axis`` and ``axis + 1`` are swapped.
    """
    if axis < 0:
        axis += len(cores)
    if axis >= len(cores) - 1:
        raise ValueError(
            f"axis is out of bounds: got {axis} but expected axis < {len(cores) -1}"
        )
    r, i, _ = cores[axis].shape
    _, j, t = cores[axis + 1].shape
    combined = np.einsum("ris,sjt->rjit", cores[axis], cores[axis + 1])
    u, sv, vh = tlb.svd(combined.reshape(r * j, i * t), full_matrices=False)
    if tol is None:
        rank = min(r * j, i * t)
    else:
        rank = len(sv) - findfirst(np.cumsum(sv[::-1] ** 2) > tol**2)
    # move sv to left core as cores are typically moved from left to right
    cores[axis] = (u[:, :rank] * sv[:rank]).reshape(r, j, rank)
    cores[axis + 1] = vh[:rank, :].reshape(rank, i, t)
    return cores

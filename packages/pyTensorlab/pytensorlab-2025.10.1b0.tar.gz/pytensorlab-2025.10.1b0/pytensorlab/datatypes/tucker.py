"""Tucker tensor format and implementations of core operations.

A `TuckerTensor` ``T`` represents a tensor in the Tucker format. This format stores the
factor matrices ``T.factors`` and the core tensor ``T.core`` of the representation. In
the Tucker format, a tensor is expressed as a core tensor of order ``T.ndim``,
multiplied with a matrix along each axis using the mode-n tensor-matrix product. The
array representation of the tensor can be expressed as ``tl.tmprod(T.core, T.factors,
range(T.ndim))``. In einsum notation, a Tucker representation of order three corresponds
to ``numpy.einsum("il,jm,kn,lmn->ijk", *T.factors, T.core)``.

The multilinear singular value decomposition (MLSVD) is a special case of the Tucker
decomposition, in which the factor matrices are column-wise orthonormal and the core is
ordered and all-orthogonal. Any TuckerTensor ``T`` can be converted to the MLSVD format
by ``T.normalize()``.

Notes
-----
Refer to the MLSVD and LMLRA routines in the :mod:`pytensorlab.algorithms` module for
the computation of a Tucker decomposition.

See Also
--------
~pytensorlab.algorithms.mlsvd.mlsvd, ~pytensorlab.algorithms.lmlra.lmlra

Examples
--------
A `TuckerTensor` can be created by providing the factor matrices and core:

>>> import pytensorlab as tl
>>> shape = (3,4,5)
>>> coreshape = (2,3,4)
>>> factors = tuple(tl.random.randn((s, c)) for s, c in zip(shape, coreshape))
>>> core = tl.random.randn(coreshape)
>>> T = tl.TuckerTensor(factors, core)

Refer to the documentation of :class:`TuckerTensor` for more examples.
"""

import math
import sys
from collections.abc import Generator, Sequence
from copy import deepcopy
from functools import singledispatchmethod
from typing import Any, Literal, cast

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


import numpy as np
from numpy.typing import ArrayLike, DTypeLike

import pytensorlab.backends.numpy as tlb
from pytensorlab.datatypes.core import getitem
from pytensorlab.typing import (
    ArrayType,
    Axis,
    AxisLike,
    BasicIndex,
    IndexType,
    MatrixType,
    NormalizedBasicIndexType,
    NormalizedIndexType,
    NumberType,
    Shape,
    SupportsArrayFromShape,
    VectorType,
    isint,
)
from pytensorlab.typing.core import ShapeLike
from pytensorlab.util.indextricks import _reshape_axes, findfirst, normalize_axes

from ..random._utils import _random, _random_like
from ..random.rng import get_rng
from ..util.indextricks import normalize_index
from ..util.utils import cumsum, kron, noisy, sumprod
from .core import (
    _mtkronprod_all,
    _mtkronprod_single,
    _mtkrprod_all,
    _mtkrprod_single,
    _tmprod,
    _tvprod,
    frob,
    mtkrprod,
    tens2mat,
    tmprod,
)
from .tensor import DenseTensor, Tensor


class TuckerTensor(DenseTensor):
    """Represent a tensor in the Tucker format.

    Refer to the module documentation for more information on the Tucker decomposition.
    The array representation of a third-order `TuckerTensor` can be constructed as
    ``numpy.einsum("il,jm,kn,lmn->ijk", *T.factors, T.core)``.

    Parameters
    ----------
    factors : Sequence[MatrixType]
        The factor matrices of the Tucker representation.
    core : ArrayType
        The core tensor of the Tucker repr.
    normalize : bool, default = False
        Normalize the `TuckerTensor` after construction, i.e. compute its MLSVD.

    Raises
    ------
    ValueError
        If the number of factors does not match ``core.ndim``.
    ValueError
        If the number of columns of a factor does not match the corresponding core
        dimension.

    Examples
    --------
    A `TuckerTensor` can be created by providing the factor matrices and core:

    >>> import pytensorlab as tl
    >>> shape = (3, 4, 5)
    >>> coreshape = (2, 3, 4)
    >>> factors = tuple(tl.random.randn((s, c)) for s, c in zip(shape, coreshape))
    >>> core = tl.random.randn(coreshape)
    >>> T = tl.TuckerTensor(factors, core)

    Alternatively, a `TuckerTensor` can be created by providing a 1-D array that
    consists of the vectorized versions of the factor matrices and the vectorized
    version of the core stacked on top of each other:

    >>> import numpy as np
    >>> data = np.concatenate([f.ravel() for f in factors])
    >>> data = np.concatenate([data, core.ravel()])
    >>> T2 = tl.TuckerTensor.from_vector(data, shape, coreshape)

    A `TuckerTensor` with random factor matrices and a random core can be created by
    providing the shape of the tensor and the shape of the core:

    >>> T = tl.TuckerTensor.randn(shape, coreshape)

    Here the standard normal distribution is used to generate the factor matrices and
    core. Other distributions are also available, and :func:`TuckerTensor.random` can be
    used to specify any distribution. Complex-valued factors and core can be generated
    by using the optional `imag` argument.

    See Also
    --------
    from_vector, random, randn, rand, random_like, randn_like, rand_like, empty,
    empty_like, zeros, zeros_like
    """

    def __init__(
        self, factors: Sequence[MatrixType], core: ArrayType, normalize: bool = False
    ):
        if any(not isinstance(f, np.ndarray) for f in factors):
            factors = [np.asarray(f) for f in factors]
        if not isinstance(core, np.ndarray):
            core = np.asarray(core)

        if any(f.ndim != 2 for f in factors):
            idx = findfirst(f.ndim != 2 for f in factors)
            raise ValueError(
                f"factor {idx} is not a matrix: ndim is {factors[idx].ndim}"
            )
        if any(0 in f.shape for f in factors):
            idx = findfirst(0 in f.shape for f in factors)
            raise ValueError(
                f"factor {idx} with shape ({factors[idx].shape[0]},"
                f"{factors[idx].shape[1]}) contains zero dimension"
            )
        if len(factors) < core.ndim:
            raise ValueError(
                f"not enough factor matrices: {len(factors)} given, "
                f"but expected {core.ndim}"
            )
        if 0 in core.shape:
            raise ValueError("core contains zero dimension")
        coreshape = core.shape + (1,) * (len(factors) - core.ndim)
        if any(f.shape[1] != s for f, s in zip(factors, coreshape)):
            idx = findfirst(f.shape[1] != s for f, s in zip(factors, coreshape))
            raise ValueError(
                f"dimension factor {idx} does not match core tensor: "
                f"factors[{idx}].shape[1] is {factors[idx].shape[1]}, "
                f"but expected {coreshape[idx]}"
            )

        shape = tuple(f.shape[0] for f in factors)
        super().__init__(shape)
        self._data: VectorType = np.concatenate(
            tuple(f.ravel() for f in factors) + (core.ravel(),)
        )
        self._coreshape: Shape = coreshape
        self._compute_factor_and_core_views()
        if normalize:
            self.normalize()

    @classmethod
    def from_vector(
        cls,
        data: ArrayType,
        shape: Shape,
        coreshape: Shape,
        copy: bool = True,
        normalize: bool = False,
    ) -> Self:
        """Create a `TuckerTensor` using the factors and core in vectorized format.

        Parameters
        ----------
        data : ArrayLike
            The vectorized factor matrices and core, concatenated in a vector.
        shape : Shape
            The dimensions of the tensor.
        coreshape : Shape
            The dimensions of the core tensor.
        copy : bool
            If True, the `TuckerTensor` stores an array copy of `data`. Otherwise, it
            stores a view to `data`.
        normalize : bool, default = False
            Normalize the `TuckerTensor` after construction, i.e. compute its MLSVD.

        Returns
        -------
        TuckerTensor
            A `TuckerTensor` with the factors and core provided in `data`.

        Raises
        ------
        ValueError
            If the number of dimensions of the core does not match the number of
            dimensions of the tensor.
        ValueError
            If the size of `data` does not match the expected number of parameters of
            the decomposition.
        """
        obj = cls.__new__(cls)
        super().__init__(obj, tuple(shape))
        if len(shape) != len(coreshape):
            raise ValueError(
                f"lengths of shape and coreshape do not match: len(coreshape) is "
                f"{len(coreshape)} while expected {len(shape)}"
            )
        obj._data = np.asarray(data, copy=copy if copy else None).ravel()
        if isinstance(data, np.ndarray):
            obj.setflags(write=copy or data.flags["WRITEABLE"])

        if obj._data.size != sumprod(shape, coreshape) + math.prod(coreshape):
            raise ValueError(
                f"size of data does not match the expected number of parameters: size "
                f"is {obj._data.size} while expected "
                f"{sumprod(shape, coreshape) + math.prod(coreshape)}"
            )

        obj._coreshape = tuple(coreshape)
        obj._compute_factor_and_core_views()
        if normalize:
            obj.normalize()
        return obj

    @classmethod
    def empty(cls, shape: Shape, coreshape: Shape) -> Self:
        """Create a `TuckerTensor` with empty factors and core.

        Parameters
        ----------
        shape : Shape
            The dimensions of the tensor.
        coreshape : Shape
            The dimensions of the core tensor.

        Returns
        -------
        TuckerTensor
            A `TuckerTensor` with empty factors and core.

        See Also
        --------
        numpy.empty
        """
        return cls.random(shape, coreshape, real=np.empty)

    @classmethod
    def zeros(cls, shape: Shape, coreshape: Shape) -> Self:
        """Create a `TuckerTensor` with factors and core containing all zeros.

        Parameters
        ----------
        shape : Shape
            The dimensions of the tensor.
        coreshape : Shape
            The dimensions of the core tensor.

        Returns
        -------
        TuckerTensor
            A `TuckerTensor` with factors and core containing all zeros.

        See Also
        --------
        numpy.zeros
        """
        return cls.random(shape, coreshape, real=np.zeros)

    @classmethod
    def empty_like(cls, array: ArrayLike, coreshape: Shape) -> Self:
        """Create a `TuckerTensor` with empty factors and core.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        coreshape : Shape
            The dimensions of the core tensor.

        Returns
        -------
        TuckerTensor
            A `TuckerTensor` with empty factors and core.

        See Also
        --------
        numpy.empty_like
        """
        return cls.random_like(array, coreshape, real=np.empty)

    @classmethod
    def zeros_like(cls, array: ArrayLike, coreshape: Shape) -> Self:
        """Create a `TuckerTensor` with factors and core containing all zeros.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        coreshape : Shape
            The dimensions of the core tensor.

        Returns
        -------
        TuckerTensor
            A `TuckerTensor` with factors and core containing all zeros.

        See Also
        --------
        numpy.zeros_like
        """
        return cls.random_like(array, coreshape, real=np.zeros)

    @classmethod
    def random(
        cls,
        shape: Shape,
        coreshape: Shape,
        real: SupportsArrayFromShape | None = None,
        imag: SupportsArrayFromShape | bool | None = None,
        normalize: bool = False,
    ) -> Self:
        """Generate a `TuckerTensor` with random factors and core.

        By default, real factors and a real core are generated, drawn from a uniform
        distribution. The distribution can be changed by providing an alternative
        random number generating function to `real`. Complex factors and a complex core
        can be generated by providing a random number generating function to `imag`.

        Parameters
        ----------
        shape : Shape
            The shape of the tensor.
        coreshape : Shape
            The shape of the core tensor.
        real : SupportsArrayFromShape, default = tl.get_rng().random
            Random number generating function for generating the real part of the
            factors.
        imag : SupportsArrayFromShape | bool, optional
            If this argument is provided, complex factors and a complex core are
            generated. If `imag` is true, the function provided to `real` is also used
            to generate the imaginary part of the factors and core. If a random number
            generating function is provided, this function is used for generating the
            imaginary part of the factors and core.
        normalize : bool, default = False
            Normalize the randomly generated `TuckerTensor` after construction, i.e.
            compute its MLSVD.

        Returns
        -------
        TuckerTensor
            A `TuckerTensor` with random factors and core, in which each element is
            drawn from `real` (with an optional imaginary part drawn from `imag`).

        See Also
        --------
        randn, rand, random_like, randn_like, rand_like, normalize
        """
        size = sumprod(shape, coreshape) + math.prod(coreshape)
        data = _random(size, real, imag)
        return cls.from_vector(data, shape, coreshape, normalize=normalize)

    @classmethod
    def randn(
        cls,
        shape: Shape,
        coreshape: Shape,
        imag: bool | None = None,
        normalize: bool = False,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random factors and core, drawn from a standard normal distribution.

        Parameters
        ----------
        shape : Shape
            The shape of the tensor.
        coreshape : Shape
            The shape of the core tensor.
        imag : bool, optional
            If True, the factors and core are complex, with the imaginary part also
            drawn from a standard normal distribution.
        normalize : bool, default = False
            Normalize the randomly generated `TuckerTensor` after construction, i.e.
            compute its MLSVD.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        TuckerTensor
            A `TuckerTensor` with random factors, in which each element is drawn from
            a standard normal distribution.
        """
        _rng = get_rng(_rng)

        randn = get_rng(_rng).standard_normal
        return cls.random(shape, coreshape, real=randn, imag=imag, normalize=normalize)

    @classmethod
    def rand(
        cls,
        shape: Shape,
        coreshape: Shape,
        imag: bool | None = None,
        normalize: bool = False,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random factors and core, drawn from a uniform distribution.

        Parameters
        ----------
        shape : Shape
            The shape of the tensor.
        coreshape : Shape
            The shape of the core tensor.
        imag : bool, optional
            If True, the factors and core are complex, with the imaginary part also
            drawn from a uniform distribution.
        normalize : bool, default = False
            Normalize the randomly generated `TuckerTensor` after construction, i.e.
            compute its MLSVD.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        TuckerTensor
            A `TuckerTensor` with random factors and core, in which each element is
            drawn from a uniform distribution.
        """
        _rng = get_rng(_rng)

        random = get_rng(_rng).random
        return cls.random(shape, coreshape, real=random, imag=imag, normalize=normalize)

    @classmethod
    def random_like(
        cls,
        array: ArrayLike,
        coreshape: Shape,
        real: SupportsArrayFromShape | None = None,
        imag: SupportsArrayFromShape | bool | None = None,
        normalize: bool = False,
    ) -> Self:
        """Generate a `TuckerTensor` with random factors and core.

        By default, real factors and a real core are generated, drawn from a uniform
        distribution. The distribution can be changed by providing an alternative
        random number generating function to `real`. Complex factors and a complex core
        can be generated by providing a random number generating function to `imag`.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        coreshape : Shape
            The dimensions of the core tensor.
        real : SupportsArrayFromShape, default = tl.get_rng().random
            Random number generating function for generating the real part of the
            factors.
        imag : SupportsArrayFromShape | bool, optional
            If this argument is provided, complex factors and a complex core are
            generated. If `imag` is true, the function provided to `real` is also used
            to generate the imaginary part of the factors and core. If a random number
            generating function is provided, this function is used for generating the
            imaginary part of the factors and core.
        normalize : bool, default = False
            Normalize the randomly generated `TuckerTensor` after construction, i.e.
            compute its MLSVD.

        Returns
        -------
        TuckerTensor
            A `TuckerTensor` with random factors and core, in which each element is
            drawn from `real` (with an optional imaginary part drawn from `imag`).
        """
        shape = np.shape(array)
        size = sumprod(shape, coreshape) + math.prod(coreshape)
        data = _random_like(array, size, real, imag)
        return cls.from_vector(data, shape, coreshape, normalize=normalize)

    @classmethod
    def randn_like(
        cls,
        array: ArrayLike,
        coreshape: Shape,
        imag: bool | None = None,
        normalize: bool = False,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random factors and core, drawn from a standard normal distribution.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        coreshape : Shape
            The dimensions of the core tensor.
        imag : bool, optional
            If True, the factors and core are complex, with the imaginary part also
            drawn from a standard normal distribution.
        normalize : bool, default = False
            Normalize the randomly generated `TuckerTensor` after construction, i.e.
            compute its MLSVD.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        TuckerTensor
            A `TuckerTensor` with random factors, in which each element is drawn from
            a standard normal distribution.
        """
        _rng = get_rng(_rng)

        randn = get_rng(_rng).standard_normal
        return cls.random_like(array, coreshape, randn, imag, normalize=normalize)

    @classmethod
    def rand_like(
        cls,
        array: ArrayLike,
        coreshape: Shape,
        imag: bool | None = None,
        normalize: bool = False,
        _rng: np.random.Generator | int | None = None,
    ) -> Self:
        """Generate random factors and core, drawn from a uniform distribution.

        Parameters
        ----------
        array : ArrayLike
            The shape of `array` determines the shape of the returned tensor. If `array`
            is complex, then the returned tensor is complex too.
        coreshape : Shape
            The dimensions of the core tensor.
        imag : bool, optional
            If True, the factors and core are complex, with the imaginary part also
            drawn from a uniform distribution.
        normalize : bool, default = False
            Normalize the randomly generated `TuckerTensor` after construction, i.e.
            compute its MLSVD.
        _rng : numpy.random.Generator | int, optional
            Seed or random number generator used for all random operations in this
            function. If an integer is given, a new generator is created with that seed.
            If a generator is provided, it is used directly. If None, the global
            generator (set via `set_rng`) is used.

        Returns
        -------
        TuckerTensor
            A `TuckerTensor` with random factors and core, in which each element is
            drawn from the uniform distribution.
        """
        _rng = get_rng(_rng)

        random = get_rng(_rng).random
        return cls.random_like(array, coreshape, random, imag, normalize=normalize)

    @property
    def coreshape(self) -> Shape:
        """The dimensions of the core tensor.

        Returns
        -------
        Shape
            Dimensions of the core tensor.
        """
        return self._coreshape

    @property
    def core_shape(self) -> Shape:
        """The dimensions of the core tensor.

        Returns
        -------
        Shape
            Dimensions of the core tensor.
        """
        return self._coreshape

    @property
    def dtype(self) -> np.dtype[Any]:
        """Datatype of the tensor elements.

        Returns
        -------
        numpy.dtype[Any]
            The datatype of the tensor elements.
        """
        return self._data.dtype

    def _compute_factor_and_core_views(self) -> None:
        """Compute views of the factors and the core.

        Views of the factors and of the core are computed and stored.
        """
        bounds = [0] + list(cumsum(s * r for s, r in zip(self.shape, self.coreshape)))
        self._factors = tuple(
            self._data[i:j].reshape(s, r)
            for (i, j, s, r) in zip(bounds[:-1], bounds[1:], self.shape, self.coreshape)
        )
        self._core = self._data[bounds[-1] :].reshape(self.coreshape)

    @property
    def factors(self) -> tuple[MatrixType, ...]:
        """Factor matrices.

        The factor matrices are returned as a tuple of views of the underlying data.

        Returns
        -------
        tuple[MatrixType, ...]
            The factors of the `TuckerTensor`.

        See Also
        --------
        core

        Examples
        --------
        The following can be used to view the first factor:

        >>> import pytensorlab as tl
        >>> T = tl.TuckerTensor.randn((3, 3, 3), (2, 2, 2))
        >>> T.factors[0]
        array([[ 1.10572788,  0.5304342 ],
        ...    [ 0.22575759, -0.20260285],
        ...    [-0.03839152, -0.18930443]]) #random

        As `factors` provides a tuple of views of the underlying data, changing all
        elements in a factor matrix should be done as follows:

        >>> import numpy as np
        >>> T.factors[0][:] = np.ones((3, 2))

        Changing elements as follows is not allowed:

        >>> T.factors[0] = np.ones((3, 2))
        Traceback (most recent call last):
            ...
        TypeError: 'tuple' object does not support item assignment

        To change specific elements, use:

        >>> T.factors[2][0, 1] = 0
        """
        return self._factors

    @property
    def core(self) -> ArrayType:
        """Core tensor.

        The core tensor is returned as a view of the underlying data.

        Returns
        -------
        ArrayType
            The core tensor.

        See Also
        --------
        factors

        Examples
        --------
        The following can be used to view the core:

        >>> import pytensorlab as tl
        >>> A = tl.TuckerTensor.randn((3, 3, 3), (1, 2, 2))
        >>> A.core
        array([[[ 2.02245563, -0.07854674],
        ...     [ 0.84957779, -2.04790289]]])  #random

        As `core` provides a view of the underlying data, changing all elements in the
        core tensor should be done as follows:

        >>> import numpy as np
        >>> A.core[:] = np.zeros((1, 2, 2))

        Changing elements as follows is not allowed:

        >>> A.core = np.zeros((2, 2, 2))
        Traceback (most recent call last):
            ...
        AttributeError: can't set attribute

        To change specific elements, use:

        >>> A.core[0,1,0] = 3
        """
        return self._core

    def copy(self) -> Self:
        """Create copy of tensor.

        Returns
        -------
        Self
            Copy of the tensor.
        """
        return cast(
            Self, type(self).from_vector(self._data, self.shape, self.coreshape)
        )

    def __str__(self) -> str:
        return (
            f"""Tucker tensor of shape {self.shape} with core shape {self.coreshape}"""
        )

    def __repr__(self) -> str:
        if Tensor._REPR_MODE != "repr":
            return str(self)
        with np.printoptions(threshold=50, linewidth=88, precision=3, edgeitems=2):
            factors = ",\n".join(map(repr, self.factors))
            return f"{self.__class__.__name__}(\n({factors}),\n{self.core!r},\n)"

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
        Self
            A new `TuckerTensor` with permuted axes.
        """
        axes = normalize_axes(axes, self.ndim, fill=True, fillreversed=True)
        core = np.transpose(self.core, axes)
        return type(self)([self.factors[i] for i in axes], core)

    def __array__(self, dtype: DTypeLike = None, copy: bool | None = None) -> ArrayType:
        return _tuckergen(self.factors, self.core, (slice(None),) * self.ndim)

    def _entry(self, indices: Sequence[NormalizedIndexType]) -> ArrayType:
        return _tuckergen(self.factors, self.core, indices)

    def _getitem_sliced(self, key: Sequence[NormalizedBasicIndexType]) -> float | Self:
        def _factors(
            factors: Sequence[MatrixType], key: Sequence[BasicIndex]
        ) -> Generator[MatrixType, None, None]:
            factoriter = iter(factors)
            for k in key:
                if k is None:
                    yield np.ones((1, 1), self._data.dtype)
                else:
                    f = next(factoriter)
                    yield np.reshape(f[k, :], (-1, f.shape[1]))  # type:ignore

        factors = list(_factors(self.factors, key))
        core = self.core[tuple(np.newaxis if k is None else slice(None) for k in key)]

        # Return a scalar if all indices are integers
        if all(isint(k) for k in key):
            return tmprod(core, factors, range(len(factors))).ravel()[0]

        # Remove modes with dimension one if selected using integer
        intidx = tuple(i for i, k in enumerate(key) if isint(k))
        core = tmprod(core, [factors[i] for i in intidx], intidx)
        core.shape = tuple(s for s, k in zip(core.shape, key) if not isint(k))
        factors = [f for f, k in zip(factors, key) if not isint(k)]

        return type(self)(factors, core)

    def extract(self, *key: IndexType) -> Self:
        """Extract a tensor by indexing the core tensor.

        A `TuckerTensor` is extracted from this tensor by slicing the core tensor, i.e.,
        the core tensor of the result is ``core[key]``. The factor matrices are sliced
        accordingly: the new factors are ``[factors[:, k] for k in key]``. An integer
        key ``k`` is interpreted as the upper bound of a slice, i.e., ``slice(k)``.

        Parameters
        ----------
        key : IndexType
            Indices used to extract the core tensor and corresponding factor matrices.

        Returns
        -------
        TuckerTensor
            `TuckerTensor` with the extracted core and corresponding factor matrices.

        See Also
        --------
        extend

        Examples
        --------
        >>> import pytensorlab as tl
        >>> T = tl.TuckerTensor.random((10, 11, 12), (4, 5, 6))
        >>> S = T.extract(2, 3, 4)
        >>> print(S)
        Tucker tensor of shape (10, 11, 12) with core shape (2, 3, 4)

        This is equivalent to:

        >>> S = T.extract(slice(2), slice(3), slice(4))
        >>> print(S)
        Tucker tensor of shape (10, 11, 12) with core shape (2, 3, 4)

        If the intended result is to extract a single index, a tuple can be used:

        >>> S = T.extract((2,), (3,), (4,))
        >>> print(S)
        Tucker tensor of shape (10, 11, 12) with core shape (1, 1, 1)

        Integers, tuples of integers and booleans can be used as well:

        >>> S = T.extract([True, False, False, True], (3,  -1), 1)
        >>> print(S)
        Tucker tensor of shape (10, 11, 12) with core shape (2, 2, 1)

        The ellipsis operator is supported and is automatically added if needed:

        >>> S = T.extract((2,), ..., (4,))
        >>> print(S)
        Tucker tensor of shape (10, 11, 12) with core shape (1, 5, 1)

        >>> S = T.extract((2,))
        >>> print(S)
        Tucker tensor of shape (10, 11, 12) with core shape (1, 5, 6)
        """
        if any(k is None for k in key):
            raise ValueError("None and np.newaxis are not supported")
        key = cast(
            tuple[IndexType], tuple(slice(k) if isinstance(k, int) else k for k in key)
        )
        normalized_key = normalize_index(key, self.coreshape)

        factors = tuple(
            np.reshape(f[:, k], (f.shape[0], -1))
            for f, k in zip(self.factors, normalized_key)
        )
        core = np.asarray(getitem(self.core, normalized_key))
        return type(self)(factors, core)

    def extend(self, coreshape: Shape) -> Self:
        """Extend a tensor by enlarging its core.

        A new `TuckerTensor` is formed by embedding the current core in a larger core
        of shape `coreshape` and adding additional columns in the factors accordingly.
        The extra entries in the enlarged core are filled with zeros so the new tensor
        is equal to the original tensor.

        Parameters
        ----------
        coreshape : Shape
            Shape of the enlarged core.

        Returns
        -------
        TuckerTensor
            `TuckerTensor` with the extended core and corresponding factor matrices.

        See Also
        --------
        extract
        """
        if self.ndim != len(coreshape):
            raise ValueError(
                "length of provided core shape is incompatible; "
                f"expected len(coreshape) = {self.ndim}, but got {len(coreshape)}"
            )
        v = tuple(
            not cs <= csn < s
            for cs, csn, s in zip(self.coreshape, coreshape, self.shape)
        )
        if any(v):
            k = findfirst(v)
            raise ValueError(
                f"core shape for axis {k} is incompatible; got {coreshape[k]} but "
                f"expected a dimension between {self.coreshape[k]} and {self.shape[k]}"
            )

        delta = tuple(max(0, r - n) for n, r in zip(self.coreshape, coreshape))
        core = tlb.pad(self.core, tuple((0, d) for d in delta))
        factors = []
        for f, d in zip(self.factors, delta):
            q, _ = tlb.qr(np.pad(f, ((0, 0), (0, d))), mode="reduced")
            factors.append(np.hstack((f, q[:, -d:])))

        return type(self)(factors, core)

    def has_orthonormal_factors(self, tol_abs: float = 1e-12) -> bool:
        """Check if factor matrices of TuckerTensor are column-wise orthonormal.

        Returns true if each factor matrix has orthonormal columns. The check is
        performed by evaluating ``f.conj().T @ f`` for all factor matrices ``f`` and
        examining whether the matrix elements are within an absolute tolerance of
        `tol_abs` from the identity matrix.

        Parameters
        ----------
        tol_abs : float, default = 1e-12
            The absolute tolerance used to check for orthogonality of the factors.

        Returns
        -------
        bool
            Whether the factor matrices have orthonormal columns.

        See Also
        --------
        normalize
        """
        return all(
            [
                np.allclose(np.eye(f.shape[1]), f.conj().T @ f, rtol=0, atol=tol_abs)
                for f in self.factors
            ]
        )

    def is_normalized(self, tol_abs: float = 1e-12) -> bool:
        """Return True if the factors and core are normalized.

        Returns True if each factor matrix has orthonormal columns and the core
        tensor is all-orthogonal and ordered. In other words, the inner products of
        the mode-n unfoldings of the core produce diagonal matrices with entries in
        non-increasing descending order.

        Parameters
        ----------
        tol_abs : float, default = 1e-12
            The absolute tolerance used to check for orthogonality of the factors.

        Returns
        -------
        bool
            Whether the `TuckerTensor` is normalized.

        See Also
        --------
        has_orthonormal_factors, normalize
        """
        # Check orthogonality of factors
        if not self.has_orthonormal_factors(tol_abs=tol_abs):
            return False

        for n in range(self.ndim):
            tmp = tens2mat(self.core, n)
            SSH = tmp @ tmp.conj().T
            s = np.abs(deepcopy(np.diag(SSH)))
            np.fill_diagonal(SSH, 0)
            SHS_norm = frob(SSH)
            # Core should be all-orthogonal.
            if SHS_norm > np.linalg.norm(s) * 1e-12:
                return False
            # Norms should be ordered in descending order. Allow for small deviations of
            # ordering because of numerical reasons, especially for near equal or near
            # zero values.
            if not all(s[:-1] >= s[1:] - 10 * max(s) * np.finfo(float).eps):
                return False

        return True

    def normalize(self) -> Self:
        """Normalize factors and core tensor.

        After normalization, each factor matrix has orthonormal columns and the core
        tensor is all-orthogonal, i.e., the inner products of the mode-n unfoldings are
        diagonal, and ordered, i.e., the norms of the order ``self.ndim - 1`` slices
        do not increase for increasing indices.

        Notes
        -----
        If ``self.coreshape`` is larger than ``self.shape``, ``self.factors`` and
        ``self.core`` will be padded with zeros.

        Examples
        --------
        >>> import pytensorlab as tl
        >>> T = tl.TuckerTensor.randn((3,4,5), (2,3,3))
        >>> S = T.normalize()

        All factors have orthonormal columns, hence their the inner products are the
        identity matrix::

            for n in range(T.ndim):
                T.factors[n].conj().T @ T.factors[n]

        The core tensor is all-orthogonal with ordered slices, hence the following inner
        products are diagonal matrices with non-increasing elements that are the squared
        slice norms:

        >>> for n in range(T.ndim):
        >>>     tl.tens2mat(T.core, n).conj().T @ tl.tens2mat(T.core, n)
        """
        factors, R = zip(*tuple(tlb.qr(f, mode="reduced") for f in self.factors))
        core = tmprod(self.core, R, range(self.ndim))

        def colspace(n):
            U, _, _ = tlb.svd(tens2mat(core, n), full_matrices=False)
            if U.shape[1] < self._coreshape[n]:
                pad = np.zeros((U.shape[0], self._coreshape[n] - U.shape[1]))
                U = np.concatenate((U, pad), axis=1)
            return U

        U = tuple(colspace(n) for n in range(self.ndim))
        factors = tuple(f @ u for f, u in zip(factors, U))
        core = tmprod(core, U, range(self.ndim), "H")

        for f1, f2 in zip(self.factors, factors):
            f1[:] = f2[:]
        self.core[:] = core[:]

        return self

    def reshape(self, shape: ShapeLike) -> Self:
        axes = _reshape_axes(self.shape, shape)

        def _new_factors():
            for ax in axes:
                if len(ax) == 1:
                    yield self.factors[ax[0]]
                else:
                    factors = tuple(self.factors[n] for n in ax)
                    yield kron(*factors)

        new_shape = tuple(math.prod([self.core_shape[n] for n in ax]) for ax in axes)
        new_core = self.core.reshape(new_shape)

        return type(self)(tuple(_new_factors()), new_core)

    @singledispatchmethod
    def __add__(self, T: Any) -> Any:
        return NotImplemented

    def __neg__(self) -> Self:
        T = self.copy()
        T.core[:] *= -1
        return T

    def __sub__(self, other: Any) -> Any:
        return self + (-other)

    def iscomplex(self) -> bool:
        """Test if the tensor elements are complex-valued.

        Returns
        -------
        bool
            If the tensor elements are complex-valued.
        """
        return tlb.iscomplexobj(self._data)

    def conj(self) -> Self:
        """Compute complex conjugate tensor.

        Returns
        -------
        Self
            Complex conjugate `PolyadicTensor`.
        """
        if self.iscomplex():
            return cast(
                Self,
                type(self).from_vector(self._data.conj(), self.shape, self.coreshape),
            )

        return self


def _tuckergen(
    factors: Sequence[MatrixType],
    core: ArrayType,
    indices: Sequence[NormalizedIndexType],
) -> ArrayType:
    S = core
    isprevindex = False
    for n, (f, idx) in reversed(list(enumerate(zip(factors, indices)))):
        if isinstance(idx, slice):
            S = tlb.tensordot(S, f, (n, 1))
        elif not isprevindex:
            F: MatrixType = np.reshape(f[idx, :], (-1, f.shape[1]))
            S = tlb.tensordot(S, F, (n, 1))
            isprevindex = True
        else:
            key = (None,) * n + (slice(None),) + (None,) * (S.ndim - n - 2) + (idx,)
            M: ArrayType = f.T[key]
            M.shape = M.shape + (1,) * (S.ndim - M.ndim)
            S = cast(ArrayType, np.sum(S * M, n))

    return S.T


@_mtkrprod_single.register
def _mtkrprod_single_tucker(
    T: TuckerTensor, U: Sequence[MatrixType], axis: int, conjugate: bool = True
) -> MatrixType:
    VU = [v.conj().T @ u for v, u in zip(T.factors, U)]
    return T.factors[axis] @ _mtkrprod_single(T.core, VU, axis)


@_mtkrprod_all.register
def _mtkrprod_all_tucker(
    T: TuckerTensor, U: Sequence[MatrixType], conjugate: bool = True
) -> Sequence[MatrixType]:
    V = T.factors
    VU = [v.conj().T @ u for (v, u) in zip(V, U)]
    core_prod = mtkrprod(T.core, VU)
    return [v @ s for (v, s) in zip(V, core_prod)]


@_mtkronprod_single.register
def _mtkronprod_single_tucker(
    T: TuckerTensor,
    U: Sequence[MatrixType],
    axis: int,
    transpose: Literal["T", "H"] | None = None,
) -> MatrixType:
    if transpose == "T":
        U = [f.T for f in U]
    elif transpose == "H":
        U = [f.conj().T for f in U]

    VU = [v.conj().T @ u for v, u in zip(T.factors, U)]

    return T.factors[axis] @ _mtkronprod_single(T.core, VU, axis)


@_mtkronprod_all.register
def _mtkronprod_all_tucker(
    T: TuckerTensor,
    U: Sequence[MatrixType],
    transpose: Literal["T", "H"] | None = None,
) -> Sequence[MatrixType]:
    if transpose == "T":
        U = [f.T for f in U]
    elif transpose == "H":
        U = [f.conj().T for f in U]

    VU = [v.conj().T @ u for v, u in zip(T.factors, U)]
    core_prod = _mtkronprod_all(T.core, VU)

    return [v @ s for v, s in zip(T.factors, core_prod)]


@_tmprod.register
def _tmprod_tucker(
    T: TuckerTensor,
    matrices: Sequence[MatrixType],
    axes: Axis,
) -> TuckerTensor:
    matiter = iter(matrices)
    factors = [next(matiter) @ f if n in axes else f for n, f in enumerate(T.factors)]
    return TuckerTensor(factors, T.core)


@_tvprod.register
def _tvprod_tucker(
    T: TuckerTensor, vectors: Sequence[VectorType], axes: Axis
) -> TuckerTensor | VectorType | NumberType:
    row_factors = [v[np.newaxis, :] @ T.factors[a] for a, v in zip(axes, vectors)]
    core = tmprod(T.core, row_factors, axes)
    if len(axes) == T.ndim and hasattr(core, "__getitem__"):
        return core.item()
    factors = [f for a, f in enumerate(T.factors) if a not in axes]
    if len(axes) == T.ndim - 1:
        return factors[0] @ np.squeeze(core)
    return TuckerTensor(factors, np.squeeze(core, axes))


@frob.register
def _frob_tucker(T: TuckerTensor, squared: bool = False) -> float:
    f = [cast(MatrixType, f.conj().T @ f) for f in T.factors]
    nrm2 = cast(float, np.sum(tmprod(np.conj(T.core), f, range(T.ndim), "T") * T.core))
    return abs(nrm2) if squared else math.sqrt(abs(nrm2))


@noisy.register
def _noisy_tucker(array: TuckerTensor, snr: float, _rng=None):
    _rng = get_rng(_rng)

    return TuckerTensor(
        noisy(array.factors, snr, _rng=_rng), noisy(array.core, snr, _rng=_rng)
    )

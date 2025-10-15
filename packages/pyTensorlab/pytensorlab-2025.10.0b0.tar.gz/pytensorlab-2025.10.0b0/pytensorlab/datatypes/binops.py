"""Operators with tensors as the first two arguments.

Depending on the types of the two tensors, the operator selects the appropriate
implementation that exploits the underlying structure.

Classes
-------
BinaryOperatorDispatcher
    Dispatcher for binary operators.


Routines
--------
binaryoperator
    Create a dispatcher for this binary operator.
inprod
    Computes the inner product between two tensors.
matdot
    Computes the matricized tensor times conjugated transposed matricized tensor
    product.


Examples
--------
Define a binary operator using the :func:`.binaryoperator` decorator:

>>> import pytensorlab as tl
>>> from pytensorlab.datatypes.binops import binaryoperator
>>> from pytensorlab.typing import ArrayType

>>> @binaryoperator
... def binop(T1: tl.Tensor, T2: tl.Tensor) -> ArrayType:
...     pass

Register an implementation for two specific tensor types using the register decorator:

>>> @binop.register
... def binop_polyadic_tucker(
...     T1: tl.PolyadicTensor, T2: tl.TuckerTensor
... ) -> ArrayType:
...     pass

Using the types of the arguments `T1` and `T2` provided to a binary operator, the
matching implementation is selected.
"""

import functools as ft
import math
import typing
from collections.abc import Callable, Sequence
from functools import singledispatchmethod
from inspect import signature
from itertools import product
from typing import (
    Any,
    Concatenate,
    Generic,
    TypeAlias,
    TypeGuard,
    TypeVar,
    Union,
    cast,
    overload,
)

import numpy as np
from numpy.fft import fft, ifft
from typing_extensions import ParamSpec

import pytensorlab.backends.numpy as tlb
from pytensorlab.typing import ArrayType, MatrixType, NumberType, TensorType

from ..util.indextricks import _complement_indices, findfirst, normalize_axes
from ..util.utils import inprod_kr
from .core import _mtkrprod_single, mtkrprod, tens2mat, tmprod, tvprod
from .deferred_residual import DeferredResidual
from .hankel import HankelTensor, dehankelize, hankelize
from .partial import IncompleteTensor, PartialTensor, SparseTensor
from .polyadic import PolyadicTensor
from .tensor import DenseTensor, Tensor
from .tensortrain import TensorTrainTensor
from .tucker import TuckerTensor

P = ParamSpec("P")
SwapT = TypeVar("SwapT")
"""Type of the swapped object."""

ResultT = TypeVar("ResultT")
"""Type of the result."""

SwapOperator: TypeAlias = Callable[[SwapT], SwapT]
"""Operator executed when two operands are swapped.

The signature is::

    (result: SwapT) -> SwapT

See Also
--------
.binaryoperator
.BinaryOperator
.BinaryOperatorDispatcher
"""

R = TypeVar("R")


def _nop(a: SwapT) -> SwapT:
    """No operation."""
    return a


T1 = TypeVar("T1")
T2 = TypeVar("T2")
Res = TypeVar("Res")
BinaryOperator: TypeAlias = Callable[Concatenate[T1, T2, P], ResultT]
"""Operator acting on two operands.

The signature is::

    (op1: T1, op2: T2, *arg: P.args, **kwargs: P.kwargs) -> Res
"""


class BinaryOperatorDispatcher(Generic[P, R]):
    """Dispatcher for binary operators.

    This dispatcher calls the correct function ``f(a,b)`` to invoke based on the types
    of the two arguments. If no such function is found, but a function for the swapped
    types is available, the function ``swap(f(b,a))`` is called.

    Parameters
    ----------
    f : BinaryOperator
        Operator to be dispatched.
    swap : SwapOperator
        Swapping function called after swapping operations.

    Attributes
    ----------
    table : dict[tuple[Type[T], type[T]], BinaryOperator]
        Dispatch table with a tuple of types as key and the function to be called as
        value. This table is controlled using the `register` method.
    swap : SwapOperator
        Function called if the arguments are swapped.
    original : BinaryOperator
        The original function to be called if no matches are found. This function can be
        used, e.g., for error handling or to implement default behavior.

    Examples
    --------
    This class is typically not used directly, but using the :func:`.binaryoperator`
    decorator. For example:

    >>> from pytensorlab.datatypes.binops import binaryoperator

    >>> @binaryoperator
    ... def binop(a, b):
    ...     pass # do something

    The swap function can be set using:

    >>> binop.swap = lambda x: x

    A new implementation can be registered using the ``@op.register`` decorator, where
    ``op`` is the name for the binary operator:

    >>> @binop.register
    ... def binop_int_float(a: int, b: float):
    ...     pass # do something
    """

    def __init__(self, f: BinaryOperator[Any, Any, P, R], swap: SwapOperator[R] = _nop):
        self.table: dict[
            tuple[type[Any], type[Any]], BinaryOperator[Any, Any, P, R]
        ] = {}
        self.swap: SwapOperator[R] = swap
        self.original: BinaryOperator[Any, Any, P, R] = f
        # Cache the function here to avoid memory leaks.

        self._find_matching_implementation = ft.lru_cache()(
            self.__find_matching_implementation
        )

    def register(self, f: BinaryOperator[T1, T2, P, R]) -> BinaryOperator[T1, T2, P, R]:
        """Register an implementation for specific types.

        The function `f` is added as the implementation for the types of its two first
        two arguments. The function `f` should have at least two arguments with type
        annotations.

        Parameters
        ----------
        f : BinaryOperator
            The implementation to be registered.

        Returns
        -------
        BinaryOperator
            The function `f`.

        Raises
        ------
        ValueError
            If `f` has fewer than two arguments.
        ValueError
            If an implementation has already been registered with the types of the first
            two arguments of `f`.
        """

        def _normalize_parameter(param) -> tuple[type[Any], ...]:
            param_type = param.annotation
            if typing.get_origin(param_type) == Union:
                result_type = typing.get_args(param_type)
            else:
                result_type = (param_type,)
            # TensorType from typing.core uses a ForwardRef to avoid circular imports,
            # but this does not match in the implementation; therefore we replace it
            # here. Alternatively, TensorType can be redefined in all files, but this
            # would lead to code duplication.
            result_type = tuple(
                Tensor if t == type["Tensor"] else t for t in result_type
            )
            return result_type  # type:ignore

        params = signature(f).parameters
        if len(params) < 2:
            raise ValueError(
                f"at least two parameters are expected; {len(params)} given"
            )
        param_iter = iter(params)
        type_first: tuple[type[Any], ...] = _normalize_parameter(
            params[next(param_iter)]
        )
        type_second: tuple[type[Any], ...] = _normalize_parameter(
            params[next(param_iter)]
        )

        # Register all types in a Union separately.
        for key in product(type_first, type_second):
            if key not in self.table:
                self.table[key] = f
            else:
                raise ValueError(
                    f"duplicate implementation of binary operator with "
                    f"types {key[0]} and {key[1]}"
                )
        # Clear cache to make sure the new implementation f can be found.
        self._find_matching_implementation.cache_clear()
        return f

    def __call__(self, a: Any, b: Any, *args: P.args, **kwargs: P.kwargs) -> R:
        """Apply the binary operator.

        If no implementation is found, the original function is called.

        Parameters
        ----------
        a
            The first argument of the binary operator.
        b
            The second argument of the binary operator.

        Returns
        -------
        TensorType
            The result of the binary operator.
        """
        f, swap = self._find_matching_implementation(
            type(a), type(b)  # type:ignore [arg-type] #  (mypy bug #11469)
        )
        return self.swap(f(b, a, *args, **kwargs)) if swap else f(a, b, *args, **kwargs)

    def __find_matching_implementation(
        self, typeA: type[Any], typeB: type[Any]
    ) -> tuple[BinaryOperator, bool]:
        """Find a matching implementation based on the argument types.

        Using the dispatching table, the implementation for the binary operation is
        selected based on the types `typeA` and `typeB`, and the result is returned.

        Parameters
        ----------
        typeA
            The type of the first argument of the binary operator.
        typeB
            The type of the second argument of the binary operator.

        Returns
        -------
        BinaryOperator
            Implementation that matches `typeA` and `typeB`. If no match is found,
            `self.original` is returned.
        bool
            Indicates whether an implementation of the binary operator that matches
           `typeA` and `typeB` has been found.
        """

        def match(ta: type[Any], tb: type[Any]) -> bool:
            matcha = issubclass(typeA, typing.get_origin(ta) or ta)
            matchb = issubclass(typeB, typing.get_origin(tb) or tb)
            return matcha and matchb

        # Check types.
        f = self.table.get((typeA, typeB), None)
        if f:
            return f, False
        f = self.table.get((typeB, typeA), None)
        if f:
            return f, True

        # Check subtypes.
        matches: dict[int, list[tuple[Callable[Concatenate[Any, Any, P], R], bool]]] = {
            0: [],
            1: [],
            2: [],
        }
        for ta, tb in self.table.keys():
            level = (ta == typeA) + (tb == typeB)
            if match(ta, tb):
                op = cast(
                    Callable[Concatenate[Any, Any, P], R], self.table.get((ta, tb))
                )
                matches[level].append((op, False))
            elif match(tb, ta):
                op = cast(
                    Callable[Concatenate[Any, Any, P], R], self.table.get((ta, tb))
                )
                matches[level].append((op, True))
        if len(matches[1]) == 1:
            return matches[1][0]
        elif len(matches[1]) == 0 and len(matches[0]) == 1:
            return matches[0][0]

        # No implementation found.
        return self.original, False


def binaryoperator(f: BinaryOperator[Any, Any, P, R]) -> BinaryOperatorDispatcher[P, R]:
    """Create a dispatcher for this binary operator.

    Parameters
    ----------
    f : BinaryOperator
        The binary operator that should be dispatched to the correct implementation.

    Returns
    -------
    BinaryOperatorDispatcher
        The dispatcher that selects the matching implementation for this binary
        operator.

    Examples
    --------
    >>> import pytensorlab as tl
    >>> from pytensorlab.datatypes.binops import binaryoperator
    >>> from pytensorlab.typing import ArrayType

    >>> @binaryoperator
    ... def binop(T1: tl.Tensor, T2: tl.Tensor) -> ArrayType:
    ...     pass

    Register an implementation for two specific tensor types using the register
    decorator:

    >>> @binop.register
    ... def binop_polyadic_tucker(
    ...     T1: tl.PolyadicTensor, T2: tl.TuckerTensor
    ... ) -> ArrayType:
    ...     pass

    To set the function to be called after swapping the `T1` and `T2` arguments, use,
    e.g.,

    >>> binop.swap = lambda x: x

    See Also
    --------
    BinaryOperatorDispatcher
    """
    dispatcher = BinaryOperatorDispatcher(f)
    return dispatcher


def inprod(T1: TensorType, T2: TensorType) -> NumberType:
    """Compute the inner product of two tensors.

    Compute the inner product of two tensors ``np.inner(tens2vec(T1), tens2vec(T2))``.

    Parameters
    ----------
    T1 : TensorType
        First tensor.
    T2 : TensorType
        Second tensor.

    Returns
    -------
    NumberType
        Inner product of `T1` and `T2`.

    Raises
    ------
    ValueError
        If `T1` and `T2` have a different number of dimensions.
    ValueError
        If `T1` and `T2` have a different shape.
    """
    if T1.ndim != T2.ndim:
        raise ValueError(
            f"the tensors have a different number of dimensions: {T1.ndim} != {T2.ndim}"
        )
    if T1.shape != T2.shape:
        raise ValueError(
            f"dimensions of the tensors do not match: T1 has dimensions "
            f"{T1.shape} and T2 has dimensions {T2.shape}"
        )

    return _inprod(T1, T2)


@binaryoperator
def _inprod(T1: TensorType, T2: TensorType) -> NumberType:
    raise NotImplementedError(
        f"no (unique) implementation found for types {type(T1)} and {type(T2)}"
    )


_inprod.swap = lambda x: np.conj(x)


@_inprod.register
def _inprod_polyadic_polyadic(T1: PolyadicTensor, T2: PolyadicTensor) -> NumberType:
    res = np.sum(_mtkrprod_single(T1, T2.factors, 0) * T2.factors[0].conj())
    return cast(NumberType, res.item() if hasattr(res, "__getitem__") else res)


@_inprod.register
def _inprod_polyadic_tucker(T1: PolyadicTensor, T2: TuckerTensor) -> NumberType:
    W = [u.conj().T @ v for v, u in zip(T1.factors, T2.factors)]
    res = np.sum(_mtkrprod_single(T2.core.conj(), W, 0, conjugate=False) * W[0])
    return cast(NumberType, res.item() if hasattr(res, "__getitem__") else res)


@_inprod.register
def _inprod_polyadic_array(T1: PolyadicTensor, T2: ArrayType) -> NumberType:
    operands: tuple[ArrayType | MatrixType | tuple[int, ...], ...] = (
        T2.conj(),
        tuple(range(T2.ndim)),
    )
    for i, f in enumerate(T1.factors):
        operands += (f, (i, T1.ndim))

    res = tlb.einsum(*operands, optimize="optimal")
    return cast(NumberType, res.item() if hasattr(res, "__getitem__") else res)


@_inprod.register
def _inprod_tucker_tucker(T1: TuckerTensor, T2: TuckerTensor) -> NumberType:
    W = [v.conj().T @ u for u, v in zip(T1.factors, T2.factors)]
    S = tmprod(T2.core.conj(), W, range(T1.ndim), "T")
    res = tlb.tensordot(T1.core, S, axes=T1.ndim)
    return cast(NumberType, res.item() if hasattr(res, "__getitem__") else res)


@_inprod.register
def _inprod_tucker_array(T1: TuckerTensor, T2: ArrayType) -> NumberType:
    return _inprod_array_array(T1.core, tmprod(T2, T1.factors, range(T1.ndim), "H"))


@_inprod.register
def _inprod_array_array(T1: ArrayType, T2: ArrayType) -> NumberType:
    res = tlb.tensordot(T1, T2.conj(), axes=T1.ndim)
    return cast(NumberType, res.item() if hasattr(res, "__getitem__") else res)


@_inprod.register
def _inprod_partial_array(T1: PartialTensor, T2: ArrayType) -> NumberType:
    res = np.vdot(T2[T1.indices], T1.data)
    return cast(NumberType, res.item() if hasattr(res, "__getitem__") else res)


@_inprod.register
def _inprod_partial_polyadic(T1: PartialTensor, T2: PolyadicTensor) -> NumberType:
    res = np.vdot(T2._entry(T1.indices), T1.data)
    return cast(NumberType, res.item() if hasattr(res, "__getitem__") else res)


# Same as previous function but can not be combined by using Tensor as the type hint
# for T2: this causes 2 matching level 0 implementations in for example inprod(sparse,
# sparse).
@_inprod.register
def _inprod_partial_tucker(T1: PartialTensor, T2: TuckerTensor) -> NumberType:
    res = np.vdot(T2._entry(T1.indices), T1.data)
    return cast(NumberType, res.item() if hasattr(res, "__getitem__") else res)


@_inprod.register
def _inprod_partial_partial(T1: PartialTensor, T2: PartialTensor) -> NumberType:
    _, comm1, comm2 = np.intersect1d(
        T1.flat_indices, T2.flat_indices, assume_unique=True, return_indices=True
    )
    res = np.sum(T1.data[comm1] * T2.data[comm2].conj())
    return cast(NumberType, res.item() if hasattr(res, "__getitem__") else res)


@_inprod.register
def _inprod_hankel_polyadic(T1: HankelTensor, T2: PolyadicTensor) -> NumberType:
    res = np.sum(_mtkrprod_single(T1, T2.factors, 0) * T2.factors[0].conj())
    return cast(NumberType, res.item() if hasattr(res, "__getitem__") else res)


@_inprod.register
def _inprod_hankel_tucker(T1: HankelTensor, T2: TuckerTensor) -> NumberType:
    if math.prod(T2.shape) <= math.prod(T2.core_shape):
        return _inprod_array_array(np.array(T1), np.array(T2))
    tmp = cast(ArrayType, tmprod(T1, T2.factors, range(T1.ndim), "H"))
    res = tlb.tensordot(T2.core.conj(), tmp, axes=T1.ndim)
    return cast(NumberType, res.item() if hasattr(res, "__getitem__") else res)


@_inprod.register
def _inprod_hankel_array(T1: HankelTensor, T2: ArrayType) -> NumberType:
    tmp = dehankelize(T2, order=T1.order, axis=T1.axis, method=np.sum)
    return _inprod_array_array(T1._data, tmp)


@_inprod.register
def _inprod_hankel_hankel(T1: HankelTensor, T2: HankelTensor) -> NumberType:
    if T1.axis != T2.axis or T1.hankel_shape != T2.hankel_shape:
        return _inprod_array_array(np.array(T1), np.array(T2))

    N = T1._data.shape[T1.axis]
    fft_ones = tuple(fft(np.ones((s,)), N) for s in T1.hankel_shape)
    weights = np.round(np.real(ifft(np.multiply.reduce(fft_ones))))
    after_axes = T1.ndim - T1.axis - T1.order
    data1 = T1._data * weights[(slice(None),) + (None,) * after_axes]
    return _inprod_array_array(data1, T2._data)


@_inprod.register
def _inprod_partial_hankel(T1: PartialTensor, T2: HankelTensor) -> NumberType:
    res = np.vdot(T2[T1.indices], T1.data)
    return cast(NumberType, res.item() if hasattr(res, "__getitem__") else res)


@_inprod.register
def _inprod_tensortrain_tensortrain(
    T1: TensorTrainTensor, T2: TensorTrainTensor
) -> NumberType:
    res = T1.cores[-1] @ T2.cores[-1].conj().T
    for c0, c1 in zip(
        T1.cores3[-2 : -T1.ndim - 1 : -1], T2.cores3[-2 : -T1.ndim - 1 : -1]
    ):
        if c0.shape[2] > c1.shape[2]:
            res = (c0 @ res).reshape(c0.shape[0], -1)
            res = res @ c1.conj().reshape(c1.shape[0], -1).T
        else:
            res = (c1.conj() @ res.T).reshape(c1.shape[0], -1)
            res = c0.reshape(c0.shape[0], -1) @ res.T
    return res.item()


@_inprod.register
def _inprod_array_tensortrain(T1: ArrayType, T2: TensorTrainTensor) -> NumberType:
    return _inprod_array_array(T1, np.array(T2))


@_inprod.register
def _inprod_tucker_tensortrain(T1: TuckerTensor, T2: TensorTrainTensor) -> NumberType:
    res = tmprod(T2, T1.factors, range(T1.ndim), transpose="H")
    return _inprod_array_array(T1.core, np.array(res))


def _is_sequence_numbertype(seq: Any) -> TypeGuard[Sequence[NumberType]]:
    """Check if the argument is a sequence of number type elements."""
    return isinstance(seq, Sequence) and all(
        isinstance(elem, int | float | complex) for elem in seq
    )


@_inprod.register
def _inprod_polyadic_tensortrain(
    T1: PolyadicTensor, T2: TensorTrainTensor
) -> NumberType:
    terms = (tuple(f.conj().ravel() for f in term.factors) for term in T1.term_iter())
    inprod_terms = [tvprod(T2, factors, list(range(T1.ndim))) for factors in terms]
    assert _is_sequence_numbertype(inprod_terms)
    return np.conj(sum(inprod_terms))


@_inprod.register
def _inprod_partial_tensortrain(T1: PartialTensor, T2: TensorTrainTensor) -> NumberType:
    res = np.vdot(T2[T1.indices], T1.data)
    return cast(NumberType, res.item() if hasattr(res, "__getitem__") else res)


@_inprod.register
def _inprod_hankel_tensortrain(T1: HankelTensor, T2: TensorTrainTensor) -> NumberType:
    tmp = np.array(T2)
    return _inprod_hankel_array(T1, tmp)


@_inprod.register
def _inprod_deferred_array(T1: DeferredResidual, T2: ArrayType) -> NumberType:
    return _inprod(T1.T1, T2) - _inprod(T1.T2, T2)


@_inprod.register
def _inprod_deferred_tensor(T1: DeferredResidual, T2: Tensor) -> NumberType:
    return _inprod(T1.T1, T2) - _inprod(T1.T2, T2)


def matdot(T1: TensorType, T2: TensorType, row: int = 0) -> MatrixType:
    """Multiply a matricized tensor with a conjugated transposed matricized tensor.

    Compute the product of a matricized tensor and a conjugated transposed matricized
    tensor ``tens2mat(T1, row) @ tens2mat(T2, row).conj().T``, in which `T1` and `T2`
    are tensors with compatible shapes.

    Parameters
    ----------
    T1 : TensorType
        First tensor.
    T2 : TensorType
        Second tensor.
    row : int, default = 0
        Index that indicates the mode of the tensors that corresponds to the rows of the
        matricizations.

    Returns
    -------
    MatrixType
        The product of the two matricizations.

    Raises
    ------
    ValueError
        If `T1` and `T2` have a different number of dimensions.
    ValueError
        If `T1` and `T2` have a different shape.
    """
    if T1.ndim != T2.ndim:
        raise ValueError(
            f"tensors are of different order: T1 is of order {T1.ndim}"
            f", while T2 is of order {T2.ndim}"
        )
    if tuple(s for i, s in enumerate(T1.shape) if i != row) != tuple(
        s for i, s in enumerate(T2.shape) if i != row
    ):
        raise ValueError(
            f"shapes do not match: {T1.shape} is not equal to {T2.shape} "
            "in each axis besides {row}"
        )
    row = normalize_axes(row, T1.ndim, fill=False)[0]
    return _matdot(T1, T2, row)


@binaryoperator
def _matdot(T1: TensorType, T2: TensorType, row: int) -> MatrixType:
    raise NotImplementedError(
        f"no (unique) implementation found for types {type(T1)} and {type(T2)}"
    )


_matdot.swap = lambda x: x.conj().T


@_matdot.register
def _matdot_polyadic_polyadic(
    T1: PolyadicTensor, T2: PolyadicTensor, row: int
) -> MatrixType:
    AHB = inprod_kr(T2.factors, T1.factors, exclude=row).T
    res = (T1.factors[row] @ AHB) @ T2.factors[row].conj().T
    return res


@_matdot.register
def _matdot_polyadic_tucker(
    T1: PolyadicTensor, T2: TuckerTensor, row: int
) -> MatrixType:
    f = [v.conj().T @ u for u, v in zip(T1.factors, T2.factors)]
    M = mtkrprod(T2.core, f, row).conj().T
    res = np.matmul(np.matmul(T1.factors[row], M), T2.factors[row].conj().T)
    return res


@_matdot.register
def _matdot_polyadic_array(T1: PolyadicTensor, T2: ArrayType, row: int) -> MatrixType:
    res = np.matmul(T1.factors[row], mtkrprod(T2, T1.factors, row).conj().T)
    return res


@_matdot.register
def _matdot_tucker_tucker(T1: TuckerTensor, T2: TuckerTensor, row: int) -> MatrixType:
    if math.prod(T2.coreshape) > math.prod(T1.coreshape):
        return _matdot_tucker_tucker(T2, T1, row).conj().T
    col = _complement_indices(row, T1.ndim)
    f = [
        v.conj().T @ u
        for i, (u, v) in enumerate(zip(T1.factors, T2.factors))
        if i in col
    ]
    tmp = tlb.tensordot(tmprod(T1.core, f, col), T2.core.conj(), (col, col))
    return T1.factors[row] @ tmp @ T2.factors[row].conj().T


@_matdot.register
def _matdot_tucker_array(T1: TuckerTensor, T2: ArrayType, row: int) -> MatrixType:
    f, col = zip(*[(f, i) for i, f in enumerate(T1.factors) if i != row])
    f = cast(tuple[MatrixType, ...], f)
    col = cast(tuple[int, ...], col)
    # TODO can be replaced by mtkronprod (when implemented).
    # This avoids the need for the line above.
    T2c = tmprod(T2, f, col, "H")
    res = T1.factors[row] @ _matdot_array_array(T1.core, T2c, row)
    return res


@_matdot.register
def _matdot_array_array(T1: ArrayType, T2: ArrayType, row: int) -> MatrixType:
    col = _complement_indices(row, T1.ndim)
    return cast(MatrixType, tlb.tensordot(T1, T2.conj(), (col, col)))


@_matdot.register
def _matdot_partial_array(T1: PartialTensor, T2: ArrayType, row: int) -> MatrixType:
    return cast(MatrixType, tens2mat(T1, row) @ tens2mat(T2, row).conj().T)


# Scipy always returns a sparse matrix when matrix multiplying two sparse matrices.
# Therefore, if the result is (almost) dense, which will occur often, it will be stored
# inefficiently. To avoid this, the sparse tensor with the most nonzeros is converted to
# a dense matrix.
@_matdot.register
def _matdot_partial_partial(
    T1: PartialTensor, T2: PartialTensor, row: int
) -> MatrixType:
    if len(T1.data) / math.prod(T1.shape) < len(T2.data) / math.prod(T2.shape):
        return _matdot_partial_partial(T2, T1, row).conj().T
    if isinstance(T1, IncompleteTensor):
        T1 = SparseTensor._from_incomplete(T1)
    return tens2mat(np.array(T1), row) @ tens2mat(T2, row).conj().T


@_matdot.register
def _matdot_partial_polyadic(
    T1: PartialTensor, T2: PolyadicTensor, row: int
) -> MatrixType:
    return _mtkrprod_single(T1, T2.factors, row) @ T2.factors[row].conj().T


@_matdot.register
def _matdot_partial_tucker(T1: PartialTensor, T2: TuckerTensor, row: int) -> MatrixType:
    col = _complement_indices(row, T1.ndim)
    factors = tuple(T2.factors[i] for i in col)
    if isinstance(T1, IncompleteTensor):
        T1 = SparseTensor._from_incomplete(T1)
    tmp = tens2mat(tmprod(T1, factors, col, "H"), row)
    return cast(
        MatrixType, tmp.dot(tens2mat(T2.core, row).conj().T) @ T2.factors[row].conj().T
    )


@_matdot.register
def _matdot_hankel_hankel(T1: HankelTensor, T2: HankelTensor, row: int) -> MatrixType:
    ishankelrow = T1.axis <= row < T1.axis + T1.order
    if (T1.axis != T2.axis or T1.order != T2.order) or (ishankelrow and T1.order == 2):
        return _matdot(np.array(T1), np.array(T2), row)

    hankel_shape = tuple(s for n, s in enumerate(T1.hankel_shape) if n != row - T1.axis)
    row_shape = T1.shape[row] - 1 if ishankelrow else 0
    N = T1._data.shape[T1.axis] - row_shape
    fft_ones = tuple(fft(np.ones((s,)), N) for s in hankel_shape)
    weights = np.round(np.real(ifft(np.multiply.reduce(fft_ones))))
    if ishankelrow:
        data1 = hankelize(T1._data, order=2, axis=T1.axis, breakpoints=row_shape)
        data2 = hankelize(T2._data, order=2, axis=T1.axis, breakpoints=row_shape)
    else:
        data1 = T1._data
        data2 = T2._data
    after_axes = T1.ndim - T1.axis - T1.order
    data1 = data1 * weights[(slice(None),) + (None,) * after_axes]
    if ishankelrow:
        row = T1.axis
    elif row > T1.axis:
        row -= T1.order - 1
    return _matdot_array_array(data1, data2, row=row)


def _matdot_tt_left2right(
    T1: TensorTrainTensor, T2: TensorTrainTensor, row: int
) -> MatrixType:
    if row == 0:
        return np.ones((1, 1))
    res = T1.cores[0].T @ T2.cores[0].conj()
    for c1, c2 in zip(T1.cores[1:row], T2.cores[1:row]):
        if c1.shape[0] < c2.shape[0]:
            res = (res @ c2.conj().reshape(c2.shape[0], -1)).reshape(-1, c2.shape[2])
            res = c1.reshape(-1, c1.shape[2]).T @ res
        else:
            res = (res.T @ c1.reshape(c1.shape[0], -1)).reshape(-1, c1.shape[2])
            res = res.T @ c2.conj().reshape(-1, c2.shape[2])
    return res


def _matdot_tt_right2left(
    T1: TensorTrainTensor, T2: TensorTrainTensor, row: int
) -> MatrixType:
    if row == T1.ndim - 1:
        return np.ones((1, 1))
    res = T1.cores[-1] @ T2.cores[-1].conj().T
    N = T1.ndim
    for c1, c2 in zip(T1.cores[N - 2 : row : -1], T2.cores[N - 2 : row : -1]):
        if c1.shape[2] < c2.shape[2]:
            res = c2.conj() @ res.T
            res = c1.reshape(c1.shape[0], -1) @ res.reshape(res.shape[0], -1).T
        else:
            res = c1 @ res
            res = res.reshape(res.shape[0], -1) @ c2.conj().reshape(c2.shape[0], -1).T

    return res


@_matdot.register
def _matdot_tensortrain_tensortrain(
    T1: TensorTrainTensor, T2: TensorTrainTensor, row: int
) -> MatrixType:
    a = _matdot_tt_left2right(T1, T2, row)
    b = _matdot_tt_right2left(T1, T2, row)

    core1 = T1.cores3[row]
    core2 = T2.cores3[row]

    if core1.shape[2] > core2.shape[2]:
        core1 = core1 @ b
    else:
        core2 = core2 @ b.conj().T

    if core1.shape[0] > core2.shape[0]:
        core1 = (a.T @ core1.reshape(core1.shape[0], -1)).reshape(core2.shape)
    else:
        core2 = (a.conj() @ core2.reshape(core2.shape[0], -1)).reshape(core1.shape)

    return np.tensordot(core1, core2.conj(), axes=((0, 2), (0, 2)))


@_matdot.register
def _matdot_tensortrain_tucker(
    T1: TensorTrainTensor, T2: TuckerTensor, row: int
) -> MatrixType:
    return tens2mat(np.array(T1), row) @ tens2mat(T2.conj(), row).T


@_matdot.register
def _matdot_tensortrain_polyadic(
    T1: TensorTrainTensor, T2: PolyadicTensor, row: int
) -> MatrixType:
    return tens2mat(np.array(T1), row) @ tens2mat(T2.conj(), row).T


@_matdot.register
def _matdot_tensortrain_array(
    T1: TensorTrainTensor, T2: ArrayType, row: int
) -> MatrixType:
    return tens2mat(np.array(T1), row) @ tens2mat(T2.conj(), row).T


@_matdot.register
def _matdot_tensortrain_hankel(
    T1: TensorTrainTensor, T2: HankelTensor, row: int
) -> MatrixType:
    return tens2mat(np.array(T1), row) @ tens2mat(T2.conj(), row).T


@_matdot.register
def _matdot_tensortrain_partial(
    T1: TensorTrainTensor, T2: PartialTensor, row: int
) -> MatrixType:
    return tens2mat(np.array(T1), row) @ tens2mat(T2.conj(), row).T


@_matdot.register
def _matdot_deferred_array(T1: DeferredResidual, T2: ArrayType, row: int) -> MatrixType:
    return _matdot(T1.T1, T2, row) - _matdot(T1.T2, T2, row)


@_matdot.register
def _matdot_deferred_tensor(T1: DeferredResidual, T2: Tensor, row: int) -> MatrixType:
    return _matdot(T1.T1, T2, row) - _matdot(T1.T2, T2, row)


def _add_polyadic_polyadic(T1: PolyadicTensor, T2: PolyadicTensor) -> PolyadicTensor:
    if T1.ndim != T2.ndim:
        raise ValueError(
            f"tensors are of different order: T1 is of order {T1.ndim}, "
            f"while T2 is of order {T2.ndim}; broadcasting is not supported"
        )
    if not T1.shape == T2.shape:
        raise ValueError(
            f"shapes do not match: {T1.shape} is not equal to {T2.shape}; "
            f"broadcasting is not supported"
        )
    return PolyadicTensor([np.hstack(z) for z in zip(T1.factors, T2.factors)])


def _add_tucker_polyadic(T1: TuckerTensor, T2: PolyadicTensor) -> TuckerTensor:
    if T1.ndim != T2.ndim:
        raise ValueError(
            f"tensors are of different order: T1 is of order {T1.ndim}, "
            f"while T2 is of order {T2.ndim}; broadcasting is not supported"
        )
    if not T1.shape == T2.shape:
        raise ValueError(
            f"shapes do not match: {T1.shape} is not equal to {T2.shape}; "
            f"broadcasting is not supported"
        )

    N = T2.ndim
    R = T2.nterm
    coreshape = [i + R for i in T1.coreshape]

    core = np.zeros(coreshape, dtype=np.result_type(T1.dtype, T2.dtype))
    np.fill_diagonal(core[(slice(R),) * N], 1)
    core[(slice(R, None),) * N] = T1.core

    factors = [np.concatenate(f, axis=1) for f in zip(T2.factors, T1.factors)]

    return TuckerTensor(factors, core)


def _add_tucker_tucker(T1: TuckerTensor, T2: TuckerTensor) -> TuckerTensor:
    if T1.ndim != T2.ndim:
        raise ValueError(
            f"tensors are of different order: T1 is of order {T1.ndim}"
            f", while T2 is of order {T2.ndim}; broadcasting is not supported"
        )
    if not T1.shape == T2.shape:
        raise ValueError(
            f"shapes do not match: {T1.shape} is not equal to {T2.shape}; "
            f"broadcasting is not supported"
        )

    coreshape = [i + j for i, j in zip(T1.coreshape, T2.coreshape)]

    core = np.zeros(coreshape, dtype=np.result_type(T1.dtype, T2.dtype))
    core[tuple(slice(i) for i in T1.coreshape)] = T1.core
    core[tuple(slice(i, None) for i in T1.coreshape)] = T2.core

    factors = [np.concatenate(f, axis=1) for f in zip(T1.factors, T2.factors)]

    return TuckerTensor(factors, core)


def _add_tensortrain_tensortrain(
    T1: TensorTrainTensor, T2: TensorTrainTensor
) -> TensorTrainTensor:
    if T1.ndim != T2.ndim:
        raise ValueError(
            f"T does not have the correct number of dimensions: {T2.ndim} while"
            f"expected {T1.ndim}"
        )
    if not T1.shape == T2.shape:
        i = findfirst(s1 != s2 for s1, s2 in zip(T1.shape, T2.shape))
        raise ValueError(
            f"shape of T does not match in index {i}: {T2.shape[i]} while expected "
            f"{T1.shape[i]}"
        )

    first_core = np.concatenate((T1.cores[0], T2.cores[0]), axis=1)
    last_core = np.concatenate((T1.cores[-1], T2.cores[-1]), axis=0)

    middle_cores: list[ArrayType] = []
    for a, b in zip(T1.cores[1:-1], T2.cores[1:-1]):
        r_a_0, i_a, r_a_1 = a.shape
        r_b_0, i_b, r_b_1 = b.shape
        assert i_a == i_b

        c = np.zeros(((r_a_0 + r_b_0), i_a, (r_a_1 + r_b_1)), dtype=first_core.dtype)
        c[:r_a_0, :, :r_a_1] = a
        c[r_a_0:, :, r_a_1:] = b

        middle_cores.append(c)

    cores = [first_core] + middle_cores + [last_core]

    return TensorTrainTensor(cores)


_add_tucker = cast(singledispatchmethod, TuckerTensor.__add__)
_add_tucker.register(PolyadicTensor)(_add_tucker_polyadic)
_add_tucker.register(TuckerTensor)(_add_tucker_tucker)
_add_polyadic = cast(singledispatchmethod, PolyadicTensor.__add__)
_add_polyadic.register(PolyadicTensor)(_add_polyadic_polyadic)
_add_polyadic.register(TuckerTensor)(lambda T1, T2: _add_tucker_polyadic(T2, T1))
_add_tensortrain = cast(singledispatchmethod, TensorTrainTensor.__add__)
_add_tensortrain.register(TensorTrainTensor)(_add_tensortrain_tensortrain)


def residual(
    T1: TensorType,
    T2: TensorType,
    defer: bool | None = None,
    _use_cached_frob: bool = False,
) -> TensorType:
    """Compute the difference between two tensors.

    Computes the difference ``T1 - T2``. Depending on the type of `T1` and `T2` the
    actual computation of the difference might be deferred and a `DeferredResidual`
    object is returned. This way several operations on this residual can be computed
    more efficiently by exploiting any structure present in `T1` and/or `T2`. The
    automatic selection of the return type can be controlled by the `defer` option.

    Parameters
    ----------
    T1 : TensorType
        First tensor in the difference.
    T2 : TensorType
        Second tensor in the difference.
    defer : bool, optional
        Defer the computation of the difference. By default, the return type depends on
        the types of `T1` and `T2`. To force the actual computation of the difference as
        an array, set `defer` to False. To force the a `DeferredResidual`, set `defer`
        to True.
    _use_cached_frob : bool
        Cache the squared Frobenius norm of `T2`, such that it does not have to be
        recomputed when computing the Frobenius norm of the difference again. Note that
        accuracy can be lost due to the squaring. If the residual is small, large values
        that are approximately equal will be subtracted, leading to numerical errors.
        By squaring the norm, the maximum achievable accuracy then becomes the square
        root of machine precision.

    Returns
    -------
    ArrayType
        The residual between `T1` and `T2`.

    See Also
    --------
    .DeferredResidual

    Notes
    -----
    For specific type combinations, a more efficient format might be returned. For
    example

    >>> import pytensorlab as tl
    >>> A = tl.PolyadicTensor.random((3, 4, 5), 2)
    >>> B = tl.PolyadicTensor.random((3, 4, 5), 1)
    >>> type(tl.residual(A, B))
    pytensorlab.datatypes.polyadic.PolyadicTensor
    """
    if defer is None:
        # Let the dispatch table decide which format to return.
        return _residual(T1, T2, _use_cached_frob)
    if defer:
        return DeferredResidual(T1, T2, _use_cached_frob)
    return _residual_in_place(T1, T2)


def _residual_in_place(T1: TensorType, T2: TensorType) -> TensorType:
    T1_array = np.asarray(T1)
    if T1_array is T1:
        return T1_array - np.asarray(T2)
    T1_array -= np.asarray(T2)
    return T1_array


@binaryoperator
def _residual(T1: TensorType, T2: TensorType, _use_cached_frob: bool) -> TensorType:
    return _residual_in_place(T1, T2)


@_residual.register
def _residual_polyadic_polyadic(
    T1: PolyadicTensor, T2: PolyadicTensor, _use_cached_frob: bool
) -> PolyadicTensor:
    factors = [
        np.concatenate((f1, f2 * (-1 if n == 0 else 1)), 1)
        for n, (f1, f2) in enumerate(zip(T1.factors, T2.factors))
    ]
    return PolyadicTensor(factors)


@_residual.register
def _residual_dense_incomplete(
    T1: DenseTensor, T2: IncompleteTensor, _use_cached_frob: bool, _negate: bool = False
) -> IncompleteTensor:
    data = T1[T2.indices] - T2._data if not _negate else T2._data - T1[T2.indices]
    return IncompleteTensor(
        data,
        indices=T2.indices,
        shape=T2.shape,
        flat_indices=T2.flat_indices,
        _check_unique_ind=False,
        _check_bounds=False,
    )


@_residual.register
def _residual_incomplete_dense(
    T1: IncompleteTensor, T2: DenseTensor, _use_cached_frob: bool
) -> IncompleteTensor:
    res = _residual_dense_incomplete(
        T2,
        T1,
        _use_cached_frob,
        _negate=True,  # type:ignore
    )
    return cast(IncompleteTensor, res)


@_residual.register
def _residual_tensor_tensor(
    T1: Tensor, T2: Tensor, _use_cached_frob: bool
) -> DeferredResidual:
    return DeferredResidual(T1, T2, _use_cached_frob)


@overload
def _negate(x: Tensor) -> Tensor: ...


@overload
def _negate(x: ArrayType) -> ArrayType: ...


@overload
def _negate(x: TensorType) -> TensorType: ...


def _negate(x: TensorType) -> TensorType:
    return -x


_residual.swap = _negate

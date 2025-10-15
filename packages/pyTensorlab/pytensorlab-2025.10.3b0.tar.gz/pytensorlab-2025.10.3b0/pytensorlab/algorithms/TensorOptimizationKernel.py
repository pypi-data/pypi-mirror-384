"""Template for tensor optimization functions."""

from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from functools import wraps
from typing import (
    Any,
    Concatenate,
    Generic,
    NoReturn,
    Protocol,
    TypeVar,
    cast,
    overload,
)

import numpy as np
from typing_extensions import ParamSpec

from pytensorlab.datatypes import Tensor
from pytensorlab.optimization.problem import PointType
from pytensorlab.typing import ArrayType, MatrixType, VectorType


class TensorOptimizationKernel(Generic[PointType], metaclass=ABCMeta):
    """An abstract base kernel for tensor optimization.

    Template for tensor optimization problems that groups the evaluation of the
    objective function (:meth:`.objfun`), the gradient (:meth:`.gradient`), the Hessian
    (:meth:`.hessian`) or an approximation thereof, and the Hessian times vector product
    (:meth:`.hessian_vector`). `TensorOptimizationKernel` requires serialization and
    deserialization routines that convert between a tensor type `PointType` and a vector
    of type `VectorType`. Serialized versions of all the methods that automatically
    perform deserialization/serialization are provided using the ``_serialized`` suffix.

    Cached variables can be computed in the :meth:`.update_cache` method of a
    `TensorOptimizationKernel`. This method can be called automatically before calling a
    method by adding the :func:`.cached` decorator. This decorator only updates the
    cache if the variables have been modified since the last call.

    See Also
    --------
    .PolyadicKernel
        Optimization routines for computing a canonical polyadic decomposition.
    .LMLRAKernel
        Optimization routines for computing a low multilinear rank approximation.
    .TuckerKernel
        Optimization routines for computing a low multilinear rank approximation, using
        only the factor matrices as variables.
    cached
        Decorator methods that use cached information.
    """

    def __init__(self) -> None:
        """Construct a new `TensorOptimizationKernel`."""
        # The `_zcached` attribute is used to store the variables used in the last cache
        # update; see `cached`.
        self._zcached: ArrayType = np.empty((1,))
        self.calls: dict[str, int] = {}

    @abstractmethod
    def isvalid(self, z: PointType) -> bool:
        """Check if the combination of kernel and optimization variables is valid.

        Checks if the combination of parameters, data and optimization variables `z` is
        valid. If True, all implemented kernel methods can be computed.

        Parameters
        ----------
        z : PointType
            The optimization variables that need to be checked.

        Returns
        -------
        bool
            True if all implemented kernel methods can be computed.
        """
        ...

    def update_cache(self, z: PointType) -> None:
        """Update cached data.

        Updates cached data stored in this kernel based on the given optimization
        variables `z`.

        Parameters
        ----------
        z : PointType
            Variables used to compute the cached data.

        See Also
        --------
        cached
        """
        raise NotImplementedError

    @abstractmethod
    def objfun(self, z: PointType, /) -> float:
        """Compute the objective function value.

        Parameters
        ----------
        z : PointType
            Optimization variables for which to compute the objective function value.

        Returns
        -------
        float
            The objective function value.
        """
        ...

    def objfun_serialized(self, z: VectorType) -> float:
        """Compute the objective function value for serialized variables.

        Computes the objective function value after deserializing the optimization
        variables `z`.

        Parameters
        ----------
        z : VectorType
            Serialized optimization variables in which the objective function value is
            evaluated.

        Returns
        -------
        float
            The objective function value.

        See Also
        --------
        objfun, deserialize
        """
        zs = self.deserialize(z)
        return self.objfun(zs)

    @abstractmethod
    def gradient(self, z: PointType, /) -> PointType:
        """Compute the gradient.

        Computes the gradient of the objective function evaluated in the optimization
        variables `z`.

        Parameters
        ----------
        z : PointType
            Optimization variables in which the gradient of the objective function is
            evaluated.

        Returns
        -------
        PointType
            The computed gradient in the same format as the optimization variables.

        See Also
        --------
        objfun
        """
        ...

    def gradient_serialized(self, z: VectorType) -> VectorType:
        """Compute the serialized gradient for serialized variables.

        Computes the gradient of the objective function evaluated in the serialized
        optimization variables `z`.

        Parameters
        ----------
        z : VectorType
            Serialized optimization variables in which the gradient of the objective
            function is evaluated.

        Returns
        -------
        VectorType
            The serialized computed gradient.

        See Also
        --------
        objfun, gradient, deserialize
        """
        zs = self.deserialize(z)
        return self.serialize(self.gradient(zs))

    def hessian(self, z: PointType, /) -> MatrixType:
        """Compute (an approximation of) the Hessian.

        Computes the Hessian or a positive semi-definite approximation of the Hessian of
        the objective function, evaluated in the optimization variables `z`. Whether the
        Hessian or an approximation is used depends on the chosen implementation.

        Parameters
        ----------
        z : PointType
            The optimization variables in which the Hessian is evaluated.

        Returns
        -------
        MatrixType
            The (approximation of the) Hessian evaluated at `z`.

        See Also
        --------
        objfun, hessian_serialized
        """
        raise NotImplementedError

    def hessian_serialized(self, z: VectorType) -> MatrixType:
        """Compute (an approximation of) the Hessian for serialized variables.

        Computes the Hessian or a positive semi-definite approximation of the Hessian
        of the objective function, evaluated in the serialized optimization variables
        `z`. Whether the Hessian or an approximation is used depends on the chosen
        implementation.

        Parameters
        ----------
        z : VectorType
            Serialized optimization variables in which the Hessian is evaluated.

        Returns
        -------
        MatrixType
            The (approximation of the) Hessian evaluated at `z`.

        See Also
        --------
        objfun, hessian, deserialize
        """
        zs = self.deserialize(z)
        return self.hessian(zs)

    def hessian_vector(self, z: PointType, x: PointType, /) -> PointType:
        """Compute the Hessian times vector product.

        Computes the Hessian times vector product ``self.hessian(z) @
        self.serialize(x)``, where the Hessian is evaluated in the optimization
        variables `z`. The vector `x` should be in the same format as `z`. Whether the
        Hessian or an approximation is used depends on the chosen implementation.


        Parameters
        ----------
        z : PointType
            The optimization variables in which the Hessian is evaluated.
        x : PointType
            The (deserialized) vector by which the Hessian is multiplied.

        Returns
        -------
        PointType
            The computed Hessian times vector product in the same format as the
            optimization variables.

        See Also
        --------
        objfun, hessian, hessian_vector_serialized

        """
        raise NotImplementedError

    def hessian_vector_serialized(self, z: VectorType, x: VectorType) -> VectorType:
        """Compute the serialized Hessian times vector product for serialized variables.

        Computes the Hessian times vector product ``self.hessian_serialized(z) @ x``,
        where the Hessian is evaluated in the serialized optimization variables `z`.
        Whether the Hessian or an approximation is used depends on the chosen
        implementation.

        Parameters
        ----------
        z : VectorType
            Serialized optimization variables in which the Hessian is evaluated.
        x : VectorType
            The vector by which the Hessian is multiplied.

        Returns
        -------
        VectorType
            The computed Hessian times vector product.

        See Also
        --------
        objfun, hessian, hessian_vector, deserialize, serialize
        """
        zs = self.deserialize(z)
        xs = self.deserialize(x)
        return self.serialize(self.hessian_vector(zs, xs))

    @abstractmethod
    def deserialize(self, z: VectorType) -> PointType:
        """Deserialize optimization variables.

        Parameters
        ----------
        z : VectorType
            The variables as a vector to be deserialized.

        Returns
        -------
        PointType
            The variables formatted as a tensor.
        """
        ...

    @abstractmethod
    def serialize(self, z: PointType) -> VectorType:
        """Serialize optimization variables.

        Parameters
        ----------
        z : PointType
            The optimization variables to be serialized.

        Returns
        -------
        VectorType
            The serialized variables as a vector.
        """
        ...


TOK = TypeVar("TOK", bound=TensorOptimizationKernel)
P = ParamSpec("P")


def count_calls(
    f: Callable[Concatenate[TOK, P], Any],
) -> Callable[Concatenate[TOK, P], Any]:
    """Count the number of calls to a given function.

    Count the number of times a method `f` is being called within the `calls` field.

    Parameters
    ----------
    f : Callable[[TensorOptimizationKernel, ...], Any]
        Function of which the number of calls will be counted.

    Returns
    -------
    Callable[[TensorOptimizationKernel, ...], Any]
       Function for which the number of calls is logged.
    """

    @wraps(f)
    def wrapper(self: TOK, *args: P.args, **kwargs: P.kwargs):
        self.calls[f.__name__] = self.calls.get(f.__name__, 0) + 1
        return f(self, *args, **kwargs)

    return wrapper


class HasData(Protocol):
    """Enforce availability of `_data` member."""

    _data: VectorType


KernelT = TypeVar("KernelT", bound=TensorOptimizationKernel)
"""A tensor optimization kernel."""

TensorT = TypeVar("TensorT", bound=HasData)
"""A tensor type having a _data attribute."""

OutT = TypeVar("OutT")
"""An output type."""


# Ideally, the type of f and the return type should be CachableKernelMethod[KernelT,
# TensorT, P, OutT]. This works with pyright, but, currently, mypy cannot deal with a
# combination of positional arguments and ParamSpec.
def cached(
    f: Callable[Concatenate[KernelT, TensorT, P], OutT],
) -> Callable[Concatenate[KernelT, TensorT, P], OutT]:
    """Update cache if optimization variables have changed.

    Tests if the optimization variables `z` have changed compared to the last call to
    any cached method, and calls ``update_cache(z)`` to update the cache if this is the
    case. Next, `f` is called.

    Parameters
    ----------
    f : Callable[[KernelT, TensorT, ...], OutT]
        Method in an implementation of `TensorOptimizationKernel` that accepts the
        variables `z` as first argument. The variables `z` are used to determine if the
        :meth:`~TensorOptimizationKernel.update_cache` method needs to be called before
        calling `f`. All remaining arguments are passed on as given.

    Returns
    -------
    Callable[[KernelT, TensorT, ...], OutT]
        A function that ensures cached variables are correct before evaluating `f`.

    Notes
    -----
    To test if the variables `z` have changed, the `_zcached` attribute of the
    object of `f` is used to store the variables used in the previous cached call.

    See Also
    --------
    TensorOptimizationKernel
    """

    @wraps(f)
    def wrapper(
        self: KernelT,
        z: TensorT,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> OutT:
        if not np.array_equal(z._data, self._zcached):
            self._zcached = z._data.copy()
            try:
                self.update_cache(z)
            except NotImplementedError:
                # Caching is not implemented, so ignore.
                pass
        return f(self, z, *args, **kwargs)

    return wrapper


_T = TypeVar("_T", bound=Tensor)
_TensorOrArray = TypeVar("_TensorOrArray", Tensor, ArrayType)


@overload
def ensure_deserialized(
    f: Callable[Concatenate[KernelT, _T, P], OutT],
) -> Callable[Concatenate[KernelT, _T, P], OutT]: ...


@overload
def ensure_deserialized(
    f: Callable[Concatenate[KernelT, ArrayType, P], Any],
) -> NoReturn: ...


def ensure_deserialized(
    f: Callable[Concatenate[KernelT, Any, P], OutT],
) -> Callable[Concatenate[KernelT, Any, P], OutT] | NoReturn:
    """Decorate function to ensure that its variables are deserialized.

    Create a wrapper function for `f`. The wrapped function first checks if its first
    argument is a subtype of `Tensor`. If not, it raises a :class:`ValueError`.

    Parameters
    ----------
    f : Callable[[KernelT, Any, ...], OutT]
        Function to be decorated

    Returns
    -------
    Callable[[KernelT, Any, ...], OutT]
        The decorated function. Raises a :class:`ValueError` if its first argument is
        not a subtype of `Tensor`.

    Notes
    -----
    The main use of this decorator is to inform users of the serialized method.
    """

    @wraps(f)
    def wrapper(
        kernel: KernelT, z: _TensorOrArray, *args: P.args, **kwargs: P.kwargs
    ) -> OutT:
        if not isinstance(z, Tensor):
            raise ValueError(
                f"variable is of type {type(z)}, but expected a subtype of Tensor; "
                f"did you mean to call {f.__name__}_serialized instead?"
            )
        return f(kernel, z, *args, **kwargs)

    return wrapper


F = TypeVar("F", bound=Callable[..., Any])


def ensure_use_gramian(f: F) -> F:
    """Decorate function to ensure that the `use_gramian` attribute is True.

    Create a wrapper function for `f`. The wrapped function first checks if the
    `use_gramian` attribute is True. If not, it raises a :class:`ValueError`.

    Parameters
    ----------
    f : F
        Function to be decorated

    Returns
    -------
    F
        The decorated function. Raises a :class:`ValueError` if the `use_gramian`
        attribute is False.
    """

    @wraps(f)
    def wrapper(self, z, *args):
        if not self.use_gramian:
            raise ValueError(f"{f.__name__} requires `use_gramian` set to True")
        return f(self, z, *args)

    return cast(F, wrapper)


def ensure_use_preconditioner(f: F) -> F:
    """Decorate function to ensure that the `use_preconditioner` attribute is True.

    Create a wrapper function for `f`. The wrapped function first checks if the
    `use_preconditioner` attribute is True. If not, it raises a :class:`ValueError`.

    Parameters
    ----------
    f : F
        Function to be decorated

    Returns
    -------
    F
        The decorated function. Raises a :class:`ValueError` if the `use_preconditioner`
        attribute is False.
    """

    @wraps(f)
    def wrapper(self, z, *args):
        if not self.use_preconditioner:
            raise ValueError(f"{f.__name__} requires `use_preconditioner` set to True")
        return f(self, z, *args)

    return cast(F, wrapper)

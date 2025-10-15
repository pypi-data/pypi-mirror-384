"""Low-rank approximation algorithms for matrices.

This module contains implementations for computing the low-rank approximation of a
matrix or a mode-0 unfolding of a higher-order array. More concrete, the factors ``U``
and ``VH`` are determined such that

    tl.frob(tl.tens2mat(a, 0) - U @ tl.tens2mat(VH, 0))

is (approximately) minimal for a given rank or below a given tolerance.

Routines
--------
LowRankApproximationFcn
    Protocol for low-rank approximation functions.
lra_svd
    Compute a low-rank approximation via singular value decomposition.
lra_eig
    Compute a low-rank approximation via eigenvalue decomposition.
"""

import math
from collections.abc import MutableMapping  # noqa: F401 # sphinx
from typing import (
    Protocol,
    TypeVar,
    cast,
    runtime_checkable,
)

import numpy as np

import pytensorlab as tl
import pytensorlab.backends.numpy as tlb
from pytensorlab.datatypes import Tensor  # noqa: F401  # sphinx
from pytensorlab.typing import ArrayType, PositiveInt, TensorType
from pytensorlab.typing.core import MatrixType, ShapeLike
from pytensorlab.util.indextricks import findfirst

T = TypeVar("T", TensorType, ArrayType)


@runtime_checkable
class LowRankApproximationFcn(Protocol):
    """Compute a low-rank approximation.

    The function implementing this protocol should return a low-rank approximation of a
    given matrix based on a fixed rank or a given tolerance.
    """

    def __call__(
        self,
        a: T,
        rank: PositiveInt | None = None,
        tol: float | None = None,
    ) -> tuple[MatrixType, T | ArrayType]:
        """Compute a low-rank approximation.

        A low-rank approximation of the matrix `a` is computed such that::

            tl.frob(tl.tens2mat(a, 0) - U @ tl.tens2mat(VH, 0))

        is minimal for a given `rank` or below a threshold `tol`. The `VH` factor of the
        low-rank approximation is returned with the same type as the array `a` if
        possible.

        Parameters
        ----------
        a : T
            The matrix (array) of which the low-rank approximation is computed. If an
            array is given, it is flattened first such that all but the first axis are
            in the columns, i.e., ``tl.tens2mat(a, 0)`` is used (explicitly or
            implicitly).
        rank : PositiveInt, optional
            An upper bound for the rank of the approximation. If both `rank` and `tol`
            are not provided, `rank` is equal to ``min(a.shape)``.
        tol : float, optional
            Tolerance on the approximation error. Only used if `rank` is not given.

        Returns
        -------
        U : MatrixType
            The column estimates of the low-rank approximation.
        VH : T | ArrayType
            The row estimates of the low-rank approximation. The same type as `a` is
            returned if possible, i.e., the row estimate can be returned as a
            higher-order array.
        """
        ...


@runtime_checkable
class HasReshape(Protocol):
    """Supports reshape."""

    shape: tuple[int, ...]

    def reshape(self, a: T, shape: ShapeLike) -> T | ArrayType: ...


def lra_svd(
    a: MatrixType | TensorType,
    rank: PositiveInt | None = None,
    tol: float | None = None,
) -> tuple[MatrixType, MatrixType]:
    """Compute a low-rank approximation via singular value decomposition.

    A low-rank approximation of the matrix `a` is computed such that::

        tl.frob(tl.tens2mat(a, 0) - U @ tl.tens2mat(VH, 0))

    is minimal for a given `rank` or below a threshold `tol`. The `VH` factor of the
    low-rank approximation is returned with the same type as the array `a` if possible.

    Parameters
    ----------
    a : MatrixType | TensorType
        The matrix (array) of which the low-rank approximation is computed. If an array
        is given, it is flattened first such that all but the first axis are in the
        columns, i.e., ``tl.tens2mat(a, 0)`` is used.
    rank : PositiveInt, optional
        An upper bound for the rank of the approximation. If both `rank` and `tol` are
        not provided, `rank` is equal to ``min(a.shape)``.
    tol : float, optional
        Tolerance on the approximation error. Only used if `rank` is not given.

    Returns
    -------
    U : MatrixType
        The column estimates of the low-rank approximation.
    VH : MatrixType
        The row estimates of the low-rank approximation.
    """
    if a.ndim > 2:
        if hasattr(a, "reshape"):
            assert isinstance(a, HasReshape)
            a = np.asarray(a).reshape((a.shape[0], -1))
    a = cast(MatrixType, np.asarray(a).reshape(a.shape[0], -1))
    U, sv, Vh = tlb.svd(a, full_matrices=False)
    if rank is None:
        if tol is None:
            rank = min(a.shape)
        else:
            rank = len(sv) - findfirst(np.cumsum(sv[::-1] ** 2) > tol**2)

    return U[:, :rank], sv[:rank, None] * Vh[:rank, :]


def lra_eig(
    a: T,
    rank: PositiveInt | None = None,
    tol: float | None = None,
) -> tuple[MatrixType, T | ArrayType]:
    """Compute a low-rank approximation via eigenvalue decomposition.

    A low-rank approximation of the matrix `a` is computed such that::

        tl.frob(tl.tens2mat(a, 0) - U @ tl.tens2mat(VH, 0))

    is minimal for a given `rank` or below a threshold `tol`. The `VH` factor of the
    low-rank approximation is returned with the same type as the array `a` if
    possible.

    Parameters
    ----------
    a : T
        The matrix (array) of which the low-rank approximation is computed. If an
        array is given, it is flattened first such that all but the first axis are
        in the columns, i.e., ``tl.tens2mat(a, 0)`` is used (explicitly or
        implicitly).
    rank : PositiveInt, optional
        An upper bound for the rank of the approximation. If both `rank` and `tol`
        are not provided, `rank` is equal to ``min(a.shape)``.
    tol : float, optional
        Tolerance on the approximation error. Only used if `rank` is not given.

    Returns
    -------
    U : MatrixType
        The column estimates of the low-rank approximation.
    VH : T | ArrayType
        The row estimates of the low-rank approximation. The same type as `a` is
        returned if possible, i.e., the row estimate can be returned as a
        higher-order array.
    """
    d, U = tlb.eigh(tl.matdot(a, a, 0))
    sv2 = np.abs(d)
    i = np.argsort(sv2)[::-1]
    sv2 = sv2[i]
    if rank is None:
        if tol is None:
            rank = min(a.shape[0], math.prod(a.shape[1:]))
        else:
            rank = len(sv2) - findfirst(np.cumsum(sv2[::-1]) > tol**2)
    U = U[:, i[:rank]]
    VH = tl.tmprod(a, U, 0, "H")
    assert isinstance(VH, type(a)) or isinstance(VH, np.ndarray)
    return U, VH

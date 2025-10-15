r"""Algorithms for computing the tensor-train decomposition.

In a tensor-train decomposition (TTD) :cite:`oseledets2011tensor`, a Nth-order tensor
$\ten{A}$ with dimensions :math:`I_{0} \times I_{1} \times \cdots \times I_{N-1}` is
expressed by TT rank-:math:`(r_0, \ldots, r_{N-2})` tensor $\ten{T}$ given by

.. math::

   \ten{T} = \mat{U}^{(0)} \cdot \ten{U}^{(1)} \cdot
    \cdots \cdot \ten{U}^{(N-2)} \cdot \mat{U}^{(N-1)},

where the first and the last cores are matrices of size :math:`I_0 \times r_0` and
:math:`r_{N-2} \times I_{N-1}`, respectively, and the other cores :math:`\ten{U}^{(i)}`
are third-order tensors of size :math:`r_{i-1} \times I_i \times r_i`. The
multiplications between the cores are defined as tensor contraction along the dimensions
of the TT ranks. The entry-wise definition is as follows:

.. math::

   t_{i_0,\ldots,i_{N-1}} = \left(\vec{u}^{(0)}_{i_0}\right)^{\T} \mat{U}^{(1)}_{i_1}
   \cdots \mat{U}^{(N-2)}_{i_{N-1}} \vec{u}^{(N-1)}_{i_{N-1}},

where the vector or matrix slices along the non-tensor rank dimensions are used.

The general routine to compute a TT is :func:`.tt_svd`.

Functions
---------
TT
    Framework for tensor-train decomposition via low-rank approximation.
tt_svd
    Compute the tensor-train decomposition using singular value decomposition.
tt_eig
    Compute the tensor-train decomposition using eigenvalue decomposition.

Notes
-----
For more information, see Oseledets, I.V., "Tensor-train decomposition," SIAM Journal on
Scientific Computing, Vol. 33, No. 5, pp. 2295-2317, 2011.

Examples
--------
>>> import pytensorlab as tl
>>> import numpy as np
>>> T = tl.TensorTrainTensor.random((10, 11, 12, 13), (3, 4, 5))
>>> Tf = tl.noisy(np.array(T), 50)
>>> tl.tt_svd(Tf, (3, 4, 5)) # target TT rank
Tensor-train tensor of shape (10, 11, 12, 13) with ranks (3, 4, 5)
>>> tl.tt_eig(Tf, tol=1e-2)
Tensor-train tensor of shape (10, 11, 12, 13) with ranks (3, 4, 5)

The :class:`.TT` allows custom implementations for the low-rank approximation:

>>> from pytensorlab.algorithms import TT, lra_svd
>>> tt_custom = TT(compute_lra=lra_svd)
>>> tt_custom(Tf, (3, 4, 5))
Tensor-train tensor of shape (10, 11, 12, 13) with TT ranks (3, 4, 5)
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

import pytensorlab as tl
from pytensorlab.algorithms.lra import LowRankApproximationFcn
from pytensorlab.typing import ArrayType, PositiveInt, TensorType

from ..datatypes import (
    Tensor,  # noqa: F401 # sphinx
    TensorTrainTensor,
)
from .lra import lra_eig as lra_eig
from .lra import lra_svd as lra_svd


@dataclass
class TT:
    """Framework for tensor-train decomposition via low-rank approximation.

    This class provides a framework for implementing tensor-train (TT) decomposition
    algorithms based on successive low-rank approximations of matrix unfoldings of a
    tensor. It supports truncation based on a given TT rank or a given tolerance. The
    low-rank approximation function can be customized.

    Parameters
    ----------
    a : TensorType
        Tensor to be decomposed.
    tt_rank : Sequence[PositiveInt], optional
        Upper bound for the TT rank. If not provided, either `tol` is used to determine
        the TT rank or the theoretically maximal upper bound is used.
    tol : float, optional
        Upper bound on the Frobenius norm of the residual between the `a` and its
        approximation. Ignored if `tt_rank` is given.

    Returns
    -------
    TensorTrainTensor
        A TT tensor that approximates the given tensor.

    Notes
    -----
    The implementation of this framework is based on Oseledets, I.V., "Tensor-train
    decomposition," SIAM Journal on Scientific Computing, Vol. 33, No. 5, pp. 2295-2317,
    2011.

    Examples
    --------
    >>> import pytensorlab as tl
    >>> from pytensorlab.algorithms import TT, lra_svd
    >>> import numpy as np
    >>> T = tl.TensorTrainTensor.random((10, 11, 12, 13), (3, 4, 5))
    >>> Tf = tl.noisy(np.array(T), 50)
    >>> tt_custom = TT(compute_lra=lra_svd)
    >>> tt_custom(Tf, (3, 4, 5))
    Tensor-train tensor of shape (10, 11, 12, 13) with TT ranks (3, 4, 5)
    """

    compute_lra: LowRankApproximationFcn = lra_svd
    """Function that computes a low-rank approximation

    The function should accept a matrix or a axis-0 unfolding of a tensor.
    """

    def __call__(
        self,
        a: TensorType,
        tt_rank: Sequence[PositiveInt] | None = None,
        tol: float | None = None,
    ) -> TensorTrainTensor:
        """Compute the tensor-train decomposition.

        Parameters
        ----------
        a : TensorType
            Tensor to be decomposed.
        tt_rank : Sequence[PositiveInt], optional
            Upper bound for the TT rank. If not provided, either `tol` is used to
            determine the tt rank or the theoretically maximal upper bound is used.
        tol : float, optional
            Upper bound on the Frobenius norm of the residual between the `a` and its
            approximation. Ignored if `tt_rank` is given.

        Returns
        -------
        T : TensorTrainTensor
            A `TensorTrainTensor` with the given TT ranks.
        """
        if a.ndim < 2:
            raise ValueError(
                f"expected at least a second order tensor, got order {a.ndim}"
            )
        if tt_rank is not None and len(tt_rank) != a.ndim - 1:
            raise ValueError(f"got {len(tt_rank)} ranks, expected {a.ndim - 1}")

        A = np.asarray(a)

        cores: tuple[ArrayType, ...] = ()

        if tol is not None:
            tol = tol / math.sqrt(a.ndim - 1) * tl.frob(a)
        if tt_rank is None:
            rank = [1] * a.ndim
        else:
            rank = [1, *tuple(tt_rank)]
            tol = None

        shape = A.shape

        for n in range(a.ndim - 1):
            # Compute low rank approximation
            A = A.reshape((rank[n] * shape[n], *shape[n + 1 :]))
            U, VH = self.compute_lra(A, rank[n + 1] if tt_rank else None, tol)
            rank[n + 1] = U.shape[1]
            cores += (U.reshape((rank[n], shape[n], rank[n + 1])),)
            A = VH

        cores += (np.asarray(A).reshape((rank[-1], shape[-1], 1)),)
        return TensorTrainTensor(cores)


def tt_svd(
    a: TensorType,
    tt_rank: Sequence[PositiveInt] | None = None,
    tol: float | None = None,
) -> TensorTrainTensor:
    """Compute the tensor-train decomposition using singular value decomposition.

    Parameters
    ----------
    a : TensorType
        Tensor to be decomposed.
    tt_rank : Sequence[PositiveInt], optional
        Upper bound for the TT rank. If not provided, either `tol` is used to determine
        the TT rank or the theoretically maximal upper bound is used.
    tol : float, optional
        Upper bound on the Frobenius norm of the residual between the `a` and its
        approximation. Ignored if `tt_rank` is given.

    Returns
    -------
    TensorTrainTensor
        A TT tensor that approximates the given tensor.

    Notes
    -----
    The implementation of this framework is based on Oseledets, I.V., "Tensor-train
    decomposition," SIAM Journal on Scientific Computing, Vol. 33, No. 5, pp. 2295-2317,
    2011.

    Examples
    --------
    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> T = tl.TensorTrainTensor.random((10, 11, 12, 13), (3, 4, 5))
    >>> Tf = tl.noisy(np.array(T), 50)
    >>> tt_svd(Tf, (3, 4, 5))
    Tensor-train tensor of shape (10, 11, 12, 13) with TT ranks (3, 4, 5)
    """
    return TT()(a, tt_rank, tol)


def tt_eig(
    a: TensorType,
    tt_rank: Sequence[PositiveInt] | None = None,
    tol: float | None = None,
) -> TensorTrainTensor:
    """Compute the tensor-train decomposition using eigenvalue decomposition.

    Parameters
    ----------
    a : TensorType
        Tensor to be decomposed.
    tt_rank : Sequence[PositiveInt], optional
        Upper bound for the TT rank. If not provided, either `tol` is used to determine
        the TT rank or the theoretically maximal upper bound is used.
    tol : float, optional
        Upper bound on the Frobenius norm of the residual between the `a` and its
        approximation. Ignored if `tt_rank` is given.

    Returns
    -------
    TensorTrainTensor
        A TT tensor that approximates the given tensor.

    Notes
    -----
    The implementation of this framework is based on Oseledets, I.V., "Tensor-train
    decomposition," SIAM Journal on Scientific Computing, Vol. 33, No. 5, pp. 2295-2317,
    2011.

    This implementation uses the eigenvalue decomposition of the Gram matrix formed by
    the matrix unfoldings, which allows efficient implementations for structured tensors
    (subclasses of :class:`.Tensor`) and can also be cheaper for dense tensors. Because
    the Gram matrix is formed, the accuracy can be limited to half the expected
    precision for the given data type (approximately ``1e-8`` instead of ``1e-16`` for
    standard float).

    Examples
    --------
    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> T = tl.TensorTrainTensor.random((10, 11, 12, 13), (3, 4, 5))
    >>> Tf = tl.noisy(np.array(T), 50)
    >>> tt_eig(Tf, (3, 4, 5))
    Tensor-train tensor of shape (10, 11, 12, 13) with TT ranks (3, 4, 5)
    """
    return TT(compute_lra=lra_eig)(a, tt_rank, tol)

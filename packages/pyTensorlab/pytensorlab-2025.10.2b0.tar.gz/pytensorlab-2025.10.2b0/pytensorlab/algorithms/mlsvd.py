r"""Algorithms for computing the multilinear singular value decomposition.

In the multilinear singular value decomposition (MLSVD), an Nth-order tensor
:math:`\mathcal{A}` with dimensions :math:`I_{0} \times I_{1} \times \cdots \times
I_{N-1}` is factorized as

.. math::

     \mathcal{A} = \mathcal{S} \cdot_0 \mathbf{U}^{(0)} \cdot_1 \mathbf{U}^{(1)} \cdot
     \cdots \cdot_{N-1} \mathbf{U}^{(N-1)}

in which :math:`\mathcal{S}` is the all-orthogonal and ordered core tensor of with
dimensions :math:`R_0\times R_1\times \cdots \times R_{N-1}` and
:math:`\mathbf{U}^{(n)}`, :math:`n=0,1,\ldots,N`, are the factors with dimensions
:math:`I_n\times R_n`. These factors contain an orthonormal basis for the mode-n
subspaces.

In pyTensorlab, the core tensor and factor matrices are stored in a
:class:`.TuckerTensor`. Let ``T`` be the MLSVD of the tensor ``a``, then::

    T.core      # core tensor (S above)
    T.factors   # factor matrices (U0, U1, ... above)
    T.coreshape # dimensions of the core tensor as a tuple (R0, R1, ...)
    T.shape     # dimensions of the tensor (I0, I1, ...)

To reconstruct the tensor, use ``a = tl.tmprod(T.core, T.factors,
range(T.ndim))``, or simply ``a = numpy.asarray(T)``.

Apart from the core tensor and the factors, the multilinear singular values ``sv`` are
computed. For each mode, the nth element of the tuple ``sv`` is a vector collecting the
mode-n singular values, which are the norms of the order-(N-1) slices (or subtensors) of
the core tensor for each mode, i.e.::

    sv[n][i] = tl.frob(np.take(core, i, axis=n))

See :cite:`delathauwer2000multilinear` for more background information on the MLSVD.

While the definition of the MLSVD implies the use of the singular value decomposition
applied to the matrix unfoldings, many types of algorithms have been developed to speed
up computations. Below, we give an annotated list of algorithms and options available in
pyTensorlab.

- :func:`mlsvd` computes the standard MLSVD. For large tensors, the SVD can be replaced
  by the eigenvalue decomposition by setting `large_scale` to True.

- :func:`mlsvd_rsi` uses randomized range finders to compute the factors
  :cite:`halko2011finding`. Typically, `mlsvd_rsi` is much faster, while being almost
  as accurate as `mlsvd`. This is the recommended algorithm for large, dense tensors.

- The `truncate_sequentially` option (default is True for `mlsvd` and
  `mlsvd_rsi`) enables sequential truncation, which improves performance if the
  multilinear rank is low compared to the dimensions of the tensor; see
  :cite:`vannieuwenhoven2012new`. Disabling sequential truncation can be beneficial
  for certain types of tensor as truncation destroys structure such as sparsity.

Classes
-------
MLSVD
    Computational kernel for multilinear singular value decomposition.

Functions
---------
mlsvd
    Compute the sequentially truncated multilinear singular value decomposition.
mlsvd_rsi
    Compute the multilinear SVD using randomized subspace iteration.
mlsvds
    Compute the multilinear SVD of a sparse tensor.

Examples
--------
Standard computation:

>>> import pytensorlab as tl
>>> a = tl.random.randn((4, 5, 6))
>>> T, sv = tl.mlsvd(a)

Fixed multilinear rank:

>>> import pytensorlab as tl
>>> import numpy as np
>>> a = np.array(tl.TuckerTensor.randn((4, 5, 6), (2, 3, 4)))
>>> T, sv = tl.mlsvd(a, (2, 3, 4))

Estimate the multilinear rank by setting a target relative error in the Frobenius norm
(only for :func:`.mlsvd`):

>>> import pytensorlab as tl
>>> import numpy as np
>>> a = tl.noisy(np.array(tl.TuckerTensor.randn((4, 5, 6), (2, 3, 4))), 60)
>>> T, sv = tl.mlsvd(a, tol=1e-2)
"""

import functools as ft
import math
import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from typing import (
    Any,
    Literal,
    Protocol,
    cast,
    runtime_checkable,
)
from warnings import warn

import numpy as np
import scipy.linalg as sla
import scipy.sparse.linalg as sspla

import pytensorlab as tl
import pytensorlab.backends.numpy as tlb
from pytensorlab.datatypes.core import tens2mat
from pytensorlab.datatypes.tensor import Tensor
from pytensorlab.typing import (
    Axis,
    DenseTensorType,
    MatrixLike,
    MatrixType,
    Shape,
    TensorType,
    VectorType,
)
from pytensorlab.util.exceptions import AssumptionViolationException
from pytensorlab.util.indextricks import findfirst

from ..datatypes import SparseTensor, TuckerTensor
from ..datatypes.tensor import DenseTensor  # noqa: F401 # sphinx
from ..random.rng import get_rng
from ..util.utils import _subspace_error, argmax, argsort, matrix_like_to_array


def svd_rsi(
    a: MatrixType,
    k: int,
    /,
    oversampling: int = 5,
    niter: int = 2,
    _rng: np.random.Generator | int | None = None,
) -> tuple[MatrixType, VectorType, MatrixType]:
    """Compute randomized SVD with subspace iteration.

    A matrix `a` is (approximately) factorized by the rank-`k` approximation ``u @
    numpy.diag(s) @ vh`` in which `u` and `vh` have orthonormal columns and rows,
    respectively.

    Parameters
    ----------
    a : MatrixType
        Matrix to be factorized.
    k : int
        Target rank.
    oversampling: int, default = 5
        Number of additional columns sampled using randomized compression. A higher
        value can improve the estimate of the subspaces.
    niter : int, default = 2
        The number of subspace iterations performed.
    _rng : numpy.random.Generator | int, optional
        Seed or random number generator used for all random operations in this
        function. If an integer is given, a new generator is created with that seed. If
        a generator is provided, it is used directly. If None, the global generator is
        used; see :func:`.get_rng`.

    Returns
    -------
    u : MatrixType
        Matrix with left singular vectors.
    s : VectorType
        Vector with singular values.
    vh : MatrixType
        Matrix with (transposed) right singular vectors.

    Notes
    -----
    The randomized SVD (alg 5.1 in :cite:`halko2011finding`) is computed with randomized
    subspace iteration (alg 4.4 in :cite:`halko2011finding`) for improved accuracy.
    """
    _rng = get_rng(_rng)

    if a.ndim != 2:
        raise ValueError(f"expected a matrix, but number of dimensions is {a.ndim}")

    # randomized projection
    b = a @ _rng.standard_normal((a.shape[1], k + oversampling))
    q, _ = tlb.qr(b, mode="reduced")

    # subspace iteration
    for _ in range(niter):
        b = a.conj().T @ q
        q, _ = tlb.qr(b, mode="reduced")
        b = a @ q
        q, _ = tlb.qr(b, mode="reduced")

    # SVD stage
    b = q.conj().T @ a
    u, s, vh = tlb.svd(b, full_matrices=False)
    u = q @ u

    return u[:, :k], s[:k], vh[:k, :]


@runtime_checkable
class ColumnSpaceFcn(Protocol):
    """Function to compute or estimate the column space.

    The function implementing this protocol should return an orthonormal basis `U`
    for (an estimate of) the mode-n subspace of tensor `a`, with n set by `axis`.
    In other words, the column space of the mode-`axis` unfolding of `a`,
    ``tl.tens2mat(a, axis)``, is computed.

    See Also
    --------
    colspace_eig, colspace_eigs, colspace_qr, colspace_qrs, colspace_rsvd, colspace_svd

    Notes
    -----
    Depending on the truncation function used, the columns of `U` should be sorted
    such that basis vectors belonging to more dominant parts of the subspace have
    lower indices.

    If no estimates for the singular values are available, any vector with at least `k`
    entries can be returned, as long as the truncation function does not depend on these
    estimates; see MLSVD and TruncationFcn.
    """

    def __call__(
        self,
        a: TensorType,
        axis: int,
        k: int,
        /,
        **kwargs: Any,
    ) -> tuple[MatrixType, VectorType]:
        """Compute the column space.

        Return an orthonormal basis `U` for (an estimate of) the mode-n subspace of
        tensor `a`, with n set by `axis`. In other words, the column space of the
        mode-`axis` unfolding of `a`, ``tl.tens2mat(a, axis)``, is computed.

        Parameters
        ----------
        a : TensorType
            The array of which the mode-`axis` space is computed.
        axis : int
            The mode along which `a` is unfolded before computing the column space.
        k : int
            The dimension of the mode-`axis` space to compute. If `k` is smaller than
            the dimension of the subspace, an orthonormal basis for the dominant
            dimension `k` subspace is computed. This parameter may be ignored by the
            implementation.
        **kwargs
            Options for subspace computation method.

        Returns
        -------
        U : MatrixType
            Matrix containing an orthonormal basis for the dominant mode-`axis` subspace
            of at least dimension `k`.
        sv : VectorType
            Vector containing (estimates for) the singular values.
        """
        ...


def colspace_eig(
    a: TensorType,
    axis: int,
    k: int,
    /,
    order: Literal["AHA", "AAH"] | None = None,
    **_: Any,
) -> tuple[MatrixType, VectorType]:
    """Compute column space of a tensor unfolding using the EVD.

    Return an orthonormal basis `U` for (an estimate of) the mode-n subspace of
    tensor `a`, with n set by `axis`. In other words, the column space of the
    mode-`axis` unfolding of `a`, ``tl.tens2mat(a, axis)``, is computed. This column
    space is computed via the eigenvalue decomposition of an outer product between the
    mode-`axis` unfolding of `a` and its conjugate transpose.

    Parameters
    ----------
    a : TensorType
        The tensor for which the column space of its unfolding is computed.
    axis : int
        The mode along which `a` is unfolded before computing the column space.
    k : int
        The dimension of the mode-`axis` space to compute. If `k` is smaller than the
        dimension of the subspace, an orthonormal basis for the dominant dimension
        `k` subspace is computed.
    order : "AHA" | "AAH", optional
        Term order of the product between the mode-`axis` unfolding of `a` and its
        conjugate transpose for the computation of the eigenvalue decomposition. Order
        "AHA" corresponds to ``tl.tens2mat(a, axis).conj().T @ tl.tens2mat(a, axis)``,
        and order "AAH" corresponds to ``tl.tens2mat(a, axis) @
        tl.tens2mat(a, axis).conj().T``. If not provided, the order is decided based on
        the dimensions of the mode-`axis` unfolding of `a`; if it has more columns than
        rows, the order is "AAH", otherwise the order is "AHA".
    **_
        Unused.

    Returns
    -------
    U : MatrixType
        Matrix containing an orthonormal basis for the dominant mode-`axis` subspace of
        at least dimension `k`.
    sv : VectorType
        Vector containing (estimates for) the singular values.

    See Also
    --------
    colspace_eigs, colspace_qr, colspace_qrs
    """
    if order is None:
        if math.prod(a.shape[i] for i in range(a.ndim) if i != axis) > a.shape[axis]:
            order = "AAH"
        else:
            order = "AHA"

    if order == "AAH":
        M = None
        d, U = tlb.eigh(tl.matdot(a, a, axis))
    else:
        M = tl.tens2mat(a, axis)
        d, U = tlb.eigh(np.array(M.conj().T @ M))

    return _colspace_eig(M, d, U, k, order)


class _AAHLinearOperator(sspla.LinearOperator):
    """Sparse operator for order "AAH"."""

    def __init__(self, M):
        super().__init__(M.dtype, (M.shape[0], M.shape[0]))

        self.A = M
        self.AH = M.conj().T

    def _matmat(self, X: MatrixType) -> MatrixType:
        return self.A.dot(self.AH.dot(X))


class _AHALinearOperator(sspla.LinearOperator):
    """Sparse operator for order "AHA"."""

    def __init__(self, M):
        super().__init__(M.dtype, (M.shape[1], M.shape[1]))

        self.A = M
        self.AH = M.conj().T

    def _matmat(self, X: MatrixType) -> MatrixType:
        return self.AH.dot(self.A.dot(X))


def colspace_eigs(
    a: TensorType,
    axis: int,
    k: int,
    /,
    order: Literal["AHA", "AAH"] | None = None,
    backup_method: ColumnSpaceFcn | None = None,
    **kwargs: Any,
) -> tuple[MatrixType, VectorType]:
    """Compute column space of a sparse tensor unfolding using the EVD.

    Return an orthonormal basis `U` for (an estimate of) the mode-n subspace of
    tensor `a`, with n set by `axis`. In other words, the column space of the
    mode-`axis` unfolding of `a`, ``tl.tens2mat(a, axis)``, is computed. This column
    space is computed via the sparse eigenvalue decomposition of an outer product
    between the mode-`axis` unfolding of `a` and its conjugate transpose.

    Parameters
    ----------
    a : TensorType
        The tensor for which the column space of its unfolding is computed.
    axis : int
        The mode along which `a` is unfolded before computing the column space.
    k : int
        The dimension of the mode-`axis` space to compute. If `k` is smaller than the
        dimension of the subspace, an orthonormal basis for the dominant dimension
        `k` subspace is computed.
    order : "AHA" | "AAH", optional
        Term order of the product between the mode-`axis` unfolding of `a` and its
        conjugate transpose for the computation of the eigenvalue decomposition. Order
        "AHA" corresponds to ``tl.tens2mat(a, axis).conj().T @ tl.tens2mat(a, axis)``,
        and order "AAH" corresponds to ``tl.tens2mat(a, axis) @
        tl.tens2mat(a, axis).conj().T``. If not provided, the order is decided based on
        the dimensions of the mode-`axis` unfolding of `a`; if it has more columns than
        rows, the order is "AAH", otherwise the order is "AHA".
    backup_method : ColumnSpaceFcn, optional
        When column space computation fails because the requested multilinear rank is
        too high, `backup_method` is used. If not provided, a ValueError is raised in
        this case.
    **kwargs
        Options passed to `backup_method`.

    Returns
    -------
    U : MatrixType
        Matrix containing an orthonormal basis for the dominant mode-`axis` subspace of
        at least dimension `k`.
    sv : VectorType
        Vector containing (estimates for) the singular values.

    Raises
    ------
    ValueError
        If `k` is too high to compute the column space and no `backup_method` is
        supplied.

    See Also
    --------
    colspace_eig, colspace_qr, colspace_qrs
    """
    M = tl.tens2mat(a, axis)

    if order is None:
        order = "AAH" if M.shape[1] > M.shape[0] else "AHA"
    assert order is not None

    A: sspla.LinearOperator = (
        _AAHLinearOperator(M) if order == "AAH" else _AHALinearOperator(M)
    )

    if k >= A.shape[0] - 1:
        if backup_method is None:
            raise ValueError("k is too large to use colspace_eigs")
        else:
            return backup_method(a, axis, k, order=order, kwargs=kwargs)

    try:
        d, U = tlb.eigsh(A, k=k)
    except ValueError as e:
        if all(i in str(e) for i in ("type", "f", "d", "F", "D")):
            dtype = M.dtype  # type:ignore
            if dtype in [np.float32, np.float64, np.complex64, np.complex128]:
                # np.longdouble and np.clongdouble might result in a matrix of type
                # np.float64 and np.complex128, respectively, although this depends
                # on the system. Even then, scipy considers them different because their
                # dtype.char is different even though the effective dtype is correct.
                raise ValueError(
                    f"only tensors with dtype.char equal to 'f', 'd', "
                    f"'F', or 'D' are accepted, not '{dtype.char}'"
                )
            else:
                raise ValueError(
                    f"only tensors containing floats or doubles are "
                    f"accepted, not {dtype}"
                )
        else:
            raise

    return _colspace_eig(M, d, U, k, order)


def colspace_qr(
    a: TensorType,
    axis: int,
    k: int,
    /,
    U0: MatrixType | None = None,
    order: Literal["AHA", "AAH"] | None = None,
    _rng: np.random.Generator | int | None = None,
    **_: Any,
) -> tuple[MatrixType, VectorType]:
    """Compute column space of a tensor unfolding using the QR algorithm.

    Return an orthonormal basis `U` for (an estimate of) the mode-n subspace of
    tensor `a`, with n set by `axis`. In other words, the column space of the
    mode-`axis` unfolding of `a`, ``tl.tens2mat(a, axis)``, is computed. This column
    space is computed via the QR decomposition of an outer product between the
    mode-`axis` unfolding of `a` and its conjugate transpose.

    Parameters
    ----------
    a : TensorType
        The tensor for which the column space of its unfolding is computed.
    axis : int
        The mode along which `a` is unfolded before computing the column space.
    k : int
        The dimension of the mode-`axis` space to compute. If `k` is smaller than the
        dimension of the subspace, an orthonormal basis for the dominant dimension
        `k` subspace is computed.
    U0 : MatrixType, optional
        Matrix of shape ``(a.shape[axis], k)`` used as initial starting point for the QR
        algorithm. If not provided, this matrix is randomly generated with entries drawn
        from the standard normal distribution.
    order : "AHA" | "AAH", optional
        Term order of the product between the mode-`axis` unfolding of `a` and its
        conjugate transpose for the computation of the eigenvalue decomposition. Order
        "AHA" corresponds to ``tl.tens2mat(a, axis).conj().T @ tl.tens2mat(a, axis)``,
        and order "AAH" corresponds to ``tl.tens2mat(a, axis) @
        tl.tens2mat(a, axis).conj().T``. If not provided, the order is decided based on
        the dimensions of the mode-`axis` unfolding of `a`; if it has more columns than
        rows, the order is "AAH", otherwise the order is "AHA".
    _rng : :class:`numpy.random.Generator` | int, default = :func:`.get_rng()`
        Random number generator or random seed to be used to generate `U0` if not
        provided.
    **_
        Unused.

    Returns
    -------
    U : MatrixType
        Matrix containing an orthonormal basis for the dominant mode-`axis` subspace of
        at least dimension `k`.
    sv : VectorType
        Vector containing (estimates for) the singular values.

    See Also
    --------
    colspace_eig, colspace_eigs, colspace_qrs
    """
    _rng = get_rng(_rng)

    if order is None:
        order = "AAH" if math.prod(a.shape) > a.shape[axis] ** 2 else "AHA"
    assert order is not None

    if U0 is None:
        U0 = _rng.standard_normal((a.shape[axis], k))
    assert U0 is not None

    if order == "AAH":
        M = None
        d, U = _qr_algorithm(tl.matdot(a, a, axis), U0)
    else:
        M = tl.tens2mat(a, axis)
        U0 = np.asarray(M.conj().T @ U0)
        d, U = _qr_algorithm(cast(MatrixLike, M.conj().T @ M), U0)

    return _colspace_eig(M, d, U, k, order)


def colspace_qrs(
    a: TensorType,
    axis: int,
    k: int,
    /,
    U0: MatrixType | None = None,
    order: Literal["AHA", "AAH"] | None = None,
    _rng: np.random.Generator | int | None = None,
    **_: Any,
) -> tuple[MatrixType, VectorType]:
    """Compute column space of a sparse tensor unfolding using the QR algorithm.

    Return an orthonormal basis `U` for (an estimate of) the mode-n subspace of
    tensor `a`, with n set by `axis`. In other words, the column space of the
    mode-`axis` unfolding of `a`, ``tl.tens2mat(a, axis)``, is computed. This column
    space is computed via the sparse QR decomposition of an outer product between the
    mode-`axis` unfolding of `a` and its conjugate transpose.

    Parameters
    ----------
    a : TensorType
        The tensor for which the column space of its unfolding is computed.
    axis : int
        The mode along which `a` is unfolded before computing the column space.
    k : int
        The dimension of the mode-`axis` space to compute. If `k` is smaller than the
        dimension of the subspace, an orthonormal basis for the dominant dimension
        `k` subspace is computed.
    U0 : MatrixType, optional
        Matrix of shape ``(a.shape[axis], k)`` used as initial starting point for the QR
        algorithm. If not provided, this matrix is randomly generated with entries drawn
        from the standard normal distribution.
    order : "AHA" | "AAH", optional
        Term order of the product between the mode-`axis` unfolding of `a` and its
        conjugate transpose for the computation of the eigenvalue decomposition. Order
        "AHA" corresponds to ``tl.tens2mat(a, axis).conj().T @ tl.tens2mat(a, axis)``,
        and order "AAH" corresponds to ``tl.tens2mat(a, axis) @
        tl.tens2mat(a, axis).conj().T``. If not provided, the order is decided based on
        the dimensions of the mode-`axis` unfolding of `a`; if it has more columns than
        rows, the order is "AAH", otherwise the order is "AHA".
    _rng : :class:`numpy.random.Generator` | int, default = :func:`.get_rng()`
        Random number generator or random seed to be used to generate `U0` if not
        provided.
    **_
        Unused.

    Returns
    -------
    U : MatrixType
        Matrix containing an orthonormal basis for the dominant mode-`axis` subspace of
        at least dimension `k`.
    sv : VectorType
        Vector containing (estimates for) the singular values.

    See Also
    --------
    colspace_eig, colspace_eigs, colspace_qr
    """
    _rng = get_rng(_rng)

    M = tl.tens2mat(a, axis)

    if order is None:
        order = "AAH" if M.shape[1] > M.shape[0] else "AHA"
    assert order is not None

    if U0 is None:
        U0 = _rng.standard_normal((M.shape[0], k))

    if order == "AAH":
        A = _AAHLinearOperator(M)
    else:
        A = _AHALinearOperator(M)
        U0 = np.asarray(M.conj().T @ U0)

    d, U = _qr_algorithm(A, U0)

    return _colspace_eig(M, d, U, k, order)


def _qr_algorithm(
    A: MatrixLike | sspla.LinearOperator, U0: MatrixType, maxiter: int = 3
) -> tuple[VectorType, MatrixType]:
    U = U0
    tol = np.finfo(U.dtype).eps * U.shape[0]
    for _ in range(maxiter):
        Uprev = U
        U, _ = tlb.qr(np.asarray(A @ U), "reduced")
        if _subspace_error(U, Uprev) < tol:
            break

    L, Q = tlb.eigh(U.conj().T @ (A @ U))
    U = U @ Q

    return L, U


def _colspace_eig(
    M: MatrixLike | None,
    d: VectorType,
    U: MatrixType,
    k: int,
    order: Literal["AHA", "AAH"],
    **_: Any,
) -> tuple[MatrixType, VectorType]:

    if order == "AAH":
        d = np.abs(d)
        idx = np.argsort(d)
        sv = np.sqrt(d[idx[::-1]])
        U = U[:, idx[::-1]]
    else:
        d = np.abs(d)
        idx = np.argsort(d)[-k:]
        sv = np.sqrt(d[idx[::-1]])
        U = U[:, idx[::-1]]

        if any(sv < math.sqrt(np.finfo(d.dtype).eps * d.size) * sv[0]):
            warn(
                sla.LinAlgWarning(
                    "Matrix has lower rank than the requested column space size."
                )
            )

        U = np.asarray(M @ U)
        U = U / tlb.norm(U, 2, 0)
    return U, sv


def colspace_svd(
    a: TensorType,
    axis: int,
    _: int,
    /,
    full_matrices: bool = False,
    **kwargs: Any,
) -> tuple[MatrixType, VectorType]:
    """Compute column space of tensor unfolding using SVD.

    Parameters
    ----------
    a : TensorType
        The tensor for which the column space of its unfolding is computed.
    axis : int
        The mode along which `a` is unfolded before computing the column space.
    _ : int
        Unused.
    full_matrices : bool, default = False
        Compute the full matrices instead of using an economy SVD; see
        :func:`numpy.linalg.svd`.
    **kwargs
        Unused.

    Returns
    -------
    U : MatrixType
        Matrix containing an orthonormal basis for the dominant mode-`axis` subspace of
        at least dimension `k`.
    sv : VectorType
        Vector containing (estimates for) the singular values.

    See Also
    --------
    numpy.linalg.svd, colspace_rsvd
    """
    M = tl.tens2mat(a, axis)
    U, sv, Vh = tlb.svd(matrix_like_to_array(M), full_matrices=full_matrices)
    return U, sv


def colspace_rsvd(
    a: DenseTensorType,
    axis: int,
    k: int,
    /,
    oversampling: int = 5,
    niter: int = 2,
    **_: Any,
) -> tuple[MatrixType, VectorType]:
    """Compute column space of tensor unfolding using randomized SVD.

    Parameters
    ----------
    a : DenseTensorType
        The tensor for which the column space of its unfolding is computed.
    axis : int
        The mode along which `a` is unfolded before computing the column space.
    k : int
        The dimension of the mode-`axis` space to compute. If `k` is smaller than the
        dimension of the subspace, an orthonormal basis for the dominant dimension
        `k` subspace is computed.
    oversampling: int, default = 5
        Oversampling factor in the randomized svd; see :func:`svd_rsi`.
    niter : int, default = 2
        Number of subspace iterations in the randomized svd; see :func:`svd_rsi`.
    **_
        Unused.

    Returns
    -------
    U : MatrixType
        Matrix containing an orthonormal basis for the dominant mode-`axis` subspace of
        at least dimension `k`.
    sv : VectorType
        Vector containing (estimates for) the singular values.

    See Also
    --------
    svd_rsi, colspace_svd
    """
    U, sv, Vh = svd_rsi(tl.tens2mat(a, axis), k, oversampling=oversampling, niter=niter)
    return U, sv


@runtime_checkable
class TruncationFcn(Protocol):
    """Function to truncate a column space.

    Given a matrix with a basis for some subspace, a basis for a smaller subspace of
    dimension `k` is returned.

    See Also
    --------
    truncate_never : Does not truncate.
    truncate_rank : Truncate after the first k columns.
    TruncationMLSVTolerance : Truncates based on a target (estimated) relative error.
        This is an example of a class based implementation that keeps its state.
    """

    def __call__(
        self,
        a: MatrixType,
        sv: VectorType,
        k: int,
        /,
    ) -> MatrixType:
        """Truncate a column space.

        Given a matrix with a basis for some subspace, a basis for a smaller subspace of
        dimension `k` is returned.

        Parameters
        ----------
        a : MatrixType
            Matrix containing the basis for a subspace.
        sv : VectorType
            Vector of (estimates for) the singular values. This parameter may be
            ignored by the implementation.
        k : int
            Dimension of the returned basis.

        Returns
        -------
        MatrixType:
            Matrix with `k` columns selected from `a`.
        """
        ...


@dataclass
class TruncationMLSVTolerance(TruncationFcn):
    """Truncate based on a target relative error.

    Based on the estimated relative error, the subspace is truncated to obtain a
    specified relative error `tol` for the MLSVD after `ndim` truncation steps. The
    error is estimated based on the computed singular values. Note that to ensure a
    correct result, all singular values need to be provided.

    Parameters
    ----------
    a : MatrixType
        Matrix containing the basis for a subspace.
    sv : VectorType
        A vector of (estimates for) the singular values.
    _
        Unused.

    Attributes
    ----------
    tol: float
        The target relative error or truncation tolerance.
    ndim: int
        Number of dimensions of the tensor.
    normsq: float, optional
        Squared norm of the tensor. If not provided, it is estimated from the singular
        values during the first call.
    _relerr: float, default = 0
        Current estimate for the relative error accumulated from previous truncations.
    _n: int, default = 0
        Number of modes that have been processed.

    Returns
    -------
    MatrixType:
        Matrix with `k` columns selected from `a`.

    Notes
    -----
    This function internally keeps track of the accumulated error from previous
    computation steps, and the number of times it is called. Therefore, a new callable
    functions has to be created for every computation of an MLSVD.

    Examples
    --------
    >>> import pytensorlab as tl
    >>> from pytensorlab.algorithms.mlsvd import TruncationMLSVTolerance, MLSVD
    >>> a = tl.random.randn((5, 3))
    >>> tr = TruncationMLSVTolerance(tol=1e-3, ndim=a.ndim)
    >>> mlsvd_obj = MLSVD(truncate=tr)
    """

    tol: float
    """The target relative error or truncation tolerance."""

    ndim: int
    """Number of dimensions of the tensor."""

    normsq: float | None = None
    """Squared norm of the tensor. 
    
    If not given, it is estimated from the singular values during the first call."""

    _relerr: float = 0
    """Current estimate for the relative error accumulated from previous truncations."""

    _n: int = 0
    """Number of modes that have been processed."""

    def __call__(self, a: MatrixType, sv: VectorType, _: int) -> MatrixType:
        """Truncate a column space using singular value based tolerance.

        Given a matrix with a basis for some subspace, a basis for a smaller subspace of
        dimension `k` subspace is returned. `k` is determined to heuristically obtain a
        relative error on the low multilinear rank approximation, set by `tol`.

        Parameters
        ----------
        a : MatrixType
            Matrix containing the basis for a subspace.
        sv : VectorType
            A vector of (estimates for) the singular values.
        _ : int
            Unused.

        Returns
        -------
        MatrixType:
            Matrix with `k` columns selected from `a`.

        See Also
        --------
        TruncationMLSVTolerance
        """
        if a.shape[1] != sv.size:
            raise AssumptionViolationException(
                f"truncation cannot be computed if not all singular values are given: "
                f"expected {a.shape[1]} but {sv.size} given"
            )
        if self.normsq is None:
            self.normsq = np.dot(sv, sv)
        cs = np.sqrt(np.add.accumulate((sv * sv)[::-1]) / self.normsq)
        try:
            idx = findfirst(self._relerr + cs[::-1] < self.tol / (self.ndim - self._n))
            self._relerr += cs[-idx - 1]
        except KeyError:  # no index found; do not truncate
            return a

        return a[:, :idx]


def truncate_never(a: MatrixType, sv: VectorType, k: int) -> MatrixType:
    """Do not truncate.

    Parameters
    ----------
    a : MatrixType
        Matrix containing the basis for a subspace.
    sv : VectorType
        Vector of (estimates for) the singular values.
    k : int
        Dimension of the returned basis.

    Returns
    -------
    MatrixType
        The untruncated matrix `a`.
    """
    return a


def truncate_rank(a: MatrixType, sv: VectorType, k: int) -> MatrixType:
    """Truncate after a certain number of columns.

    Parameters
    ----------
    a : MatrixType
        Matrix containing the basis for a subspace.
    sv : VectorType
        Vector of (estimates for) the singular values.
    k : int
        Dimension of the returned basis.

    Returns
    -------
    MatrixType
        The matrix `a` truncated after `k` columns.
    """
    return a[:, :k]


@dataclass
class MLSVD:
    """Computational kernel for multilinear singular value decomposition.

    The higher-order tensor `a` is factorized as ``tl.tmprod(core, factors,
    range(a.ndim))``, where ``core`` is the all-orthogonal core tensor with the same
    number of dimensions as `a` and ``factors`` is a tuple of ``a.ndim`` factor matrices
    containing an orthogonal basis for the (estimate of the) dominant mode-n subspace of
    dimension ``coreshape[n]``. The multilinear singular values are given as the tuple
    of mode-n singular values `sv` and are defined such that ``sv[n][i] =
    tl.frob(np.take(core, i, axis=n))``, as long as no truncation is performed. As the
    core tensor is 'ordered', the mode-n singular values are sorted in non-increasing
    order.

    Attributes
    ----------
    compute_column_space : :class:`.ColumnSpaceFcn`, default = :func:`.colspace_svd`
        Function to compute the column space of a matrix unfolding.
    truncate : :class:`.TruncationFcn`, default = :func:`.truncate_never`
        Function to truncate a computed column space.

    Parameters
    ----------
    a : TensorType
        Tensor to be decomposed.
    coreshape : Shape, optional
        The multilinear rank of the result. If not provided it is set to ``a.shape``.
    truncate_sequentially : bool, default = True
        Use sequential truncation to reduce the complexity.
    perm : Axis, optional
        Processing order of the modes of the tensor. This can be seen as a
        permutation of the tensor before computing the MLSVD. If not provided, it
        is set to ``range(a.ndim)`` if `truncate_sequentially` is False, and
        ``numpy.argsort(a.shape)`` if `truncate_sequentially` is True.

    Returns
    -------
    T : TuckerTensor
        A `TuckerTensor` with attributes ``core`` and ``factors``.
    sv : Sequence[VectorType]
        List of singular values per mode.

    Notes
    -----
    The MLSVD :cite:`delathauwer2000multilinear` is computed using sequential
    truncation :cite:`vannieuwenhoven2012new` and randomized SVDs (alg 5.1 in
    :cite:`halko2011finding`) with randomized subspace iteration (alg 4.4 in
    :cite:`halko2011finding`) for improved accuracy.
    """

    compute_column_space: ColumnSpaceFcn = colspace_svd
    """Function to compute the column space of a matrix unfolding."""

    truncate: TruncationFcn = truncate_never
    """Function to truncate a computed column space."""

    def __call__(
        self,
        a: TensorType,
        coreshape: Shape | None = None,
        /,
        truncate_sequentially: bool = True,
        perm: Axis | None = None,
    ) -> tuple[TuckerTensor, Sequence[VectorType]]:
        """Compute the multilinear singular value decomposition.

        The higher-order tensor a is factorized as ``tl.tmprod(core, factors,
        range(a.ndim))``, where `core` is the all-orthogonal core tensor with the same
        number of dimensions as a and `factors` is a tuple of ``a.ndim`` factor matrices
        containing an orthogonal basis for the (estimate of the) dominant mode-n
        subspace of dimension ``coreshape[n]``. The multilinear singular values are
        given as the tuple of mode-n singular values `sv` and are defined such that
        ``sv[n][i] = tl.frob(np.take(core, i, axis=n))`` (as long as no truncation is
        performed). As the core tensor is 'ordered', the mode-n singular values are
        sorted in non-increasing order.

        Parameters
        ----------
        a : TensorType
            Tensor to be decomposed.
        coreshape : Shape, optional
            The multilinear rank of the result. If not provided it is set to
            ``a.shape``.
        truncate_sequentially : bool
            Use sequential truncation to reduce the complexity.
        perm : Axis, optional
            Processing order of the modes of the tensor. This can be seen as a
            permutation of the tensor before computing the MLSVD. If not provided, it
            is set to ``range(a.ndim)`` if `truncate_sequentially` is False, and
            ``numpy.argsort(a.shape)`` if `truncate_sequentially` is True.

        Returns
        -------
        T : TuckerTensor
            A `TuckerTensor` with attributes ``core`` and ``factors``.
        sv : Sequence[VectorType]
            List of singular values per mode.

        Notes
        -----
        The MLSVD :cite:`delathauwer2000multilinear` can be computed computed using
        sequential truncation :cite:`vannieuwenhoven2012new` for improved efficiency.
        """
        if coreshape is None:
            coreshape = a.shape
        assert coreshape is not None
        v = tuple(k > s for k, s in zip(coreshape, a.shape))
        if any(v):
            k = findfirst(v)
            raise ValueError(
                f"dimension of the {k}th mode of the coreshape is "
                f"{coreshape[k]}; expected {a.shape[k]} or less"
            )
        i_max = argmax(coreshape)
        shape_i_max_other = math.prod(coreshape) // coreshape[i_max]
        if shape_i_max_other < coreshape[i_max]:
            warnings.warn(
                (
                    f"theoretical maximal mode-{i_max} rank "
                    f"is {shape_i_max_other}, but got {coreshape[i_max]}"
                ),
                UserWarning,
            )

        core = a.copy()

        if perm is None:
            perm = argsort(a.shape) if truncate_sequentially else range(a.ndim)
        elif len(perm) != a.ndim or sorted(perm) != list(range(a.ndim)):
            raise ValueError("perm is not a permutation of range(a.ndim)")

        factors: tuple[MatrixType, ...] = ()
        sv: tuple[VectorType, ...] = ()
        for n in perm:
            U, svn = self.compute_column_space(core, n, coreshape[n])

            U = self.truncate(U, svn, coreshape[n])
            if truncate_sequentially:
                core = tl.tmprod(core, U, n, "H")
            factors += (U,)
            sv += (svn,)

        # undo permutation
        iperm = argsort(perm)
        factors = tuple(factors[i] for i in iperm)
        sv = tuple(sv[i] for i in iperm)

        # truncate factors and core to final result
        factors = tuple(f[:, slice(s)] for f, s in zip(factors, coreshape))
        if not truncate_sequentially:
            core = tl.tmprod(core, factors, tuple(range(core.ndim)), "H")
        core_tr = np.asarray(core[tuple(slice(u.shape[1]) for u in factors)])

        # truncated "mlsvd" should be normalized
        if self.truncate != truncate_never or coreshape != a.shape:
            factors_tr: tuple[MatrixType, ...] = ()
            sv = ()
            for n in range(a.ndim):
                U, svn, _ = tlb.svd(tens2mat(core_tr, n), full_matrices=False)
                factors_tr += (U,)
                sv += (svn,)
            core_tr = tl.tmprod(core_tr, factors_tr, range(core.ndim), "H")
            factors = tuple(f @ u for f, u in zip(factors, factors_tr))

        return TuckerTensor(factors, core_tr), sv


def _mlsvd_matrix(
    a: TensorType,
    coreshape: Shape | None = None,
    tol: float | None = None,
    full_matrices: bool = False,
):
    """Compute the multilinear singular value decomposition of a matrix.

    The singular value decomposition is computed, but returned in the same format
    as `mlsvd` would. The output arguments are a `TuckerTensor`, containing the
    decomposition, and a list with two vectors, containing the singular values in
    each mode, which are identical in the matrix case. Alternatively, `mlsvd` can
    also be used for matrices and provides more options and info.

    Parameters
    ----------
    a : TensorType
        Matrix to be decomposed.
    coreshape : Shape, optional
        The multilinear rank of the result.
    tol : float, optional
        Tolerance on the relative error (or target relative error) in the Frobenius
        norm. Must be in the interval [0, 1). This tolerance is ignored if `coreshape`
        is given.
    full_matrices: bool, default = False
        Compute the full matrices instead of using an economy SVD; see
        :func:`numpy.linalg.svd`.

    Returns
    -------
    T : TuckerTensor
        A `TuckerTensor` representing the MLSVD of `a`.
    sv : Sequence[VectorType]
        List of singular values per mode.

    See Also
    --------
    mlsvd

    Notes
    -----
    For a matrix, its MLSVD is essentially equivalent to its SVD
    :cite:`delathauwer2000multilinear`. Note though that the second factor obtained
    through MLSVD still has to be transposed to correspond with the factors obtained
    with :func:`numpy.linalg.svd`; see examples. Although typically not meaningful in
    the matrix case, note that the mode-n ranks in `coreshape` can be chosen
    independently for each mode.

    Examples
    --------
    >>> import pytensorlab as tl
    >>> import numpy as np

    >>> rng = tl.get_rng(1)
    >>> a = rng.standard_normal((10,10)) + 1j * rng.standard_normal((10,10))

    >>> T, sv = tl.mlsvd(a)
    >>> np.linalg.norm(a - T.factors[0] @ T.core @ T.factors[1].T)   # Transpose needed.
    np.float64(3.776107120144757e-14)

    >>> U, S, Vh = np.linalg.svd(a)
    >>> np.linalg.norm(a - U @ np.diag(S) @ Vh)                   # No transpose needed.
    np.float64(3.776107120144757e-14)
    """
    if a.ndim != 2:
        raise ValueError(f"not a matrix; expected 2 axes but got {a.ndim}")

    U0, sv, U1 = tlb.svd(np.asarray(a), full_matrices=full_matrices)
    U1 = U1.T

    if coreshape is None:
        if tol is not None:
            if tol >= 1 or tol < 0:
                raise ValueError(f"expected tol in [0, 1), but got {tol}")
            try:
                sv_sq = sv * sv
                sv_rel_sq_cumsum = np.cumsum(sv_sq[::-1] / np.sum(sv_sq))[::-1]
                R = max(findfirst(sv_rel_sq_cumsum < tol * tol), 1)
            except KeyError:
                R = min(a.shape)
            coreshape = (R, R)
        else:
            coreshape = (U0.shape[1], U1.shape[1])
    else:
        if tol is not None:
            warnings.warn("argument tol ignored as coreshape is given")
        if coreshape[0] > U0.shape[1] or coreshape[1] > U1.shape[1]:
            if full_matrices:
                warnings.warn(
                    f"coreshape can not be larger than the largest dimension of the "
                    f"matrix: coreshape is {coreshape}, but the largest dimension "
                    f"is {max(U0.shape[1], U1.shape[1])}"
                )
            else:
                warnings.warn(
                    f"coreshape can not be larger than the smallest dimension of the "
                    f"matrix: coreshape is {coreshape}, but the smallest dimension "
                    f"is {min(U0.shape[1], U1.shape[1])}"
                )

        coreshape = (min(coreshape[0], U0.shape[1]), min(coreshape[1], U1.shape[1]))

    factors = (U0[:, : coreshape[0]], U1[:, : coreshape[1]])
    core = np.zeros(coreshape)
    np.fill_diagonal(core, sv[: min(coreshape)])
    return TuckerTensor(factors, core), (sv, sv)


def mlsvd(
    a: TensorType,
    coreshape: Shape | None = None,
    tol: float | None = None,
    full_matrices: bool = False,
    large_scale: bool | None = None,
    compute_column_space: ColumnSpaceFcn | None = None,
    **kwargs: Any,
) -> tuple[TuckerTensor, Sequence[VectorType]]:
    """Compute the sequentially truncated multilinear singular value decomposition.

    The higher-order tensor `a` is factorized as ``tl.tmprod(core, factors,
    range(a.ndim))``, where ``core`` is the all-orthogonal core tensor with the same
    number of dimensions as `a` and ``factors`` is a tuple of ``a.ndim`` factor matrices
    containing an orthogonal basis for the (estimate of the) dominant mode-n subspace of
    dimension ``coreshape[n]``. The multilinear singular values are given as the tuple
    of mode-n singular values `sv` and are defined such that ``sv[n][i] =
    tl.frob(np.take(core, i, axis=n))`` (as long as no truncation is performed). As the
    core tensor is 'ordered', the mode-n singular values are sorted in non-increasing
    order.

    Parameters
    ----------
    a : TensorType
        Tensor to be decomposed.
    coreshape : Shape, optional
        The multilinear rank of the result.
    tol : float, optional
        Tolerance on the relative error (or target relative error) in the Frobenius
        norm. `tol` must be in the interval [0, 1). This tolerance is ignored if
        `coreshape` is given.
    full_matrices: bool, default = False
        Compute the full matrices instead of using an economy SVD; see
        :func:`numpy.linalg.svd`.
    large_scale : bool, optional
        Enable faster but potentially less accurate implementations of the column space
        computation. If not provided, this parameter is set to True if `a` contains
        more than 100000 elements, otherwise it is set to False.
    compute_column_space : ColumnSpaceFcn, optional
        Function to compute the column space. If given, `large_scale` is ignored.
    **kwargs
        Options passed to subspace computation method.

    Returns
    -------
    T : TuckerTensor
        A `TuckerTensor` representing the MLSVD of `a`.
    sv : Sequence[VectorType]
        List of singular values per mode.

    Notes
    -----
    The MLSVD :cite:`delathauwer2000multilinear` is computed using sequential truncation
    :cite:`vannieuwenhoven2012new`.

    See Also
    --------
    mlsvd_rsi, mlsvals, mlsvds
    """
    args: dict[str, Any] = dict()
    if tol is not None:
        if coreshape is not None:
            warnings.warn("argument tol ignored as coreshape is given")
        else:
            if not 0 <= tol < 1:
                raise ValueError(f"expected tol in [0, 1), but got {tol}")
            args["truncate"] = TruncationMLSVTolerance(tol, a.ndim)

    if a.ndim < 2:
        raise ValueError(
            f"a should be a matrix or a tensor; expected ndim > 1, but got {a.ndim}"
        )

    if compute_column_space is None:
        if a.ndim == 2:
            return _mlsvd_matrix(a, coreshape, tol, full_matrices)

        if large_scale is None:
            large_scale = math.prod(a.shape) > 100000

        if large_scale:
            compute_column_space = colspace_eig
        else:
            compute_column_space = ft.partial(colspace_svd, full_matrices=full_matrices)

    args["compute_column_space"] = compute_column_space

    return MLSVD(**args)(a, coreshape, **kwargs)


def mlsvd_rsi(
    a: TensorType, coreshape: Shape, **kwargs: Any
) -> tuple[TuckerTensor, Sequence[VectorType]]:
    """Compute the multilinear SVD using randomized subspace iteration.

    The higher-order tensor `a` is factorized as ``tl.tmprod(core, factors,
    range(a.ndim))``, where ``core`` is the all-orthogonal core tensor with the same
    number of dimensions as `a` and ``factors`` is a tuple of ``a.ndim`` factor matrices
    containing an orthogonal basis for the (estimate of the) dominant mode-n subspace of
    dimension ``coreshape[n]``. The multilinear singular values are given as the tuple
    of mode-n singular values `sv` and are defined such that ``sv[n][i] =
    tl.frob(np.take(core, i, axis=n))`` (as long as no truncation is performed). As the
    core tensor is 'ordered', the mode-n singular values are sorted in non-increasing
    order.

    Parameters
    ----------
    a : TensorType
        Tensor to be decomposed.
    coreshape : Shape
        The multilinear rank of the result.
    oversampling : int, optional
        Value of `oversampling` parameter passed to :func:`svd_rsi`.
    nsubspaceiter: int, optional
        Value of `niter` argument passed to :func:`svd_rsi`.

    Returns
    -------
    T : TuckerTensor
        A `TuckerTensor` with attributes `core` and `factors`.
    sv : Sequence[VectorType]
        List of singular values per mode.

    See Also
    --------
    svd_rsi

    Notes
    -----
    The MLSVD :cite:`delathauwer2000multilinear` is computed using sequential
    truncation :cite:`vannieuwenhoven2012new` and randomized SVDs (alg 5.1 in
    :cite:`halko2011finding`) with randomized subspace iteration (alg 4.4 in
    :cite:`halko2011finding`) for improved accuracy.

    See Also
    --------
    mlsvd, mlsvals, mlsvds
    """
    args: dict[str, Any] = dict()
    args["oversampling"] = kwargs.get("oversampling", 5)
    args["niter"] = kwargs.get("nsubspaceiter", 2)

    _mlsvd = MLSVD(compute_column_space=ft.partial(colspace_rsvd, **args))
    return _mlsvd(a, coreshape, **kwargs)


def mlsvds(
    a: SparseTensor, coreshape: Shape, **kwargs: Any
) -> tuple[TuckerTensor, Sequence[VectorType]]:
    """Compute the multilinear SVD of a sparse tensor.

    The higher-order tensor `a` is factorized as ``tl.tmprod(core, factors,
    range(a.ndim))``, where ``core`` is the all-orthogonal core tensor with the same
    number of dimensions as `a` and ``factors`` is a tuple of ``a.ndim`` factor matrices
    containing an orthogonal basis for the (estimate of the) dominant mode-n subspace of
    dimension ``coreshape[n]``. The multilinear singular values are given as the tuple
    of mode-n singular values `sv` and are defined such that ``sv[n][i] =
    tl.frob(np.take(core, i, axis=n))`` (as long as no truncation is performed). As the
    core tensor is 'ordered', the mode-n singular values are sorted in non-increasing
    order.

    Parameters
    ----------
    a : SparseTensor
        Tensor to be decomposed.
    coreshape : Shape
        The multilinear rank of the result.
    backup_method : ColumnSpaceFcn, default = colspace_eig
        Function used when :func:`colspace_eigs` fails because the requested multilinear
        rank is too high. If not provided, :func:`colspace_eig` is used as backup. Can
        be set to None to disable.

    Returns
    -------
    T : TuckerTensor
        A `TuckerTensor` with attributes `core` and `factors`.
    sv : Sequence[VectorType]
        List of singular values per mode.

    Notes
    -----
    The MLSVD :cite:`delathauwer2000multilinear` is computed using sequential truncation
    :cite:`vannieuwenhoven2012new` and EVDs of the Gramian of the unfoldings. The EVDs
    only compute the largest eigenvalues using :func:`scipy.sparse.linalg.eigs`.

    See Also
    --------
    mlsvd, mlsvals, mlsvd_rsi
    """
    args: dict[str, Any] = dict()
    args["backup_method"] = kwargs.get("backup_method", colspace_eig)

    if a._data.dtype not in (
        np.float32,
        np.float64,
        np.complex64,
        np.complex128,
    ) and np.can_cast(a._data.dtype, np.float64, "safe"):
        new_data = a._data.astype(np.float64)
        a = tl.SparseTensor(
            new_data,
            a.indices,
            a.shape,
            a._flat_indices,
            _check_unique_ind=False,
            _check_bounds=False,
        )

    kwargs.pop("backup_method", None)
    kwargs.setdefault("truncate_sequentially", False)
    _mlsvd = MLSVD(compute_column_space=ft.partial(colspace_eigs, **args))
    return _mlsvd(a, coreshape, **kwargs)


def _mlsvals_svd(a: TensorType, n: int) -> VectorType:
    """Compute the singular values of the mode-n unfolding via SVD.

    The singular values of the mode-`n` unfolding of the tensor `a` are computed using
    the singular value decomposition.

    Parameters
    ----------
    a : TensorType
        Tensor of which the multilinear singular values are computed.
    n : int
        The axis along which the tensor is unfolded.

    Returns
    -------
    sv : VectorType
        Singular values of the mode-`n` unfolding of `a`.

    See Also
    --------
    mlsvals, tens2mat, _mlsvals_eig_AAH, _mlsvals_eig_AHA

    Notes
    -----
    This is an accurate but less efficient implementation, use only for small tensors or
    if accuracy is desired.
    """
    return tlb.svdvals(matrix_like_to_array(tens2mat(a, n)))


def _mlsvals_eig_AAH(a: TensorType, n: int) -> VectorType:
    """Compute the singular values of the mode-n unfolding via EVD of the outer product.

    The singular values of the mode-`n` unfolding of the tensor `a` are computed using
    the eigenvalues of the outer product of the mode-n unfolding of `a`::

        tens2mat(a, n) @ tens2mat(a, n).conj().T

    Parameters
    ----------
    a : TensorType
        Tensor of which the multilinear singular values are computed.
    n : int
        The axis along which the tensor is unfolded.

    Returns
    -------
    sv : VectorType
        Singular values of the mode-`n` unfolding of `a`.

    See Also
    --------
    mlsvals, tens2mat, matdot, _mlsvals_svd, _mlsvals_eig_AHA

    Notes
    -----
    This is an efficient but less accurate implementation; use for large tensors and
    when accuracy is not critical.
    """
    AAH = tl.matdot(a, a, n)
    return np.sqrt(np.flip(abs(tlb.eigvalsh(AAH))))


def _mlsvals_eig_AHA(a: TensorType, n: int) -> VectorType:
    """Compute the singular values of the mode-n unfolding via EVD of the inner product.

    The singular values of the mode-n unfolding of the tensor `a` are computed using the
    eigenvalues of the inner product of the mode-n unfolding of `a`::

        tens2mat(a, n).conj().T @ tens2mat(a, n)

    Parameters
    ----------
    a : TensorType
        Tensor for which the multilinear singular values are computed.
    n : int
        The mode at which the tensor is unfolded.

    Returns
    -------
    sv : VectorType
        Singular values of the mode-`n` unfolding of `a`.

    See Also
    --------
    mlsvals, tens2mat, _mlsvals_svd, _mlsvals_eg_AAH

    Notes
    -----
    This is an efficient but less accurate implementation; use for large tensors and
    when accuracy is not critical.
    """
    AHA = cast(MatrixType, tens2mat(a, n).conj().T @ tens2mat(a, n))
    return np.sqrt(np.flip(abs(tlb.eigvalsh(AHA))))


_MLSVALS_LARGE_SCALE_LIMIT = 1_000_000
"""Threshold for using eigenvalue instead of singular value decomposition.

See Also
--------
mlsvals
"""


def mlsvals(
    a: TensorType,
    large_scale: bool | None = None,
) -> Sequence[VectorType]:
    """Compute the multilinear singular values.

    The multilinear singular values of the higher-order tensor `a` are computed without
    computing the full multilinear singular value decomposition.

    Parameters
    ----------
    a : TensorType
        Tensor of which the multilinear singular values are computed.
    large_scale : bool, optional
        If True, use a faster but potentially less accurate implementation based on
        the eigenvalue decomposition. If False, the singular value decomposition is
        used. If not provided (None), `large_scale` is determined based on the shape
        and type of `a`.

    Returns
    -------
    sv : Sequence[VectorType]
        Sequence of mode-n singular values for every axis n.

    See Also
    --------
    mlsvd, mlsvd_rsi, mlsvds

    Notes
    -----
    When the large-scale version is used, the numerical precision is limited to half the
    precision with which `a` is represented. Set `large_scale` to False to get full
    precision.

    The number of mode-n singular values ``len(sv[n])`` is determined by the theoretical
    maximal multilinear rank. Hence, ``len(sv[n])`` can be smaller than ``a.shape[n]``.

    Examples
    --------
    >>> import pytensorlab as tl
    >>> a = tl.get_rng(31415).standard_normal((4, 5, 6))
    >>> tl.mlsvals(a)
    (array([6.88922737, 5.62679703, 5.29419531, 4.704312  ]),
     array([6.64232766, 5.93921565, 4.6244135 , 3.83555808, 3.71346853]),
     array([6.39053649, 5.35942596, 4.74293109, 3.99699862, 3.38148864, 3.1325855 ]))
    >>> T, sv = tl.mlsvd(a)
    >>> sv[0]
    array([6.88922737, 5.62679703, 5.29419531, 4.704312  ])
    >>> [float(tl.frob(slice)) for slice in T.core]
    [6.889227366506636, 5.626797028286733, 5.2941953138364575, 4.704311997576691]

    Depending on the maximal multilinear rank of `a`, the number of returned singular
    values can be smaller than the corresponding dimension:

    >>> import pytensorlab as tl
    >>> a = tl.get_rng(31415).standard_normal((8, 2, 2)) # ML rank is (4, 2, 2)
    >>> tl.mlsvals(a)
    (array([4.02727635, 3.63437713, 1.74374613, 1.35255743]),
     array([4.24276813, 4.03690879]),
     array([4.44750611, 3.81017105]))
    """
    svals_alg = _mlsvals_eig_AAH if large_scale else _mlsvals_svd
    size = math.prod(a.shape)
    sv: tuple[VectorType, ...] = ()
    for n in range(a.ndim):
        ncol = size // a.shape[n]
        if large_scale is None:
            if isinstance(a, Tensor):
                svals_alg = _mlsvals_eig_AAH
            elif size > _MLSVALS_LARGE_SCALE_LIMIT:
                svals_alg = _mlsvals_eig_AAH if ncol > a.shape[n] else _mlsvals_eig_AHA
            else:
                svals_alg = _mlsvals_svd

        svn = svals_alg(a, n)
        sv += (svn[: min(ncol, a.shape[n])],)

    return sv

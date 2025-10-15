r"""CPD computation using generalized eigenvalue decomposition.

In a polyadic decomposition, an Nth-order tensor :math:`\mathcal{A}` with dimensions
:math:`I_{0} \times I_{1} \times \cdots \times I_{N-1}` is expressed by a rank-:math:`R`
tensor :math:`\ten{T}` given by

.. math::

   \ten{T} = \sum_{r=0}^{R-1} \vec{u}^{(0)}_r \op \vec{u}^{(1)}_r \op
    \cdots \op \vec{u}^{(N-1)}_r.

In pyTensorlab, such a structured tensor can be formed with the class
:class:`.PolyadicTensor`. A canonical polyadic decomposition (CPD) is a polyadic
tensor of minimal rank.

The GEVD algorithm, implemented by :func:`cpd_gevd`, is an algebraic algorithm for
computing the CPD by means of the generalized eigevalue decomposition. This method can,
in the absence of numerical errors, compute the exact CPD of a subclass of tensors. In
general, it is used to compute an approximation of the CPD to be used as initialization
for optimization-based CPD computation, as implemented by :func:`.cpd`.

Functions
---------
cpd_gevd
    Compute CPD using generalized eigenvalue decomposition.

See Also
--------
pytensorlab.algorithms.cpd
"""

import warnings
from collections.abc import Sequence

import numpy as np
from scipy.linalg import LinAlgError, LinAlgWarning

import pytensorlab.backends.numpy as tlb
from pytensorlab.typing import MatrixType, TensorType

from ..datatypes import (
    PolyadicTensor,
    Tensor,  # noqa: F401 # sphinx
    mtkrprod,
    tmprod,
)
from ..random.rng import get_rng
from ..util.utils import argsort, inprod_kr
from .mlsvd import mlsvd


def cpd_gevd(
    T: TensorType,
    nterm: int,
    force_real: bool = True,
    randomslices: bool = True,
    refine: bool = True,
    _rng: np.random.Generator | int | None = None,
) -> PolyadicTensor:
    """Compute the canonical polyadic decomposition via GEVD.

    The canonical polyadic decomposition with `nterm` terms of the Nth-order tensor `T`
    are computed via the generalized eigenvalue decomposition. The decomposition is
    exact if the rank of `T` is equal to `nterm`, and at least two factor matrices have
    full column rank. This implies that the mode-n rank should be equal to `nterm` for
    at least two modes.

    Parameters
    ----------
    T : TensorType
        Tensor to be decomposed.
    nterm : int
        The number of rank-1 terms.
    force_real: bool, default = True
        Force the factor matrices to be real if True. If `T` is complex, `force_real`
        is ignored.
    randomslices: bool, default = True
        Use random slices in the GEVD. If False, the first 2 slices are taken.
    refine : bool, default = True
        Use an ALS step to refine the estimate for the first factor matrix.
    _rng : numpy.random.Generator | int, optional
        Seed or random number generator used for all random operations in this
        function. If an integer is given, a new generator is created with that seed. If
        a generator is provided, it is used directly. If None, the global generator
        (set via `set_rng`) is used.

    Returns
    -------
    PolyadicTensor
        Canonical polyadic decomposition of T.

    Notes
    -----
    See [1]_, [2]_, or [3]_ for more information.

    References
    ----------
    .. [1] S.E. Leurgans, R.T. Ross, R.B. Abel, "A decomposition for three-way arrays,"
       SIAM J. Matrix Anal. Appl., Vol. 14, 1993, pp. 1064-1083.
    .. [2] E. Sanchez, B.R. Kowalski, "Tensorial resolution: A direct trilinear
       decomposition," J. Chemometrics, Vol. 4, 1990, pp. 29-45.
    .. [3] R. Sands, F. Young, "Component models for three-way data: An alternating
       least squares algorithm with optimal scaling features," Psychometrika, Vol. 45,
       1980, pp. 39-67.
    """
    _rng = get_rng(_rng)

    # Check inputs.
    if T.ndim < 3:
        raise ValueError(
            f"order of tensor is {T.ndim} while expected order is 3 or higher"
        )
    if sum(s >= nterm for s in T.shape) < 2:
        raise ValueError(
            "at least two dimensions should be larger than nterm: shape is {T.shape}"
        )
    if tlb.iscomplexobj(T):
        force_real = False  # override settings if tensor is complex ==> factors complex

    if nterm == 1:
        return _rank_one(T)
    else:
        return _cpd_general_case(T, nterm, force_real, randomslices, refine, _rng=_rng)


def _rank_one(T: TensorType) -> PolyadicTensor:
    """Compute CPD of rank-1 tensor."""
    Tm, _ = mlsvd(T, (1,) * T.ndim)
    S = Tm.core.flat[0]
    S = (np.abs(S) if np.isreal(S) else S) ** (1.0 / T.ndim)
    factors = [np.reshape(f, (-1, 1)) * S for f in Tm.factors]
    if np.isreal(Tm.core.flat[0]):
        factors[0] *= np.sign(Tm.core.flat[0]).real
    return PolyadicTensor(factors)


def _cpd_general_case(
    T: TensorType,
    nterm: int,
    force_real: bool,
    randomslices: bool,
    refine: bool,
    _rng: np.random.Generator,
) -> PolyadicTensor:
    """Compute CPD of general tensor via GEVD."""
    # Prepermute the (core) tensor such that the largest two modes are the first
    # two, which hopefully maximizes the probability that the first two factor
    # matrices have full column rank.
    Tm, sv = mlsvd(T)
    eps = np.finfo(Tm.core.dtype).eps
    maxrank = (max(s, T.size // s) for s in T.shape)
    size_core = (sum(s >= s[0] * eps * r) for s, r in zip(sv, maxrank))
    idx = argsort([-i for i in size_core])
    iperm = argsort(idx)

    # transpose and extract
    Tm = Tm.transpose(idx)
    Tm = Tm.extract(nterm, nterm)

    if randomslices:
        randn = _rng.standard_normal
        U = [randn((s, 1 + (n == 2))) for n, s in enumerate(Tm.coreshape) if n > 1]
        S = tmprod(Tm.core, U, range(2, Tm.ndim), "T").squeeze()
    else:
        S = Tm.core[(slice(None),) * 2 + (slice(0, 2, 1),) + (1,) * (Tm.ndim - 3)]

    if any(s < t for s, t in zip(Tm.coreshape, (nterm, nterm, 2))):
        raise ValueError(
            f"at least two mode-n ranks should be larger than nterm: multilinear rank "
            f"is {Tm.coreshape}"
        )

    # Find first factor matrix from GEVD.
    eigvals, Ainvtp = tlb.eig(S[:, :, 0].T, S[:, :, 1].T)

    if force_real and tlb.iscomplexobj(Ainvtp):
        for i, val in enumerate(eigvals):
            if np.iscomplex(val):
                if val.imag > 0:
                    Ainvtp[:, i] = np.real(Ainvtp[:, i])
                elif val.imag < 0:
                    Ainvtp[:, i] = np.imag(Ainvtp[:, i])
        Ainvtp = np.real(Ainvtp)

    A = tlb.solve(Ainvtp, Tm.factors[0].T).T

    # Retrieve remaining factors via the least squares problem and a best rank-1
    # approximation.
    X = tmprod(T, np.conj(Tm.factors[0]) @ Ainvtp, idx[0], "T")
    other = fit_rank1(X.transpose(idx), 0)
    Tpd = PolyadicTensor([A, *other])

    # Undo permutation.
    Tpd = Tpd.transpose(iperm)

    # Refine U[0] using an ALS step. If the problem is ill-conditioned, it is
    # advised to skip this step by setting refine to False.
    if refine:
        Tpd.factors[0][:] = cpdals_step(T, Tpd, 0)

    return Tpd.normalize()


def cpdals_step(T: TensorType, U: PolyadicTensor, axis: int) -> MatrixType:
    """Compute a single alternating least squares step for CPD.

    Compute a single substep in the alternating least squares algorithm for
    approximating `T` with the canonical polyadic decomposition `U` in a least
    squares sense.

    Parameters
    ----------
    T : TensorType
        Tensor to be approximated.
    U : PolyadicTensor
        Current approximation.
    axis : int
        Axis to compute the update for.

    Returns
    -------
    MatrixType
        Updated factor matrix for the given axis.
    """
    axis = axis if axis >= 0 else T.ndim + axis
    W = inprod_kr(U.factors, U.factors, axis)
    tmp = mtkrprod(T, U.factors, axis).T
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("error", category=LinAlgWarning)
            return tlb.solve_hermitian(W, tmp).T
    except (LinAlgError, LinAlgWarning):
        # If rank-deficient, use pseudoinverse.
        return tlb.lstsq(W, tmp, rcond=None)[0].T


def fit_rank1(T: TensorType, axis: int = 0) -> Sequence[MatrixType]:
    """Fit rank-1 terms to slices of a given tensor.

    Parameters
    ----------
    T : TensorType
        Tensor to be sliced.
    axis : int, default = 0
        Axis defining the slices to loop over.

    Returns
    -------
    Sequence[MatrixType]
        Sequence of matrices such that the outer product of the rth columns approximate
        the rth slice of `T` along the given axis.
    """
    axes = (axis, *(ax for ax in range(T.ndim) if ax != axis))
    approx = tuple(_rank_one(t).factors for t in T.transpose(axes))
    return [np.hstack(f) for f in zip(*approx)]

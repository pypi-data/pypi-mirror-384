"""Tensorization via statistics.

Several statistical functions are provided to map lower-order data to higher-order
tensors, i.e., to *tensorize* the data. The functions :func:`scov` and :func:`dcov`
compute (sequences of) second-order statistics, while functions :func:`cum3`,
:func:`cum4`, :func:`xcum4` and :func:`stcum4` compute higher-order statistics.
"""

import math
from collections.abc import Sequence
from typing import Any

import numpy as np

import pytensorlab.backends.numpy as tlb
from pytensorlab.typing import (
    ArrayType,
    AxisLike,
    MatrixType,
    NonnegativeInt,
)
from pytensorlab.util import argsort
from pytensorlab.util import krr as krr
from pytensorlab.util.indextricks import _ensure_sequence, normalize_axes


def scov(
    X: MatrixType,
    shifts: Sequence[NonnegativeInt] | None = None,
    prewhiten: bool = False,
) -> ArrayType:
    r"""Compute shifted covariance matrices.

    Parameters
    ----------
    X : MatrixType
        The data matrix with observations in rows and variables in columns.
    shifts : Sequenceable[NonnegativeInt], optional
        Sequence of nonnegative integers specifying the shifts. If not provided
        (or None), `shifts` is set to ``range(min(X.shape[0] - 1, X.shape[1]))``.
    prewhiten : bool, default = False
        If True, apply a linear transformation to the columns of `X` such that the
        covariance matrix of the new matrix (without `shifts`) is the identity matrix
        before computing its shifted covariance matrices.

    Returns
    -------
    C : ArrayType
        Array containing the shifted covariance matrices as frontal slices.

    See Also
    --------
    numpy.cov, dcov, cum3, cum4

    Notes
    -----
    The shifted covariance matrices :math:`\mat{C}_{::k}` are computed for a matrix
    :math:`\mat{X} \in \C^{n \times v}`, where each row represents an observation at a
    certain time instance, and each column represents a variable. Herein,

    .. math::

        (\mat{C}_{::k})_{ij} = E\{x_i(t) x_j(t + \tau_{k})^{*}\},

    where the expectation :math:`E` is approximated by a mean that is normalized by
    :math:`(n - 1 - \tau_{k})`, :math:`\tau_k` denotes the ``shifts[k]``,
    :math:`x_i(t)` is the :math:`i`\th mean-centered variable, and
    :math:`x_j(t + \tau_{k})` is the :math:`j`\th mean-centered variable shifted by
    :math:`\tau_k` time steps. The vector :math:`\mat{\tau}` holds a sequence of
    nonnegative integers, each less than or equal to :math:`n - 2`. The superscript
    :math:`^*` denotes the complex conjugate.

    See [SOS1997]_ and [USMD2008]_ for details.
    """
    n, v = X.shape

    shifts = _ensure_sequence(list(range(min(v, n - 1))) if shifts is None else shifts)

    if not all((0 <= x <= n - 2) for x in shifts):
        raise ValueError(
            f"shifts must be a sequence of nonnegative integers, "
            f"each less than or equal to {int(n-2)}"
        )

    # Center the variables.
    X = X - np.mean(X, axis=0)

    # Apply a prewhitening to X if requested.
    if prewhiten:
        X = _prewhiten(X)
        v = X.shape[1]

    X_conj = X.conj()
    # Compute the shifted covariance matrices.
    C = np.zeros((v, v, len(shifts)), dtype=X.dtype)
    for k, t in enumerate(shifts):
        C[:, :, k] = (X[: n - t, :].T @ X_conj[t:, :]) / (n - 1 - t)

    return C


def cum3(X: MatrixType, prewhiten: bool = False) -> ArrayType:
    r"""Compute the third-order cumulant.

    Parameters
    ----------
    X : MatrixType
        The data matrix with observations in rows and variables in columns.
    prewhiten : bool, default = False
        If True, apply a linear transformation to the columns of `X` such that the
        covariance matrix of the new matrix is the identity matrix before computing the
        third-order cumulant.

    Returns
    -------
    C3 : ArrayType
        Array containing the third-order cumulant of the data matrix `X`.

    See Also
    --------
    scov, dcov, cum4, cum4, stcum4

    Notes
    -----
    The third-order cumulant :math:`\ten{C}_{\vec{x}}^{(3)}` is computed for a matrix
    :math:`\mat{X}` in which each row represents an observation, and each column
    represents a variable. Herein,

    .. math::

       (\ten{C}_{\vec{x}}^{(3)})_{ijk} = E\{x_i x_j^{*}x_k^{*}\}

    where the expectation :math:`E` is approximated by the arithmetic mean and
    :math:`x_i` is the :math:`i`\th mean-centered variable (and analogously for
    :math:`x_j` and :math:`x_k`). The superscript :math:`^*` denotes the complex
    conjugate.

    See [TMS1987]_ and [HOSA1993]_ for details.
    """
    # Center the variables.
    X = X - np.mean(X, axis=0)

    # Apply a prewhitening to X if requested.
    if prewhiten:
        X = _prewhiten(X)
    n, v = X.shape

    # Compute the third-order cumulant tensor.
    X_conj = X.conj()
    C3 = (X.T @ krr(X_conj, X_conj)).reshape(v, v, v)
    C3 /= n
    return C3


def cum4(
    X: MatrixType, prewhiten: bool = False
) -> tuple[ArrayType, ArrayType, MatrixType]:
    r"""Compute the fourth-order cumulant.

    Parameters
    ----------
    X : MatrixType
        The data matrix with observations in rows and variables in columns.
    prewhiten : bool, default = False
        If True, apply a linear transformation to the columns of `X` such that the
        covariance matrix of the new matrix is the identity matrix before computing its
        fourth-order cumulant.

    Returns
    -------
    C4 : ArrayType
        Array containing the fourth-order cumulant of the data matrix `X`.
    M4 : ArrayType
        Array containing the fourth-order moment of the data matrix `X`.
    C2 : MatrixType
        Array containing the second-order cumulant of the data matrix `X`.

    See Also
    --------
    scov, dcov, cum3, xcum4, stcum4

    Notes
    -----
    The second-order cumulant (covariance matrix) :math:`\mat{C}_{\vec{x}}^{(2)}`,
    fourth-order moment :math:`\ten{M}_{\vec{x}}^{(4)}`, and fourth-order cumulant
    (quadricovariance tensor) :math:`\ten{C}_{\vec{x}}^{(4)}` are computed for a matrix
    :math:`\mat{X}` where each row represents an observation, and each column 
    represents a variable. Herein,

    .. math::

       (\mat{C}_{\vec{x}}^{(2)})_{ij}   &= E\{x_i x_j^{*}\}\\
       (\ten{M}_{\vec{x}}^{(4)})_{ijkl} &= E\{x_i x_j^{*} x_k^{*} x_l\}\\
       (\ten{C}_{\vec{x}}^{(4)})_{ijkl} &= E\{x_i x_j^{*} x_k^{*} x_l\}
                                           - E\{x_i x_j^{*}\}E\{x_k^{*} x_l\}\\
                                        &\qquad - E\{x_i x_k^{*}\}E\{x_j^{*} x_l\}
                                           - E\{x_i x_l\}E\{x_j^{*} x_k^{*}\}

    where the expectation :math:`E` is approximated by the arithmetic mean, and
    :math:`x_i` is the :math:`i`\th mean-centered variable (and analogously for
    :math:`x_j, x_k, x_l`). The superscript :math:`^*` denotes the complex conjugate.

    See [TMS1987]_ and [HOSA1993]_ for more details.
    """
    # Center the variables.
    X = X - np.mean(X, axis=0)

    # Apply a prewhitening to X if requested.
    if prewhiten:
        X = _prewhiten(X)
    n, v = X.shape

    # Compute the second-order cumulant matrix.
    X_conj = X.conj()

    C2 = X.T @ X_conj
    C2 /= n

    R2 = X.T @ X
    R2 /= n

    # Compute fourth-order moment.
    XXc = krr(X, X_conj)
    M4 = (XXc.T @ XXc).reshape(v, v, v, v).transpose(0, 1, 3, 2)
    M4 /= n

    # Compute the fourth-order cumulant.
    C4 = -C2[:, :, None, None] * C2.T
    C4 += C4.transpose(0, 2, 1, 3)
    C4 += M4
    C4 -= R2[:, None, None, :] * R2.conj()[None, :, :, None]
    return C4, M4, C2


def xcum4(
    X0: MatrixType, X1: MatrixType, X2: MatrixType, X3: MatrixType, center: bool = True
) -> tuple[ArrayType, ArrayType]:
    r"""Compute the fourth-order cross-moment and fourth-order cross-cumulant.

    Parameters
    ----------
    X0 : MatrixType
        The first data matrix with observations in rows and variables in columns.
    X1 : MatrixType
        The second data matrix with observations in rows and variables in columns.
    X2 : MatrixType
        The third data matrix with observations in rows and variables in columns.
    X3 : MatrixType
        The fourth data matrix with observations in rows and variables in columns.
    center : bool, default = True
        Center the data such that each column has mean zero if True.

    Returns
    -------
    C4 : ArrayType
        Array containing the fourth-order cross cumulant.
    M4 : ArrayType
        Array containing the fourth-order cross moment.

    See Also
    --------
    cum3, cum4, stcum4

    Notes
    -----
    The fourth-order cross moment :math:`\ten{M}_{\vec{x}}^{(4)}` and fourth-order
    cross cumulant :math:`\ten{C}_{\vec{x}}^{(4)}` of the matrices :math:`\mat{X}_0`,
    :math:`\mat{X}_1`, :math:`\mat{X}_2` and :math:`\mat{X}_3` are computed. In each 
    matrix, the rows represent observations, and the columns represent variables. 
    Herein,

    .. math::
    
       (\ten{M}_{\vec{x}}^{(4)})_{ijkl}
                            &= E\{x_{0i} x_{1j}^{*} x_{2k}^{*} x_{3l}\}\\
       (\ten{C}_{\vec{x}}^{(4)})_{ijkl}
                           &= E\{x_{0i} x_{1j}^{*} x_{2k}^{*} x_{3l}\}
                           - E\{x_{0i} x_{1j}^{*}\}E\{x_{2k}^{*} x_{3l}\}\\
                           &\qquad -  E\{x_{0i} x_{2k}^{*}\}E\{x_{1j}^{*} x_{3l}\}
                           - E\{x_{0i} x_{3l}\}E\{x_{1j}^{*} x_{2k}^{*}\}

    where the expectation :math:`E` is approximated by the arithmetic mean and
    :math:`x_{ri}` is the :math:`i`\th mean centered variable (and analogously for
    :math:`x_{rj}, x_{rk}` and :math:`x_{rl}`, for :math:`r = 0, 1, 2, 3`).
    The superscript :math:`^*` denotes the complex conjugate.
    """
    n = X0.shape[0]
    if (X1.shape[0] != n) or (X2.shape[0] != n) or (X3.shape[0] != n):
        raise ValueError("all matrices must have the same number of rows")

    # Center the variables.
    if center:
        X0 = X0 - np.mean(X0, axis=0)
        X1 = X1 - np.mean(X1, axis=0)
        X2 = X2 - np.mean(X2, axis=0)
        X3 = X3 - np.mean(X3, axis=0)
    v0, v1, v2, v3 = X0.shape[1], X1.shape[1], X2.shape[1], X3.shape[1]

    # Compute the fourth-order cross moment.
    X1_conj = X1.conj()
    X2_conj = X2.conj()
    X0X1c = krr(X0, X1_conj)
    X2cX3 = krr(X2_conj, X3)
    M4 = (X0X1c.T @ X2cX3).reshape(v0, v1, v2, v3)
    M4 /= n

    # Compute second order contributions.
    s1 = X0.T @ X1_conj
    s1 /= n

    s2 = X2_conj.T @ X3
    s2 /= n

    s3 = X0.T @ X2_conj
    s3 /= n

    s4 = X1_conj.T @ X3
    s4 /= n

    s5 = X0.T @ X3
    s5 /= n

    s6 = X1_conj.T @ X2_conj
    s6 /= n

    # Compute the fourth-order cross cumulant.
    C4 = -s1[:, :, None, None] * s2[None, None, :, :]
    C4 += M4
    C4 -= s3[:, None, :, None] * s4[None, :, None, :]
    C4 -= s5[:, None, None, :] * s6[None, :, :, None]

    return C4, M4


def stcum4(X: MatrixType, shift: NonnegativeInt = 0) -> ArrayType:
    r"""Compute the fourth-order spatio-temporal cumulant.

    Parameters
    ----------
    X : MatrixType
        The data matrix with observations in rows and variables in columns.
    shift : NonnegativeInt, default = 0
        Maximum time shift (lag) for computing the spatio-temporal cumulant. It defines 
        the symmetric interval `[-shift, shift]` for time shifts applied to signals. 

    Returns
    -------
    C4 : ArrayType
        Array containing the fourth-order spatio-temporal cumulant.

    See Also
    --------
    cum3, cum4, xcum4

    Notes
    -----
    The fourth-order spatio-temporal cumulant tensor :math:`\ten{C}_{\vec{x}}^{(4)}` is
    computed for a matrix :math:`\mat{X}` in which each row represents an observation,
    and each column represents a variable. Herein,

    .. math::

       (\ten{C}_{\vec{x}}^{(4)})_{i j k l t_0 t_1 t_2}
          &= E\{x_i(t) x_j(t+t_0)^{*} x_k(t+t_1)^{*} x_l(t+t_2)\}\\
          &\qquad - E\{x_i(t) x_j(t+t_0)^{*}\}E\{x_k(t+t_1)^{*} x_l(t+t_2)\}\\
          &\qquad - E\{x_i(t) x_k(t+t_1)^{*}\}E\{x_j(t+t_0)^{*} x_l(t+t_2)\}\\
          &\qquad - E\{x_i(t) x_l(t+t_2)\}E\{x_j(t+t_0)^{*} x_k(t+t_1)^{*}\}

    where the expectation :math:`E` is approximated by the arithmetic mean, and
    :math:`x_i` represents the :math:`i`\th mean-centered variable (and analogously 
    for :math:`x_j, x_k`, and :math:`x_l`). The superscript :math:`^*` denotes the 
    complex conjugate. Variables :math:`t_0, t_1`, and :math:`t_2` vary between
    `-shift` and `shift` and are indexed as ``np.arange(0, 2 * shift + 1)``.
    """
    n, v = X.shape

    if n < 2 * shift + 1:
        raise ValueError(
            f"time shift must be nonnegative integer less than or "
            f"equal to {int((n-1)/2)}, got {shift}"
        )

    # Center the variables.
    X = X - np.mean(X, axis=0)

    # Compute spatio-temporal cumulant by computing the cross
    # cumulant for all time shifts.
    t = np.arange(0, n - 2 * shift)
    if not np.iscomplex(X).any():
        C4 = np.zeros((2 * shift + 1, 2 * shift + 1, 2 * shift + 1, v, v, v, v))
        for t0 in range(0, 2 * shift + 1):
            for t1 in range(t0, 2 * shift + 1):
                for t2 in range(t1, 2 * shift + 1):
                    tmp, _ = xcum4(
                        X[t + shift, :],
                        X[t + t0, :],
                        X[t + t1, :],
                        X[t + t2, :],
                        False,
                    )
                    C4[t0, t1, t2, :, :, :, :] = tmp
                    C4[t1, t0, t2, :, :, :, :] = np.transpose(tmp, (0, 2, 1, 3))
                    C4[t1, t2, t0, :, :, :, :] = np.transpose(tmp, (0, 2, 3, 1))
                    C4[t0, t2, t1, :, :, :, :] = np.transpose(tmp, (0, 1, 3, 2))
                    C4[t2, t0, t1, :, :, :, :] = np.transpose(tmp, (0, 3, 1, 2))
                    C4[t2, t1, t0, :, :, :, :] = np.transpose(tmp, (0, 3, 2, 1))
    else:
        C4 = np.zeros(
            (2 * shift + 1, 2 * shift + 1, 2 * shift + 1, v, v, v, v), dtype="complex"
        )
        for t0 in range(0, 2 * shift + 1):
            for t1 in range(t0, 2 * shift + 1):
                for t2 in range(0, 2 * shift + 1):
                    tmp, _ = xcum4(
                        X[t + shift, :],
                        X[t + t0, :],
                        X[t + t1, :],
                        X[t + t2, :],
                        False,
                    )
                    C4[t0, t1, t2, :, :, :, :] = tmp
                    C4[t1, t0, t2, :, :, :, :] = np.transpose(tmp, (0, 2, 1, 3))

    return C4.transpose(3, 4, 5, 6, 0, 1, 2)


def dcov(
    X: ArrayType,
    observation_axis: int = 0,
    variable_axis: int = 1,
    perm: tuple[int, int] | int | bool | None = None,
    bias: bool = False,
    includenan: bool = True,
    **kwargs: Any,
) -> ArrayType:
    """Compute covariance matrices along specific dimensions.

    Parameters
    ----------
    X : ArrayType
        Array containing observations for which the covariance matrices are computed.
    observation_axis : int, default = 0
        Axis corresponding to the dimension representing observations.
    variable_axis : int, default = 1
        Axis corresponding to the dimension representing variables.
    perm : tuple[int, int] | int | bool | None, default = None
        Axes along which to place the covariance matrices in the output tensor. If None
        or False, the axes ``(observation_axis, variable_axis)`` are used. If True, the
        covariance matrices are placed along the first two modes. If an integer is
        given, the matrices are placed along axes ``(perm, perm + 1)``. If a tuple, the
        specified axes ``(perm[0], perm[1])`` are used instead.
    includenan : bool, default = True
        If True, the output contains NaN values if the input contains NaNs or missing
        entries. If False, any slices along the observation axis that contain NaN values
        are omitted.
    bias : bool, default = False
        If False, the normalization is by `N - 1`, where `N` is the number of
        observations given (unbiased estimate). If `bias` is True, then normalization
        is by `N`. These values can be overridden by using the keyword `ddof`.
    **kwargs
        Extra arguments to :func:`numpy.cov`: refer to its documentation for a list of
        all possible arguments.

    Returns
    -------
    C : ArrayType
        Array containing covariance matrices.

    Raises
    ------
    ValueError
        If `observation_axis` and `variable_axis` refer to the same axis.

    See Also
    --------
    numpy.cov, scov

    Notes
    -----
    See [SDT2015]_ for details.
    """
    observation_axis = normalize_axes(observation_axis, X.ndim, fill=False)[0]
    variable_axis = normalize_axes(variable_axis, X.ndim, fill=False)[0]

    if observation_axis == variable_axis:
        raise ValueError("observation_axis and variable_axis must be different")
    axes: AxisLike = (observation_axis, variable_axis)

    if perm is None:
        perm = (observation_axis, variable_axis)
    elif isinstance(perm, bool):
        perm = (0, 1) if perm else (observation_axis, variable_axis)
    elif isinstance(perm, int):
        perm = (perm, perm + 1)

    axes = normalize_axes(axes, X.ndim, fill=False)
    filledaxes = normalize_axes(axes, X.ndim, fill=True)
    filledperm = normalize_axes((perm[0], perm[1]), X.ndim, fill=True)

    X = X.transpose(filledaxes)
    sz = X.shape

    # Reshape to third-order tensor.
    X = X.reshape(sz[0], sz[1], math.prod(sz[2:]))
    C: ArrayType = np.zeros((sz[1], sz[1], math.prod(sz[2:])), dtype=X.dtype)

    # Prevent redundant arguments.
    kwargs.pop("rowvar", None)
    kwargs.pop("bias", None)

    # Compute covariance matrices.
    for k in range(X.shape[2]):
        if includenan:
            data = X[:, :, k]
        else:
            valid_rows = ~np.any(np.isnan(X[:, :, k]), axis=1)
            data = X[valid_rows, :, k]
        C[:, :, k] = np.cov(
            data,
            rowvar=False,
            bias=bias,
            **kwargs,
        )

    C = C.reshape(sz[1], sz[1], *sz[2:])

    if not perm == (0, 1):
        newshape = argsort(filledperm)
        C = C.transpose(newshape)

    return C


def _prewhiten(X: MatrixType, keepdims: bool = True) -> MatrixType:
    """Prewhiten the input matrix `X`."""
    n, _ = X.shape
    U, S, _ = tlb.svd(X, full_matrices=False)

    if keepdims:
        U[:, S < S[0] * 1e-15] = 0
    else:
        U = U[:, S >= S[0] * 1e-15]

    U *= math.sqrt(n - 1)
    return U

"""Generate tensor with prescribed multilinear singular values.

Two optimization-based methods for generating a random tensor with given multilinear
singular values are given. Note that not all combinations of multilinear singular values
are feasible; if unfeasible, a best effort solution is returned. For more information on
mutilinear singular values see :func:`.mlsvd`.
"""

from collections.abc import Generator, Sequence
from typing import Any, cast

import numpy as np
import scipy.optimize as opt

import pytensorlab as tl
import pytensorlab.backends.numpy as tlb
from pytensorlab.typing import ArrayType, VectorType
from pytensorlab.typing.core import MatrixType, Shape

from ..random.rng import get_rng


def gentensor_mlsv_altproj(
    sv: Sequence[VectorType],
    a: ArrayType | None = None,
    maxiter: int = 100,
    randomize: bool = False,
    iscomplex: bool = False,
    _rng: np.random.Generator | int | None = None,
) -> ArrayType:
    """Create tensor with given multilinear singular values via alternating projection.

    A random all-orthogonal array is computed such that its multilinear singular values
    match the given values, if possible. An alternation projection based method is used.

    Parameters
    ----------
    sv : Sequence[VectorType]
        Tuple of multilinear singular values.
    a : ArrayType, optional
        Initial guess for the optimization routine. If not given, a couple of iterations
        of alternating projection are performed on a random starting value.
    maxiter : int
        Maximal number of iterations performed by the optimization routine.
    randomize : bool
        Multiply by a random orthogonal matrix in each mode.
    iscomplex : bool
        Return a complex tensor; only used if randomize is True. This flag is always
        True if a complex initial guess a is given.
    _rng : numpy.random.Generator | int, optional
        Seed or random number generator used for all random operations in this
        function. If an integer is given, a new generator is created with that seed. If
        a generator is provided, it is used directly. If None, the global generator
        (set via `set_rng`) is used.

    Returns
    -------
    ArrayType:
        All-orthogonal array with multlinear singular values `sv`.

    See Also
    --------
    gentensor_mlsv : Alternative algorithm based on Gauss--Newton.
    .scipy.optimize.minimize : Optimization algorithm used.

    Notes
    -----
    Not all combinations of multlinear singular values are feasible. If this is
    the case, the algorithm returns a best effort.

    This optimization-based algorithm is an improved version of the algorithm presented
    in [6]_. This function provides the function evaluation, gradient and Hessian-vector
    product for an inexact Gauss--Newton algorithm and calls the trust-ncg method in
    :func:`scipy.optimize.minimize`.

    References
    ----------
    .. [6] W. Hackbusch, D. Kressner, A. Uschmajew, "Perturbation of higher-order
       singular values," SIAM Journal on Applied Algebra and Geometry, vol. 1, no. 1,
       July 2017, pp. 374–387.

    Examples
    --------
    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> sv = tuple(np.ones((s,)) / s for s in (3, 4, 5))
    >>> a = tl.gentensor_mlsv_altproj(sv)
    >>> np.isclose(tl.matdot(a,a,0), np.diag(sv[0] ** 2))
    array([[False,  True,  True],
           [ True, False,  True],
           [ True,  True, False]])
    """
    _rng = get_rng(_rng)

    sv_mat = tuple(np.asarray(s).reshape((-1, 1)) for s in sv)
    shape = tuple(s.size for s in sv_mat)
    ndim = len(shape)
    randn = _rng.standard_normal

    if a is None:
        a = randn(shape)
        if iscomplex:
            a = a + randn(shape) * 1j
    else:
        if a.shape != shape:
            raise ValueError(
                f"shape of a does not match given singular values: shape is {a.shape} "
                f"but expected {shape}"
            )
        iscomplex = cast(bool, iscomplex or np.iscomplex(a).any())

    for _ in range(maxiter):
        for n, s in enumerate(sv_mat):
            # Set singular values in mode n.
            _, _, vh = tlb.svd(tl.tens2mat(a, 0), full_matrices=False)
            a = cast(MatrixType, s * vh[: shape[n], :])
            # Undo matrix unfolding.
            a = a.reshape((shape[n],) + shape[n + 1 :] + shape[:n])
            a = a.transpose(tuple(range(1, ndim)) + (0,))

    def gen_rand_orth_factors(
        shape: Shape, iscomplex: bool
    ) -> Generator[MatrixType, None, None]:
        for s in shape:
            U = randn((s, s))
            if iscomplex:
                U = U + randn((s, s)) * 1j
            yield tlb.orth(U)

    if randomize:
        # Multiply by a random orthgonal matrix in each mode.
        U = list(gen_rand_orth_factors(shape, iscomplex))
        a = tl.tmprod(a, U, range(ndim))

    return a


def gentensor_mlsv(
    sv: Sequence[VectorType],
    a: ArrayType | None = None,
    maxiter: int = 5000,
    _rng: np.random.Generator | int | None = None,
    **kwargs: Any,
) -> ArrayType:
    """Generate tensor with given multilinear singular values using Gauss--Newton.

    A random all-orthogonal array is computed such that its multilinear singular values
    match the given values, if possible. An inexact Gauss--Newton based algorithm is
    used.

    Parameters
    ----------
    sv : Sequence[VectorType]
        Tuple of multilinear singular values.
    a : ArrayType, optional
        Initial guess for the optimization routine. If not given, a couple of iterations
        of alternating projection are performed on a random starting value.
    maxiter : int
        Maximal number of iterations performed by the optimization routine.
    _rng : numpy.random.Generator | int, optional
        Seed or random number generator used for all random operations in this
        function. If an integer is given, a new generator is created with that seed. If
        a generator is provided, it is used directly. If None, the global generator
        (set via `set_rng`) is used.
    **kwargs
        Additional options passed on to the optimization routine as keyword arguments.

    Returns
    -------
    ArrayType:
        All-orthogonal array with multlinear singular value `sv`.

    See Also
    --------
    gentensor_mlsv_altproj : Alternative algorithm based on alternating projection.
    scipy.optimize.minimize : Optimization algorithm used.

    Notes
    -----
    Not all combinations of multlinear singular values are feasible. If this is
    the case, the algorithm returns a best effort.

    This optimization-based algorithm is an optimized version of the algorithm presented
    in [5]_. This function provides the objective function evaluation, gradient and
    Hessian-vector product for an inexact Gauss--Newton algorithm and calls the
    trust-ncg method in :func:`scipy.optimize.minimize`.

    References
    ----------
    .. [5] M. Boussé, N. Vervliet, I. Domanov, O. Debals, L. De Lathauwer, "Linear
       systems with a canonical polyadic decomposition constrained solution: Algorithms
       and applications", Numerical Linear Algebra with Applications, Special Issue on
       Matrix Equations and Tensor Techniques, vol. 25, no. 6, Aug. 2018, pp. 1-18.

    Examples
    --------
    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> sv = tuple(np.ones((s,)) / s for s in (3, 4, 5))
    >>> a = tl.gentensor_mlsv(sv)
    >>> np.isclose(tl.matdot(a,a,0), np.diag(sv[0] ** 2))
    array([[False,  True,  True],
           [ True, False,  True],
           [ True,  True, False]])
    """
    _rng = get_rng(_rng)

    sv = tuple(np.asarray(s) for s in sv)
    shape = tuple(s.size for s in sv)
    ndim = len(shape)

    if a is not None and a.shape != shape:
        raise ValueError(
            f"shape of a does not match given singular values: shape is {a.shape} "
            f"but expected {shape}"
        )

    G = tuple(np.diag(np.square(s)) for s in sv)

    def fval(z: VectorType) -> float:
        """Objective function value."""
        Z = z.reshape(shape)
        GZ = tuple(tl.matdot(Z, Z, n) for n in range(ndim))
        res = tuple(tl.frob(g - gz, True) for g, gz in zip(G, GZ))
        return 0.5 * np.sum(res)

    def grad(z: VectorType) -> VectorType:
        """Gradient."""
        Z = z.reshape(shape)
        GZ = tuple(tl.matdot(Z, Z, n) for n in range(ndim))
        residual = tuple(gz - g for g, gz in zip(G, GZ))
        grad = np.zeros(shape)
        for n, res in enumerate(residual):
            grad += tl.tmprod(Z, res.conj().T + res, n, "T")
        return grad.reshape((-1,))

    def hessp(z: VectorType, x: VectorType) -> VectorType:
        """Hessian-vector product."""
        Z = z.reshape(shape)
        X = x.reshape(shape)
        y = np.zeros(shape)
        for n in range(ndim):
            W = tl.matdot(X, Z, n)
            tmp = tl.tmprod(Z, W + W.conj().T, n)
            y += 2 * np.real(tmp)
        return y.reshape((-1,))

    if a is None:
        a = gentensor_mlsv_altproj(sv, maxiter=2, _rng=_rng)

    # fill in default parameters for minimize if not set by user
    kwargs["method"] = kwargs.get("method", "trust-ncg")
    kwargs["tol"] = kwargs.get("tol", 1e-30)
    options = kwargs.get("options", {})
    if not isinstance(options, dict):
        raise ValueError("options is not a dictionary")
    options["maxiter"] = options.get("maxiter", maxiter)
    kwargs["options"] = options

    result = opt.minimize(fval, a.ravel(), hessp=hessp, jac=grad, **kwargs)
    return result.x.reshape(shape)

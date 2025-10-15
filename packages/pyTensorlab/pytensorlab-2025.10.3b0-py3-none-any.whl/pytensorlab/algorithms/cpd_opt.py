r"""Optimization algorithms for computing the canonical polyadic decomposition.

In a polyadic decomposition, an Nth-order tensor :math:`\mathcal{A}` with dimensions
:math:`I_{0} \times I_{1} \times \cdots \times I_{N-1}` is expressed by a rank-:math:`R`
tensor :math:`\ten{T}` given by

.. math::

   \ten{T} = \sum_{r=0}^{R-1} \vec{u}^{(0)}_r \op \vec{u}^{(1)}_r \op
    \cdots \op \vec{u}^{(N-1)}_r.

In pyTensorlab, such a structured tensor can be formed with the class
:class:`.PolyadicTensor`. A canonical polyadic
decomposition (CPD) is a polyadic tensor of minimal rank.

pyTensorlab supports various optimization-based algorithms to compute a CPD. These
algorithms aim to minimize the loss function::

    0.5 * tl.frob(tl.PolyadicTensor(U) - T) ** 2

where ``U`` is a list of factor matrices describing the polyadic decomposition. Below,
we give an annotated list of algorithms available.

Functions
---------
:func:`cpd_als`
    Uses the alternating least squares algorithm; see :cite:`kroonenberg1980`.
:func:`cpd_minf`
    Uses unconstrained nonlinear optimization.
:func:`cpd_nls`
    Uses nonlinear least squares; see :cite:`r739`.
:func:`cpd_nls_scipy`
    Similar to :func:`cpd_nls`, but uses SciPy optimization routines instead of
    built-in algorithms.

Notes
-----
See, e.g., :cite:`kroonenberg2008` and :cite:`r739` for more information on algorithms.

Examples
--------
>>> import pytensorlab as tl
>>> shape = (5, 6, 7)
>>> nterm = 2
>>> T = tl.random.rand(shape)
>>> init = tl.PolyadicTensor.random(shape, nterm)
>>> Tcpd, _ = tl.cpd_als(T, init)
"""

import warnings
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from itertools import combinations, islice, permutations
from typing import Any, Literal, cast

import numpy as np
import scipy.linalg as nla
from scipy.optimize import minimize
from scipy.sparse.linalg import cg

import pytensorlab as tl
import pytensorlab.backends.numpy as tlb
from pytensorlab.algorithms.optimization_default_settings import (
    default_minimize_options,
    default_minimize_solver_options,
)
from pytensorlab.datatypes import (
    PolyadicTensor,
    Tensor,  # noqa: F401 # sphinx
)
from pytensorlab.optimization import (
    IterativeSolver,
    IterativeSolverOptions,
    NewtonDirectProblem,
    NewtonIterativeProblem,
    OptimizationOptions,
    OptimizationProgressLogger,
    ProgressPrinter,
    StoppingCriterionAlgorithm,
    StoppingCriterionReached,
    VoidPrinter,
    default_printer_fields,
    default_stopping_criteria,
    minimize_trust_region,
)
from pytensorlab.optimization.problem import Problem
from pytensorlab.typing import (
    Axis,
    MatrixType,
    MinfOptimizationMethod,
    NonnegativeFloat,
    NonnegativeInt,
    TensorType,
    VectorType,
)
from pytensorlab.util import Options
from pytensorlab.util.exceptions import ShapeMismatchException
from pytensorlab.util.indextricks import findfirst, normalize_axes
from pytensorlab.util.utils import (
    _mapC2R,
    _mapC2Rmatrix,
    _mapR2C,
    hadamard,
    hadamard_all,
)

from .TensorOptimizationKernel import (
    TensorOptimizationKernel,
    cached,
    ensure_deserialized,
    ensure_use_gramian,
    ensure_use_preconditioner,
)


class PolyadicKernel(TensorOptimizationKernel[PolyadicTensor]):
    """Provide routines for least-squares fitting a polyadic decomposition.

    The kernel provides the computational routines required for optimization algorithms
    that minimize the least-squares error between a tensor `T` and its approximation by
    a polyadic decomposition `z`. The following objective function is used::

        0.5 * tl.frob(numpy.array(z) - T) ** 2

    The kernel provides implementations for the objective function value :func:`objfun`
    and the gradient :func:`gradient`. Moreover, :func:`hessian` implements the Gramian
    of the Jacobian, which is a positive semidefinite approximation to the Hessian,
    which is used in quasi-Newton type methods such as in(exact) Gauss-Newton and
    Levenberg-Marquardt; see [SVD2013]_.

    Parameters
    ----------
    T : TensorType
        Tensor to be decomposed.
    use_gramian: bool,  default = True
        If True, update the cached variables to compute the Hessian approximation.
        The parameter must be set to True if :func:`hessian` or
        :func:`hessian_vector` are used.
    use_preconditioner : bool,  default = False
        If True, update cached variables required to compute the preconditioner. The
        parameter must be set to True if :func:`M_blockJacobi` is used.

    Attributes
    ----------
    use_gramian : bool,  default = True
        If True, update the cached variables to compute the Hessian approximation.
        The parameter must be set to True if :func:`hessian` or
        :func:`hessian_vector` are used.
    use_preconditioner : bool,  default = False
        Update cached variables required to compute the preconditioner if True. The
        parameter must be set to True if :func:`M_blockJacobi` is used.
    """

    def __init__(
        self,
        T: TensorType,
        use_gramian: bool = True,
        use_preconditioner: bool = False,
    ):
        """Initialize the polyadic kernel.

        Parameters
        ----------
        T : TensorType
            Tensor to be decomposed.
        use_gramian: bool,  default = True
            If True, update the cached variables to compute the Hessian approximation.
            The parameter must be set to True if :func:`hessian` or
            :func:`hessian_vector` are used.
        use_preconditioner : bool,  default = False
            If True, update cached variables required to compute the preconditioner. The
            parameter must be set to True if :func:`M_blockJacobi` is used.
        """
        # tensor protected properties.
        self._T: TensorType = T

        # cached variables
        self._objfun_value: float
        self._residual: TensorType
        self._T2 = tl.frob(T, squared=True)
        self._UHU: Sequence[MatrixType] = []
        self._Wn: Sequence[MatrixType] = []
        self._invWn: Sequence[MatrixType] = []
        self._zcached: VectorType = np.empty((1,))

        # set computational settings
        self.use_gramian: bool = use_gramian
        self.use_preconditioner: bool = use_preconditioner

    def isvalid(self, z: PolyadicTensor) -> bool:
        """Validate compatibility of kernel parameters, data and variables.

        Checks if the kernel is valid, i.e., if all kernel methods can be computed using
        this particular combination of parameters, data, and variables `z`.

        Parameters
        ----------
        z : PolyadicKernel
            Optimization variables to be validated.

        Returns
        -------
        bool
            True if kernel is valid, otherwise False.

        Raises
        ------
        ShapeMismatchException
            If the shape of `T` and the shape of `z` do not match.
        """
        if z.ndim != self._T.ndim:
            raise ValueError(
                f"ndim of z does not match T: got {z.ndim} but expected {self._T.ndim}"
            )
        if z.shape != self._T.shape:
            raise ShapeMismatchException(self._T.shape, z.shape)
        return True

    def update_cache(self, z: PolyadicTensor) -> None:
        """Update cached attributes.

        Parameters
        ----------
        z : PolyadicTensor
            Variables for which the cached attributes will be computed.

        Notes
        -----
        Instead of calling this method, the :func:`.cached` decorator should be used.
        """
        self._zcached = z._data
        self._residual = tl.residual(z, self._T)
        self._objfun_value = 0.5 * tl.frob(self._residual, squared=True)
        if self.use_gramian:
            self._UHU = [zi.T @ zi.conj() for zi in z.factors]
            self._Wn = hadamard_all(self._UHU, nexclude=1)
        if self.use_preconditioner:
            self._invWn = [tlb.inv(W) for W in self._Wn]

    @ensure_deserialized
    @cached
    def objfun(self, z: PolyadicTensor) -> float:
        """Compute the objective function.

        Evaluate the least squares cost function ``0.5 * tl.frob(numpy.array(z) - T,
        squared)**2`` in the variables `z`.

        Parameters
        ----------
        z : PolyadicTensor
            Current iterate.

        Returns
        -------
        float
            Objective function value.
        """
        return self._objfun_value

    @ensure_deserialized
    @cached
    def gradient(self, z: PolyadicTensor) -> PolyadicTensor:
        """Compute the gradient.

        Evaluate the gradient of the objective function in the optimization `z`.

        Parameters
        ----------
        z : PolyadicTensor
            Current iterate.

        Returns
        -------
        PolyadicTensor
            Gradient of the CPD cost function.
        """
        gradient = tl.mtkrprod(self._residual, z.factors)
        return tl.PolyadicTensor(gradient)

    @ensure_use_gramian
    @ensure_deserialized
    @cached
    def hessian_vector(self, z: PolyadicTensor, x: PolyadicTensor) -> PolyadicTensor:
        """Compute the approximate Hessian vector product.

        Compute the product of the Hessian evaluated in `z` and a vector `x`. Here, the
        Gramian of the Hessian is used as a positive semidefinite approximation of the
        Hessian.

        Parameters
        ----------
        z : PolyadicTensor
            Current iterate in which the Gramian is evaluated.
        x : PolyadicTensor
            Vector that is multiplied with the approximate Hessian. The actual vector
            used is ``x._data``.

        Returns
        -------
        PolyadicTensor
            The product of the approximate Hessian and the vector.

        See Also
        --------
        hessian
        """
        y: list[MatrixType] = [xi @ wi for (xi, wi) in zip(x.factors, self._Wn)]
        xzm = [xt.T @ zf.conj() for xt, zf in zip(x.factors, z.factors)]
        for n in range(z.ndim):
            idx_wnm = islice(
                permutations(range(z.ndim), 2),
                n * (z.ndim - 1),
                (n + 1) * (z.ndim - 1),
            )
            idx_xzm = [j for j in range(z.ndim) if j != n]
            xzWnm = [
                hadamard(self._UHU, exclude=widx) * xzm[xidx]
                for widx, xidx in zip(idx_wnm, idx_xzm)
            ]
            y[n] = y[n] + z.factors[n] @ sum(xzWnm)
        return tl.PolyadicTensor(y)

    @ensure_use_gramian
    @ensure_deserialized
    @cached
    def hessian(self, z: PolyadicTensor) -> MatrixType:
        """Compute a positive semidefinite approximation of the Hessian.

        Evaluate the Gramian of the Hessian as a positive semidefinite approximation of
        the Hessian in the variables `z`.

        Parameters
        ----------
        z : PolyadicTensor
            Current iterate in which the Gramian is evaluated.

        Returns
        -------
        MatrixType
            Gramian of the Hessian evaluated in `z`.

        See Also
        --------
        hessian_vector
        """
        sz = np.array(z.shape) * z.nterm
        JHJ: list[list[MatrixType]] = [[np.empty((m, n)) for m in sz] for n in sz]
        for i in range(z.ndim):
            JHJ[i][i] = tl.kron(np.eye(z.shape[i]), self._Wn[i].conj())

        if z.ndim == 2:
            tmp = tlb.einsum(
                "ik,jl->iljk", z.factors[0], z.factors[1].conj(), optimize="greedy"
            )
            JHJ[0][1] = np.reshape(tmp, (sz[0], sz[1]))
            JHJ[1][0] = JHJ[0][1].conj().T
        else:
            znm = [
                np.multiply.outer(z1, z2.conj())
                for (z1, z2) in combinations(z.factors, 2)
            ]
            Wnm = hadamard_all(self._UHU, nexclude=2)
            zWnm = [
                tlb.einsum("ikjl,kl->iljk", z_, w_, optimize="greedy")
                for z_, w_ in zip(znm, Wnm)
            ]
            ij: Iterator[tuple[int, int]] = combinations(tuple(range(z.ndim)), 2)
            for zw, (i, j) in zip(zWnm, ij):
                JHJ[i][j] = np.reshape(zw, (sz[i], sz[j]))
                JHJ[j][i] = JHJ[i][j].conj().T

        return np.block(JHJ)

    @ensure_use_gramian
    @ensure_use_preconditioner
    @ensure_deserialized
    @cached
    def M_blockJacobi(self, z: PolyadicTensor, b: PolyadicTensor) -> PolyadicTensor:
        """Apply block-Jacobi preconditioner.

        Applies the block-Jacobi preconditioner to `b`.

        Parameters
        ----------
        z : PolyadicTensor
            Current iterate.
        b : PolyadicTensor
            `PolyadicTensor` to which the preconditioner is applied.

        Returns
        -------
        PolyadicTensor
            Result of applying the preconditioner.
        """
        x = [bfactor @ invW for invW, bfactor in zip(self._invWn, b.factors)]
        return tl.PolyadicTensor(x)

    def M_blockJacobi_serialized(self, z: VectorType, b: VectorType) -> VectorType:
        """Apply block-Jacobi to serialized PolyadicTensor.

        Parameters
        ----------
        z : VectorType
            Serialized current iterate.
        b : VectorType
            Serialized `PolyadicTensor` to which the preconditioner is applied.

        Returns
        -------
        VectorType
            Serialized result of applying the preconditioner.
        """
        zs = self.deserialize(z)
        bs = self.deserialize(b)
        return self.serialize(self.M_blockJacobi(zs, bs))

    def deserialize(self, z: VectorType) -> PolyadicTensor:
        """Return a given vector in PolyadicTensor format.

        Parameters
        ----------
        z : VectorType
            The serialized `PolyadicTensor`.

        Returns
        -------
        PolyadicTensor
            The `PolyadicTensor` corresponding to the given vector `z`.
        """
        return tl.PolyadicTensor.from_vector(
            z, self._T.shape, int(np.size(z) / sum(self._T.shape)), copy=False
        )

    def serialize(self, z: PolyadicTensor) -> VectorType:
        """Return a given PolyadicTensor in serialized format.

        Parameters
        ----------
        z : PolyadicTensor
            The `PolyadicTensor` to be serialized.

        Returns
        -------
        VectorType
            The serialized `PolyadicTensor`.
        """
        return z._data


@dataclass
class CPDAlsOptions(Options):
    """Options for :func:`cpd_als`.

    See Also
    --------
    cpd_als
    """

    max_iterations: NonnegativeInt = 500
    """The maximum number of iterations."""

    tol_relfval: NonnegativeFloat = 1e-8
    """Tolerance for relative change in objective function value. 
    
    Note that because the objective function is a squared norm, `tol_relfval` can be as
    small as ``numpy.finfo(float).eps ** 2``.
    """

    tol_relstep: NonnegativeFloat = 1e-6
    """Tolerance for step size relative to the norm of the current iterate."""

    tol_absfval: NonnegativeFloat = 0.0
    """Tolerance for absolute change in objective function value."""

    fast_update: bool = True
    """Use a faster but less accurate function value estimate if True.
    
    This is usually safe unless a high accuracy solution is required.
    """

    order: Axis = field(default_factory=tuple[int])
    """The order in which to update the factor matrices of the polyadic tensor.
    
    If set to None, the order is set to ``tuple(range(T.ndim))``.
    """

    display: NonnegativeInt = 10
    """Progress is printed after every `display` iterations. 
    
    If set to 0, the printing is completely suppressed.
    """


def cpd_als(
    T: TensorType,
    Tinit: PolyadicTensor,
    options: Options | None = None,
) -> tuple[PolyadicTensor, OptimizationProgressLogger]:
    """Compute the canonical polyadic decomposition using alternating least squares.

    Via the alternating least squares (ALS) algorithm, the given tensor `T` is
    approximated by a polyadic tensor. The following objective function in ``U``
    is used::

        0.5 * tl.frob(numpy.array(U) - T) ** 2

    Parameters
    ----------
    T : TensorType
        Tensor to be approximated by a polyadic tensor.
    Tinit : PolyadicTensor
        Starting point for the algorithm.
    options : CPDAlsOptions, default = CPDAlsOptions()
        Options to change settings of the ALS algorithm.

    Returns
    -------
    Uopt : PolyadicTensor
        Resulting polyadic decomposition.
    logger : OptimizationProgressLogger
        Log containing optimization progress information and stopping criteria.

    Raises
    ------
    ValueError
        If `order` contains repeated axes.
    ValueError
        If `order` is not a permutation of ``range(T.ndim)``.
    ValueError
        If any axis in `order` is not within ``range(-ndim, ndim)``.
    """
    options = CPDAlsOptions.from_options(options)
    # check dimension compatibility of tensor and initial factor matrices
    if T.ndim != Tinit.ndim:
        raise ValueError(
            f"ndim of initialization U does not match ndim of data T; "
            f"got {Tinit.ndim} but expected {T.ndim}"
        )
    if not T.shape == Tinit.shape:
        boolshape = np.array(T.shape) != np.array(Tinit.shape)
        raise ValueError(
            f"the shape of U does not match the shape of T at indices "
            f"{findfirst(boolshape)}: U has shape {Tinit.shape} while expected "
            f"{T.shape}"
        )
    # check computation order
    order = tuple(range(T.ndim)) if not options.order else options.order
    order = normalize_axes(order, T.ndim, ispermutation=True)

    # ensure that Tinit is complex if T is complex
    if np.iscomplexobj(T) and not np.iscomplexobj(Tinit):
        Tinit = tl.PolyadicTensor.from_vector(
            Tinit._data.astype(complex), Tinit.shape, Tinit.nterm
        )

    # keep initial factor matrices
    Ures = tl.PolyadicTensor(Tinit.factors)
    fval = _objfun(T, Ures)
    T2 = tl.frob(T, squared=True)
    UHU = [Ux.conj().T @ Ux for Ux in Ures.factors]

    # initialize OptimizationProgressLogger and set stopping criteria
    criteria = default_stopping_criteria(
        tol_relfval=options.tol_relfval,
        tol_absfval=options.tol_absfval,
        tol_relstep=options.tol_relstep,
        max_iter=options.max_iterations,
    )

    logger = OptimizationProgressLogger(cpd_als, stopping_criteria=criteria)
    ChosenPrinter = ProgressPrinter if options.display > 0 else VoidPrinter
    printer = ChosenPrinter(default_printer_fields, logger, display=options.display)
    logger.log_init(Ures._data, fval)
    assert isinstance(logger.zp, np.ndarray)
    printer.print_iteration()

    # main iteration loop
    while not logger.check_termination():
        for n in order:
            W = hadamard(UHU, exclude=n)
            K = tl.mtkrprod(T, Ures.factors, n)
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("error", category=nla.LinAlgWarning)
                    Un = tlb.solve_hermitian(W, K.T)
            except nla.LinAlgError:
                warnings.warn(
                    f"the {n}th substep Hessian is singular in iteration "
                    + f"{logger.niterations + 1}",
                    nla.LinAlgWarning,
                )
                Un, *_ = tlb.lstsq(W, K.T)
            except nla.LinAlgWarning:
                warnings.warn(
                    f"the {n}th substep Hessian is nearly singular in iteration "
                    + f"{logger.niterations + 1}",
                    nla.LinAlgWarning,
                )
                Un, *_ = tlb.lstsq(W, K.T)
            Ures.factors[n][:] = Un.T
            UHU[n] = Un[:].conj() @ Un[:].T

        if options.fast_update and np.log10(fval) > np.log10(T2) - 16 + 2.5:
            fval = _objfun_fast_update(T2, UHU[n], W, Un, K)  # type:ignore
        else:
            fval = _objfun(T, Ures)
        logger.log(Ures._data, fval)
        printer.print_iteration()
    printer.print_termination()
    Uopt = tl.PolyadicTensor.from_vector(logger.zp, T.shape, Ures.nterm)
    return Uopt, logger


def _objfun_fast_update(
    T2: float, UHUn: MatrixType, W: MatrixType, Un: MatrixType, K: MatrixType
) -> float:
    """Compute the objective function faster but less accurately.

    Computes the objective function using intermediate results of the last ALS
    iteration.

    Parameters
    ----------
    T2 : float
        Squared Frobenius norm of the tensor `T`.
    UHUn : MatrixType
        Gramian of the factor matrix that was last updated.
    W : MatrixType
        Hadamard product of the gramians of each factor matrix besides the one that was
        last updated.
    Un : MatrixType
        Factor matrix that was last updated.
    K : MatrixType
        Last computed matricized tensor times Khatri-Rao product.

    Returns
    -------
    float
        Objective function value.
    """
    return np.abs(0.5 * (T2 + np.sum(W * UHUn)) - np.sum(K * Un.conj().T).real)


def _objfun(T: TensorType, U: PolyadicTensor) -> float:
    """Compute the objective function for the CPD."""
    return 0.5 * tl.frob(tl.residual(U, T), squared=True)


def _logger_callback(
    z: VectorType,
    kernel: PolyadicKernel,
    logger: OptimizationProgressLogger,
    printer: ProgressPrinter,
):
    """Store intermediate results and check for stopping criteria.

    Parameters
    ----------
    z : VectorType
        Current iterate.
    kernel : PolyadicKernel
        Kernel used in the optimization algorithm.
    logger : OptimizationProgressLogger
        Object to store intermediate iterates and stopping criteria in.
    printer : ProgressPrinter
        Printer for printing intermediate iterates.
    """
    logger.log(z, kernel.objfun_serialized(z))
    printer.print_iteration()
    logger.check_termination()


@dataclass
class CPDMinfOptions(Options):
    """Options for :func:`cpd_minf`.

    See Also
    --------
    cpd_minf
    """

    method: MinfOptimizationMethod | str = "l-bfgs-b"
    """Name of the optimization method to use.
    
    Currently, the following method from :mod:`scipy.optimize` are supported: 
    ``"bfgs"``, ``"cg"``, and ``"l-bfgs-b"``.
    """

    memory_limit: NonnegativeInt = 30
    """Maximum number of updates used to construct the Hessian approximation.
    
    The limit is imposed if L-BFGS-B is the chosen `method`. This value is automatically
    upper bounded by the number variables (``Tinit._data.size``).
    """

    max_iterations: NonnegativeInt = 500
    """Maximum number of iterations."""

    tol_relfval: NonnegativeFloat = 1e-12
    """Tolerance for relative change in objective function value."""

    tol_relstep: NonnegativeFloat = 1e-8
    """Tolerance for step size relative to the norm of the current iterate."""

    tol_absfval: NonnegativeFloat = 0.0
    """Tolerance for absolute change in objective function value."""

    solver_options: dict[str, Any] = field(default_factory=dict)
    """Options to the optimization algorithm."""

    display: NonnegativeInt = 10
    """Print the progress after every `display` iterations. 
    
    If set to 0, the printing is completely suppressed."""


def cpd_minf(
    T: TensorType, Tinit: PolyadicTensor, options: Options | None = None
) -> tuple[PolyadicTensor, OptimizationProgressLogger]:
    """Compute the canonical polyadic decomposition using nonlinear optimization.

    Approximates a given tensor `T` by a polyadic tensor using unconstrained nonlinear
    optimization. The following objective function in ``U`` is used::

        0.5 * tl.frob(numpy.array(U) - T) ** 2

    Parameters
    ----------
    T : TensorType
        Tensor to be approximated.
    Tinit : PolyadicTensor
        Starting point for the algorithm.
    options : CPDMinfOptions, default = CPDMinfOptions()
        Options to change settings of the minf algorithm.

    Returns
    -------
    Uopt : PolyadicTensor
        Resulting polyadic decomposition.
    logger : OptimizationProgressLogger
        Log containing optimization progress information and stopping criteria.

    See Also
    --------
    cpd_als, cpd_nls

    Notes
    -----
    See [SVD2012]_ and [SVD2013]_ for more details.
    """
    # determine solver specific options
    options = CPDMinfOptions.from_options(options)
    methods: Sequence[str] = ["bfgs", "cg", "l-bfgs-b"]
    method = options.method.lower()
    if method not in methods:
        warnings.warn(
            f"the method name is {method} while expected one of {methods}", UserWarning
        )

    # Set default options such that pyTensorlab controls stopping criteria.
    solver_options = default_minimize_solver_options.get(method, {})
    if method == "l-bfgs-b":
        # Set memory limit for the l-bfgs-b algorithm
        solver_options["maxcor"] = min(Tinit._data.size, options.memory_limit)
    solver_options |= options.solver_options

    # ensure that Tinit is complex if T is complex
    if np.iscomplexobj(T) and not np.iscomplexobj(Tinit):
        Tinit = tl.PolyadicTensor.from_vector(
            Tinit._data.astype(complex), Tinit.shape, Tinit.nterm
        )

    # construct kernel and check for errors
    kernel = PolyadicKernel(T, use_gramian=False, use_preconditioner=False)
    kernel.isvalid(Tinit)

    # initialize OptimizationProgressLogger and set stopping criteria
    criteria = default_stopping_criteria(
        max_iter=options.max_iterations,
        tol_relfval=options.tol_relfval,
        tol_relstep=options.tol_relstep,
        tol_absfval=options.tol_absfval,
    )
    logger = OptimizationProgressLogger(
        cpd_minf, stopping_criteria=criteria, terminate_with_exception=True
    )
    ChosenPrinter = ProgressPrinter if options.display > 0 else VoidPrinter
    printer = ChosenPrinter(default_printer_fields, logger, display=options.display)
    logger.log_init(Tinit._data, kernel.objfun(Tinit))
    assert isinstance(logger.zp, np.ndarray)

    # declare objective function, gradient and callback function
    init = Tinit._data
    if not np.iscomplexobj(Tinit):

        objfun = kernel.objfun_serialized
        jacobian = kernel.gradient_serialized

        def callback(z: VectorType) -> None:
            return _logger_callback(z, kernel, logger, printer)

    else:

        def objfun(z: VectorType) -> float:
            return kernel.objfun_serialized(_mapR2C(z))

        def jacobian(z: VectorType) -> VectorType:
            return _mapC2R(kernel.gradient_serialized(_mapR2C(z)))

        def callback(z: VectorType) -> None:
            return _logger_callback(_mapR2C(z), kernel, logger, printer)

        init = _mapC2R(init)
    # start optimization
    printer.print_iteration()
    try:
        res = minimize(
            objfun,
            init,
            method=method,
            **default_minimize_options,
            jac=jacobian,
            hessp=None,
            callback=callback,
            options=solver_options,
        )
        logger.reason_termination = StoppingCriterionAlgorithm(
            "optimization stopped by solver",
            f"scipy.optimize.minimize returned: {res.message}",
            res,
        )
    except StoppingCriterionReached:
        pass
    printer.print_termination()
    Uopt = tl.PolyadicTensor.from_vector(logger.zp, T.shape, Tinit.nterm)
    return Uopt, logger


NlsOptimizationMethods = (
    Literal["trust-ncg"] | Literal["trust-krylov"] | Literal["trust-ncg"]
)


@dataclass
class CPDNlsOptions(Options):
    """Options for :func:`cpd_nls` and :func:`cpd_nls_scipy`.

    See Also
    --------
    cpd_nls, cpd_nls_scipy
    """

    max_iterations: NonnegativeInt = 200
    """Maximum number of iterations."""

    tol_relfval: NonnegativeFloat = 1e-12
    """Tolerance for relative change in objective function value.
    
    The relative change is computed as the absolute value of the difference between 
    current ``f[k]`` and the previous ``f[k - 1]`` objective function value, divided by 
    the initial objectivefunction value ``f[0]``. Note that because the objective 
    function is a squared norm, `tol_relfval` can be as small as 
    ``numpy.finfo(float).eps ** 2``.
    """

    tol_relstep: NonnegativeFloat = 1e-8
    """Tolerance for step size relative to the norm of the current iterate."""

    tol_absfval: NonnegativeFloat = 0.0
    """Tolerance for absolute change in objective function value."""

    large_scale: bool | None = None
    """Use an iterative instead of a direct internal solver if True.
    
    If True, the step direction is computed using an iterative solver and Gramian times 
    vector products. If False, a direct solver for linear systems is used. If not set 
    (None), the small or large scale version is selected based on the number of 
    variables.
    """

    internal_solver: IterativeSolver = cast(IterativeSolver, cg)
    """Internal iterative solver to use if `large_scale` is True."""

    max_internal_iterations: NonnegativeInt = 15
    """Maximum number of iterations for the internal iterative solver."""

    tol_internal_residual: NonnegativeFloat = 1e-6
    """Tolerance on the residual when computing the step using the internal solver."""

    internal_solver_options: dict[str, Any] = field(default_factory=dict)
    """Options to the optimization algorithm."""

    preconditioner: bool = True
    """The internal solver uses a preconditioner if available.
    
    If True, the solver will use a preconditioner in the iterative solver. This is only 
    useful if `large_scale` is True, otherwise a direct solver is used.

    Notes
    -----
    This option is only supported for :func:`cpd_nls` (:func:`cpd_nls_scipy` ignores 
    this).
    """

    solver_options: dict[str, Any] = field(default_factory=dict)
    """Options for the optimization algorithm.

    Notes
    -----
    These options are only used by :func:`cpd_nls_scipy`. 
    """

    display: NonnegativeInt = 10
    """Print the progress after every `display` iterations. 
    
    If set to 0, the printing is suppressed.
    """


def cpd_nls(
    T: TensorType, Tinit: PolyadicTensor, options: Options | None = None
) -> tuple[PolyadicTensor, OptimizationProgressLogger]:
    """Compute the canonical polyadic decomposition using nonlinear least squares.

    Approximates a given tensor `T` by a polyadic tensor using nonlinear least squares.
    The following objective function in ``U`` is used::

        0.5 * tl.frob(numpy.array(U) - T) ** 2

    This algorithm approximates the Hessian by the Gramian of the Jacobian of the
    residual to obtain a step direction.

    Parameters
    ----------
    T : TensorType
        Tensor to be approximated.
    Tinit : PolyadicTensor
        Starting point for the algorithm.
    options : CPDNlsOptions, default = CPDNlsOptions()
        Options to change settings of the nls algorithm.

    Returns
    -------
    Uopt : PolyadicTensor
        Resulting polyadic decomposition.
    logger : OptimizationProgressLogger
        Log containing optimization progress information and stopping criteria.

    See Also
    --------
    cpd_als, cpd_minf, cpd_nls_scipy, CPDNlsOptions

    Notes
    -----
    See [SVD2012]_ and [SVD2013]_ for more details on the optimization methods.
    """
    options = CPDNlsOptions.from_options(options)
    if options.large_scale is None:
        options.large_scale = Tinit._data.size > 500
    if np.iscomplexobj(T) and not np.iscomplexobj(Tinit):
        data = Tinit._data + np.zeros(Tinit._data.shape) * 1j
        Tinit = PolyadicTensor.from_vector(data, Tinit.shape, Tinit.nterm)
    options.preconditioner = options.preconditioner and options.large_scale

    # Construct kernel and check for errors.
    kernel = PolyadicKernel(
        T, use_gramian=True, use_preconditioner=options.preconditioner
    )
    kernel.isvalid(Tinit)

    log = OptimizationProgressLogger(cpd_nls)
    problem: Problem[PolyadicTensor]
    if options.large_scale:
        PC = kernel.M_blockJacobi if options.preconditioner else None

        problem = NewtonIterativeProblem(
            kernel.objfun,
            kernel.gradient,
            kernel.hessian_vector,
            preconditioner=PC,
            solver=options.internal_solver,
            solver_options=IterativeSolverOptions(
                tolerance=options.tol_internal_residual,
                max_iterations=options.max_internal_iterations,
            ),
        )
        log.add_custom_list_field("matvecs_cg", "nmatvec")
        log.add_custom_list_field("residual_cg", "residual")
    else:
        problem = NewtonDirectProblem(kernel.objfun, kernel.gradient, kernel.hessian)
    problem.serialize = kernel.serialize
    problem.deserialize = kernel.deserialize

    printer: ProgressPrinter
    if options.display == 0:
        printer = VoidPrinter()
    else:
        printer = ProgressPrinter(display=options.display)

    optimization_options = OptimizationOptions.from_options(options)
    return minimize_trust_region(
        problem, Tinit, options=optimization_options, log=log, printer=printer
    )


def cpd_nls_scipy(
    T: TensorType,
    Tinit: PolyadicTensor,
    options: Options | None = None,
    method: NlsOptimizationMethods | str = "trust-ncg",
) -> tuple[PolyadicTensor, OptimizationProgressLogger]:
    """Compute the canonical polyadic decomposition using SciPy's solvers.

    Approximates a given tensor `T` by a polyadic tensor using nonlinear least squares.
    The following objective function in ``U`` is used::

        0.5 * tl.frob(numpy.array(U) - T) ** 2

    This algorithm approximates the Hessian by the Gramian of the Jacobian of the
    residual to obtain a step direction. The standard quasi-Newton methods from SciPy
    can be used. Note that preconditioning is not supported, reducing the efficiency
    significantly compared to :func:`cpd_nls`.

    Parameters
    ----------
    T : TensorType
        Tensor to be approximated.
    Tinit : PolyadicTensor
        Starting point for the algorithm.
    options : CPDNlsOptions, default = CPDNlsOptions()
        Options to change settings of the nls algorithm.
    method : str, default = "trust-ncg"
        Method from :func:`scipy.optimize.minimize` to use.

    Returns
    -------
    Tresult : PolyadicTensor
        Resulting polyadic decomposition.
    info : OptimizationProgressLogger
        Log containing optimization progress information and stopping criteria.

    See Also
    --------
    cpd_nls, cpd_als, cpd_minf

    Notes
    -----
    See [SVD2012]_ and [SVD2013]_ for more details on the optimization methods.
    """
    # Check and determine solver specific options.
    options = CPDNlsOptions.from_options(options)
    methods: Sequence[str] = [
        "newton-cg",
        "trust-krylov",
        "trust-ncg",
    ]
    method = method.lower()
    if method not in methods:
        warnings.warn(
            f"the method name is {method} while expected one of {methods}", UserWarning
        )

    # Set default options such that pyTensorlab controls stopping criteria.
    solver_options = (
        default_minimize_solver_options.get(method, {}) | options.solver_options
    )

    large_scale = (
        Tinit._data.size >= 200 if options.large_scale is None else options.large_scale
    )

    # ensure that Tinit is complex if T is complex
    if np.iscomplexobj(T) and not np.iscomplexobj(Tinit):
        Tinit = tl.PolyadicTensor.from_vector(
            Tinit._data.astype(complex), Tinit.shape, Tinit.nterm
        )

    # Construct kernel and check for errors.
    kernel = PolyadicKernel(T, use_gramian=True, use_preconditioner=False)
    kernel.isvalid(Tinit)

    # Initialize OptimizationProgressLogger and set stopping criteria.
    criteria = default_stopping_criteria(
        max_iter=options.max_iterations,
        tol_relfval=options.tol_relfval,
        tol_relstep=options.tol_relstep,
        tol_absfval=options.tol_absfval,
    )
    logger = OptimizationProgressLogger(
        cpd_nls, stopping_criteria=criteria, terminate_with_exception=True
    )
    ChosenPrinter = ProgressPrinter if options.display > 0 else VoidPrinter
    printer = ChosenPrinter(default_printer_fields, logger, display=options.display)
    logger.log_init(Tinit._data, kernel.objfun(Tinit))
    assert isinstance(logger.zp, np.ndarray)
    printer.print_iteration()

    # Construct optimization routine: objective, gradient, hessian, and callback
    objfun = kernel.objfun_serialized
    jacobian = kernel.gradient_serialized

    init = Tinit._data

    if not np.iscomplexobj(Tinit):
        hessp = kernel.hessian_vector_serialized if large_scale else None
        hess = kernel.hessian_serialized if not large_scale else None

        def callback(z: VectorType) -> None:
            return _logger_callback(z, kernel, logger, printer)

    else:

        def objfun(z: VectorType) -> float:
            return kernel.objfun_serialized(_mapR2C(z))

        def jacobian(z: VectorType) -> VectorType:
            return _mapC2R(kernel.gradient_serialized(_mapR2C(z)))

        def callback(z: VectorType) -> None:
            return _logger_callback(_mapR2C(z), kernel, logger, printer)

        def hessp_real(z: VectorType, x: VectorType) -> VectorType:
            return _mapC2R(kernel.hessian_vector_serialized(_mapR2C(z), _mapR2C(x)))

        def hess_real(z: VectorType) -> MatrixType:
            return _mapC2Rmatrix(kernel.hessian_serialized(_mapR2C(z)))

        init = _mapC2R(init)

        hessp = hessp_real if large_scale else None
        hess = hess_real if not large_scale else None

    # run optimization
    try:
        res = minimize(
            objfun,
            init,
            method=method,
            **default_minimize_options,
            jac=jacobian,
            hess=hess,
            hessp=hessp,
            callback=callback,
            options=solver_options,
        )
        logger.reason_termination = StoppingCriterionAlgorithm(
            "optimization stopped by solver",
            f"scipy.optimize.minimize returned: {res.message}",
            res,
        )
    except StoppingCriterionReached:
        pass

    printer.print_termination()
    Tresult = tl.PolyadicTensor.from_vector(logger.zp, T.shape, Tinit.nterm)
    return Tresult, logger


# set options defaults
Options.set_defaults(cpd_als, CPDAlsOptions)
Options.set_defaults(cpd_minf, CPDMinfOptions)
Options.set_defaults(cpd_nls, CPDNlsOptions)
Options.set_defaults(cpd_nls_scipy, CPDNlsOptions)

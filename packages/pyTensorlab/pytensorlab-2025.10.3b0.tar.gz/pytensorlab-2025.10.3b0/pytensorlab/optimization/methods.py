r"""Methods for solving optimization problems.

This module defines ways of specifying unconstrained optimization problems

.. math::

    \underset{\vec{z}}{\text{min}}\ f(\vec{z})

of a scalar, real-valued objective function :math:`f` in real or complex variables
:math:`\vec{z}`, and nonlinear least squares problems, in which

.. math::

    f(\vec{z}) = \frac12 \| \vec{F}(\vec{z}) \|^2_{\F}.

Optimization with complex variables $\vec{z} \in \C^N$ is fully supported for most
methods, but requires specialized implementations if the Jacobian or a Hessian
approximation is required and the method is not analytic/holomorphic, i.e., depends on
the conjugated variables $\conj{\vec{z}}$.

Several methods are available to solve the optimization problem, each requiring specific
information about the problem such as a way to evaluate the objective function $f$, its
gradient and/or its Hessian (or an approximation thereof). The method is selected by
creating an instance of a specific :class:`.Problem` subclass. These subclasses are
named according to the method name, implementation details and function type.

Classes
-------
NewtonDirectProblem
    Newton-type method using a direct solver to compute the step. This includes the
    Gauss--Newton, damped Newton and Levenberg--Marquardt methods as approximations of
    the Hessian can be used, e.g., the Gramian of the Jacobian.
NewtonDirectNonHolomorphicProblem
    Newton-type method for non-holomorphic problems using a direct solver to compute the
    step.
NewtonIterativeProblem
    Newton-type method using an iterative solver relying on Hessian times vector
    products to compute the step.
NewtonIterativeNonHolomorphicProblem
    Newton-type method for non-holomorphic problems using an iterative solver relying on
    Hessian times vector products to compute the step.
GaussNewtonDirectProblem
    Gauss--Newton type method using a direct solver to compute the step based on the
    Jacobian and the residual. :class:`.NewtonDirectProblem` is recommended when using
    the Gramian of the Jacobian and the gradient instead.
GaussNewtonDirectNonHolomorphicProblem
    Gauss--Newton type method for non-holomorphic problems using a direct solver to
    compute the step based on the Jacobian and the residual.
    :class:`.NewtonDirectNonHolomorphicProblem` is recommended when using the Gramian
    of the Jacobian and the gradient instead.
GaussNewtonIterativeProblem
    Gauss--Newton type method using an iterative solver to compute the step based on the
    Jacobian and the residual with only Jacobian times vector
    products. :class:`.NewtonIterativeProblem` is recommended when using the Gramian of
    the Jacobian and the gradient instead.
GaussNewtonIterativeNonHolomorphicProblem
    Gauss--Newton type method for non-holomorphic problems using an iterative solver to
    compute the step based on the Jacobian and the residual with only Jacobian times
    vector products. :class:`.NewtonIterativeNonHolomorphicProblem` is recommended when
    using the Gramian of the Jacobian and the gradient instead.
LBFGSProblem
    Limited-memory BFGS type method using only the gradient.

Examples
--------
Two running examples are used. The first minimization problem computes the best rank-1
approximation of a matrix in least squares sense:

.. math::

    \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
    \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F}.

To solve this problem for real variables, any of the methods can be used. In general,
only the methods labeled ``NonHolomorphic`` can be used to solve this problem for
complex variables, one exception being the Gauss--Newton methods.

>>> import pytensorlab as tl
>>> import numpy as np
>>> M = np.array(tl.PolyadicTensor.random((5, 6), 1))
>>> z_init = tl.PolyadicTensor.random((5, 6), 1)
>>> a, b = z_init.factors  # not needed, shows link to original variables
>>> def objective(z):
...     return 0.5 * tl.frob(tl.residual(z, M)) ** 2
...
>>> def gradient(z):
...     ...  # implementation omitted
...
>>> def gramian(z):
...     ...  # implementation omitted
...
>>> problem = NewtonDirectProblem(objective, gradient, gramian)
>>> problem.serialize = lambda z: z._data
>>> problem.deserialize = lambda data: tl.PolyadicTensor.from_vector(data, (5, 6), 1)
>>> z_res, info = tl.minimize_trust_region(problem, z_init)

The second minimization problem computes the best Hermitian rank-1 approximation of a
complex Hermitian matrix in least squares sense:

.. math::

    \underset{\vec{a}}{\text{minimize}}\ \frac12
     \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F},

In this example, the residual $F(\vec{a}, \conj{\vec{a}}) = \vec{a} \conj{\vec{a}}^{\T}
- \mat{M}$ depends on both $\vec{a}$ and $\conj{\vec{a}}$, i.e., the residual is not
holomorphic/analytic. The methods labeled ``NonHolomorphic`` are required to solve this
problem.
"""

import inspect
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, cast

import numpy as np
from scipy.sparse.linalg import cg, lsqr

import pytensorlab.backends.numpy as tlb
from pytensorlab.optimization.problem import CurvatureProblem, PointType
from pytensorlab.optimization.protocols import (
    ComplexHessianFcn,
    ComplexHessianVectorProductFcn,
    ComplexJacobianFcn,
    ComplexJacobianVectorProductFcn,
    CustomLinearOperator,
    GradientFcn,
    HessianFcn,
    HessianVectorProductFcn,
    IterativeSolver,
    IterativeSolverOptions,
    IterativeSolverQR,
    JacobianFcn,
    JacobianVectorProductFcn,
    ObjectiveFcn,
    PreconditionerFcn,
    ResidualFcn,
)
from pytensorlab.typing import MatrixType, VectorType
from pytensorlab.typing.core import NumberType
from pytensorlab.typing.validators import PositiveInt


@dataclass
class ComplexCurvatureException(Exception):
    """Exception when a complex curvature is encountered."""

    curvature: complex
    """Curvature at the optimization point which caused the exception."""

    def __str__(self) -> str:
        return f"curvature should be real: got {self.curvature:.3e}"


class CallOrderException(Exception):
    """Exception indicating two methods are called in the incorrect order."""

    pass


def _ensure_real(a: NumberType) -> float:
    """Ensure a number is real.

    If `a` is a complex number, but has a (numerically) zero imaginary part, the
    imaginary part is dropped.
    """
    if not np.iscomplexobj(a):
        return cast(float, a)
    if np.abs(a.imag) > np.abs(a) * np.finfo(float).eps * 10:
        raise ValueError(f"a should be real: got {a:.3e}")
    return np.real(a)


def mapC2R(a: VectorType, flip: bool = False) -> VectorType:
    """Map a vector of complex numbers to a vector of real numbers.

    Parameters
    ----------
    a : VectorType
        Vector of complex numbers.
    flip : bool, default = False
        Flip the order of the real and the imaginary part of `a`.

    Returns
    -------
    b : VectorType
        Real vector with ``b[: len(a)] = a.real`` and ``b[len(a) :] = a.imag``. If
        `flip` is True, the real and imaginary parts are swapped.

    See Also
    --------
    mapR2C
    """
    if flip:
        return np.concatenate((a.imag, a.real))
    return np.concatenate((a.real, a.imag))


def mapR2C(a: VectorType) -> VectorType:
    """Map a vector of real numbers to a vector of complex numbers.

    Parameters
    ----------
    a : VectorType
        Vector where the top half corresponds the real part and the bottom half
        corresponds to the imaginary part. The size of `a` should be even.

    Returns
    -------
    b : VectorType
        Complex vector with ``b.real = a[: N]`` and ``b.imag = a[N :]`` in which
        ``N = len(a) // 2``.

    See Also
    --------
    mapC2R
    """
    return a[: len(a) // 2] + a[len(a) // 2 :] * 1j


@dataclass
class ResidualExtractor:
    """Auxiliary class to extract the residual norm from iterative methods.

    As some iterative solvers in :mod:`scipy.sparse.linalg` to not expose the residual,
    a hack is used to extract it from its stack frame via the `callback` option in e.g.,
    :func:`scipy.sparse.linalg.cg` and :func:`scipy.sparse.linalg.gmres`. The
    `create_callback` method creates an options dictionary that can be supplied to these
    methods.
    """

    residual_norm: float | None = None
    """Extracted norm of the residual.

    None if not set or if the callback raises an exception.
    """

    enabled: bool | None = None
    """Enable the extractor.

    If False, `create_callback` returns an empty dict, effectively disabling the
    callback.
    """

    add_callback_type: bool | None = None
    """Add callback_type option, which is needed for some solvers.

    If None, the option will be added if the solver is not
    :func:`scipy.sparse.linalg.cg`.
    """

    def callback(self, x: VectorType) -> None:
        """Extract the residual norm from an iterative solver.

        Parameters
        ----------
        x : VectorType
            Current iterate. Ignored.
        """
        try:
            frame = inspect.currentframe()
            assert frame is not None
            frame = frame.f_back
            assert frame is not None
            residual = frame.f_locals["r"]
            self.residual_norm = tlb.norm(residual)
        except (KeyError, AssertionError):
            pass

    def create_callback(self, solver: IterativeSolver) -> Mapping[str, Any]:
        """Create callback options for scipy's iterative solvers.

        The created callback uses the inspect module to get the stack frame from the
        iterative solver and extracts the residual vector ``r``.

        Parameters
        ----------
        solver : IterativeSolver
            The solver for which the callback is created.

        Returns
        -------
        Mapping[str, Any]
            Dictionary with a ``callback`` function, and if required for the given
            `solver` a ``callback_type`` key.

        See Also
        --------
        scipy.sparse.linalg.cg, scipy.sparse.linalg.gmres

        Notes
        -----
        This method relies on implementation details from scipy. As these might change,
        the callback might become useless. The callback is designed to disable itself
        when errors occur.
        """
        if self.enabled is None:
            self.enabled = "callback" in inspect.signature(solver).parameters
        if not self.enabled:
            return {}
        options: dict[str, Any] = {"callback": self.callback}
        if self.add_callback_type is None:
            self.add_callback_type = (
                "callback_type" in inspect.signature(solver).parameters
            )
        if self.add_callback_type:
            options |= {"callback_type": "x"}

        return options


@dataclass
class NewtonDirectProblem(CurvatureProblem[PointType]):
    r"""Newton-type optimization problem using a direct solver.

    This problem definition can be used to solve an unconstrained optimization problem
    in the variables ``z``::

        minimize f(z)

    In general, the variables should be real-valued, but in some cases complex-valued
    variables can used. The step is computed in least squares sense using the Hessian or
    an approximation thereof, and the gradient. A direct solver is used.

    See Also
    --------
    NewtonDirectNonHolomorphicProblem
        Newton-type optimization problem for complex variables.
    NewtonIterativeProblem
        Newton-type optimization problem using an iterative solver relying only on
        Hessian times vector products.

    Examples
    --------
    To compute the best rank-1 approximation of a matrix in least squares sense, the
    following optimization problem can be formulated:

    .. math::
        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F}.

    To solve this problem with a Newton-type method, the problem is defined as follows:

    .. code-block:: python

        >>> import pytensorlab as tl
        >>> import numpy as np
        >>> tl.random.set_rng(31415)  # fix random number seed
        >>> M = np.array(tl.PolyadicTensor.random((5, 6), 1))
        >>> z_init = tl.PolyadicTensor.random((5, 6), 1)
        >>> a, b = z_init.factors  # not needed, shows link to original variables
        >>> def objective(z):
        ...     global M
        ...     return 0.5 * tl.frob(tl.residual(z, M)) ** 2
        ...
        >>> def gradient(z):
        ...     global M
        ...     res = np.array(z) - M
        ...     ga = res @ z.factors[1].conj()
        ...     gb = res.T @ z.factors[0].conj()
        ...     return tl.PolyadicTensor((ga, gb))
        ...
        >>> def hessian(z):
        ...     global M
        ...     m, n = z.shape
        ...     a, b = z.factors
        ...     res = np.array(z) - M
        ...     H11 = np.vdot(b, b) * np.eye(m)
        ...     H12 = np.outer(a, b) + res
        ...     H22 = np.vdot(a, a) * np.eye(n)
        ...     return np.block([[H11, H12], [H12.T, H22]])
        ...
        >>> problem = NewtonDirectProblem(objective, gradient, hessian)
        >>> problem.serialize = lambda z: z._data
        >>> problem.deserialize = lambda d: tl.PolyadicTensor.from_vector(d, (5, 6), 1)
        >>> z_res, info = tl.minimize_trust_region(problem, z_init)
            iter         fval     rel fval     rel step         rho        delta
         max=200               tol=1.0e-12  tol=1.0e-06

               0    1.304e+00
               1    7.125e-01    4.535e-01    3.000e-01    1.008025    1.121e+00
               2    3.507e-01    2.775e-01    5.915e-01    0.388622    1.016e+00
               3    1.446e-02    2.579e-01    1.437e-01    1.117038    1.016e+00
               4    6.405e-05    1.104e-02    4.578e-02    1.041762    1.016e+00
               5    2.409e-09    4.912e-05    3.954e-03    1.003859    1.016e+00
               6    1.050e-17    1.848e-09    3.728e-05    1.000037    1.016e+00
               7    2.168e-31    8.053e-18    1.613e-08    1.000000    1.016e+00

        algorithm minimize_trust_region has stopped (see reason_termination):
            relative function value is smaller than tolerance: 8.052852e-18 <= 1e-12

        data fields:
            niterations : 7
            fval : [..., 2.1677e-31]
            relative_fval : [..., 8.0529e-18]
            relative_step : [..., 1.6128e-08]
            normgrad : []
            rho : [..., 1]
            delta : [..., 1.0157]

        other fields:
            stopping_criteria, zp, algorithm, reason_termination

    The Gramian of the Jacobian can also be used to have the Gauss--Newton method. In
    this case, both real and complex variables can be used.

    >>> def gramian(z):
    ...     m, n = z.shape
    ...     a, b = z.factors
    ...     G11 = np.vdot(b, b) * np.eye(m)
    ...     G12 = np.outer(a, b.conj())
    ...     G22 = np.vdot(a, a) * np.eye(n)
    ...     return np.block([[G11, G12], [G12.conj().T, G22]])
    ...
    >>> problem = NewtonDirectProblem(objective, gradient, gramian)
    >>> problem.serialize = lambda z: z._data
    >>> problem.deserialize = lambda d: tl.PolyadicTensor.from_vector(d, (5, 6), 1)
    """

    objective: ObjectiveFcn[PointType]
    """Function that evaluates the objective function in a given point."""

    gradient: GradientFcn[PointType]
    """Function that evaluates the gradient in a given point."""

    hessian: HessianFcn[PointType]
    """Function that evaluates (an approximation of) the Hessian in a given point."""

    def compute_objective(self, point: VectorType) -> float:
        self._fval = cast(float, self.objective(self._deserialize(point)))
        return self._fval

    def compute_step(self, point: VectorType) -> tuple[VectorType, Mapping[str, Any]]:
        z = self._deserialize(point)
        self._gradient = self._serialize(self.gradient(z))
        self._gradient_norm = tlb.norm(self._gradient)

        hessian = self.hessian(z)
        curvature = cast(float, np.vdot(self._gradient, hessian @ self._gradient))
        try:
            self._curvature = _ensure_real(curvature)
        except ValueError:
            raise ComplexCurvatureException(curvature)
        self._step, *_ = tlb.lstsq(hessian, -self._gradient, rcond=None)
        return self._step, {}


@dataclass
class NewtonIterativeProblem(CurvatureProblem[PointType]):
    r"""Newton-type optimization problem using an iterative solver.

    This problem definition can be used to solve an unconstrained optimization problem
    in the variables ``z``::

        minimize f(z)

    In general, the variables are real-valued, but in some cases the complex-valued
    variables can used. The step is computed in least squares sense using the Hessian or
    an approximation thereof, and the gradient. An iterative solver using only Hessian
    times vector products is used.

    See Also
    --------
    NewtonIterativeNonHolomorphicProblem
        Newton-type optimization problem for complex variables.
    NewtonDirectProblem
        Newton-type optimization problem using a direct solver.

    Examples
    --------
    To compute the best rank-1 approximation of a matrix in least squares sense, the
    following optimization problem can be formulated:

    .. math::
        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F}.

    To solve this problem with a Newton-type method, the problem is defined as follows:

    .. code-block:: python

        >>> import pytensorlab as tl
        >>> import numpy as np
        >>> tl.random.set_rng(31415)  # fix random number seed
        >>> M = np.array(tl.PolyadicTensor.random((5, 6), 1))
        >>> z_init = tl.PolyadicTensor.random((5, 6), 1)
        >>> a, b = z_init.factors  # not needed, shows link to original variables
        >>> def objective(z):
        ...     global M
        ...     return 0.5 * tl.frob(tl.residual(z, M)) ** 2
        ...
        >>> def gradient(z):
        ...     global M
        ...     res = np.array(z) - M
        ...     ga = res @ z.factors[1].conj()
        ...     gb = res.T @ z.factors[0].conj()
        ...     return tl.PolyadicTensor((ga, gb))
        ...
        >>> def hessian_vector(z, x):
        ...     global M
        ...     a, b = z.factors
        ...     xa, xb = x.factors
        ...     res = np.array(z) - M
        ...     ya = xa * np.vdot(b, b) + a * np.vdot(b, xb) + res @ xb
        ...     yb = xb * np.vdot(a, a) + b * np.vdot(a, xa) + res.T @ xa
        ...     return tl.PolyadicTensor((ya, yb))
        ...
        >>> problem = NewtonIterativeProblem(objective, gradient, hessian_vector)
        >>> problem.serialize = lambda z: z._data
        >>> problem.deserialize = lambda d: tl.PolyadicTensor.from_vector(d, (5, 6), 1)
        >>> z_res, info = tl.minimize_trust_region(problem, z_init)
            iter         fval     rel fval     rel step         rho        delta
         max=200               tol=1.0e-12  tol=1.0e-06

               0    1.304e+00
               1    7.125e-01    4.535e-01    3.000e-01    1.008025    1.121e+00
               2    3.507e-01    2.775e-01    5.915e-01    0.388622    1.016e+00
               3    1.446e-02    2.579e-01    1.437e-01    1.117038    1.016e+00
               4    6.405e-05    1.104e-02    4.578e-02    1.041762    1.016e+00
               5    2.409e-09    4.912e-05    3.954e-03    1.003859    1.016e+00
               6    1.050e-17    1.848e-09    3.728e-05    1.000037    1.016e+00
               7    1.168e-32    8.053e-18    2.028e-09    1.000000    1.016e+00

        algorithm minimize_trust_region has stopped (see reason_termination):
            relative function value is smaller than tolerance: 8.052851e-18 <= 1e-12

        data fields:
            niterations : 7
            fval : [..., 1.1677e-32]
            relative_fval : [..., 8.0529e-18]
            relative_step : [..., 2.0280e-09]
            normgrad : []
            rho : [..., 1]
            delta : [..., 1.0157]

        other fields:
            stopping_criteria, zp, algorithm, reason_termination

    The Gramian of the Jacobian can also be used to have the Gauss--Newton method. In
    this case, both real and complex variables can be used. To speed up convergence of
    the iterative solver, a preconditioner can be used.

    .. code-block:: python

        >>> def gramian_vector(z, x):
        ...     a, b = z.factors
        ...     xa, xb = x.factors
        ...     ya = xa * np.vdot(b, b) + a * np.vdot(b, xb)
        ...     yb = xb * np.vdot(a, a) + b * np.vdot(a, xa)
        ...     return tl.PolyadicTensor((ya, yb))
        ...
        >>> def preconditioner(z, r):
        ...     a, b = z.factors
        ...     ra, rb = r.factors
        ...     return tl.PolyadicTensor((ra / np.vdot(b, b), rb / np.vdot(a, a)))
        ...
        >>> problem = NewtonIterativeProblem(
        ...     objective, gradient, gramian_vector, preconditioner
        ... )
        >>> problem.serialize = lambda z: z._data
        >>> problem.deserialize = lambda d: tl.PolyadicTensor.from_vector(d, (5, 6), 1)
        >>> z_res, info = tl.minimize_trust_region(problem, z_init)
            iter         fval     rel fval     rel step         rho        delta
         max=200               tol=1.0e-12  tol=1.0e-06

               0    1.304e+00
               1    7.125e-01    4.535e-01    3.000e-01    1.138492    1.121e+00
               2    3.153e-02    5.223e-01    5.915e-01    1.075882    2.243e+00
               3    5.980e-05    2.414e-02    6.938e-02    0.998336    2.243e+00
               4    1.267e-10    4.587e-05    4.901e-03    0.999998    2.243e+00
               5    2.054e-22    9.717e-11    7.232e-06    1.000000    2.243e+00
               6    2.025e-32    1.576e-22    9.210e-12    1.000000    2.243e+00

        algorithm minimize_trust_region has stopped (see reason_termination):
            relative function value is smaller than tolerance: 1.575617e-22 <= 1e-12

        data fields:
            niterations : 6
            fval : [..., 2.0253e-32]
            relative_fval : [..., 1.5756e-22]
            relative_step : [..., 9.2105e-12]
            normgrad : []
            rho : [..., 1]
            delta : [..., 2.2425]

        other fields:
            stopping_criteria, zp, algorithm, reason_termination
    """

    objective: ObjectiveFcn[PointType]
    """Function computing the objective function in a given point."""

    gradient: GradientFcn[PointType]
    """Function computing the gradient in a given point."""

    hessian_vector: HessianVectorProductFcn[PointType]
    """Function computing the Hessian times vector product for a given point."""

    preconditioner: PreconditionerFcn[PointType] | None = None
    """Function applying a preconditioner in a iterative solver."""

    solver: IterativeSolver = cast(IterativeSolver, field(default=cg))
    """Iterative solver used to compute the step."""

    solver_options: IterativeSolverOptions = field(
        default_factory=IterativeSolverOptions
    )
    """Options for the iterative solver."""

    _residual_extractor: ResidualExtractor = field(default_factory=ResidualExtractor)
    """Function extracting the residual from the iterative solver if not exposed."""

    def compute_objective(self, point: VectorType) -> float:
        self._fval = cast(float, self.objective(self._deserialize(point)))
        return self._fval

    def compute_step(self, point: VectorType) -> tuple[VectorType, Mapping[str, Any]]:
        z = self._deserialize(point)
        gradient = self.gradient(z)
        self._gradient = self._serialize(gradient)
        self._gradient_norm = tlb.norm(self._gradient)

        hessian_gradient = self._serialize(self.hessian_vector(z, gradient))
        curvature = cast(float, np.vdot(self._gradient, hessian_gradient))
        try:
            curvature = _ensure_real(curvature) if np.isfinite(curvature) else 1.0
        except ValueError:
            raise ComplexCurvatureException(curvature)
        cauchy_point = -self._gradient_norm**2 / curvature * self._gradient
        self._curvature = curvature

        def Ax(x: VectorType) -> VectorType:
            y = self.hessian_vector(z, self._deserialize(x))
            return self._serialize(y)

        def M(b: VectorType) -> VectorType:
            assert self.preconditioner is not None
            return self._serialize(self.preconditioner(z, self._deserialize(b)))

        shape = (point.size, point.size)
        A = CustomLinearOperator(shape, Ax, dtype=point.dtype)
        options: dict[str, Any] = {
            "rtol": self.solver_options.tolerance,
            "maxiter": self.solver_options.max_iterations,
        }
        options |= self.solver_options.other
        options |= self._residual_extractor.create_callback(self.solver)
        if self.preconditioner:
            options["M"] = CustomLinearOperator(shape, M, dtype=point.dtype)

        self._step, _ = self.solver(
            A,
            -self._gradient,
            cauchy_point,
            **options,  # type:ignore
        )

        if self._residual_extractor.residual_norm is None:
            self._residual_extractor.enabled = False
        residual = self._residual_extractor.residual_norm
        residual = None if residual is None else residual / self._gradient_norm
        return self._step, {"nmatvec": A.ncalls, "residual": residual}


@dataclass
class GaussNewtonDirectProblem(CurvatureProblem[PointType]):
    r"""Gauss--Newton-type optimization problem using a direct solver.

    This problem definition can be used to solve an unconstrained nonlinear least
    squares optimization problem in the variables ``z``::

        minimize 0.5 * tl.frob(F(z)) ** 2

    The variables can be complex as long as the residual ``F(z)`` does not depend on
    conjugated variables ``z.conj()``, i.e., ``F(z)`` is holomorphic/analytic. The step
    is computed in least squares sense using the Jacobian and the residual. A direct
    solver is used.

    See Also
    --------
    NewtonDirectProblem
        General Newton-type optimization problem using a direct solver.
    GaussNewtonIterativeProblem
        Gauss--Newton-type optimization problem using an iterative solver relying only
        on Jacobian times vector products.
    GaussNewtonDirectNonHolomorphicProblem
        Gauss--Newton-type optimization problem where the residual is
        non-holomorphic/non-analytic, i.e., depends on the conjugated variables. A
        direct solver is used.

    Examples
    --------
    To compute the best rank-1 approximation of a matrix in least squares sense, the
    following optimization problem can be formulated:

    .. math::
        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F}.

    To solve this problem with a Gauss--Newton-type method, the problem is defined as
    follows:

    .. code-block:: python

        >>> import pytensorlab as tl
        >>> import numpy as np
        >>> tl.random.set_rng(31415)  # fix random number seed
        >>> M = np.array(tl.PolyadicTensor.random((5, 6), 1))
        >>> z_init = tl.PolyadicTensor.random((5, 6), 1)
        >>> a, b = z_init.factors  # not needed, shows link to original variables
        >>> def residual(z):
        ...     global M
        ...     return np.array(z) - M  # note that correct order is model - data
        ...
        >>> def jacobian(z):
        ...     m, n = z.shape
        ...     a, b = z.factors
        ...     return np.hstack((np.kron(np.eye(m), b), np.kron(a, np.eye(n))))
        ...
        >>> problem = GaussNewtonDirectProblem(residual, jacobian)
        >>> problem.serialize = lambda z: z._data
        >>> problem.deserialize = lambda d: tl.PolyadicTensor.from_vector(d, (5, 6), 1)
        >>> z_res, info = tl.minimize_trust_region(problem, z_init)
            iter         fval     rel fval     rel step         rho        delta
         max=200               tol=1.0e-12  tol=1.0e-06

               0    1.304e+00
               1    7.125e-01    4.535e-01    3.000e-01    1.138492    1.121e+00
               2    3.760e-02    5.177e-01    5.915e-01    1.063113    2.243e+00
               3    9.326e-05    2.877e-02    8.348e-02    0.997914    2.243e+00
               4    4.051e-11    7.153e-05    6.222e-03    1.000000    2.243e+00
               5    9.732e-26    3.107e-11    4.138e-06    1.000000    2.243e+00
               6    2.569e-32    7.465e-26    2.028e-13    1.000000    2.243e+00

        algorithm minimize_trust_region has stopped (see reason_termination):
            relative function value is smaller than tolerance: 7.464596e-26 <= 1e-12

        data fields:
            niterations : 6
            fval : [..., 2.5687e-32]
            relative_fval : [..., 7.4646e-26]
            relative_step : [..., 2.0284e-13]
            normgrad : []
            rho : [..., 1]
            delta : [..., 2.2425]

        other fields:
            stopping_criteria, zp, algorithm, reason_termination
    """

    residual: ResidualFcn[PointType]
    """Function computing the residual between model evaluated at point and data.

    This corresponds to the objective function::

        0.5 * tl.frob(residual) ** 2
    """

    jacobian: JacobianFcn[PointType]
    """Function computing the Jacobian of the residual evaluated at point."""

    def compute_objective(self, point: VectorType) -> float:
        self._residual = self.residual(self._deserialize(point)).ravel()
        self._fval = tlb.norm2(self._residual) / 2
        return self._fval

    def compute_step(self, point: VectorType) -> tuple[VectorType, Mapping[str, Any]]:
        J = self.jacobian(self._deserialize(point))
        try:
            self._gradient = J.conj().T @ self._residual
        except AttributeError:
            raise CallOrderException(
                "compute_objective should be called before compute_step to update the "
                "residual for point."
            )
        self._gradient_norm = tlb.norm(self._gradient)

        curvature = J @ self._gradient
        self._curvature = tlb.norm2(curvature)

        if J.shape[0] <= J.shape[1]:
            A = J
            b: VectorType = -self._residual
        else:
            A = J.conj().T @ J
            b = -self._gradient
        self._step, *_ = tlb.lstsq(A, b)
        return self._step, {}


@dataclass
class GaussNewtonIterativeProblem(CurvatureProblem[PointType]):
    r"""Gauss--Newton-type optimization problem using an iterative solver.

    This problem definition can be used to solve an unconstrained nonlinear least
    squares optimization problem in the variables ``z``::

        minimize 0.5 * tl.frob(F(z)) ** 2

    The variables can be complex as long as the residual ``F(z)`` does not depend on
    conjugated variables ``z.conj()``, i.e., ``F(z)`` is holomorphic/analytic. The step
    is computed in least squares sense using the Jacobian and the residual. An iterative
    solver using only Jacobian times vector products is used.

    See Also
    --------
    NewtonIterativeProblem
        General Newton-type optimization problem using an iterative solver.
    GaussNewtonDirectProblem
        Gauss--Newton-type optimization problem using a direct solver.
    GaussNewtonIterativeNonHolomorphicProblem
        Gauss--Newton-type optimization problem where the residual is
        non-holomorphic/non-analytic, i.e., depends on the conjugated variables. An
        iterative solver is used.

    Examples
    --------
    To compute the best rank-1 approximation of a matrix in least squares sense, the
    following optimization problem can be formulated:

    .. math::
        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F}.

    To solve this problem with a Gauss--Newton-type method, the problem is defined as
    follows:

    .. code-block:: python

        >>> import pytensorlab as tl
        >>> import numpy as np
        >>> tl.random.set_rng(31415)  # fix random number seed
        >>> M = np.array(tl.PolyadicTensor.random((5, 6), 1))
        >>> z_init = tl.PolyadicTensor.random((5, 6), 1)
        >>> a, b = z_init.factors  # not needed, shows link to original variables
        >>> def residual(z):
        ...     global M
        ...     return np.array(z) - M  # note that correct order is model - data
        ...
        >>> def jacobian_vector(z, x, transpose):
        ...     a, b = z.factors
        ...     if transpose:
        ...         x = x.reshape(z.shape)
        ...         return tl.PolyadicTensor((x @ b, x.T @ a))
        ...     xa, xb = x.factors
        ...     return np.kron(xa, b) + np.kron(a, xb)
        ...
        >>> problem = GaussNewtonIterativeProblem(residual, jacobian_vector)
        >>> problem.serialize = lambda z: z._data
        >>> problem.deserialize = lambda d: tl.PolyadicTensor.from_vector(d, (5, 6), 1)
        >>> z_res, info = tl.minimize_trust_region(problem, z_init)
            iter         fval     rel fval     rel step         rho        delta
         max=200               tol=1.0e-12  tol=1.0e-06

               0    1.304e+00
               1    7.125e-01    4.535e-01    3.000e-01    1.138492    1.121e+00
               2    3.760e-02    5.177e-01    5.915e-01    1.063113    2.243e+00
               3    9.326e-05    2.877e-02    8.348e-02    0.997914    2.243e+00
               4    4.051e-11    7.153e-05    6.222e-03    1.000000    2.243e+00
               5    9.732e-26    3.107e-11    4.138e-06    1.000000    2.243e+00
               6    2.554e-32    7.464e-26    2.028e-13    1.000000    2.243e+00

        algorithm minimize_trust_region has stopped (see reason_termination):
            relative function value is smaller than tolerance: 7.464232e-26 <= 1e-12

        data fields:
            niterations : 6
            fval : [..., 2.5543e-32]
            relative_fval : [..., 7.4642e-26]
            relative_step : [..., 2.0284e-13]
            normgrad : []
            rho : [..., 1]
            delta : [..., 2.2425]

        other fields:
            stopping_criteria, zp, algorithm, reason_termination
    """

    residual: ResidualFcn[PointType]
    """Function computing the residual between model, evaluated at point, and data.

    This corresponds to the objective function::

        0.5 * tl.frob(residual) ** 2
    """

    jacobian_vector: JacobianVectorProductFcn[PointType]
    """Function computing the Jacobian times vector product evaluated at point."""

    solver: IterativeSolverQR = field(default=lsqr)
    """Iterative solver used to compute the step."""

    solver_options: IterativeSolverOptions = field(
        default_factory=IterativeSolverOptions
    )
    """Options for the iterative solver."""

    def compute_objective(self, point: VectorType) -> float:
        self._residual = self.residual(self._deserialize(point)).ravel()
        self._fval = tlb.norm2(self._residual) / 2
        return self._fval

    def compute_step(
        self, point: VectorType, /
    ) -> tuple[VectorType, Mapping[str, Any]]:
        z = self._deserialize(point)
        try:
            gradient = self.jacobian_vector(z, self._residual, transpose=True)
        except AttributeError:
            raise CallOrderException(
                "compute_objective should be called before compute_step to update the "
                "residual for point."
            )
        self._gradient = self._serialize(gradient)
        self._gradient_norm = tlb.norm(self._gradient)

        curvature = self.jacobian_vector(z, gradient, transpose=False)
        self._curvature = tlb.norm2(curvature)
        if self._curvature != 0:
            cauchy_point = -self._gradient_norm**2 / self._curvature * self._gradient
        else:
            cauchy_point = -1.0 * self._gradient

        def Ax(x):
            return self.jacobian_vector(z, self._deserialize(x), transpose=False)

        def ATx(x):
            return self._serialize(self.jacobian_vector(z, x, transpose=True))

        A = CustomLinearOperator(
            (self._residual.size, point.size), Ax, rmatvec=ATx, dtype=point.dtype
        )
        self._step, *info = self.solver(
            A,
            -self._residual,
            x0=-cauchy_point,
            iter_lim=self.solver_options.max_iterations,
            atol=self.solver_options.tolerance,
            btol=self.solver_options.tolerance,
        )
        residual = info[2] / self._gradient_norm if len(info) >= 3 else None
        return self._step, {"nmatvec": A.ncalls, "residual_norm": residual}


@dataclass
class GaussNewtonDirectNonHolomorphicProblem(CurvatureProblem[PointType]):
    r"""Complex Gauss--Newton-type optimization problem using a direct solver.

    This problem definition can be used to solve an unconstrained nonlinear least
    squares optimization problem in the variables ``z``::

        minimize 0.5 * tl.frob(F(z)) ** 2

    The residual ``F(z)`` can be non-holomorphic/non-analytic, i.e., depend on both the
    variables and the conjugated variables ``z.conj()``. The step is computed in least
    squares sense using the Jacobian and the residual. A direct solver is used.

    See Also
    --------
    NewtonDirectNonHolomorphicProblem
        General complex Newton-type optimization problem using a direct solver.
    GaussNewtonIterativeNonHolomorphicProblem
        Complex Gauss--Newton-type optimization problem using an iterative solver
        relying only on Jacobian times vector products.
    GaussNewtonDirectProblem
        Gauss--Newton-type optimization problem where the residual is
        holomorphic/analytic, i.e., does not depend on the conjugated variables. A
        direct solver is used.

    Examples
    --------
    To compute the best Hermitian rank-1 approximation of a Hermitian matrix in least
    squares sense, the following optimization problem can be formulated:

    .. math::
        \underset{\vec{a}}{\text{minimize}}\ \frac12
        \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F}.

    To solve this problem with a Gauss--Newton-type method, the problem is defined as
    follows:

    .. code-block:: python

        >>> import pytensorlab as tl
        >>> import numpy as np
        >>> tl.random.set_rng(31415)  # fix random number seed
        >>> a = tl.get_rng().random((5,)) + 1j * tl.get_rng().random((5,))
        >>> M = np.outer(a, a.conj())
        >>> a_init = tl.get_rng().random((5,)) + 1j * tl.get_rng().random((5,))
        >>> def residual(a):
        ...     global M
        ...     return np.outer(a, a.conj()) - M  # correct order is model - data
        ...
        >>> def jacobian(a):
        ...     Jz = np.kron(np.eye(a.size), a[:, None].conj())
        ...     Jzc = np.kron(a[:, None], np.eye(a.size))
        ...     return Jz, Jzc
        ...
        >>> problem = GaussNewtonDirectNonHolomorphicProblem(residual, jacobian)
        >>> a_res, info = tl.minimize_trust_region(problem, a_init)
            iter         fval     rel fval     rel step         rho        delta
         max=200               tol=1.0e-12  tol=1.0e-06

               0    5.745e+00
               1    3.061e+00    4.672e-01    3.000e-01    1.123775    9.338e-01
               2    2.543e-01    4.885e-01    5.984e-01    1.092551    1.868e+00
               3    4.753e-04    4.417e-02    8.348e-02    0.998381    1.868e+00
               4    2.121e-09    8.273e-05    4.750e-03    1.000000    1.868e+00
               5    2.142e-20    3.692e-10    1.101e-05    1.000000    1.868e+00
               6    1.113e-31    3.728e-21    3.614e-11    1.000000    1.868e+00

        algorithm minimize_trust_region has stopped (see reason_termination):
            relative function value is smaller than tolerance: 3.728020e-21 <= 1e-12

        data fields:
            niterations : 6
            fval : [..., 1.1130e-31]
            relative_fval : [..., 3.7280e-21]
            relative_step : [..., 3.6144e-11]
            normgrad : []
            rho : [..., 1]
            delta : [..., 1.8676]

        other fields:
            stopping_criteria, zp, algorithm, reason_termination
    """

    residual: ResidualFcn[PointType]
    """Function computing the residual between model, evaluated at point, and data.

    This corresponds to the objective function::

        0.5 * tl.frob(residual) ** 2
    """

    jacobian: ComplexJacobianFcn[PointType]
    """Complex Jacobian evaluated at point. 
    """

    def compute_objective(self, point: VectorType) -> float:
        self._residual = self.residual(self._deserialize(point)).ravel()
        self._fval = tlb.norm2(self._residual) / 2
        return self._fval

    def compute_step(self, point: VectorType) -> tuple[VectorType, Mapping[str, Any]]:
        Jz, Jzc = self.jacobian(self._deserialize(point))
        try:
            self._gradient = (
                Jz.conj().T @ self._residual + Jzc.T @ self._residual.conj()
            )
        except AttributeError:
            raise CallOrderException(
                "compute_objective should be called before compute_step to update the "
                "residual for point."
            )
        self._gradient_norm = tlb.norm(self._gradient)

        curvature = Jz @ self._gradient + Jzc @ self._gradient.conj()
        self._curvature = tlb.norm2(curvature)

        J = np.hstack((mapC2R(Jz + Jzc), mapC2R((Jz - Jzc).conj(), True)))
        if J.shape[0] <= J.shape[1]:
            A = J
            b = -mapC2R(self._residual)
        else:
            A = J.conj().T @ J
            b = -mapC2R(self._gradient)
        step, *_ = tlb.lstsq(A, b)
        self._step = mapR2C(step)

        return self._step, {}


@dataclass
class GaussNewtonIterativeNonHolomorphicProblem(CurvatureProblem[PointType]):
    r"""Complex Gauss--Newton-type optimization problem using an iterative solver.

    This problem definition can be used to solve an unconstrained nonlinear least
    squares optimization problem in the variables ``z``::

        minimize 0.5 * tl.frob(F(z)) ** 2

    The residual ``F(z)`` can be non-holomorphic/non-analytic, i.e., depend on both the
    variables and the conjugated variables ``z.conj()``. The step is computed in least
    squares sense using the Jacobian and the residual. An iterative solver using only
    Jacobian times vector products is used.

    See Also
    --------
    NewtonIterativeNonHolomorphicProblem
        General complex Newton-type optimization problem using an iterative solver.
    GaussNewtonDirectNonHolomorphicProblem
        Complex Gauss--Newton-type optimization problem using a direct solver.
    GaussNewtonIterativeProblem
        Gauss--Newton-type optimization problem where the residual is
        holomorphic/analytic, i.e., does not depend on the conjugated variables. An
        iterative solver using only Jacobian times vector products is used.

    Examples
    --------
    To compute the best Hermitian rank-1 approximation of a Hermitian matrix in least
    squares sense, the following optimization problem can be formulated:

    .. math::
        \underset{\vec{a}}{\text{minimize}}\ \frac12
        \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F}.

    To solve this problem with a Newton-type method, the problem is defined as follows:

    .. code-block:: python

        >>> import pytensorlab as tl
        >>> import numpy as np
        >>> tl.random.set_rng(31415)  # fix random number seed
        >>> a = tl.get_rng().random((5,)) + 1j * tl.get_rng().random((5,))
        >>> M = np.outer(a, a.conj())
        >>> a_init = tl.get_rng().random((5,)) + 1j * tl.get_rng().random((5,))
        >>> def residual(a):
        ...     global M
        ...     return np.outer(a, a.conj()) - M  # correct order is model - data
        ...
        >>> def jacobian_vector(a, x, transpose):
        ...     if transpose:
        ...         x = x.reshape((a.size, a.size))
        ...         return x @ a, x.T @ a.conj()
        ...     return np.kron(x, a.conj()), np.kron(a, x.conj())
        ...
        >>> problem = GaussNewtonIterativeNonHolomorphicProblem(
        ...     residual, jacobian_vector
        ... )
        >>> a_res, info = tl.minimize_trust_region(problem, a_init)
            iter         fval     rel fval     rel step         rho        delta
         max=200               tol=1.0e-12  tol=1.0e-06

               0    5.745e+00
               1    3.061e+00    4.672e-01    3.000e-01    1.123775    9.338e-01
               2    2.543e-01    4.885e-01    5.984e-01    1.092551    1.868e+00
               3    4.753e-04    4.417e-02    8.348e-02    0.998381    1.868e+00
               4    2.121e-09    8.273e-05    4.750e-03    1.000000    1.868e+00
               5    2.142e-20    3.692e-10    1.101e-05    1.000000    1.868e+00
               6    6.501e-32    3.728e-21    3.614e-11    1.000000    1.868e+00

        algorithm minimize_trust_region has stopped (see reason_termination):
            relative function value is smaller than tolerance: 3.728020e-21 <= 1e-12

        data fields:
            niterations : 6
            fval : [..., 6.5011e-32]
            relative_fval : [..., 3.7280e-21]
            relative_step : [..., 3.6144e-11]
            normgrad : []
            rho : [..., 1]
            delta : [..., 1.8676]

        other fields:
            stopping_criteria, zp, algorithm, reason_termination
    """

    residual: ResidualFcn[PointType]
    """Function computing the residual between model evaluated at point and data.

    This corresponds to the objective function::

        0.5 * tl.frob(residual) ** 2
    """

    jacobian_vector: ComplexJacobianVectorProductFcn[PointType]
    """Function computing the Jacobian times vector product evaluated at point."""

    solver: IterativeSolverQR = field(default=lsqr)
    """Iterative solver used to compute the step."""

    solver_options: IterativeSolverOptions = field(
        default_factory=IterativeSolverOptions
    )
    """Options for the iterative solver."""

    def compute_objective(self, point: VectorType) -> float:
        self._residual = self.residual(self._deserialize(point)).ravel()
        self._fval = tlb.norm2(self._residual) / 2
        return self._fval

    def compute_step(self, point: VectorType) -> tuple[VectorType, Mapping[str, Any]]:
        z = self._deserialize(point)
        try:
            gz, gzc = self.jacobian_vector(z, self._residual, transpose=True)
        except AttributeError:
            raise CallOrderException(
                "compute_objective should be called before compute_step to update the "
                "residual for point."
            )
        self._gradient = self._serialize(gz) + self._serialize(gzc).conj()
        self._gradient_norm = tlb.norm(self._gradient)
        gradient = self._deserialize(self._gradient)

        Jz, Jzc = self.jacobian_vector(z, gradient, transpose=False)
        self._curvature = tlb.norm2(Jz + Jzc)
        if self._curvature != 0:
            cauchy_point = -self._gradient_norm**2 / self._curvature * self._gradient
        else:
            cauchy_point = -1.0 * self._gradient

        def Ax(x: VectorType) -> VectorType:
            J, Jc = self.jacobian_vector(
                z, self._deserialize(mapR2C(x)), transpose=False
            )
            return mapC2R(J.ravel() + Jc.ravel())

        def ATx(x: VectorType) -> VectorType:
            Jz, Jzc = self.jacobian_vector(z, mapR2C(x), transpose=True)
            return mapC2R(self._serialize(Jz) + self._serialize(Jzc).conj())

        shape = (2 * self._residual.size, 2 * point.size)
        A = CustomLinearOperator(shape, Ax, rmatvec=ATx, dtype=point.dtype)
        step, *info = self.solver(
            A,
            mapC2R(-self._residual),
            x0=mapC2R(-cauchy_point),
            iter_lim=self.solver_options.max_iterations,
            atol=self.solver_options.tolerance,
            btol=self.solver_options.tolerance,
        )
        self._step = mapR2C(step)
        residual = info[2] / self._gradient_norm if len(info) >= 3 else None
        return self._step, {"nmatvecs": A.ncalls / 2, "residual_norm": residual}


@dataclass
class NewtonDirectNonHolomorphicProblem(CurvatureProblem[PointType]):
    r"""Complex Newton-type optimization problem using a direct solver.

    This problem definition can be used to solve an unconstrained optimization problem
    in the complex variables ``z``::

        minimize f(z)

    This problem can be used for any real-valued, non-holomorphic/non-analytic objective
    function, i.e., the function can depend on both the variables ``z`` and the
    conjugated variables ``z.conj()``. The step is computed in least squares sense using
    the Hessian or an approximation thereof, and the gradient. A direct solver is used.

    See Also
    --------
    NewtonDirectProblem
        Newton-type optimization problem for real variables.
    NewtonIterativeNonHolomorphicProblem
        Complex Newton-type optimization problem using an iterative solver relying only
        on Hessian times vector products.

    Examples
    --------
    To compute the best Hermitian rank-1 approximation of a Hermitian matrix in least
    squares sense, the following optimization problem can be formulated:

    .. math::

        \underset{\vec{a}}{\text{minimize}}\ \frac12
        \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F}.

    To solve this problem with a Newton-type method, the problem is defined as follows:

    .. code-block:: python

        >>> import pytensorlab as tl
        >>> import numpy as np
        >>> tl.random.set_rng(31415)  # fix random number seed
        >>> a = tl.get_rng().random((5,)) + 1j * tl.get_rng().random((5,))
        >>> M = np.outer(a, a.conj())
        >>> a_init = tl.get_rng().random((5,)) + 1j * tl.get_rng().random((5,))
        >>> def objective(a):
        ...     global M
        ...     residual = np.outer(a, a.conj()) - M
        ...     return 0.5 * np.linalg.norm(residual) ** 2
        ...
        >>> def gradient(a):
        ...     global M
        ...     residual = np.outer(a, a.conj()) - M
        ...     return 2 * residual @ a
        ...
        >>> def hessian(a):
        ...     global M
        ...     residual = np.outer(a, a.conj()) - M
        ...     Id = np.eye(a.size)
        ...     return 2 * np.vdot(a, a) * Id + 2 * residual.T, 2 * np.outer(a, a)
        ...
        >>> problem = NewtonDirectNonHolomorphicProblem(objective, gradient, hessian)
        >>> a_res, info = tl.minimize_trust_region(problem, a_init)
            iter         fval     rel fval     rel step         rho        delta
         max=200               tol=1.0e-12  tol=1.0e-06

               0    5.745e+00
               1    3.061e+00    4.672e-01    3.000e-01    1.122401    9.338e-01
               2    2.626e-01    4.871e-01    5.984e-01    0.993059    1.868e+00
               3    3.161e-03    4.515e-02    7.934e-02    1.057199    1.868e+00
               4    7.774e-07    5.500e-04    1.163e-02    1.010361    1.868e+00
               5    5.416e-14    1.353e-07    1.867e-04    1.000180    1.868e+00
               6    2.567e-28    9.427e-15    4.988e-08    1.000000    1.868e+00

        algorithm minimize_trust_region has stopped (see reason_termination):
            relative function value is smaller than tolerance: 9.426744e-15 <= 1e-12

        data fields:
            niterations : 6
            fval : [..., 2.5674e-28]
            relative_fval : [..., 9.4267e-15]
            relative_step : [..., 4.9884e-08]
            normgrad : []
            rho : [..., 1]
            delta : [..., 1.8676]

        other fields:
            stopping_criteria, zp, algorithm, reason_termination

    The Gramian of the Jacobian can also be used to have the Gauss--Newton method.

    >>> def gramian(a):
    ...     Id = np.eye(a.size)
    ...     return 2 * np.vdot(a, a) * Id, 2 * np.outer(a, a)
    ...
    >>> problem = NewtonDirectNonHolomorphicProblem(objective, gradient, gramian)
    """

    objective: ObjectiveFcn[PointType]
    """Function that evaluates the objective function in a given point."""

    gradient: GradientFcn[PointType]
    """Function that evaluates the gradient in a given point."""

    hessian: ComplexHessianFcn[PointType]
    """Function that computes the complex Hessian in a given point."""

    def compute_objective(self, point: VectorType) -> float:
        self._fval = cast(float, self.objective(self._deserialize(point)))
        return self._fval

    def compute_step(self, point: VectorType) -> tuple[VectorType, Mapping[str, Any]]:
        self._gradient = self._serialize(self.gradient(self._deserialize(point)))
        self._gradient_norm = tlb.norm(self._gradient)

        Hzz, Hzzc = self.hessian(self._deserialize(point))
        hessian_real = np.block(
            [
                [Hzz.real + Hzzc.real, Hzzc.imag - Hzz.imag],
                [Hzz.imag + Hzzc.imag, Hzz.real - Hzzc.real],
            ],
        )
        gradient_real = mapC2R(self._gradient)
        self._curvature = np.dot(gradient_real, hessian_real @ gradient_real)

        step, *_ = np.linalg.lstsq(hessian_real, -gradient_real, rcond=None)
        self._step = mapR2C(step)
        return self._step, {}


@dataclass
class NewtonIterativeNonHolomorphicProblem(CurvatureProblem[PointType]):
    r"""Complex Newton-type optimization problem using an iterative solver.

    This problem definition can be used to solve an unconstrained optimization problem
    in the complex variables ``z``::

        minimize f(z)

    This problem can be used for any real-valued, non-holomorphic/non-analytic objective
    function, i.e., the function can depend on both the variables ``z`` and the
    conjugated variables ``z.conj()``. The step is computed in least squares sense using
    the Hessian or an approximation thereof, and the gradient. An iterative solver using
    only Hessian times vector products is used.

    See Also
    --------
    NewtonIterativeProblem
        Newton-type optimization problem for real variables.
    NewtonDirectNonHolomorphicProblem
        Complex Newton-type optimization problem using a direct solver.

    Examples
    --------
    To compute the best Hermitian rank-1 approximation of a Hermitian matrix in least
    squares sense, the following optimization problem can be formulated:

    .. math::

        \underset{\vec{a}}{\text{minimize}}\ \frac12
        \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F}.

    To solve this problem with a Newton-type method, the problem is defined as follows:

    .. code-block:: python

        >>> import pytensorlab as tl
        >>> import numpy as np
        >>> tl.random.set_rng(31415)  # fix random number seed
        >>> a = tl.get_rng().random((5,)) + 1j * tl.get_rng().random((5,))
        >>> M = np.outer(a, a.conj())
        >>> a_init = tl.get_rng().random((5,)) + 1j * tl.get_rng().random((5,))
        >>> def objective(a):
        ...     global M
        ...     residual = np.outer(a, a.conj()) - M
        ...     return 0.5 * np.linalg.norm(residual) ** 2
        ...
        >>> def gradient(a):
        ...     global M
        ...     residual = np.outer(a, a.conj()) - M
        ...     return 2 * residual @ a
        ...
        >>> def hessian_vector(a, x):
        ...     global M
        ...     residual = np.outer(a, a.conj()) - M
        ...     return 2 * (np.vdot(a, a) * x + a * np.vdot(x, a) + residual.T @ x)
        ...
        >>> problem = NewtonIterativeNonHolomorphicProblem(
        ...     objective, gradient, hessian_vector
        ... )
        >>> a_res, info = tl.minimize_trust_region(problem, a_init)
            iter         fval     rel fval     rel step         rho        delta
         max=200               tol=1.0e-12  tol=1.0e-06

               0    5.745e+00
               1    3.061e+00    4.672e-01    3.000e-01    1.122401    9.338e-01
               2    2.626e-01    4.871e-01    5.984e-01    0.993059    1.868e+00
               3    3.161e-03    4.515e-02    7.934e-02    1.057199    1.868e+00
               4    7.774e-07    5.500e-04    1.163e-02    1.010361    1.868e+00
               5    5.416e-14    1.353e-07    1.867e-04    1.000180    1.868e+00
               6    2.606e-28    9.427e-15    4.988e-08    1.000000    1.868e+00

        algorithm minimize_trust_region has stopped (see reason_termination):
            relative function value is smaller than tolerance: 9.426744e-15 <= 1e-12

        data fields:
            niterations : 6
            fval : [..., 2.6057e-28]
            relative_fval : [..., 9.4267e-15]
            relative_step : [..., 4.9882e-08]
            normgrad : []
            rho : [..., 1]
            delta : [..., 1.8676]

        other fields:
            stopping_criteria, zp, algorithm, reason_termination

    The Gramian of the Jacobian can also be used to have the Gauss--Newton method. To
    speed up convergence of the iterative solver, a preconditioner can be used.

    .. code-block:: python

        >>> def gramian_vector(a, x):
        ...     return 2 * (np.vdot(a, a) * x + a * np.vdot(x, a))
        ...
        >>> def preconditioner(a, r):
        ...     return r / np.vdot(a, a) / 2
        ...
        >>> problem = NewtonIterativeNonHolomorphicProblem(
        ...     objective, gradient, gramian_vector, preconditioner
        ... )
        >>> a_res, info = tl.minimize_trust_region(problem, a_init)
            iter         fval     rel fval     rel step         rho        delta
         max=200               tol=1.0e-12  tol=1.0e-06

               0    5.745e+00
               1    3.061e+00    4.672e-01    3.000e-01    1.123775    9.338e-01
               2    2.543e-01    4.885e-01    5.984e-01    1.092551    1.868e+00
               3    4.753e-04    4.417e-02    8.348e-02    0.998381    1.868e+00
               4    2.121e-09    8.273e-05    4.750e-03    1.000000    1.868e+00
               5    2.142e-20    3.692e-10    1.101e-05    1.000000    1.868e+00
               6    1.358e-31    3.728e-21    3.614e-11    1.000000    1.868e+00

        algorithm minimize_trust_region has stopped (see reason_termination):
            relative function value is smaller than tolerance: 3.728026e-21 <= 1e-12

        data fields:
            niterations : 6
            fval : [..., 1.3582e-31]
            relative_fval : [..., 3.7280e-21]
            relative_step : [..., 3.6144e-11]
            normgrad : []
            rho : [..., 1]
            delta : [..., 1.8676]

        other fields:
            stopping_criteria, zp, algorithm, reason_termination
    """

    objective: ObjectiveFcn[PointType]
    """Function computing the objective function value."""

    gradient: GradientFcn[PointType]
    """Function computing the gradient of the objective function."""

    hessian_vector: ComplexHessianVectorProductFcn[PointType]
    """Function computing the product of the Hessian and a vector."""

    preconditioner: PreconditionerFcn[PointType] | None = None
    """Function applying a preconditioner in an iterative solver."""

    solver: IterativeSolver = cast(IterativeSolver, field(default=cg))
    """Solver for square, symmetric linear systems used to determine the step."""

    solver_options: IterativeSolverOptions = field(
        default_factory=IterativeSolverOptions
    )
    """Options for the iterative solver."""

    _residual_extractor: ResidualExtractor = field(default_factory=ResidualExtractor)
    """Function extracting the residual from the iterative solver if not exposed."""

    def compute_objective(self, point: VectorType) -> float:
        self._fval = cast(float, self.objective(self._deserialize(point)))
        return self._fval

    def compute_step(self, point: VectorType) -> tuple[VectorType, Mapping[str, Any]]:
        z = self._deserialize(point)
        gradient = self.gradient(z)
        self._gradient = self._serialize(gradient)
        self._gradient_norm = tlb.norm(self._gradient)

        hessian_gradient = self._serialize(self.hessian_vector(z, gradient))
        self._curvature = cast(float, np.vdot(self._gradient, hessian_gradient).real)

        if self._curvature != 0:
            cauchy_point = -self._gradient_norm**2 / self._curvature * self._gradient
        else:
            cauchy_point = -1.0 * self._gradient

        def Ax(x: VectorType) -> VectorType:
            y = self.hessian_vector(z, self._deserialize(mapR2C(x)))
            return mapC2R(self._serialize(y))

        def M(b: VectorType) -> VectorType:
            assert self.preconditioner is not None
            x = self.preconditioner(z, self._deserialize(mapR2C(b)))
            return mapC2R(self._serialize(x))

        shape = (point.size * 2, point.size * 2)
        A = CustomLinearOperator(shape, Ax, dtype=point.dtype)
        options: dict[str, Any] = {
            "rtol": self.solver_options.tolerance,
            "maxiter": self.solver_options.max_iterations,
        }
        options |= self.solver_options.other
        options |= self._residual_extractor.create_callback(self.solver)
        if self.preconditioner:
            options["M"] = CustomLinearOperator(shape, M, dtype=point.dtype)

        step, _ = self.solver(
            A,
            -mapC2R(self._gradient),
            x0=mapC2R(cauchy_point),
            **options,  # type:ignore
        )
        self._step = mapR2C(step)
        if self._residual_extractor.residual_norm is None:
            self._residual_extractor.enabled = False
        residual = self._residual_extractor.residual_norm
        residual = None if residual is None else residual / self._gradient_norm
        return self._step, {"nmatvec": A.ncalls, "residual": residual}


@dataclass
class LBFGSProblem(CurvatureProblem[PointType]):
    r"""Limited memory BFGS-type problem.

    This problem definition can be used to solve an unconstrained optimization problem
    in the variables ``z``::

        minimize f(z)

    The variables can be real or complex. The step is computed using the quasi-Newton
    type Broyden-Fletcher-Goldfarb-Shanno (BFGS) algorithm . In particular, the
    limited-memory variant is used.

    See Also
    --------
    NewtonDirectProblem
        Newton-type optimization problem for real variables.
    NewtonDirectNonHolomorphicProblem
        Newton-type optimization problem for complex variables.

    Examples
    --------
    To compute the best rank-1 approximation of a matrix in least squares sense, the
    following optimization problem can be formulated:

    .. math::
        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F}.

    To solve this problem with the L-BFGS method, the problem is defined as follows:

    .. code-block:: python

        >>> import pytensorlab as tl
        >>> import numpy as np
        >>> tl.random.set_rng(31415)  # fix random number seed
        >>> M = np.array(tl.PolyadicTensor.random((5, 6), 1))
        >>> z_init = tl.PolyadicTensor.random((5, 6), 1)
        >>> a, b = z_init.factors  # not needed, shows link to original variables
        >>> def objective(z):
        ...     global M
        ...     return 0.5 * tl.frob(tl.residual(z, M)) ** 2
        ...
        >>> def gradient(z):
        ...     global M
        ...     res = np.array(z) - M
        ...     ga = res @ z.factors[1].conj()
        ...     gb = res.T @ z.factors[0].conj()
        ...     return tl.PolyadicTensor((ga, gb))
        ...
        >>> problem = LBFGSProblem(objective, gradient)
        >>> problem.serialize = lambda z: z._data
        >>> problem.deserialize = lambda d: tl.PolyadicTensor.from_vector(d, (5, 6), 1)
        >>> z_res, info = tl.minimize_trust_region(problem, z_init)
                iter         fval     rel fval     rel step         rho        delta
         max=200               tol=1.0e-12  tol=1.0e-06

               0    1.304e+00
               1    7.125e-01    4.535e-01    3.000e-01    0.882654    1.121e+00
               2    4.320e-01    2.151e-01    5.293e-01    0.591485    2.007e+00
               3    9.903e-02    2.554e-01    1.558e-01    0.938625    2.007e+00
               4    8.336e-03    6.956e-02    1.333e-01    1.261648    2.007e+00
               5    1.957e-04    6.244e-03    6.083e-02    0.954208    2.007e+00
               6    2.180e-05    1.334e-04    4.875e-03    0.797498    2.007e+00
               7    2.974e-07    1.649e-05    1.355e-03    1.090610    2.007e+00
               8    3.313e-10    2.278e-07    1.712e-04    1.020488    2.007e+00
               9    1.869e-13    2.540e-10    5.428e-06    1.018495    2.007e+00
              10    1.872e-17    1.433e-13    1.309e-07    1.005737    2.007e+00

        algorithm minimize_trust_region has stopped (see reason_termination):
            relative function value is smaller than tolerance: 1.433483e-13 <= 1e-12

        data fields:
            niterations : 10
            fval : [..., 1.8718e-17]
            relative_fval : [..., 1.4335e-13]
            relative_step : [..., 1.3089e-07]
            normgrad : []
            rho : [..., 1.0057]
            delta : [..., 2.0068]

        other fields:
            stopping_criteria, zp, algorithm, reason_termination


    To compute the best Hermitian rank-1 approximation of a Hermitian matrix in least
    squares sense, the following optimization problem can be formulated:

    .. math::

        \underset{\vec{a}}{\text{minimize}}\ \frac12
        \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F}.

    To solve this problem with the LBFGS-type, the problem is defined as follows:

    .. code-block:: python

        >>> import pytensorlab as tl
        >>> import numpy as np
        >>> tl.random.set_rng(31415)  # fix random number seed
        >>> a = tl.get_rng().random((5,)) + 1j * tl.get_rng().random((5,))
        >>> M = np.outer(a, a.conj())
        >>> a_init = tl.get_rng().random((5,)) + 1j * tl.get_rng().random((5,))
        >>> def objective(a):
        ...     global M
        ...     residual = np.outer(a, a.conj()) - M
        ...     return 0.5 * np.linalg.norm(residual) ** 2
        ...
        >>> def gradient(a):
        ...     global M
        ...     residual = np.outer(a, a.conj()) - M
        ...     return 2 * residual @ a
        ...
        >>> problem = LBFGSProblem(objective, gradient)
        >>> a_res, info = tl.minimize_trust_region(problem, a_init)
            iter         fval     rel fval     rel step         rho        delta
         max=200               tol=1.0e-12  tol=1.0e-06

               0    5.745e+00
               1    3.061e+00    4.672e-01    3.000e-01    0.952500    9.338e-01
               2    2.626e-01    4.871e-01    5.984e-01 0.609177+0~    1.868e+00
               3    6.785e-02    3.389e-02    9.578e-02    0.670525    1.868e+00
               4    1.125e-03    1.161e-02    5.431e-02    1.144893    1.868e+00
               5    8.365e-06    1.943e-04    8.444e-03    0.956569    1.868e+00
               6    7.039e-08    1.444e-06    4.846e-04    1.071025    1.868e+00
               7    5.047e-11    1.224e-08    5.024e-05    1.016904    1.868e+00
               8    2.101e-14    8.781e-12    1.722e-06    1.015675    1.868e+00
               9    7.330e-19    3.657e-15    3.445e-08    1.003761    1.868e+00

        algorithm minimize_trust_region has stopped (see reason_termination):
            relative function value is smaller than tolerance: 3.656975e-15 <= 1e-12

        data fields:
            niterations : 9
            fval : [..., 7.3304e-19]
            relative_fval : [..., 3.6570e-15]
            relative_step : [..., 3.4445e-08]
            normgrad : []
            rho : [..., 1.0038]
            delta : [..., 1.8676]

        other fields:
            stopping_criteria, zp, algorithm, reason_termination
    """

    objective: ObjectiveFcn[PointType]
    """Function computing the objective function value."""

    gradient: GradientFcn[PointType]
    """Function evaluating the gradient in a certain point."""

    memory_limit: PositiveInt = 30
    """Maximum of pairs of update vectors that are stored."""

    _previous_point: VectorType = field(default_factory=lambda: np.empty(0))
    """Point used in the previous step computation."""

    _previous_gradient: VectorType = field(default_factory=lambda: np.empty(0))
    """Gradient evaluated in the point used in the previous step computation."""

    _current_index: int = -1
    """Index of the current item in the memory matrices `_S` and `_Y`."""

    _memory_length: int = 0
    """Number of items currently stored.

    This is primarily used to avoid computations with zero vectors from `_S` and `_Y`
    when the number of calls to `compute_step` is smaller than `memory_limit`.
    """

    _S: MatrixType = field(default_factory=lambda: np.empty((0, 0)))
    """Matrix of steps taken by the algorithm.

    Every time `compute_step` is called, the step is computed as the difference of the
    point and the previous point and stored as a vector in `_S`. To limit memory usage,
    this is a circular buffer, i.e., during call ``k`` (counting from 0)::

        _S[k % memory_limit] = step

    See Also
    --------
    _current_index, _Y
    """

    _Y: MatrixType = field(default_factory=lambda: np.empty((0, 0)))
    """Matrix of gradient changes.

    Each gradient change is computed as the difference between the current and the
    previous gradient. To limit memory usage, this is a circular buffer, i.e., during
    call ``k`` (counting from 0)::

        _Y[k % memory_limit] = gradient_difference    

    See Also
    --------
    _current_index, _S
    """

    _rho: VectorType = field(default_factory=lambda: np.empty(0))
    """Inverse of the inner product of the step and the gradient change.

    To limit memory usage, this is a circular buffer, i.e., during call ``k`` (counting
    from 0)::

        kmod = k % memory_limit
        _rho[kmod] = 1 / np.real(np.vdot(_S[kmod], _Y[kmod]))

    See Also
    --------
    _current_index, _S, _Y
    """

    def initialize_cache(self, point: VectorType) -> None:
        """Initialize cached variables.

        Preallocate memory for the cached variables.

        Parameters
        ----------
        point : VectorType
            Vector of variables used in this problem. The actual values in `point` are
            irrelevant as only the ``dtype`` and ``size`` are used.
        """
        size = point.size
        self._previous_point = np.zeros((size,), dtype=point.dtype)
        self._previous_gradient = np.zeros((size,), dtype=point.dtype)
        self._S = np.empty((self.memory_limit, size), dtype=point.dtype)
        self._Y = np.empty((self.memory_limit, size), dtype=point.dtype)
        self._rho = np.empty((self.memory_limit,), dtype=point.dtype)

    def compute_objective(self, point: VectorType) -> float:
        self._fval = cast(float, self.objective(self._deserialize(point)))
        return self._fval

    def compute_step(self, point: VectorType) -> tuple[VectorType, Mapping[str, Any]]:
        if self._previous_point.size == 0:
            self.initialize_cache(point)

        self._gradient = self._serialize(self.gradient(self._deserialize(point)))
        self._gradient_norm = tlb.norm(self._gradient)

        y = self._gradient - self._previous_gradient
        s = point - self._previous_point
        sy = np.vdot(s, y).real

        s_norm2 = tlb.norm2(s)
        if s_norm2 == 0:
            raise ValueError("point is identical to previous point")

        if sy > 0:
            self._Y[self._current_index] = y
            self._S[self._current_index] = s
            self._rho[self._current_index] = 1 / sy

        step = -self._gradient.copy()
        alpha = np.zeros((self.memory_limit,), dtype=point.dtype)
        for i in range(
            self._current_index, self._current_index - self._memory_length, -1
        ):
            alpha[i] = self._rho[i] * np.vdot(self._S[i], step).real
            step -= alpha[i] * self._Y[i]

        if self._memory_length > 0:
            y_norm2 = tlb.norm2(y)
            gamma = self._rho[self._current_index] * y_norm2
            step /= gamma

            curvature = gamma * (
                self._gradient_norm**2
                - np.vdot(self._gradient, s).real ** 2 / s_norm2
                + np.vdot(self._gradient, y).real ** 2 / y_norm2
            )
        else:
            curvature = self._gradient_norm**2

        for i in range(
            self._current_index - self._memory_length + 1, self._current_index + 1
        ):
            beta = self._rho[i] * np.vdot(self._Y[i], step).real
            step += (alpha[i] - beta) * self._S[i]

        self._previous_point = point.copy()
        self._previous_gradient = self._gradient.copy()
        if sy > 0:
            self._current_index = (self._current_index + 1) % self.memory_limit
            self._memory_length = min(self._memory_length + 1, self.memory_limit)
        self._curvature = cast(float, curvature)
        self._step = step

        return self._step, {}

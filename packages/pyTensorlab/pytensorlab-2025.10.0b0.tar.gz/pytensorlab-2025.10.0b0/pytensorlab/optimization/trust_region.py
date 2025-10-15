"""Trust region optimization methods.

This module provides a trust region solver for the unconstrained optimization problem::

        minimize f(z)

with variables ``z``. In each (outer) iteration a model of the objective function in the
current variables (`point`) is used in a trust region subproblem to find an update,
i.e., the step. The step length depends on the trustworthiness of the model. The
subproblem can be solved exactly or inexactly.

The main trust region solver is :func:`.minimize_trust_region` and the main subproblem
solver is :func:`minimize_dogleg`, which uses the dogleg method. Other solvers can be
created based on the :class:`TrustRegionOptimizer` and the :class:`PlaneSearchFcn`
classes.

Functions
---------
minimize_dogleg
    Compute an approximate trust region minimizer using the dogleg step.
minimize_trust_region
    Minimize an unconstrained optimization problem using the trust region method.

Classes
-------
PlaneSearchFcn
    Function computing the optimal point in a plane within a trust region.
TrustRegionOptimizer
    Function solving a minimization problem via trust region subproblems.
OptimizationOptions
    Options for an optimization algorithm.

Examples
--------
See :class:`.TrustRegionOptimizer`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import (
    Generic,
    Literal,
    NoReturn,
    Protocol,
    TypeVar,
    cast,
)

import numpy as np

import pytensorlab.backends.numpy as tlb
from pytensorlab.optimization import (
    OptimizationProgressLogger,
    PrinterField,
    ProgressPrinter,
    StoppingCriterion,
    StoppingCriterionCustom,
    default_stopping_criteria,
)
from pytensorlab.optimization.methods import ComplexCurvatureException
from pytensorlab.optimization.problem import CurvatureProblem, PointType
from pytensorlab.typing import NonnegativeFloat, NonnegativeInt, VectorType
from pytensorlab.util import Options

_Number = TypeVar("_Number", bound=float)


def _solve_quadratic(a: _Number, b: _Number, c: _Number) -> tuple[_Number, _Number]:
    """Compute the real roots of quadratic equation.

    The quadratic equation ``a * x**2 + b * x + c = 0`` is solved in a numerically
    stable way.
    """
    u = -b + np.sign(b) * np.sqrt(b**2 - 4 * a * c)
    if b < 0:
        return 2 * c / u, u / (2 * a)
    return u / (2 * a), 2 * c / u


class PlaneSearchFcn(Protocol):
    """Function computing the optimal point in a plane within a trust region.

    An objective function or an approximation of this objective function around `point`
    is minimized in a plane spanned by two vectors `p` and `q`. The optimum should lie
    in a ball with a given `radius`.

    See Also
    --------
    minimize_dogleg
    """

    def __call__(
        self,
        point: VectorType,
        p: VectorType,
        q: VectorType,
        /,
        radius: float,
        cost: float,
        curvature: float,
    ) -> tuple[VectorType, float]:
        """Compute  the optimal point in a plane within a trust region.

        Parameters
        ----------
        point : VectorType
            Current optimization point.
        p : VectorType
            Vector defining the first direction of the plane spanned by `p` and `q`.
        q : VectorType
            Vector defining the second direction of the plane spanned by `p` and `q`.
        radius : float
            Radius of the ball around the current point in which the optimal point is
            sought.
        cost : float
            Value of the objective function in the current point.
        curvature : float
            Curvature of the objective function in the current point.

        Returns
        -------
        optimal_point : VectorType
            A (quasi-)optimal point in the plane spanned by `p` and `q` and inside the
            ball with the given `radius`.
        float
            Objective function value at `optimal_point`.
        """
        ...


@dataclass
class TrustRegionStepRejectedException(Exception):
    """Exception raised when the step is rejected by a trust region method."""

    trustworthiness: float
    """Trustworthiness of the model."""

    step_norm: float
    """Step size."""

    tolerance: float
    """Step size tolerance."""

    radius: float
    """Radius of the trust region."""

    def __str__(self) -> str:
        return (
            f"step norm is {self.step_norm:.3e} <= step tolerance "
            f"({self.tolerance:.1e}) while the model is not trustworthy "
            f"({self.trustworthiness:.3} <= 0)"
        )


class ProblemException(Exception):
    """Exception raised when the problem is incorrect."""

    pass


class TrustRegionInvalidUpdateException(Exception):
    """Exception raised when invalid trust region update is computed."""

    pass


def minimize_dogleg(
    point: VectorType,
    gradient: VectorType,
    step: VectorType,
    radius: float,
    cost: float,
    curvature: float,
) -> tuple[VectorType, float]:
    """Compute an approximate trust region minimizer using the dogleg step.

    The following trust region problem is solved::

        step = arg min fk + dot(g, p) + 0.5 * dot(p, H @ p)
        subject to norm(p) <= radius
                   p in span{cauchy_point, proposed_step}

    Instead of solving this problem exactly, the dogleg method
    :cite:`nocedal2006optimization` is used.

    Parameters
    ----------
    point : VectorType
        The evaluation point in which the second-order approximation is computed.
    cost : float
        Objective function value evaluated at `point`.
    gradient : VectorType
        The gradient evaluated at `point`.
    proposed_step : VectorType
        The propsed step evaluated at `point`, for example, a quasi-Newton, a
        Gauss-Newton or a Newton step.
    curvature : float
        Curvature along the gradient direction. If the Hessian or an approximation
        evaluated at `point` is denoted by `H`, the curvature is defined as
        ``np.vdot(gradient, H @ gradient)``.

    Returns
    -------
    VectorType
        The dogleg step.
    float
        The estimated improvement in function value.


    """
    if curvature < 0:
        raise ProblemException(f"curvature is {curvature:.3e} but should be positive")

    step_norm = tlb.norm(step)
    gradient_norm = tlb.norm(gradient)
    cauchy_scalar = gradient_norm**2 / curvature
    cauchy_point = -cauchy_scalar * gradient

    if step_norm <= radius:
        dogleg_step = step
        dfval = cast(float, -0.5 * np.real(np.vdot(gradient, dogleg_step)))
    elif gradient_norm**3 / curvature < radius:
        leg = step - cauchy_point
        leg_norm2 = cast(float, np.real(np.vdot(leg, leg)))

        tau, _ = _solve_quadratic(
            leg_norm2,
            cast(float, 2 * np.real(np.vdot(cauchy_point, leg))),
            gradient_norm**6 / curvature**2 - radius**2,
        )
        assert 0 <= tau <= 1
        dogleg_step = cauchy_point + tau * leg

        grad_step = cast(float, np.real(np.vdot(gradient, step)))
        dfval = cauchy_scalar / 2 * (1 - tau) ** 2 * gradient_norm**2
        dfval += tau * (tau / 2 - 1) * grad_step
    else:
        dogleg_step = -radius / gradient_norm * gradient
        dfval = radius * (gradient_norm - 0.5 * radius / cauchy_scalar)

    return dogleg_step, dfval


@dataclass
class TrustRegionOptimizer(Generic[PointType]):
    r"""Function solving a minimization problem via trust region subproblems.

    An unconstrained optimization problem::

        minimize f(z)

    is solved for the variables ``z``. In each iteration, the current variables, which
    are referred to as `point`, are updated via a trust region subproblem: the following
    problem::

        step = arg min fk + dot(g, p) + 0.5 * dot(p, H @ p)
        subject to norm(p) <= radius
                   p in span{cauchy_point, proposed_step}

    is solved for ``step``, which updates the current variables in `point`, i.e., the
    updated variables will be ``point + step``. This optimization problem minimizes with
    respect to ``p`` and uses the function value ``fk``, the gradient ``g``, and the
    Hessian ``H``, which are all evaluated in the current variables `point`. The search
    region is restricted to the intersection of the plane spanned by ``cauchy_point``
    and a ``proposed_step``, e.g., the Newton or the L-BFGS step, and a ball with a
    certain trust ``radius``. This ``radius`` is updated based on the trustworthiness of
    the model.

    The computation of different elements is defined in `problem`. The actual
    minimization is carried out by the `minimize_plane` function; this function does not
    need to return an exact solution as long as sufficient decrease is obtained. The
    main iterations of the algorithm are performed by the `iterate` function, which
    performs exactly one iteration. By calling this :class:`.TrustRegionOptimizer`, the
    optimizer calls `iterate` until one of the stopping criteria defined in `log` are
    satisfied.

    Examples
    --------
    To compute the best rank-1 approximation of a matrix in least squares sense, the
    following optimization problem can be formulated:

    .. math::
        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F}.

    To solve this problem with a Newton-type method, the problem is defined first:

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

    For the overall algorithm, the algorithm is stopped after three iterations.

    >>> log = tl.optimization.OptimizationProgressLogger(
    ...     tl.minimize_trust_region,  # typically the name of the algorithm
    ...     stopping_criteria=tl.default_stopping_criteria(max_iter=3),
    ...     terminate_with_exception=False,
    ... )

    Next, the optimizer is defined. The :func:`minimize_dogleg` function is used to
    solve the trust region problem each outer iteration:

    >>> optimizer = TrustRegionOptimizer(problem, minimize_dogleg, log)

    Finally, the algorithm is actually run, starting from the initial guess:

    .. code-block:: python

        >>> z_res, log = optimizer(problem._serialize(z_init))
            iter         fval     rel fval     rel step
           max=3

               0    1.304e+00
               1    7.125e-01    4.535e-01    3.000e-01
               2    3.760e-02    5.177e-01    5.915e-01
               3    9.326e-05    2.877e-02    8.348e-02

        algorithm minimize_trust_region has stopped (see reason_termination):
            number of iterations exceeds maximum: 3 >= 3

        data fields:
            niterations : 3
            fval : [..., 9.3260e-05]
            relative_fval : [..., 0.0288]
            relative_step : [..., 0.0835]
            normgrad : []

        other fields:
            stopping_criteria, zp, algorithm, reason_termination
    """

    problem: CurvatureProblem[PointType]
    """Method for solving an optimization problem.

    The problem defines the necessary functions to compute the objective function value
    in the current point and the proposed step, as well as the curvature at the current
    point.

    See Also
    --------
    pytensorlab.optimization.methods
    """

    minimize_plane: PlaneSearchFcn
    """Function that computes the a step in the trust region.

    See Also
    --------
    .minimize_dogleg
    """

    log: OptimizationProgressLogger
    """Log containing progress values and stopping criteria."""

    printer: ProgressPrinter = field(default_factory=ProgressPrinter)
    """Printer that displays logged values per iteration.

    See Also
    --------
    .ProgressPrinter, .VoidPrinter
    """

    point: VectorType = field(default_factory=lambda: np.empty((1,)))
    """Current optimization point."""

    radius: float | None = None
    """Radius of the trust region."""

    step_tolerance: float = 1e-6
    """Tolerance on the step size."""

    trustworthiness_tolerance: float = 0.5
    """Lower bound on the trustworthiness to accept the step."""

    max_inner_iterations: int = 10
    """Maximum number of inner iterations.

    An exception will be raised when this limit is reached.
    """

    def __post_init__(self) -> None:
        self.printer.add_logger(self.log)  # Make sure the same log is used.

    def compute_trustworthiness(
        self, step: VectorType, current_cost: float, predicted_improvement: float, /
    ) -> tuple[float, float]:
        """Compute the trustworthiness for the given step.

        Parameters
        ----------
        step : VectorType
            Step for which to compute the trustworthiness.
        current_cost : float
            Current cost function value.
        predicted_improvement: float
            The predicted improvement for the given step.

        Returns
        -------
        float
            Trustworthiness of the model based on the given step.
        float
            Cost function evaluation at ``self.point + step``
        """
        cost = self.problem.compute_objective(self.point + step)
        actual_improvement = current_cost - cost
        trustworthiness = actual_improvement / predicted_improvement
        return trustworthiness, cost

    def compute_relative_step(self, point: VectorType, step: VectorType) -> float:
        """Compute the step norm relative to the point norm.

        Parameters
        ----------
        point : VectorType
            Current optimization point.
        step : VectorType
            Proposed step.

        Returns
        -------
        float
            Norm of the proposed `step` relative to the norm of the variables `point`.
        """
        point_norm = cast(float, tlb.norm(point))
        step_norm = cast(float, tlb.norm(step))
        if point_norm == 0 or np.isnan(step_norm):
            return 0.0
        return step_norm / point_norm

    def has_failed(self, trustworthiness: float, relative_step_norm: float) -> bool:
        """Check if the algorithm failed to find a trustworthy step.

        Parameters
        ----------
        trustworthiness : float
            The trustworthiness of the model.
        relative_step_norm : float
            The norm of the step relative to the norm of the variables.

        Returns
        -------
        bool
            True if the algorithm did not find a step.
        """
        return trustworthiness <= 0 and relative_step_norm <= self.step_tolerance

    def update_radius(
        self, radius: float, trustworthiness: float, step: VectorType, /
    ) -> float:
        """Update the radius of the trust region.

        In general, the radius may increase if the model is trustworthy. If the model is
        not trustworthy, the radius is decreased.

        Parameters
        ----------
        radius : float
            Current radius of the trust region.
        trustworthiness : float
            Trustworthiness of the model at the current point.
        step : VectorType
            Computed step inside the trust region.

        Returns
        -------
        float
            The updated trust region.
        """
        if trustworthiness > self.trustworthiness_tolerance:
            return max(radius, 2 * cast(float, tlb.norm(step)))

        if trustworthiness < -50:
            sigma = 0.25  # avoid overflow in exp: np.exp(14 * 50) is close to overflow
        else:
            sigma = (3 / 4) / (1 + np.exp(-14 * (trustworthiness - 0.25))) + 1 / 4
        if tlb.norm(self.problem._step) < sigma * radius and trustworthiness < 0:
            e = np.log2(tlb.norm(self.problem._step) / radius) / np.log2(sigma)
            return radius * sigma ** np.ceil(e)
        else:
            return radius * sigma

    def has_converged(
        self,
        trustworthiness: float | None,
        relative_step_norm: float | None,
    ) -> bool | NoReturn:
        """Check if the trust region problem has converged.

        Parameters
        ----------
        trustworthiness : float | None
            Trustworthiness of the model.
        relative_step_norm : float | None
            Norm of the step, relative to the norm of the optimization point.

        Returns
        -------
        bool
            True if the model has converged.

        Raises
        ------
        TrustRegionStepRejectedException
            If the trust region method has failed to compute a valid step.
        """
        if trustworthiness is None or relative_step_norm is None:
            return False
        if self.has_failed(trustworthiness, relative_step_norm):
            assert self.radius is not None
            raise TrustRegionStepRejectedException(
                trustworthiness, relative_step_norm, self.step_tolerance, self.radius
            )
        return trustworthiness > 0

    def iterate(
        self, point: VectorType
    ) -> tuple[VectorType, float, float, float | None]:
        """Perform one iteration.

        Starting from `point`, a `step` towards a new point is computed inside the trust
        region.

        Parameters
        ----------
        point : VectorType
            The current optimization point from which to start.

        Returns
        -------
        step : VectorType
            The step towards the new point within the trust region, starting from
            `point`.
        new_cost : float
            Objective function value in the new point, i.e., ``point + step``.
        new_radius : float
            The updated radius based on the trustworthiness of the model in the current
            `point`.
        trustworthiness : float | None
            The trustworthiness of the model in the current `point`. Can be None if
            the trust region solver does not perform any iterations.

        Raises
        ------
        TrustRegionInvalidUpdateException
            If the radius update method did not decrease the radius when a step was not
            accepted.
        TrustRegionInvalidUpdateException
            No suitable step is found within the specified number of trust region
            iterations.
        """
        assert self.radius is not None
        radius = self.radius
        step = np.zeros(self.point.shape)
        cost = self.problem._fval
        previous_radius = np.inf
        iterations = 0

        trustworthiness = None
        relative_step_norm = np.inf
        new_cost = np.inf
        while not self.has_converged(trustworthiness, relative_step_norm):
            if radius >= previous_radius:
                raise TrustRegionInvalidUpdateException(
                    f"radius did not decrease from {self.radius:.3e} to {radius:.3e} "
                    f"even though the step is not accepted ({trustworthiness = :.3e}; "
                    f"check update_radius."
                )
            if iterations >= self.max_inner_iterations:
                raise TrustRegionInvalidUpdateException(
                    f"no valid step found within {self.max_inner_iterations} inner "
                    f"trust region iterations"
                )
            previous_radius = radius

            step, predicted_improvement = self.minimize_plane(
                point,
                self.problem._gradient,
                self.problem._step,
                radius,
                cost,
                self.problem._curvature,
            )
            if predicted_improvement > 0:
                trustworthiness, new_cost = self.compute_trustworthiness(
                    step, cost, predicted_improvement
                )
            else:
                trustworthiness, new_cost = -np.inf, cost
            radius = self.update_radius(radius, trustworthiness, step)
            relative_step_norm = self.compute_relative_step(point, step)
            iterations += 1

        self.radius = radius
        return step, new_cost, radius, trustworthiness

    def __call__(
        self, point: VectorType
    ) -> tuple[VectorType, OptimizationProgressLogger]:
        """Run the outer optimization algorithm.

        Parameters
        ----------
        point : VectorType
            The initial guess for the variables, serialized.

        Returns
        -------
        VectorType
            The result of the optimization algorithm.
        OptimizationProgressLogger
            A log containing information on the optimization process.
        """
        cost_initial = self.problem.compute_objective(point)
        self.point = point.copy()
        self.log.log_init(self.point, cost_initial)
        self.printer.print_iteration()
        if self.radius is None:
            self.radius = 0.3 * max(1.0, cast(float, tlb.norm(point)))
        assert self.radius is not None

        if len(self.log.stopping_criteria) == 0:
            raise ValueError("log does not contain stopping criteria")

        while not self.log.check_termination():
            # Compute unrestricted step.
            step, info = self.problem.compute_step(self.point)

            try:
                # Compute step in trust region.
                step, cost, radius, trustworthiness = self.iterate(self.point)
                if (
                    self.point.dtype == np.float64
                    and step.dtype == np.complex128
                    and all(np.isreal(step))
                ):
                    self.point += step.real
                else:
                    self.point += step
                self.log.log(
                    self.point,
                    cost,
                    radius=radius,
                    trustworthiness=trustworthiness,
                    **info,
                )
            except TrustRegionStepRejectedException as e:
                self.log.log(
                    self.point,
                    self.log.fval[-1],
                    trustworthiness=e.trustworthiness,
                    radius=e.radius,
                    **info,
                )
                criterion = StoppingCriterionCustom(
                    "failed to find suitable step", str(e), test=lambda _: True
                )
                self.log.reason_termination = criterion
                self.printer.print_iteration()
                break
            except (ComplexCurvatureException, TrustRegionInvalidUpdateException) as e:
                criterion = StoppingCriterionCustom(
                    "failed to find suitable step", str(e), test=lambda _: True
                )
                self.log.reason_termination = criterion
                break

            self.printer.print_iteration()

        self.printer.print_termination()
        return self.point, self.log


@dataclass
class OptimizationOptions(Options):
    """Options for an optimization algorithm."""

    tol_relfval: NonnegativeFloat = 1e-12
    """Tolerance on the relative objective function value change.

    The relative change is computed as::
    
        (cost(previous_point) - cost(current_point)) / cost(initial_point)
    """

    tol_absfval: NonnegativeFloat | None = None
    """Tolerance on the objective function value in the current point."""

    tol_relstep: NonnegativeFloat = 1e-6
    """Tolerance on the relative step size.

    The relative step size is computed as::

        norm(step) / norm(point)
    """

    max_iterations: NonnegativeInt = 200
    """Maximum number of iterations."""


def minimize_trust_region(
    problem: CurvatureProblem[PointType],
    point: PointType,
    plane_search: PlaneSearchFcn | None = None,
    options: OptimizationOptions | None = None,
    *,
    log: OptimizationProgressLogger | None = None,
    extra_stopping_criteria: Sequence[StoppingCriterion] | None = None,
    stopping_criteria_protocol: Literal["append"] | Literal["replace"] = "append",
    printer: ProgressPrinter | None = None,
) -> tuple[PointType, OptimizationProgressLogger]:
    r"""Minimize an unconstrained optimization problem using the trust region method.

    An unconstrained optimization problem::

        minimize f(z)

    is solved for the variables ``z``. In each step, the current variables, which are
    referred to as `point`, are updated via a trust region subproblem. The actual
    computations are defined in `problem`, which contains implementations for, e.g., the
    function value, gradient and Hessian, depending on the type of the problem. The
    trust region problem is solved using the method defined by `plane_search`. The
    variables can be given in any format, provided suitable serialization and
    deserialization methods are provided in `problem`.

    Parameters
    ----------
    problem : CurvatureProblem[PointType]
        The optimization problem to be solved. The problem defines a way to compute the
        objective function value, the gradient, the step and the curvature.
    point : PointType
        The initial guess for the optimization variables. These variables can be given
        in any format, provided suitable (de)serialization functions are provided in
        `problem`.
    plane_search : PlaneSearchFcn, default = minimize_dogleg
        Function solving the plane search problem with respect to the trust region.
    options : OptimizationOptions, default = OptimizationOptions()
        Options for solver, e.g., stopping criteria.
    log : OptimizationProgressLogger, optional
        Logger containing information on the stopping criteria. The logger also stores
        information during the optimization process. By default, an empty logger is
        created with stopping criteria based on `options`.
    extra_stopping_criteria : Sequence[StoppingCriterion], optional
        Add extra stopping criteria to `log`.
    stopping_criteria_protocol: "append" | "replace", default = "append"
        Protocol to use when `extra_stopping_criteria` are used. If "append", the list
        is append to the ones already defined in `log`. If "replace", the stopping
        criteria in `log` are overwritten. This can be useful to override the default
        stopping criteria defined by `options`.
    printer : ProgressPrinter, default = ProgressPrinter()
        Printer that display the information in `log` every iteration or fewer.

    Returns
    -------
    PointType
        The result of the optimization algorithm.
    OptimizationProgressLogger
        Logged information during the optimization algorithm as well as stopping
        conditions.

    Examples
    --------
    To compute the best rank-1 approximation of a matrix in least squares sense, the
    following optimization problem can be formulated:

    .. math::
        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F}.

    To solve this problem with a quasi-Newton-type method, the problem is defined first:

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

    For the overall algorithm, the algorithm is stopped after three iterations.

    .. code-block:: python

        >>> options = tl.optimization.OptimizationOptions(max_iterations=3)
        >>> z_res, info = tl.minimize_trust_region(problem, z_init, options=options)
            iter         fval     rel fval     rel step
           max=3

               0    1.304e+00
               1    7.125e-01    4.535e-01    3.000e-01
               2    3.760e-02    5.177e-01    5.915e-01
               3    9.326e-05    2.877e-02    8.348e-02

        algorithm minimize_trust_region has stopped (see reason_termination):
            number of iterations exceeds maximum: 3 >= 3

        data fields:
            niterations : 3
            fval : [..., 9.3260e-05]
            relative_fval : [..., 0.0288]
            relative_step : [..., 0.0835]
            normgrad : []

        other fields:
            stopping_criteria, zp, algorithm, reason_termination
    """
    if options is None:
        options = OptimizationOptions()
    if plane_search is None:
        plane_search = minimize_dogleg
    if printer is None:
        printer = ProgressPrinter()

    stopping_criteria: list[StoppingCriterion] = default_stopping_criteria(
        tol_relfval=options.tol_relfval,
        tol_absfval=options.tol_absfval,
        tol_relstep=options.tol_relstep,
        max_iter=options.max_iterations,
    )

    if extra_stopping_criteria is not None:
        if stopping_criteria_protocol == "append":
            stopping_criteria.extend(extra_stopping_criteria)
        else:
            stopping_criteria = list(extra_stopping_criteria)

    if log is None:
        log = OptimizationProgressLogger(
            minimize_trust_region,
            stopping_criteria=stopping_criteria,
            terminate_with_exception=False,
        )
    else:
        log.terminate_with_exception = False
        if log.algorithm is None:
            log.algorithm = minimize_trust_region
        if not log.stopping_criteria:
            log.stopping_criteria = stopping_criteria

    log.add_custom_list_field("rho", "trustworthiness", replace=True)
    log.add_custom_list_field("delta", "radius", replace=True)
    field_rho = PrinterField("rho", "rho", 11, ".6f", "s", "")
    field_delta = PrinterField("delta", "delta", 12, ".3e", "s", "")
    printer.append_field(field_rho)
    printer.append_field(field_delta)
    printer.add_logger(log)

    assert plane_search is not None
    optimizer = TrustRegionOptimizer(
        problem, plane_search, log, printer, step_tolerance=options.tol_relstep
    )
    result, log = optimizer(problem._serialize(point))
    return problem._deserialize(result), log

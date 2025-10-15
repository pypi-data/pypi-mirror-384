"""Logging and stopping criteria for optimization routines.

This module provides a logger :class:`OptimizationProgressLogger` that tracks the
progress of an optimization algorithm through different variables such as objective
function value, step size and any custom metric required for the problem at hand. It
also collects the various stopping criteria in use for the optimization problem and
can check if these are satisfied based on the current values.

Classes
-------
OptimizationProgressLogger
    Log progress information for optimization methods.
StoppingCriterion
    Generic stopping criterion for optimization algorithms.
StoppingCriterionTolerance
    Tolerance-based stopping criterion for optimization algorithms.
StoppingCriterionCustom
    Custom stopping criterion for optimization algorithms (useful to create custom
    stopping criteria without needing to define a subclass of StoppingCriterion).
StoppingCriterionAlgorithm
    Criterion used when the underlying solver decides to stop.
StoppingCriterionReached
    Exception raised when a stopping criterion is satisfied. This exception is useful to
    exit methods that do not allow custom stopping criteria.
TerminationMessage
    Signature for a termination message.
LoggedField
    Field storing a value that is logged.

Routines
--------
default_stopping_criteria
    Return list of commonly used stopping criteria. Which criteria are returned depends
    on the arguments supplied to this function.

Examples
--------
To create a custom logger with an additional field, a subclass of
:class:`OptimizationProgressLogger` can be created. For example, in each iteration the
absolute value of each variable can be stored as a list of floats in `custom_field`:

>>> import numpy as np
>>> from dataclasses import dataclass, field
>>> from pytensorlab.optimization.logger import (
...     OptimizationProgressLogger,
...     StoppingCriterionTolerance,
...     StoppingCriterionCustom,
...     StoppingCriterion
... )
>>> @dataclass
... class CustomLogger(OptimizationProgressLogger):
...     custom_field: list[list[float]] = field(default_factory=list)

This `custom_field` should be updated externally if other information than the current
iterate `z` or function value `fval` is needed, otherwise, `log` can be overwritten in
`CustomLogger` (this is a method in the `CustomLogger` class defined above):

>>> def log(self, z, fval):
...     super().log(z, fval) # do not forget to call the superclass.
...     self.custom_field.append([abs(value) for value in z])

The `custom_field` can be used to create a new type of stopping criterion, e.g., the
maximal value for the last iterate should be smaller than a certain value. First, the
test function is created:

>>> def custom_stop(log: CustomLogger) -> bool:
...     return max(log.custom_field[-1]) > 10

The stopping criterion is then created as:

>>> @dataclass(frozen=True) # frozen=True is required here.
>>> class MyStoppingCriterion(StoppingCriterion):
...     def issatisfied(self, log):
...         return True

>>> msg = lambda criterion, log, value: (
...     f"maximal absolute value {max(value)} exceeds 10"
... )
>>> criterion = MyStoppingCriterion("maxiter", msg)
>>> custom_criterion = StoppingCriterionCustom(
...    "description of custom criterion",
...    termination_message=lambda criterion, log, value: (
...        f"criterion met: {max(value)} > 10"
...    ),
...    test=custom_stop
... )

The logger can be used in the optimization algorithm as follows:

>>> algorithm = lambda: None # dummy algorithm
>>> z = np.ones((1,)) # initialization
>>> fval = 1 # function value in initialization
>>> logger = CustomLogger(algorithm, stopping_criteria=[custom_criterion])
>>> logger.log_init(z, fval)
>>> logger.log(z, fval) # log in the optimization loop
>>> logger.check_termination() # returns True if `custom_stop` is True
True

If `log` is not overwritten, the value in the current loop should be added manually,
right after the call to `log`:

>>> logger.custom_field.append(0.5)

If a stopping criterion is satisfied, the `reason_termination` attribute is set to this
stopping criterion. If multiple stopping criteria are satisfied at the same time, the
first one in the list `stopping_criteria` is used.

The `custom_criterion` criterion can be implemented using
:class:`.StoppingCriterionTolerance` as well:

>>> custom_criterion = StoppingCriterionTolerance(
...     "description of custom criterion",
...     termination_message=lambda criterion, log, value: (
...         f"criterion met: {value} <= {criterion.tolerance}"
...     ),
...     field="custom_field",
...     tolerance=10,
... )

By default, :class:`.StoppingCriterionTolerance` tests if the final value is smaller
than or equal to the tolerance. Other tests, e.g., handling an array of final values,
can be created using the `compare` attribute:

>>> custom_criterion = StoppingCriterionTolerance(
...     "description of custom criterion",
...     termination_message="some message",
...     field="custom_field",
...     compare=lambda value, tolerance: np.max(value) >= tolerance,
...     tolerance=10,
... )
"""

from __future__ import annotations

import math
import operator
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass, field, fields
from textwrap import dedent
from typing import (
    Any,
    Protocol,
    TypeVar,
    cast,
)

import numpy as np

import pytensorlab.backends.numpy as tlb
from pytensorlab.typing import ArrayType
from pytensorlab.util.utils import SerializableT, _serialize, is_serializable


def default_stopping_criteria(
    *,
    tol_relfval: float | None = None,
    tol_absfval: float | None = None,
    tol_relstep: float | None = None,
    tol_normgrad: float | None = None,
    tol_subspace: float | None = None,
    max_iter: int | None = None,
    max_radius_updates: int | None = None,
) -> list[StoppingCriterion]:
    """Return list of default stopping criteria.

    Parameters
    ----------
    tol_relfval : float, optional
        Tolerance on the function value relative to the initial function value.
    tol_absfval : float, optional
        Tolerance on the absolute function value.
    tol_relstep : float, optional
        Tolerance on the step size relative to the norm of the current variables.
    tol_normgrad : float, optional
        Tolerance on the norm of the gradient.
    tol_subspace : float, optional
        Tolerance on the maximal angle between subspaces.
    max_iter : int, optional
        Upper bound on the number of iterations.
    max_radius_updates : int, optional
        Upper bound on the number of trust region steps.

    Returns
    -------
    list[StoppingCriterion]
        A list of stopping criteria for all the parameters that are given and not set to
        None.
    """
    criteria: list[StoppingCriterion] = []
    if tol_relfval is not None:
        criteria.append(
            StoppingCriterionTolerance(
                description=(
                    "stop if the last relative function value is below a threshold"
                ),
                termination_message=lambda criterion, _, value: (
                    f"relative function value is smaller than tolerance: "
                    f"{value:.6e} <= "
                    f"{cast(StoppingCriterionTolerance, criterion).tolerance}"
                ),
                field="relative_fval",
                tolerance=tol_relfval,
            )
        )
    if tol_absfval is not None:
        criteria.append(
            StoppingCriterionTolerance(
                description=(
                    "stop if the last absolute function value is below a threshold"
                ),
                termination_message=lambda criterion, _, value: (
                    f"absolute function value is smaller than tolerance: "
                    f"{value:.6e} <= "
                    f"{cast(StoppingCriterionTolerance, criterion).tolerance}"
                ),
                field="fval",
                tolerance=tol_absfval,
            )
        )
    if tol_relstep is not None:
        criteria.append(
            StoppingCriterionTolerance(
                description="stop if the last relative step size is below a threshold",
                termination_message=lambda criterion, _, value: (
                    f"relative step size is smaller than tolerance: "
                    f"{value:.6e} <= "
                    f"{cast(StoppingCriterionTolerance, criterion).tolerance}"
                ),
                field="relative_step",
                tolerance=tol_relstep,
            )
        )
    if tol_normgrad is not None:
        criteria.append(
            StoppingCriterionTolerance(
                description="stop if the the norm of the gradient is below a threshold",
                termination_message=lambda criterion, _, value: (
                    f"norm of gradient is smaller than tolerance: {value} "
                    f"<= {cast(StoppingCriterionTolerance, criterion).tolerance}"
                ),
                field="normgrad",
                tolerance=tol_normgrad,
            )
        )
    if tol_subspace is not None:
        criteria.append(
            StoppingCriterionTolerance(
                description=(
                    "stop if the maximal angle between subspaces is below a "
                    "threshold"
                ),
                termination_message=lambda criterion, _, value: (
                    f"maximal angle between subspaces is smaller than tolerance: "
                    f"{np.max(value):.6e} <= "
                    f"{cast(StoppingCriterionTolerance, criterion).tolerance}"
                ),
                field="max_subspace_angle",
                tolerance=tol_subspace,
            )
        )
    if max_iter is not None:
        criteria.append(
            StoppingCriterionTolerance(
                description="stop if the number of iterations exceeds the maximum",
                termination_message=lambda criterion, _, value: (
                    f"number of iterations exceeds maximum: "
                    f"{value} >= "
                    f"{cast(StoppingCriterionTolerance, criterion).tolerance}"
                ),
                field="niterations",
                tolerance=max_iter,
                compare=lambda value, tolerance: value >= tolerance,
            )
        )
    if max_radius_updates is not None:
        criteria.append(
            StoppingCriterionTolerance(
                description=(
                    "stop if the number of trust region steps exceeds the maximum"
                ),
                termination_message=lambda criterion, _, value: (
                    f"number of trust region steps exceeds maximum: "
                    f"{value} >= "
                    f"{cast(StoppingCriterionTolerance, criterion).tolerance}"
                ),
                field="tr_counter",
                tolerance=max_radius_updates,
                compare=lambda value, tolerance: value >= tolerance,
            )
        )
    return criteria


class LoggedField(Protocol):
    """Field storing a value that is logged."""

    value: Any
    """Value to be logged."""

    def log(
        self, logger: OptimizationProgressLogger, point: SerializableT, /, **kwargs: Any
    ) -> None: ...

    """Log a value.

    Parameters
    ----------
    logger : OptimizationProgressLogger
        Logger to which this field is added. Information from this logger can be used to
        compute the logged value for this field.
    point : SerializableT
        The current point in the optimization routine.
    **kwargs
        Extra arguments to compute the value for this logged field.
    """


def _format_field(var: Any):
    """Format a variable based on its type and properties."""
    if isinstance(var, float):
        # Determine formatting based on magnitude.
        if abs(var) >= 1e5 or (abs(var) > 0 and abs(var) < 1e-4):
            return f"{var:.4e}"  # scientific notation
        else:
            return f"{var:.4f}".rstrip("0").rstrip(".")  # Trim trailing zeroes and dot.
    elif isinstance(var, str):
        return repr(var)
    else:
        # Formatting defined by string representation.
        return str(var)


def _compact_str(
    name: str, field: Any, symb: str = " : ", endline: str = "\n", full: bool = False
) -> str:
    """Create a compact printable string for a field."""
    if field is None:
        return f"    {name}{symb}None{endline}"

    elif isinstance(field, str):
        return f"    {name}{symb}{_format_field(field)}{endline}"

    elif isinstance(field, Sequence):
        if len(field) == 0:
            return f"    {name}{symb}[]{endline}"
        elif len(field) == 1:
            return f"    {name}{symb}[{_format_field(field[-1])}]{endline}"
        else:
            if full:
                values = ",\n        ".join([f"{_format_field(x)}" for x in field])
                return f"    {name}=[\n        {values},\n    ]{endline}"
            else:
                return f"    {name}{symb}[..., {_format_field(field[-1])}]{endline}"

    elif isinstance(field, Mapping):
        if len(field) == 0:
            return f"    {name}{symb}{{}}{endline}"
        elif len(field) == 1:
            key = _format_field(list(field.keys())[-1])
            value = _format_field(list(field.values())[-1])
            return f"    {name}{symb}{{{key}: {value}}}{endline}"
        else:
            if len(field) <= 5 or full:
                keyvals = ",\n        ".join(
                    [
                        f"{_format_field(x[0])}: {_format_field(x[1])}"
                        for x in field.items()
                    ]
                )
                return f"    {name}{symb}{{\n        {keyvals},\n    }}{endline}"
            else:
                items = list(field.items())
                keyvals = ",\n        ".join(
                    [
                        f"{_format_field(items[i][0])}: {_format_field(items[i][1])}"
                        for i in range(5)
                    ]
                )
                keyvals_dots = ",\n        ".join([keyvals, "..."])
                return f"    {name}{symb}{{\n        {keyvals_dots}\n    }}{endline}"

    else:
        return f"    {name}{symb}{_format_field(field)}{endline}"


IGNORED_PROGRESS_LOGGER_FIELDS = {
    "algorithm",
    "zp",
    "custom_fields",
    "reason_termination",
    "stopping_criteria",
    "terminate_with_exception",
    "_data_fields",
}


@dataclass
class OptimizationProgressLogger:
    """Log progress information for optimization methods."""

    algorithm: Callable[..., Any]
    """Algorithm being logged."""

    zp: ArrayType | None = None
    """Previous iterate."""

    niterations: int = 0
    """Number of iterations."""

    fval: list[float] = field(default_factory=list)
    """Function value."""

    relative_fval: list[float] = field(default_factory=list)
    """Function difference relative to the first function value."""

    relative_step: list[float] = field(default_factory=list)
    """Step size relative to the norm of the initialization."""

    custom_fields: MutableMapping[str, LoggedField] = field(default_factory=dict)
    """Custom logged fields."""

    normgrad: list[float] = field(default_factory=list)
    """Norm of the gradient."""

    reason_termination: StoppingCriterion | None = None
    """Reason for termination.

    Stopping criterion that triggered termination; None if not terminated.
    """

    stopping_criteria: Sequence[StoppingCriterion] = field(default_factory=list)
    """List of stopping criteria to check."""

    terminate_with_exception: bool = False
    """Throw a StoppingCriterionReached exception on termination.

    If `check_termination` is called, the function returns true if one of the stopping
    criteria is fulfilled. If `terminate_with_exception` is set to True, a
    `StoppingCriterionReached` exception will be thrown instead. This is required for
    some optimization solvers.
    """

    _data_fields: set[str] = field(default_factory=set, init=False)
    """Names of data fields.

    Cached for efficiency.
    """

    def __post_init__(self) -> None:
        data_fields = {f.name for f in fields(self)}
        self._data_fields = data_fields - IGNORED_PROGRESS_LOGGER_FIELDS

    def log_init(self, z0: SerializableT, fval0: float) -> None:
        """Log the initialization.

        Log the value of the initialization `z0` and the function value `fval0` at
        `z0`. This function should be called before first optimization step is taken, as
        the iteration counter `niterations` is not increased.

        Parameters
        ----------
        z0 : SerializableT
            Initialization of the algorithm.
        fval0 : float
            Objective function value at the initialization.
        """
        assert is_serializable(z0)
        self.zp = _serialize(z0).copy()
        self.fval.append(fval0)

    def log(self, z: SerializableT, fval: float, **kwargs: Any) -> None:
        """Log current iteration.

        Stores the current iterate and the objective function value and computes the
        relative change in function value and the relative step size. `niterations` is
        increased by 1.

        Parameters
        ----------
        z : SerializableT
            The current iterate, i.e., the values of the optimization variables after
            this iteration.
        fval: float
            Objective function value at the current iterate.
        """
        self.niterations += 1
        self.fval.append(fval)
        if len(self.fval) < 2:
            raise ValueError(
                "not enough function values (fval) to compute relative_fval; "
                "call log_init first"
            )
        if math.isfinite(fval) and math.isfinite(self.fval[-2]):
            res = self.fval[-2] - self.fval[-1]
            if self.fval[0] == 0:
                res = 0 if res == 0 else np.inf
            else:
                res /= self.fval[0]
            self.relative_fval.append(res)
        else:
            self.relative_fval.append(np.nan)
        assert self.zp is not None
        self.relative_step.append(
            tlb.norm(_serialize(self.zp) - _serialize(z))
            / tlb.norm(_serialize(self.zp))
        )
        for custom_field in self.custom_fields.values():
            custom_field.log(self, z, **kwargs)
        self.zp = _serialize(z).copy()

    def check_termination(self) -> bool:
        """Check termination criteria."""
        for criterion in self.stopping_criteria:
            if criterion.issatisfied(self):
                self.reason_termination = criterion
                if self.terminate_with_exception:
                    raise StoppingCriterionReached
                return True
        return False

    def __repr__(self) -> str:
        """Create readable text representation."""
        text = f"{type(self).__name__}(\n"
        if self.reason_termination is not None:
            termination_message = self.reason_termination.message(self)
        else:
            termination_message = None

        if self.zp is not None:
            zp_type = f"<{type(self.zp).__name__} at {id(self.zp):#018x}>"
        else:
            zp_type = None

        text += ",\n".join(
            [
                f"    algorithm={self.algorithm!r}",
                _compact_str(
                    "stopping_criteria", self.stopping_criteria, "=", "", full=True
                ),
                f"    reason_termination={termination_message!r}",
                f"    terminate_with_exception={self.terminate_with_exception!r}",
                f"    niterations={self.niterations!r}",
                f"    zp={zp_type}",
                _compact_str("fval", self.fval, "=", ""),
                _compact_str("relative_fval", self.relative_fval, "=", ""),
                _compact_str("relative_step", self.relative_step, "=", ""),
                _compact_str("normgrad", self.normgrad, "=", ""),
                _compact_str("custom_fields", self.custom_fields, "=", "", full=True),
                ")",
            ]
        )

        return text

    def __str__(self) -> str:
        """Create string representation."""
        if self.reason_termination:
            text = f"algorithm {self.algorithm.__name__} has stopped "
            text += "(see reason_termination): \n    "
            text += self.reason_termination.message(self)
        else:
            text = f"algorithm {self.algorithm.__name__} has not stopped "

        nondatafields = (
            "stopping_criteria",
            "zp",
            "algorithm",
            "reason_termination",
        )

        text += "\n\ndata fields:\n"
        for f in fields(self):
            if f.name in IGNORED_PROGRESS_LOGGER_FIELDS:
                continue
            if f.name.startswith("_"):  # ignore private fields
                continue
            text += _compact_str(f.name, getattr(self, f.name))

        if self.custom_fields:
            for name, field in self.custom_fields.items():
                text += _compact_str(name, field.value)

        text += "\nother fields:\n    "
        text += ", ".join(nondatafields)

        return text

    def __getattr__(self, name: str) -> Any:
        try:
            return self.custom_fields[name].value
        except KeyError:
            raise AttributeError(
                f"{self.__class__.__name__} object has no attribute {name}"
            )

    def fields(self) -> set[str]:
        return self._data_fields.union(set(self.custom_fields))

    def add_custom_list_field(self, name: str, key: str, replace: bool = False) -> None:
        """Add a custom field for a list of values.

        A custom log field with the given `name` is added to this logger. When `log` is
        called, the value corresponding to `key` is added to the list of values.

        Parameters
        ----------
        name : str
            Name of the value to be logged.
        key : str
            Key in the kwargs dictionary provided to `log` corresponding to the value to
            be logged.
        replace : bool, default=False
            If False, raise an exception if a field with name `name` is already present.

        Raises
        ------
        KeyError
            If a custom field with name `name` already exists (and `replace` is False).
        """
        if not replace and name in self.custom_fields:
            raise KeyError(f"custom field with name {name} already exists")

        @dataclass
        class Field:
            value: list[Any] = field(default_factory=list)

            def log(
                self,
                logger: OptimizationProgressLogger,
                point: SerializableT,
                /,
                **kwargs: Any,
            ) -> None:
                self.value.append(kwargs.get(key, None))

            def __str__(self) -> str:
                return dedent(_compact_str("", self.value, "", ""))

        self.custom_fields[name] = Field()


class StoppingCriterionReached(Exception):
    """Stopping criterion reached."""

    pass


LoggerType = TypeVar("LoggerType", bound=OptimizationProgressLogger, contravariant=True)
"""OptimizationProgressLogger or one of its subclasses.

See Also
--------
OptimizationProgressLogger
"""


_T = TypeVar("_T", bound=float)


class _ComparableFcn(Protocol):
    """A callable that compares two numbers."""

    def __call__(self, value: _T, tolerance: _T, /) -> bool:
        """Compare two numbers."""
        ...


class _CriterionFcn(Protocol[LoggerType]):
    """A callable that checks if a stopping criterion is satisfied."""

    def __call__(self, log: LoggerType, /) -> bool:
        """Check if a stopping criterion is satisfied.

        Parameters
        ----------
        log : LoggerType
            The logger collecting the necessary stopping criteria and values to
            determine if the criterion is satisfied.

        Returns
        -------
        bool
            True if the criterion is satisfied.
        """
        ...


def _getfinal(log: Any, field: str) -> Any:
    """Extract value from field or final value in list."""
    try:
        value = getattr(log, field)
    except AttributeError:
        try:
            value = log.custom_fields[field]
        except KeyError:
            raise ValueError(f"log does not have an attribute or custom field {field}")
    try:
        if len(value) == 0:
            return None
        value = value[-1]
    except TypeError:
        pass
    return value


class TerminationMessage(Protocol):
    """Signature for a termination message."""

    def __call__(
        self,
        criterion: StoppingCriterion,
        log: OptimizationProgressLogger,
        value: Any,
        /,
    ) -> str:
        """Return formatted termination message.

        Parameters
        ----------
        criterion : StoppingCriterion
            Stopping criterion that has this message.
        log : OptimizationProgressLogger
            Logger containing the optimization progress used to format this message.
        value : float
            Value that triggered the stopping criterion.

        Returns
        -------
        str
            Formatted termination message.
        """
        ...


@dataclass(frozen=True)
class StoppingCriterion:
    """Stopping criterion for optimization algorithms."""

    description: str
    """Text description of the criterion."""

    termination_message: str | TerminationMessage
    """Message printed if the criterion is met.

    The message can either be a string, or a function returning a string. This function
    should accept the following arguments:
    
    - `criterion`: this criterion
    - `log`: the optimization logger
    - `value`: the final value of the logger, if applicable, otherwise None.

    See Also
    --------
    message

    Examples
    --------
    The following message extracts the number of iterations from the log:

    >>> from pytensorlab.optimization.logger import (
    ...     dataclass, 
    ...     OptimizationProgressLogger,
    ...     StoppingCriterion
    ... )
    >>> @dataclass(frozen=True)
    ... class MyStoppingCriterion(StoppingCriterion):
    ...     def issatisfied(self, log):
    ...         return True
   
    >>> msg = lambda criterion, log, value: (
    ...     f"number of iterations {log.niterations} exceeds maximum"
    ... )
    >>> criterion = MyStoppingCriterion("maxiter", msg) 
    >>> log = OptimizationProgressLogger(lambda x: x, stopping_criteria=[criterion])
    >>> criterion.message(log)
    number of iterations 0 exceeds maximum
    """

    def issatisfied(self, log: OptimizationProgressLogger) -> bool:
        """Check if the criterion is satisfied.

        Parameters
        ----------
        log : OptimizationProgressLogger
            Log containing information to decide if the criterion is satisfied.

        Returns
        -------
        bool
            True if the criterion is satisfied.
        """
        return False

    def message(self, log: OptimizationProgressLogger) -> str:
        """Return formatted termination message.

        Uses the format string in `termination_message` to create a termination
        message. The fields `log` and `criterion` are set.

        Parameters
        ----------
        log : OptimizationProgressLogger
            Log containing optimization information.

        Returns
        -------
        str
            Formatted termination message if this criterion is satisfied; otherwise, the
            default unsatisfied message is returned.
        """
        if not self.issatisfied(log):
            return "criterion not satisfied"
        if isinstance(self.termination_message, str):
            return self.termination_message
        return self.termination_message(self, log, None)

    def __str__(self) -> str:
        return self.description


@dataclass(frozen=True)
class StoppingCriterionTolerance(StoppingCriterion):
    """Tolerance-based stopping criterion for optimization algorithms.

    The criterion takes the value or last logged value from the `field` attribute in the
    log and compares this value to the `tolerance` using the `compare` function. This
    function should return True if the criterion is satisfied.
    """

    field: str
    """Field to be used in the log."""

    tolerance: float
    """Tolerance to use in the test."""

    compare: _ComparableFcn = operator.le
    """Function used to compare value and tolerance.

    Default is the less than or equal to function :func:`operator.le`.
    """

    def issatisfied(self, log: OptimizationProgressLogger) -> bool:
        """Check if the criterion is satisfied."""
        value = _getfinal(log, self.field)
        return value is not None and self.compare(value, self.tolerance)

    def message(self, log: OptimizationProgressLogger) -> str:
        """Return formatted termination message.

        Uses the format string in `termination_message` to create a termination message.
        The fields `log` and `criterion` are set. Additionally, the final values in
        `field` attribute of `log` are available as `value` and the `tolerance` is
        available as `tolerance`.

        Parameters
        ----------
        log : OptimizationProgressLogger
            Log containing optimization information.

        Returns
        -------
        str
            Formatted termination message if this criterion is satisfied; otherwise, the
            default unsatisfied message is returned.
        """
        if not self.issatisfied(log):
            return "criterion not satisfied"
        if isinstance(self.termination_message, str):
            return self.termination_message
        return self.termination_message(self, log, _getfinal(log, self.field))

    def __str__(self) -> str:
        return f"{self.description} ({self.tolerance})"


@dataclass(frozen=True)
class StoppingCriterionCustom(StoppingCriterion):
    """Custom stopping criterion for optimization algorithms.

    This auxiliary class allows to quickly create a criterion based on the `criterion`
    test function.
    """

    test: _CriterionFcn[OptimizationProgressLogger]
    """Test function for the criterion."""

    def issatisfied(self, log: OptimizationProgressLogger) -> bool:
        """Check if the criterion is satisfied."""
        return self.test(log)


@dataclass(frozen=True)
class StoppingCriterionAlgorithm(StoppingCriterion):
    """Criterion used when the underlying solver decides to stop.

    This criterion is meant to store the output result from an optimization solver if
    that solver exits and none of the pyTensorlab stopping criteria are satisfied. This
    class is therefore not meant to be used as an actual stopping criterion, but as a
    place holder.
    """

    output: Any
    """The output of the optimization solver."""

    def issatisfied(self, log: OptimizationProgressLogger) -> bool:
        """Check if the criterion is satisfied."""
        return True

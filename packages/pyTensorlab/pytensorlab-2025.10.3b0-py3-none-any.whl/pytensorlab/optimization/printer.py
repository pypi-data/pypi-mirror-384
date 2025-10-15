"""Class and utilities for printing the progress of an iterative routine.

The :class:`.ProgressPrinter` is a customizable printer for information in a
:class:`.PrintableLogger` instance. :class:`.ProgressPrinter` prints the values of
selected fields every x iterations and automatically inserts header and info lines if
requested. The (number) formatting for each field can be customized.

Classes
-------
PrintableLogger
    Log that can be printed.
PrinterField
    Field of a ProgressPrinter.
ProgressPrinter
    Customizable printer for iterative routines.
VoidPrinter
    Printer that does not produce output.

Routines
--------
conditional_printer
    Create a conditional printer.

Notes
-----
If a value in the printer exceeds the width in its corresponding :class:`.PrinterField`,
then it is cut off to this width. By default, the final character is replaced by "~" to
indicate that it has been cut off.

Examples
--------
The information that is printed can be specified using the `fields` argument. If
:data:`default_printer_fields` is used, the output of an example printer for an
iterative routine is:

>>> from pytensorlab.optimization.logger import default_stopping_criteria
>>> import pytensorlab as tl
>>> from pytensorlab.optimization import (
...     default_printer_fields,
...     OptimizationProgressLogger,
...     ProgressPrinter,
...     PrinterField
... )
>>> import numpy as np

>>> def example_routine(logger, printer):
...     fval = 1.732
...     z = np.ones((1,))
...     logger.log_init(z, fval)
...     printer.print_iteration()
...     while not logger.check_termination():
...         fval = fval / 10
...         z = z / 2
...         logger.log(z, fval)
...         printer.print_iteration()
...     printer.print_termination()

.. code-block:: python

    >>> logger = OptimizationProgressLogger(
    ...     example_routine,
    ...     stopping_criteria=default_stopping_criteria(
    ...         tol_relfval=1e-4, tol_relstep=1e-2, max_iter=10
    ...     ),
    ... )
    >>> printer = ProgressPrinter(default_printer_fields, logger)
    >>> example_routine(logger, printer)

      iter         fval     rel fval     rel step
    max=10               tol=1.0e-04  tol=1.0e-02

         0    1.732e+00
         1    1.732e-01    9.000e-01    5.000e-01
         2    1.732e-02    9.000e-02    5.000e-01
         3    1.732e-03    9.000e-03    5.000e-01
         4    1.732e-04    9.000e-04    5.000e-01
         5    1.732e-05    9.000e-05    5.000e-01

    algorithm example_routine has stopped (see reason_termination):
        relative function value is smaller than tolerance: 9.000000e-05 <= 0.0001

    data fields:
        niterations : 5
        fval : [..., 1.7320e-05]
        relative_fval : [..., 9.0000e-05]
        relative_step : [..., 0.5]
        normgrad : []

    other fields:
        stopping_criteria, zp, algorithm, reason_termination


:data:`default_printer_fields` consists of a list of :class:`PrinterField` objects. For
each :class:`PrinterField`, the printer prints one column. In this column, the printer
prints the corresponding values that are stored in the logger. Therefore, the logger
should contain a field that matches the `field` attribute of this :class:`PrinterField`
instance. Using the other attributes of :class:`PrinterField`, each column can be
customized individually:

.. code-block:: python

    >>> fields = [
    ...     PrinterField(
    ...         field="niterations",
    ...         title="iters",
    ...         width=20,
    ...         value_format="d",
    ...         info="extra info",
    ...         info_format="s",
    ...     ),
    ...     PrinterField(
    ...         field="fval",
    ...         title="objective function",
    ...         width=30,
    ...         value_format=".8e",
    ...         info_format=".5e", # formats the tolerance of the stopping criterion
    ...                            # associated with this field if info is not specified
    ...     ),
    ... ]
    >>> logger = OptimizationProgressLogger( # regenerate logger
    ...     example_routine,
    ...     stopping_criteria=default_stopping_criteria(
    ...         tol_relfval=1e-4, tol_relstep=1e-2, max_iter=10
    ...     ),
    ... )
    >>> printer = ProgressPrinter(fields, logger)
    >>> example_routine(logger, printer)

                 iters             objective function
            extra info

                     0                 1.73200000e+00
                     1                 1.73200000e-01
                     2                 1.73200000e-02
                     3                 1.73200000e-03
                     4                 1.73200000e-04
                     5                 1.73200000e-05

    algorithm example_routine has stopped (see reason_termination):
        relative function value is smaller than tolerance: 9.000000e-05 <= 0.0001

    data fields:
        niterations : 5
        fval : [..., 1.7320e-05]
        relative_fval : [..., 9.0000e-05]
        relative_step : [..., 0.5]
        normgrad : []

    other fields:
        stopping_criteria, zp, algorithm, reason_termination

Specify after how many iterations information should be printed using the `display`
argument of :class:`.ProgressPrinter`. Similarly, specify after how many printed
iterations the header should be repeated using the `header_repeat` argument:

.. code-block:: python

    >>> logger = OptimizationProgressLogger( # regenerate logger
    ...     example_routine,
    ...     stopping_criteria=default_stopping_criteria(
    ...         tol_relfval=1e-4, tol_relstep=1e-2, max_iter=10
    ...     ),
    ... )
    >>> printer = ProgressPrinter(fields, logger, display=2, header_repeat=2)
    >>> example_routine(logger, printer)

                     iters             objective function
                extra info

                         0                 1.73200000e+00
                         2                 1.73200000e-02

                     iters             objective function
                extra info

                         4                 1.73200000e-04
                         5                 1.73200000e-05

    algorithm example_routine has stopped (see reason_termination):
        relative function value is smaller than tolerance: 9.000000e-05 <= 0.0001

    data fields:
        niterations : 5
        fval : [..., 1.7320e-05]
        relative_fval : [..., 9.0000e-05]
        relative_step : [..., 0.5]
        normgrad : []

    other fields:
        stopping_criteria, zp, algorithm, reason_termination

"""

# ruff: noqa: T201

import re
import string
from collections.abc import Callable, Generator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import (
    Any,
    Protocol,
)

from pytensorlab.typing.validators import NonnegativeInt

from .logger import StoppingCriterion, StoppingCriterionTolerance, _getfinal


@dataclass(frozen=True)
class PrinterField:
    """Field of a `ProgressPrinter`.

    Parameters
    ----------
    field : str
        Name of the field in the `PrintableLogger` to be printed.
    title : str
        Title to be printed in the header for this column.
    width : int
        The width of this column.
    value_format : str
        Format specification string that determines the formatting of each value in this
        column. This format string can be constructed as described in
        https://docs.python.org/3/library/string.html#formatspec. Fill and align values
        are not allowed.
    info : str
        Extra information that is printed in the header under the title.
    info_format : str, optional
        Format specification string that determines the formatting of `info`.
    """

    field: str
    title: str
    width: int
    value_format: str
    info_format: str
    info: str | None = None


default_printer_fields: list[PrinterField] = [
    PrinterField("niterations", "iter", 8, "d", "d"),
    PrinterField("fval", "fval", 12, ".3e", ".1e"),
    PrinterField("relative_fval", "rel fval", 12, ".3e", ".1e"),
    PrinterField("relative_step", "rel step", 12, ".3e", ".1e"),
]
"""Default printer fields to be displayed when printing progress.

See Also
--------
PrinterField, ProgressPrinter
"""


ValueType = int | float | str | None


class NoneFormatter(string.Formatter):
    """String formatter that can handle None values.

    Parameters
    ----------
    missing_value : str, default = " "
        None values are replaced by multiple repetitions of `missing_value`.
    cutoff_char : str, default = "~"
        Formatted values that exceed their width, as specified in their corresponding
        format specifier, are cut off to this width. The final character is replaced by
        `cutoff_char`.
    """

    def __init__(self, missing_value: str = " ", cutoff_char: str = "~"):
        self.missing_value: str = missing_value
        self.cutoff_char: str = cutoff_char

    def get_value(
        self,
        key: int | str,
        args: Sequence[ValueType],
        kwargs: Mapping[str, ValueType],
    ) -> ValueType:
        """Return the value associated with key.

        Parameters
        ----------
        key : int | str
            Field name or index of a replacement field in a format string.
        args: Sequence[ValueType]
            Sequence of values.
        kwargs: Mapping[str, ValueType]
            Mapping containing field name and value pairs.

        Returns
        -------
        ValueType
            Value of the corresponding field. Returns None if no corresponding value is
            found in `kwargs`.

        Notes
        -----
        The :func:`get_value()` function in the standard `string.Formatter` throws
        an error when `key` is not present in `kwargs`. This function returns None
        instead.
        """
        if isinstance(key, str):
            return kwargs.get(key)
        return args[key]

    def format_field(self, value: ValueType, format_spec: str) -> str:
        """Format a value according to a format specification string.

        Parameters
        ----------
        value : ValueType
            Value to be formatted.
        format_spec : str
            Format specification string that determines the formatting of `value`.

        Returns
        -------
        str
            `value` formatted according to `format_spec`.

        Notes
        -----
        If `value` is None, then the function returns ``self.missing_value`` times the
        width, as specified in `format_spec`. If the width of the formatted value
        exceeds the specified width in `format_spec`, then it is cut off to this width
        and the last character is replaced by ``cutoff_char``.
        """
        # Get column width from format spec
        format_spec_width = format_spec.split(".", 1)[0]
        tmp_width = re.search(r"\d+", format_spec_width)
        if tmp_width is None:
            raise ValueError(f"no width specified in format spec {format_spec}")
        width = int(tmp_width.group())

        if value is None:
            return self.missing_value * width
        formatted_value = super().format_field(value, format_spec)
        if len(formatted_value) > width:
            return formatted_value[: width - 1] + self.cutoff_char
        else:
            return formatted_value


class PrintableLogger(Protocol):
    """Log that can be printed."""

    stopping_criteria: Sequence[StoppingCriterion]
    """Sequence of stopping criteria."""

    niterations: int
    """Number of iterations."""

    def __str__(self) -> str: ...

    def fields(self) -> set[str]: ...


@dataclass
class ProgressPrinter:
    """Customizable printer for iterative routines.

    A :class:`.ProgressPrinter` prints the values stored in a :class:`.PrintableLogger`,
    which, in turn, logs the progress of an iterative routine after each iteration.

    Parameters
    ----------
    fields : list[PrinterField]
        Specifies which attributes of `logger` are printed and the formats for the
        values and the header.
    logger : PrintableLogger, optional
        Log containing the values for each field that is printed. If `logger` is not yet
        available when an instance of `ProgressPrinter` is created, then `logger` can be
        added later using `add_logger`.
    display : NonnegativeInt, default = 1
        Progress is printed after every `display` iterations of the iterative routine.
    header_repeat : NonnegativeInt, default = 20
        The header, which contains the title for each field and additional information,
        is repeated after every `header_repeat` lines of values that are printed.
    """

    fields: list[PrinterField] = field(default_factory=default_printer_fields.copy)
    logger: PrintableLogger | None = None
    display: NonnegativeInt = 1
    header_repeat: NonnegativeInt = 20
    _fmt: NoneFormatter = field(default_factory=NoneFormatter, init=False)
    _last_iteration: int = -1

    def __post_init__(self) -> None:
        if self.logger:
            self.add_logger(self.logger)

        self._create_header_string()
        self._create_value_format()

    def _create_header_string(self) -> None:
        header_format: str = " ".join("{:>" + str(f.width) + "}" for f in self.fields)
        self.header_row: str = self._fmt.format(
            header_format, *[f.title for f in self.fields]
        )

    def _create_value_format(self) -> None:
        self.value_format: str = " ".join(
            "{" + f.field + ":>" + str(f.width) + f.value_format + "}"
            for f in self.fields
        )

    def _create_info_string(self) -> None:
        def tolerance_type(criterion: StoppingCriterionTolerance) -> str:
            """Determine the info field for a `StoppingCriterionTolerance`.

            Parameters
            ----------
            criterion: StoppingCriterionTolerance
                Stopping criterion with tolerance to determine the comparison of.

            Returns
            -------
            str
                Info field corresponding to the type of the `criterion`.
            """
            tolerance = criterion.tolerance
            if criterion.compare(tolerance - 1, tolerance):
                return "tol="
            if criterion.compare(tolerance + 1, tolerance) and isinstance(
                tolerance, int
            ):
                return "max="
            return ""

        if self.logger is None:
            raise ValueError("no logger provided to the printer")

        # For fields that do not have extra information specified and have a
        # StoppingCriterionTolerance associated with that field, the tolerance is
        # printed as extra information in the header.
        criteria: list[StoppingCriterionTolerance] = [
            c
            for c in self.logger.stopping_criteria
            if isinstance(c, StoppingCriterionTolerance)
        ]

        def info_values() -> Generator[tuple[str, str], None, None]:
            for f in self.fields:
                criterion = next((c for c in criteria if c.field == f.field), None)
                if f.info is not None:
                    yield f.field, f.info
                elif criterion is not None:
                    tolerance = ("{:" + f.info_format + "}").format(criterion.tolerance)
                    yield f.field, tolerance_type(criterion) + tolerance

        info = dict(info_values())
        if info:
            info_format: str = " ".join(
                f"{{{f.field}:>{str(f.width)}}}" for f in self.fields
            )
            self.info_row: str = self._fmt.format(info_format, **info)

    def append_field(self, field: PrinterField) -> None:
        """Append a new field to be printed.

        Parameters
        ----------
        field : PrinterField
            New field to be printed after the current last column.
        """
        self.insert_field(len(self.fields), field)

    def insert_field(self, index: int, field: PrinterField) -> None:
        """Insert a new field at a specific column.

        Parameters
        ----------
        index : int
            Column in which the new field is printed. All current fields at columns
            `index` and later are moved to the right.
        field : PrinterField
            New field to be printed.
        """
        self.fields.insert(index, field)
        self._create_header_string()
        self._create_value_format()
        if self.logger is not None:
            self.add_logger(self.logger)

    def add_logger(self, logger: PrintableLogger) -> None:
        """Add a printable logger to the printer.

        Parameters
        ----------
        logger: PrintableLogger
            The logger to add to this printer.

        Raises
        ------
        ValueError
            If a field in `self.fields` is not present in `logger`.
        """
        self.logger = logger
        logger_fields = logger.fields()
        fields_present: list[bool] = [f.field in logger_fields for f in self.fields]
        if not all(fields_present):
            raise ValueError(
                f"field {self.fields[fields_present.index(False)].field} not "
                f"an attribute of logger"
            )

        self._create_info_string()

    def print_header(self) -> None:
        """Print the header consisting of column titles and extra information.

        Raises
        ------
        ValueError
            If called before a `logger` has been added.
        """
        if self.logger is None:
            raise ValueError("no logger provided to the printer")

        if self.logger.niterations % (self.display * self.header_repeat) == 0:
            print()
            print(self.header_row)
            if hasattr(self, "info_row"):
                print(self.info_row)
            print()

    def print_iteration(self, force: bool = False) -> None:
        """Print a line of progress values for the current iteration.

        Parameters
        ----------
        force : bool, default = False
            Print iteration regardless of the iteration number if True.

        Raises
        ------
        ValueError
            If called before a `logger` has been added.
        """
        if self.logger is None:
            raise ValueError("no logger provided to the printer")

        self.print_header()
        # Print values
        if (force and self.display) or self.logger.niterations % self.display == 0:
            self._last_iteration = self.logger.niterations
            vals = {f.field: _getfinal(self.logger, f.field) for f in self.fields}
            print(self._fmt.format(self.value_format, **vals))

    def print_termination(self) -> None:
        """Print termination message.

        Raises
        ------
        ValueError
            If called before a `logger` has been added.
        """
        if self.logger is None:
            raise ValueError("no logger provided to the printer")

        if self.logger.niterations > self._last_iteration:
            self.print_iteration(force=True)
        print(f"\n{self.logger}\n")


class VoidPrinter(ProgressPrinter):
    """Printer that does not produce output.

    The main use of this printer is to suppress output from an iterative algorithm.

    See Also
    --------
    ProgressPrinter
    """

    def print_header(self) -> None:
        pass

    def print_iteration(self, force: bool = False) -> None:
        pass

    def print_termination(self) -> None:
        pass


def _void_printer(*args: Any, **kwargs: Any) -> None:
    pass


def conditional_printer(display: bool) -> Callable[..., None]:
    """Create a conditional printer.

    Parameters
    ----------
    display: bool
        Whether text should displayed by the printer or not.

    Returns
    -------
    Callable
        Either the print function if `display` is set to True or the _void_printer if
        set to False.
    """
    if display:
        return print
    return _void_printer

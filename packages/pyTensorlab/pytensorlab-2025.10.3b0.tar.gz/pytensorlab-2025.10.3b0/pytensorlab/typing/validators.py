"""Support for Annotated types with runtime checks.

Type hints can contain the :data:`typing.Annotated` type to add more involved validators
to certain types. For example, nonnegative integers can be expressed as::

    number : Annotated[int, Nonnegative()]

The :class:`Nonnegative()` validator ideally ensures that only nonnegative values can be
assigned. Unfortunately, static type checkers currently cannot run this validator. This
module provides runtime checking for `Annotated` types via the :func:`issubtype`
function, which returns True if both the type matches and the validators succeed, and a
:class:`TypeError` if the type does not match or a :class:`ValueError` if the value
causes a validator to fail. :func:`issubtype` can only use validators that implement the
:class:`Validator`
protocol.

Examples
--------
A 'smaller than' validator can be implemented as follows:

>>> class SmallerThan:
...     def __init__(self, upper_bound : Any):
...         self.upper_bound = upper_bound
...     def succeeds(self, value : Any) -> bool:
...         return value < self.upper_bound
...     def error_message(self, value : Any) -> str:
...         return f"expected value smaller than {self.upper_bound}, but got {value} "
...     def __str__(self) -> str:  # Optional; used for human readable string
...         return f"< {self.upper_bound}"

This validator can be used to model an integer range:

>>> from pytensorlab.typing import Positive
>>> number : Annotated[int, Positive(), SmallerThan(10)] = 1

If the type is used repeatedly, a `TypeAlias` can be constructed:

>>> RangedInt : TypeAlias = Annotated[int, Positive(), SmallerThan(10)]

To check if a number is of this type and is valid, :func:`issubtype` is used:

>>> from pytensorlab.typing import issubtype
>>> issubtype(1, RangedInt)
True

>>> issubtype(0, RangedInt)
ValueError: expected positive number, but got 0

>>> issubtype(10, RangedInt)
ValueError: expected value smaller than 10, but got 10

>>> issubtype(5.0, RangedInt)
TypeError: value does not match type: got float, expected int

Types can be printed in a more readable way using the :func:`type2str` function:

>>> from pytensorlab.typing import type2str
>>> type2str(RangedInt)
'Annotated[int, > 0, < 10]'
"""

from collections.abc import Callable, Generator, Iterable, Mapping, Sequence, Sized
from typing import (
    Annotated,
    Any,
    Literal,
    NoReturn,
    Protocol,
    TypeAlias,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    runtime_checkable,
)


class Comparable(Protocol):
    """Protocol for annotating comparable types."""

    def __lt__(self: Any, other: Any) -> bool: ...

    def __gt__(self: Any, other: Any) -> bool: ...

    def __ge__(self: Any, other: Any) -> bool: ...

    def __le__(self: Any, other: Any) -> bool: ...

    def __eq__(self: Any, other: Any) -> bool: ...


_T = TypeVar("_T", contravariant=True)


@runtime_checkable
class Validator(Protocol[_T]):
    """Validator for an annotated type.

    This protocol is used to impose runtime checkable validators in type hints on
    variables. As the validator is stored in the type hint, it can be run automatically.

    See Also
    --------
    Positive, Nonnegative, .Options

    Examples
    --------
    >>> a: Annotated[int, Positive()] = 1
    """

    def succeeds(self, value: _T) -> bool:
        """Return True if validation succeeds for this value.

        Parameters
        ----------
        value : _T
            Value to validate.

        Returns
        -------
        bool
            Whether the validation was successful.
        """
        ...

    def error_message(self, value: _T) -> str:
        """Return a meaningful error message.

        Parameters
        ----------
        value : _T
            The value for which this validator fails.

        Returns
        -------
        str
            The error message.
        """
        ...


class Positive:
    """Type condition for positive numbers."""

    def succeeds(self, value: Comparable) -> bool:
        """Return True if value is positive.

        Parameters
        ----------
        value : Comparable
            Value to check.

        Returns
        -------
        bool
            Whether the value is positive.
        """
        return value > 0

    def error_message(self, value: Comparable) -> str:
        """Return a meaningful error message.

        Parameters
        ----------
        value : Comparable
            The value for which this validator fails.

        Returns
        -------
        str
            The error message.
        """
        return f"expected positive number, but got {value}"

    def __str__(self) -> str:
        return "> 0"

    def __repr__(self) -> str:
        return "Positive()"


class Nonnegative:
    """Type condition for nonnegative numbers."""

    def succeeds(self, value: Comparable) -> bool:
        """Return True if value is nonnegative.

        Parameters
        ----------
        value : Comparable
            Value to check.

        Returns
        -------
        bool
            Whether the value is nonnegative.
        """
        return value >= 0

    def error_message(self, value: Comparable) -> str:
        """Return a meaningful error message.

        Parameters
        ----------
        value : Comparable
            The value for which this validator fails.

        Returns
        -------
        str
            The error message.
        """
        return f"expected nonnegative number, but got {value}"

    def __str__(self) -> str:
        return ">= 0"

    def __repr__(self) -> str:
        return "Nonnegative()"


PositiveInt: TypeAlias = Annotated[int, Positive()]
NonnegativeInt: TypeAlias = Annotated[int, Nonnegative()]
NonnegativeFloat: TypeAlias = Annotated[float, Nonnegative()]


@runtime_checkable
class HasNdim(Protocol):
    """Protocol for class having the attribute ndim."""

    ndim: int
    """Number of dimensions."""


class Ndim:
    """Array type with a bound on the number of dimensions.

    Parameters
    ----------
    lower_bound : NonnegativeInt
        Lower bound for the number of dimensions (inclusive).
    upper_bound : NonnegativeInt, optional
        Upper bound for the number of dimensions (inclusive). If not provided, no upper
        bound is enforced.
    """

    def __init__(
        self, lower_bound: NonnegativeInt, upper_bound: NonnegativeInt | None = None
    ):
        """Create a bound on the number of dimensions.

        Parameters
        ----------
        lower_bound : NonnegativeInt
            Lower bound for the number of dimensions (inclusive).
        upper_bound : Optional[NonnegativeInt]
            Upper bound for the number of dimensions (inclusive). If None, no upper
            bound is enforced.
        """
        if upper_bound and lower_bound > upper_bound:
            raise ValueError(
                f"lower bound ({lower_bound}) should be smaller than or equal to "
                f"upper bound ({upper_bound})"
            )
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def succeeds(self, value: HasNdim) -> bool:
        """Return True if the number of dimensions is within the given bounds.

        Parameters
        ----------
        value : HasNdim
            The value to check.

        Returns
        -------
        bool
            Whether ``value.ndim`` is within the given bounds.
        """
        if self.upper_bound is None:
            return self.lower_bound <= value.ndim
        return self.lower_bound <= value.ndim <= self.upper_bound

    def error_message(self, value: HasNdim) -> str:
        """Return a meaningful error message.

        Parameters
        ----------
        value : HasNdim
            The value for which this validator fails.

        Returns
        -------
        str
            The error message.
        """
        if self.upper_bound is None:
            return (
                f"expected array with ndim >= {self.lower_bound}, but got {value.ndim}"
            )
        if self.lower_bound == self.upper_bound:
            return (
                f"expected array with ndim == {self.lower_bound}, but got {value.ndim}"
            )
        return (
            f"expected array with {self.lower_bound} <= ndim <= {self.upper_bound}, "
            f"but got {value.ndim}"
        )

    def __str__(self) -> str:
        if self.upper_bound is None:
            return f"{self.lower_bound} <= ndim"
        if self.lower_bound == self.upper_bound:
            return f"ndim == {self.lower_bound}"
        return f"{self.lower_bound} <= ndim <= {self.upper_bound}"

    def __repr__(self) -> str:
        return f"Ndim({self.lower_bound}, {self.upper_bound})"


def type2str(type_hint: type[Any]) -> str:
    """Convert a type to a human-readable string.

    Parameters
    ----------
    type_hint : Type[Any]
        Type hint to be converted.

    Returns
    -------
    str
        Human-readable representation of the type.

    Examples
    --------
    >>> from pytensorlab.typing import type2str, Nonnegative
    >>> from typing import Union, Annotated
    >>> type2str(Union[Annotated[int, Nonnegative()], str])
    'Annotated[int, >= 0] | str'
    """
    origin = get_origin(type_hint)
    if origin == Union:
        return " | ".join(map(type2str, get_args(type_hint)))
    elif origin == Annotated:
        base_type, *checks = get_args(type_hint)
        return f"Annotated[{type2str(base_type)}, {', '.join(map(str, checks))}]"
    return type_hint.__name__


def _issubtype_union(value: Any, type_hint: type[Any]) -> bool | NoReturn:
    failed_validators: list[ValueError] = []
    for p in get_args(type_hint):
        try:
            return issubtype(value, p)
        except ValueError as e:
            failed_validators.append(e)
        except TypeError:
            pass
    if failed_validators:
        if len(failed_validators) == 1:
            raise failed_validators[0]
        raise ValueError(
            "multiple types match, but their validators are not successful:\n    "
            + "\n    ".join(map(str, failed_validators))
        )
    raise TypeError(
        f"value does not match type:\n"
        f"    got {type(value).__name__},\n"
        f"    expected {type2str(type_hint)}"
    )


def _issubtype_annotated(
    value: Any, type_hint: type[Annotated[Any, ...]]
) -> bool | NoReturn:
    hint, *validators = get_args(type_hint)
    try:
        assert issubtype(value, hint)
        for validator in validators:
            if not isinstance(validator, Validator):
                # Other types of validators cannot be checked, hence ignore
                continue
            if not validator.succeeds(value):
                raise ValueError(validator.error_message(value))
    except (ValueError, TypeError) as e:
        raise e
    return True


def _issubtype_default(value: Any, type_hint: type[Any]) -> bool | NoReturn:
    try:
        is_type_correct = isinstance(value, type_hint)
    except TypeError:  # support for generic types
        is_type_correct = isinstance(value, cast(type, get_origin(type_hint)))

    if not is_type_correct:
        raise TypeError(
            f"value does not match type: "
            f"got {type(value).__name__}, "
            f"expected {type2str(type_hint)}"
        )

    return True


def _issubtype_tuple(value: Any, type_hint: type[Any]) -> bool | NoReturn:
    if not isinstance(value, cast(type, get_origin(type_hint))):
        raise TypeError(
            f"value does not match type: "
            f"got {type(value).__name__}, "
            f"expected {type2str(type_hint)}"
        )
    args = get_args(type_hint)
    if len(args) and not args[-1] == Ellipsis:
        assert isinstance(value, Sized)
        if len(value) != len(args):
            raise TypeError(f"number of elements is {len(value)}; expected {len(args)}")

    def type_generator(args) -> Generator[Any, None, None]:
        """Yield types in a tuple, repeating the final one if an ellipsis is found."""
        if args[-1] is not Ellipsis:
            yield from args
        else:
            while True:
                yield args[0]

    assert isinstance(value, Iterable)
    for k, (val, hint) in enumerate(zip(value, type_generator(args))):
        try:
            issubtype(val, hint)
        except TypeError as e:
            raise TypeError(str(e).replace("value", f"value[{k}]", 1))
        except ValueError as e:
            raise ValueError(f"value[{k}] has an invalid value: {e}")

    return True


def _issubtype_list(value: Any, type_hint: type[Any]) -> bool | NoReturn:
    if not isinstance(value, cast(type, get_origin(type_hint))):
        raise TypeError(
            f"value does not match type: "
            f"got {type(value).__name__}, "
            f"expected {type2str(type_hint)}"
        )
    element_type, *_ = get_args(type_hint)
    assert isinstance(value, Iterable)
    for k, v in enumerate(value):
        try:
            issubtype(v, element_type)
        except TypeError:
            raise TypeError(
                f"value[{k}] does not match type: got {type2str(type(v))}, "
                f"expected {type2str(element_type)}"
            )
        except ValueError as e:
            raise ValueError(f"value[{k}] has an invalid value: {e}")

    return True


def _issubtype_dict(value: Any, type_hint: type[Any]) -> bool | NoReturn:
    if not isinstance(value, cast(type, get_origin(type_hint))):
        raise TypeError(
            f"value does not match type: "
            f"got {type(value).__name__}, "
            f"expected {type2str(type_hint)}"
        )

    key_type, value_type = get_args(type_hint)
    assert isinstance(value, dict)
    for k, v in value.items():
        try:
            issubtype(k, key_type)
        except TypeError as e:
            raise TypeError(str(e).replace("value", f"key '{k}'", 1))
        except ValueError as e:
            raise ValueError(f"invalid key '{k}': {e}")
        try:
            issubtype(v, value_type)
        except TypeError as e:
            raise TypeError(str(e).replace("value", f"value for key '{k}'", 1))
        except ValueError as e:
            raise ValueError(f"invalid value for key '{k}': {e}")
    return True


def _issubtype_any(value: Any, type_hint: type[Any]) -> bool:
    return True


def _issubtype_literal(value: Any, type_hint: type[Any]) -> bool | NoReturn:
    literals = get_args(type_hint)
    if value is None and any(literal is None for literal in literals):
        return True
    if value in literals:
        return True
    raise ValueError(f"{value} does not match {type_hint}")


_subtype_checks: Mapping[Any, Callable[[Any, type[Any]], bool | NoReturn]] = {
    Union: _issubtype_union,
    Annotated: _issubtype_annotated,
    tuple: _issubtype_tuple,
    dict: _issubtype_dict,
    Mapping: _issubtype_dict,
    list: _issubtype_list,
    Sequence: _issubtype_list,
    Literal: _issubtype_literal,
    Any: _issubtype_any,
}
"""Map of types and checks that are run.

Additional check can be added to this map to implement new types. The key is a type, or
the origin of a type.
"""


def issubtype(value: Any, type_hint: Any) -> bool | NoReturn:
    """Return True if value is of the given type.

    Check if `value` is an instance of the types defined in `type_hint`. If `type_hint`
    contains :data:`typing.Annotated` types, check if `value` passes validators if
    applicable. Currently, only annotations following the :class:`.Validator` protocol
    are tested.

    Parameters
    ----------
    value : Any
        The value to be checked.
    type_hint : Any
        The (annotated) type hint to check value against.

    Returns
    -------
    bool
        True if `value` is an instance of `type_hint` and checks in annotations pass.

    Raises
    ------
    TypeError
        If `value` is not an instance of `type_hint`
    ValueError
        If `value` is an instance of `type_hint`, but a check fails.

    Examples
    --------
    >>> from pytensorlab.typing import issubtype
    >>> issubtype(1, int)
    True

    >>> from pytensorlab.typing import Positive
    >>> from typing import Union, Annotated
    >>> issubtype(-1, Union[Annotated[int, Positive()], int])
    True

    >>> issubtype(-1, Annotated[int, Positive()])
    ValueError: expected positive number, but got -1

    >>> from pytensorlab.typing import Nonnegative
    >>> issubtype(-1.0, Union[int, Annotated[float, Nonnegative()]])
    ValueError: expected nonnegative number: got -1.0

    >>> issubtype(-1.0, Union[int, str])
    TypeError: value does not match type:
        got float,
        expected int | str
    """
    key = get_origin(type_hint) if get_origin(type_hint) else type_hint
    check = _subtype_checks.get(key, _issubtype_default)
    return check(value, type_hint)

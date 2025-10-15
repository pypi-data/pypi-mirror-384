"""Options dataclass with type checking.

The :class:`Options` dataclass is the base class for all option classes in pytensorlab,
such as :class:`.LMLRAHooiOptions` and :class:`.CPDNlsOptions`. These are used for
passing options to algorithms, such as :func:`.lmlra_hooi` and :func:`.cpd_nls`,
respectively.

Options dataclasses can be converted from one to another using the
:meth:`Options.from_options`. To get all default options of a function
:func:`get_options` can be used.

See Also
--------
get_options, Options.from_options
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import MISSING, asdict, dataclass, fields
from typing import (
    Any,
    Literal,
    NoReturn,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)
from warnings import warn

from pytensorlab.typing import issubtype

_DEFAULT_OPTIONS: dict[Callable[..., Any], type[Options]] = {}
_OPTION_CONVERSION_STRATEGY: Literal["silent", "warn", "error"] = "silent"
"""Strategy used when converting options.

Many algorithms have a specific set of options. With this option, the behavior when an
'incorrect' or unknown option object is provided can be set:

- ``"silent"``: convert the options to the desired options type, ignoring unknown
  options. This is the default behavior.
- ``"warn"``: raise a warning if an option is unknown.
- ``"error"``: raise an error if an option is unknown.

See Also
--------
Options.from_options
"""

SelfT = TypeVar("SelfT", bound="Options")


class UnknownOptionError(TypeError):
    """Unknown option encountered."""


def _check_annotated_types(obj: Options) -> bool | NoReturn:
    type_hints = get_type_hints(type(obj), include_extras=True)
    for param, hint in type_hints.items():
        value = getattr(obj, param)
        try:
            issubtype(value, hint)
        except (TypeError, ValueError) as exception:
            raise type(exception)(f"attribute {param}: {exception.args[0]}")
    return True


def _check_annotated_type(obj: Options, param: str) -> bool | NoReturn:
    type_hints = get_type_hints(type(obj), include_extras=True)
    if param not in type_hints:
        raise AttributeError(f"unknown parameter {param}")
    value = getattr(obj, param)
    try:
        issubtype(value, type_hints[param])
    except (TypeError, ValueError) as exception:
        raise type(exception)(f"attribute {param}: {exception.args[0]}")
    return True


def _is_unset_optional(option, field):
    return (
        field.default is None
        and getattr(option, field.name) is None
        and get_origin(field.type) == Union
        and any(a is type(None) for a in get_args(field.type))
    )


@dataclass
class Options:
    """Options dataclass with type checking.

    The goal of the :class:`Options` dataclass is to add typing information and
    documentation to the various options that an algorithm needs. Moreover, the type
    and validators in annotated types are enforced when creating an instance or when
    setting an option.

    Similar options can be passed to multiple algorithms by using the
    :meth:`from_options` class method for conversion.

    Examples
    --------
    Create a new option:

    >>> from typing import Annotated
    >>> from dataclasses import dataclass
    >>> from pytensorlab.typing import Nonnegative
    >>> from pytensorlab.util.options import Options
    >>> @dataclass
    ... class MyOptions(Options):
    ...     number : Annotated[int, Nonnegative()] = 1

    Instance the option:

    >>> options = MyOptions(number = 2)
    >>> options.number
    2

    >>> options.number = -1
    ValueError()

    >>> options.number = "a"
    TypeError()

    The ``MyOptions`` options can be converted to ``OtherOptions`` using
    :meth:`from_options`:

    >>> @dataclass
    ... class OtherOptions(Options):
    ...     number : Annotated[int, Nonnegative()] = 1
    >>> other = OtherOptions.from_options(options)
    """

    @overload
    @classmethod
    def set_defaults(
        cls, function: Callable[..., Any], default_options: Options
    ) -> None: ...

    @overload
    @classmethod
    def set_defaults(
        cls, function: Callable[..., Any], default_options: type[Options]
    ) -> None: ...

    @classmethod
    def set_defaults(
        cls,
        function: Callable[..., Any],
        default_options: Options | type[Options],
    ) -> None:
        """Register default options and values for a function.

        Parameters
        ----------
        function : Callable[..., Any]
            Function for which the defaults are registered.
        default_options : Type[Options]
            Type of the default options to be registered.
        """
        if isinstance(default_options, type):
            _DEFAULT_OPTIONS[function] = default_options
        else:
            _DEFAULT_OPTIONS[function] = type(default_options)

    @classmethod
    def get_defaults(cls, function: Callable[..., Any]) -> Options:
        """Get default options and values for a function.

        Parameters
        ----------
        function : Callable[..., Any]
            Function for which to retrieve the default options and values.

        Returns
        -------
        Options
            Default options and values for the given function.
        """
        try:
            return _DEFAULT_OPTIONS[function]()
        except KeyError:
            raise KeyError(
                f"no default options registered for {function.__name__}"
            ) from None

    @classmethod
    def from_options(
        cls: type[SelfT],
        other: Options | None,
        ignore_unknown: bool | None = None,
    ) -> SelfT | NoReturn:
        """Convert options to another type of options.

        This method allows converting between different `Options` subclasses by
        creating a new instance of the target class `cls` and copying values from
        fields that exist in both. This conversion step initializes a new object, hence
        all type checks are performed.

        Parameters
        ----------
        other : Options | None
            Options to be converted. If None, all default values are taken.
        ignore_unknown : bool, optional
            Silently ignore and drop unknown options if True. If False, an error will be
            raised. If not, the default value option is used, which can be set using
            :meth:`Options.set_default_option_conversion_strategy`.

        Returns
        -------
        SelfT
            The converted options.

        Raises
        ------
        UnknownOptionError
            An option in `other` is not presented in `cls`, and `ignore_unknown` is
            False.
        TypeError
            An option in `other` has an incompatible type for the option with the same
            name in `cls`.
        ValueError
            The value of an option in `other` does not satisfy the validators for the
            option with the same name in `cls`,

        Examples
        --------
        >>> @dataclass
        ... class A(Options):
        ...     number : int = 1
        >>> @dataclass
        ... class B(Options):
        ...     number : int = 2
        >>> a = A(number = 3)
        >>> b = B.from_options(a)
        >>> b.number
        3
        """
        if other is None:
            return cls()
        if ignore_unknown is None:
            strategy = _OPTION_CONVERSION_STRATEGY
        else:
            strategy = "silent" if ignore_unknown else "error"

        # Step 1: fix fields that do not have defaults.
        non_default_fields = {
            field.name
            for field in fields(cls)
            if field.default is MISSING and field.default_factory is MISSING
        }
        overlap = non_default_fields & {f.name for f in fields(other)}
        if len(overlap) < len(non_default_fields):
            missing_fields = non_default_fields - overlap
            names = ", ".join(f"'{f}'" for f in missing_fields)
            raise TypeError(
                f"missing value for "
                f"attribute{'s' if len(missing_fields) > 1 else ''}: {names}"
            )
        kwargs = {k: v for (k, v) in asdict(other).items() if k in overlap}
        option = cls(**kwargs)

        # Step 2: handle fields in other that are not in this type (cls).
        fields_remaining = {f.name for f in fields(other)} - non_default_fields
        defaults = {f.name for f in fields(option)} - non_default_fields
        fields_to_process = fields_remaining & defaults
        if len(fields_remaining) > len(fields_to_process):
            unknown_fields = fields_remaining - defaults
            names = ", ".join(f"'{f}'" for f in unknown_fields)
            message = (
                f"unknown option{'s' if len(unknown_fields) > 1 else ''} "
                f"{names} for {cls.__name__}"
            )

            if strategy == "error":
                raise UnknownOptionError(message) from None
            elif strategy == "warn":
                warn(f"ignoring {message}")

        # Step 3: update default fields, ignoring unset optional fields in other.
        for field in {f for f in fields(other) if f.name in fields_to_process}:
            if not _is_unset_optional(other, field):
                setattr(option, field.name, getattr(other, field.name))
        return option

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        _check_annotated_type(self, name)

    @classmethod
    def set_default_option_conversion_strategy(
        cls, strategy: Literal["silent", "warn", "error"]
    ) -> None:
        """Set the default strategy for converting unknown options.

        If an unknown option in the :meth:`Options.from_options` method is encountered,
        this option can be ignored, or the user can be made aware of this using an
        exception or a warning.

        Parameters
        ----------
        strategy : "silent" | "warn" | "error"
            One of the following three strategies can be used:
                - ``"silent"``: ignore unknown option,
                - ``"warn"``: raise a warning,
                - ``"error"``: raise an exception.
        """
        global _OPTION_CONVERSION_STRATEGY
        _OPTION_CONVERSION_STRATEGY = strategy


def get_options(function: Callable[..., Any]) -> Options:
    """Get default options and values for a function.

    Parameters
    ----------
    function : Callable[..., Any]
        Function for which to retrieve the default options and values.

    Returns
    -------
    Options
        Default options and values for the given function.

    See Also
    --------
    .Options.get_defaults

    Notes
    -----
    This is a convenience function for :meth:`.Options.get_defaults`.
    """
    return Options.get_defaults(function)

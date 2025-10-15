"""All custom exception classes."""

from pytensorlab.typing import Shape


class AssumptionViolationException(Exception):
    """Exception indicating violation of an assumption in an annotation.

    See Also
    --------
    .Validator
    """

    def __init__(self, msg: str):
        super().__init__(msg)


class ShapeMismatchException(Exception):
    """Raised when two shapes mismatch.

    Attributes
    ----------
    target : Shape
        Target shape.
    value : Shape
        Actual shape.
    message : str
        Explanation of the exception.
    """

    def __init__(self, target: Shape, value: Shape):
        """Initialize with target and value shapes."""
        self.target: Shape = target
        self.value: Shape = value
        self.message: str = (
            f"the given shape {self.value} does not match the target shape "
            f"{self.target}."
        )
        super().__init__(self.message)

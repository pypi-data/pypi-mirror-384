"""Definition of optimization problems.

The optimization methods require two main actions for any optimization problem: a way to
compute the objective function value and a way to compute the step. This module defines
two protocols for problems that are solved with line search or trust region/plane search
methods.

Classes
-------
Problem
    Optimization problem definition for line search type methods.
CurvatureProblem
    Optimization problem definition for trust region or plane search type methods.

See Also
--------
.LBFGSProblem
.GaussNewtonDirectNonHolomorphicProblem
.GaussNewtonDirectProblem
.GaussNewtonIterativeNonHolomorphicProblem
.GaussNewtonIterativeProblem
.NewtonDirectNonHolomorphicProblem
.NewtonDirectProblem
.NewtonIterativeNonHolomorphicProblem
.NewtonIterativeProblem
"""

from collections.abc import Callable, Mapping
from typing import Any, Protocol, TypeVar

import numpy as np

from pytensorlab.typing import VectorType

PointType = TypeVar("PointType")
"""Type of the optimization variables.

This can be any type, but typically it needs support for serialization, i.e., conversion
to a vector of floats (:data:`.VectorType`).

See Also
--------
.Problem.serialize
    Conversion from `PointType` to :data:`.VectorType`.
.Problem.deserialize
    Conversion from :data:`.VectorType` to `PointType`.
"""


class Problem(Protocol[PointType]):
    """Optimization problem definition for line search type methods."""

    def compute_objective(self, point: VectorType, /) -> float:
        """Compute the objective function value.

        Additional cached variables such as `_fval` can be set, if applicable.

        Parameters
        ----------
        point : VectorType
            The point in which the objective function is evaluated.

        Returns
        -------
        float
            Objective function value in `point`.
        """
        ...

    def compute_step(
        self, point: VectorType, /
    ) -> tuple[VectorType, Mapping[str, Any]]:
        """Compute the step.

        Compute the step based on a model in the given `point`. Additional cached
        variables such as `_gradient` and `_curvature` can be set, if applicable.

        Parameters
        ----------
        point : VectorType
            The point to compute the step for.

        Returns
        -------
        VectorType
            The computed step in `point`.
        Mapping[str, Any]
            A dictionary with extra information, if applicable.
        """
        ...

    serialize: Callable[[PointType], VectorType] | None = None
    """Function that serializes a custom point type.

    The signature of the serialization functions is::

        (point: PointType) -> tl.typing.VectorType

    If None, `PointType` should be :data:`.VectorType`.

    Examples
    --------
    >>> import pytensorlab as tl
    >>> def serialize_polyadic(point: tl.PolyadicTensor) -> tl.typing.VectorType:
    >>>     return point._data
    """

    def _serialize(self, point: PointType) -> VectorType:
        if self.serialize is None:
            assert isinstance(point, np.ndarray)
            return point
        return self.serialize(point)

    deserialize: Callable[[VectorType], PointType] | None = None
    """Function that converts serialized data to a custom point type.

    The signature of the deserialization function is::

        (serialized_data: tl.typing.VectorType) -> PointType

    If None, `PointType` should be :data:`.VectorType`.

    Examples
    --------
    >>> import pytensorlab as tl
    >>> shape = (2, 3, 4)
    >>> nterm = 2
    >>> def deserialize_polyadic(data: tl.typing.VectorType) -> tl.PolyadicTensor:
    >>>     return tl.PolyadicTensor.from_vector(data, shape, nterm)
    """

    def _deserialize(self, point: VectorType) -> PointType:
        if self.deserialize is None:
            return point  # type:ignore
        return self.deserialize(point)

    _fval: float
    """Computed objective function value.

    The objective function value computed by :func:`.compute_objective` in `point`.

    See Also
    --------
    compute_objective
    """

    _step: VectorType
    """Computed step.

    The step computed by :func:`.compute_step` in `point`.

    See Also
    --------
    compute_step
    """

    _gradient: VectorType
    """Gradient of the objective function.

    The gradient is computed by :func:`.compute_step` and is evaluated in `point`.

    See Also
    --------
    compute_step
    """

    _gradient_norm: float
    """Norm of the cached gradient of the objective function.

    See Also
    --------
    cached_gradient
    """


class CurvatureProblem(Problem[PointType]):
    """Optimization problem definition for trust-region/plane search type methods.

    Implementations of this problem should compute `_curvature` during the
    `compute_step` call.
    """

    _curvature: float
    """Curvature in point along the gradient direction.

    The curvature is computed by :func:`compute_step` and is evaluated in `point` along
    the gradient that is also computed in `point`.

    See Also
    --------
    compute_step
    """

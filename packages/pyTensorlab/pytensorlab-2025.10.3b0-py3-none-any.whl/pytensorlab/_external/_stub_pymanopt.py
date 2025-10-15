# flake8: noqa
# pylint: disable=unused-import
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Protocol,
    TypeVar,
    Union,
)
from collections.abc import Sequence
from typing_extensions import TypeAlias
from pytensorlab.typing import ArrayType, MatrixType, VectorType
import abc

import pymanopt  # type:ignore


if TYPE_CHECKING:

    PointT: TypeAlias = VectorType

    class Manifold(Protocol, metaclass=abc.ABCMeta):
        def __init__(
            self,
            name: str,
            dimension: int,
            point_layout: int | Sequence[int] = ...,
        ) -> None: ...

        @property
        def dim(self) -> int: ...

        @property
        def point_layout(self) -> int | Sequence[int]: ...

        @property
        def num_values(self) -> int: ...

        @property
        def typical_dist(self) -> float: ...

        @abc.abstractmethod
        def inner_product(
            self,
            point: PointT,
            tangent_vector_a: PointT,
            tangent_vector_b: PointT,
        ) -> float: ...

        @abc.abstractmethod
        def projection(self, point: PointT, vector: PointT) -> PointT: ...

        @abc.abstractmethod
        def norm(self, point: PointT, tangent_vector: PointT) -> float: ...

        @abc.abstractmethod
        def random_point(self) -> PointT: ...

        @abc.abstractmethod
        def random_tangent_vector(self, point: PointT) -> PointT: ...

        @abc.abstractmethod
        def zero_vector(self, point: PointT) -> PointT: ...

        def dist(self, point_a: PointT, point_b: PointT) -> float: ...

        def euclidean_to_riemannian_gradient(
            self, point: PointT, euclidean_gradient: PointT
        ) -> PointT: ...

        def euclidean_to_riemannian_hessian(
            self,
            point: PointT,
            euclidean_gradient: PointT,
            euclidean_hessian: PointT,
            tangent_vector: PointT,
        ) -> PointT: ...

        def retraction(self, point: PointT, tangent_vector: PointT) -> PointT: ...

        def exp(self, point: PointT, tangent_vector: PointT) -> PointT: ...

        def log(self, point_a: PointT, point_b: PointT) -> PointT: ...

        def transport(
            self, point_a: PointT, point_b: PointT, tangent_vector_a: PointT
        ) -> PointT: ...

        def pair_mean(self, point_a: PointT, point_b: PointT) -> PointT: ...

        def to_tangent_space(self, point: PointT, vector: PointT) -> PointT: ...

        def embedding(self, point: PointT, tangent_vector: PointT) -> PointT: ...

    class OptimizerResult:
        point: list[MatrixType]

    class Optimizer:
        _min_gradient_norm: float
        _max_iterations: int

    class TrustRegions(Optimizer):
        def run(
            self,
            problem: pymanopt.Problem,
            *,
            initial_point: Sequence[MatrixType] = ...,
            **kwargs: Any,
        ) -> OptimizerResult: ...

    _T = TypeVar("_T")

    class LineSearcher(Protocol[_T]):
        def search(
            self,
            objective: Callable[..., float],
            manifold: Manifold,
            x: _T,
            d: Any,
            f0: float,
            df0: float,
        ) -> tuple[float, _T]: ...

    class SteepestDescent(Optimizer, Generic[_T]):
        _line_searcher: LineSearcher[_T]

else:
    from pymanopt.optimizers import (
        TrustRegions as TrustRegions,
        SteepestDescent as SteepestDescent,
    )
    from pymanopt.manifolds.manifold import (
        Manifold as Manifold,
    )

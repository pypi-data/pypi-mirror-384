r"""Algorithms for computing low multilinear rank approximations of tensors.

In a low multilinear rank approximation (LMLRA), an Nth-order tensor :math:`\mathcal{A}`
with dimensions :math:`I_{0} \times I_{1} \times \cdots \times I_{N-1}` is approximated
with a multilinear rank :math:`(R_0,R_1, \ldots R_{N-1})` tensor
:math:`\ten{T}`, expressed through the factorization

.. math::

     \ten{T}  = \mathcal{C} \cdot_0 \mathbf{U}^{(0)} \cdot_1 \mathbf{U}^{(1)}
     \cdot_2 \mathbf{U}^{(2)} \cdots \cdot_{N-1} \mathbf{U}^{(N-1)}

in which :math:`\mathcal{C}` is the core tensor with dimensions :math:`R_0\times
R_1\times \cdots \times R_{N-1}` and :math:`\mathbf{U}^{(n)}`, :math:`n=0,1,\ldots,N-1`,
are the factors with dimensions :math:`I_n\times R_n`. In pyTensorlab, such a structured
tensor can be formed with the class :class:`.TuckerTensor`.

The general routine to compute an LMLRA is :func:`lmlra`. This function applies a two
stage process by first determining an initial guess for the LMLRA through different
means (MLSVD, random, or user specified initialization) and subsequently refining this
guess using one of the optimization-based methods. The optimization-based algorithms can
also be called directly. The following three algorithms minimize the loss function::

  -0.5 * (tl.frob(T) - tl.frob(tl.tmprod(T, U, range(T.ndim), "H"), squared=True))

:func:`lmlra_hooi`
    Uses the higher-order orthogonal iteration algorithm; see
    :cite:`delathauwer2000best`.
:func:`lmlra_mantr`
    Minimizes the loss function on a Cartesian product of Stiefel manifolds (as dictated
    by the factor matrices). This algorithm uses the trust region method of the Pymanopt
    package preconditioner to `b`; see :cite:`townsend2016pymanopt`.
:func:`lmlra_mansd`
    Similar to :func:`lmlra_mantr`, but uses the steepest descent
    algorithm of the Pymanopt package :cite:`townsend2016pymanopt`.

The next two algorithms minimize the loss function::

    0.5 * tl.frob(T - numpy.array(tl.TuckerTensor(U, S)) , squared=True)

:func:`lmlra_nls`
    Uses nonlinear least squares; see :cite:`r739`.
:func:`lmlra_minf`
    Uses unconstrained nonlinear optimization.

Notes
-----
See, e.g., :cite:`kroonenberg2008`, :cite:`kroonenberg1980`, and
:cite:`delathauwer2000best` for more information on algorithms.

Examples
--------
>>> import pytensorlab as tl
>>> shape = (5, 6, 7)
>>> coreshape = (2, 3, 4)
>>> T = tl.random.rand(shape)
>>> Tlmlra, _ = tl.lmlra(T, coreshape)
"""

import math
import textwrap
import warnings
from collections.abc import (
    Callable,  # noqa: F401 # sphinx
    Iterator,
    MutableMapping,  # noqa: F401 # sphinx
    Sequence,
)
from copy import deepcopy
from dataclasses import dataclass, field
from itertools import combinations
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,  # noqa: F401 # sphinx
    Protocol,
    TypeGuard,
    cast,
    runtime_checkable,
)

import numpy as np
import pymanopt  # type:ignore
from scipy.optimize import minimize
from scipy.sparse.linalg import cg

import pytensorlab.backends.numpy as tlb
from pytensorlab._external._stub_pymanopt import (
    SteepestDescent,
    TrustRegions,
)
from pytensorlab.algorithms.optimization_default_settings import (
    default_minimize_options,
    default_minimize_solver_options,
)
from pytensorlab.optimization import (
    IterativeSolver,
    IterativeSolverOptions,
    NewtonDirectProblem,
    NewtonIterativeProblem,
    OptimizationOptions,
    OptimizationProgressLogger,
    PrinterField,
    ProgressPrinter,
    VoidPrinter,
    conditional_printer,
    default_stopping_criteria,
    minimize_trust_region,
)
from pytensorlab.optimization.logger import (
    LoggedField,  # noqa: F401 # sphinx
    StoppingCriterion,  # noqa: F401 # sphinx
    StoppingCriterionAlgorithm,
    StoppingCriterionReached,
)
from pytensorlab.optimization.problem import Problem
from pytensorlab.typing import (
    ArrayType,
    MatrixType,
    NonnegativeFloat,
    NonnegativeInt,
    Shape,
    TensorType,
    VectorType,
)
from pytensorlab.typing.core import MinfOptimizationMethod
from pytensorlab.util import Options, get_name
from pytensorlab.util.indextricks import findfirst
from pytensorlab.util.utils import (
    SerializableT,
    _mapC2R,
    _mapR2C,
    _subspace_error,
    argmax,
    kron,
)

from ..datatypes import (
    Tensor,  # noqa: F401 # sphinx
    TuckerTensor,
    frob,
    mat2tens,
    mtkronprod,
    residual,
    tens2mat,
    tmprod,
)
from ..random.rng import get_rng
from ..util.utils import cumsum
from .mlsvd import (
    ColumnSpaceFcn,
    colspace_eig,
    colspace_qr,
    colspace_svd,
    mlsvd,
)
from .TensorOptimizationKernel import (
    TensorOptimizationKernel,
    cached,
    count_calls,
    ensure_deserialized,
    ensure_use_gramian,
    ensure_use_preconditioner,
)

# Local stubs for pymanopt are used to satisfy type checkers.
if TYPE_CHECKING:
    from pytensorlab._external._stub_pymanopt import LineSearcher


#### Printing
printer_fields_lmlrakernel: list[PrinterField] = [
    PrinterField(
        field="niterations",
        title="iters",
        width=8,
        value_format="d",
        info_format="d",
    ),
    PrinterField(
        field="fval",
        title="fval",
        width=15,
        value_format=".6e",
        info_format=".1e",
    ),
    PrinterField(
        field="max_subspace_angle",
        title="max angle",
        width=14,
        value_format=".6e",
        info_format=".1e",
    ),
]
extended_printer_fields: list[PrinterField] = printer_fields_lmlrakernel + [
    PrinterField(
        field="normgrad",
        title="||grad||",
        width=14,
        value_format=".6e",
        info_format=".1e",
    )
]


#### Supporting functions ####


def _mtkronprod_axis_ignore_for_array(
    T: np.ndarray,
    U: Sequence[MatrixType],
    axis: int,
    axis_ignore: int,
) -> MatrixType:
    """Compute the matricized tensor times Kronecker product with axis ignore.

    Compute the matricized tensor times Kronecker product ``tens2mat(T, axis) @
    kron(U[i] for i in range(T.ndim) if i != axis)``. However, for i = axis_ignore,
    U[i] is replaced with the identity matrix.

    Parameters
    ----------
    T : ArrayType
        The tensor to be matricized.
    U : Sequence[MatrixType]
        List of ``T.ndim`` matrices.
    axis : int
        Mode to exclude.
    axis_ignore:  int
        The mode for which U[i] should be set to Identity.

    Returns
    -------
    ArrayType
        The matricized tensor times Kronecker product.

    See Also
    --------
    .mtkronprod
    """
    for i in range(axis):
        if i == axis_ignore:
            T = np.moveaxis(T, 0, -1)
        else:
            T = tlb.tensordot(T, U[i], axes=(0, 0))

    for i in range(axis + 1, T.ndim):
        if i == axis_ignore:
            shift = list(range(T.ndim))
            shift.append(shift.pop(1))
            T = np.transpose(T, shift)
        else:
            T = tlb.tensordot(T, U[i], axes=(1, 0))

    return tens2mat(T, 0)


def _is_valid_lmlra_init(
    T: TensorType,
    core_shape: Shape,
    init_factors: Sequence[MatrixType],
    feasible_core_shape: Shape | None = None,
) -> bool:
    """Validate inputs for LMLRA optimization algorithms.

    Checks if the inputs provided to LMLRA optimization algorithms are valid, such that
    all routines that will be called will run without any errors.

    Parameters
    ----------
    T : TensorType
        The tensor of which an LMLRA is to be computed.
    core_shape : Shape
        The shape of the core tensor of the LMLRA as specified by user.
    init_factors : Sequence[MatrixType]
        Initialization for the LMLRA algorithm.
    feasible_core_shape : Shape, optional
        The shape of the core tensor of the LMLRA after correcting for feasibility. If
        not given, the shape of the LMLRA initialization is not further tested for
        feasibility of the shape of the core tensor.

    Returns
    -------
    bool
        True if `init` is valid for computing the LMLRA of the given tensor `T`.

    Raises
    ------
    ValueError
        If shape of `T` and `core_shape` do not match the initialization `init_factors`.
    """
    if T.ndim < 3:
        raise ValueError(f"order of tensor is {T.ndim}; expected order 3 or higher")
    if len(init_factors) != T.ndim:
        raise ValueError(
            f"initialization contains {len(init_factors)} factors; expected {T.ndim}"
        )
    v = tuple(s1.shape[0] != s2 for s1, s2 in zip(init_factors, T.shape))
    if any(v):
        k = findfirst(v)
        raise ValueError(
            f"shape for axis {k} in the initialization is incorrect; "
            f"got {init_factors[k].shape[0]} but expected {T.shape[k]}"
        )
    if feasible_core_shape is not None:
        v = tuple(
            s1.shape[1] != s2 for s1, s2 in zip(init_factors, feasible_core_shape)
        )
        if any(v):
            k = findfirst(v)
            raise ValueError(
                f"shape for axis {k} of the core in the initialization is "
                f"incorrect; got {feasible_core_shape[k]} but expected "
                f"{init_factors[k].shape[1]}"
            )
    # check if coreshape is smaller than shape of tensor
    v = tuple(s1 < s2 for s1, s2 in zip(T.shape, core_shape))
    if any(v):
        k = findfirst(v)
        raise ValueError(
            f"requested shape for axis {k} of the core in the initialization "
            f"exceeds shape of tensor; got {core_shape[k]} but expected "
            f"<={T.shape[k]}"
        )
    return True


def _is_sequence_matrixtype(items) -> TypeGuard[Sequence[MatrixType]]:
    return isinstance(items, Sequence) and all(isinstance(x, np.ndarray) for x in items)


@dataclass
class LMLRAProgressLogger(OptimizationProgressLogger):
    """Progress logger for the LMLRA algorithm."""

    subspace_angle: list[VectorType] = field(default_factory=list)
    """Subspace angle of factors between consecutive iterations."""

    max_subspace_angle: list[float] = field(default_factory=list)
    """Maximum subspace angle of factors between consecutive iterations."""

    tr_counter: int = 0
    """Number of attempts before a trust region step is accepted."""

    _bounds: list = field(default_factory=list)
    _factor_shapes: list = field(default_factory=list)
    _is_serialized: bool = False
    _is_normalized: bool = True

    def configure_logger(
        self, T: TuckerTensor, is_serialized: bool = False, is_normalized: bool = True
    ) -> None:
        """Configure the `LMLRAProgressLogger` for the optimization algorithm.

        Configure the `LMLRAProgressLogger` so that the outputs of the optimization
        algorithm are properly tracked.

        Parameters
        ----------
        T : TuckerTensor
            The initial `Tuckertensor` tensor of which an LMLRA is be computed.
        is_serialized : bool, default = False
            Input for the log call is serialized.
        is_normalized : bool, default = True
            Input for the log call has orthonormal factor matrices.
        """
        self._bounds = list(cumsum(f.size for f in T.factors))
        self._factor_shapes = [f.shape for f in T.factors]
        self._is_serialized = is_serialized
        self._is_normalized = is_normalized

    def log(
        self,
        z: SerializableT,
        fval: float,
        **_: Any,
    ) -> None:
        zp = self._retrieve_factors(self.zp)
        super().log(z, fval)
        self.tr_counter = 0
        if self._is_serialized:
            z = self._retrieve_factors(z)
        assert _is_sequence_matrixtype(z)
        if not self._is_normalized:
            zp = [tlb.qr(fp, mode="reduced")[0] for fp in zp]
            z = [tlb.qr(f, mode="reduced")[0] for f in z]
        assert _is_sequence_matrixtype(z)
        angle = np.array([_subspace_error(f, fp) for f, fp in zip(z, zp)])
        self.subspace_angle.append(angle)
        self.max_subspace_angle.append(angle.max())

    def _retrieve_factors(self, z):
        factors_serialized = np.split(z[: self._bounds[-1]], self._bounds)
        Up = [f.reshape(s) for f, s in zip(factors_serialized, self._factor_shapes)]
        return Up

    def __repr__(self) -> str:
        return super().__repr__()


class LMLRAKernel(TensorOptimizationKernel[TuckerTensor]):
    """Computational routines for the LMLRA.

    Class that collects the routines for the computation of an LMLRA of a tensor `T`
    by minimizing the loss function::

        -0.5 * (tl.frob(T, squared=True) - tl.frob(tl.tmprod(T, U, range(T.ndim), "H"),
        squared=True))

    over ``U`` on the Stiefel manifold. The class stores intermediate results for
    improved efficiency.

    Parameters
    ----------
    T : TensorType
        Tensor to be decomposed.
    core_shape : Shape
        The shape of the core tensor of the LMLRA. The multilinear is bounded by
        this parameter.
    use_gramian : bool, default = False
        Use the Gramian as an approximation for the Hessian.

    Attributes
    ----------
    use_gramian : bool,  default = False
        If True, update the cached variables to compute the Hessian approximation.

    Notes
    -----
    In this implementation, only the factor matrices are optimized, i.e., the
    gradient w.r.t. the core is not computed (unlike in :class:`TuckerKernel`).

    See Also
    --------
    TuckerKernel
    """

    def __init__(self, T: TensorType, core_shape: Shape, use_gramian: bool = False):
        """Initialize an LMLRAKernel object.

        Parameters
        ----------
        T : TensorType
            Tensor to be decomposed.
        core_shape : Shape
            The shape of the core tensor of the LMLRA. The multilinear is bounded by
            this parameter.
        use_gramian : bool, default = False
            Use the Gramian as an approximation for the Hessian.
        """
        super().__init__()

        # tensor protected properties.
        self._T: TensorType = T
        self._Tfrob = frob(self._T, squared=True)

        # shape parameters (required for serializing and deserializing)
        self._core_shape = core_shape

        # cached variables
        self._objfun_value: float
        # A separate current optimization point is stored to avoid inconsistencies when
        # using pymanopts TrustRegion solvers, as `objfun` is called to test the
        # performance of the proposed point, which may be rejected. This means
        # `_zcached` can point to a rejected step. Instead, `_point` is only updated
        # when calling the gradient which is only called for accepted points.
        self._point: TuckerTensor | None = None

        # settings
        self.use_gramian = use_gramian

    def isvalid(self, z: TuckerTensor) -> bool:
        """Validate the kernel.

        Checks if the kernel is valid, i.e., if this particular combination of
        parameters, data, and variables `z` allows all kernel routines to be completed
        without errors (unless underlying routines defined elsewhere fail).

        Parameters
        ----------
        z : TuckerTensor
            Current iterate.

        Returns
        -------
        bool
            True if kernel is valid, otherwise False.

        Raises
        ------
        ValueError
            If `z` does not match the shape of `T` and the provided multilinear rank.
        """
        return _is_valid_lmlra_init(self._T, self._core_shape, z.factors)

    def update_cache(self, z: TuckerTensor) -> None:
        """Update cached variables.

        Parameters
        ----------
        z : TuckerTensor
            Current iterate.
        """
        self._core = tmprod(self._T, z.factors, range(self._T.ndim), "H")
        self._W = mtkronprod(self._T.conj(), z.factors)

    @ensure_deserialized
    @cached
    def objfun(self, z: TuckerTensor) -> float:
        """Evaluate objective function.

        Parameters
        ----------
        z: TuckerTensor
           Current iterate.

        Returns
        -------
        float
           The objective value at z.
        """
        self._objfun_value = 0.5 * (self._Tfrob - frob(self._core, squared=True))
        return self._objfun_value

    @ensure_deserialized
    @cached
    def gradient(self, z: TuckerTensor) -> TuckerTensor:
        """Compute the gradient for the LMLRA.

        Parameters
        ----------
        z: TuckerTensor
           Current iterate.

        Returns
        -------
        TuckerTensor
           Gradient of the LMLRAKernel cost function.
        """
        self._point = z
        gradient_factors = [
            -Wi @ tens2mat(self._core, i).T for (i, Wi) in enumerate(self._W)
        ]
        return TuckerTensor(gradient_factors, np.zeros(self._core_shape))

    @ensure_deserialized
    @cached
    def hessian(self, z: TuckerTensor) -> MatrixType:
        """Compute the Hessian for the LMLRA.

        Parameters
        ----------
        z : TuckerTensor
            Current iterate.

        Returns
        -------
        MatrixType
            The (approximated) Hessian.
        """
        raise NotImplementedError

    @count_calls
    @ensure_deserialized
    @cached
    def hessian_vector(self, z: TuckerTensor, x: TuckerTensor) -> TuckerTensor:
        """Compute the product of (approximate) Hessian times vector for the LMLRA.

        Parameters
        ----------
        z : TuckerTensor
            Current iterate.
        x : TuckerTensor
            Vector to be multiplied by.

        Returns
        -------
        TuckerTensor
            The product of (approximate) Hessian times vector.
        """
        # contribution by Gramian
        # J*x
        S = np.zeros(self._core_shape, dtype=z.core.dtype)
        for k in range(z.ndim):
            S += mat2tens(
                x.factors[k].conj().T @ self._W[k].conj(), self._core_shape, k
            )
        # JH*s
        hessvect_factors = [
            cast(MatrixType, -Wi.conj() @ tens2mat(S, i).T)
            for (i, Wi) in enumerate(self._W)
        ]

        # second-order term if complete Hessian is required/desired
        if not self.use_gramian:
            for k in range(z.ndim):
                Tk = np.array(tmprod(self._T, x.factors[k], k, "H"))
                for i in range(z.ndim):
                    if i != k:
                        V = _mtkronprod_axis_ignore_for_array(Tk, z.factors, i, k)
                        hessvect_factors[i] -= V @ tens2mat(self._core, i).conj().T

        return TuckerTensor(hessvect_factors, np.zeros(self._core_shape))

    def deserialize(self, z: VectorType) -> TuckerTensor:
        """Return a given vector in TuckerTensor format.

        Parameters
        ----------
        z : VectorType
            The serialized `TuckerTensor`.

        Returns
        -------
        TuckerTensor
            The `TuckerTensor` corresponding to the given vector `z`.
        """
        z = np.concatenate((z, np.zeros(math.prod(self._core_shape))))
        return TuckerTensor.from_vector(z, self._T.shape, self._core_shape, copy=False)

    def serialize(self, z: TuckerTensor) -> VectorType:
        """Return a given TuckerTensor in serialized format.

        Parameters
        ----------
        z : TuckerTensor
            The `TuckerTensor` to be serialized.

        Returns
        -------
        VectorType
            The serialized `TuckerTensor`.
        """
        return np.concatenate(tuple(f.ravel() for f in z.factors))


class TuckerKernel(TensorOptimizationKernel[TuckerTensor]):
    """Computational routines for computing an LMLRA.

    Class that collects the routines for the computation of an LMLRA of a tensor `T`
    by minimizing the loss function::

        0.5 * tl.frob(T - numpy.array(tl.TuckerTensor(U, S)) , squared=True)

    over ``U`` and ``S`` in Euclidean space. The class stores intermediate results for
    improved efficiency.

    Parameters
    ----------
    T : TensorType
        Tensor to be decomposed.
    core_shape : Shape
        The shape of the core tensor of the LMLRA. The multilinear rank of the
        approximation is bounded above by this parameter.
    use_gramian : bool, default = True
        If True, update the cached variables to compute the Hessian approximation.
        The parameter must be set to True if :func:`hessian` or
        :func:`hessian_vector` are used.
    use_preconditioner : bool, default = True
        If True, update the cached variables required to compute the preconditioner.
        The parameter must be set to True if :func:`M_blockJacobi` is used.

    Attributes
    ----------
    use_gramian : bool, default = True
        If True, update the cached variables to compute the Hessian approximation.
        The parameter must be set to True if :func:`hessian` or
        :func:`hessian_vector` are used.
    use_preconditioner : bool, default = True
        Update cached variables required to compute the preconditioner if True. The
        parameter must be set to True if :func:`M_blockJacobi` is used.

    Notes
    -----
    In this implementation, both the factor matrices and core tensor are optimized
    (unlike in :class:`LMLRAKernel` where only the factor matrices are optimized).

    See Also
    --------
    LMLRAKernel
    """

    def __init__(
        self,
        T: TensorType,
        core_shape: Shape,
        use_gramian: bool = True,
        use_preconditioner: bool = True,
    ):
        """Initialize an TuckerKernel object.

        Parameters
        ----------
        T : TensorType
            Tensor to be decomposed.
        core_shape : Shape
            The shape of the core tensor of the LMLRA. The multilinear rank is bounded
            by this parameter.
        use_gramian : bool, default = True
            If True, update the cached variables to compute the Hessian approximation.
            The parameter must be set to True if :func:`hessian` or
            :func:`hessian_vector` are used.
        use_preconditioner : bool, default = True
            If True, update the cached variables required to compute the preconditioner.
            The parameter must be set to True if :func:`M_blockJacobi` is used.
        """
        super().__init__()

        # tensor protected properties.
        self._T: TensorType = T

        # shape parameters (required for serializing and deserializing)
        self._core_shape = core_shape

        # cached variables
        self._objfun_value: float
        self._residual: TensorType

        # set computational settings
        self.use_gramian = use_gramian
        self.use_preconditioner = use_preconditioner

    def isvalid(self, z: TuckerTensor) -> bool:
        """Validate the kernel.

        Checks if the kernel is valid, i.e., if this particular combination of
        parameters, data, and variables `z` allows all kernel routines to be completed
        without errors (unless underlying routines defined elsewhere fail).

        Parameters
        ----------
        z : TuckerTensor
            Current iterate.

        Returns
        -------
        bool
            True if kernel is valid, otherwise False.

        Raises
        ------
        ValueError
            If `z` does not match the shape of `T` and the provided multilinear rank.
        """
        return _is_valid_lmlra_init(self._T, self._core_shape, z.factors)

    def update_cache(self, z: TuckerTensor) -> None:
        """Update cached variables.

        Parameters
        ----------
        z : TuckerTensor
            Current iterate.
        """
        self._residual = residual(z, self._T)
        if self.use_gramian or self.use_preconditioner:
            self.UHU = [f.conj().T @ f for f in z.factors]
        if self.use_gramian:
            self.UHUC = mtkronprod(z.core, self.UHU)
            self.CUHUC = [
                tens2mat(z.core.conj(), k) @ f.T for (k, f) in enumerate(self.UHUC)
            ]
        if self.use_preconditioner:
            self.UHUinv: list[MatrixType] = [tlb.inv(f) for f in self.UHU]
            self.CUHUCinv: list[MatrixType] = [tlb.pinv(u) for u in self.CUHUC]

    @ensure_deserialized
    @cached
    def objfun(self, z: TuckerTensor) -> float:
        """Evaluate objective function.

        Parameters
        ----------
        z: TuckerTensor
           Current iterate.

        Returns
        -------
        float
           The objective value at z.
        """
        self._objfun_value = 0.5 * frob(self._residual, squared=True)
        return self._objfun_value

    @ensure_deserialized
    @cached
    def gradient(self, z: TuckerTensor) -> TuckerTensor:
        """Compute the gradient.

        Parameters
        ----------
        z: TuckerTensor
           Current iterate.

        Returns
        -------
        TuckerTensor
           Gradient of the TuckerKernel cost function.
        """
        # pre-computations
        W = mtkronprod(self._residual, z.factors)
        # gradient term core
        g_core = mat2tens(z.factors[0].conj().T @ W[0], self._core_shape)
        g_core = cast(ArrayType, g_core)
        # gradient term factors
        g_factors = [Wk @ tens2mat(z.core, k).conj().T for k, Wk in enumerate(W)]
        return TuckerTensor(g_factors, g_core)

    @ensure_use_gramian
    @ensure_deserialized
    @cached
    def hessian_vector(self, z: TuckerTensor, x: TuckerTensor) -> TuckerTensor:
        """Compute the product of approximate Hessian times vector for the LMLRA.

        Parameters
        ----------
        z : TuckerTensor
            Current iterate.
        x : TuckerTensor
            Vector to be multiplied by.

        Returns
        -------
        TuckerTensor
            The product of (approximate) Hessian times vector.
        """
        UHX = [f.conj().T @ g for f, g in zip(z.factors, x.factors)]

        # core contribution
        gramian_core = tmprod(x.core, self.UHU, range(self._T.ndim))
        for n in range(self._T.ndim):
            proj = [UHX[k] if k == n else uhu for k, uhu in enumerate(self.UHU)]
            gramian_core += tmprod(z.core, proj, range(self._T.ndim))

        # factors
        gramian_factors = []
        for k in range(self._T.ndim):
            f_k = np.zeros_like(z.factors[k])
            for m in range(self._T.ndim):
                proj = [UHX[j] if j == m else uhu for (j, uhu) in enumerate(self.UHU)]
                tmp = mtkronprod(z.core, proj, k).conj().T
                if k == m:
                    f_k += x.factors[k] @ (tens2mat(z.core, k) @ tmp)
                    f_k += z.factors[k] @ (tens2mat(x.core, k) @ tmp)
                if k != m:
                    f_k += z.factors[k] @ (tens2mat(z.core, k) @ tmp)
            gramian_factors.append(f_k)

        return TuckerTensor(gramian_factors, gramian_core)

    @ensure_use_gramian
    @ensure_deserialized
    @cached
    def hessian(self, z: TuckerTensor) -> MatrixType:
        """Compute the Hessian for the LMLRA.

        Parameters
        ----------
        z : TuckerTensor
            Current iterate.

        Returns
        -------
        ArrayType
            The (approximated) Hessian.
        """
        sz = [math.prod(f.shape) for f in z.factors] + [math.prod(z.coreshape)]
        JHJ: list[list[MatrixType]] = [[np.empty((n, m)) for m in sz] for n in sz]
        # diagonal terms (factors)
        for i in range(z.ndim):
            JHJ[i][i] = kron(np.eye(z.shape[i]), self.CUHUC[i])
        # diagonal terms (core)
        JHJ[z.ndim][z.ndim] = kron(*self.UHU)

        # off-diagonal terms (factors)
        ij: Iterator[tuple[int, int]] = combinations(tuple(range(z.ndim)), 2)
        for i, j in ij:
            UHU_excl = [uhu for (k, uhu) in enumerate(self.UHU) if k not in (i, j)]
            ind_excl = [k for k in range(z.ndim) if k not in (i, j)]
            K = tmprod(z.core, UHU_excl, ind_excl)
            G = np.tensordot(z.core.conj(), K, axes=(ind_excl, ind_excl))
            H = tmprod(G, [z.factors[j].conj(), z.factors[i]], [1, 2])

            JHJ[i][j] = tens2mat(H, [2, 0], [1, 3])
            JHJ[j][i] = JHJ[i][j].conj().T

        # off-diagonal terms (core)
        for i in range(z.ndim):
            tmp = mat2tens(self.UHUC[i], z.coreshape, i)
            tmp = np.tensordot(tmp, z.factors[i].conj().T, axes=0)
            rows = [z.ndim if j == i else j for j in range(z.ndim)]
            cols = [z.ndim + 1, i]
            JHJ[z.ndim][i] = tens2mat(tmp, rows, cols)
            JHJ[i][z.ndim] = JHJ[z.ndim][i].conj().T

        return np.block(JHJ)

    @ensure_use_gramian
    @ensure_use_preconditioner
    @ensure_deserialized
    @cached
    def M_blockJacobi(self, z: TuckerTensor, b: TuckerTensor) -> TuckerTensor:
        """Apply block-Jacobi preconditioner.

        Applies the block-Jacobi preconditioner to `b`.

        Parameters
        ----------
        z : TuckerTensor
            Current iterate.
        b : TuckerTensor
            `TuckerTensor` to which the preconditioner is applied.

        Returns
        -------
        TuckerTensor
            Result of applying the preconditioner.
        """
        core = tmprod(b.core, self.UHUinv, range(self._T.ndim))
        factors = [f @ u for (u, f) in zip(self.CUHUCinv, b.factors)]

        return TuckerTensor(factors, core)

    def M_blockJacobi_serialized(self, z: VectorType, b: VectorType) -> VectorType:
        """Apply block-Jacobi to serialized TuckerTensor.

        Parameters
        ----------
        z : VectorType
            Serialized current iterate.
        b : VectorType
            Serialized `TuckerTensor` to which the preconditioner is applied.

        Returns
        -------
        VectorType
            Serialized result of applying the preconditioner.
        """
        zs = self.deserialize(z)
        bs = self.deserialize(b)
        return self.serialize(self.M_blockJacobi(zs, bs))

    def deserialize(self, z: VectorType) -> TuckerTensor:
        """Return a given vector in TuckerTensor format.

        Parameters
        ----------
        z : VectorType
            The serialized `TuckerTensor`.

        Returns
        -------
        TuckerTensor
            The `TuckerTensor` corresponding to the vector `z`.
        """
        return TuckerTensor.from_vector(z, self._T.shape, self._core_shape, copy=False)

    def serialize(self, z: TuckerTensor) -> VectorType:
        """Return a given TuckerTensor in serialized format.

        Parameters
        ----------
        z : TuckerTensor
            The `TuckerTensor` to be serialized.

        Returns
        -------
        VectorType
            The serialized `TuckerTensor`.
        """
        return z._data


def _preprocess_lmlra(
    T: TensorType, init: TuckerTensor | Sequence[MatrixType]
) -> tuple[TuckerTensor, Shape]:
    """Preprocess the inputs of LMLRA optimization routines.

    Performs preprocessing operations on the inputs of LMLRA optimization routines. In
    particular, it checks if a feasible coreshape is provided by the user and if the
    initial factors are orthonormalized.

    Parameters
    ----------
    T : TensorType
        Tensor to be approximated with an LMLRA.
    init : TuckerTensor | Sequence[MatrixType]
        Initialization for the LMLRA routine provided by the user.

    Returns
    -------
    init : TuckerTensor
        Preprocessed initialization with feasible core shape and orthonormal factors.
    core_shape : Shape
        The shape of the core tensor of the provided initialization `init`.

    See Also
    --------
    lmlra_hooi, lmlra_mantr, _postprocess_lmlra
    """
    # derive core_shape from input
    if isinstance(init, TuckerTensor):
        core_shape = init.coreshape
        init = init.factors
    else:
        core_shape = tuple(f.shape[1] for f in init)

    # determine feasible core shape
    i_max = argmax(core_shape)
    shape_i_max_other = math.prod(core_shape) // core_shape[i_max]
    if shape_i_max_other < core_shape[i_max]:
        shape_i_max = shape_i_max_other
        warnings.warn(
            (
                f"core shape at axis {i_max} is set too high at {core_shape[i_max]}; "
                f"theoretical maximal mode-{i_max} rank is {shape_i_max_other}"
            ),
            UserWarning,
        )
        feasible_core_shape = tuple(min(s, shape_i_max) for s in core_shape)
        U, _, _ = tlb.svd(init[i_max], full_matrices=False)
        init = [U[:, :shape_i_max] if i == i_max else f for (i, f) in enumerate(init)]
    else:
        feasible_core_shape = tuple(core_shape)

    # check validity initial condition
    _is_valid_lmlra_init(T, core_shape, init, feasible_core_shape)

    # corrected initialization
    init = TuckerTensor(init, np.zeros(feasible_core_shape))

    # normalize factor matrices if necessary
    if not init.has_orthonormal_factors():
        init.normalize()

    return init, core_shape


def _postprocess_lmlra(
    Tlmlra: TuckerTensor,
    core_shape: Shape,
    _rng: np.random.Generator | int | None = None,
) -> TuckerTensor:
    """Postprocess the outputs of LMLRA optimization routines.

    Performs postprocessing operations on the outputs of LMLRA optimization routines. In
    particular, if the core shape has been modified in the preprocessing step, the
    computed LMLRA will be updated to an LMLRA with the original core shape. This is
    done by augmenting the core with zero entries in the respective mode and adding
    complementary columns to the accompanying factor matrix.

    Parameters
    ----------
    Tlmlra : TuckerTensor
        The LMLRA computed by the optimization routine.
    core_shape : Shape
        The original core shape provided by the user.
    _rng : numpy.random.Generator | int, optional
        Seed or random number generator used for all random operations in this
        function. If an integer is given, a new generator is created with that seed. If
        a generator is provided, it is used directly. If None, the global generator
        (set via `set_rng`) is used.

    Returns
    -------
    TuckerTensor
        The postprocessed LMLRA.

    See Also
    --------
    lmlra_hooi, lmlra_mantr, _preprocess_lmlra
    """
    _rng = get_rng(_rng)

    if core_shape == Tlmlra.coreshape:
        return Tlmlra

    # find index of modified mode
    i_max = findfirst(tuple(s1 != s2 for s1, s2 in zip(core_shape, Tlmlra.coreshape)))

    # modify factor
    U_i_max = Tlmlra.factors[i_max]
    extra_cols = core_shape[i_max] - Tlmlra.coreshape[i_max]
    X = _rng.standard_normal((U_i_max.shape[0], extra_cols))
    Ucompl, _ = tlb.qr(X - U_i_max @ (U_i_max.conj().T @ X), mode="reduced")
    U_i_max = np.concatenate((U_i_max, Ucompl), 1)
    U = [U_i_max if i == i_max else f for (i, f) in enumerate(Tlmlra.factors)]

    # modify core
    zero_padding = tuple(
        (0, extra_cols) if i == i_max else (0, 0) for i in range(Tlmlra.ndim)
    )
    S = np.pad(Tlmlra.core, zero_padding, "constant")

    return TuckerTensor(U, S)


def _generate_lmlra_problem(
    T: TensorType,
    init: TuckerTensor,
) -> tuple[LMLRAKernel, pymanopt.Problem]:
    """Create an LMLRA kernel and a Pymanopt problem instance.

    Generates an LMLRA kernel and Pymanopt LMLRA problem instance, which are required in
    certain LMLRA optimization routines.

    Parameters
    ----------
    T : TensorType
        Tensor to be approximated with an LMLRA.
    init : TuckerTensor
        Initialization for the LMLRA routine.

    Returns
    -------
    kernel : LMLRAKernel
        The LMLRA kernel.
    pymanopt_problem : pymanopt.Problem
        The Pymanopt problem instance.
    """
    # Create Kernel
    kernel = LMLRAKernel(T, init.core_shape)

    # Define manifold
    manifold = pymanopt.manifolds.Product(
        [pymanopt.manifolds.Stiefel(*f.shape) for f in init.factors]
    )

    # Define cost, gradient, gramian/hessian and set up problem
    @pymanopt.function.numpy(manifold)
    def cost(*point: MatrixType) -> float:
        return kernel.objfun(TuckerTensor(point, init.core))

    @pymanopt.function.numpy(manifold)
    def euclidean_gradient(*point: MatrixType) -> Sequence[MatrixType]:
        grad_kernel = kernel.gradient(TuckerTensor(point, init.core))
        return grad_kernel.factors

    @pymanopt.function.numpy(manifold)
    def euclidean_hessian(*point_and_U: MatrixType):
        point = point_and_U[: kernel._T.ndim]
        U = point_and_U[kernel._T.ndim :]
        hessprod_kernel = kernel.hessian_vector(
            TuckerTensor(point, init.core), TuckerTensor(U, init.core)
        )
        return hessprod_kernel.factors

    pymanopt_problem = pymanopt.Problem(
        manifold,
        cost,
        euclidean_gradient=euclidean_gradient,
        euclidean_hessian=euclidean_hessian,
    )

    return kernel, pymanopt_problem


@dataclass
class LMLRAHooiOptions(Options):
    """Options for :func:`lmlra_hooi`.

    See Also
    --------
    lmlra_hooi
    """

    normalize_init: bool = True
    """Normalize the initialization before applying the HOOI algorithm."""

    normalize_output: bool = True
    """Normalize the output after applying the HOOI algorithm."""

    maxiter: NonnegativeInt = 500
    """The maximum number of iterations."""

    tol_absfval: NonnegativeFloat | None = None
    """The tolerance absolute value of the objective function.

    The following objective function is considered::

        -0.5 * (tl.frob(T, squared=True) - tl.frob(tl.tmprod(T, U, range(T.ndim), "H"),
        squared=True))

    where `T` refers to the tensor for which an LMLRA is computed and ``U`` the factor
    matrices of the LMLRA. If set to None, `tol_absfval` is not used as a stopping
    criterion.
    """

    tol_subspace: NonnegativeFloat | None = 1e-6
    """Tolerance on the maximal canonical angle between two successive iterates."""

    tol_normgrad: NonnegativeFloat | None = None
    """The tolerance on the gradient of the objective function. 
    
    This tolerance can be used as an optional stopping criteria.
    """

    display: NonnegativeInt = 10
    """Print the progress after every `display` iterations. 
    
    If set to 0, the printing is suppressed.
    """

    large_scale: bool | None = None
    """Enable faster implementations for column space computation for large tensors.

    Note that these faster implementations can be potentially less accurate. Defaults to
    False for small tensors. See also :func:`colspace_large_scale_hooi`.
    """

    compute_column_space: ColumnSpaceFcn | None = None
    """Function to compute the column space. 
    
    If given, `large_scale` is neglected.
    """


def colspace_large_scale_hooi(
    a: TensorType, axis: int, k: int, /, **kwargs: Any
) -> tuple[MatrixType, VectorType]:
    """Compute column space of tensor unfolding selecting a fast method.

    This method will use :func:`.colspace_eig` if `k` is larger than
    ``min(tl.tens2mat(a, axis).shape) / 4`` and :func:`.colspace_qr` otherwise.

    Parameters
    ----------
    a : TensorType
        The tensor for which the column space of an unfolding is computed.
    axis : int
        The mode along which the tensor is unfolded.
    k : int
        The dimension of the mode-`axis` space to compute.
    **kwargs
        Additional keyword arguments for :func:`.colspace_eig` and :func:`.colspace_qr`.

    Returns
    -------
    MatrixType
        Column space of the matrix unfolding.
    VectorType
        Vector containing (estimates for) the singular values.

    See Also
    --------
    .colspace_eig, .colspace_qr
    """
    i = a.shape[axis]
    j = math.prod(s for i, s in enumerate(a.shape) if i != axis)
    if k < min(i, j) / 4:
        return colspace_qr(a, axis, k, kwargs=kwargs)
    else:
        return colspace_eig(a, axis, k, kwargs=kwargs)


def lmlra_hooi(
    T: TensorType,
    init: TuckerTensor | Sequence[MatrixType],
    options: Options | None = None,
) -> tuple[TuckerTensor, LMLRAProgressLogger]:
    """Compute LMLRA by higher-order orthogonal iteration.

    Given an initial guess of factor matrices, a normalized LMLRA is computed of the
    tensor `T` by using the higher-order orthogonal iteration (HOOI) algorithm; see,
    e.g., :cite:`delathauwer2000best`.

    Parameters
    ----------
    T : TensorType
        Tensor to be approximated with an LMLRA.
    init : TuckerTensor | Sequence[MatrixType]
        Initialization for the HOOI algorithm. If a `TuckerTensor` is given, only the
        factors ``init.factors`` are used. If the factors are not orthonormal, they are
        normalized first.
    options: LMLRAHooiOptions, default = LMLRAHooiOptions()
        Options to change settings of the HOOI algorithm.

    Returns
    -------
    Tlmlra : TuckerTensor
        The computed LMLRA of `T`.
    logger : LMLRAProgressLogger
        Additional information logged by the HOOI algorithm.

    See Also
    --------
    lmlra_mantr, lmlra_mansd, lmlra_nls, lmlra_minf

    Notes
    -----
    See, e.g., :cite:`kroonenberg1980`, :cite:`kroonenberg2008`, and
    :cite:`delathauwer2000best` for more information.
    """
    options = LMLRAHooiOptions.from_options(options)

    if options.compute_column_space is None:
        if options.large_scale is None:
            options.large_scale = math.prod(T.shape) > 100000
        if options.large_scale:
            compute_column_space = colspace_large_scale_hooi
        else:
            compute_column_space = colspace_svd
    else:
        compute_column_space = options.compute_column_space

    # preprocess
    init, core_shape = _preprocess_lmlra(T, init)
    if options.normalize_init:
        init.normalize()

    # set tol_normgrad equal to none for complex tensors
    if np.iscomplexobj(T):
        options.tol_normgrad = None

    # create logger
    logger = LMLRAProgressLogger(
        lmlra_hooi,
        stopping_criteria=default_stopping_criteria(
            tol_absfval=options.tol_absfval,
            tol_subspace=options.tol_subspace,
            tol_normgrad=options.tol_normgrad,
            max_iter=options.maxiter,
        ),
    )
    logger.configure_logger(init)
    # create printer
    ChosenPrinter = ProgressPrinter if options.display > 0 else VoidPrinter
    if options.tol_normgrad is None:
        problem = None
        printer = ChosenPrinter(
            printer_fields_lmlrakernel, logger, display=options.display
        )
    else:
        # create lmlra problem instance
        _, problem = _generate_lmlra_problem(T, init)
        printer = ChosenPrinter(
            extended_printer_fields, logger, display=options.display
        )
        printer = ChosenPrinter(
            extended_printer_fields, logger, display=options.display
        )

    # initialization
    U = list(init.factors)
    S = U[0].conj().T @ mtkronprod(T, U, 0)
    Tfrob = frob(T, squared=True)
    logger.log_init(U, 0.5 * (Tfrob - frob(S, squared=True)))
    if problem:
        normgrad = cast(float, problem.manifold.norm(U, problem.riemannian_gradient(U)))
        logger.normgrad.append(normgrad)
    printer.print_iteration()

    if logger.check_termination():
        printer.print_termination()
        return TuckerTensor(U, np.reshape(S, init.coreshape)), logger

    # perform HOOI iterations
    while not logger.check_termination():
        for n in range(T.ndim):
            S = mtkronprod(T, U, n)
            Rn = init.coreshape[n]
            Un, s = compute_column_space(S, 0, Rn, U0=U[n])
            Un = Un[:, :Rn]
            U[n] = Un

        Sfrob = frob(s[:Rn]) ** 2  # pyright:ignore [reportPossiblyUnboundVariable]
        logger.log(U, 0.5 * (Tfrob - Sfrob))
        if problem:
            riem_grad = problem.riemannian_gradient(U)
            normgrad = cast(float, problem.manifold.norm(U, riem_grad))
            logger.normgrad.append(normgrad)
        printer.print_iteration()

    printer.print_termination()

    # estimate core
    S = np.reshape(S.T @ U[-1].conj(), init.coreshape)
    Tlmlra = TuckerTensor(U, S)
    # post process
    Tlmlra = _postprocess_lmlra(Tlmlra, core_shape)
    if options.normalize_output:
        Tlmlra.normalize()

    return Tlmlra, logger


@dataclass
class LMLRAMantrOptions(Options):
    """Options for :func:`lmlra_mantr`.

    See Also
    --------
    lmlra_mantr
    """

    normalize_init: bool = True
    """Normalize the initialization before applying the trust region algorithm."""

    normalize_output: bool = True
    """Normalize the output after applying the trust region algorithm."""

    maxiter: NonnegativeInt = 200
    """The maximum number of iterations."""

    max_internal_iterations: NonnegativeInt | None = None
    """The maximum number of conjugate gradient iterations. 
    
    These conjugate gradient steps occur in the inner loop of the trust region method. 
    If set to None, `max_internal_iterations` is internally set to the dimension of 
    the manifold.
    """

    tol_absfval: NonnegativeFloat | None = None
    """Tolerance on the absolute value of the loss function. 
    
    If set to None, `tol_absfval` is not used as a stopping criterion.
    """

    tol_subspace: NonnegativeFloat | None = None
    """The tolerance on the maximal canonical angle between two successive iterates.

    If set to None, `tol_subspace` is not used as stopping criterion.
    """

    tol_normgrad: NonnegativeFloat = 1e-8
    """The tolerance on the gradient of the objective function. 
    
    This is used as a stopping criterion to terminate the iterations in the trust region
    method.
    """

    use_gramian: bool = False
    """Use Gramian as an approximation to the Hessian in the trust region algorithm. 
    
    Note that for the considered objective function, the Gramian does not coincide with 
    the Hessian in the global optimum.
    """

    display: NonnegativeInt = 10
    """Print the progress after every `display` iterations. 
    
    If set to 0, the printing is completely suppressed.
    """

    max_radius_updates: NonnegativeInt = 200
    """Maximum number of radius update steps in the trust region method. 
    
    The algorithm terminates if this limit is reached.
    """


class _TrustRegionLMLRA(TrustRegions):
    def __init__(
        self,
        kernel: LMLRAKernel,
        problem: pymanopt.Problem,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._T = kernel._T
        self._kernel = kernel
        self._problem = problem

    def _check_stopping_criterion(
        self,
        *,
        start_time,
        iteration=-1,
        gradient_norm=np.inf,
    ):
        # if self._kernel._point is not equal to self._kernel._zcached, the step is
        # rejected. If rejected, the step size or relative function should not be used
        # to decide on convergence, as the difference is zero.
        if (
            self._kernel._point is not None
            and self._log.zp is not None
            and self._kernel._zcached is not None
        ):
            if np.array_equal(self._kernel._zcached, self._kernel._point._data):
                self._log.log(self._kernel._point.factors, self._kernel._objfun_value)
                self._log.normgrad.append(gradient_norm)
                self._printer.print_iteration()
            else:
                self._log.tr_counter += 1

        return self._log.check_termination()

    def _initialize_log(self, *, optimizer_parameters=None) -> None:
        pass

    def run_algorithm(
        self, initial_point: TuckerTensor, options: LMLRAMantrOptions
    ) -> tuple[TuckerTensor, LMLRAProgressLogger]:
        # We must initialize the logging here so that the stopping criteria can be
        # checked before the trust region iterations are initiated.
        self._log = LMLRAProgressLogger(
            lmlra_mantr,
            stopping_criteria=default_stopping_criteria(
                tol_absfval=options.tol_absfval,
                tol_subspace=options.tol_subspace,
                tol_normgrad=options.tol_normgrad,
                max_iter=options.maxiter,
                max_radius_updates=options.max_radius_updates,
            ),
        )
        self._log.configure_logger(initial_point)
        ChosenPrinter = ProgressPrinter if options.display > 0 else VoidPrinter
        self._printer = ChosenPrinter(
            extended_printer_fields, self._log, display=options.display
        )
        self._log.log_init(
            initial_point.factors,
            self._kernel.objfun(initial_point),
        )
        riem_grad = self._problem.riemannian_gradient(initial_point.factors)
        normgrad = cast(
            float, self._problem.manifold.norm(initial_point.factors, riem_grad)
        )
        self._log.normgrad.append(normgrad)
        self._printer.print_iteration()
        U = initial_point.factors
        if not self._log.check_termination():
            U = tuple(
                super()
                .run(
                    self._problem,
                    initial_point=U,
                    maxinner=options.max_internal_iterations,
                )
                .point
            )
        S = np.array(tmprod(self._T, U, range(self._T.ndim), "H"))
        self._printer.print_termination()

        return TuckerTensor(U, S), self._log


def lmlra_mantr(
    T: TensorType,
    init: TuckerTensor | Sequence[MatrixType],
    options: Options | None = None,
) -> tuple[TuckerTensor, LMLRAProgressLogger]:
    """Compute an LMLRA using a trust region method over a manifold.

    Given an initial guess of the factor matrices, a normalized LMLRA is computed of
    the tensor `T` by minimizing the loss function::

        -0.5 * (tl.frob(T, squared=True) - tl.frob(tl.tmprod(T, U, range(T.ndim), "H"),
        squared=True))

    on a Cartesian product of Stiefel manifolds as dictated by the factor matrices.
    This algorithm relies on the Pymanopt package and uses the trust region method;
    see :cite:`townsend2016pymanopt`.

    Parameters
    ----------
    T : TensorType
        Tensor to be approximated with an LMLRA.
    init : TuckerTensor | Sequence[MatrixType]
        Initialization for the algorithm. If a `TuckerTensor` is given, only the
        factors ``init.factors`` are used. If the factors are not orthonormal, they are
        normalized first.
    options: LMLRAMantrOptions, default = LMLRAMantrOptions()
        Options to change settings of the trust region algorithm.

    Returns
    -------
    Tlmlra : TuckerTensor
        The computed LMLRA of `T`.
    logger : LMLRAProgressLogger
        Additional information logged by the trust region method algorithm.

    See Also
    --------
    lmlra_mansd, lmlra_hooi, lmlra_nls, lmlra_minf

    Notes
    -----
    This function only supports real tensors.
    """
    options = LMLRAMantrOptions.from_options(options)
    # preprocess
    init, core_shape = _preprocess_lmlra(T, init)
    if options.normalize_init:
        init.normalize()
    # create problem instance
    kernel, problem = _generate_lmlra_problem(T, init)
    # select optimizer
    optimizer = _TrustRegionLMLRA(kernel, problem, verbosity=0)
    # run and process results
    Tlmlra, logger = optimizer.run_algorithm(init, options)
    # post process
    Tlmlra = _postprocess_lmlra(Tlmlra, core_shape)
    if options.normalize_output:
        Tlmlra.normalize()

    return Tlmlra, logger


class _SteepestDescentLMLRA(SteepestDescent):
    def __init__(
        self,
        kernel: LMLRAKernel,
        tol_absfval: float | None,
        tol_subspace: float | None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._T = kernel._T
        self._kernel = kernel
        self._tol_absfval = tol_absfval
        self._tol_subspace = tol_subspace

    def _run_algorithm(
        self,
        problem: pymanopt.Problem,
        initial_point: TuckerTensor,
        display: NonnegativeInt,
    ) -> tuple[TuckerTensor, LMLRAProgressLogger]:
        manifold = problem.manifold
        objective = problem.cost
        gradient = problem.riemannian_gradient

        self.line_searcher: LineSearcher[tuple[MatrixType, ...]] = deepcopy(
            self._line_searcher
        )

        # define stopping critreria and construct logger
        stopping_criteria = default_stopping_criteria(
            tol_absfval=self._tol_absfval,
            tol_subspace=self._tol_subspace,
            tol_normgrad=self._min_gradient_norm,
            max_iter=self._max_iterations,
        )
        logger = LMLRAProgressLogger(lmlra_mansd, stopping_criteria=stopping_criteria)
        logger.configure_logger(initial_point)
        ChosenPrinter = ProgressPrinter if display > 0 else VoidPrinter
        printer = ChosenPrinter(extended_printer_fields, logger, display=display)
        # initial point
        U = initial_point.factors
        cost = cast(float, objective(U))
        grad = gradient(U)
        gradient_norm = cast(float, manifold.norm(U, grad))

        # initialize logger
        logger.log_init(U, cost)
        logger.normgrad.append(gradient_norm)
        printer.print_iteration()
        while not logger.check_termination():
            # compute next step
            _, U = self.line_searcher.search(
                objective,
                manifold,  # type:ignore
                U,
                -grad,  # type:ignore
                cost,
                -(gradient_norm**2),
            )

            # Calculate new cost, grad, gradient_norm, subspace angles w.r.t prev. point
            cost = cast(float, objective(U))
            grad = gradient(U)
            gradient_norm = cast(float, manifold.norm(U, grad))

            # log and print
            logger.log(U, cost)
            logger.normgrad.append(gradient_norm)
            printer.print_iteration()
        S = np.array(tmprod(self._T, U, range(self._T.ndim), "H"))
        printer.print_termination()

        return TuckerTensor(U, S), logger


@dataclass
class LMLRAMansdOptions(Options):
    """Options for :func:`lmlra_mansd`.

    See Also
    --------
    lmlra_mansd
    """

    normalize_init: bool = True
    """Normalize the initialization before applying the steepest descent algorithm."""

    normalize_output: bool = True
    """Normalize the output after applying the steepest descent algorithm."""

    maxiter: NonnegativeInt = 200
    """The maximum number of iterations."""

    tol_absfval: NonnegativeFloat | None = None
    """Tolerance on the absolute value of the loss function. 
    
    If set to None, `tol_absfval` is not used as stopping criterion.
    """

    tol_subspace: NonnegativeFloat | None = None
    """The tolerance on the maximal canonical angle between two successive iterates. 

    If set to None, `tol_subspace` is not used as stopping criterion.
    """

    tol_normgrad: NonnegativeFloat = 1e-5
    """The tolerance on the gradient of the objective function. 
    
    This is used as a stopping criterion to terminate the iterations in the steepest
    descent method.
    """

    display: NonnegativeInt = 10
    """Print the progress after every `display` iterations. 
    
    If set to 0, the printing is suppressed.
    """


def lmlra_mansd(
    T: TensorType,
    init: TuckerTensor | Sequence[MatrixType],
    options: Options | None = None,
) -> tuple[TuckerTensor, LMLRAProgressLogger]:
    """Compute an LMLRA using a steepest descent method over a manifold.

    Given an initial guess of the factor matrices, a normalized LMLRA is computed of
    the tensor `T` by minimizing the loss function::

        -0.5 * (tl.frob(T, squared=True) - tl.frob(tl.tmprod(T, U,'H'), squared=True)

    on a Cartesian product of Stiefel manifolds as dictated by the factor matrices. This
    algorithm relies on the Pymanopt package and employs the steepest descent method;
    see :cite:`townsend2016pymanopt`. We advise users to use this routine only on an
    experimental basis, since convergence properties cannot always be satisfied.

    Parameters
    ----------
    T : TensorType
        Tensor to be approximated with an LMLRA.
    init : TuckerTensor | Sequence[MatrixType]
        Initialization for the algorithm. If a `TuckerTensor` is given, only the factors
        ``init.factors`` are used. If the factors are not orthonormal, they are
        normalized first.
    options: LMLRAMansdOptions, default = LMLRAMansdOptions()
        Options to change settings of the steepest descent algorithm.

    Returns
    -------
    Tlmlra : TuckerTensor
        The computed LMLRA of `T`.
    logger : LMLRAProgressLogger
        The intermediate iterates and stopping criteria.

    See Also
    --------
    lmlra_hooi, lmlra_mantr, lmlra_nls, lmlra_minf

    Notes
    -----
    `lmlra_mansd` only works for real tensors.
    """
    options = LMLRAMansdOptions.from_options(options)
    init, core_shape = _preprocess_lmlra(T, init)
    if options.normalize_init:
        init.normalize()
    kernel, problem = _generate_lmlra_problem(T, init)
    optimizer = _SteepestDescentLMLRA(
        kernel,
        options.tol_absfval,
        options.tol_subspace,
        max_iterations=options.maxiter,
        min_gradient_norm=options.tol_normgrad,
    )
    Tlmlra, logger = optimizer._run_algorithm(problem, init, options.display)

    Tlmlra = _postprocess_lmlra(Tlmlra, core_shape)
    if options.normalize_output:
        Tlmlra.normalize()

    return Tlmlra, logger


@dataclass
class LMLRANlsOptions(Options):
    """Options for :func:`lmlra_nls`.

    See Also
    --------
    lmlra_mantr
    """

    normalize_init: bool = True
    """Normalize the initialization before applying the NLS algorithm."""

    normalize_output: bool = True
    """Normalize the output after applying the NLS algorithm."""

    maxiter: NonnegativeInt = 200
    """The maximum number of iterations."""

    tol_relfval: NonnegativeFloat = 1e-12
    """Tolerance for relative change in objective function value."""

    tol_relstep: NonnegativeFloat = 1e-8
    """Tolerance for step size relative to the norm of the current iterate."""

    tol_absfval: NonnegativeFloat = 0.0
    """Tolerance for absolute change in objective function value."""

    large_scale: bool | None = None
    """Use an iterative instead of a direct internal solver if True. 
    
    If True, the step direction is computed using an iterative solver and Gramian times 
    vector products. If False, a direct solver for linear systems is used. If None,
    the small or large scale version is selected based on the number of variables.
    """

    internal_solver: IterativeSolver = cast(IterativeSolver, cg)
    """Internal iterative solver to use if `large_scale` is True."""

    max_internal_iterations: NonnegativeInt = 15
    """Maximum number of iterations for the internal iterative solver."""

    tol_internal_residual: NonnegativeFloat = 1e-6
    """Tolerance on the residual when computing the step using the internal solver."""

    tol_subspace: NonnegativeFloat | None = 1e-14
    """The tolerance on the maximal canonical angle between two successive iterates.

    If set to None, `tol_subspace` is not used as stopping criterion.
    """

    internal_solver_options: dict[str, Any] = field(default_factory=dict)
    """Options to the optimization algorithm."""

    preconditioner: bool = True
    """Use a preconditioner if the iterative internal solver is used."""

    solver_options: dict[str, Any] = field(default_factory=dict)
    """Options for the optimization algorithm."""

    display: NonnegativeInt = 10
    """Print the progress after every `display` iterations. 
    
    If set to 0, the printing is suppressed.
    """


def lmlra_nls(
    T: TensorType,
    Tinit: TuckerTensor | Sequence[MatrixType],
    options: Options | None = None,
) -> tuple[TuckerTensor, OptimizationProgressLogger]:
    """Compute an LMLRA using nonlinear least squares.

    Approximates a given tensor `T` by a `TuckerTensor` using nonlinear least squares.
    The following objective function in ``U`` and ``S`` is used::

        0.5 * tl.frob(T - numpy.array(tl.TuckerTensor(U, S)), squared=True)

    This algorithm approximates the Hessian by the Gramian of the Jacobian of the
    residual to obtain a step direction.

    Parameters
    ----------
    T : TensorType
        Tensor to be approximated with an LMLRA.
    Tinit : TuckerTensor | Sequence[MatrixType]
        Initialization for the algorithm.
    options: LMLRANlsOptions, default = LMLRANlsOptions()
        Options to change settings of the NLS algorithm.

    Returns
    -------
    TuckerTensor
        The computed LMLRA of `T`.
    logger : OptimizationProgressLogger
        Additional information logged by the HOOI algorithm.

    See Also
    --------
    lmlra_hooi, lmlra_minf, lmlra_mantr, lmlra_mansd
    """
    # convert to TuckerTensor
    if isinstance(Tinit, TuckerTensor):
        _is_valid_lmlra_init(T, Tinit.coreshape, Tinit.factors)
    else:
        Tinit = cast(Sequence[MatrixType], Tinit)
        _is_valid_lmlra_init(T, tuple(f.shape[1] for f in Tinit), Tinit)
        Cinit = cast(ArrayType, tmprod(T, Tinit, range(T.ndim), transpose="H"))
        Tinit = TuckerTensor(Tinit, Cinit)

    # set options
    options = LMLRANlsOptions.from_options(options)
    if options.large_scale is None:
        options.large_scale = Tinit._data.size > 500
    if options.normalize_init and Tinit.has_orthonormal_factors():
        Tinit = deepcopy(Tinit)
        Tinit.normalize()

    # Construct kernel and check for errors.
    kernel = TuckerKernel(T, Tinit.coreshape, use_preconditioner=options.preconditioner)

    # create logger
    criteria = default_stopping_criteria(
        tol_absfval=options.tol_absfval,
        tol_relstep=options.tol_relstep,
        tol_relfval=options.tol_relfval,
        max_iter=options.maxiter,
        tol_subspace=options.tol_subspace,
    )
    logger: OptimizationProgressLogger = LMLRAProgressLogger(
        lmlra_nls, stopping_criteria=criteria, terminate_with_exception=True
    )
    logger.configure_logger(Tinit, is_serialized=True, is_normalized=False)

    # create problem
    problem: Problem[TuckerTensor]
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
        logger.add_custom_list_field("matvecs_cg", "nmatvec")
        logger.add_custom_list_field("residual_cg", "residual")
    else:
        problem = NewtonDirectProblem(kernel.objfun, kernel.gradient, kernel.hessian)
    problem.serialize = kernel.serialize
    problem.deserialize = kernel.deserialize

    # create printer
    if options.display > 0:
        printer_fields: list[PrinterField] = [
            PrinterField("niterations", "iter", 8, "d", "d"),
            PrinterField("fval", "fval", 12, ".3e", ".1e"),
            PrinterField("relative_fval", "rel fval", 12, ".3e", ".1e"),
            PrinterField("relative_step", "rel step", 12, ".3e", ".1e"),
            PrinterField("max_subspace_angle", "max angle", 14, ".6e", ".1e"),
        ]
        printer = ProgressPrinter(printer_fields, logger, display=options.display)
    else:
        printer = VoidPrinter()

    optimization_options = OptimizationOptions.from_options(options)
    Tlmlra, logger = minimize_trust_region(
        problem,
        Tinit,
        options=optimization_options,
        log=logger,
        printer=printer,
    )
    if options.normalize_output:
        Tlmlra.normalize()

    return Tlmlra, logger


def _logger_callback(
    z: VectorType,
    kernel: TuckerKernel,
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
class LMLRAMinfOptions(Options):
    """Options for :func:`lmlra_minf`.

    See Also
    --------
    lmlra_mantr
    """

    normalize_init: bool = True
    """Normalize the initialization before applying the minf algorithm."""

    normalize_output: bool = True
    """Normalize the output after applying the minf algorithm."""

    maxiter: NonnegativeInt = 200
    """The maximum number of iterations."""

    method: MinfOptimizationMethod | str = "l-bfgs-b"
    """Name of the optimization method to use. 
    
    Currently, the following method from :mod:`scipy.optimize` are supported: 'bfgs',
    'cg', 'l-bfgs-b'.
    """

    memory_limit: NonnegativeInt = 30
    """Maximum number of updates used to construct the Hessian approximation. 
    
    The limit is imposed if L-BFGS-B is the chosen `method`. This value is 
    automatically upper bounded by the number variables (``Tinit._data.size``).
    """

    tol_relfval: NonnegativeFloat = 1e-12
    """Tolerance for relative change in objective function value."""

    tol_relstep: NonnegativeFloat = 1e-7
    """Tolerance for step size relative to the norm of the current iterate."""

    tol_absfval: NonnegativeFloat = 0.0
    """Tolerance for absolute change in objective function value."""

    tol_subspace: NonnegativeFloat | None = 1e-14
    """The tolerance on the maximal canonical angle between two successive iterates.

    If set to None, `tol_subspace` is not used as stopping criterion.
    """

    solver_options: dict[str, Any] = field(default_factory=dict)
    """Options for the optimization algorithm."""

    display: NonnegativeInt = 10
    """Print the progress after every `display` iterations. 
    
    If set to 0, the printing is suppressed.
    """


def lmlra_minf(
    T: TensorType,
    Tinit: TuckerTensor | Sequence[MatrixType],
    options: Options | None = None,
) -> tuple[TuckerTensor, OptimizationProgressLogger]:
    """Compute an LMLRA using nonlinear optimization.

    Approximates a given tensor `T` by a `TuckerTensor` using unconstrained nonlinear
    optimization. The following objective function in ``U`` and ``S`` is used::

        0.5 * tl.frob(T - numpy.array(tl.TuckerTensor(U, S)) , squared=True)

    Parameters
    ----------
    T : TensorType
        Tensor to be approximated by an LMLRA.
    Tinit : TuckerTensor | Sequence[MatrixType]
        Initialization for the algorithm.
    options: LMLRAMinfOptions, default = LMLRAMinfOptions()
        Options to change settings of the minf algorithm.

    Returns
    -------
    Tlmlra : TuckerTensor
        The computed LMLRA of `T`.
    logger : OptimizationProgressLogger
        Additional information logged by the HOOI algorithm.

    See Also
    --------
    lmlra_mantr, lmlra_mansd, lmlra_nls, lmlra_hooi
    """
    # convert to TuckerTensor
    if isinstance(Tinit, TuckerTensor):
        _is_valid_lmlra_init(T, Tinit.coreshape, Tinit.factors)
    else:
        Tinit = cast(Sequence[MatrixType], Tinit)
        _is_valid_lmlra_init(T, tuple(f.shape[1] for f in Tinit), Tinit)
        Cinit = cast(ArrayType, tmprod(T, Tinit, range(T.ndim), transpose="H"))
        Tinit = TuckerTensor(Tinit, Cinit)

    # ensure that Tinit is complex if T is complex
    if np.iscomplexobj(T) and not np.iscomplexobj(Tinit):
        Tinit = TuckerTensor.from_vector(
            Tinit._data.astype(complex), Tinit.shape, Tinit.coreshape
        )

    # construct kernel
    kernel = TuckerKernel(T, Tinit.coreshape)

    # determine solver specific options
    options = LMLRAMinfOptions.from_options(options)
    if options.normalize_init and Tinit.has_orthonormal_factors():
        Tinit = deepcopy(Tinit)
        Tinit.normalize()
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

    # initialize OptimizationProgressLogger and set stopping criteria
    criteria = default_stopping_criteria(
        tol_absfval=options.tol_absfval,
        tol_relstep=options.tol_relstep,
        tol_relfval=options.tol_relfval,
        max_iter=options.maxiter,
        tol_subspace=options.tol_subspace,
    )
    logger = LMLRAProgressLogger(
        lmlra_minf,
        stopping_criteria=criteria,
        terminate_with_exception=True,
    )
    logger.configure_logger(Tinit, is_serialized=True, is_normalized=False)
    if options.display > 0:
        printer_fields: list[PrinterField] = [
            PrinterField("niterations", "iter", 8, "d", "d"),
            PrinterField("fval", "fval", 12, ".3e", ".1e"),
            PrinterField("relative_fval", "rel fval", 12, ".3e", ".1e"),
            PrinterField("relative_step", "rel step", 12, ".3e", ".1e"),
            PrinterField("max_subspace_angle", "max angle", 14, ".6e", ".1e"),
        ]
        printer = ProgressPrinter(printer_fields, logger, display=options.display)
    else:
        printer = VoidPrinter()
    logger.log_init(Tinit._data, kernel.objfun(Tinit))
    assert isinstance(logger.zp, np.ndarray)

    # declare objective function, gradient and callback function

    if not np.iscomplexobj(Tinit):

        init = Tinit._data
        objfun = kernel.objfun_serialized
        jacobian = kernel.gradient_serialized

        def callback(z: VectorType) -> None:
            return _logger_callback(z, kernel, logger, printer)

    else:
        init = _mapC2R(Tinit._data)

        def objfun(z: VectorType) -> float:
            return kernel.objfun_serialized(_mapR2C(z))

        def jacobian(z: VectorType) -> VectorType:
            return _mapC2R(kernel.gradient_serialized(_mapR2C(z)))

        def callback(z: VectorType) -> None:
            return _logger_callback(_mapR2C(z), kernel, logger, printer)

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
    Tlmlra = TuckerTensor.from_vector(logger.zp, T.shape, Tinit.coreshape)
    if options.normalize_output:
        Tlmlra.normalize()
    return Tlmlra, logger


#### The main lmlra function ####


@runtime_checkable
class LMLRAInitializationFcn(Protocol):
    """Signature for an LMLRA initialization algorithm.

    Returns a initialization for an LMLRA of a tensor `T`.

    Parameters
    ----------
    T : TensorType
        The array for which the LMLRA initialization is determined.
    coreshape : Shape
        The shape of the core tensor of the LMLRA. The multilinear rank is bounded
        by this parameter.

    Returns
    -------
    TuckerTensor
        The LMLRA initialization for `T`.
    Sequence[VectorType] | None
        Sequence of multilinear singular values.

    See Also
    --------
    .TuckerTensor.random_like, :func:`.mlsvd`, .mlsvd_rsi
    """

    def __call__(
        self,
        T: TensorType,
        coreshape: Shape,
        /,
    ) -> tuple[TuckerTensor, Sequence[VectorType] | None]: ...


@runtime_checkable
class LMLRAOptimizerFcn(Protocol):
    """Signature for an LMLRA optimization algorithm.

    Computes a `TuckerTensor` by optimizing an LMLRA objective function.

    Parameters
    ----------
    T : TensorType
        The tensor of which the LMLRA is computed.
    init : TuckerTensor | Sequence[MatrixType]
        Initialization for the algorithm.
    options: Options
        Optimization settings for the optimization algorithm.

    Returns
    -------
    TuckerTensor
        The computed LMLRA of `T`.
    OptimizationProgressLogger
        Extra information logged by the algorithm.

    See Also
    --------
    lmlra_hooi, lmlra_mantr, lmlra_mansd
    """

    def __call__(
        self,
        T: TensorType,
        init: TuckerTensor | Sequence[MatrixType],
        /,
        options: Options = ...,
    ) -> tuple[TuckerTensor, LMLRAProgressLogger]: ...


LMLRAInitializationMethods = Literal["manual"] | Literal["manual with estimation"]


@dataclass
class LMLRAInitializationInfo:
    """Output information for the initialization step in :func:`lmlra`."""

    message: str
    """Description of performed action."""

    Uinit: TuckerTensor
    """Output of the initialization step."""

    method: LMLRAInitializationMethods | LMLRAInitializationFcn
    """Method of initialization."""

    relative_error: NonnegativeFloat
    """Relative Frobenius error between computed tensor and initialization."""

    def __repr__(self) -> str:
        """Create readable text representation."""
        return textwrap.dedent(
            f"""\
            {type(self).__name__}(
                message={self.message!r},
                Uinit=<{type(self.Uinit).__name__} at {id(self.Uinit):#018x}>,
                method={self.method!r},
                relative_error={self.relative_error!r},
            )"""
        )

    def __str__(self) -> str:
        return textwrap.dedent(
            f"""\
            Output information for the initialization step of the lmlra function:
                message : {self.message}
                Uinit : {self.Uinit}
                method : {self.method}
                relative_error : {self.relative_error}
            """
        )


@dataclass
class LMLRAOptimizationInfo:
    """Output information for the optimization step in :func:`lmlra`."""

    message: str
    """Description of performed action."""

    Uopt: TuckerTensor
    """Output of the optimization step."""

    method: LMLRAOptimizerFcn
    """Method of initialization."""

    relative_error: NonnegativeFloat
    """Relative Frobenius error between computed tensor and initialization."""

    log: OptimizationProgressLogger
    """Information logged by the optimization algorithm."""

    def __repr__(self) -> str:
        """Create readable text representation."""
        return textwrap.dedent(
            f"""\
            {type(self).__name__}(
                message={self.message!r},
                method={self.method!r},
                Uopt=<{type(self.Uopt).__name__} at {id(self.Uopt):#018x}>,
                relative_error={self.relative_error!r},
                log=<{type(self.log).__name__} at {id(self.log):#018x}>,
            )"""
        )

    def __str__(self) -> str:
        return textwrap.dedent(
            f"""\
            Output information for the optimization step of the lmlra function:
                message : {self.message}
                Uopt : {self.Uopt}
                method : {self.method}
                relative_error : {self.relative_error}
                log : {type(self.log)}
            """
        )


@dataclass
class LMLRAInfo:
    """Output information of the intermediate steps for :func:`lmlra`."""

    initialization_info: LMLRAInitializationInfo
    """Output from the initialization step."""

    optimization_info: LMLRAOptimizationInfo
    """Output of the optimization step."""

    def __repr__(self) -> str:
        """Create readable text representation."""
        text = f"{type(self).__name__}(\n"
        text += textwrap.indent(
            ",\n".join(
                [
                    repr(self.initialization_info),
                    repr(self.optimization_info),
                ]
            ),
            "    ",
        )
        text += ",\n)"

        return text

    def __str__(self) -> str:
        return (
            "Output information for the intermediate steps of the lmlra function: "
            "initialization_info, optimization_info."
        )


# set options defaults
Options.set_defaults(lmlra_mansd, LMLRAMansdOptions)
Options.set_defaults(lmlra_mantr, LMLRAMantrOptions)
Options.set_defaults(lmlra_hooi, LMLRAHooiOptions)
Options.set_defaults(lmlra_nls, LMLRANlsOptions)
Options.set_defaults(lmlra_minf, LMLRAMinfOptions)


def lmlra(
    T: TensorType,
    core_shape: Shape,
    initialization: TuckerTensor | LMLRAInitializationFcn = mlsvd,
    optimization: LMLRAOptimizerFcn = lmlra_hooi,
    options: Options | None = None,
    print_steps: bool = True,
) -> tuple[TuckerTensor, LMLRAInfo]:
    """Compute a low multilinear rank approximation of a tensor.

    Computes the factor matrices and core tensor belonging to an LMLRA of the N-th order
    tensor `T`. This is done by first determining an initialization (if not provided
    explicitly) and then refining this initial guess using one of the optimization-based
    methods.

    Parameters
    ----------
    T : TensorType
        Tensor to be approximated with an LMLRA.
    core_shape : Shape
        The shape of the core tensor of the LMLRA. The multilinear rank of the result is
        bounded by this parameter.
    initialization : TuckerTensor | LMLRAInitializationFcn, default = mlsvd
        The LMLRA initialization method for the subsequent optimization step. Examples:
        :func:`.mlsvd`, :func:`.mlsvd_rsi`, or
        :meth:`.TuckerTensor.random_like`.
    optimization : LMLRAOptimizerFcn, default = lmlra_hooi
        The optimization method that is used to compute the LMLRA. Examples:
        :func:`lmlra_hooi` and :func:`lmlra_mantr`.
    options: Options, optional
        Options for `optimization`. If set to None, the defaults from the optimization
        method are used. See the documentation of the optimization method for more
        details.
    print_steps : bool, default = True
        Enable or suppress printing of intermediate steps.

    Returns
    -------
    Tlmlra : TuckerTensor
        The computed LMLRA of `T`
    info : LMLRAInfo
        Output information for the initialization and optimization steps.

    See Also
    --------
    lmlra_hooi, lmlra_mantr, lmlra_mansd
    """
    # set printer
    cond_print = conditional_printer(print_steps)

    # Step 1: Initialize the factor matrices, unless the user has already provided them.
    if isinstance(initialization, TuckerTensor):
        v = tuple(s1 != s2 for s1, s2 in zip(initialization.core_shape, core_shape))
        if any(v):
            k = findfirst(v)
            raise ValueError(
                f"dimension of the {k}th mode of the core in the initialization is "
                f"{initialization.core_shape[k]}; expected {core_shape[k]}"
            )
        init_method: LMLRAInitializationMethods | LMLRAInitializationFcn = (
            "manual with estimation"
        )
        if np.isnan(initialization._data).any():
            core_available = np.isfinite(initialization.core).all()
            factors_available = [np.isfinite(f).all() for f in initialization.factors]
            message = (
                "Initialization is manual with nan "
                "entries estimated from available data"
            )
            if not core_available and all(factors_available):
                # determine core
                factors = [tlb.pinv(f) for f in initialization.factors]
                S0 = tmprod(T, factors, range(T.ndim))
                initial = TuckerTensor(initialization.factors, np.array(S0))
            elif core_available and factors_available.count(np.False_) == 1:
                # determine single missing factor
                n = factors_available.index(np.False_)
                inverted_factors = [
                    f.T if i == n else tlb.pinv(f)
                    for i, f in enumerate(initialization.factors)
                ]
                Y = mtkronprod(T, inverted_factors, n, "H")
                A = tens2mat(initialization.core, n)
                X, _, _, _ = tlb.lstsq(A.T, Y.T, rcond=None)
                factors = list(initialization.factors)
                factors[n] = cast(MatrixType, X).T
                initial = TuckerTensor(factors, initialization.core)
            else:
                raise ValueError(
                    "provided TuckerTensor for initialization has a missing entries "
                    "pattern that is unsupported"
                )
        else:
            initial = initialization
            init_method = "manual"
            message = "Initialization is manual"
    else:
        try:
            computed_init = initialization(T, core_shape)
            if isinstance(computed_init, tuple):
                initial = computed_init[0]
            else:
                initial = computed_init
            assert isinstance(initial, TuckerTensor)
        except Exception as e:
            raise ValueError(
                f"initialization function has failed to return a TuckerTensor: \n\t{e}"
            )

        init_method = initialization
        message = f"Initialization is {get_name(init_method)}"
    cond_print(f"Step 1: {message}... ", end="")
    initialization_error = frob(residual(T, initial)) / frob(T)
    initialization_info = LMLRAInitializationInfo(
        message=message,
        Uinit=initial,
        method=init_method,
        relative_error=initialization_error,
    )
    cond_print(f"relative error = {initialization_error}")

    # Step 2: Optimize
    message = f"Optimization is {get_name(optimization)}"
    cond_print(f"Step 2: {message}... ", end="")
    if options is None:
        options = Options.get_defaults(optimization)
    if not print_steps:
        options.display = 0
    try:
        Uopt, logger = optimization(T, initial, options)
        assert isinstance(Uopt, TuckerTensor)
    except Exception as e:
        raise ValueError(
            f"optimization function has failed to return a TuckerTensor: \n\t{e}"
        )
    optimization_error = frob(residual(T, Uopt)) / frob(T)
    cond_print(f"relative error = {optimization_error}")
    optimization_info = LMLRAOptimizationInfo(
        message=message,
        Uopt=Uopt,
        relative_error=optimization_error,
        method=optimization,
        log=logger,
    )

    # The result
    Tlmlra = Uopt
    info = LMLRAInfo(
        initialization_info=initialization_info,
        optimization_info=optimization_info,
    )

    return Tlmlra, info

r"""General CPD routine.

In a polyadic decomposition, an Nth-order tensor :math:`\mathcal{A}` with dimensions
:math:`I_{0} \times I_{1} \times \cdots \times I_{N-1}` is expressed by a rank-:math:`R`
tensor :math:`\ten{T}` given by

.. math::

   \ten{T} = \sum_{r=0}^{R-1} \vec{u}^{(0)}_r \op \vec{u}^{(1)}_r \op
    \cdots \op \vec{u}^{(N-1)}_r.

In pyTensorlab, such a structured tensor can be formed with the class
:class:`.PolyadicTensor`. A canonical polyadic  decomposition (CPD)
is a polyadic tensor of minimal rank.

Functions
---------
The general routine to compute a CPD is :func:`cpd`. This function applies a four stage
process consisting of a compression step that compresses the tensor, an initialization
step that provides an initial guess/estimate, an optimization step that improves
on this initial/estimate, and a refinement step that performs further refinements on
the tensor after decompression.

Examples
--------
>>> import pytensorlab as tl
>>> shape = (5, 6, 7)
>>> nterm = 2
>>> T = tl.random.rand(shape)
>>> Tcpd, _ = tl.cpd(T, nterm)
"""

import math
import textwrap
import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from functools import singledispatch
from typing import (
    Any,
    Literal,
    Protocol,
    cast,
    runtime_checkable,
)

import numpy as np
from numpy.linalg import LinAlgError

import pytensorlab.backends.numpy as tlb
from pytensorlab.datatypes.partial import IncompleteTensor
from pytensorlab.optimization import (
    OptimizationProgressLogger,
    conditional_printer,
)
from pytensorlab.typing import MatrixType, Shape, TensorType
from pytensorlab.typing.validators import NonnegativeFloat, PositiveInt
from pytensorlab.util import Options, get_name
from pytensorlab.util.exceptions import ShapeMismatchException
from pytensorlab.util.utils import inprod_kr

from ..datatypes import (
    PolyadicTensor,
    Tensor,
    TuckerTensor,
    frob,
    residual,
    tens2mat,
    tmprod,
)
from ..datatypes.core import _tmprod
from ..random.rng import get_rng
from ..util import kr, pretty_repr
from .cpd_gevd import cpd_gevd, fit_rank1
from .cpd_opt import cpd_nls
from .mlsvd import mlsvd_rsi


@runtime_checkable
class CompressFcn(Protocol):
    """Signature for a tensor compression function.

    Computes a compressed version of the tensor `T` in `TuckerTensor` format for a given
    core shape.

    Parameters
    ----------
    T : TensorType
        Tensor to be compressed.
    coreshape : Shape
        Shape of the compressed tensor.

    Returns
    -------
    TuckerTensor
        Compressed tensor with given core shape.
    Any
        Any additional output of the algorithm.

    See Also
    --------
    :func:`.mlsvd`, :func:`.mlsvd_rsi`, :func:`.lmlra`
    """

    def __call__(
        self, T: TensorType, coreshape: Shape, /
    ) -> tuple[TuckerTensor, Any]: ...


@runtime_checkable
class CPDInitializationFcn(Protocol):
    """Signature for a CPD initialization function.

    Compute or create an initialization for a CPD algorithm, i.e., a
    `PolyadicTensor` with the given number of rank-1 terms.

    Parameters
    ----------
    T : TensorType
        Tensor for which the initialization is created.
    nterm : int
        Number of rank-1 terms of the initialization.

    Returns
    -------
    PolyadicTensor
        Initialization with `nterm` terms and the same shape as `T`.

    See Also
    --------
    :func:`.cpd_gevd`, .PolyadicTensor.randn_like, .cpd_svd
    """

    def __call__(self, T: TensorType, nterm: int, /) -> PolyadicTensor: ...


def cpd_svd(T: TensorType, nterm: int) -> PolyadicTensor:
    """Compute the CPD of a matrix by singular value decomposition.

    Compute a CPD for tensors that behave like matrices, i.e., only two dimensions of
    the higher-order tensor are not equal to one. The CPD is computed by means
    of a (multilinear) singular value decomposition.

    Parameters
    ----------
    T : TensorType
        Tensor for which the CPD is computed.
    nterm : int
        Number of rank-1 terms in the CPD.

    Returns
    -------
    PolyadicTensor
        A polyadic decomposition of `T` with `nterm` terms.

    See Also
    --------
    cpd, .cpd_gevd.cpd_gevd, .cpd_nls, .cpd_minf
    """
    nonsingleton = [i for i, s in enumerate(T.shape) if s > 1]
    if len(nonsingleton) != 2:
        raise ValueError(
            "not a matrix; expected 2 axes not equal to one in dimension "
            f"but got {len(nonsingleton)}"
        )
    factors = [np.ones((1, nterm))] * T.ndim
    i, j = nonsingleton
    R = min(min(T.shape[i], T.shape[j]), nterm)
    M = np.squeeze(np.asarray(T))
    U, sv, Vh = tlb.svd(M, full_matrices=False)
    sqrtsv = np.sqrt(sv[:R])
    factors[i] = np.hstack((sqrtsv * U[:, :R], np.zeros((T.shape[i], nterm - R))))
    factors[j] = np.hstack((sqrtsv * Vh[:R, :].T, np.zeros((T.shape[j], nterm - R))))

    return PolyadicTensor(factors)


@runtime_checkable
class CPDOptimizeFcn(Protocol):
    """Signature for a CPD optimization algorithm.

    Compute a `PoladicTensor` by optimizing a CPD objective function.

    Parameters
    ----------
    T : TensorType
        Tensor for which a CPD is computed.
    Uinit : PolyadicTensor
        The initialization for the optimization algorithm.
    options : Options
        The options to be passed on the optimization algorithm; see selected
        algorithm for details.

    Returns
    -------
    PolyadicTensor
        The computed CPD of `T`.
    OptimizationProgressLogger
        Extra information logged by the algorithm.

    See Also
    --------
    .cpd_als, .cpd_minf, .cpd_nls, .cpd_nls_scipy
    """

    def __call__(
        self, T: TensorType, Uinit: PolyadicTensor, options: Options = ..., /
    ) -> tuple[PolyadicTensor, OptimizationProgressLogger]: ...


@singledispatch
def estimate_remaining(T: TensorType, U: PolyadicTensor) -> PolyadicTensor:
    """Estimate one or more missing factors in a `PolyadicTensor`.

    Given at least one factor matrix, the remaining factor matrices are computed using
    least squares. The factors that need to be estimated are indicated by having at
    least one nan entry.

    Parameters
    ----------
    T : TensorType
        Tensor for which a CPD is computed.
    U : PolyadicTensor
        The (incomplete) PolyadicTensor with missing entries.

    Returns
    -------
    PolyadicTensor
        The reconstructed `PolyadicTensor` to be used.

    Examples
    --------
    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> U = tl.PolyadicTensor.random((5, 7, 6, 4), 2)
    >>> T = np.array(U)
    >>> Uinit = U.copy(); Uinit.factors[2][:] = np.nan
    >>> Ures = tl.estimate_remaining(T, Uinit)
    >>> bool(U.error(Ures) < [0, 0, 5E-16 ,0])
    True

    See Also
    --------
    cpd
    """
    raise NotImplementedError


@estimate_remaining.register
def _estimate_remaining_array(T: np.ndarray, U: PolyadicTensor) -> PolyadicTensor:
    given = tuple((i, f) for i, f in enumerate(U.factors) if not np.any(np.isnan(f)))
    ind, factors = list(zip(*given))
    factors = cast(tuple[MatrixType, ...], factors)
    M = tens2mat(T, cast(tuple[int, ...], ind))
    M = kr(*factors).conj().T @ M
    W = inprod_kr(factors, factors)
    if tlb.cond(W) < 1e12:
        Uother = tlb.solve_hermitian(W, M)
    else:
        raise LinAlgError("given known matrices are badly conditioned")

    other, shape = list(
        zip(*tuple((i, s) for i, s in enumerate(T.shape) if i not in ind))
    )
    Ures = U.copy()
    if len(ind) == T.ndim - 1:
        Ures.factors[other[0]][:] = Uother.T[:]
    else:
        Utmp = fit_rank1(np.reshape(Uother, (U.nterm,) + shape))
        for i, f in zip(other, Utmp):
            Ures.factors[i][:] = f
    return Ures


@dataclass
class CPDCompressionInfo:
    """Output information for the compression step in :func:`cpd`."""

    message: str
    """Description of performed action."""

    Tcompressed_core: TensorType
    """Resulting core tensor of the compression step. 
    
    In case compression is skipped, this attribute is set to the original tensor.
    """

    Tcompressed_factors: Sequence[MatrixType]
    """Factors of the output of the compression step. 
    
    In case compression is skipped, an empty list is returned.
    """

    relative_error: NonnegativeFloat
    """Relative Frobenius norm error introduced by the compression algorithm."""

    log: Any
    """Additional information logged by the compression algorithm."""

    ratio: float
    """Ratio of number of entries after compression versus original tensor."""

    method: CompressFcn | None
    """Method of compression.

    If compression is skipped, this is set to None.
    """

    def __repr__(self) -> str:
        """Create readable text representation."""
        core = self.Tcompressed_core

        if self.Tcompressed_factors is not None:
            factors_type = f"<list of {len(self.Tcompressed_factors)} arrays>"
        else:
            factors_type = None

        if isinstance(self.log, tuple):
            log_type = f"<tuple of {len(self.log)} arrays>"
        else:
            log_type = f"<{type(self.log).__name__} at {id(self.log):#018x}>"

        return textwrap.dedent(
            f"""\
            {type(self).__name__}(
                message={self.message!r},
                method={self.method!r},
                Tcompressed_core=<{type(core).__name__} at {id(core):#018x}>,
                Tcompressed_factors={factors_type},
                ratio={self.ratio!r},
                relative_error={self.relative_error!r},
                log={log_type},
            )"""
        )

    def __str__(self) -> str:
        return textwrap.dedent(
            f"""\
            Output information for the compression step of the cpd function:
                message : {self.message}
                Tcompressed_core : {pretty_repr(self.Tcompressed_core)}
                Tcompressed_factors : {pretty_repr(self.Tcompressed_factors)}
                relative_error : {self.relative_error}
                log : {type(self.log)}
                ratio : {self.ratio}
                method : {self.method}
            """
        )


CPDInitializationMethod = (
    Literal["manual"]
    | Literal["manual with random"]
    | Literal["manual with estimation"]
)


@dataclass
class CPDInitializationInfo:
    """Output information for the initialization step in :func:`cpd`."""

    message: str
    """Description of performed action."""

    Uinit: TensorType
    """Output of the initialization step."""

    method: CPDInitializationMethod | CPDInitializationFcn
    """Method of initialization."""

    relative_error: NonnegativeFloat
    """Relative Frobenius norm of the error at the initialization step."""

    def __repr__(self) -> str:
        """Create readable text representation."""
        return textwrap.dedent(
            f"""\
            {type(self).__name__}(
                message={self.message!r},
                method={self.method!r},
                Uinit=<{type(self.Uinit).__name__} at {id(self.Uinit):#018x}>,
                relative_error={self.relative_error!r},
            )"""
        )

    def __str__(self) -> str:
        return textwrap.dedent(
            f"""\
            Output information for the initialization step of the cpd function:
                message : {self.message}
                Uinit : {self.Uinit}
                method : {self.method}
                relative_error : {self.relative_error}
            """
        )


@dataclass
class CPDOptimizationInfo:
    """Output information for the optimization step in :func:`cpd`."""

    message: str
    """Description of performed action."""

    Uopt: PolyadicTensor
    """Output of the optimization step."""

    method: CPDOptimizeFcn
    """Method of optimization."""

    relative_error: NonnegativeFloat
    """Relative Frobenius norm error after the optimization step."""

    log: OptimizationProgressLogger
    """Additional information logged by the optimization algorithm."""

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
            Output information for the optimization step of the cpd function:
                message : {self.message}
                Uopt : {self.Uopt}
                method : {self.method}
                relative_error : {self.relative_error}
                log : {type(self.log)}
            """
        )


@dataclass
class CPDDecompressionInfo:
    """Output information for the decompression step in :func:`cpd`."""

    message: str
    """Description of performed action."""

    Udecomp: TensorType
    """Output of the decompression step."""

    relative_error: NonnegativeFloat
    """Relative Frobenius norm of the error after the decompression step."""

    is_decompressed: bool
    """A boolean specifying whether decompression has occurred."""

    def __repr__(self) -> str:
        """Create readable text representation."""
        return textwrap.dedent(
            f"""\
            {type(self).__name__}(
                message={self.message!r},
                is_decompressed={self.is_decompressed!r},
                Udecomp=<{type(self.Udecomp).__name__} at {id(self.Udecomp):#018x}>,
                relative_error={self.relative_error!r},
            )"""
        )

    def __str__(self) -> str:
        return textwrap.dedent(
            f"""\
            Output information for the decompression step of the cpd function:
                message : {self.message}
                Udecomp : {self.Udecomp}
                relative_error : {self.relative_error}
                is_decompresed : {self.is_decompressed}
            """
        )


@dataclass
class CPDRefinementInfo:
    """Output information for the refinement step in :func:`cpd`."""

    message: str
    """Description of performed action."""

    Uref: PolyadicTensor
    """Output of the refinement step."""

    relative_error: NonnegativeFloat
    """Method of refinement."""

    method: CPDOptimizeFcn | None
    """Relative Frobenius norm of the error after the refinement step."""

    log: OptimizationProgressLogger | None
    """Additional information logged by the refinement algorithm."""

    def __repr__(self) -> str:
        """Create readable text representation."""
        if self.log is not None:
            log = f"<{type(self.log).__name__} at {id(self.log):#018x}>"
        else:
            log = None

        return textwrap.dedent(
            f"""\
            {type(self).__name__}(
                message={self.message!r},
                method={self.method!r},
                Uref=<{type(self.Uref).__name__} at {id(self.Uref):#018x}>,
                relative_error={self.relative_error!r},
                log={log},
            )"""
        )

    def __str__(self) -> str:
        return textwrap.dedent(
            f"""\
            Output information for the refinement step of the cpd function:
                message : {self.message}
                Uref : {self.Uref}
                relative_error : {self.relative_error}
                method : {self.method}
                log : {type(self.log)}
            """
        )


@dataclass
class CPDInfo:
    """Output information for the intermediate steps of :func:`cpd`."""

    compression_info: CPDCompressionInfo
    """Output from the compression step."""

    initialization_info: CPDInitializationInfo
    """Output from the initialization step."""

    optimization_info: CPDOptimizationInfo
    """Output of the optimization step."""

    decompression_info: CPDDecompressionInfo
    """Output of the decompression step."""

    refinement_info: CPDRefinementInfo
    """Output of the refinement step."""

    def __repr__(self) -> str:
        """Create readable text representation."""
        text = f"{type(self).__name__}(\n"
        text += textwrap.indent(
            ",\n".join(
                [
                    repr(self.compression_info),
                    repr(self.initialization_info),
                    repr(self.optimization_info),
                    repr(self.decompression_info),
                    repr(self.refinement_info),
                ]
            ),
            "    ",
        )
        text += ",\n)"

        return text

    def __str__(self) -> str:
        return (
            "Info about intermediate steps of cpd: "
            "compression_info, initialization_info, optimization_info, "
            "decompression_info, refinement_info."
        )


def determine_compression_strategy(
    T: TensorType, nterm: PositiveInt, compress: CompressFcn | bool
) -> tuple[CompressFcn | None, float, str]:
    """Determine the compression strategy for CPD compression step.

    Determines which compression algorithm should be used or if the compression step
    should be skipped in :func:`cpd`.

    Parameters
    ----------
    T : TensorType
        Tensor for which a CPD is computed.
    nterm : PositiveInt
        Number of rank-1 terms in the polyadic decomposition.
    compress : CompressFcn | bool
        The compression algorithm to apply. If True, the algorithm is chosen depending
        on the original tensor. If False, compression is skipped.

    Returns
    -------
    compression : CompressFcn | None
        Compression function or None if no compression is needed.
    ratio : float
        Ratio of the number of entries in the compressed tensor versus the number of
        entries in the original tensor.
    message : str
        Description and motivation of the chosen compression strategy.

    See Also
    --------
    cpd
    """
    core_shape = min(tuple(T.shape), tuple(nterm * np.ones(T.ndim, dtype=int)))
    ratio = float(math.prod(core_shape) / math.prod(T.shape))

    compression: CompressFcn | None = None
    if nterm == 1:
        reason = "nterm = 1"
    elif isinstance(T, IncompleteTensor):
        reason = "incomplete tensor"
    elif sum(np.array(T.shape) > 1) <= 2:
        reason = "sum(np.array(T.shape) > 1) <= 2"
    elif not compress:
        reason = "requested by user"
    elif compress is True:
        if ratio < 0.5:
            compression = mlsvd_rsi
        sign = "<" if ratio < 0.5 else ">="
        reason = f"compression ratio {ratio:.3} {sign} 0.5"
    elif isinstance(compress, CompressFcn):
        compression = compress
        reason = "requested by user"
    else:
        reason = "invalid option"

    message = (
        f"Compression is {get_name(compression) if compression else 'skipped'} "
        f"({reason})"
    )

    return compression, ratio, message


def determine_initialization_strategy(
    T: TensorType,
    nterm: PositiveInt,
    initialization: CPDInitializationFcn | None = None,
) -> tuple[CPDInitializationFcn, str]:
    """Determine the initialization strategy for CPD optimization step.

    Evaluates which initialization method should be used in the optimization step of
    :func:`cpd`.

    Parameters
    ----------
    T : TensorType
        Tensor for which a CPD is computed.
    nterm : PositiveInt
        Number of rank-1 terms in the polyadic decomposition.
    initialization : CPDInitializationFcn, optional
        The initialization algorithm to use if provided.

    Returns
    -------
    initialization : CPDInitializationFcn
        The initialization algorithm to be used in :func:`cpd`.
    message : str
        Description and motivation of the chosen initialization strategy.

    See Also
    --------
    cpd
    """
    if initialization is None:
        if isinstance(T, np.ndarray) and sum(s > 1 for s in T.shape) == 2:
            initialization = cpd_svd
            reason = "matrix input"
        elif isinstance(T, np.ndarray) and sum(np.array(T.shape) >= nterm) >= 2:
            initialization = cpd_gevd
            reason = "sum(np.array(T.shape) >= nterm) >= 2"
        else:
            initialization = PolyadicTensor.randn_like
            reason = "default"
    else:
        reason = "requested by user"
    message = f"Initialization is {get_name(initialization)} ({reason})"
    return initialization, message


def set_initialization(
    T: TensorType,
    nterm: PositiveInt,
    initialization: PolyadicTensor,
    _rng: np.random.Generator | int | None = None,
) -> tuple[PolyadicTensor, str, CPDInitializationMethod | CPDInitializationFcn]:
    """Set the initialization for CPD optimization step.

    Sets the initialization for the CPD optimization step in case an explicit
    PolyadicTensor is provided as an input. In case this PolyadicTensor contains factors
    with nan entries, it is attempted to estimate these nan entries from `T` through a
    call to :func:`estimate_remaining`. If the latter fails, the nan entries are filled
    in randomly.

    Parameters
    ----------
    T : TensorType
        Tensor for which a CPD is computed.
    nterm : PositiveInt
        Number of rank-1 terms in the polyadic decomposition.
    initialization : PolyadicTensor
        The provided initialization by the user.
    _rng : numpy.random.Generator | int, optional
        Seed or random number generator used for all random operations in this
        function. If an integer is given, a new generator is created with that seed. If
        a generator is provided, it is used directly. If None, the global generator
        (set via `set_rng`) is used.

    Returns
    -------
    Uinit : PolyadicTensor
        The initialization to be used by the optimization algorithm.
    message : str
        Description and motivation for the initialization strategy.
    method : InitializationMethod | CPDInitializationFcn
        Method of initialization.

    See Also
    --------
    estimate_remaining, cpd
    """
    randn = get_rng(_rng).standard_normal

    if nterm != initialization.nterm:
        raise ValueError(
            f"provided initialization contains {initialization.nterm} rank-1 "
            f"terms; expected {nterm} rank-1 terms"
        )
    if initialization.ndim != T.ndim:
        raise ValueError(
            f"ndim of initialization does not match ndim of data T; "
            f"got {initialization.ndim} but expected {T.ndim}"
        )
    if initialization.shape != T.shape:
        raise ShapeMismatchException(T.shape, initialization.shape)

    nanfactors = [np.any(np.isnan(f)) for f in initialization.factors]
    method: str | CPDInitializationFcn
    if np.any(nanfactors):
        if np.all(nanfactors):
            Uinit = PolyadicTensor.randn_like(T, nterm, _rng=_rng)
            message = (
                f"Initialization is {get_name(PolyadicTensor.randn_like)} "
                f"(all factors in U contain nan entries)"
            )
            method = PolyadicTensor.randn_like
        else:
            try:
                Uinit = estimate_remaining(T, initialization)
                message = "Initialization is manual with estimation of nan entries"
                method = cast(CPDInitializationMethod, "manual with estimation")
            except LinAlgError as e:
                if "conditioned" in e.args[0]:
                    Uinit = PolyadicTensor(
                        [
                            (randn((f.shape[0], nterm)) if np.any(np.isnan(f)) else f)
                            for f in initialization.factors
                        ]
                    )
                    message = (
                        "Initialization is partially random "
                        "(estimation of nan factors is not possible)"
                    )
                    method = cast(CPDInitializationMethod, "manual with random")
                else:
                    raise e
    else:
        Uinit = initialization
        message = "Initialization is manual"
        method = cast(CPDInitializationMethod, "manual")

    return Uinit, message, method


def determine_refinement_strategy(
    T: TensorType,
    refinement: CPDOptimizeFcn | bool,
    optimization: CPDOptimizeFcn,
    is_compressed: bool,
    optimization_error: NonnegativeFloat,
    refinement_options: Options | None = None,
    optimization_options: Options | None = None,
    continue_refinement_threshold: NonnegativeFloat = 1e-8,
) -> tuple[CPDOptimizeFcn | None, Options | None, str]:
    """Determine the refinement strategy for CPD refinement step.

    Determines which optimization algorithm should be used in the refinement step or if
    this step should be skipped altogether in :func:`cpd`.

    Parameters
    ----------
    T : TensorType
        Tensor for which a CPD is computed.
    refinement : CPDOptimizeFcn | bool, default = True
        Algorithm to use for the refinement step.

        If True, select the algorithm and options automatically. If False, refinement
        is disabled. Examples of refinement algorithms are :func:`.cpd_als`,
        :func:`.cpd_minf`, :func:`.cpd_nls` and :func:`.cpd_nls_scipy`.
    optimization : CPDOptimizeFcn, default = cpd_nls
        The optimization algorithm that was used in the optimization step of
        :func:`cpd`.
    is_compressed: bool
        Whether compression of the tensor has been performed in :func:`cpd`.
    optimization_error: NonnegativeFloat
        Approximation error of the computed decomposition after the optimization step.
    refinement_options : Options, optional
        The options to be passed on the optimization algorithm of the refinement step.
        If set to None, the default options of that optimization algorithm will be
        used.
    optimization_options : Options, optional
        The options that were used in the optimization algorithm of the optimization
        step in :func:`cpd`. If set to None, the default options were used in the
        optimization step. These options are only used if `refinement_options` are not
        given.
    continue_refinement_threshold : NonnegativeFloat, default = 1e-8
        Threshold for the relative Frobenius norm error of the computed result in the
        case the data to be decomposed is a structured tensor, i.e., a subclass of
        `Tensor`. For structured tensors, the relative error is typically limited by
        the square root of the machine precision due to numerical loss of precision. If
        the error is below this threshold, the refinement step is disabled and no longer
        pursued.

    Returns
    -------
    refine : CPDOptimizeFcn | None
        The chosen refinement algorithm if refinement is needed.
    options : Options | None
        The chosen options for the refinement algorithm.
    message : str
        Description and motivation of the chosen refinement strategy.

    See Also
    --------
    cpd
    """
    refine: CPDOptimizeFcn | None = None
    refine_options: Options | None = None
    if not is_compressed:
        reason = "no compression"
    elif refinement is False:
        reason = "requested by user"
    elif isinstance(T, Tensor) and optimization_error < continue_refinement_threshold:
        reason = "numerical accuracy reached"
        warnings.warn(
            (
                "relative error after decompression has reached threshold of "
                f"{continue_refinement_threshold} for structured tensors; further "
                "refinement is not possible; run cpd on np.array(T) if a higher "
                "accuracy is desired"
            ),
            UserWarning,
        )
    elif refinement is True:
        refine = optimization
        if not refinement_options:
            refine_options = optimization_options
        reason = "same as optimization step"
    else:
        refine = refinement
        refine_options = refinement_options
        reason = "requested by user"

    if refine and refine_options is None:
        if optimization_options and refine == optimization:
            refine_options = optimization_options

    message = f"Refinement is {get_name(refine) if refine else 'skipped'} ({reason})"

    return refine, refine_options, message


def cpd(
    T: TensorType,
    nterm: PositiveInt,
    compression: CompressFcn | bool = True,
    compression_options: dict[str, Any] | None = None,
    initialization: PolyadicTensor | CPDInitializationFcn | None = None,
    initialization_options: dict[str, Any] | None = None,
    optimization: CPDOptimizeFcn = cpd_nls,
    optimization_options: Options | None = None,
    refinement: CPDOptimizeFcn | bool = True,
    refinement_options: Options | None = None,
    print_steps: bool = True,
) -> tuple[PolyadicTensor, CPDInfo]:
    """Compute a canonical polyadic decomposition of a tensor.

    Computes the factor matrices belonging to a canonical polyadic decomposition of
    the N-th order tensor `T` in `nterm` rank-1 terms.

    Parameters
    ----------
    T : TensorType
        Tensor for which a CPD is computed.
    nterm : PositiveInt
        Number of rank-1 terms in the polyadic decomposition.
    compression : CompressFcn | bool, default = True
        Whether or not compression of the tensor is attempted in the CPD routine.
        In case set to True, an appropriate compression algorithm will be determined
        as specified in :func:`determine_compression_strategy`. Alternatively, a
        compression algorithm can be manually provided.
    compression_options : dict[str, Any], default = {}
        The options to be passed on to the compression algorithm.
    initialization : PolyadicTensor | CPDInitializationFcn, optional
        Provide an initialization for the CPD routine either in the form a
        `PolyadicTensor` or initialization algorithm; see, e.g., :func:`cpd` or
        :meth:`.PolyadicTensor.randn_like`. If set to None, an initialization
        will be performed as specified in :func:`determine_initialization_strategy`.
    initialization_options : dict[str, Any], default = {}
        The options to be passed on to the initialization algorithm.
    optimization : CPDOptimizeFcn, default = cpd_nls
        The optimization algorithm to be used in the computation of the CPD. Examples
        are :func:`.cpd_als`, :func:`.cpd_minf`, :func:`.cpd_nls` or
        :func:`.cpd_nls_scipy`.
    optimization_options: Options, optional
        The options to be passed on to the optimization algorithm. If not given, default
        options corresponding to `optimization` are used.
    refinement : CPDOptimizeFcn[Options] | bool, default = True
        Whether or not refinement of computed CPD in the optimization step is attempted
        in the CPD routine. If True, an appropriate refinement algorithm will be
        determined as per specified in
        :func:`determine_compression_strategy`. Alternatively, one can manually specify
        a refinement algorithm.
    refinement_options : Options, optional
        The options to be passed on to the refinement algorithm. Only used if
        `refinement` is not False. If not given, appropriate options are determined as
        per specified in :func:`determine_compression_strategy`.
    print_steps : bool, default = True
        Enable or suppress printing of intermediate steps.

    Returns
    -------
    Ures : PolyadicTensor
        Resulting polyadic decomposition.
    info : CPDInfo
        Output information on the intermediate steps.

    See Also
    --------
    .cpd_nls, .cpd_nls_scipy, .cpd_minf, .cpd_als, .cpd_gevd.cpd_gevd, :func:`.mlsvd`,
    .lmlra.lmlra
    """
    if isinstance(nterm, PolyadicTensor):
        raise ValueError(
            "nterm should be a positive integer; "
            "use initialization to provide an initial guess"
        )
    if compression_options is None:
        compression_options = {}
    if initialization_options is None:
        initialization_options = {}
    # set printer
    cond_print = conditional_printer(print_steps)

    # Step 1: Compression.
    compress, ratio, message = determine_compression_strategy(T, nterm, compression)
    cond_print(f"Step 1: {message}... ", end="")
    if compress is None:
        Tcompressed_core = T
        Tcompressed_factors: Sequence[MatrixType] = []
        output = None
        compression_error = 0.0
    else:
        coreshape = tuple(min(nterm, s) for s in T.shape)
        try:
            Tc, output = compress(T, coreshape, **compression_options)
            assert isinstance(Tc, TuckerTensor)
        except Exception as e:
            raise ValueError(
                f"compression function has failed to return a TuckerTensor:\n\t{e}"
            )
        Tcompressed_core, Tcompressed_factors = Tc.core, Tc.factors
        compression_error = frob(residual(T, Tc)) / frob(T)
    compression_info = CPDCompressionInfo(
        message=message,
        Tcompressed_core=Tcompressed_core,
        Tcompressed_factors=Tcompressed_factors,
        relative_error=compression_error,
        log=output,
        ratio=ratio,
        method=compress,
    )
    cond_print(f"relative error = {compression_error:.6}")

    # Step 2: Initialize the factor matrices unless they were all provided by the user.
    if isinstance(initialization, PolyadicTensor):
        Uinit, message, init_method = set_initialization(T, nterm, initialization)
        cond_print(f"Step 2: {message}... ", end="")
        if compression and Tcompressed_factors:
            Uinit = tmprod(
                Uinit, Tcompressed_factors, tuple(range(T.ndim)), transpose="H"
            )
    else:
        initialization, message = determine_initialization_strategy(
            Tcompressed_core, nterm, initialization
        )
        cond_print(f"Step 2: {message}... ", end="")
        try:
            Uinit = initialization(Tcompressed_core, nterm, **initialization_options)
            assert isinstance(Uinit, PolyadicTensor)
        except Exception as e:
            raise ValueError(
                f"initialization function has failed to return a PolyadicTensor:\n\t{e}"
            )
        init_method = initialization
    initialization_error = frob(residual(Tcompressed_core, Uinit)) / frob(
        Tcompressed_core
    )
    initialization_info = CPDInitializationInfo(
        message=message,
        Uinit=Uinit,
        method=init_method,
        relative_error=initialization_error,
    )
    cond_print(f"relative error = {initialization_error:.6}.")

    # Step 3: Optimize
    if compress:
        message = f"Optimization is {get_name(optimization)} on the compressed tensor"
    else:
        message = f"Optimization is {get_name(optimization)} on the uncompressed tensor"
    cond_print(f"Step 3: {message}... ", end="")
    try:
        if optimization_options is None:
            optimization_options = Options.get_defaults(optimization)
        if not print_steps:
            optimization_options.display = 0
        Uopt, opt_logger = optimization(Tcompressed_core, Uinit, optimization_options)
        assert isinstance(Uopt, PolyadicTensor)
    except Exception as e:
        raise ValueError(
            f"optimization function has failed to return a PolyadicTensor:\n\t{e}"
        )
    optimization_error = frob(residual(Tcompressed_core, Uopt)) / frob(Tcompressed_core)
    optimization_info = CPDOptimizationInfo(
        message=message,
        Uopt=Uopt,
        relative_error=optimization_error,
        method=optimization,
        log=opt_logger,
    )
    cond_print(f"relative error = {optimization_error:.6}.")

    # Step 4: decompression
    if compress:
        Udecomp = _tmprod(Uopt, Tcompressed_factors, tuple(np.arange(T.ndim)))
        Udecomp = cast(PolyadicTensor, Udecomp)
        decompression_error = frob(residual(T, Udecomp)) / frob(T)
        decompress = True
        message = "Decompression has been performed"
    else:
        Udecomp = Uopt
        decompression_error = optimization_error
        decompress = False
        message = "Decompression is skipped"
    decompression_info = CPDDecompressionInfo(
        message=message,
        Udecomp=Udecomp,
        relative_error=decompression_error,
        is_decompressed=decompress,
    )
    cond_print(f"Step 4: {message}... ", end="")
    cond_print(f"relative error = {decompression_error:.6}.")

    # Step 5: Refinement
    refine, refinement_options, message = determine_refinement_strategy(
        T,
        refinement,
        optimization,
        compress is not None,
        optimization_error,
        refinement_options=refinement_options,
        optimization_options=optimization_options,
    )
    cond_print(f"Step 5: {message}... ", end="")
    ref_logger: OptimizationProgressLogger | None
    if refine:
        try:
            if refinement_options is None:
                refinement_options = Options.get_defaults(refine)
            if not print_steps:
                refinement_options.display = 0
            Uref, ref_logger = refine(T, Udecomp, refinement_options)
            assert isinstance(Uref, PolyadicTensor)
        except Exception as e:
            raise ValueError(
                f"refinement function has failed to return a PolyadicTensor:\n\t{e}"
            )
        refine_method = refine
    else:
        Uref = Udecomp
        ref_logger = None
        refine_method = None
    refinement_error = frob(residual(T, Uref)) / frob(T)
    refinement_info = CPDRefinementInfo(
        message=message,
        Uref=Uref,
        relative_error=refinement_error,
        method=refine_method,
        log=ref_logger,
    )
    cond_print(f"relative error = {refinement_error:.6}.")

    # The result
    Ures = Uref
    info = CPDInfo(
        compression_info=compression_info,
        initialization_info=initialization_info,
        optimization_info=optimization_info,
        decompression_info=decompression_info,
        refinement_info=refinement_info,
    )

    return Ures, info

r"""Definition of protocols used in the optimization methods.

This module defines the various protocols for ingredients required by optimization
methods, such as the residual, objective function value, gradient, Hessian,
etc. Versions for real and complex optimization variables are available.

Classes
-------
.ResidualFcn
    Function computing the residual.
.ObjectiveFcn
    Function computing the objective function value.
.GradientFcn
    Function computing the gradient.
.JacobianFcn
    Function computing the Jacobian for a nonlinear least-squares problem.
.ComplexJacobianFcn
    Function computing the complex Jacobian for a nonlinear least-squares problem.
.HessianFcn
    Function computing (an approximation of) the Hessian.
.ComplexHessianFcn
    Function computing (an approximation of) the complex Hessian.
.JacobianVectorProductFcn
    Function computing the Jacobian times vector product.
.ComplexJacobianVectorProductFcn
    Function computing the complex Jacobian times vector product.
.HessianVectorProductFcn
    Function computing the Hessian times vector product.
.ComplexHessianVectorProductFcn
    Function computing the complex Hessian times vector product.
.PreconditionerFcn
    Function applying a preconditioner.
.CustomLinearOperator
    Linear operator with typed left and right matrix-vector products.
.IterativeSolver
    Function iteratively solving a linear system.
.IterativeSolverQR
    Function iteratively solving a linear system using QR factorization.
.IterativeSolverOptions
    Default options for iterative solvers.

Examples
--------
Two running examples are used. The first minimization problem computes the best rank-1
approximation of a matrix in least squares sense:

.. math::

    \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
    \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F}.

The objective function value is real, but for complex variables $\vec{a}$ and $\vec{b}$
which are collected in $\vec{z}$, the function depends on $\vec{z}$ and
$\conj{\vec{z}}$, i.e., one has $f(\vec{z}, \conj{\vec{z}})$. In that case, the complex
variants are required, unless in specific cases, such as nonlinear least squares
functions where the residual, i.e., $\vec{F}(\vec{z}) = \vec{a} \vec{b}^{\T} - \mat{M}$,
does not depend on conjugated variables, which is the case here.

The second minimization problem computes the best Hermitian rank-1 approximation of a
complex Hermitian matrix in least squares sense:

.. math::

    \underset{\vec{a}}{\text{minimize}}\ \frac12
     \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F},

In this the residual $\vec{F}(\vec{a}, \conj{\vec{a}}) = \vec{a} \conj{\vec{a}}^{\T} -
\mat{M}$ depends on both $\vec{a}$ and $\conj{\vec{a}}$, i.e., the residual is not
holomorphic, and the complex variants of all methods are required.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Protocol,
    TypeVar,
    overload,
    runtime_checkable,
)

import numpy as np

from pytensorlab.typing import (
    MatrixType,
    NonnegativeFloat,
    NonnegativeInt,
    VectorType,
)
from pytensorlab.typing.core import ArrayType
from pytensorlab.util import Options

if TYPE_CHECKING:

    class LinearOperator:
        """Linear operator."""

        dtype: np.dtype[Any]
        """Data type of the linear operator."""

        ncalls: int
        """Number of times this linear operator is called."""

        def __init__(self, dtype: None, shape: tuple[int, int]) -> None: ...
        def _init_dtype(self) -> None: ...

else:
    from scipy.sparse.linalg import LinearOperator


class CustomLinearOperator(LinearOperator):
    """Linear operator with typed left and right matrix-vector products."""

    def __init__(
        self,
        shape: tuple[int, int],
        matvec: Callable[[VectorType], VectorType],
        /,
        rmatvec: Callable[[VectorType], VectorType] | None = None,
        dtype: np.dtype[Any] | None = None,
    ):
        super().__init__(None, shape)
        self.__matvec_impl = matvec
        self.__rmatvec_impl = rmatvec
        self.ncalls: int = 0
        if dtype is None:
            self._init_dtype()
        else:
            self.dtype = dtype

    def _matvec(self, x: VectorType) -> VectorType:
        self.ncalls += 1
        return self.__matvec_impl(x)

    def _rmatvec(self, x: VectorType) -> VectorType:
        if self.__rmatvec_impl is None:
            raise NotImplementedError("rmatvec is not defined")
        self.ncalls += 1
        return self.__rmatvec_impl(x)


@runtime_checkable
class IterativeSolver(Protocol):
    """Function iteratively solving a linear system."""

    def __call__(
        self,
        A: CustomLinearOperator,
        b: VectorType,
        x0: VectorType,
        *,
        M: CustomLinearOperator | None,
        rtol: float,
        maxiter: int,
    ) -> tuple[VectorType, Any]:
        """Solve a linear system iteratively.

        Parameters
        ----------
        A : CustomLinearOperator
            Matrix of the linear system ``A @ x = b`` as a linear operator.
        b : VectorType
            Right-hand side of the linear system.
        x0 : VectorType
            Initial guess for the iterative method.
        M : CustomLinearOperator, optional
            Preconditioner for the linear system.
        rtol : float
            Relative tolerance, used as stopping criterion. The exact meaning depends on
            the solver used.
        maxiter : int
            Maximum number of iterations.

        Returns
        -------
        x : VectorType
            Solution `x` of the linear system.
        _ : Any
            Any other outputs which are ignored.

        See Also
        --------
        scipy.sparse.linalg.cg, scipy.sparse.linalg.minres, scipy.sparse.linalg.gmres
        """
        ...


@runtime_checkable
class IterativeSolverQR(Protocol):
    """Function iteratively solving a linear system using QR factorization."""

    def __call__(
        self,
        A: CustomLinearOperator,
        b: VectorType,
        *,
        x0: VectorType,
        atol: float,
        btol: float,
        iter_lim: int,
    ) -> tuple[VectorType, Any]:
        """Solve a rectangular linear system iteratively using QR factorization.

        Parameters
        ----------
        A : CustomLinearOperator
            Matrix of the linear system ``A @ x = b`` as a linear operator.
        b : VectorType
            Right-hand side of the linear system.
        x0 : VectorType
            Initial guess for the iterative method.
        atol : float
            Tolerance in terms of `A`, used as stopping criterion. The exact meaning
            depends on the solver used.
        btol : float
            Tolerance in terms of `b`, used as stopping criterion. The exact meaning
            depends on the solver used.
        iter_lim : int
            Maximum number of iterations.

        Returns
        -------
        x : VectorType
            Solution `x` of the linear system.
        _ : Any
            Any other outputs which are ignored.

        See Also
        --------
        scipy.sparse.linalg.lsqr
        """
        ...


@dataclass
class IterativeSolverOptions(Options):
    """Default options for iterative solvers."""

    tolerance: NonnegativeFloat = 1e-6
    """Stopping tolerance."""

    max_iterations: NonnegativeInt = 15
    """Maximum number of iterations."""

    absolute_tolerance: NonnegativeFloat = 0.0
    """Absolute tolerance."""

    other: Mapping[str, Any] = field(default_factory=dict)
    """Other options directly passed on to the solver."""


PointTypeContra = TypeVar("PointTypeContra", contravariant=True)
"""Contravariant type of an optimization point."""

PointType = TypeVar("PointType")
"""Type of an optimization point."""


FT = float | np.floating[Any]
"""Floating point number (scalar)."""


class ObjectiveFcn(Protocol[PointTypeContra]):
    r"""Function computing the objective function value.

    While the function must be real-valued, the variables in which it is evaluated can
    be real or complex. The function has the signature::

        (point: PointType) -> float

    Examples
    --------
    To compute the best rank-1 approximation of a matrix :math:`\mat{M}`, one can
    minimize

    .. math::

        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F},

    hence :math:`\vec{F}(\vec{z}) = \vec{a} \vec{b}^{\T} - \mat{M}` where $`\vec{z}`$
    contains the variables :math:`\vec{a}` and :math:`\vec{b}`, which can be complex.

    >>> import numpy as np
    >>> def objective(z):
    ...     m, n = M.shape  # assume M is known
    ...     a, b = z[:m], z[m:]
    ...     return 0.5 * np.linalg.norm(np.outer(a, b) - M) ** 2

    The point ``z`` is given as a :class:`numpy.ndarray` above. Alternatively, ``z`` can
    be any convenient type, e.g., a :class:`.PolyadicTensor` with factors ``a`` and
    ``b``:

    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> def objective(z: tl.PolyadicTensor) -> float:
    ...     return 0.5 * tl.frob(np.array(z) - M) ** 2  # assume M is known
    """

    def __call__(self, point: PointTypeContra, /) -> FT:
        """Compute the objective function value.

        Parameters
        ----------
        point : PointType
            The point in which the objective function value is evaluated.

        Returns
        -------
        float
            The objective function value in `point`.
        """
        ...


class GradientFcn(Protocol[PointType]):
    r"""Function computing the gradient.

    The gradient evaluated in a given `point` is computed. If the variables are complex,
    twice the derivative with respect to the conjugated variables, evaluated in a
    given `point`, is computed. The type of the output is the same as the input
    type. The signature is::

        (point: PointType) -> PointType

    Notes
    -----
    In the real case, let the objective :math:`f(\vec{z})` be a function in real
    variables :math:`\vec{z} \in \mathbb{R}^N`. The computed gradient is a vector
    containing the partial derivatives with respect to the variables :math:`\vec{z}`,
    evaluated in `point` denoted by :math:`\vec{z}_k`, i.e.,

    .. math:: \vec{g} = \frac{\mathrm{d} f(\vec{z}_k)}{\mathrm{d} \vec{z}}.

    In the complex case, let objective :math:`f(\vec{z}, \conj{\vec{z}})` be a real
    function in complex variables :math:`\vec{z} \in \mathbb{C}^N` and their conjugates
    :math:`\conj{\vec{z}}`. The returned gradient is a vector containing twice the
    partial derivatives with respect to the conjugated variables :math:`\conj{\vec{z}}`,
    keeping :math:`\vec{z}` constant, evaluated in `point` denoted by :math:`\vec{z}_k`,
    i.e.,

    .. math::

        \vec{g} &= 2 \frac{\partial f(\vec{z}_k)}{\partial \conj{\vec{z}}},\\
                &= 2 \conj{\frac{\partial f(\vec{z}_k)}{\partial \vec{z}}}.

    The last equality follows from the requirement that the objective function :math:`f`
    is a real value. This gradient definition coincides with the one above for real
    variables. Note `point` contains only :math:`\vec{z}`.

    The requirement for the scaled conjugate cogradient is a design choice allowing
    easier implementation for problems involving complex variables. An alternative would
    be to write :math:`\vec{z} = \vec{x} + j \vec{y}`, where :math:`j^2 = -1`,
    and optimize with respect to the real variables :math:`\vec{x}` and
    :math:`\vec{y}`. This would require the user to implement the (real) gradients with
    respect to :math:`\vec{x}` and with respect to :math:`\vec{y}`.

    Examples
    --------
    To compute the best rank-1 approximation of a matrix :math:`\mat{M}`, one can
    minimize

    .. math::

        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F},

    hence :math:`\vec{F}(\vec{z}) = \vec{a} \vec{b}^{\T} - \mat{M}` where
    :math:`\vec{z}` contains the variables :math:`\vec{a}` and :math:`\vec{b}`, which
    can be complex. The gradient is given by:

    >>> import numpy as np
    >>> def gradient(z):
    ...     m, n = M.shape  # assume M is known
    ...     a, b = z[:m], z[m:]    
    ...     residual = np.outer(a, b) - M
    ...     grad_a = residual @ b.conj()
    ...     grad_b = residual.T @ a.conj()
    ..      return np.vstack((a, b))

    The conjugation is only required for complex variables. Above, the point ``z`` as
    well as the computed gradient are given as :class:`numpy.ndarray`. Alternatively,
    ``z`` can be any convenient type, e.g., a :class:`.PolyadicTensor` with factors
    ``a`` and ``b``:

    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> def gradient(z: tl.PolyadicTensor) -> tl.PolyadicTensor:
    ...     residual = tl.residual(z, M)  # assume M is known
    ...     grad_a = residual @ z.factors[1].conj()
    ...     grad_b = residual.T @ z.factors[0].conj()
    ...     return tl.PolyadicTensor((grad_a, grad_b))

    The Hermitian best rank-1 approximation of a Hermitian matrix can be formulated as:

    .. math::

        \underset{\vec{a}}{\text{minimize}}\ \frac12
        \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F},

    This objective function depends on both :math:`\vec{z}` and :math:`\conj{\vec{z}}`
    where :math:`\vec{z} = \vec{a}`. To compute the gradient, twice the partial
    derivative with respect to :math:`\conj{\vec{a}}` is returned:

    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> def gradient(a):
    ...     residual = np.outer(a, a.conj()) - M  # assume M is known
    ...     return 2 * residual @ a

    This can be shown easily by expanding the norm, simplifying the conjugates and then
    treating the non-conjugated variables :math:`\vec{a}` as a constant. 
    """

    def __call__(self, point: PointType, /) -> PointType:
        """Compute the gradient.

        Parameters
        ----------
        point : PointType
            The point in which the gradient is evaluated.

        Returns
        -------
        PointType
            The gradient evaluated in `point` if the objective is a function in real
            variables, or twice the conjugate cogradient evaluated in `point` if the
            objective is a function in complex variables.
        """
        ...


class JacobianFcn(Protocol[PointTypeContra]):
    r"""Function computing the Jacobian for a nonlinear least-squares problem.

    The Jacobian evaluated in a given `point` is computed.  The Jacobian is defined for
    the objective function::

        f = lambda z: 0.5 * tl.frob(F(z)) ** 2

    where ``F(z)`` is the residual in the real or complex variables ``z``. Each entry of
    the Jacobian ``J`` contains the partial derivative of each element in the residual
    (rows) with respect to each variable (columns) evaluated in `point`. The signature
    is::

        (point: PointType) -> tl.typing.MatrixType

    See Also
    --------
    :class:`.JacobianVectorProductFcn`
        Function computing the Jacobian times vector product.
    :class:`.ComplexJacobianFcn`
        Function computing the complex Jacobian for non-analytic residuals.

    Notes
    -----
    Mathematically, for a nonlinear least-squares problem with residual
    :math:`\vec{F}(\vec{z}) \in \C^M` in variables :math:`\vec{z} \in \C^N`, the
    Jacobian :math:`\mat{J} \in \C^{M \times N}` evaluated in :math:`\vec{z}_k`
    (`point`) is defined as

    .. math::

        \mat{J} = \frac{\partial \vec{F}(\vec{z}_k)}{\partial \vec{z}^{\T}},

    or, element-wise,

    .. math::

        J_{mn} = \frac{\partial F_m(\vec{z}_k)}{\partial z_n}.

    This protocol can only be used for problems involving real or complex variables, as
    long as the residual function :math:`\vec{F}(\vec{z})` is holomorphic, or analytic,
    i.e., :math:`\vec{F}(\vec{z})` does not depend on the conjugated variables
    :math:`\conj{\vec{z}}`. Otherwise, refer to :class:`.ComplexJacobianFcn`.

    Examples
    --------
    To compute the best rank-1 approximation of a matrix :math:`\mat{M}`, one can
    minimize

    .. math::

        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F},

    hence :math:`\vec{F}(\vec{z}) = \vec{a} \vec{b}^{\T} - \mat{M}` where
    :math:`\vec{z}` contains the variables :math:`\vec{a}` and :math:`\vec{b}`, which
    can be real or complex. The Jacobian of $\vec{F}(\vec{z})$ is given by

    >>> import numpy as np
    >>> def jacobian(z):
    ...     m, n = M.shape  # assume M is known
    ...     a, b = z[:m], z[m:]
    ...     Ja = np.kron(np.eye(m), b)  # partial derivative w.r.t. a
    ...     Jb = np.kron(a, np.eye(n))  # partial derivative w.r.t. b
    ...     return np.hstack((Ja, Jb))

    The Hermitian best rank-1 approximation of a matrix cannot be handled by functions
    following this protocol as

    .. math::

        \underset{\vec{a}}{\text{minimize}}\ \frac12
        \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F},

    depends on both :math:`\vec{z}` and :math:`\conj{\vec{z}}`: :math:`\vec{F}(\vec{z},
    \conj{\vec{z}}) = \vec{z} \conj{\vec{z}}^{\T} - \mat{M}` where
    :math:`\vec{z} = \vec{a}`. Instead, use :class:`.ComplexJacobianFcn`.
    """

    def __call__(self, point: PointTypeContra, /) -> MatrixType:
        """Compute the Jacobian for a nonlinear least-squares problem.

        Parameters
        ----------
        point : PointType
            The point in which the Jacobian is evaluated.

        Returns
        -------
        MatrixType
            The Jacobian evaluated in `point`.
        """
        ...


class ComplexJacobianFcn(Protocol[PointTypeContra]):
    r"""Function computing the complex Jacobian for a nonlinear least-squares problem.

    The complex Jacobian evaluated in a given `point` is computed. The complex Jacobian
    is defined for the objective function::

        f = lambda z: 0.5 * tl.frob(F(z)) ** 2

    where ``F(z)`` is the residual in the real or complex variables ``z``. In contrast
    to :class:`.JacobianFcn`, ``F(z)`` is also a function of the conjugated variables
    ``z.conj()``, and both the Jacobian with respect to ``z`` and ``z.conj()``,
    evaluated in `point` are returned. Each entry of the Jacobian ``Jz`` contains the
    partial derivative of each element in the residual (rows) with respect to each
    variable ``z`` (columns) evaluated in `point`, while the Jacobian ``Jzc`` contains
    the partial derivative of each element in the residual (rows) with respect to each
    conjugated variable ``z.conj()`` (columns). The signature is::

        (point: PointType) -> tuple[tl.typing.MatrixType, tl.typing.MatrixType]

    See Also
    --------
    :class:`.JacobianFcn`
        Function computing the Jacobian for analytic residuals.
    :class:`.ComplexJacobianVectorProductFcn`
        Function computing the Jacobian times vector product.

    Notes
    -----
    Consider a nonlinear least-squares problem

    .. math::

        \underset{\vec{z}}{\text{minimize}}\ \frac12
        \| \vec{F}(\vec{z},\conj{\vec{z}}) \|^2_{\F},

    with residual :math:`\vec{F}(\vec{z}, \conj{\vec{z}}) \in \C^M` in variables
    :math:`\vec{z} \in \C^N`. We write :math:`\vec{F}(\vec{z}, \conj{\vec{z}})` rather
    than :math:`\vec{F}(\vec{z})` to explicitly denote the dependence on the conjugated
    variables $\conj{\vec{z}}$. Mathematically, the Jacobians :math:`\mat{J}_{\vec{z}}
    \in \C^{M \times N}` and :math:`\mat{J}_{\conj{\vec{z}}} \in \C^{M \times N}`
    evaluated in :math:`\vec{z}_k` (`point`) are defined as

    .. math::

        \mat{J}_{\vec{z}} &=
        \frac{\partial\vec{F}(\vec{z}_k,\conj{\vec{z}}_k)}{\partial\vec{z}^{\T}},\\
        \mat{J}_{\conj{\vec{z}}} &=
        \frac{\partial\vec{F}(\vec{z}_k,\conj{\vec{z}}_k)}{\partial\conj{\vec{z}}^{\T}},

    or, element-wise,

    .. math::

        \left(J_{\vec{z}}\right)_{mn} &=
        \frac{\partial F_m(\vec{z}_k, \conj{\vec{z}}_k)}{\partial z_n}\\
        \left(J_{\conj{\vec{z}}}\right)_{mn} &=
        \frac{\partial F_m(\vec{z}_k, \conj{\vec{z}}_k)}{\partial \conj{z}_n}.

    This protocol should only be used for problems involving complex variables and
    non-holomorphic/non-analytic residual functions :math:`\vec{F}(\vec{z},
    \conj{\vec{z}})`. For other functions, refer to :class:`.JacobianFcn`.

    Examples
    --------
    To compute the best rank-1 approximation of a matrix :math:`\mat{M}`, one can
    minimize

    .. math::

        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F},

    hence :math:`\vec{F}(\vec{z}) = \vec{a} \vec{b}^{\T} - \mat{M}` where
    :math:`\vec{z}` contains the variables :math:`\vec{a}` and :math:`\vec{b}`, which
    can be complex. As :math:`\vec{F}(\vec{z})` does not depend on the conjugated
    variables, :math:`\mat{J}_{\conj{\vec{z}}} = \vec{0}`.

    >>> import numpy as np
    >>> def complex_jacobian(z):
    ...     m, n = M.shape  # assume M is known
    ...     a, b = z[:m], z[m:]
    ...     Ja = np.kron(np.eye(m), b)  # partial derivative w.r.t. a
    ...     Jb = np.kron(a, np.eye(n))  # partial derivative w.r.t. b
    ...     return np.hstack((Ja, Jb)), np.zeros((m * n, m + n))

    To compute the Hermitian best rank-1 approximation of a matrix :math:`\mat{M}`, one
    can minimize

    .. math::

        \underset{\vec{a}}{\text{minimize}}\ \frac12
        \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F},

    hence :math:`\vec{F}(\vec{z}, \conj{\vec{z}}) = \vec{a} \conj{\vec{a}}^{\T} -
    \mat{M}` where :math:`\vec{z} = \vec{a}`. As :math:`\vec{F}(\vec{z},
    \conj{\vec{z}})` depends on the conjugated variables,
    :math:`\mat{J}_{\conj{\vec{z}}} \neq \vec{0}`:

    >>> import numpy as np
    >>> def complex_jacobian(a):
    ...     n = a.size
    ...     Ja = np.kron(np.eye(n), a.conj())  # partial derivative w.r.t. a
    ...     Jac = np.kron(a, np.eye(n))  # partial derivative w.r.t. a.conj()
    ...     return Ja, Jac
    """

    def __call__(self, point: PointTypeContra, /) -> tuple[MatrixType, MatrixType]:
        """Compute the complex Jacobian for nonlinear least-squares problem.

        Parameters
        ----------
        point : PointType
            The point in which the complex Jacobian is evaluated.

        Returns
        -------
        Jz : MatrixType
            The Jacobian with respect to variables ``z`` evaluated in `point`.
        Jzc : MatrixType
            The Jacobian with respect to the conjugated variables ``z.conj()`` evaluated
            in `point`.
        """
        ...


class HessianFcn(Protocol[PointTypeContra]):
    r"""Function computing (an approximation of) the Hessian.

    The Hessian or an approximation thereof, e.g., the Gramian of the Jacobian for
    nonlinear least-squares problems, evaluated in a given `point` is computed. The
    Hessian can be computed for real variables only. For complex variables,
    :class:`.ComplexHessianFcn` can be used. For some approximations, e.g., the Gramian
    of the Jacobian for nonlinear least-squares problems with a residual that
    does not depend on conjugated variables, complex variables can be handled as
    well. If the residual does depend on the conjugated variables,
    :class:`.ComplexHessianFcn` can be used. The signature is::

        (point: PointType) -> tl.typing.MatrixType

    See Also
    --------
    .ComplexHessianFcn
        Function computing the (an approximation) of the complex Hessian.

    Notes
    -----
    In the real case, let the objective :math:`f(\vec{z})` be a function in real
    variables :math:`\vec{z} \in \mathbb{R}^N`. The computed Hessian is a matrix
    containing the partial derivatives with respect to the variables :math:`\vec{z}` in
    the rows and in the columns, evaluated in `point` denoted by :math:`\vec{z}_k`,
    i.e.,

    .. math::

       \mat{H} = \frac{\mathrm{d}^2 f(\vec{z}_k)}{
         \mathrm{d} \vec{z}\mathrm{d} \vec{z}^{\T}}.

    For real functions in complex variables :math:`\vec{z} \in \mathbb{C}^N`, the
    Hessian of the objective :math:`f(\vec{z}, \conj{\vec{z}})` needs to be computed
    with respect to both $\vec{z}$ and $\conj{\vec{z}}$ and :class:`.ComplexHessianFcn`
    should be used instead.

    The protocol can be used when implementing a Gauss--Newton type algorithm for
    nonlinear least squares problems in both real and complex variables if the residual
    does not depend on conjugated variables, i.e.,

    .. math::

         \underset{\vec{z}}{\text{minimize}}\ \frac{1}{2} \norm{\vec{F}(\vec{z})}^2,

    where the objective :math:`f(\vec{z}, \conj{\vec{z}})` depends on the conjugated
    variables $\conj{\vec{z}}$, but the residual function $\mat{F}(\vec{z})$ depends
    only on $\vec{z}$. In this case, the Gramian of the Jacobian is used as an
    approximation of the Hessian. Let the Jacobian with respect to the variables be

    .. math::

        \mat{J}_{\vec{z}} = \frac{\partial \mat{F}}{\partial\vec{z}^{\T}}

    The Hessian approximation then becomes

    .. math::

        \mat{H} = \mat{J}_{\vec{z}}^{\TH} \mat{J}_{\vec{z}}

    evaluated at $\vec{z}_k$. See Section 4.1 in :cite:`r665` for more details.

    Examples
    --------
    To compute the best rank-1 approximation of a real matrix :math:`\mat{M}`, one can
    minimize

    .. math::

        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F},

    hence :math:`\vec{F}(\vec{z}) = \vec{a} \vec{b}^{\T} - \mat{M}` where
    :math:`\vec{z}` contains the variables :math:`\vec{a}` and :math:`\vec{b}`, which
    are both real. The Hessian is given by:

    >>> import numpy as np
    >>> def hessian(z):
    ...     m, n = M.shape  # assume M is known
    ...     a, b = z[:m], z[m:]
    ...     res = np.outer(a, b) - M
    ...     H11 = np.vdot(b, b) * np.eye(m)
    ...     H12 = np.outer(a, b) + res
    ...     H22 = np.vdot(a, a) * np.eye(n)
    ...     return np.block([[H11, H12], [H12.T, H22]])

    Above, the point ``z`` is given as a :class:`numpy.ndarray`. Alternatively, ``z``
    can be any convenient type, e.g., a :class:`.PolyadicTensor` with factors ``a`` and
    ``b``:

    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> def hessian(z: tl.PolyadicTensor) -> tl.PolyadicTensor:
    ...     m, n = M.shape  # assume M is known
    ...     res = tl.residual(M, z)
    ...     H11 = np.vdot(b, b) * np.eye(m)
    ...     H12 = np.outer(a, b) + res
    ...     H22 = np.vdot(a, a) * np.eye(n)
    ...     return np.block([[H11, H12], [H12.T, H22]])

    If the Gramian of the Jacobian is used to approximate the Hessian, complex variables
    $\vec{z}$ can be used, as long as $\vec{F}(\vec{z})$ does not depend on the
    conjugated variables $\conj{\vec{z}}$:

    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> def gramian(z: tl.PolyadicTensor) -> tl.PolyadicTensor:
    ...     m, n = z.shape
    ...     a, b = z.factors
    ...     G11 = np.vdot(b, b) * np.eye(m)
    ...     G12 = np.outer(a, b.conj())
    ...     G22 = np.vdot(a, a) * np.eye(n)
    ...     return np.block([[G11, G12], [G12.conj().T, G22]])

    The Hermitian best rank-1 approximation of a complex, Hermitian matrix can be
    formulated as:

    .. math::

        \underset{\vec{a}}{\text{minimize}}\ \frac12
        \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F},

    where $\vec{z}\in\C^N$. Both the objective and the residual depend on
    :math:`\vec{z}` and :math:`\conj{\vec{z}}` where :math:`\vec{z} = \vec{a}`. This
    cannot be handled using this protocol; use :class:`.ComplexHessianFcn` instead.
    """

    def __call__(self, point: PointTypeContra, /) -> MatrixType:
        """Compute (an approximation of) the Hessian.

        Parameters
        ----------
        point : PointType
            The point in which the Hessian is evaluated.

        Returns
        -------
        MatrixType
            The (approximation of the) Hessian evaluated in `point`.
        """
        ...


class ComplexHessianFcn(Protocol[PointTypeContra]):
    r"""Function computing (an approximation of) the complex Hessian.

    The complex Hessian or an approximation thereof, e.g., the Gramian of the Jacobian
    for nonlinear least-squares problems, evaluated in a given `point` is computed. In
    contrast to :class:`HessianFcn`, this protocol can be used when variables are
    complex or when an approximation of the Hessian uses a non-holomorphic/non-analytic
    function, i.e., the function depends on both the variables and the conjugated
    variables. The signature is::

        (point: PointType) -> tuple[tl.typing.MatrixType, tl.typing.MatrixType]
    
    Notes
    -----
    Let $f(\vec{z}, \conj{\vec{z}})$ be a real-valued, non-holomorphic/non-analytic
    function in the variables $\vec{z}$ and its conjugate $\conj{\vec{z}}$. The Hessian
    of $f$ with respect to the variables $\vec{z}$ (keeping $\conj{\vec{z}}$
    constant) and the conjugated variables $\conj{\vec{z}}$ (keeping $\vec{z}$
    constant) and evaluated in $\vec{z}_k$ (`point`) is a two-by-two block matrix

    .. math::

        \mat{H} = \begin{bmatrix}
        \frac{\partial^2 f(\vec{z}_k,\conj{\vec{z}}_k)}{
          \partial \conj{\vec{z}} \partial \vec{z}^{\T}} &
        \frac{\partial^2 f(\vec{z}_k,\conj{\vec{z}}_k)}{
          \partial \conj{\vec{z}} \partial \conj{\vec{z}}^{\T}} \\
        \frac{\partial^2 f(\vec{z}_k,\conj{\vec{z}}_k)}{
          \partial \vec{z} \partial \vec{z}^{\T}} &
        \frac{\partial^2 f(\vec{z}_k,\conj{\vec{z}}_k)}{
          \partial \vec{z} \partial \conj{\vec{z}}^{\T}}
        \end{bmatrix}.

    Because $f$ is real-valued, the diagonal blocks are equal up to conjugation and the
    same holds for the off-diagonal blocks. As this is exploited in the implementation
    of the methods, the first return value is the partial derivative of the gradient
    with respect to $\vec{z}$, i.e., $2\frac{\partial}{\partial \vec{z}} \left(
    \frac{\partial f(\vec{z}, \conj{\vec{z}})}{\partial{\conj{\vec{z}}}} \right)$. The
    second return value is the partial derivative of the gradient with respect to
    $\conj{\vec{z}}$, i.e., $2\frac{\partial}{\partial \conj{\vec{z}}} \left(
    \frac{\partial f(\vec{z}, \conj{\vec{z}})}{\partial{\conj{\vec{z}}}} \right)$.

    For nonlinear least-squares problems, the Gramian of the Jacobian of the residual
    function $\mat{F}(\vec{z}, \conj{\vec{z}})$ can be used. Let the Jacobian with
    respect to the variables $\vec{z}$ and the conjugated variables $\conj{\vec{z}}$ be

    .. math::

        \mat{J}_{\vec{z}} = \frac{\partial \mat{F}}{\partial\vec{z}^{\T}}
        \quad 
        \text{and}
        \quad
        \mat{J}_{\conj{\vec{z}}} = \frac{\partial \mat{F}}{\partial\conj{\vec{z}}^{\T}}.

    Following the derivation in Section 4.1 in :cite:`r665`, the first and second return
    values are, respectively,

    .. math::

       \mat{J}_{\vec{z}}^{\TH}\mat{J}_{\vec{z}} +
       \conj{\mat{J}_{\conj{\vec{z}}}^{\TH}\mat{J}_{\conj{\vec{z}}}}
       \quad
       \text{and}
       \quad
       \mat{J}_{\vec{z}}^{\TH}\mat{J}_{\conj{\vec{z}}} +
       \left(\mat{J}_{\vec{z}}^{\TH}\mat{J}_{\conj{\vec{z}}}\right)^{\T}.

    Examples
    --------
    To compute the best rank-1 approximation of a complex matrix :math:`\mat{M}`, one
    can minimize

    .. math::

        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F},

    hence :math:`\vec{F}(\vec{z}) = \vec{a} \vec{b}^{\T} - \mat{M}` where $\vec{z}$
    contains the complex variables :math:`\vec{a}\in\C^m` and
    :math:`\vec{b}\in\C^n`. The complex Hessian is given by:

    >>> import numpy as np
    >>> def complex_hessian(z):
    ...     m, n = M.shape  # assume M is known
    ...     a, b = z[:m], z[m:]
    ...     res = np.outer(a, b) - M
    ...     H11 = np.block(
    ...         [
    ...             [np.vdot(b, b) * np.eye(m), np.outer(a, b.conj())],
    ...             [np.outer(b, a.conj()), np.vdot(a, a) * np.eye(n)],
    ...         ]
    ...     )
    ...     H12 =  np.block([[np.zeros((m, m)), res], [res.T, np.zeros((n, n))]])
    ...     return H11, H12

    Above, the point ``z`` is given as a :class:`numpy.ndarray`. Alternatively, ``z``
    can be any convenient type, e.g., a :class:`.PolyadicTensor` with factors ``a`` and
    ``b``. For example, if the Gramian of the Jacobian is used to approximate the
    Hessian, complex variables $\vec{z}$ can be used in the :class:`.PolyadicTensor`
    format:

    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> def complex_gramian(z: tl.PolyadicTensor):
    ...     m, n = z.shape
    ...     a, b = z.factors
    ...     G = np.block(
    ...         [
    ...             [np.vdot(b, b) * np.eye(m), np.outer(a, b.conj())],
    ...             [np.outer(b, a.conj()), np.vdot(a, a) * np.eye(n)],
    ...         ]
    ...     )
    ...     return G, np.zeros((m + n, m + n)) 

    The Hermitian best rank-1 approximation of a Hermitian matrix can be formulated as:

    .. math::

        \underset{\vec{a}}{\text{minimize}}\ \frac12
        \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F},

    This objective function depends on both :math:`\vec{z}` and :math:`\conj{\vec{z}}`
    where :math:`\vec{z} = \vec{a} \in \C^m`. In this case, the residual
    $\vec{F}(\vec{z}, \conj{\vec{z}}) = \vec{z} \conj{\vec{z}}^{\T} - \mat{M}$ is a
    function of the variables and the conjugated variables and therefore is
    non-holomorphic/non-analytic. The Hessian is computed as:

    >>> import numpy as np
    >>> def complex_hessian(a):
    ...     residual = np.outer(a, a.conj()) - M  # Assume M is known
    ...     Id = np.eye(a.size)
    ...     return 2 * np.vdot(a, a) * Id + 2 * residual.T, 2 * np.outer(a, a)    

    Similarly, the Gramian of the Jacobian can be computed as:

    >>> import numpy as np
    >>> def complex_gramian(a):
    ...     Id = np.eye(a.size)
    ...     return 2 * np.vdot(a, a) * Id, 2 * np.outer(a, a)
    """

    def __call__(self, point: PointTypeContra, /) -> tuple[MatrixType, MatrixType]:
        """Compute (an approximation of) the complex Hessian.

        Parameters
        ----------
        point : VectorType
            The point in which the complex Hessian or its approximation is evaluated.

        Returns
        -------
        MatrixType
            Partial derivative of the gradient with respect to the variables evaluated
            in `point`, treating the conjugated variables as a constant. Alternatively,
            an approximation to this derivative can be returned.
        MatrixType
            Partial derivative of the gradient with respect to the conjugated variables
            evaluated in `point`, treating the non-conjugated variables as a
            constant. Alternatively, an approximation to this derivative can be
            returned.
        """
        ...


class HessianVectorProductFcn(Protocol[PointType]):
    r"""Function computing the Hessian times vector product.

    The product of the Hessian or an approximation thereof, e.g., the Gramian of the
    Jacobian for nonlinear least-squares problems, evaluated in a given `point`, and a
    given vector is computed. The Hessian times vector product can be computed for real
    variables only. For complex variables, :class:`.ComplexHessianVectorProductFcn` can
    be used. In some cases, e.g., the nonlinear least squares problem where the residual
    does not depend on the conjugated variables, complex variables can be used as
    well. If the residual does depend on the conjugated variables,
    :class:`.ComplexHessianVectorProductFcn` can be used. The signature is::

        (point: PointType, vector: PointType) -> PointType

    See Also
    --------
    .HessianFcn
        Function computing (an approximation) of the Hessian.
    .ComplexHessianVectorProductFcn
        Function computing the complex Hessian times vector product.

    Notes
    -----
    In the real case, let the objective :math:`f(\vec{z})` be a function in real
    variables :math:`\vec{z} \in \mathbb{R}^N`. The computed Hessian is a matrix
    containing the partial derivatives with respect to the variables :math:`\vec{z}` in
    the rows and in the columns, evaluated in `point` denoted by :math:`\vec{z}_k`,
    i.e.,

    .. math::

       \mat{H} = \frac{\mathrm{d}^2 f(\vec{z}_k)}{
         \mathrm{d} \vec{z}\mathrm{d} \vec{z}^{\T}}.

    The resulting product with a vector $\vec{x}$ then becomes:

    .. math::

        \vec{y} = \mat{H}\vec{x}.

    For real functions in complex variables :math:`\vec{z} \in \mathbb{C}^N`, the
    Hessian of the objective :math:`f(\vec{z}, \conj{\vec{z}})` needs to be computed
    with respect to both $\vec{z}$ and $\conj{\vec{z}}$ and
    :class:`.ComplexHessianVectorProductFcn` should be used instead.

    The protocol can be used when using a Gauss-Newton type algorithm for nonlinear
    least squares problems in both real and complex variables if the residual does not
    depend on conjugated variables, i.e.,

    .. math::

         \underset{\vec{z}}{\text{minimize}}\ \frac{1}{2} \norm{\vec{F}(\vec{z})}^2,

    where the objective :math:`f(\vec{z}, \conj{\vec{z}})` depends on the conjugated
    variables $\conj{\vec{z}}$, but the residual function $\mat{F}(\vec{z})$ on depends
    only on $\vec{z}$. In this case, the Gramian of the Jacobian is used as an
    approximation of the Hessian. Let the Jacobian with respect to the variables be

    .. math::

        \mat{J}_{\vec{z}} = \frac{\partial \mat{F}}{\partial\vec{z}^{\T}}

    The Gramian of the Jacobian, and the Gramian times vector product then become

    .. math::

        \mat{G} &= \mat{J}_{\vec{z}}^{\TH} \mat{J}_{\vec{z}}\\
        \vec{y} &= \mat{G}\vec{x} 

    evaluated at $\vec{z}_k$. See Section 4.1 in :cite:`r665` for more details.

    Examples
    --------
    To compute the best rank-1 approximation of a real matrix :math:`\mat{M}`, one can
    minimize
    
    .. math::

        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F},

    hence :math:`\vec{F}(\vec{z}) = \vec{a} \vec{b}^{\T} - \mat{M}` where
    :math:`\vec{z}\in\R^{m+n}` contains the variables :math:`\vec{a}` and
    :math:`\vec{b}`, which are both real. The Hessian times vector product is given by:

    >>> import numpy as np
    >>> def hessian_vector_product(z, x):
    ...     m, n = M.shape  # assume M is known
    ...     a, b = z[:m], z[m:]
    ...     xa, xb = x[:m], x[m:]
    ...     res = np.outer(a, b) - M
    ...     ya = xa * np.vdot(b, b) + a * np.vdot(b, xb) + res @ xb
    ...     yb = xb * np.vdot(a, a) + b * np.vdot(a, xa) + res.T @ xa
    ...     return np.vstack((ya, yb))

    Above, the point ``z`` is given as a :class:`numpy.ndarray`. Alternatively, ``z``
    can be any convenient type, e.g., a :class:`.PolyadicTensor` with factors ``a`` and
    ``b``. The vector and the output should be in the same type:

    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> def hvp(z: tl.PolyadicTensor, x: tl.PolyadicTensor) -> tl.PolyadicTensor:
    ...     m, n = M.shape  # assume M is known
    ...     res = tl.residual(z, M)
    ...     a, b = z.factors
    ...     xa, xb = x.factors
    ...     ya = xa * np.vdot(b, b) + a * np.vdot(b, xb) + res @ xb
    ...     yb = xb * np.vdot(a, a) + b * np.vdot(a, xa) + res.T @ xa
    ...     return tl.PolyadicTensor((ya, yb))    

    If the Gramian of the Jacobian is used to approximate the Hessian, complex variables
    $\vec{z}\in\C^{m+n}$ can be used, as long as $\vec{F}(\vec{z})$ does not depend on
    the conjugated variables $\conj{\vec{z}}$:

    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> def gvp(z: tl.PolyadicTensor, x: tl.PolyadicTensor) -> tl.PolyadicTensor:
    ...     a, b = z.factors
    ...     xa, xb = x.factors
    ...     ya = xa * np.vdot(b, b) + a * np.vdot(b, xb)
    ...     yb = xb * np.vdot(a, a) + b * np.vdot(a, xa)
    ...     return tl.PolyadicTensor((ya, yb))        

    The Hermitian best rank-1 approximation of a Hermitian matrix can be formulated as:

    .. math::

        \underset{\vec{a}}{\text{minimize}}\ \frac12
        \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F},

    The residual $\vec{F}(\vec{z},\conj{\vec{z}})$ depends on both :math:`\vec{z}` and
    :math:`\conj{\vec{z}}` where :math:`\vec{z} = \vec{a}`. This cannot be handled by
    this protocol; use :class:`.ComplexHessianVectorProductFcn` instead.
    """

    def __call__(self, point: PointType, x: PointType, /) -> PointType:
        """Compute the Hessian times vector product.

        Parameters
        ----------
        point : PointType
            Point in which the Hessian is computed.
        x : PointType
            Vector to be multiplied with the Hessian.

        Returns
        -------
        PointType
            The Hessian times vector product.
        """
        ...


class ComplexHessianVectorProductFcn(Protocol[PointType]):
    r"""Function computing the complex Hessian times vector product.

    The product of the complex Hessian or an approximation thereof, e.g., the Gramian of
    the Jacobian for nonlinear least-squares problems, evaluated in a given `point`, and
    a vector is computed. In contrast to :class:`.HessianVectorProductFcn`, this
    protocol can be used when variables are complex or when an approximation of the
    Hessian uses a non-holomorphic/non-analytic function, i.e., the function depends on
    both the variables and the conjugated variables. The signature is::

        (point: PointType, vector: PointType) -> PointType
    
    Notes
    -----
    Let $f(\vec{z}, \conj{\vec{z}})$ be a real-valued, non-holomorphic/non-analytic
    function in the variables $\vec{z}\in\C^N$ and its conjugate $\conj{\vec{z}}$. The
    Hessian of $f$ with respect to the variables $\vec{z}$ (keeping
    $\conj{\vec{z}}$ constant) and the conjugated variables $\conj{\vec{z}}$ (keeping
    $\vec{z}$ constant) and evaluated in $\vec{z}_k$ (`point`) is a two-by-two block
    matrix

    .. math::

        \mat{H} = \begin{bmatrix}
        \frac{\partial^2 f(\vec{z}_k,\conj{\vec{z}}_k)}{
          \partial \conj{\vec{z}} \partial \vec{z}^{\T}} &
        \frac{\partial^2 f(\vec{z}_k,\conj{\vec{z}}_k)}{
          \partial \conj{\vec{z}} \partial \conj{\vec{z}}^{\T}} \\
        \frac{\partial^2 f(\vec{z}_k,\conj{\vec{z}}_k)}{
          \partial \vec{z} \partial \vec{z}^{\T}} &
        \frac{\partial^2 f(\vec{z}_k,\conj{\vec{z}}_k)}{
          \partial \vec{z} \partial \conj{\vec{z}}^{\T}}
        \end{bmatrix}.

    The resulting product with a vector $\vec{x}$ then becomes:

    .. math::

        \begin{bmatrix}\vec{y}\\\conj{\vec{y}}\end{bmatrix}
        = \mat{H} \begin{bmatrix}\vec{x}\\\conj{\vec{x}}\end{bmatrix}.

    Because $f$ is real-valued, the diagonal blocks of $\mat{H}$ are equal up to
    conjugation and the same holds for the off-diagonal blocks. Moreover, the bottom
    halve of the resulting product is the conjugate ($\conj{\vec{y}})$ of the top part
    $\vec{y}$. Therefore, the required output is

    .. math::

        \vec{y} =
          2\frac{\partial}{\partial \vec{z}} \left(
          \frac{\partial f(\vec{z}, \conj{\vec{z}})}{
            \partial{\conj{\vec{z}}}} \right) \vec{x}
          +
          2\frac{\partial}{\partial \conj{\vec{z}}} \left(
          \frac{\partial f(\vec{z}, \conj{\vec{z}})}{\partial{\conj{\vec{z}}}} \right)
          \conj{\vec{x}}.

    For nonlinear least-squares problems, the Gramian of the Jacobian of the residual
    function $\mat{F}(\vec{z}, \conj{\vec{z}})$ can be used. Let the Jacobian with
    respect to the variables and the conjugated variables be

    .. math::

        \mat{J}_{\vec{z}} = \frac{\partial \mat{F}}{\partial\vec{z}^{\T}}
        \quad 
        \text{and}
        \quad
        \mat{J}_{\conj{\vec{z}}} = \frac{\partial \mat{F}}{\partial\conj{\vec{z}}^{\T}}.

    Following the derivation in Section 4.1 in :cite:`r665`, the first and second return
    values are, respectively,

    .. math::

       \mat{J}_{\vec{z}}^{\TH}\mat{J}_{\vec{z}} +
       \conj{\mat{J}_{\conj{\vec{z}}}^{\TH}\mat{J}_{\conj{\vec{z}}}}
       \quad
       \text{and}
       \quad
       \mat{J}_{\vec{z}}^{\TH}\mat{J}_{\conj{\vec{z}}} +
       \left(\mat{J}_{\vec{z}}^{\TH}\mat{J}_{\conj{\vec{z}}}\right)^{\T}.

    Therefore, Gramian times vector $\vec{x}$ product $\vec{y}$ is given by:

    .. math::

       \vec{y} = 
           \left(\mat{J}_{\vec{z}}^{\TH}\mat{J}_{\vec{z}} +
           \conj{\mat{J}_{\conj{\vec{z}}}^{\TH}\mat{J}_{\conj{\vec{z}}}}
           \right) \vec{x} + 
           \left(
           \mat{J}_{\vec{z}}^{\TH}\mat{J}_{\conj{\vec{z}}} +
           \left(\mat{J}_{\vec{z}}^{\TH}\mat{J}_{\conj{\vec{z}}}\right)^{\T}
           \right)
           \conj{\vec{x}}.
    
    Examples
    --------
    To compute the best rank-1 approximation of a complex matrix :math:`\mat{M}`, one
    can minimize

    .. math::

        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F},

    hence :math:`\vec{F}(\vec{z}) = \vec{a} \vec{b}^{\T} - \mat{M}` where
    :math:`\vec{z}` contains the variables :math:`\vec{a}\in\C^m` and
    :math:`\vec{b}\in\C^n`, which are complex. The complex Hessian times vector product
    is given by:

    >>> import numpy as np
    >>> def complex_hvp(z, x):
    ...     m, n = M.shape  # assume M is known
    ...     a, b = z[:m], z[m:]
    ...     xa, xb = x[:m], x[m:]
    ...     res = np.outer(a, b) - M
    ...     ya = xa * np.vdot(b, b) + a * np.vdot(b, xb) + res @ xb.conj()
    ...     yb = xb * np.vdot(a, a) + b * np.vdot(a, xa) + res.T @ xa.conj()
    ...     return np.vstack((ya, yb))

    Above, the point ``z`` as well as the computed product are given as
    :class:`numpy.ndarray`. Alternatively, ``z`` can be any convenient type, e.g., a
    :class:`.PolyadicTensor` with factors ``a`` and ``b``. For example, if the Gramian
    of the Jacobian is used to approximate the Hessian, complex variables $\vec{z}$ can
    be used:

    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> def cgvp(z: tl.PolyadicTensor, x: tl.PolyadicTensor) -> tl.PolyadicTensor:
    ...     a, b = z.factors
    ...     xa, xb = x.factors
    ...     ya = xa * np.vdot(b, b) + a * np.vdot(b, xb)
    ...     yb = xb * np.vdot(a, a) + b * np.vdot(a, xa)
    ...     return tl.PolyadicTensor((ya, yb))

    The Hermitian best rank-1 approximation of a Hermitian matrix can be formulated as:

    .. math::

        \underset{\vec{a}}{\text{minimize}}\ \frac12
        \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F},

    This objective function depends on both :math:`\vec{z}` and :math:`\conj{\vec{z}}`
    where :math:`\vec{z} = \vec{a}`. In this case, the residual $\vec{F}(\vec{z},
    \conj{\vec{z}}) = \vec{z} \conj{\vec{z}}^{\T} - \mat{M}$ is a function of the
    variables and the conjugated variables and therefore is
    non-holomorphic/non-analytic. The complex Hessian times vector product is computed
    as:

    >>> import numpy as np
    >>> def complex_hessian_vector_product(a, x):
    ...     Msym = (M + M.conj().T) / 2  # assume M is known 
    ...     res = np.outer(a, a.conj()) - Msym
    ...     return 2 * (np.vdot(a, a) * x + a * np.vdot(x, a) + res.T @ x)

    Similarly, the Gramian of the Jacobian times vector product can be computed as:

    >>> import numpy as np
    >>> def complex_gramian_vector_product(a, x):
    ...     return 2 * np.vdot(a, a) * x + 2 * a * np.vdot(x, a)
    """

    def __call__(self, point: PointType, x: PointType, /) -> PointType:
        """Compute the complex Hessian times vector product.

        Parameters
        ----------
        point : PointType
            Point in which the complex Hessian is computed.
        x : PointType
            Vector to be multiplied with the Hessian.

        Returns
        -------
        PointType
            The Hessian times vector product.
        """
        ...


class JacobianVectorProductFcn(Protocol[PointType]):
    r"""Function computing the Jacobian times vector product.

    The Jacobian evaluated in a given `point` times a given vector is computed. The
    Jacobian is defined for the objective function::

        f = lambda z: 0.5 * tl.frob(F(z)) ** 2

    where ``F(z)`` is the residual in the real or complex variables ``z``. Each entry of
    the Jacobian ``J`` contains the partial derivative of each element in the residual
    (rows) with respect to each variable (columns) evaluated in `point`. Two types of
    products with a vector ``x`` (with appropriate sizes) are computed: ``y = J @ x``
    and the (conjugated transposed product ``y = J.conj().T @ x``, resulting in the
    following signatures::

        (point: PointType, vector: PointType, False) -> tl.typing.VectorType
        (point: PointType, vector: VectorType, True) -> PointType

    See Also
    --------
    :class:`.JacobianFcn`
        Function computing the Jacobian.
    :class:`.ComplexJacobianVectorProductFcn`
        Function computing the complex Jacobian times vector product for non-analytic
        residuals.

    Notes
    -----
    Mathematically, for a nonlinear least-squares problem with residual
    :math:`\vec{F}(\vec{z}) \in \C^M` in variables :math:`\vec{z} \in \C^N`, the
    Jacobian :math:`\mat{J} \in \C^{M \times N}` evaluated in :math:`\vec{z}_k`
    (`point`) is defined as

    .. math::

        \mat{J} = \frac{\partial \vec{F}(\vec{z}_k)}{\partial \vec{z}^{\T}},

    or, element-wise,

    .. math::

        J_{mn} = \frac{\partial F_m(\vec{z}_k)}{\partial z_n}.

    The required products are:

    .. math::

        \vec{y}_1 &= \mat{J} \vec{x}_1,\\
        \vec{y}_2 &= \mat{J}^{\TH} \vec{x}_2,

    where $\vec{x}_1, \vec{y}_2 \in \C^N$ and $\vec{x}_2, \vec{y}_1 \in \C^M$. This
    protocol can only be used for problems involving real or complex variables, as long
    as the residual function :math:`\vec{F}(\vec{z})` is holomorphic, or analytic, i.e.,
    :math:`\vec{F}(\vec{z})` does not depend on the conjugated variables
    :math:`\conj{\vec{z}}`. Otherwise, refer to
    :class:`.ComplexJacobianVectorProductFcn`.

    Examples
    --------
    To compute the best rank-1 approximation of a matrix :math:`\mat{M}`, one can
    minimize

    .. math::

        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F},

    hence :math:`\vec{F}(\vec{z}) = \vec{a} \vec{b}^{\T} - \mat{M}` where
    :math:`\vec{z}` contains the variables :math:`\vec{a}` and :math:`\vec{b}`, which
    can be real or complex. The Jacobian of $\vec{F}(\vec{z})$ is given by

    >>> import numpy as np
    >>> def jacobian_vector_product(z, x, transpose):
    ...     m, n = M.shape  # assume M is known
    ...     a, b = z[:m], z[m:]
    ...     if transpose:
    ...         x = x.reshape(z.shape)
    ...         return np.vstack((x @ b, x.T @ a))
    ...     xa, xb = x[:m], x[m:]
    ...     return np.kron(xa, b) + np.kron(a, xb)

    Above, the point ``z`` is given as a :class:`numpy.ndarray`. Alternatively, ``z``
    can be any convenient type, e.g., a :class:`.PolyadicTensor` with factors ``a`` and
    ``b``. For example,

    >>> import numpy as np
    >>> import pytensorlab as tl
    >>> def jacobian_vector(z, x, transpose):
    ...     a, b = z.factors
    ...     if transpose:
    ...         x = x.reshape(z.shape)
    ...         return tl.PolyadicTensor((x @ b, x.T @ a))
    ...     xa, xb = x.factors
    ...     return np.kron(xa, b) + np.kron(a, xb)

    The Hermitian best rank-1 approximation of a matrix cannot be handled by functions
    following this protocol as

    .. math::

        \underset{\vec{a}}{\text{minimize}}\ \frac12
        \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F},

    depends on both :math:`\vec{z}` and :math:`\conj{\vec{z}}`: :math:`\vec{F}(\vec{z},
    \conj{\vec{z}}) = \vec{z} \conj{\vec{z}}^{\T} - \mat{M}` where
    :math:`\vec{z} = \vec{a}`. Instead, use :class:`.ComplexJacobianVectorProductFcn`.
    """

    @overload
    def __call__(
        self, point: PointType, x: VectorType, /, transpose: Literal[True]
    ) -> PointType: ...

    @overload
    def __call__(
        self, point: PointType, x: PointType, /, transpose: Literal[False]
    ) -> VectorType: ...

    def __call__(
        self, point: PointType, x: PointType | VectorType, /, transpose: bool
    ) -> VectorType | PointType:
        """Compute the (transposed) Jacobian times vector product.

        Parameters
        ----------
        point : PointType
            Point in which the Jacobian is computed.
        x : PointType | VectorType
            Vector to be multiplied with the Jacobian. The vector should be in the same
            type as `point` if `transpose` is False and ``VectorType`` otherwise.
        transpose : bool
            Compute the Jacobian times `x` product if False; otherwise, computed the
            product of the conjugated transposed Jacobian times `x`.

        Returns
        -------
        PointType | VectorType
            If `transpose` is False, the ``VectorType`` result of the Jacobian times
            `x`; otherwise, the result of the conjugated transposed Jacobian times
            vector product in the same type as `point`.
        """
        ...


class ComplexJacobianVectorProductFcn(Protocol[PointType]):
    r"""Function computing the complex Jacobian times vector product.

    The complex Jacobian evaluated in a given `point` times a given vector `x` is
    computed. The complex Jacobian is defined for the objective function::

        f = lambda z: 0.5 * tl.frob(F(z)) ** 2

    where ``F(z)`` is the residual in the complex variables ``z``. In contrast to
    :class:`.JacobianVectorProductFcn`, ``F(z)`` is also a function of the conjugated
    variables ``z.conj()``, and both the products of the Jacobians with respect to ``z``
    and ``z.conj()``, evaluated in `point` times a vector (``x`` and ``x.conj()``,
    resp.) are returned. Each entry of the Jacobian ``Jz`` contains the partial
    derivative of each element in the residual (rows) with respect to each variable
    ``z`` (columns) evaluated in `point`, while the Jacobian ``Jzc`` contains
    the partial derivative of each element in the residual (rows) with respect to each
    conjugated variable ``z.conj()`` (columns). Two types of products with a vector
    ``x`` (with appropriate sizes) are computed: ``y, yc = Jz @ x, Jzc @ x.conj()`` and
    the (conjugated transposed product ``y, yc = Jz.conj().T @ x, Jzc.conj().T @
    x.conj()``, resulting in the following signatures::

        (point: PointType, vector: PointType, False) ->
            tuple[tl.typing.VectorType, tl.typing.VectorType]
    
        (point: PointType, vector: tl.typing.VectorType, True) ->
            tuple[PointType, PointType]    

    See Also
    --------
    :class:`.JacobianVectorProductFcn`
        Function computing the Jacobian times vector product for analytic residuals.
    :class:`.ComplexJacobianFcn`
        Function computing the complex Jacobian.

    Notes
    -----
    Consider a nonlinear least-squares problem

    .. math::

        \underset{\vec{z}}{\text{minimize}}\ \frac12
        \| \vec{F}(\vec{z},\conj{\vec{z}}) \|^2_{\F},

    with residual :math:`\vec{F}(\vec{z}, \conj{\vec{z}}) \in \C^M` in variables
    :math:`\vec{z} \in \C^N`. We write :math:`\vec{F}(\vec{z}, \conj{\vec{z}})` rather
    than :math:`\vec{F}(\vec{z})` to explicitly denote the dependence on the conjugated
    variables $\conj{\vec{z}}$. Mathematically, the Jacobians :math:`\mat{J}_{\vec{z}}
    \in \C^{M \times N}` and :math:`\mat{J}_{\conj{\vec{z}}} \in \C^{M \times N}`
    evaluated in :math:`\vec{z}_k` (`point`) are defined as

    .. math::

        \mat{J}_{\vec{z}} &=
        \frac{\partial\vec{F}(\vec{z}_k,\conj{\vec{z}}_k)}{\partial\vec{z}^{\T}},\\
        \mat{J}_{\conj{\vec{z}}} &=
        \frac{\partial\vec{F}(\vec{z}_k,\conj{\vec{z}}_k)}{\partial\conj{\vec{z}}^{\T}},

    or, element-wise,

    .. math::

        \left(\mat{J}_{\vec{z}}\right)_{mn} &=
        \frac{\partial F_m(\vec{z}_k, \conj{\vec{z}}_k)}{\partial z_n}\\
        \left(\mat{J}_{\conj{\vec{z}}}\right)_{mn} &=
        \frac{\partial F_m(\vec{z}_k, \conj{\vec{z}}_k)}{\partial \conj{z}_n}.

    The required products are:

    .. math::

        \vec{y}_1 = \mat{J}_{\vec{z}} \vec{x},\\
        \vec{y}_2 = \mat{J}_{\conj{\vec{z}}} \conj{\vec{x}},

    where $\vec{x}\in\C^N$ and $\vec{y}_1, \vec{y}_2\in\C^M$, and

    .. math::
    
        \vec{y}_1 = \mat{J}^{\TH}_{\vec{z}} \vec{x},\\
        \vec{y}_2 = \mat{J}^{\TH}_{\conj{\vec{z}}} \conj{\vec{x}},

    where $\vec{x}\in\C^M$ and $\vec{y}_1, \vec{y}_2\in\C^N$.

    This protocol is only recommended for problems involving complex variables and
    non-holomorphic/non-analytic residual functions :math:`\vec{F}(\vec{z},
    \conj{\vec{z}})`. For other functions, refer to :class:`.JacobianVectorProductFcn`.

    Examples
    --------
    To compute the best rank-1 approximation of a matrix :math:`\mat{M}`, one can
    minimize

    .. math::

        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F},

    hence :math:`\vec{F}(\vec{z}) = \vec{a} \vec{b}^{\T} - \mat{M}` where
    :math:`\vec{z}` contains the variables :math:`\vec{a}` and :math:`\vec{b}`, which
    can be complex. As :math:`\vec{F}(\vec{z})` does not depend on the conjugated
    variables, :math:`\mat{J}_{\conj{\vec{z}}} = \vec{0}` and the products are identical
    to the ones in :class:`.JacobianVectorProductFcn`:

    >>> import numpy as np
    >>> def complex_jacobian_vector(z, x, transpose):
    ...     m, n = M.shape  # assume M is known
    ...     a, b = z[:m], z[m:]
    ...     if transpose:
    ...         x = x.reshape(z.shape)
    ...         return np.vstack((x @ b, x.T @ a)), np.zeros((m + n,))
    ...     xa, xb = z[:m], z[m:]
    ...     return np.kron(xa, b) + np.kron(a, xb), np.zeros((m * n,))    

    Above, the point ``z`` is given as a :class:`numpy.ndarray`. Alternatively, ``z``
    can be any convenient type, e.g., a :class:`.PolyadicTensor` with factors ``a`` and
    ``b``, for example:

    >>> import numpy as np
    >>> def complex_jacobian_vector(z, x, transpose):
    ...     m, n = M.shape  # assume M is known
    ...     a, b = z[:m], z[m:]
    ...     if transpose:
    ...         x = x.reshape(z.shape)
    ...         JzHx = tl.PolyadicTensor((x @ b, x.T @ a))
    ...         JzcHx = tl.PolyadicTensor.zeros((m, n), 1)
    ...         return JzHx, JzcHx 
    ...     xa, xb = x.factors
    ...     return np.kron(xa, b) + np.kron(a, xb), np.zeros((m * n,))    
    
    To compute the Hermitian best rank-1 approximation of a matrix :math:`\mat{M}`, one
    can minimize

    .. math::

        \underset{\vec{a}}{\text{minimize}}\ \frac12
        \| \vec{a} \conj{\vec{a}}^{\T} - \mat{M} \|^2_{\F},

    hence :math:`\vec{F}(\vec{z}, \conj{\vec{z}}) = \vec{a} \conj{\vec{a}}^{\T} -
    \mat{M}` where :math:`\vec{z} = \vec{a}`. As :math:`\vec{F}(\vec{z},
    \conj{\vec{z}})` depends on the conjugated variables,
    :math:`\mat{J}_{\conj{\vec{z}}} \neq \vec{0}`:

    >>> import numpy as np
    >>> def complex_jacobian_vector(a):
    ...     if transpose:
    ...         x = x.reshape((a.size, a.size))
    ...         return x @ a, x.T @ a.conj()
    ...     return np.kron(x, a.conj()), np.kron(a, x.conj())
    """

    @overload
    def __call__(
        self, point: PointType, x: VectorType, /, transpose: Literal[True]
    ) -> tuple[PointType, PointType]: ...

    @overload
    def __call__(
        self, point: PointType, x: PointType, /, transpose: Literal[False]
    ) -> tuple[VectorType, VectorType]: ...

    def __call__(
        self, point: PointType, x: PointType | VectorType, /, transpose: bool
    ) -> tuple[PointType | VectorType, PointType | VectorType]:
        """Compute the complex Jacobian-vector product for non-analytic functions.

        Parameters
        ----------
        point : PointType
            The point in which the Jacobian is evaluated.
        x : VectorType
            The vector that is multiplied with the Jacobian.
        transpose : bool, default = False
            Whether or not to transpose the Jacobian first.

        Returns
        -------
        PointType | VectorType
            The (potentially transposed) product of the Jacobian w.r.t. the variables,
            evaluated in `point`, and the vector `x`.
        PointType | VectorType
            The (potentially transposed) product of the Jacobian w.r.t. the conjugated
            variables, evaluated in `point`, and the vector `x`.
        """
        ...


class PreconditionerFcn(Protocol[PointType]):
    """Function applying a preconditioner."""

    def __call__(self, point: PointType, b: PointType, /) -> PointType:
        """Apply a preconditioner.

        Parameters
        ----------
        point : PointType
            Point used to compute the preconditioner.
        b : PointType
            Vector to which the preconditioner is applied.

        Returns
        -------
        PointType
            The result of applying the preconditioner.
        """
        ...


class ResidualFcn(Protocol[PointTypeContra]):
    r"""Function computing the residual.

    The function has the signature::

        (point: PointType) -> tl.typing.ArrayType

    Examples
    --------
    To compute the best rank-1 approximation of a matrix :math:`\mat{M}`, one can
    minimize

    .. math::

        \underset{\vec{a}, \vec{b}}{\text{minimize}}\ \frac12
        \| \vec{a} \vec{b}^{\T} - \mat{M} \|^2_{\F},

    hence the residual :math:`\vec{F}(\vec{z}) = \vec{a} \vec{b}^{\T} - \mat{M}` where
    :math:`\vec{z}` contains the variables :math:`\vec{a}` and :math:`\vec{b}`, which
    can be complex.

    >>> import numpy as np
    >>> def residual(z):
    ...     m, _ = M.shape  # assume M is known
    ...     a, b = z[:m], z[m:]
    ...     return np.outer(a, b) - M

    The point ``z`` is given as a :class:`numpy.ndarray` above. Alternatively, ``z`` can
    be any convenient type, e.g., a :class:`.PolyadicTensor` with factors ``a`` and
    ``b``:

    >>> import pytensorlab as tl
    >>> def residual(z: tl.PolyadicTensor) -> tl.typing.ArrayType:
    ...     return tl.residual(z, M)  # assume M is known
    """

    def __call__(self, point: PointTypeContra, /) -> ArrayType:
        """Compute the residual.

        Parameters
        ----------
        point : PointType
            Compute the residual in this point.

        Returns
        -------
        ArrayType
            The computed residual.
        """
        ...

"""Complex optimization methods.

A framework for and several implementations of complex optimization methods is defined,
as well as support methods that allow consistent printing and logging. The optimization
methods are designed to handle minimization of a real objective function in real or
complex variables, where the function is not necessarily holomorphic or analytic.
Small-scale and preconditioned large-scale internal solvers can be used.
"""

from .logger import OptimizationProgressLogger as OptimizationProgressLogger
from .logger import StoppingCriterion as StoppingCriterion
from .logger import StoppingCriterionAlgorithm as StoppingCriterionAlgorithm
from .logger import StoppingCriterionCustom as StoppingCriterionCustom
from .logger import StoppingCriterionReached as StoppingCriterionReached
from .logger import StoppingCriterionTolerance as StoppingCriterionTolerance
from .logger import default_stopping_criteria as default_stopping_criteria
from .methods import (
    GaussNewtonDirectNonHolomorphicProblem as GaussNewtonDirectNonHolomorphicProblem,
)
from .methods import GaussNewtonDirectProblem as GaussNewtonDirectProblem
from .methods import (
    GaussNewtonIterativeNonHolomorphicProblem as GaussNewtonIterativeNonHolomorphicProblem,  # noqa: E501
)
from .methods import GaussNewtonIterativeProblem as GaussNewtonIterativeProblem
from .methods import LBFGSProblem as LBFGSProblem
from .methods import (
    NewtonDirectNonHolomorphicProblem as NewtonDirectNonHolomorphicProblem,
)
from .methods import NewtonDirectProblem as NewtonDirectProblem
from .methods import (
    NewtonIterativeNonHolomorphicProblem as NewtonIterativeNonHolomorphicProblem,
)
from .methods import NewtonIterativeProblem as NewtonIterativeProblem
from .printer import NoneFormatter as NoneFormatter
from .printer import PrinterField as PrinterField
from .printer import ProgressPrinter as ProgressPrinter
from .printer import VoidPrinter as VoidPrinter
from .printer import conditional_printer as conditional_printer
from .printer import default_printer_fields as default_printer_fields
from .protocols import ComplexHessianFcn as ComplexHessianFcn
from .protocols import ComplexHessianVectorProductFcn as ComplexHessianVectorProductFcn
from .protocols import ComplexJacobianFcn as ComplexJacobianFcn
from .protocols import (
    ComplexJacobianVectorProductFcn as ComplexJacobianVectorProductFcn,
)
from .protocols import CustomLinearOperator as CustomLinearOperator
from .protocols import GradientFcn as GradientFcn
from .protocols import HessianFcn as HessianFcn
from .protocols import HessianVectorProductFcn as HessianVectorProductFcn
from .protocols import IterativeSolver as IterativeSolver
from .protocols import IterativeSolverOptions as IterativeSolverOptions
from .protocols import IterativeSolverQR as IterativeSolverQR
from .protocols import JacobianFcn as JacobianFcn
from .protocols import JacobianVectorProductFcn as JacobianVectorProductFcn
from .protocols import ObjectiveFcn as ObjectiveFcn
from .protocols import PreconditionerFcn as PreconditionerFcn
from .protocols import ResidualFcn as ResidualFcn
from .trust_region import OptimizationOptions as OptimizationOptions
from .trust_region import TrustRegionOptimizer as TrustRegionOptimizer
from .trust_region import minimize_dogleg as minimize_dogleg
from .trust_region import minimize_trust_region as minimize_trust_region

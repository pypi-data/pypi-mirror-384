"""Default optimization settings for external libraries, i.e. scipy.optimization.

Set the default optimization settings of the external libraries such that all
optimization procedure can be controlled by `OptimizationProgressLogger` and
`StoppingCriteria`.
"""

from typing import Any

default_minimize_options: dict[str, Any] = {"tol": 1e-30}

default_minimize_solver_options: dict[str, dict[str, Any]] = {}

default_minimize_solver_options["newton-cg"] = {
    "xtol": 1e-30,
    "maxiter": 1500,
    "disp": False,
}

default_minimize_solver_options["trust-ncg"] = {"gtol": 1e-30, "disp": False}

default_minimize_solver_options["trust-krylov"] = {"inexact": False}

default_minimize_solver_options["bfgs"] = {
    "gtol": 1e-30,
    "maxiter": 15000,
}


default_minimize_solver_options["cg"] = {
    "gtol": 1e-16,
    "maxiter": None,
}

default_minimize_solver_options["l-bfgs-b"] = {
    "ftol": 1e-30,
    "gtol": 1e-30,
    "maxfun": 15000,
    "maxiter": 15000,
}

__all__ = ["default_minimize_options", "default_minimize_solver_options"]

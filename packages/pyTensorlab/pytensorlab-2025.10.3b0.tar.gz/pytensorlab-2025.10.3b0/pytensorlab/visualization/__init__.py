"""Visualization methods for third-order tensors."""

import pytensorlab.visualization._vedo_settings  # noqa

from .plot_convergence import plot_convergence as plot_convergence
from .plot_rank1_terms import plot_rank1_terms as plot_rank1_terms
from .plot_slice_error import plot_slice_error as plot_slice_error
from .slice3 import slice3 as slice3
from .slice3 import surf3 as surf3
from .voxel3 import voxel3 as voxel3

__all__ = [
    "slice3",
    "surf3",
    "voxel3",
    "plot_convergence",
    "plot_slice_error",
    "plot_rank1_terms",
]

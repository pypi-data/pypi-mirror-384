"""Algorithm for computing tensor decompositions.

This package provides algorithms for the computation of several tensor decompositions
using numerical linear algebra techniques and complex optimization. Both low-level
functions implementing a single technique as high-level algorithms providing a multistep
approach are available. Currently the following decompositions are supported: canonical
polyadic decomposition (CPD), multilinear singular value decomposition (MLSVD), Tucker
decomposition or low multilinear rank approximation (LMLRA) and tensor-train (TT)
decomposition. Additionally, techniques for generating tensors with prescribed
multilinear singular values are included.
"""

from .cpd import cpd as cpd
from .cpd import cpd_svd as cpd_svd
from .cpd import estimate_remaining as estimate_remaining
from .cpd_gevd import cpd_gevd as cpd_gevd
from .cpd_gevd import cpdals_step as cpdals_step
from .cpd_gevd import fit_rank1 as fit_rank1
from .cpd_opt import CPDAlsOptions as CPDAlsOptions
from .cpd_opt import CPDMinfOptions as CPDMinfOptions
from .cpd_opt import CPDNlsOptions as CPDNlsOptions
from .cpd_opt import PolyadicKernel as PolyadicKernel
from .cpd_opt import cpd_als as cpd_als
from .cpd_opt import cpd_minf as cpd_minf
from .cpd_opt import cpd_nls as cpd_nls
from .cpd_opt import cpd_nls_scipy as cpd_nls_scipy
from .gentensor_mlsv import gentensor_mlsv as gentensor_mlsv
from .gentensor_mlsv import gentensor_mlsv_altproj as gentensor_mlsv_altproj
from .lmlra import LMLRAHooiOptions as LMLRAHooiOptions
from .lmlra import LMLRAKernel as LMLRAKernel
from .lmlra import LMLRAMansdOptions as LMLRAMansdOptions
from .lmlra import LMLRAMantrOptions as LMLRAMantrOptions
from .lmlra import LMLRAMinfOptions as LMLRAMinfOptions
from .lmlra import LMLRANlsOptions as LMLRANlsOptions
from .lmlra import TuckerKernel as TuckerKernel
from .lmlra import colspace_large_scale_hooi as colspace_large_scale_hooi
from .lmlra import lmlra as lmlra
from .lmlra import lmlra_hooi as lmlra_hooi
from .lmlra import lmlra_mansd as lmlra_mansd
from .lmlra import lmlra_mantr as lmlra_mantr
from .lmlra import lmlra_minf as lmlra_minf
from .lmlra import lmlra_nls as lmlra_nls
from .lra import lra_eig as lra_eig
from .lra import lra_svd as lra_svd
from .mlsvd import colspace_eig as colspace_eig
from .mlsvd import colspace_eigs as colspace_eigs
from .mlsvd import colspace_qr as colspace_qr
from .mlsvd import colspace_qrs as colspace_qrs
from .mlsvd import colspace_rsvd as colspace_rsvd
from .mlsvd import colspace_svd as colspace_svd
from .mlsvd import mlsvals as mlsvals
from .mlsvd import mlsvd as mlsvd
from .mlsvd import mlsvd_rsi as mlsvd_rsi
from .mlsvd import mlsvds as mlsvds
from .mlsvd import svd_rsi as svd_rsi

# Import additional functions in this subpackage
from .TensorOptimizationKernel import (
    TensorOptimizationKernel as TensorOptimizationKernel,
)
from .TensorOptimizationKernel import cached as cached
from .TensorOptimizationKernel import ensure_deserialized as ensure_deserialized
from .tt import TT as TT
from .tt import tt_eig as tt_eig
from .tt import tt_svd as tt_svd

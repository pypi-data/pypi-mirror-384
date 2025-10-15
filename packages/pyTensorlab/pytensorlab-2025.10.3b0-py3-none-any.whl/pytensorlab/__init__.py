"""A python package for tensor computations and complex optimization.

pyTensorlab provides

- data types to represent sparse, incomplete, structured and decomposed tensors
  efficiently;
- tools to generate and work with these data types effectively and efficiently;
- algorithms for computing the canonical polyadic decomposition, the multilinear
  singular value decomposition, the Tucker decomposition or low multilinear rank
  approximation and the tensor-train decomposition;
- tensorization techniques relying on statistics or Hankelization;
- preconditioned Gauss--Newton type optimization methods for complex variables;
- visualization techniques.
"""

from pytensorlab import random as random
from pytensorlab.algorithms import CPDAlsOptions as CPDAlsOptions
from pytensorlab.algorithms import CPDMinfOptions as CPDMinfOptions
from pytensorlab.algorithms import CPDNlsOptions as CPDNlsOptions
from pytensorlab.algorithms import LMLRAHooiOptions as LMLRAHooiOptions
from pytensorlab.algorithms import LMLRAKernel as LMLRAKernel
from pytensorlab.algorithms import LMLRAMansdOptions as LMLRAMansdOptions
from pytensorlab.algorithms import LMLRAMantrOptions as LMLRAMantrOptions
from pytensorlab.algorithms import LMLRAMinfOptions as LMLRAMinfOptions
from pytensorlab.algorithms import LMLRANlsOptions as LMLRANlsOptions
from pytensorlab.algorithms import PolyadicKernel as PolyadicKernel
from pytensorlab.algorithms import TuckerKernel as TuckerKernel
from pytensorlab.algorithms import cpd as cpd
from pytensorlab.algorithms import cpd_als as cpd_als
from pytensorlab.algorithms import cpd_gevd as cpd_gevd
from pytensorlab.algorithms import cpd_minf as cpd_minf
from pytensorlab.algorithms import cpd_nls as cpd_nls
from pytensorlab.algorithms import cpd_nls_scipy as cpd_nls_scipy
from pytensorlab.algorithms import cpd_svd as cpd_svd
from pytensorlab.algorithms import cpdals_step as cpdals_step
from pytensorlab.algorithms import estimate_remaining as estimate_remaining
from pytensorlab.algorithms import fit_rank1 as fit_rank1
from pytensorlab.algorithms import gentensor_mlsv as gentensor_mlsv
from pytensorlab.algorithms import gentensor_mlsv_altproj as gentensor_mlsv_altproj
from pytensorlab.algorithms import lmlra as lmlra
from pytensorlab.algorithms import lmlra_hooi as lmlra_hooi
from pytensorlab.algorithms import lmlra_mansd as lmlra_mansd
from pytensorlab.algorithms import lmlra_mantr as lmlra_mantr
from pytensorlab.algorithms import lmlra_minf as lmlra_minf
from pytensorlab.algorithms import lmlra_nls as lmlra_nls
from pytensorlab.algorithms import mlsvals as mlsvals
from pytensorlab.algorithms import mlsvd as mlsvd
from pytensorlab.algorithms import mlsvd_rsi as mlsvd_rsi
from pytensorlab.algorithms import mlsvds as mlsvds
from pytensorlab.algorithms import svd_rsi as svd_rsi
from pytensorlab.algorithms import tt_eig as tt_eig
from pytensorlab.algorithms import tt_svd as tt_svd
from pytensorlab.datatypes import DeferredResidual as DeferredResidual
from pytensorlab.datatypes import HankelTensor as HankelTensor
from pytensorlab.datatypes import IncompleteTensor as IncompleteTensor
from pytensorlab.datatypes import PolyadicTensor as PolyadicTensor
from pytensorlab.datatypes import SparseTensor as SparseTensor
from pytensorlab.datatypes import Tensor as Tensor
from pytensorlab.datatypes import TensorTrainTensor as TensorTrainTensor
from pytensorlab.datatypes import TuckerTensor as TuckerTensor
from pytensorlab.datatypes import _noisy_array as _noisy_array
from pytensorlab.datatypes import _noisy_polyadic as _noisy_polyadic
from pytensorlab.datatypes import _noisy_tucker as _noisy_tucker
from pytensorlab.datatypes import dehankelize as dehankelize
from pytensorlab.datatypes import dehankelize_terms as dehankelize_terms
from pytensorlab.datatypes import frob as frob
from pytensorlab.datatypes import getitem as getitem
from pytensorlab.datatypes import hankelize as hankelize
from pytensorlab.datatypes import inprod as inprod
from pytensorlab.datatypes import mat2tens as mat2tens
from pytensorlab.datatypes import match_by_congruence as match_by_congruence
from pytensorlab.datatypes import matdot as matdot
from pytensorlab.datatypes import matricize as matricize
from pytensorlab.datatypes import mtkronprod as mtkronprod
from pytensorlab.datatypes import mtkrprod as mtkrprod
from pytensorlab.datatypes import residual as residual
from pytensorlab.datatypes import tens2mat as tens2mat
from pytensorlab.datatypes import tens2vec as tens2vec
from pytensorlab.datatypes import (
    tensor_left_right_interface_product as tensor_left_right_interface_product,
)
from pytensorlab.datatypes import tmprod as tmprod
from pytensorlab.datatypes import tvprod as tvprod
from pytensorlab.datatypes import vectorize as vectorize
from pytensorlab.optimization import (
    default_stopping_criteria as default_stopping_criteria,
)
from pytensorlab.optimization import minimize_trust_region as minimize_trust_region
from pytensorlab.random import get_rng as get_rng
from pytensorlab.random import set_rng as set_rng
from pytensorlab.tensorization import cum3 as cum3
from pytensorlab.tensorization import cum4 as cum4
from pytensorlab.tensorization import dcov as dcov
from pytensorlab.tensorization import scov as scov
from pytensorlab.tensorization import stcum4 as stcum4
from pytensorlab.tensorization import xcum4 as xcum4
from pytensorlab.util import argmax as argmax
from pytensorlab.util import argmin as argmin
from pytensorlab.util import argsort as argsort
from pytensorlab.util import cumsum as cumsum
from pytensorlab.util import get_name as get_name
from pytensorlab.util import get_options as get_options
from pytensorlab.util import hadamard as hadamard
from pytensorlab.util import hadamard_all as hadamard_all
from pytensorlab.util import inprod_kr as inprod_kr
from pytensorlab.util import kr as kr
from pytensorlab.util import kron as kron
from pytensorlab.util import krr as krr
from pytensorlab.util import noisy as noisy
from pytensorlab.visualization import plot_convergence as plot_convergence
from pytensorlab.visualization import plot_rank1_terms as plot_rank1_terms
from pytensorlab.visualization import plot_slice_error as plot_slice_error
from pytensorlab.visualization import slice3 as slice3
from pytensorlab.visualization import surf3 as surf3
from pytensorlab.visualization import voxel3 as voxel3

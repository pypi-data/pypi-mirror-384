"""Data types for efficient representation of tensors.

Several classes are defined that represent sparse, incomplete or structured
tensors. Operations to select items or parts and to perform multiplications with
matrices and tensors are defined. Efficient implementations of several important
products that are often required when computing tensor decompositions are implemented.
Currently, the following data types are available: dense (:class:`numpy.ndarray`),
sparse, incomplete, polyadic, Tucker, tensor-train and Hankel. A special deferred
residual class is used to store the residual without actually computing it, which
enables efficient operations in algorithms.
"""

from .binops import inprod as inprod
from .binops import matdot as matdot
from .binops import residual as residual
from .core import frob as frob
from .core import getitem as getitem
from .core import mat2tens as mat2tens
from .core import matricize as matricize
from .core import mtkronprod as mtkronprod
from .core import mtkrprod as mtkrprod
from .core import tens2mat as tens2mat
from .core import tens2vec as tens2vec
from .core import tmprod as tmprod
from .core import tvprod as tvprod
from .core import vectorize as vectorize
from .deferred_residual import DeferredResidual as DeferredResidual
from .hankel import HankelTensor as HankelTensor
from .hankel import dehankelize as dehankelize
from .hankel import dehankelize_terms as dehankelize_terms
from .hankel import hankelize as hankelize
from .ndarray import _noisy_array as _noisy_array
from .operators import (
    tensor_left_right_interface_product as tensor_left_right_interface_product,
)
from .partial import IncompleteTensor as IncompleteTensor
from .partial import SparseTensor as SparseTensor
from .polyadic import PolyadicTensor as PolyadicTensor
from .polyadic import _noisy_polyadic as _noisy_polyadic
from .polyadic import match_by_congruence as match_by_congruence
from .tensor import Tensor as Tensor
from .tensortrain import TensorTrainTensor as TensorTrainTensor
from .tucker import TuckerTensor as TuckerTensor
from .tucker import _noisy_tucker as _noisy_tucker

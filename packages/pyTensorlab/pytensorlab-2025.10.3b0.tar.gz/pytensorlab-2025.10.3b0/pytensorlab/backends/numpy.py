"""Implementation of array operations with numpy."""

from functools import partial
from typing import Any, cast

import numpy as np
import numpy.linalg as nla
import scipy.linalg as sla
import scipy.sparse.linalg as sspla
from numpy import tensordot as tensordot

from pytensorlab.typing import MatrixType, VectorType

cond = nla.cond
eig = sla.eig
eigh = sla.eigh
eigsh = sspla.eigsh
eigvalsh = nla.eigvalsh
svdvals = nla.svdvals
einsum = np.einsum
inv = nla.inv


def iscomplexobj(x: Any) -> bool:
    """Check for a complex type or an array of complex numbers.

    See Also
    --------
    `np.iscomplexobj`
    """
    try:
        return x.iscomplex()
    except AttributeError:
        return np.iscomplexobj(x)


lstsq = partial(nla.lstsq, rcond=None)
norm = nla.norm
orth = sla.orth
pad = np.pad
pinv = nla.pinv
qr = nla.qr
solve = nla.solve
svd = nla.svd


def solve_hermitian(A: MatrixType, B: MatrixType) -> MatrixType:
    """Solve a linear system of equations with a Hermitian matrix.

    See Also
    --------
    `scipy.linalg.solve`
    """
    return sla.solve(A, B, assume_a="her")


def norm2(a: VectorType) -> float:
    """Compute squared norm of a vector.

    Parameters
    ----------
    a : VectorType
        Array of which the norm is computed.

    Returns
    -------
    float
        Squared norm of the vector.
    """
    return cast(float, np.vdot(a, a).real)


__ALL__ = [
    "cond",
    "eig",
    "eigh",
    "eigsh",
    "eigvalsh",
    "svdvals",
    "einsum",
    "inv",
    "iscomplexobj",
    "lstsq",
    "norm",
    "norm2",
    "orth",
    "pinv",
    "qr",
    "solve",
    "solve_hermitian",
    "svd",
    "pad",
]

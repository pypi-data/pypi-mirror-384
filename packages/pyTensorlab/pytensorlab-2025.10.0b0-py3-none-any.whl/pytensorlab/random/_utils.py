from __future__ import annotations

from numpy.typing import ArrayLike

import pytensorlab.backends.numpy as tlb
from pytensorlab.typing import ArrayType, SupportsArrayFromShape

from .rng import get_rng


def _random(
    size: int,
    real: SupportsArrayFromShape | None = None,
    imag: SupportsArrayFromShape | bool | None = None,
) -> ArrayType:
    """Return a random sample of a given size.

    Parameters
    ----------
    size : int
        Size of random sample.
    real : SupportsArrayFromShape, optional
        Function generating a random sample of given shape used for the real part. If
        None, the real numbers are drawn from a uniform distribution.
    imag : SupportsArrayFromShape | bool, optional
        If this argument is False or None, no complex factors are generated and the
        result is real. If `imag` is True, the function provided to `real` is also used
        to generate the imaginary part of the factors. If a random number generating
        function is provided, this function is used for generating the imaginary part
        of the factors.

    Returns
    -------
    ArrayType
        Random sample of given size.

    See Also
    --------
    _random_like
    """
    if real is None:
        real = get_rng().random

    data_real = real((size,))
    if data_real.shape != (size,):
        raise ValueError(
            f"real did not yield a valid ArrayLike object of the correct shape: "
            f"shape is {data_real.shape} while expected {(size,)}"
        )
    if imag:
        if isinstance(imag, bool):
            imag = real
        data_imag = imag((size,))
        if data_imag.shape != (size,):
            raise ValueError(
                f"imag did not yield a valid ArrayLike object of the correct shape: "
                f"shape is {data_imag.shape} while expected {(size,)}"
            )
        return data_real + 1j * data_imag

    return data_real


def _random_like(
    array: ArrayLike,
    size: int,
    real: SupportsArrayFromShape | None = None,
    imag: SupportsArrayFromShape | bool | None = None,
) -> ArrayType:
    """Return a random sample of a given size with the same type as a given array.

    Parameters
    ----------
    array : ArrayLike
        Array used to determine properties.
    size : int
        Size of random sample.
    real : SupportsArrayFromShape, optional
        Function generating a random sample of given shape used for the real part. If
        None, the real numbers are drawn from a uniform distribution.
    imag : SupportsArrayFromShape | bool, optional
        If this argument is False, no complex factors are generated and the result is
        real. If `imag` is None or True, complex factors are only generated if `array`
        is complex, where the imaginary part is generated using the function provided
        to `real`. If a random number generating function is provided, this function is
        used for generating the imaginary part of the factors.

    Returns
    -------
    ArrayType
        Random sample of given size with real or complex elements.

    See Also
    --------
    _random
    """
    if real is None:
        real = get_rng().random

    if (imag is None and tlb.iscomplexobj(array)) or (isinstance(imag, bool) and imag):
        imag = real
    return _random(size, real, imag)

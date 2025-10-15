"""Global random number generator of pyTensorlab."""

from collections.abc import Callable
from typing import Protocol

import numpy as np


class RandomState:
    """A wrapper class for a global random number generator."""

    _rng = np.random.default_rng()

    @classmethod
    def get_rng(
        cls, rng: np.random.Generator | int | None = None
    ) -> np.random.Generator:
        """Return the global random number generator of pyTensorlab.

        Parameters
        ----------
        rng: numpy.random.Generator | int | None
            If None, return the global random number generator. If a generator, return
            that generator. If an integer, return a new generator with that number as
            seed.

        Returns
        -------
        numpy.random.Generator
            A random number generator.

        See Also
        --------
        set_rng
        """
        if rng is None:
            return cls._rng
        elif isinstance(rng, int):
            return np.random.default_rng(rng)
        else:
            return rng

    @classmethod
    def set_rng(cls, new_rng: np.random.Generator | int) -> None:
        """Set the global random number generator of pyTensorlab.

        Parameters
        ----------
        new_rng: numpy.random.Generator | int
            If a generator, set the global generator to that generator. If an integer,
            set the global generator to a new generator with that number as seed.

        See Also
        --------
        get_rng
        """
        if isinstance(new_rng, int):
            new_rng = np.random.default_rng(new_rng)
        cls._rng = new_rng


class GetRNGFcn(Protocol):
    def __call__(
        self, rng: np.random.Generator | int | None = ...
    ) -> np.random.Generator: ...


get_rng: GetRNGFcn = RandomState.get_rng
set_rng: Callable[[np.random.Generator | int], None] = RandomState.set_rng

__all__ = ["get_rng", "set_rng"]

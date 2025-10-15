"""Lazy loader loading packages on first use.

This class can be used to load imports on the first time one of their attributes is
accessed, instead of when the file is loaded.

Examples
--------
Lazy load numpy, meaning it is only loaded once `np.ones` is called.

>>> np = LazyLoader("numpy")
>>> np.ones(1, )
array([1.])
"""

import importlib
from collections.abc import Callable


class LazyLoader:
    """Holds a module that will only be loaded on the first use.

    The `LazyLoader` remembers the name of a module and will only load it once one of
    its attributes is accessed. When it first imports the module, it will call a
    callback function, if defined. Further calls to the module will just pass through
    without importing the package again.

    Parameters
    ----------
    module_name : str
        The name of the module to import.
    callback : Callable[[ModuleType], None]
        Function called on first import, with as argument the imported module.

    Examples
    --------
    Lazy load numpy, meaning it is only loaded once `np.arange` is called.

    >>> np = LazyLoader("numpy")
    >>> np.arange(10)
    array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

    A callback is added to set the print preferences during the first import.
    The module is still only loaded once `np.arange` is called.

    >>> np = LazyLoader("numpy", lambda np: np.set_printoptions(threshold=5))
    >>> np.arange(10)
    array([0, 1, 2, ..., 7, 8, 9])
    """

    def __init__(
        self,
        module_name: str,
        callback: Callable[["LazyLoader"], None] | None = None,
    ):
        self._module_name = module_name
        self._module = None
        self._callback = callback

    def __getattr__(self, attr):
        """Fetch an attribute of the module, importing the module first if needed."""
        if self._module is None:
            self._module = importlib.import_module(self._module_name)

            if self._callback is not None:
                self._callback(self)

        return getattr(self._module, attr)

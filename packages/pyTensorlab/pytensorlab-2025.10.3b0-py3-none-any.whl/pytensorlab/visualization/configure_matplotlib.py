"""Auxiliary function to load matplotlib."""


def configure_matplotlib_backend(
    preferred_backend: str = "TkAgg", verbose: bool = False
) -> None:
    """Safely configure Matplotlib backend for all environments.

    Select the correct backend in case headless setups or Jupyter notebooks are used.

    Parameters
    ----------
    preferred_gui_backend : str = "TkAgg"
        GUI backend to use if display is available.
    verbose : bool = False
        Print diagnostic messages.
    """
    import os

    import matplotlib

    def in_notebook() -> bool:
        """Return True if running inside Jupyter or IPython."""
        try:
            try:
                # Newer IPython (preferred import)
                from IPython.core.getipython import get_ipython
            except ImportError:
                # Fallback for older IPython
                from IPython import get_ipython  # type: ignore

            shell = get_ipython().__class__.__name__
            return shell in ("ZMQInteractiveShell", "Shell")  # Jupyter/IPython
        except Exception:
            return False

    def has_display() -> bool:
        """Return True if a graphical display is available."""
        if os.name == "posix":
            return bool(os.environ.get("DISPLAY"))
        elif os.name == "nt":  # Windows
            return os.environ.get("CI", "").lower() not in ("1", "true")
        return True  # macOS and others usually have a display

    # --- Jupyter Notebook ---
    if in_notebook():
        try:
            try:
                # Newer IPython (preferred import)
                from IPython.core.getipython import get_ipython
            except ImportError:
                # Fallback for older IPython
                from IPython import get_ipython  # type: ignore

            ip = get_ipython()
            assert ip is not None
            ip.run_line_magic("matplotlib", "inline")
            if verbose:
                print("Jupyter environment detected: using '%matplotlib inline'")
        except Exception as e:
            if verbose:
                print(f"could not set inline backend: {e}")
        return

    # --- Headless environment ---
    if not has_display():
        matplotlib.use("Agg", force=True)
        if verbose:
            print("headless environment detected: using 'Agg'")
        return

    # --- Interactive environment with display ---
    try:
        matplotlib.use(preferred_backend, force=True)
        if verbose:
            print(f"using interactive backend: {preferred_backend}")
    except ImportError:
        matplotlib.use("Agg", force=True)
        if verbose:
            print(f"{preferred_backend} not available: falling back to 'Agg'")

"""Plot convergence curves for an optimization method."""

import numpy as np

from .configure_matplotlib import configure_matplotlib_backend

configure_matplotlib_backend()

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from itertools import zip_longest
from typing import Any

from matplotlib import colormaps
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib.typing import ColorType
from matplotlib.widgets import CheckButtons

from pytensorlab.optimization import OptimizationProgressLogger


def plot_convergence(
    logger: OptimizationProgressLogger, model_name: str | None = None
) -> tuple[Figure, Axes]:
    """Plot convergence curves from an optimization logger.

    Parameters
    ----------
    logger : OptimizationProgressLogger
        Log containing progress values and stopping criteria.
    model_name : str, default = None
        Title label indicating the model name in the convergence plot. If None, a
        generic title "Convergence curves" is used instead.

    Returns
    -------
    figure : matplotlib.figure.Figure
        Figure containing the plot.
    axis : matplotlib.axes.Axes
        An axes associated with the figure.

    Examples
    --------
    Example 1: Using :func:`.cpd`:

    >>> import pytensorlab as tl
    >>> import numpy as np
    >>> shape = (10, 12, 15)
    >>> nterm = 5
    >>> T = tl.PolyadicTensor.rand(shape, nterm)
    >>> Tnoisy = tl.noisy(np.array(T), snr=20)
    >>> options = tl.CPDNlsOptions(tol_relfval=1e-18, tol_relstep=1e-8)
    >>> Tinit = tl.PolyadicTensor.rand(shape, nterm)
    >>> _, info_cpd = tl.cpd(
    ...     Tnoisy,
    ...     nterm,
    ...     initialization=Tinit,
    ...     optimization=tl.cpd_nls,
    ...     optimization_options=options,
    ... )
    >>> tl.plot_convergence(info_cpd.optimization_info.log)

    Example 2: Using :func:`.cpd_nls`:

    >>> _, log = tl.cpd_nls(Tnoisy, Tinit, options)
    >>> tl.plot_convergence(log)
    """
    if getattr(logger, "niterations", 0) < 1:
        raise ValueError("logger is empty: no progress information has been recorded")

    figure, axis = plt.subplots()
    figure.subplots_adjust(
        left=0.1, right=0.7, top=0.9, bottom=0.1, wspace=0.4, hspace=0.5
    )
    if model_name is not None:
        figure.suptitle(f"Convergence curves: {model_name}", x=0.4)
    else:
        figure.suptitle("Convergence curves", x=0.4)

    criteria_tolerances = _get_criteria_tolerances(logger)
    num_fields = len(criteria_tolerances)
    cmap = colormaps.get_cmap("tab10")
    line_colors: list[ColorType] = [cmap(i) for i in range(num_fields)]
    checkbuttons = None
    if num_fields > 0:
        status = [True] + [False] * (num_fields - 1)
        labels = [f"{label}" for label in criteria_tolerances.keys()]
        height = min(0.1 + 0.2 * min(num_fields, 5) / 5, 0.4)
        ax_checkbuttons = plt.axes((0.76, 0.2, 0.12, height), frameon=False)
        checkbuttons = CheckButtons(
            ax_checkbuttons,
            labels,
            status,
            label_props={"color": line_colors},
        )

    def callback(_=None):
        """Update the plot based on a GUI event."""
        if checkbuttons is not None:
            if sum(checkbuttons.get_status()) == 0:
                checkbuttons.set_active(0)
            status = checkbuttons.get_status()
            selected_criteria_tolerances = {
                key: value
                for (key, value), state in zip(criteria_tolerances.items(), status)
                if state
            }
            selected_line_colors = [
                color for color, state in zip(line_colors, status) if state
            ]
            draw_figure(
                axis, logger, selected_criteria_tolerances, selected_line_colors
            )
            axis.legend(
                title=f"Algorithm: {logger.algorithm.__name__}",
                loc="center left",
                bbox_to_anchor=(1, 0.8),
            )
            reason_termination = logger.reason_termination
            if reason_termination is not None:
                msg = reason_termination.description.removeprefix("stop if ")
                axis.set_title(msg.capitalize(), fontsize=10)
        figure.canvas.draw_idle()
        plt.pause(0.00001)

    if checkbuttons:
        checkbuttons.on_clicked(callback)

    callback()  # initial plot
    figure.align_labels()
    plt.show()

    return figure, axis


@dataclass
class Tolerance:
    """Tolerance with a label and a value."""

    label: str
    value: float | None = None


def draw_figure(
    axis: Axes,
    logger: OptimizationProgressLogger,
    criteria_tolerances: Mapping[str, Tolerance],
    colors: list[ColorType] | None = None,
) -> None:
    """Draw convergence curves for the specified stopping criteria.

    Parameters
    ----------
    axis : matplotlib.axes.Axes
        An axes associated with the figure.
    logger : OptimizationProgressLogger
        Log containing progress values and stopping criteria.
    criteria_tolerances : dict[str, Tolerance]
        Labeled tolerance values used in stopping criteria.
    colors : list[ColorType], optional
        List of colors for plotting the convergence curves. Each entry can be any valid
        Matplotlib color specification (see :mod:`matplotlib.colors`). If None, the
        default Matplotlib colors are used.

    See Also
    --------
    matplotlib.pyplot
    """
    axis.clear()
    for (field_name, tolerance), color in zip_longest(
        criteria_tolerances.items(), colors or []
    ):
        # convergence curves
        curve_data = getattr(logger, field_name, [])
        zero_fields = ("fval", "normgrad")
        start_iter = 0 if field_name in zero_fields else 1
        x = np.arange(start_iter, start_iter + len(curve_data))
        if field_name is not None:
            options: MutableMapping[str, Any] = dict()
            if len(x) < 250:
                options["marker"] = "o"
                options["markersize"] = 2
            axis.semilogy(x, curve_data, label=field_name, color=color, **options)

        # tolerance lines
        if tolerance and tolerance.value:
            axis.axhline(
                tolerance.value,
                color=color,
                linestyle="--",
                label=f"{tolerance.label}: {tolerance.value:.3g}",
            )
        axis.set_xlabel("Iteration")
        axis.xaxis.set_major_locator(MaxNLocator(integer=True))


def _get_criteria_tolerances(
    logger: OptimizationProgressLogger,
) -> dict[str, Tolerance]:
    mapping = {
        "fval": "tol_absfval",
        "relative_fval": "tol_relfval",
        "relative_step": "tol_relstep",
        "max_subspace_angle": "tol_subspace",
        "normgrad": "tol_normgrad",
    }

    criteria_tolerences: dict[str, Tolerance] = {"fval": Tolerance("tol_absfval", None)}
    for criterion in logger.stopping_criteria:
        field = getattr(criterion, "field", None)
        tolerance = getattr(criterion, "tolerance", None)
        if field in mapping:
            criteria_tolerences.update({field: Tolerance(mapping[field], tolerance)})
    return criteria_tolerences

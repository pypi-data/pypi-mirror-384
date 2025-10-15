"""Plot the rank-1 terms of a tensor in polyadic decomposition format."""

import itertools as it
from enum import Enum

import numpy as np

from .configure_matplotlib import configure_matplotlib_backend

configure_matplotlib_backend()

from collections.abc import Callable, Sequence
from typing import Literal

from matplotlib import colormaps
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.typing import ColorType
from matplotlib.widgets import CheckButtons, RadioButtons, Slider

from pytensorlab.datatypes import PolyadicTensor
from pytensorlab.typing import PositiveInt, VectorType


def plot_rank1_terms(
    T: PolyadicTensor,
    title: str = "CPD factors",
    max_modes: PositiveInt = 3,
    max_terms: PositiveInt = 3,
    combine: bool = False,
) -> tuple[Figure, list[list[Axes]]]:
    """Plot the rank-1 terms of a polyadic tensor.

    Parameters
    ----------
    T : PolyadicTensor
        The tensor whose rank-1 terms are to be plotted.
    title : str, default = "CPD factors"
        The title text for the plot.
    max_modes : PositiveInt, default = 3
        The maximum number of modes to display.
    max_terms : PositiveInt, default = 3
        The maximum number of terms to display. This is used when `combine` is set to
        False. If `combine` is True, terms are shown on a panel with check buttons.
    combine : bool, default = False
        If True, the factor vectors per mode of selected rank-1 terms are plotted in
        the same axes.

    Returns
    -------
    figure : matplotlib.figure.Figure
        Figure containing the plot.
    axes : list[list[matplotlib.axes.Axes]]
        A 2D list of :class:`matplotlib.axes.Axes`, representing subplots in a grid.
        ``axes[row][col]`` accesses the subplot at the given row and column.

    Examples
    --------
    >>> import pytensorlab as tl
    >>> shape = (10, 12, 15)
    >>> nterm = 5
    >>> T = tl.PolyadicTensor.rand(shape, nterm)
    >>> tl.plot_rank1_terms(T)
    """
    if combine:
        figure, axes = _plot_combined_rank1_terms(T, title, max_modes)
    else:
        figure, axes = _plot_rank1_terms(T, title, max_modes, max_terms)

    return figure, axes


def _plot_rank1_terms(
    T: PolyadicTensor,
    title: str,
    max_modes: PositiveInt,
    max_terms: PositiveInt,
) -> tuple[Figure, list[list[Axes]]]:
    """Plot individual rank-1 terms of a polyadic tensor.

    Parameters
    ----------
    T : PolyadicTensor
        The tensor whose rank-1 terms are to be plotted.
    title : str
        The title text for the plot.
    max_modes : PositiveInt
        The maximum number of modes to display.
    max_terms : PositiveInt
        The maximum number of terms to display.

    Returns
    -------
    figure : matplotlib.figure.Figure
        Figure containing the plot.
    axes : list[list[matplotlib.axes.Axes]]
        A 2D list of :class:`matplotlib.axes.Axes`, representing subplots in a grid.
    """
    ncols = min(T.nterm, max_terms)
    nrows = min(T.ndim, max_modes)

    figure, axes_array = plt.subplots(nrows, ncols)
    axes_array = np.atleast_2d(axes_array)
    axes: list[list[Axes]] = axes_array.tolist()
    figure.subplots_adjust(
        left=0.2, right=0.85, top=0.85, bottom=0.22, wspace=0.45, hspace=0.55
    )
    figure.suptitle(title)
    _add_inset(figure)

    mode_slider, term_slider = None, None
    if T.ndim > max_modes:
        mode_slider = _create_slider(
            rect=(0.90, 0.25, 0.025, 0.6),
            label="Modes",
            valmin=0,
            valmax=T.ndim - nrows,
            valinit=0,
            valstep=1,
            orientation="vertical",
            invert=True,
            axis="y",
            ticks=range(T.ndim - nrows + 1),
            tick_params={"left": False, "right": True},
            frameon=False,
        )
    if T.nterm > max_terms:
        term_slider = _create_slider(
            rect=(0.25, 0.09, 0.6, 0.04),
            label="Terms",
            valmin=0,
            valmax=T.nterm - ncols,
            valinit=0,
            valstep=1,
            orientation="horizontal",
            invert=False,
            axis="x",
            ticks=range(T.nterm - ncols + 1),
            tick_params={},
            frameon=False,
        )

    fix_checkbutton = _create_fix_ylim_checkbox(rect=(0.82, 0.96, 0.155, 0.04))

    num_types = len(PlotType)
    height_plot_type = num_types * 0.033  # Height per plot type entry
    bottom_plot_type = 1 - height_plot_type
    plot_type_radio = _create_plot_type_radio(
        rect=(0.005, bottom_plot_type, 0.11, height_plot_type)
    )

    current_state = {
        "modes": tuple(range(0, nrows)),
        "terms": tuple(range(0, ncols)),
        "fix_ylim": False,
        "plot_type": PlotType.scatter,
    }

    def update_plot():
        """Update the main plot based on a GUI event."""
        draw_figure(
            T,
            axes,
            current_state["modes"],
            current_state["terms"],
            current_state["fix_ylim"],
            current_state["plot_type"],
        )
        figure.canvas.draw_idle()
        plt.pause(0.0001)

    def update_terms(_=None):
        """Update selected terms and refresh the plot."""
        term_i = int(term_slider.val) if term_slider else 0
        new_terms = tuple(range(term_i, term_i + ncols))
        if new_terms != current_state["terms"]:
            current_state["terms"] = new_terms
            update_plot()

    # callbacks
    if term_slider:
        term_slider.on_changed(update_terms)

    if mode_slider:
        mode_slider.on_changed(
            lambda val: _update_modes(mode_slider, current_state, nrows, update_plot)
        )

    plot_type_radio.on_clicked(
        lambda label: _update_plot_type(plot_type_radio, current_state, update_plot)
    )

    fix_checkbutton.on_clicked(
        lambda label: _toggle_fix_y_axes(fix_checkbutton, current_state, update_plot)
    )

    update_plot()  # initial plot
    figure.align_labels()
    plt.show()
    return figure, axes


def _plot_combined_rank1_terms(
    T: PolyadicTensor,
    title: str,
    max_modes: PositiveInt,
    max_visible: PositiveInt = 20,
) -> tuple[Figure, list[list[Axes]]]:
    """Plot selected rank-1 terms of a polyadic tensor with combined mode axes.

    Factor vectors per mode of the selected terms are plotted in the same axes.

    Parameters
    ----------
    T : PolyadicTensor
        The tensor whose rank-1 terms are to be plotted.
    title : str
        The title text for the plot.
    max_modes : PositiveInt
        The maximum number of modes to display.
    max_visible : PositiveInt, default = 20
        The maximum number of visible terms and check buttons on the panel.

    Returns
    -------
    figure : matplotlib.figure.Figure
        Figure containing the plot.
    axes : list[list[matplotlib.axes.Axes]]
        A 2D list of :class:`matplotlib.axes.Axes`, representing subplots in a grid.
    """
    nrows = min(T.ndim, max_modes)

    figure, axes_array = plt.subplots(nrows, ncols=1)
    axes_array = np.atleast_2d(axes_array)
    axes: list[list[Axes]] = axes_array.tolist()
    figure.subplots_adjust(
        left=0.3, right=0.85, top=0.85, bottom=0.2, wspace=0.4, hspace=0.5
    )
    figure.suptitle(title, x=0.6, y=0.92)
    _add_inset(figure)

    cmap = colormaps.get_cmap("tab20")
    term_colors: list[ColorType] = [cmap(i / T.nterm) for i in range(T.nterm)]

    mode_slider, term_slider = None, None
    if T.ndim > max_modes:
        mode_slider = _create_slider(
            rect=(0.90, 0.25, 0.025, 0.6),
            label="Modes",
            valmin=0,
            valmax=T.ndim - max_modes,
            valinit=0,
            valstep=1,
            orientation="vertical",
            invert=True,
            axis="y",
            ticks=range(T.ndim - max_modes + 1),
            tick_params={"left": False, "right": True},
            frameon=False,
        )

    visible_terms = min(max_visible, T.nterm)
    visible_range = range(0, visible_terms)
    height = min(0.1 + 0.5 * min(visible_terms, 20) / 20, 0.6)
    if T.nterm > max_visible:
        term_slider = _create_slider(
            rect=(0.16, 0.25, 0.025, height),
            label="Terms",
            valmin=0,
            valmax=T.nterm - visible_terms,
            valinit=0,
            valstep=1,
            orientation="vertical",
            invert=True,
            axis="y",
            ticks=range(T.nterm - visible_terms + 1),
            tick_params={"left": False, "right": True},
            frameon=True,
        )

    fix_checkbutton = _create_fix_ylim_checkbox(rect=(0.82, 0.96, 0.155, 0.04))

    num_types = len(PlotType)
    height_plot_type = num_types * 0.033  # Height per plot type entry
    bottom_plot_type = 1 - height_plot_type
    plot_type_radio = _create_plot_type_radio(
        rect=(0.005, bottom_plot_type, 0.11, height_plot_type)
    )

    all_status = [True] + [False] * (T.nterm - 1)

    ax_checkbuttons = plt.axes((0.04, 0.25, 0.12, height), frameon=True)
    checkbuttons = _create_checkbuttons(
        ax=ax_checkbuttons,
        labels=[f"Term {i}" for i in range(0, visible_terms)],
        states=[all_status[i] for i in range(visible_terms)],
        colors=[term_colors[i] for i in range(visible_terms)],
    )

    current_state = {
        "modes": tuple(range(0, nrows)),
        "visible_range": visible_range,
        "selected_terms": tuple(np.flatnonzero(all_status)),
        "fix_ylim": False,
        "plot_type": PlotType.scatter,
    }

    def update_plot():
        """Update the combined plot based on a GUI event."""
        draw_figure(
            T,
            axes,
            current_state["modes"],
            current_state["selected_terms"],
            current_state["fix_ylim"],
            current_state["plot_type"],
            term_colors,
            True,
        )

        figure.canvas.draw_idle()
        plt.pause(0.0001)

    def update_terms(_=None):
        """Update selected terms and refresh the plot."""
        nonlocal checkbuttons
        term_i = int(term_slider.val) if term_slider else 0
        new_visible_range = range(term_i, term_i + visible_terms)

        old_states = checkbuttons.get_status()
        for i, idx in enumerate(current_state["visible_range"]):
            all_status[idx] = old_states[i]

        ax_checkbuttons.cla()
        checkbuttons = _create_checkbuttons(
            ax=ax_checkbuttons,
            labels=[f"Term {i}" for i in new_visible_range],
            states=[all_status[i] for i in new_visible_range],
            colors=[term_colors[i] for i in new_visible_range],
        )
        checkbuttons.on_clicked(on_checkbutton_clicked)
        current_state["visible_range"] = new_visible_range
        current_state["selected_terms"] = tuple(np.flatnonzero(all_status))
        update_plot()

    def on_checkbutton_clicked(label):
        """Handle the click event of check buttons and update the plot."""
        term_idx = int(label.split()[1])
        all_status[term_idx] = not all_status[term_idx]
        current_state["selected_terms"] = tuple(np.flatnonzero(all_status))
        update_plot()

    # callbacks
    if term_slider:
        term_slider.on_changed(update_terms)

    checkbuttons.on_clicked(on_checkbutton_clicked)

    if mode_slider:
        mode_slider.on_changed(
            lambda val: _update_modes(mode_slider, current_state, nrows, update_plot)
        )

    plot_type_radio.on_clicked(
        lambda label: _update_plot_type(plot_type_radio, current_state, update_plot)
    )

    fix_checkbutton.on_clicked(
        lambda label: _toggle_fix_y_axes(fix_checkbutton, current_state, update_plot)
    )

    update_plot()
    figure.align_labels()
    plt.show()
    axes = [[axis] for axis in axes[0]]
    return figure, axes


# --- Widget creation helper functions ---
def _create_slider(
    rect: tuple[float, float, float, float],
    label: str,
    valmin: float,
    valmax: float,
    valinit: float,
    valstep: float,
    orientation: Literal["horizontal", "vertical"],
    invert: bool,
    axis: Literal["x", "y"],
    ticks: Sequence[float] | None = None,
    tick_params: dict | None = None,
    frameon: bool = False,
) -> Slider:
    """Create and configure a slider widget.

    Parameters
    ----------
    rect : tuple[float, float, float, float]
        Axes position rectangle in ``(left, bottom, width, height)`` format normalized
        to figure coordinates (0-1 range).
    label : str
        Slider label.
    valmin : float
        Minimum slider value.
    valmax : float
        Maximum slider value.
    valinit : float
        Initial slider position.
    valstep : float
        Step size for the slider.
    orientation : {"horizontal", "vertical"}
        Orientation of the slider.
    invert : bool
        If True, invert the slider's axis.
    axis : {"x", "y"}
        Axis for tick configuration.
        - "x" for horizontal sliders (configures x-axis)
        - "y" for vertical sliders (configures y-axis)
    ticks : Sequence[float], optional
        Custom tick positions along the slider axis. When specified:
        - For horizontal: Sets x-ticks and hides labels
        - For vertical: Sets y-ticks and hides labels
        If None, ticks are auto-generated based on `valstep`.
    tick_params : dict, optional
        Additional keyword arguments for tick configuration.
    frameon : bool, default = False
        If True, the slider frame (axes border) are visible.

    Returns
    -------
    slider : matplotlib.widgets.Slider
        The created slider widget.
    """
    ax_slider = plt.axes(rect, frameon=frameon)
    slider = Slider(
        ax_slider,
        label,
        valmin,
        valmax,
        valinit=valinit,
        valstep=valstep,
        orientation=orientation,
    )
    if invert:
        slider.ax.invert_yaxis()
    slider.valtext.set_visible(False)
    # Add the relevant axis artist so that ticks can be set directly.
    if axis == "x":
        slider.ax.add_artist(slider.ax.xaxis)
    elif axis == "y":
        slider.ax.add_artist(slider.ax.yaxis)
    if ticks is not None:
        if axis == "y" and orientation == "vertical":
            slider.ax.set_yticks(ticks)
            slider.ax.set_yticklabels([])
        elif axis == "x" and orientation == "horizontal":
            slider.ax.set_xticks(ticks)
            slider.ax.set_xticklabels([])
    if tick_params is None:
        tick_params = {}
    slider.ax.tick_params(axis=axis, direction="in", length=5, **tick_params)
    return slider


def _create_fix_ylim_checkbox(
    rect: tuple[float, float, float, float], frameon: bool = False
) -> CheckButtons:
    """Create the 'Fix y axes' check button widget."""
    ax_checkbox = plt.axes(rect, frameon=frameon)
    checkbox = CheckButtons(ax_checkbox, ["Fix y axes"], [False])
    return checkbox


def _create_plot_type_radio(
    rect: tuple[float, float, float, float], frameon: bool = False
) -> RadioButtons:
    """Create the plot type radio buttons widget."""
    plot_type_names = [pt.name for pt in PlotType]
    ax_radio = plt.axes(rect, frameon=frameon)
    radio = RadioButtons(ax_radio, plot_type_names, active=0)

    return radio


def _create_checkbuttons(
    ax: Axes,
    labels: Sequence[str],
    states: Sequence[bool],
    colors: Sequence[ColorType],
) -> CheckButtons:
    """Create a check buttons widget for term selection."""
    checkbuttons = CheckButtons(ax, labels, states, label_props={"color": list(colors)})
    return checkbuttons


# --- Common callback handlers ---
def _update_modes(slider: Slider, state: dict, nrows: int, update_plot: Callable):
    """Update displayed modes from the slider position and refresh the plot."""
    mode_i = int(slider.val) if slider else 0
    new_modes = tuple(range(mode_i, mode_i + nrows))
    if new_modes != state["modes"]:
        state["modes"] = new_modes
        update_plot()


def _update_plot_type(radio: RadioButtons, state: dict, update_plot: Callable):
    """Update the plot type based on radio button selection and refresh the plot."""
    new_plot_type = PlotType[radio.value_selected]
    if new_plot_type != state["plot_type"]:
        state["plot_type"] = new_plot_type
        update_plot()


def _toggle_fix_y_axes(checkbox: CheckButtons, state: dict, update_plot: Callable):
    """Toggle y-axis scaling and refresh the plot."""
    state["fix_ylim"] = checkbox.get_status()[0]
    update_plot()


class PlotType(Enum):
    """Types of error plots."""

    scatter = "scatter"
    bar = "bar"
    line = "plot"

    def __call__(
        self,
        axis: Axes,
        x: VectorType,
        y: VectorType,
        color: ColorType | None = None,
    ) -> None:
        getattr(axis, self.value)(x, y, color=color)


def draw_figure(
    T: PolyadicTensor,
    axes: Sequence[Sequence[Axes]],
    modes: Sequence[int],
    terms: Sequence[int],
    fix_ylim: bool,
    plot_type: PlotType,
    term_colors: list[ColorType] | None = None,
    combine: bool = False,
) -> None:
    """Draw factor vectors of a polyadic tensor for specified modes and terms.

    Parameters
    ----------
    T : PolyadicTensor
        The tensor whose rank-1 terms are to be plotted.
    axes : Sequence[Sequence[Axes]]
        A 2D sequence of :class:`matplotlib.axes.Axes`, representing subplots in a
        grid. ``axes[row][col]`` accesses the subplot at the given row and column.
    modes : Sequence[int]
        The sequence of mode indices to be plotted.
    terms : Sequence[int]
        The sequence of term indices whose factor vectors are to be plotted.
    fix_ylim : bool
        If True, the y-axis limits are fixed for the plot.
    plot_type : PlotType
        The type of plot to be drawn.
    term_colors : list[ColorType], optional
        List of colors for plotting the given rank-1 terms. Each entry can be any valid
        Matplotlib color specification (see :mod:`matplotlib.colors`). If None, the
        default Matplotlib colors are used.
    combine : bool, default = False
        If False, term labels are shown as titles in the corresponding axes.

    See Also
    --------
    matplotlib.pyplot
    """
    data = [T.term(tuple(terms)).factors[mode] for mode in modes]

    for axis in it.chain.from_iterable(axes):
        axis.cla()
    if len(axes) == 1 and len(modes) > 1:
        axes = [[axis] for axis in axes[0]]
    for row, factor in zip(axes, data):
        for axis, column, term in zip(it.cycle(row), factor.T, terms):
            color = term_colors[term] if term_colors else None
            plot_type(axis, np.arange(len(column)), column, color=color)

    mode_labels = [f"Mode {j}" for j in modes]
    for row, label in zip(axes, mode_labels):
        row[0].set_ylabel(label, fontsize=10)

    if not combine:
        term_labels = [f"Term {i}" for i in terms]
        for axis, label in zip(axes[0], term_labels):
            axis.set_title(label, fontsize=10)

    if fix_ylim:
        ylims = [
            (np.nanmin(T.factors[mode]), np.nanmax(T.factors[mode])) for mode in modes
        ]
        for row, ylim in zip(axes, ylims):
            for axis in row:
                axis.set_ylim(ylim)


def _add_inset(figure: Figure, xlabel="index", ylabel="value") -> None:
    """Add an inset with arrows to a given figure."""
    inset = figure.add_axes((0.05, 0.1, 0.1, 0.1), frameon=False)
    inset.annotate("", xy=(1, 0), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=1))
    inset.annotate("", xy=(0, 1), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=1))
    inset.set_xlabel(xlabel)
    inset.set_ylabel(ylabel)
    inset.set_xticks([])
    inset.set_yticks([])

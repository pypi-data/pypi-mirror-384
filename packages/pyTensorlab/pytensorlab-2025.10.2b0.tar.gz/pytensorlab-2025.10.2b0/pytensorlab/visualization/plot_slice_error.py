"""Plot the slice-wise errors."""

from enum import Enum

import numpy as np

from .configure_matplotlib import configure_matplotlib_backend

configure_matplotlib_backend()

from collections.abc import Sequence
from typing import Literal

from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib.typing import ColorType
from matplotlib.widgets import RadioButtons, Slider

from pytensorlab.datatypes import (
    HankelTensor,
    Tensor,  # noqa: F401 # sphinx
    frob,
    residual,
)
from pytensorlab.typing import PositiveInt, TensorType, VectorType


def plot_slice_error(
    target: TensorType, approx: TensorType, max_axes: PositiveInt = 3
) -> tuple[Figure, list[Axes]]:
    """Plot slice-wise errors between a target tensor and its approximation.

    Plot the absolute or relative errors between the slices or subtensors of order
    ``target.ndim - 1`` of the `target` and its approximation `approx`.

    Parameters
    ----------
    target : TensorType
        Target tensor.
    approx : TensorType
        Approximating tensor.
    max_axes : PositiveInt, default = 3
        Maximum number of axes to display.

    Returns
    -------
    figure : matplotlib.figure.Figure
        Figure containing the plot.
    plot_axes : list[matplotlib.axes.Axes]
        List of :class:`matplotlib.axes.Axes`, representing subplots. ``plot_axes[i]``
        corresponds to the plot for a specific axes or row ``i``.

    Raises
    ------
    ValueError
        If `target` and `approx` have a different order (number of axes).
    ValueError
        If `target` and `approx` have a different shape.

    Examples
    --------
    >>> import pytensorlab as tl
    >>> shape = (10, 12, 15)
    >>> target = tl.get_rng(31415).standard_normal(shape)
    >>> approx = tl.noisy(target, snr=30) # noisy version of target
    >>> tl.plot_slice_error(target, approx)
    """
    if target.ndim != approx.ndim:
        raise ValueError(
            f"the target tensor and the approximate tensor have a different order: "
            f"{target.ndim} != {approx.ndim}"
        )
    if target.shape != approx.shape:
        raise ValueError(
            f"shape of the target tensor does not match shape of the approximate "
            f"tensor: {target.shape} != {approx.shape}"
        )
    errors, relative_errors = slicewise_errors(target, approx)
    nrows = min(target.ndim, max_axes)
    figure, axes_array = plt.subplots(nrows, ncols=1)
    axes_array = np.atleast_1d(axes_array)
    plot_axes: list[Axes] = axes_array.tolist()
    figure.subplots_adjust(
        left=0.2, right=0.85, top=0.85, bottom=0.22, wspace=0.4, hspace=0.5
    )
    figure.suptitle("Slice-wise error")
    _add_inset(figure, "Slice number", "Error")

    mode_slider = None
    if target.ndim > max_axes:
        mode_slider = _create_slider(
            rect=(0.90, 0.25, 0.025, 0.6),
            label="Modes",
            valmin=0,
            valmax=target.ndim - nrows,
            valinit=0,
            valstep=1,
            orientation="vertical",
            invert=True,
            axis="y",
            ticks=range(target.ndim - nrows + 1),
            tick_params={"left": False, "right": True},
            frameon=False,
        )

    num_types = len(PlotType)
    height_plot_type = num_types * 0.035  # Height per plot type entry
    bottom_plot_type = 1 - height_plot_type
    plot_type_radio = _create_plot_type_radio(
        rect=(0.005, bottom_plot_type, 0.11, height_plot_type)
    )

    ax_radio_error = plt.axes((0.86, 0.92, 0.13, 0.08), frameon=False)
    error_type_radio = RadioButtons(ax_radio_error, ["absolute", "relative"], active=0)

    def callback(_=None):
        """Update the plot based on a GUI event."""
        mode_i = int(mode_slider.val) if mode_slider else 0
        modes = tuple(range(mode_i, mode_i + nrows))
        error_type = error_type_radio.value_selected
        if error_type == "absolute":
            selected_errors = [errors[mode] for mode in modes]
        else:
            selected_errors = [relative_errors[mode] for mode in modes]
        plot_type = PlotType[plot_type_radio.value_selected]
        draw_figure(selected_errors, plot_axes, modes, plot_type)
        plt.pause(0.001)

    plot_type_radio.on_clicked(callback)
    error_type_radio.on_clicked(callback)
    if mode_slider:
        mode_slider.on_changed(callback)

    callback()

    figure.align_labels()
    plt.show()
    return figure, plot_axes


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


def _create_plot_type_radio(
    rect: tuple[float, float, float, float], frameon: bool = False
) -> RadioButtons:
    """Create the plot type radio buttons widget."""
    plot_type_names = [pt.name for pt in PlotType]
    ax_radio = plt.axes(rect, frameon=frameon)
    radio = RadioButtons(ax_radio, plot_type_names, active=0)

    return radio


class PlotType(Enum):
    """Types of error plots."""

    scatter = "scatter"
    bar = "bar"
    line = "plot"

    def __call__(
        self,
        plot_axis: Axes,
        x: VectorType,
        y: VectorType,
        color: ColorType | None = None,
    ) -> None:
        getattr(plot_axis, self.value)(x, y, color=color)


def draw_figure(
    errors: Sequence[VectorType],
    plot_axes: Sequence[Axes],
    axes: Sequence[int],
    plot_type: PlotType,
) -> None:
    """Draw error plots for the specified modes.

    Parameters
    ----------
    errors : Sequence[VectorType]
        Vector of absolute or relative errors for each of the specified `axes` of the
        tensor.
    plot_axes : Sequence[matplotlib.axes.Axes]
        Axes of subplots in which `errors` for `axes` are plotted.
    axes : Sequence[int]
        Axes of the tensor to be plotted.
    plot_type : PlotType
        The type of plot to be drawn.

    See Also
    --------
    matplotlib.pyplot

    Notes
    -----
    The lengths of `errors`, `plot_axes`, and `axes` must be equal.
    """
    mode_labels = [f"Mode {j}" for j in axes]
    for axis, label, err in zip(plot_axes, mode_labels, errors):
        axis.cla()
        plot_type(axis, np.arange(len(err)), err)
        axis.set_ylabel(label, fontsize=10)

        axis.xaxis.set_major_locator(MaxNLocator(integer=True))


def slicewise_errors(
    target: TensorType, approx: TensorType
) -> tuple[Sequence[VectorType], Sequence[VectorType]]:
    """Compute the errors between the slices of two tensors.

    Computes the relative and (residual) errors between the slices or order
    ``target.ndim - 1`` of `target` and `approx` for each axis.

    Parameters
    ----------
    target : TensorType
        Target tensor.
    approx : TensorType
        Approximating tensor.

    Returns
    -------
    absolute_errors : Sequence[VectorType]
        The ``target.ndim`` Frobenius norm errors computed each slice along each axis.
    relative_errors : Sequence[VectorType]
        The ``target.ndim`` Frobenius norm relative errors computed each slice along
        each axis.

    Raises
    ------
    ValueError
        If `target` and `approx` have a different order (number of axes).
    ValueError
        If `target` and `approx` have a different shape.
    """
    if target.ndim != approx.ndim:
        raise ValueError(
            f"target and approximation tensor have a different order: "
            f"{target.ndim} != {approx.ndim}"
        )
    if target.shape != approx.shape:
        raise ValueError(
            f"shape of target does not match shape of approximation: "
            f"{target.shape} != {approx.shape}"
        )
    if isinstance(target, HankelTensor):
        target = np.array(target)

    norms = _frobenius_norm_slices(target)
    Tresidual = residual(target, approx)
    errors = _frobenius_norm_slices(Tresidual)

    relative_errors = []
    for mode_errors, mode_norms in zip(errors, norms):
        mode_relative_errors = np.array(
            [
                error / norm if norm != 0 else 0
                for error, norm in zip(mode_errors, mode_norms)
            ]
        )
        relative_errors.append(mode_relative_errors)

    return errors, relative_errors


def _frobenius_norm_slices(T: TensorType) -> Sequence[VectorType]:
    """Compute the slice-wise norms.

    Computes the Frobenius norm of the slices of order ``T.ndim - 1`` along each axis
    of `T`.

    Parameters
    ----------
    T : TensorType
        Tensor of which the slice norms are computed.

    Returns
    -------
    norms : Sequence[VectorType]
        Frobenius norms of the slices along each axis.
    """

    def slice_norm(T, axis):
        order = (axis,) + tuple(i for i in range(T.ndim) if i != axis)
        return [frob(s) for s in T.transpose(order)]

    return [np.array(slice_norm(T, axis)) for axis in range(T.ndim)]


def _add_inset(figure: Figure, xlabel="index", ylabel="value") -> None:
    """Add an inset with arrows to a given figure."""
    inset = figure.add_axes((0.05, 0.1, 0.1, 0.1), frameon=False)
    inset.annotate("", xy=(1, 0), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=1))
    inset.annotate("", xy=(0, 1), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=1))
    inset.set_xlabel(xlabel)
    inset.set_ylabel(ylabel)
    inset.set_xticks([])
    inset.set_yticks([])

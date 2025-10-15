"""Utility functions for visualization tools."""

from math import floor
from typing import Any

from pytensorlab.typing import Shape


def _compute_rescaled_axes(
    shape: Shape, scale_axes: bool, min_axis_size: float
) -> tuple[tuple[float, ...], Shape]:
    if scale_axes:
        min_axis_size = round(min_axis_size * max(shape))
        axes_scale = tuple(1 if s > min_axis_size else min_axis_size / s for s in shape)
        rescaled_shape = tuple(s if s > min_axis_size else min_axis_size for s in shape)
        return axes_scale, rescaled_shape
    else:
        return (1, 1, 1), shape


def _set_rescaled_axes_ticks(
    shape: Shape, axes_scale: tuple[float, ...], max_nb_ticks: int = 5
) -> dict[str, Any]:
    axes_spec = {}
    for a, label in zip(range(3), ("x", "y", "z")):
        if axes_scale[a] != 1:
            step = max(floor(shape[a] / max_nb_ticks), 1)
            tick = [(i * axes_scale[a], i) for i in range(0, shape[a], step)]
            axes_spec[label + "_values_and_labels"] = tick
    return axes_spec

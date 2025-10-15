"""Slice plot of a third-order tensor."""

import functools
import itertools
import warnings
from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import TYPE_CHECKING, Any, cast

import numpy as np

if TYPE_CHECKING:
    import vedo
else:
    import importlib

    from ..util._lazy_loader import LazyLoader

    def _set_settings(_):
        importlib.import_module(".visualization._vedo_settings", "pytensorlab")

    vedo = LazyLoader("vedo", callback=_set_settings)

from pytensorlab.datatypes import (
    Tensor,  # noqa: F401 # sphinx
    getitem,
)
from pytensorlab.typing import ArrayType, BasicIndex, Shape, TensorType

from .utils import _compute_rescaled_axes, _set_rescaled_axes_ticks


class SliceMesh(ABC):
    """Helper class for creating vedo meshes based on tensor slices."""

    def __init__(
        self,
        T: TensorType,
        mode: int,
        Tmin: float,
        Tmax: float,
        axes_scale: tuple[float, ...],
    ):
        self.T = T
        self.mode: int = mode if mode >= 0 else mode + T.ndim
        if not 0 <= self.mode < 3:
            raise ValueError(
                f"out-of-bounds value for mode; expected -3 <= mode < 3, but got {mode}"
            )
        self.Tmin = Tmin
        self.Tmax = Tmax
        if not hasattr(self, "shape"):
            self.shape: Shape = T.shape
        self.axes_scale = axes_scale
        self.create_mesh(axes_scale)

    def create_mesh(self, axes_scale: tuple[float, ...]) -> None:
        """Create vedo mesh."""
        # construct faces
        dims = cast(
            tuple[int, int],
            tuple(s for n, s in enumerate(self.shape) if n != self.mode),
        )
        faces = list(_faces(dims))

        # construct vertices
        ranges = [range(s + 1) for s in self.shape]
        ranges[self.mode] = range(1)
        verts = np.asarray(list(itertools.product(*ranges)), dtype=np.float32)
        verts = np.array(axes_scale, ndmin=2) * verts
        self.mesh: vedo.Mesh = vedo.Mesh((verts, faces))

    def values(self, pos: int) -> ArrayType:
        """Extract values of slice at given position."""
        val = np.array(np.take(self.T, pos, axis=self.mode)).ravel()
        if self.Tmin == self.Tmax:
            val[:] = self.Tmin
        return val

    @abstractmethod
    def update_color(self, pos: int) -> None:
        """Update color of vertices or faces according to the selected slice values."""
        ...

    def _update_color(self, pos: int, cmap: str = "jet", **kwargs) -> None:
        """Update color of vertices or faces.

        The color is selected according to the selected slice values.
        """
        self.mesh.cmap(cmap, self.values(pos), **kwargs)

    @abstractmethod
    def update_position(self, pos: int) -> None:
        """Change position of mesh according to the selected slices values."""
        ...

    def _update_position(self, values: float | ArrayType) -> None:
        """Update the position of vertices."""
        verts = self.mesh.vertices
        verts[:, self.mode] = values * self.axes_scale[self.mode]
        self.mesh.vertices = verts


class ImageMesh(SliceMesh):
    """Flat mesh in which faces correspond to slice values."""

    def __init__(self, T: TensorType, *args: Any):
        super().__init__(T, *args)

    def update_color(self, pos: int, **kwargs: Any) -> None:
        values = self.values(pos)
        vmax = self.Tmax if self.Tmax > self.Tmin else self.Tmax + 1
        colors = np.ones((len(values), 4)) * 255
        colors[:, 0:3] = (
            vedo.color_map(values, name="jet", vmin=self.Tmin, vmax=vmax) * 255
        )
        colors[np.isnan(values), 3] = 0
        self.mesh.cellcolors = colors

    def update_position(self, pos: int) -> None:
        self._update_position(pos + 0.5)


class SurfaceMesh(SliceMesh):
    """Surface plot style mesh in which vertices correspond to slice values."""

    def __init__(self, T: TensorType, *args: Any):
        self.shape: Shape = tuple(s - 1 for s in T.shape)
        super().__init__(T, *args)

    def create_mesh(self, axes_scale: tuple[float, ...]) -> None:
        super().create_mesh(axes_scale)
        self.mesh.vertices += 0.5 * np.array(axes_scale, ndmin=2)

    def values(self, pos: int) -> ArrayType:
        if self.Tmin == self.Tmax:
            return super().values(pos) - self.Tmin - 1
        return 2 * (super().values(pos) - self.Tmin) / (self.Tmax - self.Tmin) - 1

    def update_color(self, pos: int, **kwargs: Any) -> None:
        # Surface plotting with nan values only works for sufficient known values
        super()._update_color(pos, vmin=-1, vmax=1, on="points")

    def update_position(self, pos: int) -> None:
        values = pos + 0.5 + self.values(pos)
        if self.Tmin == self.Tmax:
            values += 1  # center slice plot
        self._update_position(values)


def _faces(shape: tuple[int, int]) -> Generator[tuple[int, int, int, int], None, None]:
    """Generate all rectangles in an (I+1)x(J+1) grid."""
    i = 0
    for _ in range(shape[0]):
        for _ in range(shape[1]):
            yield (i, i + 1, i + shape[1] + 2, i + shape[1] + 1)
            i += 1
        i += 1


class SliceBoundingBox:
    """Helper class for creating vedo meshes of bounding boxes for slices.

    Adds a gray opaque rectangle around slice meshes for increased visibility,
    especially when many tensor entries are missing.
    """

    def __init__(
        self,
        mode: int,
        axes_scale: tuple[float, ...],
        rescaled_shape: Shape,
    ):
        self.mode: int = mode if mode >= 0 else mode + len(rescaled_shape)
        self.axes_scale = axes_scale
        self.rescaled_shape = rescaled_shape
        self.create_mesh()

    def create_mesh(self) -> None:
        """Create vedo mesh."""
        position = list(s / 2 for s in self.rescaled_shape)
        dimensions = list(self.rescaled_shape)
        dimensions[self.mode] = 0
        sl_box = vedo.Box(position, size=dimensions, alpha=0)
        sl_mesh = cast(vedo.Mesh, sl_box.boundaries())
        sl_mesh.color("gray")  # type:ignore  # vedo does accept a string
        sl_mesh.alpha(0.1)
        self.mesh: vedo.Mesh = sl_mesh

    def update_position(self, pos: int) -> None:
        """Change position of mesh according to the selected slices values."""
        verts = self.mesh.vertices
        verts[:, self.mode] = (pos + 0.5) * self.axes_scale[self.mode]
        self.mesh.vertices = verts


def _plotmesh(
    T: TensorType,
    MeshType: type[SliceMesh],
    indices: tuple[int, int, int] = (0, 0, 0),
    interactive: bool = True,
    scale_axes: bool = True,
    min_axis_size: float = 0.3,
) -> None:
    """Show a slice plot of a third-order tensor.

    Visualizes the third-order tensor T by drawing its mode-0, -1 and -2 slices using
    indices ``indices[0]``, ``indices[1]``, and ``indices[2]`` respectively.

    Parameters
    ----------
    T : TensorType
        Third-order tensor to be plotted.
    MeshType : Type[SliceMesh]
        Type of the mesh to use. Must be a subclass of SliceMesh.
    indices : tuple[int, int, int], default = (0, 0, 0)
        Indices of the slices to be plotted.
    interactive : bool, default = True
        If True, script execution is paused to allow interaction with the figure. If
        False, the plot is closed immediately and script execution is continued.
    scale_axes : bool, default = True
        If the size of some axes of `T` is smaller than ``min_axis_size *
        max(T.shape)``, rescale these axes such that their size equals ``min_axis_size
        * max(T.shape)``.
    min_axis_size : float, default = 0.3
        The minimal size of an axis, relative to ``max(T.shape)``, if `scale_axes` is
        True.

    Raises
    ------
    ValueError
        If `T` is not a third-order tensor.
    ValueError
        If all dimensions of `T` are equal to one.
    ValueError
        If `indices` is larger than ``T.shape[n]``.

    Warns
    -----
    Warning
        If all tensor entries are equal.

    See Also
    --------
    .slice3, .surf3
    """
    if not hasattr(T, "shape"):
        T = np.asarray(T)
    T = cast(TensorType, T)

    # check arguments
    if T.ndim > 3:
        raise ValueError(f"tensor T should be of order 3 instead of order {T.ndim}")
    elif T.ndim < 3:
        key = cast(tuple[BasicIndex], (...,) + (np.newaxis,) * (3 - T.ndim))
        T = cast(TensorType, getitem(T, key))

    if T.size == 1:
        raise ValueError("at least one tensor dimension should be larger than one")

    if not all(-s <= i < s for i, s in zip(indices, T.shape)):
        raise ValueError(
            "-T.shape[n] <= ind[n] < T.shape[n] does not hold for every index in ind"
        )
    ind = cast(
        tuple[int, int, int],
        tuple(i if i >= 0 else i + s for i, s in zip(indices, T.shape)),
    )

    # initialize plotter
    vp = vedo.Plotter(axes=0)

    # Compute minimum and maximum entry once.
    Tmin = np.nanmin(T)
    Tmax = np.nanmax(T)

    # Rescale axes
    axes_scale, rescaled_shape = _compute_rescaled_axes(
        T.shape, scale_axes, min_axis_size
    )

    # construct meshes
    if Tmax == Tmin:
        warnings.warn("all tensor entries are equal")

    meshes: list[SliceMesh] = list()
    slice_boxes: list[SliceBoundingBox] = list()
    for n, pos in enumerate(ind):
        mesh = MeshType(T, n, Tmin, Tmax, axes_scale)
        mesh.update_color(pos)
        mesh.update_position(pos)
        meshes.append(mesh)
        slice_box = SliceBoundingBox(n, axes_scale, rescaled_shape)
        slice_box.update_position(pos)
        slice_boxes.append(slice_box)

    # add meshes to plotter
    vp.add([mesh.mesh for mesh in meshes])
    vp.add([slice_box.mesh for slice_box in slice_boxes])

    # add circumscribed cube to plotter
    tens = vedo.Box(
        pos=tuple(s / 2 for s in rescaled_shape),
        size=rescaled_shape,
        alpha=0,
        c="black",
    )
    tens_bounds = cast(vedo.Mesh, tens.boundaries())
    tens_bounds.color("black")  # type:ignore  # vedo does accept a string
    vp.add(tens_bounds)

    # add sliders
    def index_slider(
        widget: vedo.Slider2D, _, mesh: SliceMesh, slice_box: SliceBoundingBox
    ):
        pos = int(round(widget.GetRepresentation().GetValue()))  # type:ignore
        mesh.update_position(pos)
        mesh.update_color(pos)
        slice_box.update_position(pos)

    pos1 = ((0.2, 0.05), (0.45, 0.05), (0.7, 0.05))
    pos2 = ((0.35, 0.05), (0.6, 0.05), (0.85, 0.05))
    for n, (mesh, slice_box, pos, p1, p2, s) in enumerate(
        zip(meshes, slice_boxes, ind, pos1, pos2, T.shape)
    ):
        if s <= 1:
            continue
        vp.add_slider(
            functools.partial(index_slider, mesh=mesh, slice_box=slice_box),
            pos=[p1, p2],  # type:ignore  # a list of coordinates is accepted
            value=pos,
            xmin=0,
            xmax=s - 1,
            title=f"mode {n}",
            title_size=0.75,  # type:ignore  # float is accepted
            show_value=True,
            c="black",
        )

    barmesh = vedo.Plane(alpha=0)
    barmesh.cmap("jet", [Tmax, Tmin], on="cells", vmin=Tmin, vmax=Tmax)
    barmesh.add_scalarbar(pos=(), font_size=16)
    vp.add(barmesh)

    axes_spec = {
        "xtitle": "axis 0",
        "ytitle": "axis 1",
        "ztitle": "axis 2",
        "xtitle_size": 0.04,
        "ytitle_size": 0.04,
        "ztitle_size": 0.04,
        "xygrid": False,
        "xrange": (-0.5, rescaled_shape[0]),
        "yrange": (-0.5, rescaled_shape[1]),
        "zrange": (-0.5, rescaled_shape[2]),
    }

    # Set ticks of rescaled axes
    if scale_axes:
        axes_spec.update(_set_rescaled_axes_ticks(T.shape, axes_scale))

    vp.axes = axes_spec

    # show plotter
    vp.show(interactive=interactive, azimuth=45, elevation=30)

    # close plotter
    # vp.close()


def surf3(
    T: TensorType,
    ind: tuple[int, int, int] = (0, 0, 0),
    interactive: bool = True,
    scale_axes: bool = True,
    min_axis_size: float = 0.3,
) -> None:
    """Show a surface plot of a third-order tensor.

    This function is the same as slice3 with surface set to True.

    Parameters
    ----------
    T : TensorType
        Third-order tensor to be plotted.
    ind : tuple[int, int, int], default = (0, 0, 0)
        Indices of the slices to be plotted.
    interactive : bool, default = True
        If True, script execution is paused to allow interaction with the figure. If
        False, the plot is closed immediately and script execution is continued.
    scale_axes : bool, default = True
        If the size of some axes of `T` is smaller than ``min_axis_size *
        max(T.shape)``, rescale these axes such that their size equals ``min_axis_size
        * max(T.shape)``.
    min_axis_size : float, default = 0.3
        The minimal size of an axis, relative to ``max(T.shape)``, if `scale_axes` is
        True.

    Raises
    ------
    ValueError
        If `T` is not a third-order tensor.
    ValueError
        If all dimensions of `T` are equal to one.
    ValueError
        If `ind` is larger than ``T.shape[n]``.

    Warns
    -----
    Warning
        If all tensor entries are equal.

    See Also
    --------
    .slice3, .voxel3

    Examples
    --------
    >>> import pytensorlab as tl
    >>> shape = (10, 9, 8)
    >>> T = tl.get_rng(31415).standard_normal(shape)
    >>> tl.surf3(T)
    """
    if T.ndim != 3:
        raise ValueError("tensor must have order 3")
    if any(s == 1 for s in T.shape):
        raise ValueError("each axis must have a dimension larger than 1")
    _plotmesh(T, SurfaceMesh, ind, interactive, scale_axes, min_axis_size)


def slice3(
    T: TensorType,
    ind: tuple[int, int, int] = (0, 0, 0),
    interactive: bool = True,
    scale_axes: bool = True,
    min_axis_size: float = 0.3,
) -> None:
    """Show a slice plot of a third-order tensor.

    Visualizes the third-order tensor T by drawing its mode-0, -1 and -2 slices using
    indices ``ind[0]``, ``ind[1]``, and ``ind[2]`` respectively.

    Parameters
    ----------
    T : TensorType
        Third-order tensor to be plotted.
    ind : tuple[int, int, int], default = (0, 0, 0)
        Indices of the slices to be plotted.
    interactive : bool, default = True
        If True, script execution is paused to allow interaction with the figure. If
        False, the plot is closed immediately and script execution is continued.
    scale_axes : bool, default = True
        If the size of some axes of `T` is smaller than ``min_axis_size *
        max(T.shape)``, rescale these axes such that their size equals ``min_axis_size
        * max(T.shape)``.
    min_axis_size : float, default = 0.3
        The minimal size of an axis, relative to ``max(T.shape)``, if `scale_axes` is
        True.

    Raises
    ------
    ValueError
        If `T` is not a third-order tensor.
    ValueError
        If all dimensions of `T` are equal to one.
    ValueError
        If `ind` is larger than ``T.shape[n]``.

    Warns
    -----
    Warning
        If all tensor entries are equal.

    See Also
    --------
    .surf3, .voxel3

    Examples
    --------
    >>> import pytensorlab as tl
    >>> shape = (10, 9, 8)
    >>> T = tl.get_rng(31415).standard_normal(shape)
    >>> tl.slice3(T)
    """
    _plotmesh(T, ImageMesh, ind, interactive, scale_axes, min_axis_size)

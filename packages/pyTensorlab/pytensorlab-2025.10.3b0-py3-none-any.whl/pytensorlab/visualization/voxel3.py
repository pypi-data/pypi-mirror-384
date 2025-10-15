"""Voxel plot of a third-order tensor."""

import itertools
import warnings
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, TypeAlias, cast

import numpy as np

if TYPE_CHECKING:
    import vedo

    MeshType: TypeAlias = vedo.Mesh
else:
    import importlib

    from ..util._lazy_loader import LazyLoader

    def _set_settings(_):
        importlib.import_module(".visualization._vedo_settings", "pytensorlab")

    vedo = LazyLoader("vedo", callback=_set_settings)
    MeshType: TypeAlias = type["vedo.Mesh"]

from pytensorlab.datatypes import Tensor  # noqa: F401 # sphinx
from pytensorlab.typing import ArrayType, Shape, TensorType

from .utils import _compute_rescaled_axes, _set_rescaled_axes_ticks


class SlicePair:
    """Helper class for creating pairs of vedo slice meshes flanking voxels."""

    def __init__(
        self,
        T: TensorType,
        mode: int,
        pos: int,
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
        self.pos: int = pos
        if not 0 <= self.pos < self.T.shape[self.mode]:
            raise ValueError(
                "out-of-bounds value for pos; "
                f"expected 0 <= mode < T.shape[mode], but got {pos}"
            )
        self.Tmin = Tmin
        self.Tmax = Tmax
        self.shape: Shape = T.shape
        self.axes_scale = axes_scale
        self.create_meshes()

    def create_meshes(self) -> None:
        """Create vedo meshes."""
        self.meshes: list[vedo.Mesh] = []

        # construct faces
        dims = cast(
            tuple[int, int],
            tuple(s for n, s in enumerate(self.shape) if n != self.mode),
        )
        faces, values = self._faces(dims)
        if len(faces) == 0:
            return

        # construct vertices
        ranges = [range(s + 1) for s in self.shape]
        ranges[self.mode] = range(self.pos, self.pos + 1)
        verts = np.asarray(list(itertools.product(*ranges)), dtype=np.float32)
        verts = np.array(self.axes_scale, ndmin=2) * verts
        mesh = vedo.Mesh((verts, faces))
        mesh.cmap(
            "jet",
            values,
            on="cells",
            vmin=self.Tmin,
            vmax=self.Tmax,
        )
        self.meshes.append(mesh)

        mesh = mesh.copy()
        verts[:, self.mode] += 1 * self.axes_scale[self.mode]
        mesh.vertices = verts
        self.meshes.append(mesh)

    def values(self) -> ArrayType:
        """Extract values of slice at given position."""
        val = np.array(np.take(self.T, self.pos, axis=self.mode)).ravel()
        if self.Tmin == self.Tmax:
            val[:] = self.Tmin
        return val

    def update_opacity(self, lut_opacity: ArrayType) -> None:
        for mesh in self.meshes:
            mesh.cmap(
                "jet",
                on="cells",
                alpha=lut_opacity,  # type:ignore  # list/ndarray accepted
                vmin=self.Tmin,
                vmax=self.Tmax,
            )

    def _faces(
        self,
        shape: tuple[int, int],
    ) -> tuple[list[tuple[int, int, int, int]], ArrayType]:
        """Generate all rectangles in an (I+1)x(J+1) grid."""
        faces = []
        values = []

        all_vals = self.values()
        counter = 0
        i = 0
        for _ in range(shape[0]):
            for _ in range(shape[1]):
                if not np.isnan(all_vals[counter]):
                    faces.append((i, i + 1, i + shape[1] + 2, i + shape[1] + 1))
                    values.append(all_vals[counter])
                counter += 1
                i += 1
            i += 1

        return faces, np.array(values)


def voxel3(
    T: TensorType,
    lower: None | float = None,
    upper: None | float = None,
    rolloff: float = 0.5,
    interactive: bool = True,
    scale_axes: bool = True,
    min_axis_size: float = 0.3,
) -> None:
    """Show a voxel plot of a third-order tensor.

    Each tensor entry is represented by a voxel. The transparency of these voxels
    is dependent on `lower` and `upper`. If ``lower < upper``, voxels with
    corresponding tensor entries that lie between the upper and lower bound are shown.
    If ``lower > upper``, voxels with corresponding tensor entries either greater than
    lower bound or less than upper bound are shown. Voxels in the visible range have
    opacities dictated by a raised-cosine-type gradient with roll-off factor `rolloff`.

    Parameters
    ----------
    T : TensorType
        Third-order tensor to be plotted.
    lower : float | None, default = None
        Lower bound for visible tensor entries. Voxels corresponding to tensor entries
        with value less than lower bound (and greater than upper bound) will be
        completely transparent. If specified, `lower`, must have a value between
        ``T.min()`` and ``T.max()``. If not given or None, `lower` is by default set to
        a value corresponding to ``(3 / 4) * T.min() + (1 / 4) * T.max()``.
    upper : float | None, default = None
        Upper bound for visible tensor entries. Voxels corresponding to tensor entries
        with value greater than upper bound (and less than lower bound) will be
        completely transparent. If specified, `upper`, must have a value between
        ``T.min()`` and ``T.max()``. If not given or None, `upper` is by default set to
        a value corresponding to ``(1 / 4) * T.min() + (3 / 4) * T.max()``.
    rolloff: float, default = 0.5
        Roll-off factor for the opacity gradient. The opacity gradient of voxels with
        corresponding values in the visible range is defined by a raised-cosine-type
        gradient with a roll-off factor between 0 and 1, where 0 corresponds to no
        gradient, and 1 to a smooth cosine shaped gradient.
    interactive : bool, default = True
        If True, script execution is paused to allow interaction with the figure. If
        False, the plot is closed immediately and script execution is continued.
    scale_axes : bool, default = True
        If the size of some axes of `T` is smaller than ``min_axis_size *
        max(T.shape)``, rescale these axes such that their size equals
        ``min_axis_size * max(T.shape)``.
    min_axis_size : float, default = 0.3
        The minimal size of an axis, relative to ``max(T.shape)``, if `scale_axes`
        is True.

    Raises
    ------
    ValueError
        If `T` is not a third-order tensor.

    See Also
    --------
    ~.slice3.slice3, ~.slice3.surf3

    Notes
    -----
    The voxel plot is achieved by plotting a number of faces/meshes along each
    of the three modes of the tensor. The number of faces is equal to the size
    of the corresponding tensor dimension times two. The faces are grouped in pairs,
    each flanking the voxels corresponding to one slice in the specified mode. Each
    face consists of colored transparent squares.

    Examples
    --------
    >>> import pytensorlab as tl
    >>> shape = (10, 9, 8)
    >>> T = tl.get_rng(31415).standard_normal(shape)
    >>> tl.voxel3(T)
    """
    T = np.asarray(T)

    if T.ndim > 3:
        raise ValueError(f"tensor T should be of order 3 instead of order {T.ndim}")
    elif T.ndim < 3:
        T = cast(ArrayType, T[(...,) + (np.newaxis,) * (3 - T.ndim)])

    # Rescale axes
    axes_scale, rescaled_shape = _compute_rescaled_axes(
        T.shape, scale_axes, min_axis_size
    )

    # Compute minimum and maximum entry once.
    Tmin = np.nanmin(T)
    Tmax = np.nanmax(T)

    # Avoids plot being invisible when min and max entry are the same.
    if Tmin == Tmax:
        Tmin -= 0.5
        Tmax += 0.5

    # Compute order of magnitude of largest absolute tensor value
    mag = np.floor(np.log10(np.max(np.abs([Tmin, Tmax]))))
    # Normalize minimal and maximal tensor values in (0, 10]
    Nmin = Tmin / 10**mag
    Nmax = Tmax / 10**mag

    # Check value of lower and normalize to _lower for internal use
    if lower is None:
        _lower: float = Nmin * 0.75 + Nmax * 0.25
    else:
        assert lower is not None
        _lower = lower / 10**mag

        if not Nmin <= _lower <= Nmax:
            warnings.warn(
                (
                    "lower should be in [T.min(),T.max()); "
                    "lower set to (3 / 4) * T.min() + (1 / 4) * T.max()"
                ),
                UserWarning,
            )
            _lower = Nmin * 0.75 + Nmax * 0.25

    # Check value of upper and normalize to _upper for internal use
    if upper is None:
        _upper: float = Nmin * 0.25 + Nmax * 0.75
    else:
        assert upper is not None
        _upper = upper / 10**mag

        if not Nmin <= _upper <= Nmax:
            warnings.warn(
                (
                    "upper should be in (T.min(),T.max()]; "
                    "upper set to (1 / 4) * T.min() + (3 / 4) * T.max()"
                ),
                UserWarning,
            )
            _upper = Tmin * 0.25 + Tmax * 0.75

    if not 0 <= rolloff <= 1:
        warnings.warn(
            "rolloff should be in [0, 1]; rolloff set to 0.5",
            UserWarning,
        )
        rolloff = 0.5

    # Compute period and cutoff for raised-cosine function once
    p = (1 + rolloff) / 2
    c = 1 - (1 - rolloff) / (1 + rolloff)

    def raised_cosine(x: ArrayType) -> ArrayType:
        if rolloff == 0:
            return np.ceil(x)

        y = (1 + np.cos(np.pi * p / rolloff * (1 - x - (1 - rolloff) / (2 * p)))) / 2
        y = np.minimum(1, y)
        y[x >= c] = 1
        return y

    def compute_opacity(vals: ArrayType) -> ArrayType:
        scaled_lower = (_lower - Nmin) / (Nmax - Nmin)
        scaled_upper = (_upper - Nmin) / (Nmax - Nmin)

        if abs(scaled_lower - scaled_upper) < 1e-15:
            alphas = np.zeros(vals.shape)

        elif _lower < _upper:
            mu = (scaled_upper + scaled_lower) / 2
            delta = (scaled_upper - scaled_lower) / 2
            alphas = np.maximum(0, delta - np.abs(vals - mu)) / delta

        else:
            alphas_lower = np.maximum(0, scaled_upper - vals) / scaled_upper
            alphas_upper = np.maximum(0, vals - scaled_lower) / (1 - scaled_lower)
            alphas = alphas_lower + alphas_upper

        return raised_cosine(alphas)

    # initialize plotter
    vp = vedo.Plotter()

    # Construct meshes
    meshes: list[SlicePair] = list()
    for n in range(3):
        for ind in range(T.shape[n]):
            mesh = SlicePair(T, n, ind, Tmin, Tmax, axes_scale)
            if len(mesh.meshes) > 0:
                meshes.append(mesh)
                vp.add([mesh for mesh in mesh.meshes])

    # Surrounding cube
    tens = vedo.Box(
        pos=tuple(s / 2 for s in rescaled_shape), size=rescaled_shape, alpha=0, c="b"
    )
    tens_bounds = tens.boundaries()
    tens_bounds.color("black")  # type:ignore  # string color accepted
    vp.add(tens_bounds)

    # Create plane mesh and colorbar
    color_meshes = []
    barmesh = vedo.Plane(alpha=0)
    barmesh.cmap("jet", [Tmin, Tmax], on="cells", vmin=Tmin, vmax=Tmax)
    color_meshes.append(barmesh)
    vp.add(barmesh)
    colorbar = vedo.ScalarBar(barmesh)
    color_meshes.append(colorbar)
    vp.add(colorbar)

    # set opacity for voxels and colorbar
    _update_meshes_opacity(meshes, color_meshes, compute_opacity, vp)

    def lower_slider(widget, _) -> None:
        nonlocal _lower
        _lower = widget.GetRepresentation().GetValue()
        _update_meshes_opacity(meshes, color_meshes, compute_opacity, vp)

    def upper_slider(widget, _) -> None:
        nonlocal _upper
        _upper = widget.GetRepresentation().GetValue()
        _update_meshes_opacity(meshes, color_meshes, compute_opacity, vp)

    lslider = vp.add_slider(
        lower_slider,
        xmin=Nmin - 1e-2 - 1e-4,
        xmax=Nmax + 1e-2 - 1e-4,
        pos=[
            (0.17, 0.148),
            (0.878, 0.148),
        ],  # type:ignore  # list of coordinates accepted
        value=_lower,
    )
    lslider.GetRepresentation().GetLabelProperty().SetJustificationToRight()

    rslider = vp.add_slider(
        upper_slider,
        xmin=Nmin - 1e-2 + 1e-4,
        xmax=Nmax + 1e-2 + 1e-4,
        pos=[
            (0.17, 0.067),
            (0.878, 0.067),
        ],  # type:ignore  # list of coordinates accepted
        value=_upper,
    )
    rslider.GetRepresentation().GetLabelProperty().SetJustificationToLeft()

    # Add order of magnitude, minimal and maximal slider values
    vp.add(
        vedo.Text2D(
            f"{10**mag:.0e} *",
            pos=(0.03, 0.125),  # type:ignore  # tuple of coordinates accepted
            s=1.1,
        )
    )
    vp.add(
        vedo.Text2D(
            f"{Tmin:.2e}",
            pos=(0.1, 0.05),  # type:ignore  # tuple of coordinates accepted
            s=0.9,
        )
    )
    vp.add(
        vedo.Text2D(
            f"{Tmax:.2e}",
            pos=(0.83, 0.05),  # type:ignore  # tuple of coordinates accepted
            s=0.9,
        )
    )

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

    cam_spec = {"pos": (4.5, 3.5, 40), "focal_point": (4.5, 3.5, 4.5)}

    # show plotter
    vp.show(axes=axes_spec, camera=cam_spec, interactive=interactive)

    # close plotter
    vp.close()


def _update_meshes_opacity(
    meshes: Sequence[SlicePair],
    color_meshes: list,
    compute_opacity: Callable[[ArrayType], ArrayType],
    vp: vedo.Plotter,
) -> None:
    """Update opacity of faces and generate colorbar.

    Updates the opacity of all faces of the plot and update the colorbar accordingly.

    Parameters
    ----------
    meshes : Sequence[vedo.Mesh]
        List of meshes that contains all faces of the voxel plot.
    compute_opacity : Callable[[ArrayType], ArrayType]
        Function that computes the opacity of a tensor entry given the relative
        value of that entry.
    vp : vedo.plotter.Plotter
        Plotter object of the vedo plot.
    """
    # Construct new opacity lookuptable and apply it to each mesh.
    lutsize_opacity = 256
    lut_opacity = compute_opacity(np.arange(lutsize_opacity) / (lutsize_opacity - 1))
    for mesh in meshes:
        mesh.update_opacity(lut_opacity)

    barmesh = color_meshes[0]
    barmesh.cmap(
        "jet",
        on="cells",
        alpha=lut_opacity,  # type:ignore  # list/ndarray accepted
    )
    colorbar = color_meshes[1]
    vp.remove(colorbar)
    new_colorbar = vedo.ScalarBar(
        barmesh,
        pos=[(0.17, 0.07), (0.88, 0.27)],
        nlabels=2,
        horizontal=True,
        font_size=-1,
        c="white",
    )
    color_meshes[1] = new_colorbar
    vp.add(new_colorbar)

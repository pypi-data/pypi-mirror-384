from __future__ import annotations
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.colors import BoundaryNorm, Normalize
from matplotlib.colorbar import Colorbar
from dataclasses import replace
from typing import Optional, Tuple
from allytools.units import LengthUnit
from plotter.parameters import PlotParams
from plotter.cmaps import resolve_cmap


class ScalarField2D:
    def __init__(self, data, params: Optional[PlotParams] = None, **param_overrides):
        base = params if params is not None else PlotParams()
        self.params = replace(base, **param_overrides) if param_overrides else base
        self.data = data
        self.v_min: Optional[float] = None
        self.v_max: Optional[float] = None

    """Standalone renderer: builds a Figure, draws, returns RGBA."""
    def render(self, *,
               annotate_xy: Optional[tuple[float, float]] = None,
               plot_label: Optional[str] = None,
               **overrides) -> np.ndarray:
        p = replace(self.params, **overrides)
        fig = plt.figure(figsize=p.size_in, dpi=p.dpi)
        ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
        self.draw(ax, annotate_xy=annotate_xy, plot_label=plot_label, with_colorbar=p.with_colorbar,params=p)
        canvas = FigureCanvas(fig)
        canvas.draw()
        rgba = np.asarray(canvas.buffer_rgba()).copy()
        plt.close(fig)
        return rgba

    """Inline renderer: draws into an existing Axes and returns AxesImage."""
    def render_into(self,ax,*,
                    norm=None,
                    annotate_xy: Optional[tuple[float, float]] = None,
                    plot_label: Optional[str] = None,
                    with_colorbar: bool = False,
                    **overrides):
        p = replace(self.params, **overrides)
        im, _ = self.draw(ax,
                          norm=norm,
                          annotate_xy=annotate_xy,
                          plot_label=plot_label,
                          with_colorbar=with_colorbar,
                          params=p)
        return im
    """Draw the image and decorates the axes."""
    def draw(self, ax, *, params: PlotParams,
             norm=None,
             annotate_xy: Optional[tuple[float, float]] = None,
             plot_label: Optional[str] = None,
             with_colorbar: bool = False) -> Tuple[plt.AxesImage, Optional[Colorbar]]:

        values = np.asarray(self.data.Values, dtype=float)
        cmap, norm = self._resolve_cmap_and_norm(params, values, norm)
        im = ax.imshow(values,
                       extent = self.data.extent,
                       origin="lower",
                       aspect="equal",
                       cmap=cmap,
                       norm=norm)
        cbar = None
        if with_colorbar:
            cbar = ax.figure.colorbar(im, ax=ax, pad=0.02)
            self._set_label(
                cbar, "set_label",
                params.value_label,
                getattr(self.data, "value_label", None)
            )
        self._set_label(ax, "set_xlabel", params.labelX, getattr(self.data, "XLabel", None))
        self._set_label(ax, "set_ylabel", params.labelY, getattr(self.data, "YLabel", None))
        if params.hide_ticks:
            ax.set_xticks([])
            ax.set_yticks([])
        if annotate_xy is not None:
            ax.set_xlabel(f"({annotate_xy[0]:.3g}, {annotate_xy[1]:.3g})", labelpad=2, fontsize=9)
        if plot_label is not None:
            ax.set_title(str(plot_label))
        else:
            self._set_label(ax, "set_title", params.plot_label, getattr(self.data, "description", None))
        if params.sensor_grid and (params.pixel_size is not None):
            pitch_um = float(params.pixel_size.to(LengthUnit.UM))
            if np.isfinite(pitch_um) and pitch_um > 0:
                xmin, xmax, ymin, ymax = self.data.extent
                def first_tick(a, step):
                    return math.ceil(a / step) * step
                x0 = first_tick(xmin, pitch_um)
                y0 = first_tick(ymin, pitch_um)
                xs = np.arange(x0, xmax + 1e-12, pitch_um)
                ys = np.arange(y0, ymax + 1e-12, pitch_um)
                ax.vlines(xs, ymin, ymax, colors=params.sensor_grid_color, linewidth=0.5, alpha=1.0, zorder=5)
                ax.hlines(ys, xmin, xmax, colors=params.sensor_grid_color, linewidth=0.5, alpha=1.0, zorder=5)
        return im, cbar

    def _resolve_cmap_and_norm(self, p: PlotParams, values: np.ndarray, norm):
        cmap = resolve_cmap(p.cmap)
        if norm is not None:
            return cmap, norm
        vmin, vmax = self._resolve_vmin_vmax(p, values)
        if p.use_levels:
            n_levels = max(2, int(p.n_levels))
            levels = np.linspace(vmin, vmax, n_levels)
            ncolors = getattr(cmap, "N", 256)
            norm = BoundaryNorm(levels, ncolors=ncolors, clip=True)
        else:
            norm = Normalize(vmin=vmin, vmax=vmax)
        return cmap, norm

    def _resolve_vmin_vmax(self, p: PlotParams, values: np.ndarray) -> tuple[float, float]:
        vmin = p.v_min if getattr(p, "v_min", None) is not None else self.v_min
        vmax = p.v_max if getattr(p, "v_max", None) is not None else self.v_max

        if vmin is None or vmax is None:
            finite = values[np.isfinite(values)]
            if finite.size:
                if vmin is None:
                    vmin = float(np.min(finite))
                if vmax is None:
                    vmax = float(np.max(finite))
            else:
                vmin, vmax = 0.0, 1.0

        if not np.isfinite(vmin) or not np.isfinite(vmax) or vmax <= vmin:
            vmin, vmax = 0.0, 1.0
        return vmin, vmax


    @staticmethod
    def _set_label(obj, method_name: str, preferred, fallback, default: str | None = None):
        # sanitize inputs
        pref = _coerce_label(preferred)
        fall = _coerce_label(fallback)
        defs = _coerce_label(default)
        label = pref or fall or defs
        if label is not None:
            getattr(obj, method_name)(label)

def _coerce_label(val):
    if val is None:
        return None
    s = str(val).strip()
    if s == "" or s.lower() == "none":
        return None
    return s

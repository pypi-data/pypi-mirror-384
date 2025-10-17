from typing import Optional
import numpy as np
import math
import matplotlib.pyplot as plt
from dataclasses import replace
from matplotlib.colors import BoundaryNorm, Normalize
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from wrappers import ZOSDataGrid
from .cmaps import resolve_cmap
from .parameters import PlotParams
from allytools.strings import clean_str
from allytools.units import LengthUnit


class Plotter2D:
    def __init__(self, data: ZOSDataGrid, params: Optional[PlotParams] = None, **param_overrides):
        self.data = data
        self.v_min = self.data.value_min
        self.v_max = self.data.value_max
        base = params if params is not None else PlotParams()
        self.params = replace(base, **param_overrides) if param_overrides else base

    def _compose_params(self, overrides: dict) -> PlotParams:
        return replace(self.params, **overrides) if overrides else self.params

    def render(self, **overrides) -> np.ndarray:
        p = self._compose_params(overrides)
        values = np.asarray(self.data.Values, dtype=float)
        v_min = p.v_min if p.v_min is not None else self.v_min
        v_max = p.v_max if p.v_max is not None else self.v_max
        if p.use_levels:
            levels = np.linspace(v_min, v_max, max(2, int(p.n_levels)))
            norm = BoundaryNorm(levels, ncolors=256)
        else:
            norm = Normalize(vmin=v_min, vmax=v_max)

        cmap = resolve_cmap(p.cmap)
        fig, ax = plt.subplots(1, 1, figsize=p.size_in, dpi=p.dpi)
        canvas = FigureCanvas(fig)

        im = ax.imshow(values,
                       extent=self.data.extent,
                       origin="lower",
                       aspect="equal",
                       cmap=cmap,
                       norm=norm)

        if p.with_colorbar:
            cbar = fig.colorbar(im, ax=ax, pad=0.02)
            self._set_label(cbar, "set_label", p.value_label, getattr(self.data, "ValueLabel", None), default=None)
        self._set_label(ax, "set_xlabel", p.labelX, getattr(self.data, "XLabel", None), default=None)
        self._set_label(ax, "set_ylabel", p.labelY, getattr(self.data, "YLabel", None), default=None)
        self._set_label(ax, "set_title",  p.plot_label, getattr(self.data, "description", None), default=None)

        # Ticks / annotate
        if p.annotate_xy is not None:
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xlabel(f"({p.annotate_xy[0]:.3g}, {p.annotate_xy[1]:.3g})", labelpad=2, fontsize=9)
        elif p.hide_ticks:
            ax.set_xticks([])
            ax.set_yticks([])

        if p.sensor_grid and (p.pixel_size is not None):
            pitch_um = float(p.pixel_size.to(LengthUnit.UM))
            print(pitch_um)
            if np.isfinite(pitch_um) and pitch_um > 0:
                xmin, xmax, ymin, ymax = self.data.extent
                def first_tick(a, step):
                    return math.ceil(a / step) * step
                x0 = first_tick(xmin, pitch_um)
                y0 = first_tick(ymin, pitch_um)
                xs = np.arange(x0, xmax + 1e-12, pitch_um)
                ys = np.arange(y0, ymax + 1e-12, pitch_um)
                ax.vlines(xs, ymin, ymax, colors=p.sensor_grid_color, linewidth=0.5, alpha=1.0, zorder=5)
                ax.hlines(ys, xmin, xmax, colors=p.sensor_grid_color, linewidth=0.5, alpha=1.0, zorder=5)

        fig.tight_layout()
        canvas.draw()
        img = np.asarray(canvas.buffer_rgba()).copy()  # H x W x 4 uint8
        plt.close(fig)
        return img

    @classmethod
    def _set_label(cls, ax, method_name: str,
                   preferred: Optional[str],
                   fallback: Optional[str],
                   default: Optional[str] = None) -> None:
        for raw in (preferred, fallback, default):
            text = clean_str(raw)
            if text is not None:
                getattr(ax, method_name)(text)
                return
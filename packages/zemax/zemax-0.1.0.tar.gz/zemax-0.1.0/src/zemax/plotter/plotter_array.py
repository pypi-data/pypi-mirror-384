# plotter_array.py
from __future__ import annotations
from dataclasses import replace
from typing import Optional, Tuple
from matplotlib.ticker import FixedLocator, FixedFormatter
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.colors import BoundaryNorm, Normalize
from matplotlib.cm import ScalarMappable
from plotter.scalarField2D import ScalarField2D
from .parameters import PlotParams
from .cmaps import resolve_cmap


def _blank_tile(params: PlotParams) -> np.ndarray:
    fig = plt.figure(figsize=params.size_in, dpi=params.dpi)
    ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
    ax.set_axis_off()
    canvas = FigureCanvas(fig)
    canvas.draw()
    img = np.asarray(canvas.buffer_rgba()).copy()
    plt.close(fig)
    return img


class PlotterArray:
    def __init__(self, sensor_xy, grids: np.ndarray, params: Optional[PlotParams] = None,
                 *,
                 tile_titles: bool = False,
                 mosaic_title: Optional[str] = None,
                 **param_overrides):
        self.sensor_xy = self._coerce_sensor_xy(sensor_xy)
        self.grids = np.asarray(grids, dtype=object)

        if self.grids.ndim != 2:
            raise ValueError(f"grids must be 2D (R, C), got {self.grids.shape}")
        if self.grids.shape != self.sensor_xy.shape[:2]:
            raise ValueError(f"sensor and grids shapes mismatch: {self.sensor_xy.shape[:2]} vs {self.grids.shape}")
        base = params if params is not None else PlotParams()
        defaults = dict(with_colorbar=False, hide_ticks=True)
        merged = {**defaults, **param_overrides}
        self.params = replace(base, **merged)
        self.tile_titles = tile_titles
        self.mosaic_title = mosaic_title
        auto_vmin, auto_vmax = self._global_minmax(self.grids)
        self.v_min = self.params.v_min if getattr(self.params, "v_min", None) is not None else auto_vmin
        self.v_max = self.params.v_max if getattr(self.params, "v_max", None) is not None else auto_vmax

    def render_tiles(self, **overrides) -> np.ndarray:
        p = replace(self.params, **overrides) if overrides else self.params
        R, C = self.grids.shape

        first = self._render_single(0, 0, p)
        h, w = first.shape[:2]
        tiles = np.empty((R, C, h, w, 4), dtype=np.uint8)
        tiles[0, 0] = first

        for i in range(R):
            for j in range(C):
                if i == 0 and j == 0:
                    continue
                tiles[i, j] = self._render_single(i, j, p)
        return tiles

    def render_mosaic(self, **overrides) -> np.ndarray:
        tiles = self.render_tiles(**overrides)
        R, C, h, w, _ = tiles.shape
        H, W = R * h, C * w
        canvas = np.zeros((H, W, 4), dtype=np.uint8)
        for i in range(R):
            for j in range(C):
                y0 = i * h
                x0 = j * w
                canvas[y0:y0 + h, x0:x0 + w, :] = tiles[i, j]
        return canvas

    def render_mosaic_with_colorbar(self, *,
                                    title: Optional[str] = None,
                                    cbar_width_px: int = 140,
                                    pad_px: int = 12,
                                    title_height_px: int = 64,
                                    cbar_ticks: int = 6,
                                    tick_format: str = "{x:.3g}",
                                    tick_labelsize: int = 11,
                                    cbar_labelsize: int = 12,
                                    **overrides) -> np.ndarray:
        mosaic = self.render_mosaic(**overrides)  # (H, W, 4)
        H, W, _ = mosaic.shape
        p = replace(self.params, **overrides) if overrides else self.params
        cmap = resolve_cmap(p.cmap)
        vmin, vmax = self.v_min, self.v_max

        if p.use_levels:
            n_levels = max(2, int(p.n_levels))
            levels = np.linspace(vmin, vmax, n_levels)
            ncolors = getattr(cmap, "N", 256)
            norm = BoundaryNorm(levels, ncolors=ncolors, clip=True)
        else:
            norm = Normalize(vmin=vmin, vmax=vmax)

        fig_w_in = cbar_width_px / p.dpi
        fig_h_in = H / p.dpi
        fig = plt.figure(figsize=(fig_w_in, fig_h_in), dpi=p.dpi)

        # Make opaque so tick labels don't vanish on transparent background
        fig.patch.set_facecolor("white")
        fig.patch.set_alpha(1.0)

        # Manually place the colorbar axis; leave room for tick labels
        cax = fig.add_axes([0.20, 0.05, 0.65, 0.90])  # [left, bottom, width, height] in 0..1

        sm = ScalarMappable(norm=norm, cmap=cmap)
        sm.set_array([])

        cbar = fig.colorbar(sm, cax=cax)

        # --- EXPLICIT ticks & labels (robust across MPL versions)
        ticks = np.linspace(vmin, vmax, max(2, cbar_ticks))
        cbar.locator = FixedLocator(ticks)
        cbar.formatter = FixedFormatter([tick_format.format(x=t) for t in ticks])
        cbar.update_ticks()

        # Force label visibility & color
        cbar.ax.tick_params(labelsize=tick_labelsize, colors="black")
        for ticklbl in cbar.ax.get_yticklabels():
            ticklbl.set_color("black")
            ticklbl.set_visible(True)

        # Optional colorbar label
        if getattr(p, "value_label", None):
            cbar.set_label(p.value_label, fontsize=cbar_labelsize, color="black")

        # Rasterize the colorbar figure to RGBA
        canvas = FigureCanvas(fig)
        canvas.draw()
        cbar_rgba = np.asarray(canvas.buffer_rgba()).copy()  # (H, cbar_w, 4)
        plt.close(fig)

        # 4) Concatenate: [ mosaic | pad | colorbar ]
        pad_col = np.zeros((H, max(pad_px, 0), 4), dtype=np.uint8) if pad_px > 0 else np.zeros((H, 0, 4),
                                                                                               dtype=np.uint8)
        mosaic_plus_cbar = np.concatenate([mosaic, pad_col, cbar_rgba], axis=1)

        # 5) Optional top title band
        effective_title = title if title is not None else self.mosaic_title
        if effective_title:
            fig_w_in = mosaic_plus_cbar.shape[1] / p.dpi
            fig_h_in = max(title_height_px, 1) / p.dpi

            fig2 = plt.figure(figsize=(fig_w_in, fig_h_in), dpi=p.dpi)
            fig2.patch.set_facecolor("white")
            fig2.patch.set_alpha(1.0)
            ax2 = fig2.add_axes([0, 0, 1, 1])
            ax2.set_axis_off()
            ax2.text(
                0.5, 0.5, str(effective_title),
                ha="center", va="center",
                fontsize=max(10, int(0.45 * fig_h_in * p.dpi)),
                color="black",
                transform=ax2.transAxes,
            )
            canvas2 = FigureCanvas(fig2)
            canvas2.draw()
            title_rgba = np.asarray(canvas2.buffer_rgba()).copy()
            plt.close(fig2)

            return np.concatenate([title_rgba, mosaic_plus_cbar], axis=0)

        return mosaic_plus_cbar

    def _render_single(self, i: int, j: int, params: PlotParams) -> np.ndarray:
        g = self.grids[i, j]
        if g is None:
            return _blank_tile(params)
        dp = Plotter2DScalarField(g, params=params)
        dp.v_min = self.v_min
        dp.v_max = self.v_max
        annotate = None if params.annotate_xy is not None else tuple(map(float, self.sensor_xy[i, j]))
        if not self.tile_titles:
            return dp.render(annotate_xy=annotate, plot_label="\u00A0")
        return dp.render(annotate_xy=annotate)

    @staticmethod
    def _coerce_sensor_xy(sensor_xy) -> np.ndarray:
        arr = np.asarray(sensor_xy, dtype=object)
        if arr.ndim == 3 and arr.shape[-1] == 2 and np.issubdtype(np.asarray(arr).dtype, np.number):
            return np.asarray(arr, dtype=float)
        if arr.ndim == 2:
            R, C = arr.shape
            out = np.empty((R, C, 2), dtype=float)
            for i in range(R):
                for j in range(C):
                    xy = arr[i, j]
                    if not (hasattr(xy, "__len__") and len(xy) == 2):
                        raise ValueError(f"sensor_xy[{i},{j}] must be a 2-sequence, got {type(xy)}: {xy!r}")
                    out[i, j, 0] = float(xy[0])
                    out[i, j, 1] = float(xy[1])
            return out
        raise ValueError(f"sensor_xy must be (R,C,2) numeric or (R,C) object of (x,y); got shape {arr.shape}")

    @staticmethod
    def _grid_minmax(g) -> Tuple[float, float]:
        vmin = getattr(g, "value_min", None)
        vmax = getattr(g, "value_max", None)
        if vmin is None or vmax is None:
            vals = np.asarray(g.Values, dtype=float)
            finite = vals[np.isfinite(vals)]
            if finite.size == 0:
                return np.nan, np.nan
            return float(np.min(finite)), float(np.max(finite))
        return float(vmin), float(vmax)

    def _global_minmax(self, grids: np.ndarray) -> Tuple[float, float]:
        mins, maxs = [], []
        R, C = grids.shape
        for i in range(R):
            for j in range(C):
                g = grids[i, j]
                if g is None:
                    continue
                vmin, vmax = self._grid_minmax(g)
                if np.isfinite(vmin) and np.isfinite(vmax):
                    mins.append(vmin)
                    maxs.append(vmax)
        if not mins:
            raise ValueError("No finite data found across grids.")
        return float(np.min(mins)), float(np.max(maxs))

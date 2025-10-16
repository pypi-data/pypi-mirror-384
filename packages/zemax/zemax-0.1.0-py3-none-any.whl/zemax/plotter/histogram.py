from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

try:
    from PIL import Image
except ImportError:
    Image = None

# expects: wrappers.ZOSDataGrid with .Values and (optionally) .ValueLabel/.description
from wrappers import ZOSDataGrid


@dataclass
class HistogramParams:
    size_in: Tuple[float, float] = (4.0, 3.0)  # inches (w,h)
    dpi: int = 150
    bins: int = 100
    range: Optional[Tuple[float, float]] = None  # (vmin, vmax); None = auto
    log: bool = False
    density: bool = False
    cumulative: bool = False
    show_stats: bool = True         # draw mean/median lines
    title: Optional[str] = None     # overrides grid.description
    x_label: Optional[str] = None   # overrides grid.ValueLabel
    y_label: Optional[str] = None   # None -> "count" or "density"


class ZOSGridHistogram:
    def __init__(self, grid: ZOSDataGrid, params: Optional[HistogramParams] = None, **overrides):
        self.grid = grid
        base = params if params is not None else HistogramParams()
        # simple, safe override merge
        for k, v in overrides.items():
            if hasattr(base, k):
                setattr(base, k, v)
        self.p = base

    def _values_1d(self) -> np.ndarray:
        a = np.asarray(self.grid.Values, dtype=float)
        vals = a[np.isfinite(a)].ravel()
        if vals.size == 0:
            raise ValueError("ZOSDataGrid has no finite values for histogram.")
        return vals

    def _labels(self) -> Tuple[str, str, str]:
        title = self.p.title or getattr(self.grid, "description", "") or "Histogram"
        xlab = self.p.x_label or getattr(self.grid, "ValueLabel", "") or "Value"
        ylab = self.p.y_label or ("Density" if self.p.density else "Count")
        return title, xlab, ylab

    @property
    def peak(self) -> float:
        """
        Most common value (mode estimate) as the center of the histogram bin
        with the highest count, using current bins/range settings.
        """
        vals = self._values_1d()
        if vals.size == 0:
            return float("nan")

        if self.p.range is not None:
            vmin, vmax = self.p.range
        else:
            vmin, vmax = float(np.min(vals)), float(np.max(vals))
            if not np.isfinite(vmin) or not np.isfinite(vmax) or vmax <= vmin:
                return float("nan")

        counts, edges = np.histogram(vals, bins=self.p.bins, range=(vmin, vmax), density=False)
        if counts.size == 0 or np.all(counts == 0):
            return float("nan")

        idx = int(np.argmax(counts))
        # Bin center
        return float(0.5 * (edges[idx] + edges[idx + 1]))



    def render(self) -> np.ndarray:
        vals = self._values_1d()
        vmin, vmax = (self.p.range if self.p.range is not None
                      else (float(np.min(vals)), float(np.max(vals))))
        title, xlab, ylab = self._labels()

        fig, ax = plt.subplots(1, 1, figsize=self.p.size_in, dpi=self.p.dpi)
        canvas = FigureCanvas(fig)

        ax.hist(
            vals,
            bins=self.p.bins,
            range=(vmin, vmax),
            log=self.p.log,
            density=self.p.density,
            cumulative=self.p.cumulative,
            color=None,  # let mpl choose
            edgecolor="none",
        )

        if self.p.show_stats:
            mean = float(np.mean(vals))
            med = float(np.median(vals))
            ax.axvline(mean, color="C1", linestyle="--", linewidth=1.2, label=f"mean={mean:.3g}")
            ax.axvline(med,  color="C2", linestyle="-.", linewidth=1.2, label=f"median={med:.3g}")
            ax.legend(loc="best", fontsize=8, framealpha=0.8)

        ax.set_title(title)
        ax.set_xlabel(xlab)
        ax.set_ylabel(ylab)

        fig.tight_layout()
        canvas.draw()
        img = np.asarray(canvas.buffer_rgba()).copy()  # H x W x 4 uint8
        plt.close(fig)
        return img

    def render_pil(self):
        if Image is None:
            raise RuntimeError("Pillow is not installed. `pip install pillow` to enable.")
        return Image.fromarray(self.render(), mode="RGBA")

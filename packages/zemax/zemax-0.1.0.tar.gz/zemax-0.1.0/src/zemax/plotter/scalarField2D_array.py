# plotter_array_v2.py
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import Normalize, BoundaryNorm
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from dataclasses import replace
from typing import Optional

from .parameters import PlotParams
from .cmaps import resolve_cmap
from plotter.scalarField2D import ScalarField2D


def scalar_field2d_array(
    sensor_grid: np.ndarray,
    psf_array: np.ndarray,
    *,
    params: Optional[PlotParams] = None,
    mosaic_title: Optional[str] = None,
    **param_overrides,
) -> np.ndarray:
    """
    Render a PSF mosaic (grid of images) with a real Matplotlib colorbar axis using GridSpec.
    - Reuses Plotter2D's logic via render_into(...) to keep rendering behavior consistent.
    - Uses global vmin/vmax (or levels) so all tiles share the same normalization.
    - Shows per-tile (x, y) under each image if params.annotate_xy is None.
    - Returns an RGBA numpy array (H, W, 4).

    Parameters
    ----------
    sensor_grid : np.ndarray
        Shape (R, C, 2) or (R, C) object of (x, y). Used for (x, y) labels under tiles.
    psf_array : np.ndarray
        Shape (R, C) of objects each having a 2D array in attribute `.Values`. May contain None.
    params : PlotParams, optional
        Base PlotParams. Defaults to PlotParams().
    mosaic_title : str, optional
        Top title string (can also be provided via **param_overrides as 'mosaic_title').
    **param_overrides :
        Extra PlotParams fields to override, PLUS the following function-only flags:
          - tile_titles: bool (default False)     -> whether to show per-tile title
          - with_colorbar: bool (default True)    -> include colorbar column
          - mosaic_title: str (optional)          -> top title; same as the dedicated arg

    Returns
    -------
    np.ndarray
        RGBA image array of the mosaic (H, W, 4), dtype=uint8.
    """

    # 0) Validate shapes
    if psf_array.shape != sensor_grid.shape:
        raise ValueError(
            f"sensor_grid and psf_array shapes must match; got {sensor_grid.shape} vs {psf_array.shape}"
        )
    R, C = psf_array.shape

    # 1) Extract function-only flags; pass only PlotParams fields into replace(...)
    tile_titles = bool(param_overrides.pop("tile_titles", False))
    with_colorbar = bool(param_overrides.pop("with_colorbar", True))
    mosaic_title = param_overrides.pop("mosaic_title", mosaic_title)

    base = params if params is not None else PlotParams()
    p = replace(base, **param_overrides)  # only PlotParams fields should remain here
    cmap = resolve_cmap(p.cmap)

    # 2) Global normalization (vmin/vmax or levels)
    vmins, vmaxs = [], []
    for i in range(R):
        for j in range(C):
            g = psf_array[i, j]
            if g is None:
                continue
            V = np.asarray(g.Values, dtype=float)
            if np.isfinite(V).any():
                vmins.append(np.nanmin(V))
                vmaxs.append(np.nanmax(V))
    if not vmins:
        raise ValueError("No valid PSF grids to render.")

    vmin = p.v_min if getattr(p, "v_min", None) is not None else float(min(vmins))
    vmax = p.v_max if getattr(p, "v_max", None) is not None else float(max(vmaxs))

    if p.use_levels:
        n_levels = max(2, int(p.n_levels))
        levels = np.linspace(vmin, vmax, n_levels)
        ncolors = getattr(cmap, "N", 256)
        norm = BoundaryNorm(levels, ncolors=ncolors, clip=True)
    else:
        norm = Normalize(vmin=vmin, vmax=vmax)

    # 3) Figure / GridSpec layout
    tile_w_in, tile_h_in = p.size_in
    extra_w = 0.6 if with_colorbar else 0.0
    fig_w_in = C * tile_w_in + extra_w
    fig_h_in = R * tile_h_in

    fig = plt.figure(figsize=(fig_w_in, fig_h_in), dpi=p.dpi)
    if with_colorbar:
        gs = gridspec.GridSpec(R, C + 1, figure=fig, width_ratios=[1] * C + [0.05])
        last_col_index = -1
    else:
        gs = gridspec.GridSpec(R, C, figure=fig, width_ratios=[1] * C)
        last_col_index = None  # no colorbar column

    # 4) Render tiles using Plotter2D.render_into (shared logic)
    mappable = None
    for i in range(R):
        for j in range(C):
            ax = fig.add_subplot(gs[i, j])
            g = psf_array[i, j]

            if g is None:
                ax.text(0.5, 0.5, "No PSF", ha="center", va="center")
                ax.set_axis_off()
                continue

            # Reuse Plotter2D logic (labels, annotate behavior, etc.)
            dp = ScalarField2D(g, params=p)
            annotate_xy = (
                None if getattr(p, "annotate_xy", None) is not None
                else tuple(map(float, sensor_grid[i, j]))
            )
            plot_label = ("\u00A0" if not tile_titles else None)

            im = dp.render_into(
                ax,
                norm=norm,               # shared normalization across the grid
                annotate_xy=annotate_xy, # same annotate rule as before
                plot_label=plot_label,   # suppress or allow titles
                with_colorbar=False,     # shared colorbar later
            )
            if mappable is None:
                mappable = im

    # 5) Colorbar axis (optional)
    if with_colorbar and (mappable is not None) and (last_col_index is not None):
        cax = fig.add_subplot(gs[:, last_col_index])
        cbar = fig.colorbar(mappable, cax=cax)
        # prefer PlotParams.value_label; else try to read from first non-None PSF
        label = getattr(p, "value_label", None)
        if not label:
            for i in range(R):
                for j in range(C):
                    g = psf_array[i, j]
                    if g is not None:
                        label = getattr(g, "value_label", None)
                        if label:
                            break
                if label:
                    break
        if label:
            cbar.set_label(str(label), fontsize=12)

    # 6) Mosaic title & rasterize to RGBA
    if mosaic_title:
        fig.suptitle(str(mosaic_title), y=0.995, fontsize=14)

    fig.tight_layout()
    canvas = FigureCanvas(fig)
    canvas.draw()
    rgba = np.asarray(canvas.buffer_rgba()).copy()
    plt.close(fig)
    return rgba

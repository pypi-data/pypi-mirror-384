from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import numpy as np
from wrappers import ZOSDataGrid  # your class with .Values, Nx, Ny, MinX, MinY, Dx, Dy, and _create(...)

@dataclass(frozen=True)
class CropResult:
    grid: ZOSDataGrid                  # cropped copy
    bbox_ij: Tuple[int, int, int, int] # (i0, i1, j0, j1) rows/cols slice

def crop_above_threshold(grid: ZOSDataGrid, threshold: float, pad: int = 0) -> CropResult:
    """
    Return a NEW ZOSDataGrid cropped to the smallest box containing all pixels > threshold.
    pad expands the box by 'pad' pixels in all directions (clamped to bounds).
    """
    v = np.asarray(grid.Values, dtype=float)
    if v.ndim != 2:
        raise ValueError(f"Values must be 2D, got {v.shape}")

    # mask of 'valuable' area
    mask = (v > threshold) & np.isfinite(v)
    if not mask.any():
        raise ValueError(f"No pixels above threshold={threshold!r}.")

    # bounding box of True region
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    i0, i1 = int(rows[0]), int(rows[-1] + 1)
    j0, j1 = int(cols[0]), int(cols[-1] + 1)

    # optional padding
    if pad > 0:
        i0 = max(0, i0 - pad)
        j0 = max(0, j0 - pad)
        i1 = min(grid.Ny, i1 + pad)
        j1 = min(grid.Nx, j1 + pad)

    # copy the subset (to keep it independent of original)
    sub = v[i0:i1, j0:j1].copy()

    # create a new grid with updated geometry
    new_grid = type(grid)._create(
        description=getattr(grid, "description", None),
        XLabel=getattr(grid, "XLabel", None),
        YLabel=getattr(grid, "YLabel", None),
        ValueLabel=getattr(grid, "ValueLabel", None),
        Nx=int(sub.shape[1]),
        Ny=int(sub.shape[0]),
        MinX=float(grid.MinX + j0 * grid.Dx),
        MinY=float(grid.MinY + i0 * grid.Dy),
        Dx=float(grid.Dx),
        Dy=float(grid.Dy),
        Values=sub,
    )

    return CropResult(grid=new_grid, bbox_ij=(i0, i1, j0, j1))

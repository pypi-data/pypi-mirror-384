from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import numpy as np
from zemax.wrappers import ZOSDataGrid

from typing import NamedTuple, Tuple

class CropResult(NamedTuple):
    grid: ZOSDataGrid
    bbox_ij: Tuple[int, int, int, int]

def crop_above_threshold(grid: ZOSDataGrid, threshold: float, pad: int = 0, *, strict: bool = True):
    v = np.asarray(grid.Values, dtype=float)
    if v.ndim != 2:
        raise ValueError(f"Values must be 2D, got {v.shape}")

    cmp = (v > threshold) if strict else (v >= threshold)
    mask = cmp & np.isfinite(v)
    if not mask.any():
        raise ValueError(f"No pixels {'>' if strict else '>='} {threshold!r}.")

    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    i0, i1 = int(rows[0]), int(rows[-1] + 1)
    j0, j1 = int(cols[0]), int(cols[-1] + 1)

    if pad > 0:
        i0 = max(0, i0 - pad); j0 = max(0, j0 - pad)
        i1 = min(grid.Ny, i1 + pad); j1 = min(grid.Nx, j1 + pad)

    sub = v[i0:i1, j0:j1].copy()
    new_grid = type(grid)._create(
        description=getattr(grid, "description", None),
        XLabel=getattr(grid, "XLabel", None),
        YLabel=getattr(grid, "YLabel", None),
        ValueLabel=getattr(grid, "ValueLabel", None),
        Nx=int(sub.shape[1]), Ny=int(sub.shape[0]),
        MinX=float(grid.MinX + j0 * grid.Dx),
        MinY=float(grid.MinY + i0 * grid.Dy),
        Dx=float(grid.Dx), Dy=float(grid.Dy),
        Values=sub,
    )
    # keep your dataclass (clear and handy)
    return CropResult(grid=new_grid, bbox_ij=(i0, i1, j0, j1))

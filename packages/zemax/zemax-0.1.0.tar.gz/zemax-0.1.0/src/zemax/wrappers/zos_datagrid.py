from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from numpy.typing import NDArray
from typing import Any, Mapping
from allytools.frozen import Frozen


# noinspection PyPep8Naming
@Frozen.register()
@dataclass(frozen=True, slots=True, init=False, eq=False)
class ZOSDataGrid(Frozen):
    description: str
    XLabel: str
    YLabel: str
    ValueLabel: str
    Nx: int
    Ny: int
    MinX: float
    MinY: float
    Dx: float
    Dy: float
    Values: NDArray[np.float64]

    @classmethod
    def create(cls, data: Any) -> "ZOSDataGrid | None":
        nx = int(cls.scalar(getattr(data, "Nx")))
        ny = int(cls.scalar(getattr(data, "Ny")))
        if nx <= 0 or ny <= 0:
            return None
        vals = np.ascontiguousarray(np.asarray(getattr(data, "Values")), dtype=np.float64)
        vals.setflags(write=False)

        return cls._create(description=str(cls.scalar(getattr(data, "Description"))),
                           XLabel=str(cls.scalar(getattr(data, "XLabel"))),
                           YLabel=str(cls.scalar(getattr(data, "YLabel"))),
                           ValueLabel=str(cls.scalar(getattr(data, "ValueLabel"))),
                           Nx=nx,
                           Ny=ny,
                           MinX=float(cls.scalar(getattr(data, "MinX"))),
                           MinY=float(cls.scalar(getattr(data, "MinY"))),
                           Dx=float(cls.scalar(getattr(data, "Dx"))),
                           Dy=float(cls.scalar(getattr(data, "Dy"))),
                           Values=vals)


    def __post_init__(self) -> None:
        for name in ("Nx", "Ny"):
            v = getattr(self, name)
            if v <= 0:
                raise ValueError(f"{name} must be > 0, got {v}.")
        for name in ("Dx", "Dy"):
            v = getattr(self, name)
            if not np.isfinite(v) or v == 0.0:
                raise ValueError(f"{name} must be finite and non-zero, got {v}.")
        for name in ("MinX", "MinY"):
            v = getattr(self, name)
            if not np.isfinite(v):
                raise ValueError(f"{name} must be finite, got {v}.")

        vals = self.Values
        if vals.dtype == object or not np.issubdtype(vals.dtype, np.number):
            raise TypeError(f"Values must be numeric, got dtype={vals.dtype}.")
        if vals.ndim != 2:
            raise ValueError(f"Values must be 2D, got shape {vals.shape}.")
        if vals.shape != (self.Ny, self.Nx):
            raise ValueError(f"Values shape {vals.shape} != (Ny, Nx)=({self.Ny}, {self.Nx}).")

    @classmethod
    def from_npz(cls, z: Mapping[str, Any]) -> "ZOSDataGrid":
        vals = np.asarray(z["Values"], dtype=np.float64, order="C")
        vals.setflags(write=False)
        return cls._create(description=str(np.asarray(z["description"])),
                           XLabel=str(np.asarray(z["XLabel"])),
                           YLabel=str(np.asarray(z["YLabel"])),
                           ValueLabel=str(np.asarray(z["ValueLabel"])),
                           Nx=int(np.asarray(z["Nx"])),
                           Ny=int(np.asarray(z["Ny"])),
                           MinX=float(np.asarray(z["MinX"])),
                           MinY=float(np.asarray(z["MinY"])),
                           Dx=float(np.asarray(z["Dx"])),
                           Dy=float(np.asarray(z["Dy"])),
                           Values=vals)

    def to_npz(self) -> Mapping[str, Any]:
        return {"__class__":  np.array(self.__class__.__name__, dtype=np.str_),
                "description": np.array(self.description, dtype=np.str_),
                "XLabel":      np.array(self.XLabel, dtype=np.str_),
                "YLabel":      np.array(self.YLabel, dtype=np.str_),
                "ValueLabel":  np.array(self.ValueLabel, dtype=np.str_),
                "Nx":          np.int32(self.Nx),
                "Ny":          np.int32(self.Ny),
                "MinX":        np.float64(self.MinX),
                "MinY":        np.float64(self.MinY),
                "Dx":          np.float64(self.Dx),
                "Dy":          np.float64(self.Dy),
                "Values":      np.asarray(self.Values, dtype=np.float64, order="C")}

    @property
    def shape(self) -> tuple[int, int]:
        return self.Ny, self.Nx

    @property
    def x_max(self) -> float:
        return self.MinX + (self.Nx - 1) * self.Dx

    @property
    def y_max(self) -> float:
        return self.MinY + (self.Ny - 1) * self.Dy

    @property
    def x_coords(self) -> NDArray[np.float64]:
        return self.MinX + self.Dx * np.arange(self.Nx, dtype=np.float64)

    @property
    def y_coords(self) -> NDArray[np.float64]:
        return self.MinY + self.Dy * np.arange(self.Ny, dtype=np.float64)

    @property
    def extent(self) -> tuple[float, float, float, float]:
        return self.MinX, self.x_max, self.MinY, self.y_max

    @property
    def value_min(self) -> float:
        try:
            return float(np.nanmin(self.Values))
        except ValueError:
            return float("nan")

    @property
    def value_max(self) -> float:
        try:
            return float(np.nanmax(self.Values))
        except ValueError:
            return float("nan")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ZOSDataGrid):
            return NotImplemented
        return (
            self.description == other.description
            and self.XLabel == other.XLabel
            and self.YLabel == other.YLabel
            and self.ValueLabel == other.ValueLabel
            and self.Nx == other.Nx
            and self.Ny == other.Ny
            and self.MinX == other.MinX
            and self.MinY == other.MinY
            and self.Dx == other.Dx
            and self.Dy == other.Dy
            and np.array_equal(self.Values, other.Values)
        )

    def __str__(self) -> str:
        return (f"Grid: {self.description}\n"
                f"X axis     : {self.XLabel}\n"
                f"Y axis     : {self.YLabel}\n"
                f"Value label: {self.ValueLabel}\n"
                f"Size       : {self.Nx} x {self.Ny}\n"
                f"Range X    : {self.MinX:.3f} to {self.x_max:.3f}\n"
                f"Range Y    : {self.MinY:.3f} to {self.y_max:.3f}")

    def __repr__(self) -> str:
        return (f"DataGrid(Nx={self.Nx}, Ny={self.Ny}, Dx={self.Dx}, Dy={self.Dy}, "
                f"MinX={self.MinX}, MinY={self.MinY}, Description='{self.description}')")


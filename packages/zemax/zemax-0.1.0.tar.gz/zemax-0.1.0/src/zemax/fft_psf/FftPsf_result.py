from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Tuple
from pathlib import Path
import numpy as np
from numpy.typing import NDArray

@dataclass(frozen=True, slots=True)
class PSFResult:
    description: str
    label_x_axis: str
    label_y_axis: str
    value_label: str
    Nx: int
    Ny: int
    MinX: float
    MinY: float
    Dx: float
    Dy: float
    Values: NDArray[np.float64]
    ZMXPath: str = ""
    field_xy: Tuple[float, float, float] = (0.0, 0.0, 1.0)
    _NPZ_VERSION: int = 2

    def __post_init__(self) -> None:
        vals = self.Values
        if vals.dtype == object or not np.issubdtype(vals.dtype, np.number):
            raise TypeError(f"Values must be numeric, got dtype={vals.dtype}.")
        if vals.ndim != 2:
            raise ValueError(f"Values must be 2D, got shape {vals.shape}.")
        if vals.shape != (self.Ny, self.Nx):
            raise ValueError(f"Values shape {vals.shape} != (Ny, Nx)=({self.Ny}, {self.Nx}).")

    @property
    def Vmin(self) -> float:
        return float(np.nanmin(self.Values))

    @property
    def Vmax(self) -> float:
        return float(np.nanmax(self.Values))

    @classmethod
    def from_array(cls, values: NDArray[np.floating], **kwargs) -> "PSFResult":
        vals = np.ascontiguousarray(np.asarray(values), dtype=np.float64)
        ny, nx = vals.shape
        return cls(Values=vals, Ny=ny, Nx=nx, **kwargs)

    @classmethod
    def from_datagrid(cls, data: Any, *, zmx_path: str | Path, field_xy: Tuple[float, float,float]) -> "PSFResult":
        vals = np.ascontiguousarray(np.asarray(getattr(data, "Values")), dtype=np.float64)
        return cls(description=str(getattr(data, "Description")),
                   label_x_axis=str(getattr(data, "XLabel")),
                   label_y_axis=str(getattr(data, "YLabel")),
                   value_label=str(getattr(data, "ValueLabel")),
                   Nx=int(getattr(data, "Nx")),
                   Ny=int(getattr(data, "Ny")),
                   MinX=float(getattr(data, "MinX")),
                   MinY=float(getattr(data, "MinY")),
                   Dx=float(getattr(data, "Dx")),
                   Dy=float(getattr(data, "Dy")),
                   Values=vals,
                   ZMXPath=str(zmx_path),
                   field_xy=field_xy)

    def _to_npz_payload(self) -> dict:
        return {
            "version": np.int32(self._NPZ_VERSION),
            "description": np.array(self.description, dtype=np.str_),
            "xlabel":      np.array(self.label_x_axis, dtype=np.str_),
            "ylabel":      np.array(self.label_y_axis, dtype=np.str_),
            "valuelabel":  np.array(self.value_label, dtype=np.str_),
            "Nx":   np.int32(self.Nx),
            "Ny":   np.int32(self.Ny),
            "MinX": np.float64(self.MinX),
            "MinY": np.float64(self.MinY),
            "Dx":   np.float64(self.Dx),
            "Dy":   np.float64(self.Dy),
            "Values": np.asarray(self.Values, dtype=np.float64, order="C"),
            "SystemPath": np.array(self.ZMXPath, dtype=np.str_),
            "FieldX": np.float64(self.field_xy[0]),
            "FieldY": np.float64(self.field_xy[1]),
        }

    @staticmethod
    def _scalar(a: Any) -> Any:
        return a.item() if isinstance(a, np.ndarray) and getattr(a, "shape", None) == () else a

    @classmethod
    def _from_npz_dict(cls, z: Any) -> "PSFResult":
        version = int(cls._scalar(z["version"]))
        if version != 2:
            raise ValueError(f"Unsupported PSFResult NPZ version: {version} (expected 2)")

        values = np.array(z["Values"], dtype=np.float64, copy=True)

        return cls(
            description=str(cls._scalar(z["description"])),
            label_x_axis=str(cls._scalar(z["xlabel"])),
            label_y_axis=str(cls._scalar(z["ylabel"])),
            value_label=str(cls._scalar(z["valuelabel"])),
            Nx=int(cls._scalar(z["Nx"])),
            Ny=int(cls._scalar(z["Ny"])),
            MinX=float(cls._scalar(z["MinX"])),
            MinY=float(cls._scalar(z["MinY"])),
            Dx=float(cls._scalar(z["Dx"])),
            Dy=float(cls._scalar(z["Dy"])),
            Values=values,
            ZMXPath=str(cls._scalar(z["SystemPath"])),
            field_xy=(float(cls._scalar(z["FieldX"])),
                      float(cls._scalar(z["FieldY"])),
                      float(cls._scalar(z["Weight"]))))

    def save_npz(self, file_path: str | Path, *, compress: bool = True) -> None:
        saver = np.savez_compressed if compress else np.savez
        saver(file_path, **self._to_npz_payload())

    @classmethod
    def load_npz(cls, file_path: str | Path) -> "PSFResult":
        with np.load(file_path, allow_pickle=False) as z:
            return cls._from_npz_dict(z)

    def __str__(self) -> str:
        x_max = self.MinX + (self.Nx - 1) * self.Dx
        y_max = self.MinY + (self.Ny - 1) * self.Dy
        return (
            f"Grid: {self.description}\n"
            f"X axis     : {self.label_x_axis}\n"
            f"Y axis     : {self.label_y_axis}\n"
            f"Value label: {self.value_label}\n"
            f"Size       : {self.Nx} x {self.Ny}\n"
            f"Range X    : {self.MinX:.3f} to {x_max:.3f}\n"
            f"Range Y    : {self.MinY:.3f} to {y_max:.3f}"
        )
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional, Mapping, Dict, List
import numpy as np


def _clean_str(val: Any) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    return s if s and s.lower() not in {"none", "null"} else None


def _to_f64(arr: Any) -> np.ndarray:
    return np.ascontiguousarray(np.asarray(arr, dtype=np.float64))


@dataclass(frozen=True, slots=True)
class ZOSScatterPoints:
    x: np.ndarray
    y: np.ndarray
    z: Optional[np.ndarray]
    x_label: Optional[str]
    y_label: Optional[str]
    z_label: Optional[str]
    description: Optional[str]

    # ----------- new helpers to build from ZOSAPI -----------
    @classmethod
    def from_iface(cls, sp_iface: Any) -> Optional["ZOSScatterPoints"]:
        """
        Build a ZOSScatterPoints from a ZOSAPI scatter-points interface object.
        Returns None if the iface is None or lacks valid X/Y arrays.
        """
        if sp_iface is None:
            return None

        x = getattr(sp_iface, "X", None)
        y = getattr(sp_iface, "Y", None)
        if x is None or y is None:
            return None

        xv = _to_f64(x)
        yv = _to_f64(y)
        if xv.shape != yv.shape:
            return None

        z_raw = getattr(sp_iface, "Z", None)
        zv = _to_f64(z_raw) if z_raw is not None else None

        return cls(
            x=xv,
            y=yv,
            z=zv,
            x_label=_clean_str(getattr(sp_iface, "XLabel", None)),
            y_label=_clean_str(getattr(sp_iface, "YLabel", None)),
            z_label=_clean_str(getattr(sp_iface, "ZLabel", None)),
            description=_clean_str(getattr(sp_iface, "Description", None)),
        )

    @classmethod
    def list_from_iar(cls, iar_obj: Any) -> List["ZOSScatterPoints"]:
        """
        Collect all scatter datasets from a live IAR_ object.
        Skips invalid/empty entries.
        """
        out: List[ZOSScatterPoints] = []
        n_sc = int(getattr(iar_obj, "NumberOfDataScatterPoints", 0))
        for i in range(n_sc):
            sp = getattr(iar_obj, "GetDataScatterPoint")(i)
            item = cls.from_iface(sp)
            if item is not None:
                out.append(item)
        return out

    # ----------- existing NPZ I/O -----------
    def to_npz(self, prefix: str) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            f"{prefix}x": np.asarray(self.x, dtype=np.float64, order="C"),
            f"{prefix}y": np.asarray(self.y, dtype=np.float64, order="C"),
            f"{prefix}x_label": np.array(self.x_label or "", dtype=np.str_),
            f"{prefix}y_label": np.array(self.y_label or "", dtype=np.str_),
            f"{prefix}z_label": np.array(self.z_label or "", dtype=np.str_),
            f"{prefix}description": np.array(self.description or "", dtype=np.str_),
            f"{prefix}has_z": np.array(self.z is not None),
        }
        if self.z is not None:
            out[f"{prefix}z"] = np.asarray(self.z, dtype=np.float64, order="C")
        return out

    @staticmethod
    def from_npz(npz: Mapping[str, Any], prefix: str) -> "ZOSScatterPoints":
        def s(key: str) -> Optional[str]:
            val = str(np.asarray(npz[key]))
            val = val.strip()
            return val if val and val.lower() not in {"none", "null"} else None
        has_z = bool(np.asarray(npz[f"{prefix}has_z"]))
        z = np.asarray(npz[f"{prefix}z"], dtype=np.float64, order="C") if has_z else None
        return ZOSScatterPoints(
            x=np.asarray(npz[f"{prefix}x"], dtype=np.float64, order="C"),
            y=np.asarray(npz[f"{prefix}y"], dtype=np.float64, order="C"),
            z=z,
            x_label=s(f"{prefix}x_label"),
            y_label=s(f"{prefix}y_label"),
            z_label=s(f"{prefix}z_label"),
            description=s(f"{prefix}description"),
        )

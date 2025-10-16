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
class ZOSDataSeries:
    x: np.ndarray
    y: np.ndarray
    x_label: Optional[str]
    y_label: Optional[str]
    description: Optional[str]

    # ----------- new helpers to build from ZOSAPI -----------
    @classmethod
    def from_iface(cls, s_iface: Any) -> Optional["ZOSDataSeries"]:
        """
        Build a ZOSDataSeries from a ZOSAPI DataSeries interface.
        Returns None if iface is None or lacks valid X/Y arrays.
        """
        if s_iface is None:
            return None

        x = getattr(s_iface, "X", None) or getattr(s_iface, "XValues", None)
        y = getattr(s_iface, "Y", None) or getattr(s_iface, "YValues", None)
        if x is None or y is None:
            return None

        xv = _to_f64(x)
        yv = _to_f64(y)
        if xv.shape != yv.shape:
            return None

        return cls(
            x=xv,
            y=yv,
            x_label=_clean_str(getattr(s_iface, "XLabel", None)),
            y_label=_clean_str(getattr(s_iface, "YLabel", None)),
            description=_clean_str(getattr(s_iface, "Description", None)),
        )

    @classmethod
    def list_from_iar(cls, iar_obj: Any) -> List["ZOSDataSeries"]:
        """
        Collect all data series from a live IAR_ object.
        Skips invalid/empty entries.
        """
        out: List[ZOSDataSeries] = []
        n_s = int(getattr(iar_obj, "NumberOfDataSeries", 0))
        for i in range(n_s):
            s = getattr(iar_obj, "GetDataSeries")(i)
            item = cls.from_iface(s)
            if item is not None:
                out.append(item)
        return out

    # ----------- existing NPZ I/O -----------
    def to_npz(self, prefix: str) -> Dict[str, Any]:
        return {
            f"{prefix}x": np.asarray(self.x, dtype=np.float64, order="C"),
            f"{prefix}y": np.asarray(self.y, dtype=np.float64, order="C"),
            f"{prefix}x_label": np.array(self.x_label or "", dtype=np.str_),
            f"{prefix}y_label": np.array(self.y_label or "", dtype=np.str_),
            f"{prefix}description": np.array(self.description or "", dtype=np.str_),
        }

    @staticmethod
    def from_npz(npz: Mapping[str, Any], prefix: str) -> "ZOSDataSeries":
        def s(key: str) -> Optional[str]:
            val = str(np.asarray(npz[key]))
            val = val.strip()
            return val if val and val.lower() not in {"none", "null"} else None
        return ZOSDataSeries(
            x=np.asarray(npz[f"{prefix}x"], dtype=np.float64, order="C"),
            y=np.asarray(npz[f"{prefix}y"], dtype=np.float64, order="C"),
            x_label=s(f"{prefix}x_label"),
            y_label=s(f"{prefix}y_label"),
            description=s(f"{prefix}description"),
        )

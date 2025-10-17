from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional, Mapping, Dict
from datetime import datetime
import numpy as np
from allytools.strings import clean_str
from allytools.dotnet import to_py_datetime

@dataclass(frozen=True, slots=True)
class ZOSMetaData:
    feature_description: Optional[str]
    lens_file: Optional[str]
    lens_title: Optional[str]
    date: Optional[datetime]

    @property
    def date_iso(self) -> Optional[str]:
        return self.date.isoformat() if self.date else None

    @classmethod
    def from_iface(cls, meta_iface: Any) -> "ZOSMetaData":
        if meta_iface is None:
            # create an empty metadata object
            return cls(feature_description=None, lens_file=None, lens_title=None, date=None)

        return cls(feature_description=clean_str(getattr(meta_iface, "FeatureDescription", None)),
                   lens_file=clean_str(getattr(meta_iface, "LensFile", None)),
                   lens_title=clean_str(getattr(meta_iface, "LensTitle", None)),
                   date=to_py_datetime(getattr(meta_iface, "Date", None)))

    def to_npz(self, prefix: str = "meta.") -> Dict[str, Any]:
        return {
            f"{prefix}FeatureDescription": np.array(self.feature_description or "", dtype=np.str_),
            f"{prefix}LensFile":           np.array(self.lens_file or "", dtype=np.str_),
            f"{prefix}LensTitle":          np.array(self.lens_title or "", dtype=np.str_),
            f"{prefix}DateISO":            np.array(self.date_iso or "", dtype=np.str_),
        }

    @staticmethod
    def from_npz(npz_map: Mapping[str, Any], prefix: str = "meta.") -> "ZOSMetaData":
        def s(k: str) -> Optional[str]:
            v = str(np.asarray(npz_map.get(f"{prefix}{k}", ""))).strip()
            return v or None
        date_iso = s("DateISO")
        dt = None
        if date_iso:
            try:
                dt = datetime.fromisoformat(date_iso.replace("Z", "+00:00"))
            except Exception:
                dt = None

        return ZOSMetaData(feature_description=s("FeatureDescription"),
                           lens_file=s("LensFile"),
                           lens_title=s("LensTitle"),
                           date=dt)

    def __str__(self) -> str:
        return ("ZOSMetaData(\n"
                f"  feature_description={self.feature_description!r},\n"
                f"  lens_file={self.lens_file!r},\n"
                f"  lens_title={self.lens_title!r},\n"
                f"  date={self.date_iso!r}\n"")")
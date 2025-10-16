from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional, Tuple, List, Mapping, Dict
import numpy as np
from .zos_datagrid import ZOSDataGrid
from .zos_scatter_points import ZOSScatterPoints
from .zos_data_series import ZOSDataSeries
from .zos_metadata import ZOSMetaData

_INVALID_MARKER = "Computation aborted; invalid results!"

@dataclass(frozen=True, slots=True)
class ZOSResult:
    grids: Tuple[ZOSDataGrid, ...]
    series: Tuple[ZOSDataSeries, ...]
    scatter: Tuple[ZOSScatterPoints, ...]
    messages: Tuple[str, ...]
    metadata: Optional[ZOSMetaData] = None
    valid: bool = True  # <- NEW FIELD

    @classmethod
    def from_iar(cls, iar_obj: Any) -> "ZOSResult":
        if iar_obj is None:
            raise ValueError("from_iar: iar_obj is None")

        n_g = int(getattr(iar_obj, "NumberOfDataGrids", 0))
        grids: List[ZOSDataGrid] = []
        for i in range(n_g):
            g = iar_obj.GetDataGrid(i)
            if g is not None:
                zos_g = ZOSDataGrid.create(g)
                if zos_g is not None:
                    grids.append(zos_g)

        series = ZOSDataSeries.list_from_iar(iar_obj)
        scat = ZOSScatterPoints.list_from_iar(iar_obj)

        msgs: List[str] = []
        n_m = int(getattr(iar_obj, "NumberOfMessages", 0))
        for i in range(n_m):
            m = iar_obj.GetMessageAt(i)
            text = getattr(m, "Text", None)
            msgs.append(str(text) if text is not None else str(m))

        # validity from first message
        valid = not (msgs and msgs[0].strip() == _INVALID_MARKER)

        meta_iface = getattr(iar_obj, "MetaData", None)
        meta = ZOSMetaData.from_iface(meta_iface) if meta_iface is not None else None

        return cls(grids=tuple(grids),
                   series=tuple(series),
                   scatter=tuple(scat),
                   messages=tuple(msgs),
                   metadata=meta,
                   valid=valid)

    @property
    def n_grids(self) -> int:   return len(self.grids)
    @property
    def n_series(self) -> int:  return len(self.series)
    @property
    def n_scatter(self) -> int: return len(self.scatter)
    @property
    def n_messages(self) -> int:return len(self.messages)
    @property
    def n_raysets(self) -> int: return 0

    def to_npz(self) -> Mapping[str, Any]:
        out: Dict[str, Any] = {
            "iar.__class__":  np.array(self.__class__.__name__, dtype=np.str_),
            "iar.n_grids":    np.int32(self.n_grids),
            "iar.n_series":   np.int32(self.n_series),
            "iar.n_scatter":  np.int32(self.n_scatter),
            "iar.n_messages": np.int32(self.n_messages),
            "iar.valid":      np.bool_(self.valid),  # <- persist validity
        }
        for i, g in enumerate(self.grids):
            prefix = f"iar.dg{i}."
            for k, v in g.to_npz().items():
                out[prefix + k] = v
        for i, s in enumerate(self.series):
            out.update(s.to_npz(prefix=f"iar.ser{i}." ))
        for i, sp in enumerate(self.scatter):
            out.update(sp.to_npz(prefix=f"iar.sc{i}." ))
        for i, m in enumerate(self.messages):
            out[f"iar.msg{i}"] = np.array(m, dtype=np.str_)
        if self.metadata is not None:
            out.update(self.metadata.to_npz(prefix="iar.meta."))
        else:
            out.update({"iar.meta.FeatureDescription": np.array("", dtype=np.str_),
                        "iar.meta.LensFile":           np.array("", dtype=np.str_),
                        "iar.meta.LensTitle":          np.array("", dtype=np.str_),
                        "iar.meta.DateISO":            np.array("", dtype=np.str_)})
        return out

    @classmethod
    def from_npz(cls, npz_map: Mapping[str, Any]) -> "ZOSResult":
        n_g = int(np.asarray(npz_map.get("iar.n_grids", 0)))
        n_s = int(np.asarray(npz_map.get("iar.n_series", 0)))
        n_c = int(np.asarray(npz_map.get("iar.n_scatter", 0)))
        n_m = int(np.asarray(npz_map.get("iar.n_messages", 0)))
        valid = bool(np.asarray(npz_map.get("iar.valid", True)))  # <- default True for backward compat

        grids: List[ZOSDataGrid] = []
        for i in range(n_g):
            prefix = f"iar.dg{i}."
            sub = {k[len(prefix):]: v for k, v in npz_map.items() if k.startswith(prefix)}
            from allytools.frozen import Frozen
            g = Frozen.load_from_npz(sub)
            if not isinstance(g, ZOSDataGrid):
                raise TypeError(f"Decoded grid {i} not ZOSDataGrid, got {type(g).__name__}")
            grids.append(g)

        series: List[ZOSDataSeries] = []
        for i in range(n_s):
            series.append(ZOSDataSeries.from_npz(npz_map, prefix=f"iar.ser{i}."))

        scatter: List[ZOSScatterPoints] = []
        for i in range(n_c):
            scatter.append(ZOSScatterPoints.from_npz(npz_map, prefix=f"iar.sc{i}."))

        messages: List[str] = []
        for i in range(n_m):
            messages.append(str(np.asarray(npz_map[f"iar.msg{i}"])))

        metadata = ZOSMetaData.from_npz(npz_map, prefix="iar.meta.")

        return cls(grids=tuple(grids),
                   series=tuple(series),
                   scatter=tuple(scatter),
                   messages=tuple(messages),
                   metadata=metadata,
                   valid=valid)

    def grid(self, i: int = 0) -> ZOSDataGrid:
        return self.grids[i]

    def first_grid(self) -> Optional[ZOSDataGrid]:
        if not self.valid:
            return None
        if not self.grids:
            return None
        return self.grids[0]

    def __str__(self) -> str:
        parts = [
            "ZOSAPI IAR Wrapper Summary:",
            f"  Status         : {'OK' if self.valid else 'INVALID'}",  # <- show validity
            f"  Data grids     : {self.n_grids}",
            f"  Data series    : {self.n_series}",
            f"  Scatter points : {self.n_scatter}",
            f"  Ray datasets   : {self.n_raysets}",
            f"  Messages       : {self.n_messages}",
        ]

        if self.metadata:
            parts.append("  MetaData:")
            if self.metadata.feature_description:
                parts.append(f"    FeatureDescription : {self.metadata.feature_description}")
            if self.metadata.lens_file:
                parts.append(f"    LensFile           : {self.metadata.lens_file}")
            if self.metadata.lens_title:
                parts.append(f"    LensTitle          : {self.metadata.lens_title}")
            if self.metadata.date_iso:
                parts.append(f"    Date               : {self.metadata.date_iso}")

        if self.n_messages:
            preview = "; ".join(self.messages[:2])
            if len(preview) > 120:
                preview = preview[:117] + "..."
            parts.append(f"  First messages : {preview}{'...' if len(self.messages) > 2 else ''}")

        return "\n".join(parts)

    def __repr__(self) -> str:
        return (f"IARWrapper(valid={'True' if self.valid else 'False'}, "
                f"n_grids={self.n_grids}, "
                f"n_series={self.n_series}, "
                f"n_scatter={self.n_scatter}, "
                f"n_raysets={self.n_raysets}, "
                f"n_messages={self.n_messages}, "
                f"metadata={'set' if self.metadata else 'None'})")

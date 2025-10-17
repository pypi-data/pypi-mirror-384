from __future__ import annotations
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Optional, Protocol, TypeVar, runtime_checkable, Generic

@runtime_checkable
class _IASProtocol(Protocol):
    def Verify(self) -> None: ...
    def Save(self) -> None: ...
    def Load(self) -> None: ...
    def Reset(self) -> None: ...
    def SaveTo(self, settingsFile: str) -> bool: ...
    def LoadFrom(self, settingsFile: str) -> bool: ...
    def ModifySettings(self, settingsFile: str, typeCode: str, newValue: str) -> bool: ...

def _ensure_cfg_path(p: str | Path) -> str:
    path = Path(p).expanduser().resolve()
    if path.suffix.lower() != ".cfg":
        path = path.with_suffix(".cfg")
    return str(path)

T = TypeVar("T", bound=_IASProtocol)

class ZosIAS(ABC, Generic[T]):
    """Abstract base for ZOSAPI Analysis Settings wrappers (IAS_*)."""

    def __init__(self, ias_settings: T):
        # Python.NET proxies often fail Protocol isinstance(); fall back to attr checks
        if not isinstance(ias_settings, _IASProtocol):
            required = ("Verify","Save","Load","Reset","SaveTo","LoadFrom","ModifySettings")
            if not all(hasattr(ias_settings, m) for m in required):
                missing = [m for m in required if not hasattr(ias_settings, m)]
                raise AttributeError(f"Settings object missing required members: {missing}")
        self._ias: T = ias_settings

    # ---- Abstract hook for concrete wrappers ----
    @abstractmethod
    def apply(self, ZOSAPI) -> None:
        """Write current Python-side values into the underlying IAS object."""
        raise NotImplementedError

    # ---- Direct API mirrors ----
    def verify(self) -> None: self._ias.Verify()
    def save(self) -> None: self._ias.Save()
    def load(self) -> None: self._ias.Load()
    def reset(self) -> None: self._ias.Reset()
    def save_to(self, settings_file: str | Path) -> bool: return bool(self._ias.SaveTo(_ensure_cfg_path(settings_file)))
    def load_from(self, settings_file: str | Path) -> bool: return bool(self._ias.LoadFrom(_ensure_cfg_path(settings_file)))
    def modify_setting_in_file(self, settings_file: str | Path, type_code: str, new_value: str) -> bool:
        return bool(self._ias.ModifySettings(_ensure_cfg_path(settings_file), str(type_code), str(new_value)))

    # ---- Convenience helpers ----
    def modify_file(self, settings_file: str | Path, changes: Dict[str, str]) -> bool:
        cfg = _ensure_cfg_path(settings_file)
        ok_all = True
        for k, v in changes.items():
            ok = bool(self._ias.ModifySettings(cfg, str(k), str(v)))
            ok_all = ok_all and ok
        return ok_all

    def save_then_modify(self, out_cfg: str | Path, changes: Dict[str, str]) -> str:
        cfg = _ensure_cfg_path(out_cfg)
        if not self.save_to(cfg):
            raise RuntimeError(f"SaveTo failed: {cfg}")
        if not self.modify_file(cfg, changes):
            raise RuntimeError(f"One or more ModifySettings calls failed for: {cfg}")
        return cfg

    @contextmanager
    def temporary_changes(
        self,
        changes: Dict[str, str],
        *,
        base_file: Optional[str | Path] = None,
        scratch_dir: Optional[str | Path] = None
    ):
        """Temporarily apply multiple changes, then auto-restore original settings."""
        scratch_root = Path(scratch_dir) if scratch_dir else Path.cwd()
        scratch_root.mkdir(parents=True, exist_ok=True)

        original_cfg = scratch_root / "__orig__.cfg"
        work_cfg     = scratch_root / "__work__.cfg"

        # Save true original first
        if not self.save_to(original_cfg):
            raise RuntimeError(f"SaveTo failed (original): {original_cfg}")

        # Optionally start from a provided base CFG
        if base_file:
            base_cfg = _ensure_cfg_path(base_file)
            if not self.load_from(base_cfg):
                raise RuntimeError(f"LoadFrom failed for base_file: {base_cfg}")

        # Prepare working copy and apply changes
        if not self.save_to(work_cfg):
            self.load_from(original_cfg)
            raise RuntimeError(f"SaveTo failed (work): {work_cfg}")
        if not self.modify_file(work_cfg, changes):
            self.load_from(original_cfg)
            raise RuntimeError(f"Failed to apply one or more changes: {changes}")

        # Load modified settings and yield
        if not self.load_from(work_cfg):
            self.load_from(original_cfg)
            raise RuntimeError(f"LoadFrom failed (work): {work_cfg}")

        try:
            yield
        finally:
            self.load_from(original_cfg)

from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional
from core import ZemaxStandAlone, zemax_exceptions


logger = logging.getLogger(__name__)

class ZemaxZMX:
    def __init__(self, zs: ZemaxStandAlone, zos_file: Path, save_on_close: bool = False) -> None:
        self.zs = zs
        self.zos_file = zos_file
        self.save_on_close = bool(save_on_close)
        self._opened: bool = False

    def __enter__(self) -> ZemaxZMX:
        if not self.zs.is_connected:
            raise zemax_exceptions.ZemaxInitializationError("Zemax is not connected. Call zs.connect() first.")
        zos_file = Path(self.zs.sample_dir()) / self.zos_file
        if not zos_file.exists():
            raise zemax_exceptions.ZemaxFileMissing(f"File does not exist: {zos_file}")
        self.zs.open_file(zos_file, save_if_needed=False)
        self._opened = True
        return self

    def __exit__(self, exc_type, exc, tb) -> Optional[bool]:
        if not self._opened:
            return None
        try:
            self.zs.close_file(save=self.save_on_close)
        except Exception as close_err:
            if exc_type is not None:
                logger.warning("Suppressed exception while closing file: %s", close_err, exc_info=True)
                return None  # propagate original exception
            raise
        finally:
            self._opened = False
        return None


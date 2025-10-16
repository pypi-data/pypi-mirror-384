from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from wrappers.zos_message import ZOSMessage
from .base_selector import _BaseZOSSelector

@dataclass(frozen=True, slots=True)
class ZOSSurface(_BaseZOSSelector):
    _ias_surface: Any

    _iface_attr = "_ias_surface"
    _GET_NAME   = "GetSurfaceNumber"
    _SET_NAME   = "SetSurfaceNumber"
    _LABEL      = "IAS_Surface"
    _USE_IMAGE_NAME     = "UseImageSurface"
    _USE_OBJECTIVE_NAME = "UseObjectiveSurface"

    def use_image(self) -> ZOSMessage:
        return self._call_msg(self.__class__._USE_IMAGE_NAME)  # type: ignore[arg-type]

    def use_objective(self) -> ZOSMessage:
        return self._call_msg(self.__class__._USE_OBJECTIVE_NAME)  # type: ignore[arg-type]

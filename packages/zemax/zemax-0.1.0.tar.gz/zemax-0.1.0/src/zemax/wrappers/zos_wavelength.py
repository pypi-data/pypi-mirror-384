from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from wrappers.zos_message import ZOSMessage
from .base_selector import _BaseZOSSelector

@dataclass(frozen=True, slots=True)
class ZOSWavelength(_BaseZOSSelector):
    _ias_wavelength: Any

    _iface_attr = "_ias_wavelength"
    _GET_NAME   = "GetWavelengthNumber"
    _SET_NAME   = "SetWavelengthNumber"
    _LABEL      = "IAS_Wavelength"
    _USE_ALL_NAME = "UseAllWavelengths"

    def use_all(self) -> ZOSMessage:
        return self._call_msg(self.__class__._USE_ALL_NAME)  # type: ignore[arg-type]

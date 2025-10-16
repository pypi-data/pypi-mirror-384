from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from wrappers.zos_message import ZOSMessage
from .base_selector import _BaseZOSSelector

@dataclass(frozen=True, slots=True)
class ZOSField(_BaseZOSSelector):
    _ias_field: Any

    _iface_attr = "_ias_field"
    _GET_NAME   = "GetFieldNumber"
    _SET_NAME   = "SetFieldNumber"
    _LABEL      = "IAS_Field"
    _USE_ALL_NAME = "UseAllFields"

    def use_all(self) -> ZOSMessage:
        return self._call_msg(self.__class__._USE_ALL_NAME)  # type: ignore[arg-type]

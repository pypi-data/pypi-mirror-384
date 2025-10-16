# base_selector.py
from __future__ import annotations
from abc import ABC
from dataclasses import dataclass
from typing import Any, Optional, ClassVar
from wrappers.zos_message import ZOSMessage
from wrappers.zos_error_codes import ErrorCode

@dataclass(frozen=True, slots=True)
class _BaseZOSSelector(ABC):
    _iface_attr: ClassVar[str] = ""
    _GET_NAME:   ClassVar[str] = ""
    _SET_NAME:   ClassVar[str] = ""
    _LABEL:      ClassVar[str] = ""

    @classmethod
    def wrap(cls, iface: Any) -> "_BaseZOSSelector":
        if iface is None:
            raise ValueError(f"{cls.__name__}.wrap: iface is None")
        return cls(**{cls._iface_attr: iface})  # type: ignore[arg-type]

    def _iface(self) -> Any:
        return getattr(self, self.__class__._iface_attr)

    def _call_msg(self, method_name: str, *args: Any) -> ZOSMessage:
        try:
            meth = getattr(self._iface(), method_name)
            msg = meth(*args) if args else meth()
            return ZOSMessage.from_zos(msg)
        except Exception as ex:
            return ZOSMessage(code=ErrorCode.Unknown, text=str(ex))

    def get(self) -> Optional[int]:
        try:
            return int(getattr(self._iface(), self.__class__._GET_NAME)())
        except Exception:
            return None

    def set(self, n: int) -> ZOSMessage:
        return self._call_msg(self.__class__._SET_NAME, int(n))

    def __str__(self) -> str:
        n = self.get()
        return f"{self.__class__._LABEL}(selected={n if n is not None else 'UNKNOWN'})"

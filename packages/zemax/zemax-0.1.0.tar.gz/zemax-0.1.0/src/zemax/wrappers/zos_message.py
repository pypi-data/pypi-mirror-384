from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
from wrappers.zos_error_codes import ErrorCode

@dataclass(frozen=True, slots=True)

class ZOSMessage:
    code: ErrorCode
    text: str

    @property
    def ok(self) -> bool:
        return self.code is ErrorCode.Success

    def __bool__(self) -> bool:
        return self.ok

    @classmethod
    def from_zos(cls, msg: Any) -> "ZOSMessage":
        if msg is None:
            return cls(code=ErrorCode.Unknown, text="")
        text = str(getattr(msg, "Text", "") or "")
        err  = getattr(msg, "ErrorCode", None)

        if err is not None:
            name = None
            try:
                name = str(err.ToString())
            except Exception:
                try:
                    name = str(err)
                except Exception:
                    name = None
            if name:
                key = name.strip()
                try:
                    return cls(code=ErrorCode[key], text=text)
                except KeyError:
                    for ec in ErrorCode:
                        if ec.name.lower() == key.lower():
                            return cls(code=ec, text=text)
            try:
                val = int(err)
                for ec in ErrorCode:
                    if ec.value == val:
                        return cls(code=ec, text=text)
            except Exception:
                pass
        return cls(code=ErrorCode.Unknown, text=text)

    def __str__(self) -> str:
        return f"[{self.code.name}] {self.text}"
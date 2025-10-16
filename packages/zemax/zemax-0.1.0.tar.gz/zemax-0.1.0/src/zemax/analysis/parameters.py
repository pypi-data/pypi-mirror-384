from __future__ import annotations
from dataclasses import dataclass

@dataclass
class ZosMessage:
    code: int
    text: str

    @classmethod
    def from_dotnet(cls, msg) -> "ZosMessage":
        if msg is None: # No message means success
            return cls(code=0, text="OK")
        return cls(code=int(msg.ErrorCode), text=str(msg.Text))

    def __bool__(self):
        return self.code == 0

    def __str__(self):
        return f"[{self.code}] {self.text}"

class FieldParam:
    def __init__(self, ias_field):
        self._field = ias_field

    def get(self) -> int:
        return int(self._field.GetFieldNumber())

    def set(self, n: int) -> ZosMessage:
        return ZosMessage.from_dotnet(self._field.SetFieldNumber(int(n)))

    def use_all(self) -> ZosMessage:
        return ZosMessage.from_dotnet(self._field.UseAllFields())

    def __str__(self):
        return f"FieldParam(current={self.get()})"

class SurfaceParam:
    def __init__(self, ias_surface):
        self._surf = ias_surface

    def get(self) -> int:
        return int(self._surf.GetSurfaceNumber())

    def set(self, n: int) -> ZosMessage:
        return ZosMessage.from_dotnet(self._surf.SetSurfaceNumber(int(n)))

    def use_image(self) -> ZosMessage:
        return ZosMessage.from_dotnet(self._surf.UseImageSurface())

    def use_objective(self) -> ZosMessage:
        return ZosMessage.from_dotnet(self._surf.UseObjectiveSurface())

    def __str__(self):
        return f"SurfaceParam(current={self.get()})"

class WavelengthParam:
    def __init__(self, ias_wavelength):
        self._wl = ias_wavelength

    def get(self) -> int:
        return int(self._wl.GetWavelengthNumber())

    def set(self, n: int) -> ZosMessage:
        return ZosMessage.from_dotnet(self._wl.SetWavelengthNumber(int(n)))

    def use_all(self) -> ZosMessage:
        return ZosMessage.from_dotnet(self._wl.UseAllWavelengths())

    def __str__(self):
        return f"WavelengthParam(current={self.get()})"
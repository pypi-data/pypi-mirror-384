from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from core import ZemaxStandAlone
from .analysisIDM import AnalysisIDM

R_co = TypeVar("R_co", covariant=True)  # result type of .run()

class Analysis(ABC, Generic[R_co]):
    def __init__(self, zs: ZemaxStandAlone, idm:AnalysisIDM) -> None:
        self.zs = zs
        if not (self.zs.ZOSAPI and self.zs.TheSystem):
            raise RuntimeError("Zemax not initialized. Call initialize() first.")
        self.ZOSAPI = zs.ZOSAPI
        self.TheSystem = zs.TheSystem
        self.idm = idm
        zos_idm = getattr(self.ZOSAPI.Analysis.AnalysisIDM, idm.name)
        self.zos_analysis = self.zs.TheSystem.Analyses.New_Analysis(zos_idm)

    def close(self) -> None:
        try:
            if self.zos_analysis is not None:
                self.zos_analysis.Close()
        except Exception:
            pass
        finally:
            self.zos_analysis = None  # help GC

    @abstractmethod
    def settings_from_analysis(self) -> None:
        ...

    @abstractmethod
    def run(self) -> R_co:
        ...

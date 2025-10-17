from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from zemax.core import ZemaxStandAlone
from zemax.analysis.analysisIDM import AnalysisIDM
from zemax.wrappers import ZOSResult, ZosIAS, ZOSMessage

class Analysis(ABC):
    def __init__(self, zs: ZemaxStandAlone, idm:AnalysisIDM) -> None:
        self.zs = zs
        if not (self.zs.ZOSAPI and self.zs.TheSystem):
            raise RuntimeError("Zemax not initialized. Call initialize() first.")
        self.ZOSAPI = zs.ZOSAPI
        self.TheSystem = zs.TheSystem
        self.idm = idm
        zos_idm = getattr(self.ZOSAPI.Analysis.AnalysisIDM, idm.name)
        self.zos_analysis = self.zs.TheSystem.Analyses.New_Analysis(zos_idm)
        self.zos_settings: ZosIAS = self._init_settings()

    def close(self) -> None:
        try:
            if self.zos_analysis is not None:
                self.zos_analysis.Close()
        except Exception:
            pass
        finally:
            self.zos_analysis = None  # help GC

    def run(self) -> ZOSResult:
        self.zos_settings.apply(self.ZOSAPI)
        msg = self.zos_analysis.ApplyAndWaitForCompletion()
        status = ZOSMessage.from_zos(msg)  # TODO return None in all cases
        iar = self.zos_analysis.GetResults()
        return ZOSResult.from_iar(iar)

    @abstractmethod
    def _init_settings(self) -> ZosIAS:
        ...


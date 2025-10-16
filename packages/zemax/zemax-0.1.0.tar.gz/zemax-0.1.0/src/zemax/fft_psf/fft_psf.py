from __future__ import annotations
from typing import Optional, Any
from fft_psf.FftPsf_setting import FftPsfSettings
from analysis import Analysis, AnalysisIDM
from core import ZemaxStandAlone
from lensguild.Optics import Field
from pythonnet import load
from wrappers import ZOSMessage, ZOSResult
load()  # loads .NET (CoreCLR) runtime

import clr
from System import Array, Int32

class FftPSF(Analysis[Any]):
    def __init__(self, zs: ZemaxStandAlone, settings: Optional[FftPsfSettings] = None):
        super().__init__(zs, AnalysisIDM.FftPsf)
        self.settings = settings or FftPsfSettings()



    def set_settings(self, settings: FftPsfSettings) -> None:
        self.settings = settings

    def settings_from_analysis(self) -> None:
        self.settings = FftPsfSettings.from_analysis(self.zos_analysis)

    def run(self):
        self.settings.apply_to(self.zos_analysis, self.ZOSAPI)
        msg = self.zos_analysis.ApplyAndWaitForCompletion()
        status = ZOSMessage.from_zos(msg) #TODO return None in all cases
        return self.zos_analysis.GetResults()

    def __str__(self) -> str:
        return f"FftPSF(settings={self.settings})"

    def run_at_field(self, f: "Field"):
        fld = self.TheSystem.SystemData.Fields
        fld.AddField(float(f.X), float(f.Y), 1.0)
        print(f)
        idx = fld.NumberOfFields
        self.settings.field = idx
        try:
            result = self.run()
            zos_result = ZOSResult.from_iar(result)
        finally:
            try:
                fld.DeleteFieldAt(Int32(idx))
            except Exception:
                try:
                    arr = Array[Int32]([Int32(idx)])
                    fld.DeleteFieldsAt(arr)
                except Exception as e:
                    print(f"Warning: could not delete temporary field #{idx}: {e!r}")

        return result


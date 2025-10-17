from __future__ import annotations
from zemax.psf.psf_settings import PSFSettings
from zemax.analysis import Analysis, AnalysisIDM
from zemax.core import ZemaxStandAlone
from pythonnet import load

load()  # loads .NET (CoreCLR) runtime


class PSF(Analysis):
    def __init__(self, zs: ZemaxStandAlone):
        super().__init__(zs, AnalysisIDM.FftPsf)

    def _init_settings(self) -> PSFSettings:
        return PSFSettings.from_analysis(self.zos_analysis)

    def __str__(self) -> str:
        return f"FFT PSF settings={self.zos_settings}"



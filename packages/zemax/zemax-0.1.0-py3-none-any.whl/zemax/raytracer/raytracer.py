from __future__ import annotations
import time
from typing import Tuple
import clr
import numpy as np
from pathlib import Path
from ZemaxStandAlone import  ZemaxStandAlone
clr.AddReference("System.Runtime.InteropServices") # noqa: F401
from System import Enum, Int32, Double, Array # noqa: F401
from System.Reflection import Assembly # noqa: F401
from lensguild.RayTracing.bundle import Bundle
from lensguild.RayTracing.ray import Ray, Direction, Point
from allytools.units.length import  Length

def load_raytrace_dll(anchor: Path) -> None:
    dll_path = (anchor / ".." / "DLL" / "RayTrace.dll").resolve()
    if not dll_path.is_file():
        raise FileNotFoundError(f"RayTrace.dll not found at: {dll_path}")
    Assembly.LoadFile(str(dll_path))
    import BatchRayTrace  # noqa: F401

class RayTracer:
    def __init__(self, zemax:ZemaxStandAlone):
        self.zemax = zemax
        self.system = zemax.TheSystem
        self.zosapi = zemax.ZOSAPI
        here = Path(__file__).resolve().parent
        load_raytrace_dll(here)
        self.raytrace = zemax.TheSystem.Tools.OpenBatchRayTrace()
        self.bundle = Bundle()

    def run(self, surface:int,wavelength:int, grid:Tuple[int, int]):
        x ,y = grid
        total_rays = x * y
        print("Total rays - ", total_rays)
        x_lin = np.linspace(-1.0, 1.0, x)
        y_lin = np.linspace(-1.0, 1.0, y)
        hy_ary = np.zeros(total_rays)
        normUnPolData = self.raytrace.CreateNormUnpol(total_rays,  self.zosapi .Tools.RayTrace.RaysType.Real, surface)
        normUnPolData.ClearData()
        opd_mode = getattr( self.zosapi .Tools.RayTrace.OPDMode, "None")
        sysInt = Int32(1)
        sysDbl = Double(1.0)
        start = time.time()
        for y in range(1, y + 1):
            for x in range(1, x + 1):
                normUnPolData.AddRay(wavelength, x_lin[x - 1], y_lin[y - 1], 0.0, 0.0, opd_mode)

        point1 = time.time()
        point1_delta = point1 - start
        print(f"Rays added time: {point1_delta:.4f} seconds")
        self.raytrace.RunAndWaitForCompletion()
        normUnPolData.StartReadingResults()
        point2 = time.time()
        point2_delta = point2 - point1
        print(f"Rays processed: {point2_delta:.4f} seconds")
        output = normUnPolData.ReadNextResult(sysInt, sysInt, sysInt,
                                              sysDbl, sysDbl, sysDbl,
                                              sysDbl, sysDbl, sysDbl,
                                              sysDbl, sysDbl,sysDbl, sysDbl, sysDbl)
        i = 0
        while output[0]:
            if (output[2] == 0 and output[3] == 0):# ErrorCode & vignetteCode

                x = output[4]
                y = output[5]
                l = output[7]
                m = output[8]
                n = output[9]
                p = Point(Length(x, y))
                d = Direction.from_cosines(l,m,n)
                r = Ray(p, d)
                self.bundle.add(r)
                i += 1
            output = normUnPolData.ReadNextResult(
                sysInt, sysInt, sysInt,
                sysDbl, sysDbl, sysDbl, sysDbl, sysDbl, sysDbl, sysDbl, sysDbl,
                sysDbl, sysDbl, sysDbl

            )
        end = time.time()
        point3_delta = end - point2
        print(f"Rays traced in time: {point3_delta:.4f} seconds")
        pass
from __future__ import annotations
from enum import Enum
from typing import Dict

class PsfSamplingPy(Enum):
    PsfS_32x32     = "PsfS_32x32"
    PsfS_64x64     = "PsfS_64x64"
    PsfS_128x128   = "PsfS_128x128"
    PsfS_256x256   = "PsfS_256x256"
    PsfS_512x512   = "PsfS_512x512"
    PsfS_1024x1024 = "PsfS_1024x1024"
    PsfS_2048x2048 = "PsfS_2048x2048"
    PsfS_4096x4096 = "PsfS_4096x4096"
    PsfS_8192x8192 = "PsfS_8192x8192"
    PsfS_16384x16384 = "PsfS_16384x16384"

class PsfRotationPy(Enum):
    CW0   = "CW0"
    CW90  = "CW90"
    CW180 = "CW180"
    CW270 = "CW270"

class FftPsfTypePy(Enum):
    Linear    = "Linear"
    Log       = "Log"
    Phase     = "Phase"
    Real      = "Real"
    Imaginary = "Imaginary"

# ---------------------------
# Name aliasing (for OS versions that use S_XXXX instead of PsfS_XXXX)
# ---------------------------

SAMPLING_ALIASES: Dict[str, str] = {
    "S_32x32": "PsfS_32x32",
    "S_64x64": "PsfS_64x64",
    "S_128x128": "PsfS_128x128",
    "S_256x256": "PsfS_256x256",
    "S_512x512": "PsfS_512x512",
    "S_1024x1024": "PsfS_1024x1024",
    "S_2048x2048": "PsfS_2048x2048",
    "S_4096x4096": "PsfS_4096x4096",
    "S_8192x8192": "PsfS_8192x8192",
    "S_16384x16384": "PsfS_16384x16384",
}

def normalize_sampling_name(zos_name: str) -> str:
    return SAMPLING_ALIASES.get(zos_name, zos_name)

# ---------------------------
# Optional: discover which names your ZOS actually exposes (for building dropdowns dynamically)
# ---------------------------

def sync_enums(ZOSAPI) -> Dict[str, list]:
    """
    Returns dict of available enum names actually exposed by your ZOS install.
    Useful if you want to build dropdowns directly from ZOS (guaranteed-compatible).
    """
    from System import Enum
    PsfSampling = ZOSAPI.Analysis.Settings.Psf.PsfSampling
    PsfRotation = ZOSAPI.Analysis.Settings.Psf.PsfRotation
    FftPsfType  = ZOSAPI.Analysis.Settings.Psf.FftPsfType

    samps = [ normalize_sampling_name(n) for n in list(Enum.GetNames(PsfSampling)) ]
    rots  = list(Enum.GetNames(PsfRotation))
    types = list(Enum.GetNames(FftPsfType))
    return {"PsfSampling": samps, "PsfRotation": rots, "FftPsfType": types}

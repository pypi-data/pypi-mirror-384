from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Any
from fft_psf import params
from analysis import WavelengthParam, SurfaceParam
from wrappers import ZOSField, ZOSWavelength, ZOSSurface

@dataclass
class FftPsfSettings:
    field: Optional[int] = None
    wavelength: Optional[int] = None
    image_surface: Optional[int] = None
    sample_size: params.PsfSamplingPy = params.PsfSamplingPy.PsfS_64x64
    output_size: Optional[params.PsfSamplingPy] = None
    rotation: params.PsfRotationPy = params.PsfRotationPy.CW0
    image_delta: float = 0.0
    use_polarization: bool = False
    normalize: bool = True
    psf_type: params.FftPsfTypePy = params.FftPsfTypePy.Linear

    def __post_init__(self):
        if self.output_size is None:
            self.output_size = self.sample_size
        if self.image_delta < 0:
            self.image_delta = 1.0

    @staticmethod
    def _get_casted_settings(analysis) -> Any:
        base = analysis.GetSettings()
        cast = getattr(base, "As_ZOSAPI_Analysis_Settings_Psf_IAS_FftPsf", None)
        if callable(cast):
            obj = cast()
            if obj is not None:
                return obj
        return base.__implementation__

    @staticmethod
    def _get_base_settings(analysis) -> Any:
        return analysis.GetSettings()

    @staticmethod
    def _py_to_zos_enum(ZOSAPI, enum_cls, value):
        from System import Enum as DotNetEnum

        if enum_cls is params.PsfSamplingPy:
            name = params.normalize_sampling_name(value.value)
            zos_enum = ZOSAPI.Analysis.Settings.Psf.PsfSampling
        elif enum_cls is params.PsfRotationPy:
            name = value.value
            zos_enum = ZOSAPI.Analysis.Settings.Psf.PsfRotation
        elif enum_cls is params.FftPsfTypePy:
            name = value.value
            zos_enum = ZOSAPI.Analysis.Settings.Psf.FftPsfType
        else:
            raise ValueError("Unsupported enum class")

        names = list(DotNetEnum.GetNames(zos_enum))
        if name not in names and enum_cls is params.PsfSamplingPy:
            rev_alias = {v: k for k, v in params.SAMPLING_ALIASES.items()}
            alt = rev_alias.get(name, name)
            if alt in names:
                name = alt
        if name not in names:
            name = names[0]
        return DotNetEnum.Parse(zos_enum, name)

    @staticmethod
    def _zos_to_py_sampling(name: str) -> params.PsfSamplingPy:
        norm = params.normalize_sampling_name(name)
        return params.PsfSamplingPy[norm]

    @classmethod
    def from_analysis(cls, analysis) -> "FftPsfSettings":
        s = cls._get_casted_settings(analysis)
        smp = cls._zos_to_py_sampling(s.SampleSize.ToString())
        out = cls._zos_to_py_sampling(s.OutputSize.ToString())
        rot = params.PsfRotationPy[s.Rotation.ToString()]
        typ = params.FftPsfTypePy[s.Type.ToString()]

        # Field / Wavelength / Surface via wrappers
        try:
            field = ZOSField.wrap(s.Field).get()
        except Exception:
            field = None
        try:
            wl = ZOSWavelength.wrap(s.Wavelength).get()
        except Exception:
            wl = None
        try:
            surf = ZOSSurface.wrap(s.Surface).get()
        except Exception:
            surf = None

        return cls(
            field=field,
            wavelength=wl,
            image_surface=surf,
            sample_size=smp,
            output_size=out,
            rotation=rot,
            image_delta=float(s.ImageDelta),
            use_polarization=bool(s.UsePolarization),
            normalize=bool(s.Normalize),
            psf_type=typ,
        )

    def apply_to(self, analysis, ZOSAPI) -> None:
        s_casted = self._get_casted_settings(analysis)
        s_base = self._get_base_settings(analysis)
        target = s_casted or s_base

        # enums / scalars
        target.SampleSize = self._py_to_zos_enum(ZOSAPI, params.PsfSamplingPy, self.sample_size)
        target.OutputSize = self._py_to_zos_enum(ZOSAPI, params.PsfSamplingPy, self.output_size)
        target.Rotation = self._py_to_zos_enum(ZOSAPI, params.PsfRotationPy, self.rotation)
        target.Type = self._py_to_zos_enum(ZOSAPI, params.FftPsfTypePy, self.psf_type)
        target.ImageDelta = float(self.image_delta)
        target.UsePolarization = bool(self.use_polarization)
        target.Normalize = bool(self.normalize)

        if s_casted:
            # Field
            fld = ZOSField.wrap(s_casted.Field)
            (fld.use_all() if self.field is None else fld.set(self.field))

            # Wavelength
            if self.wavelength is not None:
                ZOSWavelength.wrap(s_casted.Wavelength).set(self.wavelength)

            # Surface
            if self.image_surface is not None:
                ZOSSurface.wrap(s_casted.Surface).set(self.image_surface)

    def __str__(self) -> str:
        return (
            "FftPsfSettings(\n"
            f"  field={self.field},\n"
            f"  wavelength={self.wavelength},\n"
            f"  image_surface={self.image_surface},\n"
            f"  sample_size={self.sample_size.name},\n"
            f"  output_size={self.output_size.name},\n"
            f"  rotation={self.rotation.name},\n"
            f"  image_delta={self.image_delta},\n"
            f"  use_polarization={self.use_polarization},\n"
            f"  normalize={self.normalize},\n"
            f"  psf_type={self.psf_type.name}\n"
            ")"
        )

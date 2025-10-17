from __future__ import annotations
from typing import Optional, Any
from zemax.wrappers import ZOSField, ZOSWavelength, ZOSSurface, ZosIAS
from zemax.psf.psf_parameters import (PsfSamplingPy, PsfRotationPy, FftPsfTypePy,
                              normalize_sampling_name, SAMPLING_ALIASES)

class PSFSettings(ZosIAS):
    def __init__(self, ias_settings: Any, *,
                 field: Optional[int] = None,
                 wavelength: Optional[int] = None,
                 image_surface: Optional[int] = None,
                 sample_size: PsfSamplingPy = PsfSamplingPy.PsfS_64x64,
                 output_size: Optional[PsfSamplingPy] = None,
                 rotation: PsfRotationPy = PsfRotationPy.CW0,
                 image_delta: float = 0.0,
                 use_polarization: bool = False,
                 normalize: bool = True,
                 psf_type: FftPsfTypePy = FftPsfTypePy.Linear):
        super().__init__(ias_settings)


        self.field: Optional[int] = field
        self.wavelength: Optional[int] = wavelength
        self.image_surface: Optional[int] = image_surface
        self.sample_size: PsfSamplingPy = sample_size
        self.output_size: PsfSamplingPy = output_size or sample_size
        self.rotation: PsfRotationPy = rotation
        self.image_delta: float = image_delta if image_delta >= 0 else 1.0
        self.use_polarization: bool = bool(use_polarization)
        self.normalize: bool = bool(normalize)
        self.psf_type: FftPsfTypePy = psf_type


    @staticmethod
    def _get_casted_settings(analysis_or_settings) -> Any:
        """Return the concrete IAS_FftPsf if available, else the base IAS_* implementation."""
        base = (analysis_or_settings.GetSettings()
                if hasattr(analysis_or_settings, "GetSettings")
                else analysis_or_settings)
        cast = getattr(base, "As_ZOSAPI_Analysis_Settings_Psf_IAS_FftPsf", None)
        if callable(cast):
            obj = cast()
            if obj is not None:
                return obj
        return getattr(base, "__implementation__", base)

    @staticmethod
    def _py_to_zos_enum(ZOSAPI, enum_cls, value):
        from System import Enum as DotNetEnum

        if enum_cls is PsfSamplingPy:
            name = normalize_sampling_name(value.value)
            zos_enum = ZOSAPI.Analysis.Settings.Psf.PsfSampling
        elif enum_cls is PsfRotationPy:
            name = value.value
            zos_enum = ZOSAPI.Analysis.Settings.Psf.PsfRotation
        elif enum_cls is FftPsfTypePy:
            name = value.value
            zos_enum = ZOSAPI.Analysis.Settings.Psf.FftPsfType
        else:
            raise ValueError("Unsupported enum class")

        names = list(DotNetEnum.GetNames(zos_enum))
        if name not in names and enum_cls is PsfSamplingPy:
            rev_alias = {v: k for k, v in SAMPLING_ALIASES.items()}
            alt = rev_alias.get(name, name)
            if alt in names:
                name = alt
        if name not in names:
            name = names[0]
        return DotNetEnum.Parse(zos_enum, name)

    @staticmethod
    def _zos_to_py_sampling(name: str) -> PsfSamplingPy:
        norm = normalize_sampling_name(name)
        return PsfSamplingPy[norm]

    # ---------- factory: snapshot from live analysis/settings ----------
    @classmethod
    def from_analysis(cls, analysis) -> "PSFSettings":
        s = cls._get_casted_settings(analysis)
        smp = cls._zos_to_py_sampling(s.SampleSize.ToString())
        out = cls._zos_to_py_sampling(s.OutputSize.ToString())
        rot = PsfRotationPy[s.Rotation.ToString()]
        typ = FftPsfTypePy[s.Type.ToString()]

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
            s,
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

    @classmethod
    def from_settings(cls, ias_settings) -> "PSFSettings":
        """Same as from_analysis but accepts an IAS_* settings object directly."""
        s = cls._get_casted_settings(ias_settings)
        return cls.from_analysis(s)

    # ---------- apply current Python fields back to live ZOSAPI settings ----------
    def apply(self, ZOSAPI) -> None:
        target = self._get_casted_settings(self._ias)
        target.SampleSize = self._py_to_zos_enum(ZOSAPI, PsfSamplingPy, self.sample_size)
        target.OutputSize = self._py_to_zos_enum(ZOSAPI, PsfSamplingPy, self.output_size)
        target.Rotation   = self._py_to_zos_enum(ZOSAPI, PsfRotationPy, self.rotation)
        target.Type       = self._py_to_zos_enum(ZOSAPI, FftPsfTypePy, self.psf_type)
        target.ImageDelta = float(self.image_delta)
        target.UsePolarization = bool(self.use_polarization)
        target.Normalize = bool(self.normalize)
        try:
            if self.field is None:
                ZOSField.wrap(target.Field).use_all()
            else:
                ZOSField.wrap(target.Field).set(self.field)
        except Exception:
            pass

        if self.wavelength is not None:
            try:
                ZOSWavelength.wrap(target.Wavelength).set(self.wavelength)
            except Exception:
                pass

        if self.image_surface is not None:
            try:
                ZOSSurface.wrap(target.Surface).set(self.image_surface)
            except Exception:
                pass

    # ---------- utility ----------
    def __str__(self) -> str:
        return (
            "PSF settings:(\n"
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

from __future__ import annotations
import sys
import logging
from pathlib import Path
from typing import Optional, Any
from allytools.win import DetectOut, detect_into, require_paths
from core import zemax_exceptions, zemax_dlls, ZEMAX_REGISTRY_CANDIDATES


try:
    import System  # pythonnet: CLR exceptions live here
except Exception:  # pragma: no cover – not fatal if missing
    System = None  # type: ignore

logger = logging.getLogger(__name__)


class ZemaxStandAlone:
    def __init__(self) -> None:
        self._zosapi_loaded: bool = False
        self._connection_established: bool = False
        self._closed: bool = False
        self.ZOSAPI_connection: Any = None
        self.ZOSAPI: Any = None
        self.TheApplication: Any = None
        self.TheSystem: Any = None
        self.zemax_dir: Optional[Path] = None
        self.zemax_reg: DetectOut = DetectOut()
        self.license_type: Optional[str] = None

    def __enter__(self) -> "ZemaxStandAlone":
        if not self._zosapi_loaded:
            logger.debug("Auto-initializing inside __enter__")
            self.initialize()
        if not self._connection_established:
            logger.debug("Auto-connecting inside __enter__")
            self.connect(create_if_needed=True)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close(shutdown_net=False)

    def start(self, install_dir: Optional[Path] = None, create_if_needed: bool = True) -> "ZemaxStandAlone":
        return self.initialize(install_dir).connect(create_if_needed)

    def require(self) -> "ZemaxStandAlone":
        if detect_into(ZEMAX_REGISTRY_CANDIDATES, self.zemax_reg):
            logger.debug("Zemax registry detected at: %s", self.zemax_reg.path)
            return self
        tried = "\n  - " + "\n  - ".join(map(str, ZEMAX_REGISTRY_CANDIDATES))
        raise zemax_exceptions.ZemaxNotFound("Zemax/OpticStudio not found in registry. Tried:" + tried)

    def _get_net_helper_path(self) -> Path:
        self.require()
        p = Path(self.zemax_reg.path) / zemax_dlls.NET_HELPER_SUFFIX
        require_paths(p)
        logger.debug("Using ZOSAPI NetHelper at: %s", p)
        return p

    def initialize(self, install_dir: Optional[Path] = None) -> "ZemaxStandAlone":
        if self._zosapi_loaded:
            logger.debug("initialize() skipped: already loaded")
            return self
        import clr
        net_helper_path = self._get_net_helper_path()
        clr.AddReference(str(net_helper_path)) # type: ignore
        import ZOSAPI_NetHelper  # type: ignore
        ok = (ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize()
              if install_dir is None
              else ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize(str(install_dir)))
        if not ok:
            raise zemax_exceptions.ZemaxInitError("ZOSAPI_Initializer.Initialize(...) returned False.")
        zemax_dir_str = ZOSAPI_NetHelper.ZOSAPI_Initializer.GetZemaxDirectory()
        if not zemax_dir_str:
            raise zemax_exceptions.ZemaxInitError("GetZemaxDirectory() returned empty path.")
        self.zemax_dir = Path(zemax_dir_str)
        logger.info("Zemax directory: %s", self.zemax_dir)

        clr.AddReference(str(self.zemax_dir / zemax_dlls.ZOSAPI_DLL_NAME)) # type: ignore
        clr.AddReference(str(self.zemax_dir / zemax_dlls.ZOSAPI_IF_DLL_NAME)) # type: ignore

        self._zosapi_loaded = True
        self._closed = False
        return self

    def connect(self, create_if_needed: bool = True) -> "ZemaxStandAlone":
        if not self._zosapi_loaded:
            raise zemax_exceptions.ZemaxInitError("Call initialize() before connect().")

        import ZOSAPI  # type: ignore

        self.ZOSAPI = ZOSAPI
        self.ZOSAPI_connection = ZOSAPI.ZOSAPI_Connection()
        if self.ZOSAPI_connection is None:
            logger.error("ZOSAPI_Connection() returned None")
            raise zemax_exceptions.ZemaxConnectError("Unable to initialize .NET connection to ZOSAPI.")

        app = None
        if not create_if_needed:
            try:
                app = self.ZOSAPI_connection.ConnectToApplication()
                logger.info("Connected to existing OpticStudio instance.")
            except Exception as e:
                logger.debug("No existing OpticStudio instance found: %r", e)

        if app is None:
            app = self.ZOSAPI_connection.CreateNewApplication()
            logger.info("Created new OpticStudio instance.")

        if app is None:
            raise zemax_exceptions.ZemaxInitializationError("Unable to acquire ZOSAPI application.")

        if not app.IsValidLicenseForAPI:
            status = getattr(app, "LicenseStatus", "Unknown")
            raise zemax_exceptions.ZemaxLicenseError(f"License is not valid for ZOSAPI use (status={status}).")

        self.TheApplication = app
        self.TheSystem = app.PrimarySystem
        if self.TheSystem is None:
            raise zemax_exceptions.ZemaxSystemError("Unable to acquire Primary system.")

        self._connection_established = True
        self.license_type = self._get_license_type()
        logger.info("Connected; license=%s", self.license_type)
        return self

    def close(self, shutdown_net: bool = False) -> None:
        if getattr(self, "_closed", False):
            logger.debug("close() skipped: already closed")
            return

        app = self.TheApplication
        try:
            if app is not None:
                try:
                    close_fn = getattr(app, "CloseApplication")
                except AttributeError:
                    close_fn = None

                if callable(close_fn):
                    try:
                        close_fn()
                        logger.info("OpticStudio application closed.")
                    except (RuntimeError, OSError) as e:
                        logger.warning("CloseApplication raised a runtime/OS error: %s", e)
                    except Exception as e:
                        if System is not None and isinstance(e, System.Exception):  # type: ignore[attr-defined]
                            logger.warning("CloseApplication raised a CLR exception: %s", e)
                        else:
                            # Re-raise unexpected Python exceptions
                            raise
                else:
                    logger.debug("TheApplication.CloseApplication not available; skipping.")
        finally:
            self.TheSystem = None
            self.TheApplication = None
            self.ZOSAPI_connection = None
            self._connection_established = False
            self._closed = True

            if shutdown_net:
                try:
                    import ZOSAPI_NetHelper  # type: ignore
                    ZOSAPI_NetHelper.ZOSAPI_Initializer.Shutdown()
                    self._zosapi_loaded = False
                    logger.info("ZOSAPI runtime shutdown completed.")
                except Exception as e:
                    logger.debug("ZOSAPI_Initializer.Shutdown() failed: %s", e)

    def __del__(self) -> None:
        try:
            if sys.is_finalizing():
                return
            try:
                self.close(shutdown_net=False)
            except Exception:
                try:
                    logger.warning("Suppressed exception during __del__ while closing", exc_info=True)
                except Exception:
                    pass
        except Exception:
            pass

    def open_file(self, filepath: Path, save_if_needed: bool) -> None:
        if self.TheSystem is None:
            raise zemax_exceptions.ZemaxSystemError(f"Unable to open file; system is not available. Path={filepath}")
        path = Path(filepath)
        if not path.exists():
            raise zemax_exceptions.ZemaxSystemError(f"LoadFile failed: file not found: {path}")
        ok = self.TheSystem.LoadFile(str(path), bool(save_if_needed))
        if not ok:
            raise zemax_exceptions.ZemaxSystemError(f"LoadFile failed: {path}")

    def close_file(self, save: bool) -> None:
        if self.TheSystem is None:
            raise zemax_exceptions.ZemaxSystemError("There is no system loaded.")
        try:
            if save:
                try:
                    self.TheSystem.Save()
                except Exception:
                    pass
            self.TheSystem.Close(bool(save))
        except Exception as e:
            raise zemax_exceptions.ZemaxSystemError(f"Close failed: {e}") from e

    def sample_dir(self) -> Path:
        if self.TheApplication is None:
            raise zemax_exceptions.ZemaxSystemError("Application not available; call connect() first.")
        p = Path(self.TheApplication.SamplesDir)
        if not p.exists():
            raise zemax_exceptions.ZemaxSystemError(f"Samples directory does not exist: {p}")
        return p


    def _get_license_type(self) -> str:
        if self.TheApplication is None or self.ZOSAPI is None:
            return "Unknown"
        status = self.TheApplication.LicenseStatus
        try:
            ls = self.ZOSAPI.LicenseStatusType
            mapping = {
                getattr(ls, "PremiumEdition", None): "Premium",
                getattr(ls, "ProfessionalEdition", None): "Professional",
                getattr(ls, "StandardEdition", None): "Standard",
                getattr(ls, "NoLicense", None): "NoLicense",
                getattr(ls, "Invalid", None): "Invalid",
            }
            return mapping.get(status, "Unknown")
        except Exception:
            return "Unknown"

    @property
    def is_initialized(self) -> bool:
        return self._zosapi_loaded

    @property
    def is_connected(self) -> bool:
        return self._connection_established

    def __repr__(self) -> str:
        return (
            f"<ZemaxStandAlone initialized={self._zosapi_loaded} "
            f"connected={self._connection_established} closed={self._closed} "
            f"license={self.license_type!r} zemax_dir={str(self.zemax_dir) if self.zemax_dir else None}>"
        )

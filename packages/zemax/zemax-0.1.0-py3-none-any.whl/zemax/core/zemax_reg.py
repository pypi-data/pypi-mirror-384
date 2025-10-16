import sys
from allytools.win import RegistryLocation
from typing import Final

try:
    import winreg
except ImportError:
    winreg = None

if sys.platform == "win32" and winreg is not None:
    ZEMAX_REGISTRY_CANDIDATES: Final[tuple["RegistryLocation", ...]] = (
        RegistryLocation(winreg.HKEY_CURRENT_USER, r"Software\Zemax", "ZemaxRoot", winreg.KEY_WOW64_64KEY),
        RegistryLocation(winreg.HKEY_CURRENT_USER, r"Software\Zemax", "ZemaxRoot", winreg.KEY_WOW64_32KEY),
        RegistryLocation(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Zemax", "ZemaxRoot", winreg.KEY_WOW64_64KEY),
        RegistryLocation(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Zemax", "ZemaxRoot", winreg.KEY_WOW64_32KEY),
    )
else:
    ZEMAX_REGISTRY_CANDIDATES: Final[tuple] = ()
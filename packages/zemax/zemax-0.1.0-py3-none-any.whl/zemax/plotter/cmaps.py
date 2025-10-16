from enum import Enum
from typing import Union
from matplotlib.colors import Colormap
import matplotlib.pyplot as plt


class CMaps(str, Enum):
    GRAY = "gray"
    INFERNO = "inferno"
    PLASMA = "plasma"
    VIRIDIS = "viridis"
    HOT = "hot"
    JET = "jet"
    CIVIDIS = "cividis"
    COOLWARM = "coolwarm"


def resolve_cmap(cmap: Union[str, Colormap, CMaps]) -> Colormap:
    """Convert a string, Matplotlib Colormap, or CMaps enum to a Matplotlib Colormap object."""
    if isinstance(cmap, Colormap):
        # Already a colormap instance
        return cmap

    if isinstance(cmap, CMaps):
        # If an enum, get its string value ("viridis", "jet", etc.)
        return plt.get_cmap(cmap.value)

    if isinstance(cmap, str):
        # If a plain string, assume it is a valid Matplotlib colormap name
        return plt.get_cmap(cmap)

    raise TypeError(f"Unsupported cmap type: {type(cmap)}")

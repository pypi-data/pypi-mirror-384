from dataclasses import dataclass
from typing import Optional, Tuple, Union, Any
from matplotlib.colors import Colormap
from .cmaps import CMaps
from allytools.units import Length

@dataclass(frozen=True)
class PlotParams:
    size_in: Tuple[float, float] = (4.0, 4.0)
    dpi: int = 150
    use_levels: bool = True
    n_levels: int = 100
    cmap: Union[str, Colormap, CMaps] = "jet"
    with_colorbar: bool = True
    hide_ticks: bool = True
    annotate_xy: Optional[Tuple[float, float]] = None  # if set, hides ticks and shows "(x,y)" below
    labelX: Optional[str] = None
    labelY: Optional[str] = None
    plot_label: Optional[str] = None
    value_label: Optional[str] = None
    v_min: Optional[float] = None
    v_max: Optional[float] = None
    pixel_size: Optional[Length] = None
    sensor_grid: bool = False
    sensor_grid_color: Any = (1, 1, 1, 0.5)



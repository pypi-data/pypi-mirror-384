from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, Union, Any
from imagera.plotter.cmap import CMaps
from matplotlib.colors import Colormap

Number = float
Percentile = str

@dataclass(frozen=True)
class PlotParams:
    size_in: Tuple[float, float] = (4.0, 4.0)
    dpi: int = 150
    use_levels: bool = True
    n_levels: int = 100
    cmap: Union[str, Colormap, CMaps] = CMaps.JET
    with_colorbar: bool = False
    hide_ticks: bool = True
    interpolation: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    value_label: Optional[str] = None
    plot_label: Optional[str] = None
    v_min: Optional[Union[Number, Percentile]] = None
    v_max: Optional[Union[Number, Percentile]] = None
    extent: Optional[Tuple[float, float, float, float]] = None
    show_grid: bool = False
    grid_pitch: Optional[float] = None
    grid_color: Any = (1, 1, 1, 0.4)

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Colormap, BoundaryNorm, Normalize
from typing import Optional, Union, Tuple
from enum import Enum


class CMaps(str, Enum):
    GRAY = "gray"
    INFERNO = "inferno"
    PLASMA = "plasma"
    VIRIDIS = "viridis"
    HOT = "hot"
    JET = "jet"
    CIVIDIS = "cividis"
    COOLWARM = "coolwarm"


def resolve_cmap(cmap: Union[str, Colormap, CMaps],
                 *,
                 values: Optional[np.ndarray] = None,
                 vmin: Optional[float] = None,
                 vmax: Optional[float] = None,
                 use_levels: bool = False,
                 n_levels: int = 100) -> Tuple[Colormap, Optional[Normalize]]:
    """
    Unified color and normalization resolver.

    Returns (cmap, norm)
    - cmap: matplotlib Colormap
    - norm: matplotlib Normalize or BoundaryNorm
    """
    # 1️⃣ Resolve the actual colormap
    if isinstance(cmap, CMaps):
        cmap = cmap.value
    if isinstance(cmap, str):
        cmap = plt.get_cmap(cmap)

    # 2️⃣ Early return if no data (just the colormap)
    if values is None:
        return cmap, None

    # 3️⃣ Resolve limits
    finite = values[np.isfinite(values)]
    if vmin is None or vmax is None:
        if finite.size:
            if vmin is None: vmin = float(np.min(finite))
            if vmax is None: vmax = float(np.max(finite))
        else:
            vmin, vmax = 0.0, 1.0
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmax <= vmin:
        vmin, vmax = 0.0, 1.0

    # 4️⃣ Build normalization
    if use_levels:
        n_levels = max(2, int(n_levels))
        levels = np.linspace(vmin, vmax, n_levels)
        norm = BoundaryNorm(levels, ncolors=getattr(cmap, "N", 256), clip=True)
    else:
        norm = Normalize(vmin=vmin, vmax=vmax)

    return cmap, norm

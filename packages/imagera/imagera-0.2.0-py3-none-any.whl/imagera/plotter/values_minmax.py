import numpy as np
from typing import Tuple, Optional, Union

Number = Union[int, float]

def resolve_limits_from_params(
    values: np.ndarray,
    pmin: Optional[Union[Number, str]],
    pmax: Optional[Union[Number, str]],
    *,
    fallback: Tuple[float, float] = (0.0, 1.0),
) -> Tuple[float, float]:
    """
    Resolve vmin/vmax given numeric or percentile string specs.
    - pmin/pmax can be numbers or strings like 'p1', 'p99.5'.
    - Percentiles are computed from finite data only.
    - Returns a safe (vmin, vmax) with vmax > vmin.
    """
    finite = values[np.isfinite(values)]
    vmin: Optional[float] = float(pmin) if isinstance(pmin, (int, float)) else None
    vmax: Optional[float] = float(pmax) if isinstance(pmax, (int, float)) else None

    # Collect percentile queries in one shot
    qs: list[float] = []
    idx: list[str] = []  # 'min' or 'max'

    if vmin is None and isinstance(pmin, str) and pmin.lower().startswith("p") and len(pmin) > 1:
        q = float(pmin[1:])
        q = min(100.0, max(0.0, q))
        qs.append(q); idx.append("min")

    if vmax is None and isinstance(pmax, str) and pmax.lower().startswith("p") and len(pmax) > 1:
        q = float(pmax[1:])
        q = min(100.0, max(0.0, q))
        qs.append(q); idx.append("max")

    if qs and finite.size:
        qs_vals = np.percentile(finite, qs)
        # If only one percentile requested, qs_vals is scalar
        if np.isscalar(qs_vals):
            qs_vals = [float(qs_vals)]
        for tag, val in zip(idx, qs_vals):
            if tag == "min":
                vmin = float(val)
            else:
                vmax = float(val)

    # Fallbacks if still None
    if finite.size:
        if vmin is None:
            vmin = float(np.min(finite))
        if vmax is None:
            vmax = float(np.max(finite))
    else:
        if vmin is None:
            vmin = fallback[0]
        if vmax is None:
            vmax = fallback[1]

    # Safety & ordering
    if not np.isfinite(vmin) or not np.isfinite(vmax):
        vmin, vmax = fallback
    if vmax <= vmin:
        # Nudge to a tiny positive span
        eps = max(1e-12, abs(vmin) * 1e-12)
        vmax = vmin + eps

    return vmin, vmax

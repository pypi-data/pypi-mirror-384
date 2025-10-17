from typing import Tuple

def extent_from_affine(shape: Tuple[int, int], x0: float, y0: float, sx: float, sy: float):
    ny, nx = shape
    return x0, x0 + sx * nx, y0, y0 + sy * ny

def coerce_label(val):
    if val is None: return None
    s = str(val).strip()
    return None if s == "" or s.lower() == "none" else s

def is_percentile(x) -> bool:
    return isinstance(x, str) and x.lower().startswith("p") and len(x) > 1

def parse_percentile(x: str) -> float:
    return float(x[1:]) # "p1" -> 1.0, "p99.5" -> 99.5

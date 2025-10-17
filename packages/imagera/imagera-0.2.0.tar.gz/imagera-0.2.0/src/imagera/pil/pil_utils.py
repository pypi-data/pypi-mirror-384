from __future__ import annotations
from typing import Protocol, Any, Union
import numpy as np

class RendersRGBA(Protocol):
    def render(self, **overrides: Any) -> np.ndarray: ...

def _load_pillow():
    try:
        from PIL import Image  # type: ignore
    except Exception:
        raise RuntimeError("Pillow isn't installed. Run: pip install pillow")
    return Image

def to_pil_array(rgba: np.ndarray):
    """Convert an (H,W,4) uint8 array to a PIL Image."""
    Image = _load_pillow()
    if not (isinstance(rgba, np.ndarray) and rgba.ndim == 3 and rgba.shape[-1] == 4):
        raise ValueError("Expected an (H, W, 4) uint8 array.")
    if rgba.dtype != np.uint8:
        rgba = rgba.astype(np.uint8, copy=False)
    return Image.fromarray(rgba, mode="RGBA")

def render_to_pil(renderer: RendersRGBA, **overrides: Any):
    """Call renderer.render(**overrides) and convert to PIL Image."""
    arr = renderer.render(**overrides)
    return to_pil_array(arr)

#TODO change to Path
def save_png(obj: Union[np.ndarray, RendersRGBA], path: str, **overrides: Any):
    """
    Save either:
      - a NumPy RGBA array, or
      - a renderer with .render(**overrides) -> RGBA
    to a PNG file using PIL (lazy import).
    """
    if hasattr(obj, "render"):
        im = render_to_pil(obj, **overrides)
    else:
        im = to_pil_array(obj)  # type: ignore[arg-type]
    im.save(path)

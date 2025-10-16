import numpy as np

def is_valid_image(array: np.ndarray) -> bool:
    if array.ndim < 2: # Check if an array is at least 2D
        return False
    if array.dtype not in [np.uint8, np.float32, np.uint16]:
        return False
    if array.ndim == 2:  # Grayscale
        return True
    elif array.ndim == 3 and array.shape[2] in [3, 4]:  # RGB or RGBA
        return True
    return False
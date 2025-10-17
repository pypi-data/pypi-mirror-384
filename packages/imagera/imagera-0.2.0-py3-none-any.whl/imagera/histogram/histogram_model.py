import numpy as np
import  cv2

class HistogramModel:
    def __init__(self, _image:np.array):
        self.image = _image
        self.bit_depth = self._get_bit_depth()
        self.histogram = self._get_histogram()
        self.max_value = self.histogram.max()
        self.max_bin = np.argmax(self.histogram)

    def get_peak(self):
        pass

    def _get_bit_depth(self) -> int:
        return self.image.dtype.itemsize * 8

    def _get_histogram(self) -> np.ndarray:
        bins = 2 ** self.bit_depth
        range_max = 2 ** self.bit_depth
        return cv2.calcHist([self.image], [0], None, [bins], [0, range_max]).flatten() # TODO check channels

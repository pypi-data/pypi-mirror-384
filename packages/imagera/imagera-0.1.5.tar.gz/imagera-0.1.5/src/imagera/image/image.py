import numpy as np
from argparse import ArgumentTypeError
import cv2
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QImage
from Image.image_aid import is_valid_image


class Image:
    def __init__(self, raw_image:np.array): #TODO ImageType as parameter
        if is_valid_image(raw_image):
            self._raw_image = raw_image
            #self.image_type = image_type
        else:
            raise ArgumentTypeError("numpy array is not an image")


    def get_np_array(self):
        return self._raw_image

    def shape(self):
        if self._raw_image is not None:
            return self._raw_image.shape
        return None

    def get_qsize(self):
        qsize = QSize(self.shape()[1], self.shape()[0])
        return  qsize

    def get_qimage(self) -> QImage:
        if self._raw_image.ndim == 2:  # Grayscale
            height, width = self._raw_image.shape
            bytes_per_line = width  # 1 byte per pixel
            qimage = QImage(self._raw_image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
        elif self._raw_image.ndim == 3:  # Color (BGR or RGB)
            height, width, channels = self._raw_image.shape
            bytes_per_line = 3 * width  # 3 bytes per pixel (RGB)
            if channels == 3:  # Assume BGR from OpenCV, convert to RGB
                rgb_image = cv2.cvtColor(self._raw_image, cv2.COLOR_BGR2RGB)
                qimage = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            else:
                raise ValueError("Unsupported channel size: Must be 1 or 3.")
        else:
            raise ValueError("Unsupported image format!")
        return qimage
import numpy as np
from imagekit.Image.image import Image

class Display:
    def __init__(self, _image:np.array):
        #TODO add valid check from above
        self._root_image = Image(raw_image=_image)
        self.root_qsize = self._root_image.get_qsize()
        self.qimage = self._root_image.get_qimage()
        self.annotate_images = []

    def add_annotate_image(self, image:Image):
        self.annotate_images.append(image)

    def clean_annotate_image(self):
        self.annotate_images.clear()
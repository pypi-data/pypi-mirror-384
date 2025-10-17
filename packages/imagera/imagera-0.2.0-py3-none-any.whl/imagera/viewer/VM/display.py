from PyQt5.QtCore import QObject, pyqtSignal, QSize,QPoint
from PyQt5.QtGui import QPixmap
from imagekit.Viewer.Model.display import Display
import numpy as np

class DisplayVM(QObject):
    image_ready = pyqtSignal()
    label_size_changed = pyqtSignal(QSize)
    notify_viewport = pyqtSignal(float, QPoint)
    display_changed = pyqtSignal(float, QPoint)

    def __init__(self):
        super().__init__()
        self.display_changed.connect(lambda zoom, delta: self.notify_viewport.emit(zoom, delta))
        self.label_size_changed.connect(self.update_label_size)
        self.pixmap_image = None
        self.model = None

    def new_image(self, _image: np.array):
        self.model = Display(_image)  # TODO what happened with previous model?
        self.pixmap_image = QPixmap.fromImage(self.model.qimage)
        self.update_display()

    def reset(self):
        self.pixmap_image = QPixmap.fromImage(self.model.qimage)
        self.model.clean_annotate_image()
        self.update_display()

    def update_label_size(self, size: QSize):
        self.label_size = size

    def update_display(self):
        self.delta = QPoint(0, 0)  # TODO what happened with previous model?
        self.zoom = 1.0
        self.isFit = True
        self.image_ready.emit()
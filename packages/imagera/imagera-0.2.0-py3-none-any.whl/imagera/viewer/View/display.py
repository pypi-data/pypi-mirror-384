from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from imagekit.Viewer.View.display_label import DisplayLabel

class DisplayView(QWidget):
    def __init__(self, vm):
        super().__init__()
        self.vm = vm
        self.vm.image_ready.connect(self.update_image)
        layout = QVBoxLayout(self)
        self.image_label = DisplayLabel(self.vm)
        self.image_label.display_changed.connect(self.vm.display_changed)
        self.image_label.setObjectName("image_label")
        self.label_size = QSize(self.image_label.width(), self.image_label.height())
        #self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        #self.image_label.setAlignment(Qt.AlignCenter)
        #self.image_label.setStyleSheet("background-color: lightgray;")
        layout.addWidget(self.image_label)
        #layout.setContentsMargins(10, 10, 10, 10)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def resizeEvent(self, event):
        super().resizeEvent(event) # Call the base class implementation
        new_size = self.image_label.size()
        self.vm.label_size_changed.emit(new_size)

    def update_image(self):
        pixmap_image = self.vm.pixmap_image
        zoom = self.vm.zoom
        delta = self.vm.delta
        fit = self.vm.isFit
        self.image_label.transform_image(pixmap_image=pixmap_image, zoom_factor=zoom, delta=delta, fit= fit)





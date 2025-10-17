from PyQt5.QtGui import QPixmap,  QPainter
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QPoint

class DisplayLabel(QLabel):
    display_changed = pyqtSignal(float, QPoint)
    def __init__(self, display_vm):
        super().__init__()
        self.display_vm = display_vm
        self.setMouseTracking(True)  # Enable mouse tracking without pressing any buttons
        self.start_pos = None  # Store the initial mouse press position
        self.zoom = 1.0
        self.delta = QPoint(0,0)
        self.offset_x = 0
        self.offset_y = 0
        self.mouse_delta = QPoint(0,0)
        self.pixmap = None

    def transform_image(self, pixmap_image: QPixmap, zoom_factor: float, delta:QPoint, fit:bool):
        self.pixmap = pixmap_image
        self.fit = fit
        if self.fit:
            self.zoom = self.fitted_zoom()
        else:
            self.zoom = zoom_factor
        self.delta = delta
        self.display_changed.emit(self.zoom, self.delta)
        self.update()  # Triggers paintEvent()

    def paintEvent(self, event):
        super().paintEvent(event)  # Call the base class paintEvent
        if self.pixmap:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)  # Smooth scaling
            label_width = self.width()
            label_height = self.height()
            pixmap_width = self.pixmap.width()
            pixmap_height = self.pixmap.height()
            default_x = (label_width / self.zoom - pixmap_width)  / 2
            default_y = (label_height /self.zoom - pixmap_height) / 2
            offset_x = (default_x + self.delta.x() / self.zoom)
            offset_y = (default_y + self.delta.y() / self.zoom)
            painter.scale(self.zoom, self.zoom)
            painter.drawPixmap(int(offset_x), int(offset_y), self.pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_click_on_image(event.pos()):
            self.start_pos = event.pos()  - self.delta

    def mouseMoveEvent(self, event):
        pass
        if self.start_pos is not None:
            current_pos = event.pos()   #Get the current mouse position
            self.mouse_delta = current_pos - self.start_pos #Calculate movement in X and Y

            self.transform_image(pixmap_image = self.pixmap, zoom_factor = self.zoom, delta = self.mouse_delta, fit = False)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.mouse_delta:
                self.delta = self.mouse_delta #Save achieved offset, only if it was some movement
            self.mouse_delta = QPoint(0,0)
            self.start_pos = None

    def wheelEvent(self, event):
        angle_delta = event.angleDelta()
        delta_y = angle_delta.y()
        factor = 0.1
        if delta_y > 0:
            self.zoom = self.zoom + factor
        elif delta_y < 0:
            self.zoom = self.zoom  - factor
        self.transform_image(pixmap_image=self.pixmap,
                             zoom_factor=self.zoom,
                             delta=QPoint(int(self.offset_x), int(self.offset_y)),
                             fit=False)

    def fitted_zoom(self) -> float:
        image_width = self.pixmap.width()
        image_height = self.pixmap.height()
        label_width = self.width()
        label_height = self.height()
        scale_w = label_width / image_width
        scale_h = label_height / image_height
        zoom_factor = min(scale_w, scale_h)
        return zoom_factor

    def is_click_on_image(self, click_pos: QPoint) -> bool:
        image_width = self.pixmap.width() * self.zoom
        image_height = self.pixmap.height() * self.zoom
        label_width, label_height = self.width(), self.height()
        image_x = (label_width - image_width) / 2 + self.delta.x()
        image_y = (label_height - image_height) / 2 + self.delta.y()
        return (
            image_x <= click_pos.x() <= image_x + image_width
            and image_y <= click_pos.y() <= image_y + image_height
        )
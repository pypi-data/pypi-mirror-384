from PyQt5.QtCore import QObject, pyqtSignal
from imagekit.Viewer.Model.view_port import ViewPort

class ViewPortVM(QObject):
    change_to_viewport = pyqtSignal()

    def __init__(self, display_vm):
        super().__init__()
        self.display_vm = display_vm
        self.display_vm.notify_viewport.connect(self.changes_from_display)
        self._is_updating_from_view = False
        self.model =  ViewPort(zoom = 1, delta= (0, 0), fit_to_screen=True, centered=True, reset=True)

    def changes_from_display(self, zoom, delta):
        if not self._is_updating_from_view:
            self.model.delta = delta
            self.model.zoom = zoom
            self.display_vm.delta = delta
            self.display_vm.zoom = zoom
            self.change_to_viewport.emit()  # update zoom view value

    def get_zoom(self):
        return self.model.zoom

    def fit_clicked(self):
        self.display_vm.isFit = True
        self.delta_zero() # reset the offset
        self.display_vm.image_ready.emit()

    def set_offset(self, delta):
        self.display_vm.isFit = False
        self.model.delta = delta
        self.display_vm.image_ready.emit()

    def set_zoom(self, zoom):
        self.display_vm.isFit = False
        self._is_updating_from_view = True
        if self.model.zoom != zoom:
            self.model.zoom = zoom
        self.display_vm.zoom = zoom
        self._is_updating_from_view = False
        self.display_vm.image_ready.emit()

    def delta_zero(self):
        self.model.delta.setX(0)
        self.model.delta.setY(0)
        self.display_vm.delta.setX(0)
        self.display_vm.delta.setY(0)



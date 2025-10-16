from PyQt5.QtCore import QObject, pyqtSignal
from imagekit.Viewer.VM.view_port import ViewPortVM
from imagekit.Viewer.VM.info import InfoVM

class ControlVM(QObject):
    visibility = pyqtSignal(bool)
    def __init__(self, _display_vm):
        super().__init__()
        self.display_vm = _display_vm
        self.view_port_vm = ViewPortVM(self.display_vm)
        self.info_vm = InfoVM()

    def image_loaded(self):
        self.visibility.emit(True)

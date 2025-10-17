from PyQt5 import QtWidgets
from imagekit.Viewer.View.view_port import ViewPort
from imagekit.Viewer.View.info import Info

class Control(QtWidgets.QWidget):
    def __init__(self,vm) :
        super().__init__()
        self.vm = vm
        self.vm.visibility.connect(self.visibility_changed)
        self.view_port = ViewPort(self.vm.view_port_vm)
        self.info = Info(self.vm.info_vm)
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.view_port)
        self.layout.addWidget(self.info)
        self.setLayout(self.layout)

    def visibility_changed(self, vis: bool):
        self.setVisible(vis)
        self.setEnabled(vis)  # Enable or disable interactivity
        if vis:
            self.setStyleSheet("")  # Reset to default style when visible
        else:
            self.setStyleSheet("background: transparent; border: none;")







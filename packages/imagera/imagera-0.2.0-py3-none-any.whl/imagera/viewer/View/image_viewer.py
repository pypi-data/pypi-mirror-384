from PyQt5.QtWidgets import QWidget, QVBoxLayout,QSizePolicy
from imagekit.Viewer.View.display import DisplayView
from imagekit.Viewer.View.control import Control

class ImageViewer(QWidget):
    def __init__(self, _vm, _control_size):
        super().__init__()
        self.vm = _vm
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.display = DisplayView(self.vm.display_vm)
        self.control = Control(self.vm.control_vm)
        self.display.setStyleSheet("border: 1px solid black;")
        self.display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.display, stretch=1)
        layout.addWidget(self.control, stretch=0)
        #layout.addWidget(self.display)
        #   layout.addWidget(self.control)
        self.control.setFixedHeight(_control_size)
        self.control.setStyleSheet("background: transparent; border: none;")
        self.control.setDisabled(True)
        self.control.setVisible(True)

        self.setLayout(layout)







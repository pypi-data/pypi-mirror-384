from PyQt5 import QtWidgets
from imagekit.Viewer.View.zoom import Zoom
from imagekit.Viewer.View.fit import Fit

class ViewPort(QtWidgets.QWidget):
    def __init__(self,vm) :
        super().__init__()
        self.vm = vm
        self.layout = QtWidgets.QHBoxLayout()
        self.zoom = Zoom(self.vm)
        self.fit = Fit(self.vm)
        self.layout.addWidget(self.zoom)
        self.layout.addWidget(self.fit)
        self.layout.addStretch(1)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def visibility_changed(self, vis: bool):
        self.setVisible(vis)








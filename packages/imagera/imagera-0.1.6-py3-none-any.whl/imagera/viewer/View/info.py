from PyQt5 import QtWidgets

class Info(QtWidgets.QWidget):
    def __init__(self,vm) :
        super().__init__()
        self.vm = vm
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)


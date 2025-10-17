from PyQt5 import QtWidgets, QtCore
from aidkit.button.new_buton import new_button

class Fit(QtWidgets.QWidget):
    def __init__(self, viewport_vm):
        super().__init__()
        self.viewport_vm = viewport_vm
        self.layout = QtWidgets.QHBoxLayout()
        self.fit_button = new_button(self.layout, "F", self.button_clicked, True)
        self.fit_button.setFixedSize(50,50)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def button_clicked(self):
        self.viewport_vm.fit_clicked()





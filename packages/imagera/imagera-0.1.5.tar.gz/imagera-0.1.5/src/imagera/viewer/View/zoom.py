from PyQt5 import QtWidgets, QtCore

def set_zoom(value):
    return int(value * 100.0)
def get_zoom(value):
    return value / 100.0

class Zoom(QtWidgets.QWidget):
    def __init__(self, viewport_vm):
        super().__init__()
        self.viewport_vm = viewport_vm
        self.viewport_vm.change_to_viewport.connect(self.update_value)
        self.layout = QtWidgets.QHBoxLayout()
        self.zoom_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(500)
        self.zoom_slider.setTickInterval(50)
        self.zoom_slider.setSingleStep(10)
        self.zoom_slider.setFixedWidth(250) #TODO
        self.zoom_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.zoom_slider.valueChanged.connect(self.on_slider_value_changed)
        self.label = QtWidgets.QLabel(f"{self.zoom_slider.value()}%")
        self.layout.addWidget(self.zoom_slider)
        self.layout.addWidget(self.label)
        self.layout.addStretch()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def update_value(self):
        new_value = set_zoom(self.viewport_vm.get_zoom())
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(new_value)
        self.zoom_slider.blockSignals(False)
        self.label.setText(f"{self.zoom_slider.value()}%")

    def on_slider_value_changed(self, value):
        self.label.setText(f"{value}%")
        self.viewport_vm.set_zoom(get_zoom(value))





from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class HistogramView(QWidget):
    def __init__(self, _vm):
        super().__init__()
        self.vm = _vm
        self.vm.vm_updated.connect(self.update_view)
        layout = QVBoxLayout()
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def update_view(self):
        self._draw_histogram()

    def _draw_histogram(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Plot histogram
        ax.plot(self.vm.histogram, color='blue')

        # Draw vertical line at peak
        peak_bin = self.vm.max_bin
        peak_value = self.vm.max_value
        ax.axvline(peak_bin, color='red', linestyle='--', linewidth=1)

        # Annotate peak
        annotation = f"Bin: {peak_bin}\nValue: {int(peak_value)}"
        ax.text(peak_bin + 10, peak_value * 0.8, annotation,
                fontsize=8, color='red', verticalalignment='top')

        # Axis labels
        ax.set_title("Image Histogram")
        ax.set_xlabel("Pixel Intensity")
        ax.set_ylabel("Frequency")

        self.canvas.draw()

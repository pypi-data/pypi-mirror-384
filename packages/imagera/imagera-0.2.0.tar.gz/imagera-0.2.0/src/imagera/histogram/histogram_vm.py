from PyQt5.QtCore import QObject, pyqtSignal
from imagekit.Histogram.histogram_model import HistogramModel
from imagekit.events import EventTypes,ImageLoadedEvent, ResetEvent
from aidkit.event.Aggregator import EventAggregator

class HistogramVM(QObject):
    vm_updated = pyqtSignal()
    def __init__(self, event_aggregator: EventAggregator):
        super().__init__()
        self.event_aggregator = event_aggregator
        self.event_aggregator.subscribe(EventTypes.IMAGE_LOADED, self.image_loaded_received)
        self.event_aggregator.subscribe(EventTypes.RESET, self.reset_received)
        self._model = None
        self.histogram = 0
        self.max_value = 0
        self.max_bin = 0

    def image_loaded_received(self, event: ImageLoadedEvent):
        self._model = HistogramModel(event.raw_image)
        self.histogram = self._model.histogram
        self.max_value = self._model.max_value
        self.max_bin = self._model.max_bin
        self.update_view()

    def reset_received(self, event:ResetEvent):
        pass

    def update_view(self):
        self.vm_updated.emit()
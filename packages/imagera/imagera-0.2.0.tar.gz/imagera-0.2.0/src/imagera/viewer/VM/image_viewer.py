from PyQt5.QtCore import QObject
from imagekit.Viewer.VM.display import DisplayVM
from imagekit.Viewer.VM.control import ControlVM
from imagekit.events import EventTypes, ImageLoadedEvent, ResetEvent
from aidkit.event.Aggregator import EventAggregator


class ImageViewerVM(QObject):
    def __init__(self, event_aggregator: EventAggregator):
        super().__init__()
        self.event_aggregator = event_aggregator
        self.event_aggregator.subscribe(EventTypes.IMAGE_LOADED, self.image_loaded_received)
        self.event_aggregator.subscribe(EventTypes.RESET, self.reset_received)
        self.display_vm = DisplayVM()
        self.control_vm = ControlVM(self.display_vm)

    def image_loaded_received(self, event: ImageLoadedEvent):
        self.display_vm.new_image(event.raw_image)
        self.control_vm.image_loaded()

    def reset_received(self, event:ResetEvent):
        self.display_vm.reset_received()
from allytools.event import EventAggregator, BasicEvents, EventTypes

import os, cv2
import numpy as np

class ImageReader:
    def __init__(self, event_aggregator: EventAggregator):
        self.event_aggregator = event_aggregator

    def read_image_from_file(self, file_path: str) -> np.ndarray:
        if not os.path.exists(file_path):
            self._publish_error(f"File '{file_path}' does not exist.")
        image = cv2.imread(file_path,cv2.IMREAD_UNCHANGED)
        if image is None:
            self._publish_error(f"Failed to load image from '{file_path}'. The file may not be a valid image.")
        return image

    def _publish_error(self, message: str) -> None:
        self.event_aggregator.publish(
            BasicEvents.ErrorOccurredEvent(
                event_type=EventTypes.ERROR_OCCURRED,
                message=message)
        )


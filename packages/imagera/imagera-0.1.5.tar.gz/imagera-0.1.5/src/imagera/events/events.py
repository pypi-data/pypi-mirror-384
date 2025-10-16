from allytools.event import Event, EventType
from allytools.core import IterableConstants
import numpy as np
from dataclasses import dataclass

class EventTypes(IterableConstants):
    IMAGE_LOADED = EventType("IMAGE_LOADED", "Image successfully loaded -")
    RESET = EventType("RESET", "Reset to root image")

@dataclass
class ResetEvent(Event):
    pass

@dataclass
class ImageLoadedEvent(Event):
    file_path: str
    raw_image: np.array
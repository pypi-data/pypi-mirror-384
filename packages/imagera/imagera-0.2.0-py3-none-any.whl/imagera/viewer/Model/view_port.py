from PyQt5.QtCore import QPoint

class ViewPort:
    def __init__(self, zoom: float, delta:QPoint, fit_to_screen:bool, centered:bool, reset:bool):
        self.zoom = zoom
        self.delta =delta

        self.fit_to_screen = fit_to_screen
        self.centered = centered
        self.reset = reset









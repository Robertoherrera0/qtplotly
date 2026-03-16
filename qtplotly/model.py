from __future__ import annotations

from .curve import Curve
from .marker import Marker
from .themes.colors import ColorTable

class PlotModel:

    def __init__(self):

        self.curves: dict[str, Curve] = {}
        self.markers: dict[str, Marker] = {}

        self.axis_titles = {
            "x": "",
            "y1": "",
            "y2": ""
        }

        self.live_mode = False
        self.colors = ColorTable()

    def add_curve(self, name: str, axis: str = "y1", color: str | None = None):

        if name in self.curves:
            return self.curves[name]

        if color is None:
            color = self.colors.get(name)

        curve = Curve(name=name, axis=axis, color=color)
        self.curves[name] = curve
        return curve

    def remove_curve(self, name: str):

        self.curves.pop(name, None)

    def get_curve(self, name: str) -> Curve | None:

        return self.curves.get(name)

    def append_data(self, name: str, x, y):

        curve = self.curves.get(name)

        if curve is None:
            curve = self.add_curve(name)

        curve.append(x, y)

    def set_data(self, name: str, x, y):

        curve = self.curves.get(name)

        if curve is None:
            curve = self.add_curve(name)

        curve.set_data(x, y)

    def add_marker(self, name: str, x: float, color: str = "black", width: int = 1, persistent: bool = False):

        self.markers[name] = Marker(
            name=name,
            x=x,
            color=color,
            width=width,
            persistent=persistent
        )

    def remove_marker(self, name: str):

        self.markers.pop(name, None)

    def set_axis_title(self, axis: str, title: str):

        if axis not in self.axis_titles:
            raise ValueError(f"Unknown axis '{axis}'")

        self.axis_titles[axis] = title

    def clear(self):

        for curve in self.curves.values():
            curve.clear()

        # remove non-persistent markers
        self.markers = {
            name: m for name, m in self.markers.items()
            if m.persistent
        }
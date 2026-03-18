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
        self.plot_bgcolor = "#FFFFFF"

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

    def get_background_color(self):
        return self.plot_bgcolor
    def set_fit_curve(self, name, x, y, label=None):
        curve = self.model.add_curve(name)
        curve.set_data(x, y)
        curve.role = "fit"
        curve.label = label
        self.refresh()
        
    def add_marker(
        self,
        name: str,
        x: float,
        color: str | None = None,
        width: float = 1.0,
        persistent: bool = False,
        label: str | None = None,
    ) -> Marker:

        marker = self.markers.get(name)

        # --- reuse existing marker ---
        if marker is not None:

            marker.set_x(x)

            if color is not None:
                marker.set_color(color)

            if width is not None:
                marker.set_width(width)

            if label is not None:
                marker.set_label(label)

            marker.persistent = persistent

            return marker

        # --- create new marker ---
        if color is None:
            color = self.colors.get(name)

        marker = Marker(
            name=name,
            x=x,
            label=label,
            color=color,
            width=width,
            persistent=persistent,
        )

        self.markers[name] = marker
        return marker
    
    def get_marker_layout(self):
        visible_markers = [
            m for m in self.markers.values()
            if m.visible
        ]

        if not visible_markers:
            return {}

        visible_markers.sort(key=lambda m: m.x)

        layout = {}

        n = len(visible_markers)

        top = 0.95
        bottom = 0.55

        if n == 1:
            layout[visible_markers[0].name] = 0.9
            return layout

        step = (top - bottom) / (n - 1)

        for i, marker in enumerate(visible_markers):
            y = top - i * step
            layout[marker.name] = y

        return layout

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
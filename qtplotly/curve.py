import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from gans_control.ui.styles.colors import (
    get_curve_color,
    set_curve_color,
)


class PlotCurve:
    def __init__(self, name, axis="y1"):
        self.name = name
        self.x = np.array([])
        self.y = np.array([])
        self.axis = axis
        self.visible = True
        self.color = get_curve_color(name)


class PlotMarker:
    def __init__(self, label, persistent=False):
        self.label = label
        self.x = None
        self.color = "black"
        self.thickness = 1
        self.persistent = persistent


class PlotBase:
    def __init__(self):

        self.curves = {}
        self.markers = {}

        self.config = self._default_config()

        self.figure = make_subplots(
            rows=1,
            cols=1,
            specs=[[{"secondary_y": True}]]
        )

        self._initialize_layout()

    def _default_config(self):
        return {
            "x_log": False,
            "y_log": False,
            "show_grid": True,
            "use_lines": True,
            "use_markers": True,
            "line_width": 2,
            "marker_size": 6,
            "show_legend": True,
        }

    def set_data(self, x: np.ndarray, ydict: dict):

        self.curves = {}

        for name, payload in ydict.items():

            if isinstance(payload, dict):
                y = payload["y"]
                axis = payload.get("axis", "y1")
            else:
                y = payload
                axis = "y1"

            curve = PlotCurve(name, axis=axis)
            curve.x = np.asarray(x)
            curve.y = np.asarray(y)

            self.curves[name] = curve

        self._update_figure()

    def clear(self):
        self.curves = {}
        self.markers = {}
        self.figure.data = []
        self.figure.layout.shapes = []
        self.figure.layout.annotations = []

    def _initialize_layout(self):

        self.figure.update_layout(
            template="plotly_white",
            showlegend=self.config["show_legend"],
            margin=dict(l=60, r=60, t=40, b=60),
            xaxis=dict(title="", showgrid=True),
            yaxis=dict(title="", showgrid=True),
            yaxis2=dict(
                title="",
                overlaying="y",
                side="right",
                showgrid=False,
            ),
        )

    def _update_figure(self):
        self._rebuild_traces()
        self._rebuild_markers()

    def _rebuild_traces(self):

        self.figure.data = []

        for curve in self.curves.values():

            if not curve.visible:
                continue

            mode = self._build_mode()

            secondary = True if curve.axis == "y2" else False

            trace = go.Scatter(
                x=curve.x,
                y=curve.y,
                mode=mode,
                name=curve.name,
                line=dict(
                    width=self.config["line_width"],
                    color=curve.color,
                ),
                marker=dict(
                    size=self.config["marker_size"],
                    color=curve.color,
                ),
            )

            self.figure.add_trace(trace, secondary_y=secondary)

    def _build_mode(self):
        if self.config["use_lines"] and self.config["use_markers"]:
            return "lines+markers"
        elif self.config["use_lines"]:
            return "lines"
        elif self.config["use_markers"]:
            return "markers"
        else:
            return "lines"

    def set_axis_titles(self, x_title="", y1_title="", y2_title=""):

        self.figure.update_layout(
            xaxis_title=x_title,
            yaxis_title=y1_title,
            yaxis2_title=y2_title,
        )

    def add_vertical_marker(self, label, x, color="black", thickness=1, persistent=False):

        marker = PlotMarker(label, persistent=persistent)
        marker.x = x
        marker.color = color
        marker.thickness = thickness

        self.markers[label] = marker
        self._rebuild_markers()

    def _rebuild_markers(self):

        shapes = []
        annotations = []

        y_min, y_max = self._current_y_range()

        for marker in self.markers.values():

            if marker.x is None:
                continue

            shapes.append(
                dict(
                    type="line",
                    x0=marker.x,
                    x1=marker.x,
                    y0=y_min,
                    y1=y_max,
                    line=dict(color=marker.color, width=marker.thickness),
                )
            )

            annotations.append(
                dict(
                    x=marker.x,
                    y=y_max,
                    text=marker.label,
                    showarrow=False,
                    yanchor="bottom",
                )
            )

        self.figure.update_layout(
            shapes=shapes,
            annotations=annotations
        )

    def _current_y_range(self):

        all_y = []

        for curve in self.curves.values():
            if len(curve.y) > 0:
                all_y.append(curve.y)

        if not all_y:
            return 0, 1

        all_y = np.concatenate(all_y)
        return float(np.min(all_y)), float(np.max(all_y))

    def get_figure(self):
        return self.figure
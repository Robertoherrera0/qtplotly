from __future__ import annotations
import json
from pathlib import Path
import numpy as np

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .model import PlotModel
from .bridge import PlotBridge


class PlotWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model = PlotModel()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.web = QWebEngineView(self)
        self.web.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.web.setStyleSheet("border:0px; background:transparent;")

        layout.addWidget(self.web)

        self.bridge = PlotBridge(self.web)

        self._ready             = False
        self._pending_json      = None
        self._pending_fig       = None
        self._refresh_scheduled = False

        self._load_html()

        self._config = dict(
            displaylogo=False,
            responsive=True,
            displayModeBar=True,
            scrollZoom=True,
            doubleClick="reset",
            modeBarButtonsToRemove=["toImage"],
            modeBarButtonsToAdd=[
                "zoomIn2d",
                "zoomOut2d",
                "hoverCompareCartesian",
            ],
        )

    def _load_html(self):
        base = Path(__file__).parent / "resources"
        html_path = base / "plot.html"
        self.web.load(QUrl.fromLocalFile(str(html_path)))
        self.web.loadFinished.connect(self._on_loaded)

    def _on_loaded(self, ok):
        self._ready = ok
        if ok and self._pending_json:
            self._push_json(self._pending_json)
            self._pending_json = None

    # Public API
    def add_curve(self, name, axis="y1", color=None, role="data"):
        self.model.add_curve(name, axis=axis, color=color, role=role)
        self.refresh()

    def remove_curve(self, name):
        self.model.remove_curve(name)
        self.refresh()

    def set_data(self, name, x, y):
        self.model.set_data(name, x, y)
        self.refresh()

    def append_data(self, name, x, y):
        self.model.append_data(name, x, y)
        self.refresh()

    def add_vertical_marker(
        self,
        name: str,
        x: float,
        color: str = "#555555",
        width: float = 1.0,
        persistent: bool = False,
        y0: float = 0.0,
        y1: float = 1.0,
        label_y: float = 0.97,
    ):
        self.model.add_marker(
            name, x,
            color=color,
            width=width,
            persistent=persistent,
            y0=y0,
            y1=y1,
            label_y=label_y,
        )
        self.refresh()

    def remove_marker(self, name: str):
        self.model.remove_marker(name)
        self.refresh()

    def set_live_mode(self, enabled: bool):
        if self.model.live_mode != enabled:
            self.model.live_mode = enabled
            self.refresh()

    def clear(self):
        self.model.clear()
        self.refresh()

    def set_axis_title(self, axis, title):
        self.model.set_axis_title(axis, title)
        self.refresh()

    def set_plot_background(self, color: str):
        self.model.plot_bgcolor = color
        self.refresh()

    def refresh(self):
        self._pending_fig = self._build_figure()
        if not self._refresh_scheduled:
            self._refresh_scheduled = True
            QTimer.singleShot(40, self._do_refresh)

    def _do_refresh(self):
        self._refresh_scheduled = False
        if self._pending_fig is None:
            return
        fig = self._pending_fig
        self._pending_fig = None
        fig_json = fig.to_json(validate=False)
        if not self._ready:
            self._pending_json = fig_json
            return
        self._push_json(fig_json)

    def _push_json(self, fig_json):
        cfg_json = json.dumps(self._config)
        script = f"renderFigure({json.dumps(fig_json)}, {json.dumps(cfg_json)});"
        self.web.page().runJavaScript(script)
    
    def set_log_y(self, enabled: bool):
        self.model.log_y = enabled
        self.refresh()
    
    def _build_figure(self):
        fig = make_subplots(
            rows=1, cols=1,
            specs=[[{"secondary_y": True}]]
        )

        shapes      = []
        annotations = []

        for curve in self.model.curves.values():
            if not curve.visible:
                continue

            secondary = curve.axis == "y2"

            if curve.role == "fit":
                line = dict(color="red", width=2, dash="dash")
                mode = "lines"
            else:
                line = dict(width=2, color=curve.color) if curve.color else dict(width=2)
                mode = "lines+markers"

            fig.add_trace(
                go.Scatter(
                    x=curve.x,
                    y=curve.y,
                    mode=mode,
                    name=curve.name,
                    line=line,
                    marker=dict(size=6) if curve.role != "fit" else None,
                ),
                secondary_y=secondary,
            )

        for marker in self.model.markers.values():
            if not marker.visible:
                continue

            color = marker.color if marker.color else "#555555"

            shapes.append(dict(
                type="line",
                x0=marker.x, x1=marker.x,
                y0=marker.y0, y1=marker.y1,
                xref="x", yref="paper",
                line=dict(color=color, width=marker.width),
                layer="above",
            ))

            annotations.append(dict(
                x=marker.x,
                y=marker.label_y,
                xref="x", yref="paper",
                text=marker.label,
                showarrow=True,
                arrowhead=2,
                arrowsize=0.8,
                arrowwidth=1.0,
                arrowcolor=color,
                ax=0, ay=-14,
                font=dict(size=10, color=color),
                bgcolor="rgba(255,255,255,0.7)",
                borderwidth=0,
                xanchor="center",
                yanchor="bottom",
            ))

        shapes.append(dict(
            type="rect",
            xref="paper", yref="paper",
            x0=0, y0=0, x1=1, y1=1,
            line=dict(color="rgba(0,0,0,0.25)", width=1),
            fillcolor="rgba(0,0,0,0)",
            layer="below",
        ))

        visible_curves = [c for c in self.model.curves.values() if c.visible]
        show_legend    = len(visible_curves) > 1

        has_y2 = any(
            c.axis == "y2" and c.visible and c.x is not None and len(c.x) > 0
            for c in self.model.curves.values()
        )
        y2_title = self.model.axis_titles.get("y2", "")

        if self.model.live_mode:
            plot_bgcolor = "#FFF8E1"
        else:
            plot_bgcolor = self.model.get_background_color()

        fig.update_layout(
            autosize=True,
            plot_bgcolor=plot_bgcolor,
            paper_bgcolor="#FFFFFF",
            shapes=shapes,
            annotations=annotations,
            margin=dict(l=10, r=10, t=35, b=35),
            showlegend=show_legend,
            legend=dict(
                orientation="v",
                x=0.985, y=0.985,
                xanchor="right", yanchor="top",
                font=dict(size=11),
                bgcolor="rgba(255,255,255,0.8)",
                borderwidth=0,
            ),
            xaxis=dict(
                title=self.model.axis_titles["x"],
                showgrid=True,
                gridcolor="rgba(0,0,0,0.08)",
                zeroline=False,
                showline=True,
                linewidth=1,
                linecolor="rgba(0,0,0,0.25)",
                ticks="outside",
                ticklen=8,
                automargin=True,
            ),
            yaxis=dict(
                title=self.model.axis_titles["y1"],
                type="log" if getattr(self.model, "log_y", False) else "linear",
                showgrid=True,
                gridcolor="rgba(0,0,0,0.08)",
                zeroline=False,
                showline=True,
                linewidth=1,
                linecolor="rgba(0,0,0,0.25)",
                ticks="outside",
                ticklen=8,
                automargin=True,
            ),
            yaxis2=dict(
                overlaying="y",
                title=y2_title,
                side="right",
                visible=bool(has_y2 or y2_title),
                showgrid=False,
                showline=True,
                linewidth=1,
                linecolor="rgba(0,0,0,0.25)",
                ticks="outside",
                ticklen=8,
                automargin=True,
            ),
        )

        fig.update_xaxes(domain=[0, 1])
        fig.update_yaxes(domain=[0, 1])

        return fig
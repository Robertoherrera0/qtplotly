from __future__ import annotations
import json

from PySide6.QtCore import QObject, Signal, Slot


class PlotBridge:
    """
    Thin wrapper for sending commands from Qt to the
    JavaScript Plotly environment running inside QWebEngine.
    """
    def __init__(self, webview):
        self._webview = webview

    def call(self, function: str, *args):

        if not args:
            script = f"{function}();"
        else:
            payload = ",".join(json.dumps(a) for a in args)
            script = f"{function}({payload});"

        self._webview.page().runJavaScript(script)


class SelectionBridge(QObject):
    """
    Receives box-selection events from the JS/Plotly side via QWebChannel
    and re-emits them as a Qt signal for consumers of PlotWidget.
    """
    selection_made = Signal(float, float)

    @Slot(float, float)
    def onSelection(self, xmin: float, xmax: float):
        self.selection_made.emit(xmin, xmax)
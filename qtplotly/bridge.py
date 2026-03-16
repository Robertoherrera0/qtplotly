from __future__ import annotations
import json


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
from __future__ import annotations

import numpy as np
from PySide6.QtCore import QObject

from gans_control.clients.qt_data import QtDataClient


class PlotController(QObject):
    def __init__(self, plot, column_selection, parent=None):
        super().__init__(parent)

        self.plot = plot
        self.column_selection = column_selection

        self.client = QtDataClient()
        self.client.dataUpdated.connect(self._on_live_data)

        self.column_selection.selectionChanged.connect(
            self._on_selection_changed
        )

        self._live_data: np.ndarray | None = None
        self._col_index: dict[str, int] = {}
        self._current_scan: int | None = None
        self._last_npts: int = 0
        self._selection_state: dict | None = None

    def _on_live_data(self, payload: dict):

        rows = payload.get("data", [])
        columns = payload.get("columns", {})
        metadata = payload.get("metadata", {})

        if not rows or not columns:
            return

        scanno = metadata.get("scanno")
        npts = payload.get("npts", 0)

        if scanno != self._current_scan:
            self._current_scan = scanno
            self._last_npts = 0
            self.plot.clear()

        if npts == self._last_npts:
            return

        self._last_npts = npts

        ordered = sorted((int(k), v) for k, v in columns.items())
        ordered_columns = [name for _, name in ordered]

        self._live_data = np.asarray(rows)

        self._col_index = {
            name: int(k)
            for k, name in columns.items()
        }

        self.column_selection.set_columns(ordered_columns)

        if self._selection_state is None:
            self.column_selection.resetDefault()

        self._render()

    def _on_selection_changed(self, state: dict):
        self._selection_state = state
        self._render()

    def _render(self):

        if self._live_data is None:
            return

        if not self._selection_state:
            return

        x_list = self._selection_state.get("x", [])
        y1_list = self._selection_state.get("y1", [])
        y2_list = self._selection_state.get("y2", [])

        if not x_list:
            return

        x_name = x_list[0]

        if x_name not in self._col_index:
            return

        x = np.asarray(self._live_data[:, self._col_index[x_name]])

        curves = {}

        for name in y1_list:
            y = self._compute_column(name)
            if y is not None:
                curves[name] = {"y": y, "axis": "y1"}

        for name in y2_list:
            y = self._compute_column(name)
            if y is not None:
                curves[name] = {"y": y, "axis": "y2"}


        if not curves:
            return

        self.plot.set_data(x, curves)

    def _compute_column(self, name: str):

        if name in self._col_index:
            return np.asarray(
                self._live_data[:, self._col_index[name]]
            )

        if name == "det/mon":
            if "det" in self._col_index and "mon" in self._col_index:
                det = self._live_data[:, self._col_index["det"]]
                mon = self._live_data[:, self._col_index["mon"]]
                return np.asarray(det / np.maximum(mon, 1e-12))

        if name == "det/sec":
            if "det" in self._col_index and "sec" in self._col_index:
                det = self._live_data[:, self._col_index["det"]]
                sec = self._live_data[:, self._col_index["sec"]]
                return np.asarray(det / np.maximum(sec, 1e-12))

        return None

    def stop(self):
        self.client.disconnect()
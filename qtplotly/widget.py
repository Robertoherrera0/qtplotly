from __future__ import annotations

import sys
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QApplication,
    QMainWindow,
)

from qtplotly.curve import Curve
from qtplotly.makers import Marker
from qtplotly.model import PlotModel
from qtplotly.column_selection import ColumnSelection

class PlotWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._build_ui()
        self._build_controller()

    def _build_ui(self):

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.column_selection = ColumnSelectionWidget(self)
        self.plot = SpecPlot(self)

        self.column_selection.setMinimumWidth(260)

        layout.addWidget(self.column_selection)
        layout.addWidget(self.plot, stretch=1)

    def _build_controller(self):

        self.controller = PlotController(
            plot=self.plot,
            column_selection=self.column_selection,
            parent=self,
        )

    def stop(self):
        self.controller.stop()


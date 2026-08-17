import sys
import json
import zmq
import numpy as np

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea
)
from PySide6.QtCore import Qt

from qtzmq import subscribe, stream
from qtplotly import PlotWidget


DATA_PUB_PORT = 5560
DATA_REP_PORT = 5561

DATA_PUB_ADDR = f"tcp://127.0.0.1:{DATA_PUB_PORT}"
DATA_REP_ADDR = f"tcp://127.0.0.1:{DATA_REP_PORT}"


class ScanViewer(QWidget):
    """
    Mirrors gans_control.ui.plot.scan_plot.ScanPlot's exact curve naming
    ("data" / "data_y2") and reset/append pattern, isolated from all
    gans-control code, to determine whether the traceMap mismatch is a
    qtplotly bug or a gans-control usage bug.
    """

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.plot = PlotWidget()
        layout.addWidget(self.plot)

        # Same curve names as ScanPlot.__init__
        self.plot.add_curve("data", color="#2E86AB")
        self.plot.add_curve("data_y2", color="#F59E0B", axis="y2")
        self.plot.set_axis_title("x", "Motor")
        self.plot.set_axis_title("y1", "Counts")

        self.x_col = None
        self.y_col = None
        self.col_index = {}
        self.current_x = np.array([])
        self.current_y = np.array([])
        self._render_idx = 0

        self.last_status = None
        self.status_callback = None
        self.meta_callback = None

        subscribe("", DATA_PUB_ADDR)
        self.stream = stream("")
        self.stream.message.connect(self._on_message)

    def request_snapshot(self):
        ctx = zmq.Context.instance()
        req = ctx.socket(zmq.REQ)
        req.connect(DATA_REP_ADDR)
        req.send_string("snapshot")
        snapshot = json.loads(req.recv_string())
        self._on_message(snapshot)

    def _apply_live_state(self, status):
        self.last_status = status
        if status == "running":
            self.plot.set_plot_background("#FFF2C2")
            self.plot.set_live_mode(True)
        else:
            self.plot.set_plot_background("#FFFFFF")
            self.plot.set_live_mode(False)
        if self.status_callback:
            self.status_callback(status)

    def _on_message(self, msg):
        mtype = msg.get("type")

        if mtype == "scan_status":
            self._apply_live_state(msg.get("status"))
        elif mtype == "metadata":
            if self.meta_callback:
                self.meta_callback(msg.get("metadata", {}))
        elif mtype == "snapshot":
            self._apply_live_state(msg.get("scan_status"))
        elif mtype == "scan_start":
            self._handle_scan_start(msg)
        elif mtype == "scan_point":
            self._handle_scan_point(msg)
        elif mtype == "scan_end":
            self._apply_live_state("idle")

    # Same column-resolution logic as ScanPlot._parse_columns
    def _parse_columns(self, columns: dict):
        self.col_index = {name: int(k) for k, name in columns.items()}
        names = list(self.col_index.keys())
        self.x_col = names[0] if names else None
        self.y_col = (
            "det00" if "det00" in self.col_index else
            "det"   if "det"   in self.col_index else
            (names[1] if len(names) > 1 else None)
        )

    # Same reset pattern as ScanPlot._reset_plot — clear() + re-add_curve,
    # never renaming the curve afterward.
    def _reset_plot(self):
        self.plot.clear()
        self.plot.add_curve("data", color="#2E86AB")
        self.plot.add_curve("data_y2", color="#F59E0B", axis="y2")
        self.plot.set_axis_title("x", self.x_col or "Motor")
        self.plot.set_axis_title("y1", self.y_col or "Counts")
        self.plot.refresh()

    def _handle_scan_start(self, msg):
        print("[scan_start]", msg.get("columns"))
        self._parse_columns(msg.get("columns", {}))
        self.current_x = np.array([])
        self.current_y = np.array([])
        self._render_idx = 0
        self._reset_plot()
        self.plot.set_live_mode(True)
        self._apply_live_state("running")

    def _handle_scan_point(self, msg):
        row = msg.get("row")
        if not row or not self.x_col or not self.y_col:
            return
        try:
            self.current_x = np.append(self.current_x, row[self.col_index[self.x_col]])
            self.current_y = np.append(self.current_y, row[self.col_index[self.y_col]])
        except (KeyError, IndexError):
            return

        new_x = self.current_x[self._render_idx:]
        new_y = self.current_y[self._render_idx:]
        if len(new_x) > 0:
            print(f"[append_point] pushing {len(new_x)} new point(s), "
                  f"total so far {len(self.current_x)}")
            self.plot.append_point("data", new_x.tolist(), new_y.tolist())
            self._render_idx = len(self.current_x)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.resize(1100, 800)
        self.setWindowTitle("GANS Test — mirrors gans-control naming exactly")

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        self.setCentralWidget(central)

        self.status_label = QLabel("IDLE")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedHeight(30)
        self.status_label.setStyleSheet(
            "background: #333; color: white; font-weight: bold;"
        )
        layout.addWidget(self.status_label)

        self.viewer = ScanViewer()
        self.viewer.status_callback = self._update_status
        self.viewer.meta_callback = self._update_meta

        layout.addWidget(self.viewer)

        self.meta_label = QLabel()
        self.meta_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.meta_label.setStyleSheet("""
            background: #111;
            color: #EEE;
            padding: 6px;
            font-family: monospace;
            font-size: 11px;
        """)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.meta_label)
        scroll.setFixedHeight(150)
        layout.addWidget(scroll)

        self.viewer.request_snapshot()

    def _update_status(self, status):
        if status == "running":
            self.status_label.setText("RUNNING")
            self.status_label.setStyleSheet(
                "background: #2E7D32; color: white; font-weight: bold;"
            )
        else:
            self.status_label.setText("IDLE")
            self.status_label.setStyleSheet(
                "background: #333; color: white; font-weight: bold;"
            )

    def _update_meta(self, md):
        text = "\n".join(f"{k}: {v}" for k, v in md.items())
        self.meta_label.setText(text)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
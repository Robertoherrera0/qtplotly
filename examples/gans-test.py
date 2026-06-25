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

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.plot = PlotWidget()
        layout.addWidget(self.plot)

        self.plot.add_curve("y")

        self.last_status = None

        self.status_callback = None
        self.meta_callback = None

        self.columns = {}
        self.col_index = {}

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
            self.plot.set_plot_background("#FFF2C2")  # yellow
            self.plot.set_live_mode(True)
        else:
            self.plot.set_plot_background("#FFFFFF")
            self.plot.set_live_mode(False)

        if self.status_callback:
            self.status_callback(status)

    def _on_message(self, msg):

        mtype = msg.get("type")

        if mtype == "data_status":
            self._apply_live_state(msg.get("scan_status"))

        elif mtype == "metadata":
            if self.meta_callback:
                self.meta_callback(msg.get("metadata", {}))

        elif mtype == "scan_data":
            self._handle_snapshot(msg)

        elif mtype == "scan_start":
            self._handle_scan_start(msg)

        elif mtype == "scan_point":
            self._handle_scan_point(msg)

    def _setup_columns(self, columns):
        self.columns = columns
        self.col_index = {name: int(k) for k, name in columns.items()}

        names = list(columns.values())

        if not names:
            return None, None

        x_name = names[0]

        if "det" in self.col_index:
            y_name = "det"
        elif len(names) > 1:
            y_name = names[1]
        else:
            return None, None

        self.plot.set_axis_title("x", x_name)
        self.plot.set_axis_title("y1", y_name)

        return x_name, y_name

    def _handle_snapshot(self, msg):

        # --- metadata ---
        if self.meta_callback:
            self.meta_callback(msg.get("metadata", {}))

        # --- status ---
        self._apply_live_state(msg.get("scan_status"))

        rows = msg.get("data", [])
        columns = msg.get("columns", {})

        if not rows:
            return

        x_name, y_name = self._setup_columns(columns)
        if x_name is None:
            return

        arr = np.asarray(rows)

        x = arr[:, self.col_index[x_name]]
        y = arr[:, self.col_index[y_name]]

        self.plot.clear()
        self.plot.add_curve("y")
        self.plot.append_data("y", x, y)

    def _handle_scan_start(self, msg):

        columns = msg.get("columns", {})

        x_name, y_name = self._setup_columns(columns)
        if x_name is None:
            return

        self.plot.clear()
        self.plot.add_curve("y")

        # force live immediately
        self._apply_live_state("running")

    def _handle_scan_point(self, msg):

        if not self.col_index:
            return

        row = msg.get("row")
        if not row:
            return

        names = list(self.columns.values())

        x_name = names[0]

        if "det" in self.col_index:
            y_name = "det"
        elif len(names) > 1:
            y_name = names[1]
        else:
            return

        x = row[self.col_index[x_name]]
        y = row[self.col_index[y_name]]

        self.plot.append_data("y", [x], [y])


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.resize(1100, 800)
        self.setWindowTitle("GANS Test")

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

        # IMPORTANT: connect before snapshot
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

        # NOW safe to request snapshot
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
import sys
import numpy as np

from PySide6.QtWidgets import QApplication, QMainWindow

from qtzmq import subscribe, stream
from qtplotly import PlotWidget


DATA_PUB_PORT = 5560
DATA_PUB_ADDR = f"tcp://127.0.0.1:{DATA_PUB_PORT}"


class ScanViewer(QMainWindow):

    def __init__(self):

        super().__init__()

        self.resize(1000, 700)

        self.plot = PlotWidget()
        self.setCentralWidget(self.plot)

        self.plot.add_curve("det")

        subscribe("scan_data", DATA_PUB_ADDR)

        self.scan_stream = stream("scan_data")
        self.scan_stream.message.connect(self._on_message)

        self.last_npts = 0


    def _on_message(self, msg):

        if msg.get("type") != "scan_data":
            return

        rows = msg["data"]
        columns = msg["columns"]
        npts = msg["npts"]

        if not rows:
            return

        arr = np.asarray(rows)

        col_index = {name: int(k) for k, name in columns.items()}

        x = arr[:, col_index["th"]]
        y = arr[:, col_index["det"]]

        # NEW SCAN
        if npts < self.last_npts:

            self.plot.clear()
            self.plot.add_curve("det")
            self.plot.set_live_mode(True)

            self.last_npts = 0

        # NEW POINT ARRIVED
        if npts > self.last_npts:

            new_x = x[self.last_npts:npts]
            new_y = y[self.last_npts:npts]

            for xi, yi in zip(new_x, new_y):
                self.plot.append_data("det", xi, yi)

            self.plot.set_live_mode(True)

            peak_idx = np.argmax(y[:npts])
            peak_x = x[peak_idx]

            self.plot.add_vertical_marker("peak", peak_x)

            print(
                f"points={npts} "
                f"peak={np.max(y[:npts]):.2f} "
                f"mean={np.mean(y[:npts]):.2f}"
            )

        self.last_npts = npts


def main():

    app = QApplication(sys.argv)

    win = ScanViewer()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
"""
examples/test_viewer.py
Live plot viewer — works with any ZMQ publisher that sends
scan_start / scan_point / scan_end messages.
Run fake_publisher.py in one terminal, this in another.
"""
import sys
import time
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QToolBar
from qtzmq import subscribe, request, stream, requester, stop_all
from qtplotly import PlotWidget

PUB_ADDR = "tcp://127.0.0.1:5590"
REP_ADDR = "tcp://127.0.0.1:5591"

class ScanViewer(PlotWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.add_curve("data", color="#2E86AB")
        self.set_axis_title("x", "Motor")
        self.set_axis_title("y1", "Counts")

        self.x_col        = None
        self.y_col        = None
        self.col_index    = {}
        self.current_x    = np.array([])
        self.current_y    = np.array([])
        self._last_render = 0.0
        self._has_fit     = False

        s = stream("data")
        s.on("snapshot",   self._on_snapshot)
        s.on("scan_start", self._on_scan_start)
        s.on("scan_point", self._on_scan_point)
        s.on("scan_end",   self._on_scan_end)

        requester("data").request("snapshot")

    def _parse_columns(self, columns: dict):
        self.col_index = {name: int(k) for k, name in columns.items()}
        names = list(self.col_index.keys())
        self.x_col = names[0] if names else None
        self.y_col = (
            "det00" if "det00" in self.col_index else
            "det"   if "det"   in self.col_index else
            (names[1] if len(names) > 1 else None)
        )
        print(f"[columns] x={self.x_col}  y={self.y_col}")

    def _reset(self):
        self.clear()
        self.add_curve("data", color="#2E86AB")
        self.set_axis_title("x", "Motor")
        self.set_axis_title("y1", "Counts")
        self._has_fit = False

    def _on_snapshot(self, msg):
        cols = msg.get("columns", {})
        if cols:
            self._parse_columns(cols)
        rows = msg.get("data", [])
        if rows and self.x_col and self.y_col:
            try:
                xi = self.col_index[self.x_col]
                yi = self.col_index[self.y_col]
                self.current_x = np.array([r[xi] for r in rows])
                self.current_y = np.array([r[yi] for r in rows])
                self.set_data("data", self.current_x.tolist(), self.current_y.tolist())
                print(f"[snapshot] seeded {len(rows)} points")
            except (KeyError, IndexError) as e:
                print(f"[snapshot] {e}")
        else:
            print(f"[snapshot] status={msg.get('scan_status')}  no data to seed")

    def _on_scan_start(self, msg):
        self._parse_columns(msg.get("columns", {}))
        self.current_x    = np.array([])
        self.current_y    = np.array([])
        self._last_render = 0.0
        self._reset()
        self.set_live_mode(True)
        print("[scan_start]")

    def _on_scan_point(self, msg):
        row = msg.get("row")
        if not row or not self.x_col or not self.y_col:
            return
        try:
            self.current_x = np.append(self.current_x, row[self.col_index[self.x_col]])
            self.current_y = np.append(self.current_y, row[self.col_index[self.y_col]])
        except (KeyError, IndexError) as e:
            print(f"[scan_point] {e}")
            return

        now = time.monotonic()
        if now - self._last_render >= 0.1:
            self._last_render = now
            self.set_data("data", self.current_x.tolist(), self.current_y.tolist())
            print(f"[scan_point] rendered n={len(self.current_x)}")

    def _on_scan_end(self, msg):
        raw  = msg.get("data", [])
        cols = msg.get("columns", {})
        if raw and cols:
            self._parse_columns(cols)
            try:
                xi = self.col_index[self.x_col]
                yi = self.col_index[self.y_col]
                self.current_x = np.array([r[xi] for r in raw])
                self.current_y = np.array([r[yi] for r in raw])
            except (KeyError, IndexError) as e:
                print(f"[scan_end] {e}")

        self.set_live_mode(False)
        self.set_data("data", self.current_x.tolist(), self.current_y.tolist())
        print(f"[scan_end] final n={len(self.current_x)}")

        if len(self.current_x) > 3:
            self._draw_markers()

    def _draw_markers(self):
        try:
            y = self.current_y
            x = self.current_x

            if float(y.max() - y.min()) < 1e-10:
                print("[markers] skipped — flat data")
                return

            ysum = float(np.sum(y))
            if abs(ysum) < 1e-10:
                print("[markers] skipped — zero sum")
                return

            peak_i = int(np.argmax(y))
            xpk    = float(x[peak_i])
            half   = float(y[peak_i]) / 2
            left   = np.where(x < xpk)[0]
            right  = np.where(x > xpk)[0]
            lhmx   = float(x[left[np.argmin(np.abs(y[left]   - half))]]) if len(left)  else xpk
            uhmx   = float(x[right[np.argmin(np.abs(y[right]  - half))]]) if len(right) else xpk
            com    = float(np.sum(x * y) / ysum)
            cfwhm  = (lhmx + uhmx) / 2

            xspan     = float(x.max() - x.min()) or 1.0
            threshold = 0.05 * xspan
            step      = 0.08

            markers = [
                ("PEAK",   xpk,   "#E11D48"),
                ("COM",    com,    "#1565C0"),
                ("FWHM_L", lhmx,   "#2E7D32"),
                ("FWHM_U", uhmx,   "#2E7D32"),
                ("CFWHM",  cfwhm,  "#00838F"),
            ]

            placed   = []
            label_ys = {}
            for name, mx, _ in sorted(markers, key=lambda m: m[1]):
                ly = 0.99
                for px, py in placed:
                    if abs(mx - px) < threshold:
                        ly = min(ly, py - step)
                label_ys[name] = round(ly, 3)
                placed.append((mx, ly))

            for name, mx, color in markers:
                self.add_vertical_marker(
                    name, mx,
                    color=color, width=1,
                    y0=0.0, y1=0.98,
                    label_y=label_ys[name],
                )

            print(f"[markers] peak={xpk:.4f}  com={com:.4f}  fwhm={uhmx-lhmx:.4f}")
        except Exception as e:
            import traceback
            print(f"[markers] {e}")
            traceback.print_exc()

    def do_fit(self):
        if len(self.current_x) < 4:
            print("[fit] not enough points")
            return
        try:
            from scipy.optimize import curve_fit

            def gaussian(x, A, x0, s, B):
                return A * np.exp(-0.5 * ((x - x0) / max(s, 1e-9)) ** 2) + B

            x, y    = self.current_x, self.current_y
            p0      = [float(y.max()-y.min()), float(x[np.argmax(y)]),
                       float((x[-1]-x[0])*0.1), float(y.min())]
            popt, _ = curve_fit(gaussian, x, y, p0=p0, maxfev=5000)
            xfit    = np.linspace(x.min(), x.max(), 500)
            yfit    = gaussian(xfit, *popt)

            if not self._has_fit:
                self.add_curve("fit", color="#E11D48", role="fit")
                self._has_fit = True

            self.set_data("fit", xfit.tolist(), yfit.tolist())
            print(f"[fit] x0={popt[1]:.4f}  sigma={popt[2]:.4f}")
        except Exception as e:
            print(f"[fit] {e}")

    def clear_fit(self):
        if self._has_fit:
            self.remove_curve("fit")
            self._has_fit = False


def main():
    app = QApplication(sys.argv)

    subscribe("data", PUB_ADDR)
    request("data",   REP_ADDR)

    window = QMainWindow()
    window.setWindowTitle("qtplotly — live scan viewer")
    window.resize(1200, 800)

    viewer = ScanViewer()
    window.setCentralWidget(viewer)

    toolbar = QToolBar()
    toolbar.setMovable(False)
    window.addToolBar(toolbar)

    fit_btn   = QPushButton("Gaussian Fit")
    clear_btn = QPushButton("Clear Fit")
    fit_btn.clicked.connect(viewer.do_fit)
    clear_btn.clicked.connect(viewer.clear_fit)
    toolbar.addWidget(fit_btn)
    toolbar.addWidget(clear_btn)

    window.show()
    app.aboutToQuit.connect(stop_all)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
import sys
import numpy as np
from scipy.optimize import curve_fit

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton

from qtplotly import PlotWidget


def gaussian(x, A, x0, sigma, B):
    return A * np.exp(-0.5 * ((x - x0) / np.maximum(sigma, 1e-12)) ** 2) + B


def guess_gaussian(x, y):
    B = float(np.min(y))
    A = float(np.max(y) - B)
    x0 = float(x[np.argmax(y)])
    sigma = 0.1 * (np.max(x) - np.min(x))
    return A, x0, sigma, B


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("qtplotly Box-Select Fit Test")
        self.resize(1000, 700)

        central = QWidget()
        layout = QVBoxLayout(central)

        self.plot = PlotWidget()
        layout.addWidget(self.plot)

        self.fit_button = QPushButton("Fit Selected Region")
        self.fit_button.clicked.connect(self.run_fit)
        layout.addWidget(self.fit_button)

        self.setCentralWidget(central)

        self.x = np.linspace(0, 10, 200)
        self.y = 3 * np.exp(-0.5 * ((self.x - 5.2) / 0.8) ** 2) + 0.2 * np.random.randn(len(self.x))

        self.plot.add_curve("signal", axis="y1", color="blue")
        self.plot.set_data("signal", self.x, self.y)
        self.plot.set_axis_title("x", "Position")
        self.plot.set_axis_title("y1", "Signal")

        self._xmin = None
        self._xmax = None

        self.plot.selection_bridge.selection_made.connect(self.on_selection)
        self.plot.set_select_mode(True)

    def on_selection(self, xmin, xmax):
        self._xmin = xmin
        self._xmax = xmax

    def run_fit(self):
        x, y = self.x, self.y
        if self._xmin is not None and self._xmax is not None:
            mask = (x >= self._xmin) & (x <= self._xmax)
            x, y = x[mask], y[mask]

        if len(x) < 4:
            print("Not enough points in selection to fit.")
            return

        p0 = guess_gaussian(x, y)
        popt, _ = curve_fit(gaussian, x, y, p0=p0, maxfev=10000)

        xfit = np.linspace(np.min(x), np.max(x), 400)
        yfit = gaussian(xfit, *popt)

        if "fit" in self.plot.model.curves:
            self.plot.remove_curve("fit")
        self.plot.add_curve("fit", axis="y1", color="red", role="fit")
        self.plot.set_data("fit", xfit, yfit)


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
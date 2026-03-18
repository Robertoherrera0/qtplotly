import sys
import numpy as np
from scipy.optimize import curve_fit

from PySide6.QtWidgets import QApplication, QMainWindow

from qtplotly import PlotWidget


def gaussian(x, A, x0, sigma, B):
    return A * np.exp(-0.5 * ((x - x0) / np.maximum(sigma, 1e-12)) ** 2) + B

def guess_gaussian(x, y):
    B = float(np.min(y))
    A = float(np.max(y) - B)
    x0 = float(x[np.argmax(y)])
    sigma = 0.1 * (np.max(x) - np.min(x))
    return A, x0, sigma, B


def main():
    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("qtplotly Test")
    window.resize(1000, 700)

    plot = PlotWidget()
    window.setCentralWidget(plot)

    plot.add_curve("signal", axis="y1", color="blue")
    plot.add_curve("reference", axis="y2", color="green")

    x = np.linspace(0, 10, 200)

    y1 = 3 * np.exp(-0.5 * ((x - 5.2) / 0.8) ** 2) + 0.2 * np.random.randn(len(x))
    y2 = 0.5 * np.cos(x)

    plot.set_data("signal", x, y1)
    plot.set_data("reference", x, y2)

    p0 = guess_gaussian(x, y1)

    popt, _ = curve_fit(gaussian, x, y1, p0=p0, maxfev=10000)

    xfit = np.linspace(np.min(x), np.max(x), 800)
    yfit = gaussian(xfit, *popt)

    A, x0, sigma, B = popt
    fwhm = 2.355 * abs(sigma)

    fit_curve = plot.model.add_curve("Gaussian Fit", axis="y1")
    fit_curve.set_data(xfit, yfit)

    fit_curve.role = "fit"
    

    plot.refresh()

    plot.set_axis_title("x", "Position")
    plot.set_axis_title("y1", "Signal")
    plot.set_axis_title("y2", "Reference")

    plot.add_vertical_marker("PEAK", x0, "green")
    plot.add_vertical_marker("CFWHM", x0 - fwhm / 2, "cyan")

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
import sys
import numpy as np

from PySide6.QtWidgets import QApplication, QMainWindow

from qtplotly import PlotWidget


def main():

    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("qtplotly Test")
    window.resize(1000, 700)

    plot = PlotWidget()
    window.setCentralWidget(plot)

    # create curves
    plot.add_curve("signal", axis="y1", color="blue")
    plot.add_curve("reference", axis="y2", color="green")

    # generate test data
    x = np.linspace(0, 10, 200)

    y1 = np.sin(x)
    y2 = 0.5 * np.cos(x)

    plot.set_data("Signal", x, y1)
    plot.set_data("Reference", x, y2)

    plot.set_axis_title("x", "Position")
    plot.set_axis_title("y1", "Signal")
    plot.set_axis_title("y2", "Reference")

    plot.add_vertical_marker("PEAK", 5.0)
    plot.add_vertical_marker("CFWM", 4.9)

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
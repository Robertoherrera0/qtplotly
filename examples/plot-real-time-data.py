import sys
import zmq
import time

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer

from qtplotly import PlotWidget


class StreamSubscriber:

    def __init__(self):

        ctx = zmq.Context()

        self.socket = ctx.socket(zmq.SUB)
        self.socket.connect("tcp://127.0.0.1:7004")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")

    def poll(self):

        try:
            return self.socket.recv_json(flags=zmq.NOBLOCK)
        except zmq.Again:
            return None


def main():

    app = QApplication(sys.argv)

    window = QMainWindow()
    window.resize(1000, 700)

    plot = PlotWidget()
    window.setCentralWidget(plot)

    plot.add_curve("signal")

    subscriber = StreamSubscriber()

    timer = QTimer()

    last_message_time = 0

    def update():

        nonlocal last_message_time

        msg = subscriber.poll()

        if msg is None:

            if time.time() - last_message_time > 1:
                plot.set_live_mode(False)

            return

        last_message_time = time.time()

        plot.set_live_mode(True)

        x = msg["x"]
        y = msg["y"]

        plot.append_data("signal", x, y)

    timer.timeout.connect(update)
    timer.start(20)

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
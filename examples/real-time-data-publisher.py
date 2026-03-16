import time
import numpy as np
import zmq


def main():

    ctx = zmq.Context()

    socket = ctx.socket(zmq.PUB)
    socket.bind("tcp://127.0.0.1:7004")

    print("Publisher started on tcp://127.0.0.1:7004")

    x = 0.0
    i = 0 
    while True:
        if i % 2000 == 0:
            time.sleep(3)
            
        y = np.sin(x) + 0.1 * np.random.randn()

        payload = {
            "x": float(x),
            "y": float(y)
        }

        socket.send_json(payload)

        x += 0.1

        time.sleep(0.5)
        i+=1


if __name__ == "__main__":
    main()
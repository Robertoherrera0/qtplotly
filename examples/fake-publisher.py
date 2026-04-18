"""
Fake data acquisition publisher for testing qtplotly.
Simulates realistic scans with gaussian peaks, noise, and delays.
Run this in one terminal, then run test-viewer.py in another.
"""
import time
import json
import zmq
import numpy as np

PUB_ADDR = "tcp://127.0.0.1:5590"
REP_ADDR = "tcp://127.0.0.1:5591"

COLUMNS = {
    "0":  "th",
    "1":  "det",
    "2":  "mon",
    "3":  "sec",
}

def make_scan(center, width, amplitude, npts=40, baseline=50, noise=30):
    x = np.linspace(center - 3*width, center + 3*width, npts)
    y = amplitude * np.exp(-0.5 * ((x - center) / width)**2) + baseline
    y += np.random.normal(0, noise, npts)
    y = np.clip(y, 0, None)
    mon = np.random.randint(950, 1050, npts).astype(float)
    sec = np.ones(npts) * 1.0
    det = y * 0.1 + np.random.normal(0, 5, npts)
    mon0 = mon * 0.98
    rows = []
    for i in range(npts):
        rows.append([
            float(x[i]),
            float(y[i]),
            float(mon0[i]),
            float(sec[i]),
            float(det[i]),
            float(mon[i]),
        ])
    return x, rows


def main():
    ctx = zmq.Context()

    pub = ctx.socket(zmq.PUB)
    pub.setsockopt(zmq.SNDHWM, 1000)
    pub.bind(PUB_ADDR)

    rep = ctx.socket(zmq.REP)
    rep.setsockopt(zmq.RCVTIMEO, 100)
    rep.bind(REP_ADDR)

    print(f"[pub] PUB {PUB_ADDR}")
    print(f"[rep] REP {REP_ADDR}")
    time.sleep(0.5)

    scan_configs = [
        dict(center=2.25, width=0.30, amplitude=1000, npts=40, baseline=50,  noise=25),
        dict(center=2.10, width=0.20, amplitude=1500, npts=30, baseline=80,  noise=40),
        dict(center=2.40, width=0.50, amplitude=600,  npts=50, baseline=30,  noise=15),
        dict(center=2.00, width=0.15, amplitude=2000, npts=25, baseline=100, noise=60),
    ]

    last_x    = np.array([])
    last_rows = []
    last_cols = COLUMNS
    scan_num  = 0

    while True:
        idle_start = time.time()
        while time.time() - idle_start < 4.0:
            try:
                msg = rep.recv_string()
                if msg == "snapshot":
                    rep.send_string(json.dumps({
                        "type":          "snapshot",
                        "server_status": 1,
                        "scan_status":   "idle",
                        "data_status":   1,
                        "metadata":      {
                            "title":     f"scan {scan_num}",
                            "npts":      len(last_rows),
                            "ctime":     1.0,
                            "scanrange": f"th,{last_x[0] if len(last_x) else 0:.2f},{last_x[-1] if len(last_x) else 0:.2f}",
                            "date":      time.strftime("%Y-%m-%d %H:%M:%S"),
                        },
                        "columns":       last_cols,
                        "data":          last_rows,
                        "npts":          len(last_rows),
                        "timestamp":     time.time(),
                    }))
                else:
                    rep.send_string(json.dumps({"pong": True}))
            except zmq.Again:
                pass

        cfg      = scan_configs[scan_num % len(scan_configs)]
        scan_num += 1
        x_arr, rows = make_scan(**cfg)
        npts     = len(rows)
        metadata = {
            "title":     f"scan {scan_num}  th={cfg['center']:.2f}",
            "npts":      npts,
            "ctime":     1.0,
            "scanrange": f"th,{x_arr[0]:.2f},{x_arr[-1]:.2f}",
            "date":      time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        print(f"\n[pub] === scan {scan_num} start  center={cfg['center']}  npts={npts} ===")

        pub.send_json({
            "type":      "scan_start",
            "metadata":  metadata,
            "columns":   COLUMNS,
            "timestamp": time.time(),
        })

        for i, row in enumerate(rows):
            # handle snapshot requests mid-scan too
            try:
                msg = rep.recv_string()
                if msg == "snapshot":
                    rep.send_string(json.dumps({
                        "type":          "snapshot",
                        "server_status": 2,   # busy
                        "scan_status":   "running",
                        "data_status":   1,
                        "metadata":      metadata,
                        "columns":       COLUMNS,
                        "data":          rows[:i],
                        "npts":          i,
                        "timestamp":     time.time(),
                    }))
                else:
                    rep.send_string(json.dumps({"pong": True}))
            except zmq.Again:
                pass

            pub.send_json({
                "type":      "scan_point",
                "row":       row,
                "npts":      i + 1,
                "timestamp": time.time(),
            })
            print(f"[pub]   point {i+1:2d}/{npts}  th={row[0]:.3f}  det00={row[1]:.1f}")
            time.sleep(0.3)   # 300ms per point — realistic count time

        pub.send_json({
            "type":      "scan_end",
            "metadata":  metadata,
            "columns":   COLUMNS,
            "data":      rows,
            "timestamp": time.time(),
        })
        print(f"[pub] === scan {scan_num} end ===")

        last_x    = x_arr
        last_rows = rows
        last_cols = COLUMNS


if __name__ == "__main__":
    main()
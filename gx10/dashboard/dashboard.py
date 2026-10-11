"""Dashboard on port 8000: live picture with YOLO boxes, depth, decision, clearance per
heading, delays, GPU use, and a text box that does the same job as voice.

Started by ingest/server.py (--dashboard-port). Standard library plus OpenCV;
pictures are drawn only when the page asks for them, not every frame.
"""

import json
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import numpy as np

PAGE = (Path(__file__).parent / "index.html").read_bytes()
_CV = {1: cv2.ROTATE_90_CLOCKWISE, 2: cv2.ROTATE_180, 3: cv2.ROTATE_90_COUNTERCLOCKWISE}


class GPU:
    """nvidia-smi every 2 seconds. GB10 memory reads 'Not Supported'; utilisation, power and temperature work."""

    def __init__(self):
        self.now = {}
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while True:
            try:
                out = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu,power.draw,temperature.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=5).stdout.strip().split(", ")
                self.now = {"util_pct": float(out[0]), "power_w": float(out[1]), "temp_c": float(out[2])}
            except Exception:
                self.now = {}
            time.sleep(2)


def _upright(img, turn):
    return cv2.rotate(img, _CV[turn]) if turn else img


def picture(view):
    jpeg, turn, dets, target = view["jpeg"], view["turn"], view["dets"], view.get("target_box")
    img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        img = np.zeros((480, 640, 3), np.uint8)
    for d in dets or []:
        x1, y1, x2, y2 = d.box
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 200, 255), 2)
    img = _upright(img, turn)
    for i, d in enumerate(dets or []):  # labels after turning, so the text reads the right way
        cv2.putText(img, f"{d.label} {d.conf:.2f}", (8, 24 + 22 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
    ok, out = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 75])
    return out.tobytes()


def depth_picture(view):
    d = view["depth"].astype(np.float32)
    v = np.clip(d / 5000.0 * 255, 0, 255).astype(np.uint8)  # 0 m dark to 5 m bright
    img = cv2.applyColorMap(255 - v, cv2.COLORMAP_TURBO)  # near = red, far = blue
    img[(view["depth"] == 0) | (view["conf"] < 1)] = (40, 40, 40)  # no good reading: grey
    img = cv2.resize(img, (img.shape[1] * 2, img.shape[0] * 2), interpolation=cv2.INTER_NEAREST)
    ok, out = cv2.imencode(".png", _upright(img, view["turn"]))
    return out.tobytes()


def start(server, port: int):
    """server: ingest.server.Server. Serves until the process ends."""
    gpu = GPU()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, body, kind, code=200):
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            view = server.pipe.view
            if self.path == "/":
                return self._send(PAGE, "text/html; charset=utf-8")
            if self.path.startswith("/status"):
                s = dict(server.status())
                s["gpu"] = gpu.now
                return self._send(json.dumps(s).encode(), "application/json")
            if self.path.startswith("/frame.jpg") and view:
                return self._send(picture(view), "image/jpeg")
            if self.path.startswith("/depth.png") and view:
                return self._send(depth_picture(view), "image/png")
            self._send(b"not found", "text/plain", 404)

        def do_POST(self):
            if self.path == "/say":
                n = int(self.headers.get("Content-Length", 0))
                text = json.loads(self.rfile.read(n) or b"{}").get("text", "")
                server.text_command(text)
                return self._send(b'{"ok": true}', "application/json")
            self._send(b"not found", "text/plain", 404)

    httpd = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd

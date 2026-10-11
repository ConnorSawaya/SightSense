"""Dashboard on port 8000: live picture with YOLO boxes, depth, decision, clearance per
heading, delays, GPU use, and a text box that does the same job as voice.

Started by ingest/server.py (--dashboard-port). Standard library plus OpenCV.

Built to stay live over a slow link (Tailscale over cellular, 0.3-1 s per request):
- /stream.mjpg pushes picture and depth side by side as one MJPEG stream on one
  connection. Each viewer always gets the newest frame; stale ones are skipped,
  never queued.
- /events pushes the status about 5 times a second (server-sent events).
- Each frame is drawn once, shared by all viewers, and only while someone watches.
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
STREAM_FPS = 8  # cap per viewer; the phone sends up to 15
STATUS_HZ = 5
JPEG_QUALITY = 70
BOUNDARY = b"frame"


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


def _picture(view):
    img = cv2.imdecode(np.frombuffer(view["jpeg"], np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        img = np.zeros((480, 640, 3), np.uint8)
    for d in view["dets"] or []:
        x1, y1, x2, y2 = d.box
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 200, 255), 2)
    img = _upright(img, view["turn"])
    for i, d in enumerate(view["dets"] or []):  # labels after turning, so the text reads the right way
        cv2.putText(img, f"{d.label} {d.conf:.2f}", (8, 24 + 22 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
    return img


def _depth(view):
    v = np.clip(view["depth"].astype(np.float32) / 5000.0 * 255, 0, 255).astype(np.uint8)  # 0 m dark to 5 m bright
    img = cv2.applyColorMap(255 - v, cv2.COLORMAP_TURBO)  # near = red, far = blue
    img[(view["depth"] == 0) | (view["conf"] < 1)] = (40, 40, 40)  # no good reading: grey
    return _upright(img, view["turn"])


def composite(view) -> bytes:
    """Picture and depth side by side, same height, as one JPEG."""
    pic, dep = _picture(view), _depth(view)
    h = pic.shape[0]
    dep = cv2.resize(dep, (round(dep.shape[1] * h / dep.shape[0]), h), interpolation=cv2.INTER_NEAREST)
    ok, out = cv2.imencode(".jpg", cv2.hconcat([pic, dep]), [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    return out.tobytes() if ok else b""


class Renderer:
    """Draws the newest frame once for all viewers, only while at least one is watching."""

    def __init__(self, server):
        self.server = server
        self.viewers = 0
        self.jpeg, self.seq = b"", -1
        self.cond = threading.Condition()
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        drawn = None
        while True:
            time.sleep(1 / STREAM_FPS)
            view = self.server.pipe.view
            if not self.viewers or view is None or view is drawn:
                continue
            drawn = view
            try:
                jpeg = composite(view)
            except Exception as e:
                print("dashboard: draw failed:", repr(e), flush=True)
                continue
            with self.cond:
                self.jpeg, self.seq = jpeg, self.seq + 1
                self.cond.notify_all()

    def wait_newer(self, seq, timeout=2.0):
        with self.cond:
            self.cond.wait_for(lambda: self.seq != seq, timeout)
            return self.jpeg, self.seq


def start(server, port: int):
    """server: ingest.server.Server. Serves until the process ends."""
    gpu = GPU()
    renderer = Renderer(server)

    def status():
        s = dict(server.status())
        s["gpu"] = gpu.now
        s["viewers"] = renderer.viewers
        return s

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"  # keep connections open; a new one costs a round trip

        def log_message(self, *a):
            pass

        def _send(self, body, kind, code=200):
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _stream_headers(self, kind):
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/":
                return self._send(PAGE, "text/html; charset=utf-8")
            if path == "/status":
                return self._send(json.dumps(status()).encode(), "application/json")
            if path == "/events":
                return self._events()
            if path == "/stream.mjpg":
                return self._mjpeg()
            if path == "/frame.jpg" and server.pipe.view:  # one still, e.g. for a screenshot
                return self._send(composite(server.pipe.view), "image/jpeg")
            self._send(b"not found", "text/plain", 404)

        def _events(self):
            self._stream_headers("text/event-stream")
            try:
                while True:
                    self.wfile.write(b"data: " + json.dumps(status()).encode() + b"\n\n")
                    self.wfile.flush()
                    time.sleep(1 / STATUS_HZ)
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass

        def _mjpeg(self):
            self._stream_headers(f"multipart/x-mixed-replace; boundary={BOUNDARY.decode()}")
            with renderer.cond:
                renderer.viewers += 1
            seq = -1
            try:
                while True:
                    jpeg, new = renderer.wait_newer(seq)
                    if new == seq or not jpeg:
                        continue  # nothing new yet (no phone); keep the connection open
                    seq = new
                    # a slow viewer blocks here, then gets the newest frame next: never a backlog
                    self.wfile.write(b"--" + BOUNDARY + b"\r\nContent-Type: image/jpeg\r\nContent-Length: "
                                     + str(len(jpeg)).encode() + b"\r\n\r\n" + jpeg + b"\r\n")
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            finally:
                with renderer.cond:
                    renderer.viewers -= 1

        def do_POST(self):
            if self.path == "/say":
                n = int(self.headers.get("Content-Length", 0))
                text = json.loads(self.rfile.read(n) or b"{}").get("text", "")
                server.text_command(text)
                return self._send(b'{"ok": true}', "application/json")
            self._send(b"not found", "text/plain", 404)

    httpd = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd

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

from . import obstacle_view

PAGE = (Path(__file__).parent / "index.html").read_bytes()
_CV = {1: cv2.ROTATE_90_CLOCKWISE, 2: cv2.ROTATE_180, 3: cv2.ROTATE_90_COUNTERCLOCKWISE}
STREAM_FPS = 15  # cap per viewer; the phone sends up to 15
STREAM_H = 400  # composite height in pixels: smaller frames keep up over Tailscale
STATUS_HZ = 5
JPEG_QUALITY = 60
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


def _turn_box(box, turn, w, h):
    """A box on the original w x h picture -> the same box on the picture turned upright."""
    x1, y1, x2, y2 = box
    if turn == 1:  # 90 clockwise: (u, v) -> (h - v, u)
        pts = [(h - y1, x1), (h - y2, x2)]
    elif turn == 3:  # 90 anticlockwise: (u, v) -> (v, w - u)
        pts = [(y1, w - x1), (y2, w - x2)]
    elif turn == 2:
        pts = [(w - x1, h - y1), (w - x2, h - y2)]
    else:
        return box
    xs, ys = sorted(p[0] for p in pts), sorted(p[1] for p in pts)
    return [xs[0], ys[0], xs[1], ys[1]]


def _picture(view):
    img = view.get("upright")  # decoded and turned once by the frame service
    if img is None:
        img = cv2.imdecode(np.frombuffer(view["jpeg"], np.uint8), cv2.IMREAD_COLOR) if view["jpeg"] else None
        img = _upright(img, view["turn"]) if img is not None else np.zeros((480, 640, 3), np.uint8)
    turn = view["turn"]
    h, w = (img.shape[1], img.shape[0]) if turn in (1, 3) else img.shape[:2]  # the original picture's size
    scale = STREAM_H / img.shape[0]
    img = cv2.resize(img, (round(img.shape[1] * scale), STREAM_H), interpolation=cv2.INTER_AREA)
    # nearest first, so near labels are drawn last and stay on top
    dets = sorted(view["dets"] or [], key=lambda d: -(getattr(d, "dist_m", None) or 99))
    for d in dets:
        x1, y1, x2, y2 = (int(v * scale) for v in _turn_box(d.box, turn, w, h))
        dist = getattr(d, "dist_m", None)
        near = dist is not None and dist < 1.5
        hazard = getattr(d, "source", "yolo") == "open"
        color = (60, 60, 255) if near else (255, 120, 200) if hazard else (0, 200, 255)  # red when close; violet hazards, amber objects
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        label = d.label + (f" {dist:.1f} m" if dist is not None else "")
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        ty = y1 - 4 if y1 - th - 6 > 0 else y1 + th + 4
        cv2.rectangle(img, (x1, ty - th - 3), (x1 + tw + 4, ty + 3), (0, 0, 0), -1)
        cv2.putText(img, label, (x1 + 2, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
    return img


def centre_m(view):
    """Median good depth in the middle 8 x 8 pixels, metres: what the phone's reticle used to show."""
    d, c = view["depth"], view["conf"]
    h, w = d.shape
    patch = d[h // 2 - 4 : h // 2 + 4, w // 2 - 4 : w // 2 + 4]
    good = patch[(patch > 0) & (c[h // 2 - 4 : h // 2 + 4, w // 2 - 4 : w // 2 + 4] >= 1)]
    return round(float(np.median(good)) / 1000, 2) if good.size else None


def _depth(view):
    v = np.clip(view["depth"].astype(np.float32) / 5000.0 * 255, 0, 255).astype(np.uint8)  # 0 m dark to 5 m bright
    img = cv2.applyColorMap(255 - v, cv2.COLORMAP_TURBO)  # near = red, far = blue
    img[(view["depth"] == 0) | (view["conf"] < 1)] = (40, 40, 40)  # no good reading: grey
    return _upright(img, view["turn"])


def _reticle(img, metres):
    """Centre square, corner brackets and the distance, drawn after scaling so they stay sharp."""
    h, w = img.shape[:2]
    cx, cy, s, b, k = w // 2, h // 2, max(10, w // 22), max(40, w // 5), max(10, w // 18)
    white = (255, 255, 255)
    cv2.rectangle(img, (cx - s, cy - s), (cx + s, cy + s), white, 2, cv2.LINE_AA)
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x, y = cx + dx * b, cy + dy * b
        cv2.line(img, (x, y), (x - dx * k, y), white, 2, cv2.LINE_AA)
        cv2.line(img, (x, y), (x, y - dy * k), white, 2, cv2.LINE_AA)
    text = f"{metres:.2f} m" if metres is not None else "no reading"
    scale = max(0.7, w / 300)
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 2)
    x0, y0 = cx - tw // 2, h - 24
    cv2.rectangle(img, (x0 - 14, y0 - th - 12), (x0 + tw + 14, y0 + 12), (20, 20, 20), -1)
    cv2.putText(img, text, (x0, y0), cv2.FONT_HERSHEY_SIMPLEX, scale, white, 2, cv2.LINE_AA)
    return img


def composite(view, manual=None) -> bytes:
    """Picture and the obstacle view (or plain depth when there are no maps) side by side, as one JPEG.
    manual: the command being held in manual steering, which the obstacle view highlights."""
    pic = _picture(view)
    h = pic.shape[0]
    dep = obstacle_view.draw(view, h, manual)
    if dep is None:
        dep = _depth(view)
        dep = cv2.resize(dep, (round(dep.shape[1] * h / dep.shape[0]), h), interpolation=cv2.INTER_NEAREST)
    dep = _reticle(dep, centre_m(view))
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
            manual = self.server.manual[0] if self.server.manual else None
            if not self.viewers or view is None or (drawn and drawn[0] is view and drawn[1] == manual):
                continue
            drawn = (view, manual)  # redrawn when manual steering changes too, so the highlight follows the click
            try:
                jpeg = composite(view, manual)
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
        view = server.pipe.view
        s["centre_m"] = centre_m(view) if view is not None and s.get("frame") else None
        manual = server.manual[0] if server.manual else None
        s["explain"] = obstacle_view.banner(view, manual) if view is not None and view.get("maps") is not None and s.get("frame") else None
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
                return self._send(composite(server.pipe.view, server.manual[0] if server.manual else None), "image/jpeg")
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
            if self.path == "/manual":  # manual spin: LEFT (counter-clockwise), RIGHT (clockwise), STOP, or AUTO to hand back
                n = int(self.headers.get("Content-Length", 0))
                cmd = json.loads(self.rfile.read(n) or b"{}").get("cmd", "")
                ok = server.manual_command(cmd)
                return self._send(b'{"ok": true}' if ok else b'{"ok": false}', "application/json", 200 if ok else 400)
            self._send(b"not found", "text/plain", 404)

    httpd = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd

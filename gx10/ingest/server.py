"""The GX10 frame service: phone on one port, Pi on another.

    cd gx10 && ../../venv-yolo/bin/python -m ingest.server
    ... --phone-port 8765 --pi-port 8766 --no-yolo --record ../../recordings

Phone (contracts/MESSAGES.md): binary frame messages in; {"text": ...} voice and
route messages in; guidance and {"lookup": ...} out, on the same connection.
Pi: connects to the Pi port; gets {"seq", "cmd", "ttl_ms"} for every processed
frame. Dashboard: http://<GX10>:8000 (gx10/dashboard/). No frame for 0.4 s means nothing is sent and the Pi switches the motor off.

Only the newest frame is processed; older ones waiting are dropped, never queued.
Clear or blocked comes from depth only (planner/obstacle.py). The navigator and the
vision-language model only supply a desired bearing, speech and "within reach".
"""

import argparse
import asyncio
import json
import os
import statistics
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

import vlm
from navigator import Navigator, decode
from planner.obstacle import HEADINGS, USABLE_M, Smoother, check

from .upright import box_back, rotate_jpeg, turn_for

TTL_MS = 400


class UprightVLM:
    """vlm with the picture turned upright first, and find() boxes mapped back."""

    def __init__(self):
        self.turn = 0

    def find(self, jpeg, name):
        turn = self.turn
        a = vlm.find(rotate_jpeg(jpeg, turn), name)
        if a.box:
            w, h = vlm.core.jpeg_size(jpeg)
            a.box = box_back(a.box, turn, w, h)
        return a

    def describe(self, jpeg):
        return vlm.describe(rotate_jpeg(jpeg, self.turn))

    def read(self, jpeg):
        return vlm.read(rotate_jpeg(jpeg, self.turn))


class Pipeline:
    def __init__(self, use_yolo: bool):
        print("vision-language model:", vlm.warm(), flush=True)
        self.vlm = UprightVLM()
        self.nav = Navigator(self.vlm)
        self.det = None
        if use_yolo:
            from detector.detector import Detector

            self.det = Detector()
            print("yolo:", self.det.using, flush=True)
        self.smoother = Smoother()
        self.speech = deque()
        self.last_state = None
        self.last_frame = -1e9
        self.status = {}
        self.view = None  # newest frame's picture and depth, for the dashboard

    def process(self, raw: bytes, t_recv: float):
        f = decode(raw)
        now = time.monotonic()
        if now - self.last_frame > 1.0:  # new session or a gap: start again from STOP, forget old timers
            self.smoother, self.last_state = Smoother(), None
        self.last_frame = now
        self.vlm.turn = turn = turn_for(f.pose)
        depth = np.frombuffer(f.depth_mm, dtype=np.uint16).reshape(f.depth_h, f.depth_w)
        conf = np.frombuffer(f.conf, dtype=np.uint8).reshape(f.depth_h, f.depth_w)

        dets = None
        if self.det is not None:
            dets = self.det.detect(rotate_jpeg(f.jpeg, turn))
            for d in dets:
                d.box = box_back(d.box, turn, f.rgb_w, f.rgb_h)

        g = self.nav.on_frame(f, dets)
        c = check(depth, conf, f.fx, f.fy, f.cx, f.cy, f.pose, g.desired_bearing or 0.0, self.smoother.last_heading)
        raw_cmd = c.raw_cmd
        if g.hold_center and raw_cmd != "STOP":
            raw_cmd = "CENTER"  # turning on the spot; depth still wins
        cmd, obstacle_speech = self.smoother.update(raw_cmd, c.best, now)
        if g.stop:
            cmd = "STOP"  # the object is within reach; this only ever adds a stop

        ahead = c.clearance.get(0)
        if cmd == "STOP":
            state = "STOP"
        elif ahead is None:
            state = "UNCERTAIN"
        elif cmd != "CENTER" or ahead < USABLE_M:
            state = "CAUTION"
        else:
            state = "CLEAR"

        if g.speech:
            self.speech.append(g.speech)
        msg = {"seq": f.seq, "state": state}
        if state == "STOP":
            msg["earcon"] = "stop"  # the app plays it at most once a second
        elif state == "CAUTION" and self.last_state != "CAUTION":
            msg["earcon"] = "caution"
        self.last_state = state
        if obstacle_speech:
            msg["speech"] = obstacle_speech  # safety speech goes first
        elif self.speech:
            msg["speech"] = self.speech.popleft()

        out = [json.dumps(msg)]
        if g.lookup:
            out.append(json.dumps({"lookup": g.lookup}))
        pi = json.dumps({"seq": f.seq, "cmd": cmd, "ttl_ms": TTL_MS})
        done = time.monotonic()
        self.view = {"jpeg": f.jpeg, "turn": turn, "dets": dets, "depth": depth, "conf": conf}
        self.status = {
            "seq": f.seq, "cmd": cmd, "state": state, "turn": turn * 90, "best": c.best,
            "clearance": {k: (round(v, 2) if v is not None else None) for k, v in c.clearance.items()},
            "floor_seen": c.floor_seen, "nav": f"{g.mode}/{g.state}",
            "desired": None if g.desired_bearing is None else round(g.desired_bearing, 1),
            "dets": [f"{d.label} {d.conf:.2f}" for d in dets] if dets else [],
            "gx10_ms": round((done - t_recv) * 1000, 1), "tracking": f.tracking, "thermal": f.thermal,
            "speech": msg.get("speech"),
        }
        return out, pi


class Server:
    def __init__(self, pipe: Pipeline, record_dir=None):
        self.pipe = pipe
        self.latest = None  # (raw, t_recv, websocket)
        self.new_frame = asyncio.Event()
        self.pis = set()
        self.worker = ThreadPoolExecutor(max_workers=1)  # one frame at a time
        self.writer = ThreadPoolExecutor(max_workers=1)
        self.rx = deque(maxlen=60)
        self.proc_ms = deque(maxlen=60)
        self.dropped = 0
        self.received = 0
        self.phone_ws = None
        self.rec = None
        if record_dir:
            self.rec = Path(record_dir) / time.strftime("%Y%m%d-%H%M%S")
            self.rec.mkdir(parents=True, exist_ok=True)
            print("recording to", self.rec, flush=True)

    async def phone(self, ws):
        print("phone connected:", ws.remote_address[0], flush=True)
        self.phone_ws = ws
        try:
            async for msg in ws:
                t = time.monotonic()
                if isinstance(msg, bytes):
                    self.rx.append(t)
                    self.received += 1
                    if self.latest is not None:
                        self.dropped += 1  # an older frame was still waiting: drop it
                    self.latest = (msg, t, ws)
                    self.new_frame.set()
                    if self.rec:
                        self.writer.submit(self._save, f"{self.received:06d}-{t:.3f}.bin", msg)
                else:
                    self._text(msg)
        except ConnectionClosed:
            pass
        print("phone disconnected:", ws.remote_address[0], flush=True)
        if self.phone_ws is ws:
            self.phone_ws = None

    def text_command(self, text: str):
        """The dashboard's text box: the same as a voice command from the phone."""
        self._text(json.dumps({"text": text}))

    def status(self) -> dict:
        now = time.monotonic()
        ws = self.phone_ws
        rtt = getattr(ws, "latency", 0) if ws else 0
        return {
            "phone": ws.remote_address[0] if ws else None,
            "pis": len(self.pis),
            "fps": sum(1 for t in self.rx if now - t <= 1.0),
            "proc_ms": statistics.median(self.proc_ms) if self.proc_ms else None,
            "rtt_ms": rtt * 1000 if rtt else None,
            "dropped": self.dropped,
            "model": vlm.active_model(),
            "frame": self.pipe.status if now - self.pipe.last_frame < 2 else {},
        }

    def _text(self, msg):
        try:
            m = json.loads(msg)
        except json.JSONDecodeError:
            return
        if self.rec:
            self.writer.submit(self._append, "text.jsonl", json.dumps({"t": time.monotonic(), "msg": m}) + "\n")
        if "text" in m:
            cmd = self.pipe.nav.on_voice(str(m["text"]))
            print(f'voice: {m["text"]!r} -> {cmd.kind} {cmd.target or ""}', flush=True)
        elif "polyline" in m:
            self.pipe.nav.on_route(m)
            print("route:", m.get("dest"), flush=True)

    def _save(self, name, data):
        (self.rec / name).write_bytes(data)

    def _append(self, name, text):
        with open(self.rec / name, "a") as fh:
            fh.write(text)

    async def pi(self, ws):
        print("pi connected:", ws.remote_address[0], flush=True)
        self.pis.add(ws)
        try:
            await ws.wait_closed()
        finally:
            self.pis.discard(ws)
            print("pi disconnected:", ws.remote_address[0], flush=True)

    async def run_frames(self):
        loop = asyncio.get_running_loop()
        while True:
            await self.new_frame.wait()
            self.new_frame.clear()
            raw, t_recv, ws = self.latest
            self.latest = None
            t0 = time.monotonic()
            try:
                out, pi = await loop.run_in_executor(self.worker, self.pipe.process, raw, t_recv)
            except Exception as e:  # a bad frame must not stop the service
                print("frame error:", repr(e), flush=True)
                continue
            self.proc_ms.append((time.monotonic() - t0) * 1000)
            for p in list(self.pis):
                try:
                    await p.send(pi)
                except ConnectionClosed:
                    self.pis.discard(p)
            for text in out:
                try:
                    await ws.send(text)
                except ConnectionClosed:
                    break

    async def report(self):
        while True:
            await asyncio.sleep(1)
            now = time.monotonic()
            fps = sum(1 for t in self.rx if now - t <= 1.0)
            s = self.pipe.status
            if not s or not fps:
                continue
            ms = statistics.median(self.proc_ms) if self.proc_ms else 0
            cl = " ".join(f"{k:+d}:{'?' if v is None else f'{v:.1f}'}" for k, v in s["clearance"].items())
            print(f"{time.strftime('%H:%M:%S')} {fps:2d} fps in, {ms:5.1f} ms  {s['cmd']:6s} {s['state']:9s} "
                  f"[{cl}] floor {'y' if s['floor_seen'] else 'n'} turn {s['turn']} nav {s['nav']} "
                  f"desired {s['desired']} {','.join(s['dets'][:3])} pis {len(self.pis)} dropped {self.dropped}"
                  + (f"  says {s['speech']!r}" if s["speech"] else ""), flush=True)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=os.environ.get("SIGHTSENSE_HOST", "0.0.0.0"))
    ap.add_argument("--phone-port", type=int, default=int(os.environ.get("SIGHTSENSE_PHONE_PORT", "8765")))
    ap.add_argument("--pi-port", type=int, default=int(os.environ.get("SIGHTSENSE_PI_PORT", "8766")))
    ap.add_argument("--dashboard-port", type=int, default=int(os.environ.get("SIGHTSENSE_DASHBOARD_PORT", "8000")),
                    help="0 turns the dashboard off")
    ap.add_argument("--no-yolo", action="store_true")
    ap.add_argument("--record", help="save every frame and text message under this folder")
    a = ap.parse_args()

    server = Server(Pipeline(not a.no_yolo), a.record)
    if a.dashboard_port:
        from dashboard.dashboard import start

        start(server, a.dashboard_port)
    # ping the phone every 2 s: keeps the round trip time for the dashboard, and drops a dead link
    async with serve(server.phone, a.host, a.phone_port, max_size=8 << 20, ping_interval=2, ping_timeout=6), \
            serve(server.pi, a.host, a.pi_port):
        print(f"listening: phone on {a.host}:{a.phone_port}, pi on {a.host}:{a.pi_port}"
              + (f", dashboard on http://{a.host}:{a.dashboard_port}" if a.dashboard_port else ""), flush=True)
        await asyncio.gather(server.run_frames(), server.report())


if __name__ == "__main__":
    asyncio.run(main())

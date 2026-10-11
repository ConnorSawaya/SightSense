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
import math
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
from planner.obstacle import HEADINGS, Smoother, check
from planner.cue import DirectionCue
from planner.speech import ANSWER, GUIDE, SAFETY, SpeechPlan
from planner.state import StateSmoother

from .upright import box_back, decode_upright, rotate_jpeg, turn_for

TTL_MS = 400
# Manual spin from the dashboard: the Pi's direct-drive mode spins the motor one way for LEFT
# (counter-clockwise on the dashboard) and the other for RIGHT (clockwise) while commands keep
# coming, and switches it off for STOP. No positions: CENTER means nothing to a free-spinning motor.
MANUAL_CMDS = ("LEFT", "RIGHT", "STOP")
MANUAL_HOLD_S = 1.0  # back to automatic if the dashboard stops sending for this long (tab closed, link lost)
PI_HEALTH_FRESH_S = 6.0  # the Pi reports every 2 s; older than this is shown as missing
TALK_HOLD_S = 0.6  # the cane's talk button held this long is a hold: letting go ends the command. Shorter is a click
MANUAL_HZ = 10  # commands per second to the Pi in manual mode; also its heartbeat
LOG_LINES = 20  # conversation lines kept for the dashboard
# "sound check", by voice or typed on the dashboard: each tone the phone knows, with its name spoken, one at a time
SOUND_CHECK = (("other", "Sound check. Four tones follow."), ("left", "Left."), ("right", "Right."),
               ("unknown", "Can't see ahead."), ("stop", "Stop. Sound check done."))
SOUND_CHECK_GAP_S = 2.5


def locate(d, f, depth, conf):
    """Distance (LiDAR, median of the box's middle half) and direction of one detection.

    Sets d.dist_m (None if too few good readings) and d.bearing (degrees, positive right,
    in the floor plane like the navigator). Uses depth only, never the model.
    """
    from navigator.frame import camera_to_world, ground_bearing, pixel_to_camera

    sx, sy = f.depth_w / f.rgb_w, f.depth_h / f.rgb_h
    x1, y1, x2, y2 = d.box[0] * sx, d.box[1] * sy, d.box[2] * sx, d.box[3] * sy
    u, v = (x1 + x2) / 2, (y1 + y2) / 2
    hw, hh = max((x2 - x1) / 4, 1), max((y2 - y1) / 4, 1)
    r0, r1 = max(0, int(v - hh)), min(f.depth_h, int(v + hh) + 1)
    c0, c1 = max(0, int(u - hw)), min(f.depth_w, int(u + hw) + 1)
    z, c = depth[r0:r1, c0:c1], conf[r0:r1, c0:c1]
    good = z[(c >= 1) & (z >= 200) & (z <= 5000)]
    d.dist_m = float(np.median(good)) / 1000 if good.size >= 5 else None
    p = camera_to_world(f.pose, pixel_to_camera(f, u, v, d.dist_m or 2.0))
    d.bearing = ground_bearing(f.pose, p)


def side(bearing):
    if bearing is None:
        return ""
    return "ahead" if abs(bearing) < 10 else ("right" if bearing > 0 else "left")


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

    def ask(self, jpeg, question):
        return vlm.ask(rotate_jpeg(jpeg, self.turn), question)

    def objects(self, jpeg):
        return vlm.objects(rotate_jpeg(jpeg, self.turn))

    def interpret(self, text):
        return vlm.interpret(text)  # text only, no picture


def path_answer(cmd, ahead):
    """ "Is the path clear?" from this frame's LiDAR obstacle check only. Never calls it safe.

    cmd is this frame's own command (before smoothing), so a session that has just
    started in STOP does not answer "something is 4 metres ahead, stop".
    """
    from navigator.object_guide import distance_words
    from planner.obstacle import FAR_M, STOP_AHEAD_M, USABLE_M

    if ahead is None:
        return "I can't tell. The depth straight ahead is unclear, so I'm treating it as blocked."
    if ahead < STOP_AHEAD_M or (cmd == "STOP" and ahead < USABLE_M):
        return f"No. Something is {distance_words(ahead)} ahead. Stop."
    turn = {"LEFT": " Steering left.", "RIGHT": " Steering right."}.get(cmd, "")
    if ahead >= FAR_M:  # no obstacle points straight ahead at all, whichever way the wheel is steering
        return f"Nothing detected straight ahead as far as I can measure.{turn} Keep using your cane."
    if cmd == "CENTER" and ahead >= USABLE_M:
        return f"Nothing detected straight ahead for about {distance_words(ahead)}. Keep using your cane."
    return f"Something is {distance_words(ahead)} ahead.{turn}"


class Pipeline:
    def __init__(self, use_yolo: bool):
        try:
            print("vision-language model:", vlm.warm(), flush=True)
        except Exception as e:  # the obstacle check runs from depth alone, so start without the model
            print("vision-language model NOT loaded:", repr(e), flush=True)
            print("describe, read and find will fail until Ollama is up; then restart this service", flush=True)
        self.vlm = UprightVLM()
        self.nav = Navigator(self.vlm)
        self.det = None
        if use_yolo:
            from detector.detector import Detector
            from detector.stable import KEEP, Stabilizer

            self.det = Detector()
            self.stable, self.keep = Stabilizer(), KEEP  # answers held steady across frames
            print("yolo:", self.det.using, flush=True)
        self.smoother = Smoother()
        self.states = StateSmoother()
        self.cue = DirectionCue()
        self.voice = SpeechPlan()  # every sentence goes through it: one at a time, most important first
        self.said = (None, -1e9)
        self.checks, self.next_check = deque(), 0.0  # a sound check under way
        self.last_frame = -1e9
        self.status = {}
        self.view = None  # newest frame's picture and depth, for the dashboard
        self.log = deque(maxlen=LOG_LINES)  # (clock time, "you" | "cane", text), for the dashboard

    def process(self, raw: bytes, t_recv: float):
        f = decode(raw)
        now = time.monotonic()
        if now - self.last_frame > 1.0:  # new session or a gap: start again from STOP, forget old timers
            self.smoother, self.states, self.cue = Smoother(), StateSmoother(), DirectionCue()
            if self.det is not None:
                self.stable.reset()
        self.last_frame = now
        self.vlm.turn = turn = turn_for(f.pose)
        depth = np.frombuffer(f.depth_mm, dtype=np.uint16).reshape(f.depth_h, f.depth_w)
        conf = np.frombuffer(f.conf, dtype=np.uint8).reshape(f.depth_h, f.depth_w)

        dets = None
        upright = decode_upright(f.jpeg, turn)  # decoded once: YOLO and the dashboard share it
        if self.det is not None and upright is not None:
            dets = self.stable.update(self.det.detect_image(upright, conf=self.keep))
            for d in dets:
                d.box = box_back(d.box, turn, f.rgb_w, f.rgb_h)
                locate(d, f, depth, conf)

        g = self.nav.on_frame(f, dets)
        c = check(depth, conf, f.fx, f.fy, f.cx, f.cy, f.pose, g.desired_bearing or 0.0, self.smoother.last_heading,
                  stopped=self.smoother.cmd == "STOP", want_maps=True)  # maps: dashboard obstacle view only
        raw_cmd = c.raw_cmd
        if g.hold_center and raw_cmd != "STOP":
            raw_cmd = "CENTER"  # turning on the spot; depth still wins
        cmd, obstacle_speech = self.smoother.update(raw_cmd, c.best, now)
        if g.stop:
            cmd = "STOP"  # the object is within reach; this only ever adds a stop

        state = self.states.update(cmd, c.clearance.get(0))  # held steady: see planner/state.py
        # sounds only on a change (planner/cue.py); no stop tone for the STOP every session starts in
        cue = self.cue.update(cmd, c.clearance.get(0), now, quiet_stop=raw_cmd != "STOP" and not g.stop)

        if self.nav.take_path_question():
            self.voice.add(path_answer(raw_cmd, c.clearance.get(0)), ANSWER, now)
        if self.nav.take_repeat():
            self.voice.add(self.said[0] or "I haven't said anything yet.", ANSWER, now)
        if g.speech:
            self.voice.add(g.speech, g.speech_kind, now)
        if obstacle_speech:  # "Obstacle ahead. Stop." is safety; "Path blocked. Turn slowly to scan." is guidance
            self.voice.add(obstacle_speech, SAFETY if obstacle_speech.startswith("Obstacle") else GUIDE, now)
        if cue.speech:
            self.voice.add(cue.speech, GUIDE, now)
        if self.nav.take_sound_check():
            self.checks, self.next_check = deque(SOUND_CHECK), now
        msg = {"seq": f.seq, "state": state, "direction": cue.direction}
        if cue.earcon:
            msg["earcon"] = cue.earcon
        speech = self.voice.next(now, thinking=self.nav.thinking)  # see planner/speech.py
        if speech:
            msg["speech"] = speech
        if self.checks and now >= self.next_check and "earcon" not in msg and "speech" not in msg and self.voice.idle(now):
            msg["earcon"], msg["speech"] = self.checks.popleft()  # real guidance always goes first
            self.next_check = now + SOUND_CHECK_GAP_S
        if msg.get("speech"):
            self.said = (msg["speech"], time.monotonic())  # kept for the dashboard; speech is on one frame only
            self.log.append((time.strftime("%H:%M:%S"), "cane", msg["speech"]))

        out = [json.dumps(msg)]
        if g.lookup:
            out.append(json.dumps({"lookup": g.lookup}))
        pi = json.dumps({"seq": f.seq, "cmd": cmd, "ttl_ms": TTL_MS})
        done = time.monotonic()
        self.view = {"jpeg": f.jpeg, "upright": upright, "turn": turn, "dets": dets, "depth": depth, "conf": conf,
                     "maps": c.maps, "clearance": c.clearance, "best": c.best, "cmd": cmd}
        self.status = {
            "seq": f.seq, "cmd": cmd, "state": state, "direction": cue.direction, "turn": turn * 90, "best": c.best,
            "clearance": {k: (round(v, 2) if v is not None else None) for k, v in c.clearance.items()},
            "floor_seen": c.floor_seen, "cam_h": None if c.cam_h is None else round(c.cam_h, 2),
            "nav": f"{g.mode}/{g.state}",
            "desired": None if g.desired_bearing is None else round(g.desired_bearing, 1),
            "dets": [f"{d.label} {d.conf:.2f}" for d in dets] if dets else [],
            "objects": sorted(
                ({"label": d.label, "conf": round(d.conf, 2),
                  "dist_m": None if d.dist_m is None else round(d.dist_m, 1), "side": side(d.bearing)}
                 for d in dets or []),
                key=lambda o: (o["dist_m"] is None, o["dist_m"] or 0)),
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
        self.expired = 0
        self.received = 0
        self.phone_ws = None  # the newest phone connection: the dashboard shows it and the talk button tells it
        self.phones = []  # every open phone connection, oldest first
        self.manual = None  # (cmd, time of the dashboard's last message) while someone steers by hand
        self.manual_sent = None  # what went to the Pi
        self.manual_seq = 0
        self.pi_health = None  # (report, time received, address): temperature, input volts, settings
        self.talk_down = None  # when the cane's talk button went down, while it is held
        self.rec = None
        if record_dir:
            self.rec = Path(record_dir) / time.strftime("%Y%m%d-%H%M%S")
            self.rec.mkdir(parents=True, exist_ok=True)
            print("recording to", self.rec, flush=True)

    async def phone(self, ws):
        print("phone connected:", ws.remote_address[0], flush=True)
        self.phones.append(ws)
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
                    try:
                        self._text(msg)
                    except Exception as e:  # a bad text message must not drop the phone
                        print("text message error:", repr(e), flush=True)
        except ConnectionClosed:
            pass
        finally:
            print("phone disconnected:", ws.remote_address[0], flush=True)
            self.phones.remove(ws)
            if self.phone_ws is ws:
                self.phone_ws = self.phones[-1] if self.phones else None  # an earlier phone may still be connected

    def text_command(self, text: str):
        """The dashboard's text box: the same as a voice command from the phone."""
        self._text(json.dumps({"text": text}))

    def manual_command(self, cmd: str) -> bool:
        """The dashboard's manual spin. "AUTO" hands the wheel back to the pipeline.
        Sent again every 100-200 ms while manual mode is on; stops if that stops."""
        cmd = str(cmd).upper()
        if cmd == "AUTO":
            if self.manual:
                print("manual steering off", flush=True)
            self.manual = self.manual_sent = None
            return True
        if cmd not in MANUAL_CMDS:
            return False
        if not self.manual:
            print("manual steering on", flush=True)
        self.manual = (cmd, time.monotonic())
        return True

    def _obstacle_ahead(self, now):
        """The obstacle check says STOP on a live phone frame. Shown on the dashboard only:
        a manual spin is sent as asked, whatever the free space."""
        return now - self.pipe.last_frame < 0.5 and self.pipe.status.get("cmd") == "STOP"

    async def manual_loop(self):
        while True:
            await asyncio.sleep(1 / MANUAL_HZ)
            manual = self.manual  # read once: the dashboard's thread can clear it at any moment
            if not manual:
                continue
            now = time.monotonic()
            if now - manual[1] > MANUAL_HOLD_S:
                print("manual steering off: the dashboard stopped sending", flush=True)
                if self.manual is manual:
                    self.manual = self.manual_sent = None
                continue
            cmd = manual[0]  # sent as asked: the obstacle check does not apply to a manual spin
            self.manual_seq += 1
            self.manual_sent = {"cmd": cmd, "obstacle_ahead": self._obstacle_ahead(now),
                                "depth_live": now - self.pipe.last_frame < 0.5}
            msg = json.dumps({"seq": self.manual_seq, "cmd": cmd, "ttl_ms": TTL_MS})
            for p in list(self.pis):
                try:
                    await p.send(msg)
                except ConnectionClosed:
                    self.pis.discard(p)

    def status(self) -> dict:
        now = time.monotonic()
        ws = self.phone_ws
        rtt = getattr(ws, "latency", 0) if ws else 0
        return {
            "phone": ws.remote_address[0] if ws else None,
            "pis": len(self.pis),
            "fps": sum(1 for t in list(self.rx) if now - t <= 1.0),  # a copy: the phone's frames add to it from another thread
            "proc_ms": statistics.median(self.proc_ms) if self.proc_ms else None,
            "rtt_ms": rtt * 1000 if rtt else None,
            "dropped": self.dropped,
            "expired": self.expired,
            "model": vlm.active_model(),
            "frame": self.pipe.status if now - self.pipe.last_frame < 2 else {},
            "heard": self.pipe.nav.heard,
            "said": self.pipe.said[0] if now - self.pipe.said[1] < 10 else None,
            "log": list(self.pipe.log),
            "manual": self.manual_sent if self.manual else None,
            "pi_health": self._pi_health(now),
        }

    def _pi_health(self, now):
        if not self.pi_health or now - self.pi_health[1] > PI_HEALTH_FRESH_S:
            return None
        report, t, addr = self.pi_health
        return dict(report, age_s=round(now - t, 1), addr=addr)

    def _text(self, msg):
        try:
            m = json.loads(msg)
        except json.JSONDecodeError:
            return
        if not isinstance(m, dict):
            return
        if self.rec:
            self.writer.submit(self._append, "text.jsonl", json.dumps({"t": time.monotonic(), "msg": m}) + "\n")
        if "text" in m:
            voice = getattr(self.pipe, "voice", None)
            if voice is not None:
                voice.heard()  # the user has finished speaking
            self.pipe.log.append((time.strftime("%H:%M:%S"), "you", str(m["text"])))
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
            async for msg in ws:  # health reports and the talk button; see contracts/MESSAGES.md
                try:
                    m = json.loads(msg)
                except (TypeError, json.JSONDecodeError):
                    continue
                if isinstance(m, dict) and isinstance(m.get("health"), dict):
                    self.pi_health = (m["health"], time.monotonic(), ws.remote_address[0])
                elif isinstance(m, dict) and m.get("button") in ("down", "up"):
                    await self.talk_button(m["button"])
        except ConnectionClosed:
            pass
        finally:
            self.talk_down = None
            self.pis.discard(ws)
            print("pi disconnected:", ws.remote_address[0], flush=True)

    async def talk_button(self, event: str):
        """The talk button in the cane's handle: tell the phone to listen, as if its own talk button were held.

        Down starts it. Up ends it only after a hold; after a click the phone stops by itself when the
        speaker has finished. The phone sends what it heard back as an ordinary {"text": ...} message."""
        now = time.monotonic()
        if event == "down":
            self.talk_down, listen = now, True
            voice = getattr(self.pipe, "voice", None)
            if voice is not None:
                voice.listening(now)  # nothing but safety is said while the user speaks
        else:
            held, self.talk_down = (now - self.talk_down if self.talk_down is not None else 0.0), None
            if held < TALK_HOLD_S:
                return
            listen = False
        ws = self.phone_ws
        what = f"phone told to {'listen' if listen else 'stop listening'}" if ws else "no phone connected"
        print(f"talk button {event}: {what}", flush=True)
        log = getattr(self.pipe, "log", None)
        if log is not None:  # shown in the dashboard's conversation, so the button can be checked without the phone
            log.append((time.strftime("%H:%M:%S"), "cane", f"(talk button {event}: {what})"))
        if ws is None:
            return
        try:
            await ws.send(json.dumps({"listen": listen}))
        except ConnectionClosed:
            pass

    async def run_frames(self):
        loop = asyncio.get_running_loop()
        while True:
            await self.new_frame.wait()
            self.new_frame.clear()
            raw, t_recv, ws = self.latest
            self.latest = None
            if time.monotonic() - t_recv >= TTL_MS / 1000:
                self.expired += 1
                continue
            t0 = time.monotonic()
            try:
                out, pi = await loop.run_in_executor(self.worker, self.pipe.process, raw, t_recv)
            except Exception as e:  # a bad frame must not stop the service
                print("frame error:", repr(e), flush=True)
                continue
            self.proc_ms.append((time.monotonic() - t0) * 1000)
            if self.manual:
                pass  # in manual mode manual_loop talks to the Pi
            elif time.monotonic() - t_recv >= TTL_MS / 1000:
                self.expired += 1
            else:
                await asyncio.gather(*(self._send_pi(p, pi, t_recv) for p in list(self.pis)))
            for text in out:
                try:
                    await ws.send(text)
                except ConnectionClosed:
                    break

    async def _send_pi(self, peer, message, received):
        """Send within the frame's original lifetime; a slow peer must not block others."""
        remaining_ms = math.floor((received + TTL_MS / 1000 - time.monotonic()) * 1000)
        if remaining_ms <= 0:
            return
        command = json.loads(message)
        command["ttl_ms"] = min(command.get("ttl_ms", TTL_MS), remaining_ms)
        try:
            await asyncio.wait_for(peer.send(json.dumps(command)), remaining_ms / 1000)
        except (ConnectionClosed, asyncio.TimeoutError):
            self.pis.discard(peer)
            # A cancelled send may be incomplete: close instead of reusing the peer.
            try:
                await asyncio.wait_for(peer.close(), 1)
            except (ConnectionClosed, asyncio.TimeoutError):
                pass

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
            print(f"{time.strftime('%H:%M:%S')} {fps:2d} fps in, {ms:5.1f} ms  {s['cmd']:6s} {s['state']:9s} {s['direction']:8s} "
                  f"[{cl}] floor {('%.2fm' % s['cam_h']) if s.get('cam_h') is not None else 'n'} turn {s['turn']} nav {s['nav']} "
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
    from planner.obstacle import OWN_CANE_M

    print("own-cane strip ignored: " + (f"{OWN_CANE_M:.2f} m ahead" if OWN_CANE_M > 0 else "off (SIGHTSENSE_OWN_CANE_M)"), flush=True)
    if a.dashboard_port:
        from dashboard.dashboard import start

        start(server, a.dashboard_port)
    # ping the phone every 2 s: keeps the round trip time for the dashboard, and drops a dead link
    async with serve(server.phone, a.host, a.phone_port, max_size=8 << 20, ping_interval=2, ping_timeout=6), \
            serve(server.pi, a.host, a.pi_port):
        print(f"listening: phone on {a.host}:{a.phone_port}, pi on {a.host}:{a.pi_port}"
              + (f", dashboard on http://{a.host}:{a.dashboard_port}" if a.dashboard_port else ""), flush=True)
        await asyncio.gather(server.run_frames(), server.report(), server.manual_loop())


if __name__ == "__main__":
    asyncio.run(main())

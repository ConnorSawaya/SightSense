"""One object for the rest of the GX10 code to talk to.

    nav = Navigator(vlm)                 # vlm: the gx10/vlm package, or a fake
    nav.on_voice("guide me to the apple")  # the {"text": ...} message from the phone
    nav.on_route(route_message)          # the route message from the phone
    g = nav.on_frame(frame)              # every frame; never waits for the model

g.desired_bearing goes to the obstacle check (None = no preference, go straight).
g.stop asks for a stop because the target is within reach. g.speech, if set,
goes in the guidance message's "speech" field. g.lookup, if set, is sent to the
phone as {"lookup": ...}.

None of this decides whether the way is clear. The obstacle check does that from
depth, and it wins.
"""

import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Optional

from . import commands
from .frame import Frame
from .object_guide import ARRIVED, CONFIRMING, GUIDING, IDLE, SEARCHING, ObjectGuide, direction_words, distance_words
from .route import RouteFollower

ROUTE_EVERY_S = 1.0


@dataclass
class Guidance:
    mode: str  # idle, object, route
    state: str  # what the active guide is doing, for the dashboard
    desired_bearing: Optional[float] = None
    hold_center: bool = False
    stop: bool = False
    speech: Optional[str] = None
    lookup: Optional[str] = None
    distance_m: Optional[float] = None


class Navigator:
    def __init__(self, vlm, clock: Callable[[], float] = time.monotonic):
        self._vlm = vlm
        self._clock = clock
        self._lock = threading.Lock()
        self.objects = ObjectGuide(vlm.find, clock)
        self.route: Optional[RouteFollower] = None
        self.mode = "idle"
        self._route_confirm = None  # route waiting for "yes"
        self._place = None
        self._speech = deque()
        self._lookup = None
        self._ask = None  # ("describe" | "read" | "question", question), waiting for the next frame
        self._asking = False
        self._interpreting = False  # the model is working out a sentence the rules did not understand
        self._last = None  # the last Guidance, for "am I going the right way"
        self._last_route = -1e9
        self._route_step = None

    # ------------------------------------------------------------ from the phone

    def on_voice(self, text: str) -> commands.Command:
        """Rules first: instant and predictable. A sentence they do not understand goes to the
        model (vlm.interpret), which only picks one of the same commands, plus "status" (answered
        from the navigator's own numbers) and "question" (answered from the picture)."""
        cmd = commands.parse(text)
        with self._lock:
            if cmd.kind == "unknown" and hasattr(self._vlm, "interpret"):
                if self._interpreting:
                    self._say("One moment.")
                else:
                    self._interpreting = True
                    threading.Thread(target=self._interpret_worker, args=(text,), daemon=True).start()
                return commands.Command("interpret", text)
            self._apply(cmd)
        return cmd

    def _apply(self, cmd: commands.Command):
        """Carry out a command. Call with the lock held."""
        if cmd.kind == "object":
            self._stop_route()
            self.mode = "object"
            self._say(self.objects.start(cmd.target))
        elif cmd.kind == "place":
            self.objects.cancel()
            self._stop_route()
            self.mode = "route"
            self._place = cmd.target
            self._lookup = cmd.target
            self._say(f"Looking up {cmd.target}.")
        elif cmd.kind in ("yes", "no"):
            yes = cmd.kind == "yes"
            if self._route_confirm is not None:
                if yes:
                    self.route, self._route_confirm = self._route_confirm, None
                    self._say(f"Going to {self.route.dest}.")
                else:
                    self._stop_route()
                    self.mode = "idle"
                    self._say("Cancelled.")
            else:
                said = self.objects.confirm(yes)
                if said:
                    self._say(said)
                    if not yes:
                        self.mode = "idle"
        elif cmd.kind == "cancel":
            said = self.objects.cancel()
            had_route = self.route is not None or self._route_confirm is not None or self._place
            self._stop_route()
            self.mode = "idle"
            self._say(said or ("Cancelled." if had_route else "Stopped."))
        elif cmd.kind in ("describe", "read"):
            self._ask = (cmd.kind, None)
        elif cmd.kind == "question":
            self._ask = ("question", cmd.target)
        elif cmd.kind == "status":
            self._say(self._status())
        else:
            self._say("Sorry, I didn't catch that.")

    def on_route(self, route: dict):
        with self._lock:
            try:
                follower = RouteFollower(route, self._clock)
            except (ValueError, KeyError, TypeError):
                self._say("I couldn't find a walking route.")
                return
            if self.route is not None:  # a reroute while already walking: switch straight over
                self.route = follower
                return
            self._route_confirm = follower
            self.mode = "route"
            parts = [follower.dest]
            if route.get("distance_m") is not None:
                parts.append(f"{round(route['distance_m'] / 10) * 10:g} metres")
            if route.get("eta_min") is not None:
                parts.append(f"about {round(route['eta_min'])} minutes")
            self._say(", ".join(parts) + ". Say yes to go.")

    # ------------------------------------------------------------ every frame

    def on_frame(self, f: Frame, detections=None) -> Guidance:
        """detections: this frame's YOLO results from gx10/detector, if it is running."""
        with self._lock:
            if self._ask and not self._asking and f.jpeg:
                (kind, question), self._ask, self._asking = self._ask, None, True
                threading.Thread(target=self._ask_worker, args=(kind, f.jpeg, question), daemon=True).start()

            g = Guidance(self.mode, IDLE)
            if self.mode == "object":
                step = self.objects.update(f, detections)
                g.state, g.desired_bearing, g.stop, g.distance_m = step.state, step.desired_bearing, step.stop, step.distance_m
                if step.speech:
                    self._say(step.speech)
                if step.state == IDLE:
                    self.mode = "idle"
            elif self.mode == "route":
                g.state = "LOOKUP" if self.route is None and self._route_confirm is None else "CONFIRMING" if self.route is None else "FOLLOWING"
                if self.route is not None:
                    now = self._clock()
                    if now - self._last_route >= ROUTE_EVERY_S:
                        self._last_route = now
                        self._route_step = self.route.update(f.lat, f.lon, f.gps_acc_m, f.heading_deg)
                        if self._route_step.speech:
                            self._say(self._route_step.speech)
                        if self._route_step.lookup:
                            self._lookup = self._route_step.lookup
                        if self._route_step.arrived:
                            self._stop_route()
                            self.mode = "idle"
                    s = self._route_step
                    if s is not None and self.route is not None:
                        g.desired_bearing, g.hold_center, g.distance_m = s.desired_bearing, s.hold_center, s.remaining_m

            g.speech = self._speech.popleft() if self._speech else None
            g.lookup, self._lookup = self._lookup, None
            self._last = g
            return g

    # ------------------------------------------------------------ internals

    def _say(self, text):
        if text:
            self._speech.append(text)

    def _stop_route(self):
        self.route = self._route_confirm = self._route_step = self._place = None

    def _interpret_worker(self, text):
        try:
            a = self._vlm.interpret(text)
        except Exception as e:
            print(f"navigator: interpret failed: {e}")
            a = None
        with self._lock:
            self._interpreting = False
            if a is None or not a.ok:
                error = getattr(a, "error", None) or ("exception" if a is None else "failed")
                busy = error.startswith("busy")
                print(f"navigator: model could not interpret {text!r}: {error}", flush=True)
                self._say("One moment, then ask again." if busy else "Sorry, I didn't catch that.")
                return
            cmd = commands.Command(a.label, a.text or None)
            if cmd.kind in ("object", "place") and not cmd.target:
                cmd = commands.Command("unknown")
            if cmd.kind == "question" and not cmd.target:
                cmd.target = text
            print(f"navigator: model read {text!r} as {cmd.kind} {cmd.target or ''} ({getattr(a, 'seconds', 0):.2f} s)", flush=True)
            self._apply(cmd)

    def _status(self) -> str:
        """Answer "am I going the right way" from the navigator's own numbers, never from the model."""
        g = self._last
        if self.mode == "object":
            o, name = self.objects, self.objects.name
            if o.state == SEARCHING:
                return f"I'm still looking for the {name}. Turn slowly to scan."
            if o.state == CONFIRMING:
                return f"I found the {name}. Say yes to go."
            if o.state == GUIDING and g is not None and g.distance_m is not None and g.desired_bearing is not None:
                return f"Yes. The {name} is {distance_words(g.distance_m)}, {direction_words(g.desired_bearing)}."
            if o.state == GUIDING:
                return f"Going to the {name}."
        if self.mode == "route":
            if self.route is None:
                return f"Say yes to go to {self._route_confirm.dest}." if self._route_confirm else f"Still looking up {self._place}."
            s = self._route_step
            if s is None:
                return f"Starting the route to {self.route.dest}."
            if s.desired_bearing is None:
                return "GPS is weak, so I can't tell right now."
            left = "" if s.remaining_m is None else f" About {max(10, round(s.remaining_m / 10) * 10):g} metres to go."
            if abs(s.desired_bearing) <= 30:
                return f"Yes, you're on the way to {self.route.dest}.{left}"
            return f"Not quite. {self.route.dest} is {direction_words(s.desired_bearing)}.{left}"
        return "You're not being guided right now. Say guide me to, and a thing or a place."

    def _ask_worker(self, kind, jpeg, question=None):
        try:
            a = self._vlm.ask(jpeg, question) if kind == "question" else getattr(self._vlm, kind)(jpeg)
            if not a.ok:
                text = a.text
            elif kind == "read":
                text = a.text.replace("\n", ". ") if a.text else "I don't see any text."
            else:
                text = a.text
        except Exception as e:
            print(f"navigator: {kind} failed: {e}")
            text = "I couldn't tell"
        with self._lock:
            self._say(text)
            self._asking = False

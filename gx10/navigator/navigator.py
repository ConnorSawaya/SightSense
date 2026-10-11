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

import re
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
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


HELP = ("I can tell you what is in front of you, read signs, answer a question about what the camera sees, "
        "guide you to an object, or take you to a place. Say stop to cancel.")


def time_words(now) -> str:
    """The time and date as a sentence, from the GX10's own clock."""
    hour = now.hour % 12 or 12
    return f"It's {hour}:{now.minute:02d} {'AM' if now.hour < 12 else 'PM'}, {now.strftime('%A, %B')} {now.day}."


class Navigator:
    def __init__(self, vlm, clock: Callable[[], float] = time.monotonic, now=datetime.now):
        self._vlm = vlm
        self._clock = clock
        self._now = now  # wall clock, for "what time is it"
        self._lock = threading.Lock()
        self.objects = ObjectGuide(vlm.find, clock)
        self.route: Optional[RouteFollower] = None
        self.mode = "idle"
        self._route_confirm = None  # route waiting for "yes"
        self._place = None
        self._replaced = None  # a place whose lookup was still out when the user asked for another
        self._speech = deque()
        self._lookup = None
        self._ask = None  # ("describe" | "read" | "ask", question), waiting for the next frame
        self._asking = False
        self._interpreting = False  # the model is working out a sentence the rules could not place
        self.heard = None  # last voice command, for the dashboard: {"text", "kind", "target", "by"}
        self._last_obj = None  # the object guide's last step, for "am I going the right way"
        self.path_asked = False  # "is the path clear": the frame service answers from depth
        self.repeat_asked = False  # "say that again": the frame service knows the last sentence sent
        self.sound_check_asked = False  # "sound check": the frame service sends each tone with its name
        self._last_route = -1e9
        self._route_step = None

    # ------------------------------------------------------------ from the phone

    def on_voice(self, text: str) -> commands.Command:
        """Rules first: instant and predictable. A sentence they cannot place, or a request
        worded as a question ("could you take me to the door?"), goes to the model
        (vlm.interpret), which only picks one of the same commands."""
        cmd = commands.parse(text)
        with self._lock:
            self.heard = {"text": text, "kind": cmd.kind, "target": cmd.target, "by": "rules"}
            if hasattr(self._vlm, "interpret") and (cmd.kind == "unknown" or (cmd.kind == "ask" and _request(text))):
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
            self._replaced = self._place if self.route is None and self._route_confirm is None else None
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
        elif cmd.kind == "ask":
            self._ask = ("ask", cmd.target)
        elif cmd.kind == "status":
            self._say(self._status())
        elif cmd.kind == "path":
            self.path_asked = True
        elif cmd.kind == "help":
            self._say(HELP)
        elif cmd.kind == "repeat":
            self.repeat_asked = True
        elif cmd.kind == "soundcheck":
            self.sound_check_asked = True
        elif cmd.kind == "time":
            self._say(time_words(self._now()))
        else:
            self._say("Sorry, I didn't catch that. You can say: what's in front of me, read the sign, "
                      "or guide me to the apple.")

    def on_route(self, route: dict):
        with self._lock:
            if self.route is None and self._place is None:
                return  # no lookup is waiting: it was cancelled, or the user asked for something else
            try:
                follower = RouteFollower(route, self._clock)
            except (ValueError, KeyError, TypeError):
                if self.route is None and self._replaced and route.get("dest") == self._replaced != self._place:
                    self._replaced = None
                    return  # the earlier lookup failing; the newer one is still out
                self._say("I couldn't find a walking route.")
                if self.route is None:  # a first lookup, not a reroute: nothing is left to wait for
                    self._stop_route()
                    self.mode = "idle"
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
                threading.Thread(target=self._ask_worker, args=(kind, question, f.jpeg), daemon=True).start()

            g = Guidance(self.mode, IDLE)
            if self.mode == "object":
                step = self.objects.update(f, detections)
                self._last_obj = step
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
            return g

    # ------------------------------------------------------------ internals

    def _interpret_worker(self, text):
        try:
            a = self._vlm.interpret(text)
        except Exception as e:
            print(f"navigator: interpret failed: {e}", flush=True)
            a = None
        with self._lock:
            self._interpreting = False
            if a is None or not a.ok:
                error = getattr(a, "error", None) or ("exception" if a is None else "failed")
                print(f"navigator: model could not place {text!r}: {error}", flush=True)
                self.heard = {"text": text, "kind": "unknown", "target": None, "by": "model"}
                self._apply(commands.Command("unknown"))
                return
            cmd = commands.Command(a.label, a.text or None)
            if cmd.kind in ("object", "place") and not cmd.target:
                cmd = commands.Command("unknown")
            if cmd.kind == "ask":
                cmd.target = text  # ask with the whole sentence; the model shortens it ("colour")
            self.heard = {"text": text, "kind": cmd.kind, "target": cmd.target, "by": "model"}
            print(f"navigator: model read {text!r} as {cmd.kind} {cmd.target or ''} "
                  f"({getattr(a, 'seconds', 0):.2f} s)", flush=True)
            self._apply(cmd)

    def take_sound_check(self) -> bool:
        """True once after "sound check"; the frame service sends the tones."""
        with self._lock:
            asked, self.sound_check_asked = self.sound_check_asked, False
            return asked

    def take_repeat(self) -> bool:
        """True once after "say that again"; the frame service repeats the last sentence it sent."""
        with self._lock:
            asked, self.repeat_asked = self.repeat_asked, False
            return asked

    def take_path_question(self) -> bool:
        """True once after "is the path clear?"; the frame service answers it from depth."""
        with self._lock:
            asked, self.path_asked = self.path_asked, False
            return asked

    def _status(self) -> str:
        """Answer to "am I going the right way?" (called with the lock held)."""
        if self.mode == "object":
            name, s = self.objects.name, self._last_obj
            state = s.state if s else self.objects.state
            if state == SEARCHING:
                return f"Still looking for the {name}."
            if state == CONFIRMING:
                return f"I found the {name}. Say yes to go."
            if state == ARRIVED:
                return f"The {name} is within reach."
            if state == GUIDING and s and s.desired_bearing is not None and s.distance_m is not None:
                b, d = s.desired_bearing, distance_words(s.distance_m)
                if abs(b) < 15:
                    return f"Yes. The {name} is straight ahead, {d} away."
                side = "right" if b > 0 else "left"
                return f"Turn {side}. The {name} is {direction_words(b)}, {d} away."
            return f"I'm looking for the {name} again."
        if self.mode == "route":
            if self.route is None:
                return f"Still looking up {self._place}." if self._route_confirm is None else \
                    f"The route to {self._route_confirm.dest} is ready. Say yes to go."
            s = self._route_step
            if s is None:
                return f"Starting the route to {self.route.dest}."
            if s.hold_center and s.turn:
                return f"Not yet. Turn {s.turn} until I stop saying turn."
            if s.off_route_m is None:  # the last update had no usable GPS fix
                return "I can't tell. GPS is weak, so route guidance is paused."
            if s.desired_bearing is None and not s.hold_center:  # GPS, but no compass heading
                return "I can't tell which way you are facing. There is no compass heading."
            if s.off_route_m is not None and s.off_route_m > 15:
                return f"You are about {round(s.off_route_m)} metres off the route. I'll reroute if it continues."
            left = f" About {round(s.remaining_m / 10) * 10:g} metres to go." if s.remaining_m else ""
            return f"Yes, you're on the route to {self.route.dest}.{left}"
        return "No destination yet. Say guide me to the apple, or take me to a place."

    def _say(self, text):
        if text:
            self._speech.append(text)

    def _stop_route(self):
        self.route = self._route_confirm = self._route_step = self._place = None

    def _ask_worker(self, kind, question, jpeg):
        try:
            a = self._vlm.ask(jpeg, question) if kind == "ask" else getattr(self._vlm, kind)(jpeg)
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


def _request(text: str) -> bool:
    """A command worded as a question: "could you take me to the door?", "can you find my keys"."""
    return bool(re.match(r"\s*(?:(?:hey|ok|okay|please)[, ]+)?(?:can|could|would|will) you\b", text or "", re.IGNORECASE))

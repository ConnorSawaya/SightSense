"""Guide to a named object ("guide me to the apple"), following AGENTS.md.

Call update() with every frame. It never waits for the vision-language model:
find() runs on a background thread on a copy of one frame, and its answer is
used when it arrives. The model only supplies a box; the distance comes from the
LiDAR depth inside it, and the target is stored as a point in the ARKit world so
guidance continues when it leaves view.

This only produces a desired bearing. Whether that way is clear is the obstacle
check's job, from depth; it may steer elsewhere or stop.
"""

import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

from .frame import Frame, box_distance, camera_position, camera_to_world, ground_bearing, ground_distance, pixel_to_camera

# Starting values from AGENTS.md, to tune
REFIND_GUIDING_S = 2.0
REFIND_SEARCHING_S = 1.5
LOST_AFTER_S = 10.0  # not seen for this long and no stored point -> "I lost the ..."
REACH_M = 1.2  # keep above obstacle.STOP_AHEAD_M (0.8) plus how far an object sits back on a table, or the obstacle stop comes first
SEARCH_GIVE_UP_S = 30.0  # added: stop searching after this long
CONFIRM_TIMEOUT_S = 20.0  # added: no "yes" within this long -> cancel
POSE_JUMP_M = 0.5  # added: camera moving this far between frames means tracking reset
POSE_JUMP_WITHIN_S = 0.25

IDLE, SEARCHING, CONFIRMING, GUIDING, ARRIVED = "IDLE", "SEARCHING", "CONFIRMING", "GUIDING", "ARRIVED"


@dataclass
class Step:
    state: str
    desired_bearing: Optional[float] = None  # degrees, positive right; None = no preference
    stop: bool = False  # True: the target is within reach
    speech: Optional[str] = None  # say this once
    distance_m: Optional[float] = None  # to the stored target, floor distance


# What people call things vs the detectors' labels (YOLO's 80 objects, YOLOE's hazards)
SAME = {
    "computer": ("laptop", "tv", "keyboard"), "monitor": ("tv",), "screen": ("tv", "laptop"), "television": ("tv",),
    "sofa": ("couch",), "table": ("dining table",), "desk": ("dining table",), "phone": ("cell phone",),
    "mobile": ("cell phone",), "bin": ("trash can",), "trash": ("trash can",), "garbage can": ("trash can",),
    "doorway": ("door",), "exit": ("door",), "staircase": ("stairs",), "steps": ("stairs",), "man": ("person",),
    "woman": ("person",), "someone": ("person",), "people": ("person",), "bag": ("backpack", "handbag", "suitcase"),
    "mug": ("cup",), "plant": ("potted plant",), "seat": ("chair", "couch", "bench"), "post": ("pole",),
    "kerb": ("curb",), "cone": ("traffic cone",), "fridge": ("refrigerator",),
}


def _same_thing(label: str, name: str) -> bool:
    """Detector label vs what the user asked for: "apple" matches "apple" and "red apple";
    "computer" matches "laptop" (SAME)."""
    label, name = label.lower(), name.lower()
    if name == label or name.endswith(" " + label):
        return True
    noun = name.split()[-1] if name.split() else name
    return label in SAME.get(name, ()) or label in SAME.get(noun, ())


def direction_words(bearing: float) -> str:
    side = "right" if bearing > 0 else "left"
    b = abs(bearing)
    if b < 5:
        return "straight ahead"
    if b < 20:
        return f"slightly {side}"
    if b < 60:
        return f"to your {side}"
    return f"far to your {side}" if b < 135 else "behind you"


def distance_words(m: float) -> str:
    half = round(m * 2) / 2
    if half < 1:
        return "less than a metre"
    n = f"{half:g}"
    return f"{n} metre" + ("" if half == 1 else "s")


class ObjectGuide:
    def __init__(self, find: Callable, clock: Callable[[], float] = time.monotonic):
        """find(jpeg, name) returns an object with .ok and .box (pixels or None), like vlm.find."""
        self._find = find
        self._clock = clock
        self._lock = threading.Lock()
        self._reset(IDLE)

    # ------------------------------------------------------------ commands

    def start(self, name: str, side: Optional[str] = None) -> str:
        """side: "left" or "right" when the user said ("the door on the left"): a detection on that side wins."""
        with self._lock:
            self._reset(SEARCHING)
            self.name = name
            self.side = side
            self._started = self._clock()
            return f"Looking for the {name}" + (f" on your {side}." if side else ".")

    def confirm(self, yes: bool) -> Optional[str]:
        with self._lock:
            if self.state != CONFIRMING:
                return None
            if not yes:
                self._reset(IDLE)
                return "Cancelled."
            self.state = GUIDING
            return f"Going to the {self.name}."

    def cancel(self) -> Optional[str]:
        with self._lock:
            was = self.state
            self._reset(IDLE)
            return "Cancelled." if was not in (IDLE, ARRIVED) else None

    # ------------------------------------------------------------ every frame

    def update(self, f: Frame, detections=None) -> Step:
        """detections: this frame's YOLO results (objects with .label, .conf, .box), if any.

        A detection whose label matches the target is used at once, like a find()
        answer, so objects YOLO knows are refreshed every frame.
        """
        with self._lock:
            now = self._clock()
            if self.state == IDLE:
                return Step(IDLE)
            self._check_tracking(f, now)
            speech = self._take_result(now)
            if detections and self.state in (SEARCHING, GUIDING):
                match = [d for d in detections if _same_thing(d.label, self.name)]
                if match and getattr(self, "side", None):
                    sign = 1 if self.side == "right" else -1
                    on_side = [d for d in match if (getattr(d, "bearing", None) or 0) * sign > 0]
                    match = on_side or match
                if match:
                    speech = self._use_box(f, max(match, key=lambda d: d.conf).box, now) or speech
            if self.state in (SEARCHING, GUIDING):
                self._maybe_find(f, now)

            if self.state == SEARCHING:
                if now - self._started > SEARCH_GIVE_UP_S:
                    name = self.name
                    self._reset(IDLE)
                    return Step(IDLE, speech=f"I couldn't find the {name}.")
                if speech is None and now - self._last_hint > LOST_AFTER_S:
                    self._last_hint = now
                    speech = f"I can't see the {self.name} yet. Turn slowly to scan."
                return Step(SEARCHING, speech=speech)

            if self.state == CONFIRMING:
                if now - self._confirm_asked > CONFIRM_TIMEOUT_S:
                    self._reset(IDLE)
                    return Step(IDLE, speech="Cancelled.")
                return Step(CONFIRMING, speech=speech, distance_m=self._distance(f))

            if self.state == GUIDING:
                if self.target is None:
                    if now - self._last_seen > LOST_AFTER_S:
                        name = self.name
                        self._reset(IDLE)
                        return Step(IDLE, speech=f"I lost the {name}.")
                    return Step(GUIDING, speech=speech)
                dist = self._distance(f)
                if dist < REACH_M:
                    self.state = ARRIVED
                    return Step(ARRIVED, stop=True, speech=f"The {self.name} is within reach.", distance_m=dist)
                return Step(GUIDING, ground_bearing(f.pose, self.target), speech=speech, distance_m=dist)

            # ARRIVED: keep asking for a stop until the next command
            return Step(ARRIVED, stop=True, distance_m=self._distance(f))

    # ------------------------------------------------------------ internals

    def _reset(self, state):
        self.state = state
        self.name = getattr(self, "name", "")
        self.side = None  # set by start() after the reset
        self.target = None  # (x, y, z) in the ARKit world
        self._started = self._last_seen = self._last_find = self._confirm_asked = -1e9
        self._last_hint = self._clock()
        self._pending = None  # result from the worker thread
        self._busy = False
        self._generation = getattr(self, "_generation", 0) + 1  # ignore answers to old requests
        self._last_pos = None

    def _distance(self, f):
        return ground_distance(camera_position(f.pose), self.target) if self.target else None

    def _check_tracking(self, f, now):
        pos = camera_position(f.pose)
        jumped = (
            self._last_pos is not None
            and now - self._last_pos[1] < POSE_JUMP_WITHIN_S
            and ground_distance(pos, self._last_pos[0]) > POSE_JUMP_M
        )
        self._last_pos = (pos, now)
        if jumped or f.tracking in ("notAvailable", "relocalizing"):
            self.target = None  # stored positions are wrong after a tracking reset
            if self.state == CONFIRMING:
                self.state = SEARCHING

    def _maybe_find(self, f, now):
        every = REFIND_GUIDING_S if self.state == GUIDING else REFIND_SEARCHING_S
        if self._busy or now - self._last_find < every or not f.jpeg:
            return
        self._busy, self._last_find = True, now
        snapshot, gen, name = f, self._generation, self.name
        threading.Thread(target=self._worker, args=(snapshot, gen, name), daemon=True).start()

    def _worker(self, f, gen, name):
        try:
            answer = self._find(f.jpeg, name)
        except Exception as e:  # never let a model problem kill guidance
            answer = None
            print(f"object_guide: find failed: {e}")
        with self._lock:
            if gen == self._generation:
                self._pending = (f, answer)
                self._busy = False

    def _take_result(self, now) -> Optional[str]:
        if self._pending is None:
            return None
        f, answer = self._pending
        self._pending = None
        if answer is None or not answer.ok or not answer.box:
            return None  # busy, timed out, unparseable or not seen: try again next time
        return self._use_box(f, answer.box, now)

    def _use_box(self, f, box, now) -> Optional[str]:
        dist, u, v = box_distance(f, box)
        if dist is None:
            return f"I see the {self.name} but can't tell how far it is." if self.state == SEARCHING else None
        # Stored in the world using the pose of the frame the model looked at
        self.target = camera_to_world(f.pose, pixel_to_camera(f, u, v, dist))
        self._last_seen = now
        if self.state == SEARCHING:
            self.state = CONFIRMING
            self._confirm_asked = now
            bearing = ground_bearing(f.pose, self.target)
            where = direction_words(bearing) if bearing is not None else "ahead"
            floor = ground_distance(camera_position(f.pose), self.target)
            return f"{self.name.capitalize()}, {distance_words(floor)}, {where}. Say yes to go."
        return None

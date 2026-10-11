"""Spoken guidance around obstacles: what is in the way, how far, and which way is open.

The wheel is still decided by planner/obstacle.py from depth alone. This only puts that
decision into words, naming the thing from the detectors when one is in the way:

    entering STOP        "Stop. Chair ahead, about 1 metre. Open to your left."
                         "Stop. Something ahead, less than a metre."
                         "Stop. I can't see clearly ahead."
    steering round it    "Chair ahead. Bear left around it."   (instead of a bare "Bear left")
    past it              "You're past it. Carry on."
    hazard()             "Careful: chair ahead, about 1 metre."  said before an answer while something is close

Distances come from the LiDAR clearance, never from a model. Standard library only.
"""

from typing import Optional

from .obstacle import STOP_AHEAD_M, USABLE_M

LEFT_SIDE, RIGHT_SIDE = (-30, -20, -10), (10, 20, 30)
NAME_WITHIN_DEG = 12  # a named object counts as "the thing ahead" within this many degrees of straight on
NAME_SLACK_M = 0.7  # ... and not much farther than the clearance straight ahead
NICE = {"dining table": "table", "potted plant": "plant", "tv": "TV", "cell phone": "phone", "person": "someone",
        "traffic cone": "cone", "trash can": "bin"}


def _metres(m: float) -> str:
    from navigator.object_guide import distance_words

    words = distance_words(m)
    return words if words.startswith("less") else "about " + words


def thing_ahead(dets, ahead: Optional[float]) -> Optional[str]:
    """The nearest detected thing roughly straight ahead, at about the blocking distance."""
    best = None
    for d in dets or []:
        b, m = getattr(d, "bearing", None), getattr(d, "dist_m", None)
        if b is None or abs(b) > NAME_WITHIN_DEG or m is None:
            continue
        if ahead is not None and m > ahead + NAME_SLACK_M:
            continue
        if best is None or m < best[0]:
            best = (m, d.label)
    return NICE.get(best[1], best[1]) if best else None


def open_side(clearance: dict) -> Optional[str]:
    """"left" or "right": the side whose best heading is open, the wider one if both are."""
    def widest(side):
        known = [clearance.get(h) for h in side if clearance.get(h) is not None]
        return max(known) if known else 0.0
    left, right = widest(LEFT_SIDE), widest(RIGHT_SIDE)
    if max(left, right) < USABLE_M:
        return None
    return "left" if left >= right else "right"


class ObstacleTalk:
    def __init__(self):
        self._last_cmd = None
        self._around = None  # (side, name) while steering round something

    def update(self, cmd: str, clearance: dict, dets) -> dict:
        """Call every frame with the smoothed wheel command. Returns {"stop": sentence} on entering a stop,
        {"around": sentence} when starting to steer round something, {"past": sentence} once clear."""
        ahead = clearance.get(0)
        out = {}
        if cmd == "STOP" and self._last_cmd not in (None, "STOP"):
            out["stop"] = self.stop_sentence(clearance, dets)
            self._around = None
        elif cmd in ("LEFT", "RIGHT"):
            if ahead is not None and ahead < USABLE_M:  # turning because something is in the way
                side = cmd.lower()
                name = thing_ahead(dets, ahead)
                if self._around is None or self._around[0] != side:
                    what = (name.capitalize() if name and name != "someone" else "Someone" if name else "Something")
                    out["around"] = f"{what} ahead. Bear {side} around it."
                self._around = (side, name)
        elif cmd == "CENTER" and self._around is not None:
            if ahead is None or ahead >= USABLE_M:
                out["past"] = "You're past it. Carry on."
                self._around = None
        self._last_cmd = cmd
        return out

    @property
    def around_side(self) -> Optional[str]:
        """"left" or "right" while steering round something (its sentence replaces a bare "Bear left")."""
        return self._around[0] if self._around else None

    def stop_sentence(self, clearance: dict, dets, action: Optional[str] = None) -> str:
        """action: what to do next, from planner/recovery.py ("Turn left."); else which side is open, if one is."""
        ahead = clearance.get(0)
        if ahead is None:
            return "Stop. I can't see clearly ahead." + (f" {action}" if action else "")
        name = thing_ahead(dets, ahead) or "something"
        what = f"{name.capitalize()} ahead, {_metres(ahead)}."
        if action:
            return f"Stop. {what} {action}"
        side = open_side(clearance)
        return f"Stop. {what}" + (f" Open to your {side}." if side else "")

    def hazard(self, cmd: str, clearance: dict, dets) -> Optional[str]:
        """A short warning to put before an answer, or None if nothing is close."""
        ahead = clearance.get(0)
        if ahead is not None and ahead >= USABLE_M:
            return None  # nothing close straight ahead (a session also starts in STOP: that alone is no warning)
        if ahead is None:
            return "Careful: I can't see clearly ahead."
        name = thing_ahead(dets, ahead) or "something"
        return f"Careful: {name} ahead, {_metres(ahead)}."

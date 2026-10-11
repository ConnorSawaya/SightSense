"""Which way to go, told to the user only when it changes (LEFT, STRAIGHT, RIGHT, STOP, UNKNOWN).

Before this the phone got CLEAR / CAUTION / STOP and a beep with them: the stop beep came
with every frame (the app played it once a second for as long as STOP lasted) and the
caution beep every time CAUTION came back. Indoors that was beeping nearly all the time
(October 10 evening walk). Now:

- The direction is the smoothed wheel command, so the voice and the wheel always agree.
- LEFT / RIGHT: a tone in that ear and "Bear left" / "Bear right", once, when it starts.
  At most one spoken direction every GAP_S; the same direction is not repeated within REPEAT_S.
- STRAIGHT: silent. Silence means keep going.
- STOP: one stop tone when it starts (the obstacle smoother adds the speech). Never delayed.
- UNKNOWN (no depth reading straight ahead): after UNKNOWN_FRAMES frames, a low tone and
  "Can't see ahead", once.

Every number is a starting value to tune, not a measured result.
"""

from dataclasses import dataclass
from typing import Optional

GAP_S = 2.0  # at most one spoken direction this often (STOP is never held back)
REPEAT_S = 4.0  # the same direction again only after this long
UNKNOWN_FRAMES = 3

WORDS = {"LEFT": "Bear left", "RIGHT": "Bear right", "UNKNOWN": "Can't see ahead"}
EARCONS = {"LEFT": "left", "RIGHT": "right", "STOP": "stop", "UNKNOWN": "unknown"}


def direction_for(cmd: str, ahead: Optional[float]) -> str:
    if cmd == "STOP":
        return "STOP"
    if ahead is None and cmd == "CENTER":
        return "UNKNOWN"
    return {"LEFT": "LEFT", "RIGHT": "RIGHT"}.get(cmd, "STRAIGHT")


@dataclass
class Cue:
    direction: str
    earcon: Optional[str] = None
    speech: Optional[str] = None


class DirectionCue:
    def __init__(self):
        self.direction = None  # what the phone shows
        self._unknown = 0
        self._told = None  # (direction, time) last announced
        self._pending = None  # a direction still to announce once GAP_S has passed

    def update(self, cmd: str, ahead: Optional[float], now: float) -> Cue:
        d = direction_for(cmd, ahead)
        if d == "UNKNOWN":
            self._unknown += 1
            if self._unknown < UNKNOWN_FRAMES and self.direction is not None:
                d = self.direction if self.direction != "UNKNOWN" else d  # brief gaps keep the last direction
        else:
            self._unknown = 0

        changed = d != self.direction
        self.direction = d
        if d == "STOP":
            self._pending = None
            if changed:
                self._told = ("STOP", now)
                return Cue(d, earcon="stop")
            return Cue(d)
        if d == "STRAIGHT":
            self._pending = None
            return Cue(d)
        if changed:
            self._pending = d
        if self._pending != d:
            return Cue(d)
        last_dir, last_t = self._told or (None, -1e9)
        if now - last_t < GAP_S or (last_dir == d and now - last_t < REPEAT_S):
            return Cue(d)  # keep it pending: said once the gap has passed, if still true
        self._pending = None
        self._told = (d, now)
        return Cue(d, earcon=EARCONS[d], speech=WORDS[d])

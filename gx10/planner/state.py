"""The guidance state sent to the phone (CLEAR, CAUTION, STOP, UNCERTAIN), held steady.

Worked out fresh on every frame, the state flickered between CLEAR and CAUTION
when the phone was held still about 2.5 m from something: LiDAR noise of a few
centimetres moves the clearance ahead back and forth across USABLE_M, and every
flip into CAUTION played the caution earcon.

- STOP follows the smoothed command at once, both ways; it is never delayed here.
  Leaving STOP goes to CAUTION first.
- Into CAUTION: clearance ahead under USABLE_M, or the wheel is turning, for 2 frames.
- Back to CLEAR: clearance ahead at least USABLE_M + CLEAR_MARGIN_M and the wheel
  centred, for CLEAR_FRAMES frames in a row.
- UNCERTAIN (no reading ahead) needs 2 frames, and leaving it needs 2 frames.

Every number is a starting value to tune, not a measured result.
"""

from dataclasses import dataclass
from typing import Optional

from .obstacle import USABLE_M

CLEAR_MARGIN_M = 0.3  # leave CAUTION only once the way ahead is this much past USABLE_M
CLEAR_FRAMES = 5  # about a third of a second at 15 frames a second
CHANGE_FRAMES = 2  # any other change


def raw_state(cmd: str, ahead: Optional[float], current: Optional[str]) -> str:
    """This frame's state, with the clear threshold raised while in CAUTION."""
    if cmd == "STOP":
        return "STOP"
    if ahead is None:
        return "UNCERTAIN"
    threshold = USABLE_M + CLEAR_MARGIN_M if current in ("CAUTION", "STOP", None) else USABLE_M
    if cmd != "CENTER" or ahead < threshold:
        return "CAUTION"
    return "CLEAR"


@dataclass
class StateSmoother:
    state: Optional[str] = None  # None until the first frame
    _cand: str = ""
    _count: int = 0

    def update(self, cmd: str, ahead: Optional[float]) -> str:
        raw = raw_state(cmd, ahead, self.state)
        if raw == "STOP" or self.state is None:
            self.state, self._cand, self._count = raw, "", 0
            return self.state
        if self.state == "STOP":  # the command has left STOP: say so now, but not CLEAR yet
            self.state, self._cand, self._count = "CAUTION" if raw == "CLEAR" else raw, "", 0
            return self.state
        if raw == self.state:
            self._cand, self._count = "", 0
            return self.state
        self._count = self._count + 1 if raw == self._cand else 1
        self._cand = raw
        need = CLEAR_FRAMES if raw == "CLEAR" else CHANGE_FRAMES
        if self._count >= need:
            self.state, self._cand, self._count = raw, "", 0
        return self.state

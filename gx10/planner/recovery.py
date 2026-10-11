"""What to do after a stop: turn towards the open side, with a tone as the indicator, until the way opens.

The wheel stays stopped (planner/obstacle.py decides it from depth); the user turns on the spot.
The side, the turn made so far and "open" all come from depth and the phone's own pose:

    stop             "Stop. Chair ahead, about 1 metre. Turn left."   (the side with more room)
    while turning    the left tone, in the left ear, every TONE_EVERY_S: keep turning this way
    no turn yet      "Keep turning left."                after REMIND_S, at most twice
    turned a lot     "Nothing open that way. Turn right." after SWITCH_DEG with no way out
    way open         "Go ahead."                          when the stop ends straight ahead
    stuck            "Step back, then turn slowly."       after STUCK_S

It only runs after a stop that was announced ("Stop. ... Turn left."), and replaces "Path blocked. Turn
slowly to scan." Every number is a starting value to tune.
Standard library only.
"""

import math
from typing import Optional

from .obstacle import USABLE_M

LEFT_SIDE, RIGHT_SIDE = (-30, -20, -10), (10, 20, 30)
TONE_EVERY_S = 1.5  # the phone plays the same tone at most once a second
REMIND_S = 4.0
SWITCH_DEG = 100.0
SWITCH_MIN_S = 4.0  # never two side changes closer than this
JUMP_DEG = 30.0  # a heading change this big between two frames is the phone's tracking jumping, not a turn
STUCK_S = 20.0  # then "Step back", and the tones stop: the user may simply be standing still
EXIT_S = 1.0  # the way must stay open this long before "Go ahead."; a stop within it is the same stop


def yaw_deg(pose) -> Optional[float]:
    """Which way the camera points across the floor, degrees, turning right is positive."""
    fx, fz = -pose[8], -pose[10]
    if math.hypot(fx, fz) < 1e-6:
        return None
    return math.degrees(math.atan2(fx, -fz))


def turn_side(clearance: dict) -> str:
    """The side to turn to: the one with the most room; unknown counts as none. Left on a tie."""
    def room(side):
        known = [clearance.get(h) for h in side if clearance.get(h) is not None]
        return max(known) if known else -1.0
    return "left" if room(LEFT_SIDE) >= room(RIGHT_SIDE) else "right"


class Recovery:
    def __init__(self):
        self.active = False
        self.side = None
        self._start_yaw = None
        self._since = self._last_tone = self._last_said = self._switched = -1e9
        self._last_yaw = None
        self._clear_since = None
        self._reminders = 0
        self._stuck_said = False

    def start_words(self, clearance: dict) -> str:
        """The action to add to the stop sentence: "Turn left." Picks the side for the steps that follow."""
        self.side = turn_side(clearance)
        return f"Turn {self.side}."

    def update(self, cmd: str, clearance: dict, pose, now: float) -> dict:
        """Every frame, with the smoothed wheel command. Returns {"speech": ..., "earcon": ...}, either or neither."""
        out = {}
        yaw = yaw_deg(pose)
        if yaw is not None and self._last_yaw is not None and self._start_yaw is not None:
            jump = ((yaw - self._last_yaw + 180) % 360) - 180
            if abs(jump) > JUMP_DEG:
                self._start_yaw += jump  # tracking jumped: not a turn the user made
        self._last_yaw = yaw
        if cmd != "STOP":
            if not self.active:
                self.__init__()
                return out
            self._clear_since = self._clear_since if self._clear_since is not None else now
            if now - self._clear_since >= EXIT_S:  # open for long enough: the stop is over
                if cmd == "CENTER":
                    out["speech"] = "Go ahead."  # a turn is told by the direction cue instead
                self.__init__()
            return out
        self._clear_since = None
        ahead = clearance.get(0)
        if not self.active and (self.side is None or (ahead is not None and ahead >= USABLE_M)):
            return out  # only after an announced stop with something close (every session starts in STOP)
        if not self.active:  # the stop has just begun
            self.active, self._since, self._last_said = True, now, now
            if self.side is None:
                self.side = turn_side(clearance)
            self._start_yaw = yaw
        if now - self._last_tone >= TONE_EVERY_S and now - self._since < STUCK_S:
            out["earcon"] = self.side  # the indicator: keep turning this way
            self._last_tone = now
        turned = 0.0
        if yaw is not None and self._start_yaw is not None:
            turned = ((yaw - self._start_yaw + 180) % 360) - 180
            turned = -turned if self.side == "left" else turned  # degrees towards the side, either way
        if turned >= SWITCH_DEG and now - self._switched >= SWITCH_MIN_S:
            self.side = "right" if self.side == "left" else "left"
            self._start_yaw, self._reminders, self._last_said, self._switched = yaw, 0, now, now
            out["speech"] = f"Nothing open that way. Turn {self.side}."
            out["earcon"], self._last_tone = self.side, now  # the new side's tone at once
        elif now - self._since >= STUCK_S and not self._stuck_said:
            self._stuck_said, self._last_said = True, now
            out["speech"] = "Step back, then turn slowly."
        elif turned < 20 and self._reminders < 2 and now - self._last_said >= REMIND_S:
            self._reminders += 1
            self._last_said = now
            out["speech"] = f"Keep turning {self.side}."
        return out

    @property
    def step(self) -> Optional[str]:
        """For the dashboard: "turn left" while a stop lasts, else None."""
        return f"turn {self.side}" if self.active and self.side else None

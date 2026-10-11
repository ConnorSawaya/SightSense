"""Steering logic for the cane's wheel.

No GPIO in here. It talks to a hardware object with drive(), off() and
pressed(), so the same code runs on the Pi and against the simulated wheel.
The behaviour is described in README.md.
"""

import json
import math

LEFT, CENTER, RIGHT = "LEFT", "CENTER", "RIGHT"
POSITIONS = (LEFT, CENTER, RIGHT)
COMMANDS = (LEFT, CENTER, RIGHT, "STOP", "FREE")

MAX_DUTY = 0.25  # motor power cap
MOVE_LIMIT_S = 0.4  # longest single motor run
MAX_TTL_S = 0.4  # longest silence before the driver goes off
PAUSE_S = 0.05  # motor rests this long between runs
HOMING_PULSES = (-1, +1, +1, -1)  # directions tried when no switch is pressed
MAX_RUNS = 6  # motor runs allowed without reaching the goal
FAULT_REST_S = 3.0  # driver stays off this long after giving up


def command_ttl(ttl_ms):
    """Validate a TTL, then cap it before converting to seconds."""
    if (isinstance(ttl_ms, bool) or not isinstance(ttl_ms, (int, float))
            or ttl_ms <= 0 or (isinstance(ttl_ms, float) and not math.isfinite(ttl_ms))):
        raise ValueError(f"bad ttl_ms {ttl_ms!r}")
    return min(ttl_ms, MAX_TTL_S * 1000) / 1000


def parse_command(text):
    """Read a command message from contracts/MESSAGES.md.

    Returns (cmd, ttl_ms, seq). Raises ValueError for anything else.
    """
    try:
        msg = json.loads(text)
        cmd = msg["cmd"]
        ttl_ms = msg.get("ttl_ms", MAX_TTL_S * 1000)
        seq = msg.get("seq")
    except (TypeError, KeyError, AttributeError) as e:
        raise ValueError(f"not a command message: {e!r}") from e
    if cmd not in COMMANDS:
        raise ValueError(f"unknown cmd {cmd!r}")
    command_ttl(ttl_ms)
    return cmd, ttl_ms, seq


class Steering:
    """Turns LEFT / CENTER / RIGHT / STOP / FREE into short motor runs.

    Call command() for each message and tick() every few milliseconds.
    Times are seconds from any steady clock.
    """

    def __init__(self, hw, duty=MAX_DUTY, log=print):
        self.hw = hw
        self.duty = min(duty, MAX_DUTY)
        self.log = log
        self.position = None  # None means unknown
        self.want = CENTER  # None means free
        self.starting = True  # the start-up homing runs without a GX10
        self.homing = True
        self.deadline = 0.0
        self.fault_until = 0.0
        self._rest_until = 0.0
        self._run = None  # (stop_on, until) while the motor is on
        self._tries = 0  # motor runs since the goal was last reached
        self._misses = 0  # runs that ended on the time limit
        self._direction = 0
        self._home_direction = None
        self.hw.off()

    def command(self, cmd, now, ttl_ms=MAX_TTL_S * 1000):
        """Take one command. Every command also counts as the heartbeat."""
        if cmd not in COMMANDS:
            self.release(f"bad command {cmd!r}")
            return
        try:
            ttl_s = command_ttl(ttl_ms)
            if not math.isfinite(now):
                raise ValueError("bad command time")
        except (TypeError, ValueError, OverflowError) as e:
            self.release(str(e))
            return
        if cmd == "FREE":
            self.release("FREE")
            return
        want = CENTER if cmd == "STOP" else cmd
        if want == CENTER and self.want != CENTER and self._run:
            # Stop the old pulse now. If leaving centre, return in the opposite
            # direction; if coming from an end, continue towards centre.
            home_direction = self._direction if self.position in (LEFT, RIGHT) else -self._direction
            self._stop(now)
            self.position = None
            self.homing = True
            self._home_direction = home_direction
        if want != self.want:
            self.log(f"command {cmd}")
        self.want = want
        self.starting = False
        self.deadline = now + ttl_s

    def release(self, reason):
        """Driver off, wheel free. The next move starts by homing to centre."""
        self.hw.off()
        if self.want is not None:
            self.log(f"driver off: {reason}")
        self.want = None
        self.starting = False
        self.position = None
        self.homing = True
        self._run = None
        self._home_direction = None
        self._tries = self._misses = 0

    def tick(self, now):
        """Advance the motor. Any error switches the driver off first."""
        try:
            self._tick(now)
        except Exception:
            self.release("error")
            raise

    def _tick(self, now):
        if self.want is None:
            return
        if not self.starting and now >= self.deadline:
            self.release(f"no command for {MAX_TTL_S * 1000:.0f} ms")
            return

        pressed = self.hw.pressed()
        if len(pressed) > 1:
            if self._run or now >= self.fault_until:
                self._fault(now, f"switches {sorted(pressed)} pressed together")
            return

        if self._run:
            stop_on, until = self._run
            hit = pressed & stop_on
            if hit:
                self._stop(now)
                self.position = hit.pop()
                self.log(f"at {self.position}")
            elif now >= until:
                self._stop(now)
                self.position = None
                self.homing = True
                self._misses += 1
                self.log(f"no switch within {MOVE_LIMIT_S * 1000:.0f} ms: position unknown")
            else:
                return

        if now < max(self.fault_until, self._rest_until):
            return
        if pressed:
            self.position = next(iter(pressed))

        goal = CENTER if self.homing else self.want
        if self.position == goal:
            if self.homing:
                self.homing = False
                self.log("homed to CENTER")
            if self.starting:
                self.starting = False
                self.want = None
                self.log("waiting for commands")
            if self.want in (self.position, None):
                self._tries = self._misses = 0
            return

        if self._tries >= MAX_RUNS:
            self._fault(now, f"could not reach {goal} in {MAX_RUNS} runs")
            return
        if self.position is None:
            direction = self._home_direction or HOMING_PULSES[self._misses % len(HOMING_PULSES)]
            self._home_direction = None
            stop_on = {CENTER, _end(direction)}
            self.log(f"homing pulse {'left' if direction < 0 else 'right'}")
        else:
            here = POSITIONS.index(self.position)
            direction = 1 if POSITIONS.index(goal) > here else -1
            step = POSITIONS[here + direction]
            stop_on = {step, _end(direction)}
            self.log(f"move {self.position} -> {step}")
        self._tries += 1
        self.hw.drive(direction, self.duty)
        self._direction = direction
        self._run = (stop_on, now + MOVE_LIMIT_S)

    def _stop(self, now):
        self.hw.off()
        self._run = None
        self._rest_until = now + PAUSE_S

    def _fault(self, now, reason):
        self._stop(now)
        self.position = None
        self.homing = True
        self._tries = self._misses = 0
        self.fault_until = now + FAULT_REST_S
        self.log(f"fault: {reason}; driver off for {FAULT_REST_S:g} s")
        if self.starting:
            self.starting = False
            self.want = None


def _end(direction):
    return LEFT if direction < 0 else RIGHT

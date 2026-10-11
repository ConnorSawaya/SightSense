"""Direct drive of the mecanum wheel: LEFT and RIGHT spin opposite ways.

CENTER, STOP and FREE switch the driver off. There are no steering positions
or homing moves. Network messages never set motor power.
"""

import math

from steering import COMMANDS, MAX_DUTY, MAX_TTL_S, PAUSE_S, command_ttl

# Longest single run before a short rest. Was 0.4 s (MOVE_LIMIT_S), which made the wheel stutter. The motor still
# stops MAX_TTL_S (0.4 s) after the last command, whatever this is.
RUN_S = 2.0


class WheelDrive:
    def __init__(self, hw, duty=MAX_DUTY, rated_rpm=120, log=print):
        if isinstance(duty, bool) or not math.isfinite(duty) or duty < 0:
            raise ValueError("duty must be finite and nonnegative")
        if isinstance(rated_rpm, bool) or not math.isfinite(rated_rpm) or rated_rpm <= 0:
            raise ValueError("rated RPM must be finite and positive")
        self.hw = hw
        self.duty = min(duty, MAX_DUTY)
        self.rated_rpm = rated_rpm
        self.log = log
        self.want = None
        self.deadline = 0.0
        self._run_until = None
        self._rest_until = 0.0
        self._driven = None
        self._now = 0.0
        self.hw.off()

    @property
    def estimated_rpm(self):
        """Nameplate RPM scaled by duty, not an encoder measurement."""
        return self.rated_rpm * self.duty

    def command(self, cmd, now, ttl_ms=MAX_TTL_S * 1000):
        try:
            ttl_s = command_ttl(ttl_ms)
            if not math.isfinite(now):
                raise ValueError("bad command time")
        except (TypeError, ValueError, OverflowError) as e:
            self.release(str(e))
            return
        self._now = now
        if cmd not in COMMANDS:
            self.release(f"bad command {cmd!r}")
            return
        if cmd in ("CENTER", "STOP", "FREE"):
            self.release(cmd)
            return
        direction = -1 if cmd == "LEFT" else 1
        if direction != self.want:
            if self._run_until is not None:
                self._stop(now)  # dead time before reversing the H-bridge
            self.log(f"command {cmd}")
        self.want = direction
        self.deadline = now + ttl_s

    def release(self, reason):
        try:
            self._stop(self._now)
        finally:
            if self.want is not None:
                self.log(f"driver off: {reason}")
            self.want = None
            self.deadline = 0.0

    def tick(self, now):
        try:
            if not math.isfinite(now):
                raise ValueError("bad tick time")
            self._now = now
            if self.want is None:
                return
            if now >= self.deadline:
                self.release("command expired")
                return
            if self._run_until is not None:
                if now < self._run_until:
                    if self.duty != self._driven:  # the speed slider moved: change it now, not at the next run
                        self.hw.drive(self.want, self.duty)
                        self._driven = self.duty
                    return
                self._stop(now)
            if now < self._rest_until or self.duty == 0:
                return
            self.hw.drive(self.want, self.duty)
            self._driven = self.duty
            self._run_until = now + RUN_S
            self.log(f"wheel {'LEFT' if self.want < 0 else 'RIGHT'}: duty {self.duty:.0%}, "
                     f"estimated {self.estimated_rpm:g} rpm (unmeasured)")
        except Exception:
            self.release("error")
            raise

    def _stop(self, now):
        was_running = self._run_until is not None
        try:
            self.hw.off()
        finally:
            self._run_until = None
            if was_running:
                self._rest_until = now + PAUSE_S

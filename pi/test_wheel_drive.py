"""Direct wheel drive on a fake motor and clock. No physical GPIO."""

import math
import unittest

from steering import MAX_DUTY, MOVE_LIMIT_S, PAUSE_S, parse_command
from test_steering import Motor
from wheel_drive import WheelDrive


class WheelTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.motor = Motor(lambda: self.now)
        self.lines = []
        self.wheel = WheelDrive(self.motor, log=self.lines.append)

    def advance(self, seconds, cmd=None, ttl_ms=400):
        end, beat = self.now + seconds, self.now
        while self.now < end:
            if cmd and self.now >= beat:
                self.wheel.command(cmd, self.now, ttl_ms)
                beat += 1 / 15
            self.wheel.tick(self.now)
            self.now += 0.002

    def test_startup_never_moves_or_reads_switches(self):
        self.advance(5)
        self.assertEqual(self.motor.runs, [])
        self.assertIsNone(self.motor._on)

    def test_left_and_right_spin_opposite_ways(self):
        for cmd, direction in (("LEFT", -1), ("RIGHT", 1)):
            self.advance(0.1, cmd)
            self.assertEqual(self.motor._on[:2], (direction, MAX_DUTY))
            self.wheel.command("STOP", self.now)

    def test_every_neutral_command_stops_at_once(self):
        for cmd in ("CENTER", "STOP", "FREE"):
            self.advance(0.2, "LEFT")
            self.assertIsNotNone(self.motor._on)
            self.wheel.command(cmd, self.now)
            self.assertIsNone(self.motor._on)
            self.advance(1, cmd)
            self.assertIsNone(self.motor._on)

    def test_reversal_has_dead_time(self):
        self.advance(0.1, "LEFT")
        changed = self.now
        self.wheel.command("RIGHT", changed)
        self.assertIsNone(self.motor._on)
        self.advance(PAUSE_S / 2, "RIGHT")
        self.assertIsNone(self.motor._on)
        self.advance(PAUSE_S, "RIGHT")
        self.assertEqual(self.motor._on[0], 1)
        self.assertGreaterEqual(self.motor._on[2], changed + PAUSE_S)

    def test_heartbeat_drives_repeated_bounded_pulses(self):
        self.advance(2, "LEFT")
        self.wheel.command("STOP", self.now)
        self.assertGreater(len(self.motor.runs), 3)
        for direction, duty, seconds in self.motor.runs:
            self.assertEqual(direction, -1)
            self.assertLessEqual(duty, MAX_DUTY)
            self.assertLessEqual(seconds, MOVE_LIMIT_S + 0.0021)

    def test_silence_expires_even_while_connection_is_open(self):
        self.advance(0.1, "RIGHT")
        self.advance(0.5)
        self.assertIsNone(self.motor._on)
        self.assertIsNone(self.wheel.want)
        self.assertTrue(any("expired" in line for line in self.lines))

    def test_short_ttl_and_old_message_do_not_move(self):
        self.wheel.command("RIGHT", self.now, 20)
        self.advance(0.03)
        self.assertIsNone(self.motor._on)
        self.wheel.command("LEFT", self.now - 1, 400)
        self.wheel.tick(self.now)
        self.assertIsNone(self.motor._on)

    def test_invalid_ttl_releases_direct_calls(self):
        for ttl in (math.nan, math.inf, -math.inf, 0, -1, True, "400", None):
            self.advance(0.1, "LEFT")
            self.wheel.command("RIGHT", self.now, ttl)
            self.assertIsNone(self.motor._on)
            self.assertIsNone(self.wheel.want)

    def test_invalid_message_is_rejected(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.assertRaises(ValueError):
                parse_command('{"cmd":"LEFT","ttl_ms":' + value + '}')

    def test_bad_command_releases(self):
        self.advance(0.1, "LEFT")
        self.wheel.command("FORWARD", self.now)
        self.assertIsNone(self.motor._on)

    def test_rpm_is_an_estimate_and_power_is_capped(self):
        wheel = WheelDrive(self.motor, duty=1, rated_rpm=120, log=self.lines.append)
        self.assertEqual(wheel.duty, 0.25)
        self.assertEqual(wheel.estimated_rpm, 30)
        wheel.command("LEFT", self.now)
        wheel.tick(self.now)
        self.assertTrue(any("unmeasured" in line for line in self.lines))
        wheel.release("test complete")

    def test_zero_duty_never_powers_motor(self):
        wheel = WheelDrive(self.motor, duty=0, log=self.lines.append)
        wheel.command("RIGHT", self.now)
        wheel.tick(self.now)
        self.assertIsNone(self.motor._on)

    def test_invalid_speed_settings_are_rejected(self):
        for value in (math.nan, math.inf, -1, True):
            with self.assertRaises(ValueError):
                WheelDrive(self.motor, duty=value)
            with self.assertRaises(ValueError):
                WheelDrive(self.motor, rated_rpm=value)

    def test_gpio_error_releases_and_propagates(self):
        def broken(*args):
            raise OSError("driver unavailable")
        self.motor.drive = broken
        self.wheel.command("LEFT", self.now)
        with self.assertRaises(OSError):
            self.wheel.tick(self.now)
        self.assertIsNone(self.wheel.want)
        self.assertIsNone(self.motor._on)


if __name__ == "__main__":
    unittest.main()

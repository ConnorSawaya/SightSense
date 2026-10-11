"""Tests for the bench test, on gpiozero's mock pins.

    python3 -m unittest -v        (from this folder)

Skipped where gpiozero is not installed.
"""

import os
import tempfile
import unittest

import hardware
import spin_test

try:
    from gpiozero import Device
    from gpiozero.pins.mock import MockFactory, MockPWMPin
except ImportError:
    Device = None


class Pins(unittest.TestCase):
    def test_same_pins_as_the_controller(self):
        self.assertEqual(
            (spin_test.PIN_RPWM, spin_test.PIN_LPWM, spin_test.PIN_R_EN, spin_test.PIN_L_EN),
            (hardware.PIN_RPWM, hardware.PIN_LPWM, hardware.PIN_R_EN, hardware.PIN_L_EN),
        )
        self.assertEqual(set(spin_test.PIN_SWITCHES), set(hardware.PIN_SWITCH.values()))


class Record(unittest.TestCase):
    def test_counts_unfinished_runs(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "record")
            self.assertEqual(spin_test.unfinished(path), 0)  # no file yet
            spin_test.record(2, path)
            self.assertEqual(spin_test.unfinished(path), 2)
            spin_test.record(0, path)
            self.assertEqual(spin_test.unfinished(path), 0)
            with open(path, "w") as f:
                f.write("not a number")
            self.assertEqual(spin_test.unfinished(path), 0)


@unittest.skipUnless(Device, "gpiozero is not installed")
class Ramp(unittest.TestCase):
    def setUp(self):
        Device.pin_factory = self.pins = MockFactory(pin_class=MockPWMPin)
        self.seen = []  # (R_EN, L_EN, RPWM, LPWM) at every pause
        self.lines = []

    def state(self):
        return tuple(self.pins.pin(n).state for n in
                     (spin_test.PIN_R_EN, spin_test.PIN_L_EN, spin_test.PIN_RPWM, spin_test.PIN_LPWM))

    def spin(self, press_at=None, **kw):
        def sleep(_):
            self.seen.append(self.state())
            if press_at is not None and len(self.seen) == press_at:
                self.pins.pin(spin_test.PIN_SWITCHES[0]).drive_low()
        return spin_test.spin(ramp_s=1.0, hold_s=0.2, log=self.lines.append, sleep=sleep, **kw)

    def test_ramps_from_slow_to_full_then_switches_off(self):
        self.assertTrue(self.spin())
        self.assertEqual(self.seen[0], (0, 0, 0, 0))  # nothing on while the inputs settle
        running = self.seen[1:]
        power = [s[2] for s in running]
        self.assertAlmostEqual(power[0], 0.05)
        self.assertEqual(power[19], 1.0)
        self.assertEqual(power, sorted(power))
        self.assertTrue(all(s[:2] == (1, 1) and s[3] == 0 for s in running))
        self.assertEqual(len(running), 20 + 4)  # the ramp, then the hold
        self.assertEqual(self.lines[-1], "motor off")

    def test_reverse_powers_the_other_pin(self):
        self.spin(reverse=True)
        self.assertTrue(all(s[2] == 0 for s in self.seen))
        self.assertEqual(max(s[3] for s in self.seen), 1.0)

    def test_a_pressed_switch_stops_it(self):
        self.assertFalse(self.spin(press_at=5))
        self.assertEqual(len(self.seen), 5)
        self.assertLess(max(s[2] for s in self.seen), 0.25)
        self.assertIn("a limit switch is pressed: stopping", self.lines)

    def test_does_not_start_with_a_switch_pressed(self):
        self.assertFalse(self.spin(press_at=1))
        self.assertEqual(self.seen, [(0, 0, 0, 0)])
        self.assertIn("a limit switch is pressed: not starting", self.lines)

    def test_everything_is_off_afterwards(self):
        for kw in ({}, {"press_at": 3}):
            self.setUp()
            self.spin(**kw)
            self.assertEqual(self.state(), (0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()

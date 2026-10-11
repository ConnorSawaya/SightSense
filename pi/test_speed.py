"""The dashboard's speed level. python3 -m unittest test_speed -v   (from this folder; any computer)"""

import json
import threading
import time
import unittest

import cane
from cane import SpeedSetting, parse_speed
from steering import MAX_DUTY


class Parsing(unittest.TestCase):
    def test_levels(self):
        self.assertEqual(parse_speed('{"speed": 0.6}'), 0.6)
        self.assertEqual(parse_speed('{"speed": 3}'), 1.0)  # never above the start-up duty
        self.assertEqual(parse_speed('{"speed": -1}'), 0.0)

    def test_anything_else_is_not_a_speed(self):
        for text in ('{"cmd": "LEFT", "ttl_ms": 400}', '{"speed": true}', '{"speed": "fast"}',
                     '{"speed": NaN}', "speed", "[0.5]", ""):
            with self.subTest(text=text):
                self.assertIsNone(parse_speed(text))

    def test_setting(self):
        s = SpeedSetting()
        self.assertEqual(s.value, 1.0)
        s.set(0.4)
        self.assertEqual(s.value, 0.4)
        s.set(7)
        self.assertEqual(s.value, 1.0)
        s.set(0.2)
        s.reset()
        self.assertEqual(s.value, 1.0)


class RecordingHardware:
    """Records each drive call: (direction, duty)."""

    def __init__(self):
        self.drives = []

    def drive(self, direction, duty):
        self.drives.append((direction, duty))

    def off(self):
        pass

    def close(self):
        pass

    def read_switches(self):
        return (False, False)


class Inbox:
    def __init__(self, items):
        self.items = list(items)

    def take(self):
        return (self.items.pop(0), time.monotonic()) if self.items else None


class Loop(unittest.TestCase):
    def drive_left(self, level):
        hw, stop, speed = RecordingHardware(), threading.Event(), SpeedSetting()
        speed.set(level)
        inbox = Inbox([json.dumps({"seq": 1, "cmd": "LEFT", "ttl_ms": 400})])
        t = threading.Thread(target=cane.control_loop, args=(hw, inbox, stop, MAX_DUTY, True, 120, speed))
        t.start()
        time.sleep(0.15)
        stop.set()
        t.join(1)
        return [d for _, d in hw.drives if d > 0]

    def test_the_motor_runs_at_the_scaled_duty(self):
        self.assertTrue(self.drive_left(0.5))
        self.assertTrue(all(abs(d - MAX_DUTY * 0.5) < 1e-9 for d in self.drive_left(0.5)))
        self.assertTrue(all(abs(d - MAX_DUTY) < 1e-9 for d in self.drive_left(1.0)))

    def test_zero_means_no_power(self):
        self.assertEqual(self.drive_left(0.0), [])


if __name__ == "__main__":
    unittest.main()

import math
import unittest

from rpm import measured_rpm


class RPM(unittest.TestCase):
    def test_counted_turns(self):
        self.assertEqual(measured_rpm(2, 4), 30)
        self.assertEqual(measured_rpm(1, 0.5), 120)
        self.assertEqual(measured_rpm(0, 1), 0)

    def test_invalid_measurements(self):
        for turns, seconds in ((-1, 1), (1, 0), (math.nan, 1), (1, math.inf), (True, 1)):
            with self.assertRaises(ValueError):
                measured_rpm(turns, seconds)

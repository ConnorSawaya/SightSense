"""python3 -m unittest planner.test_state   (from gx10/)"""

import random
import unittest

from planner.obstacle import USABLE_M
from planner.state import CLEAR_FRAMES, CLEAR_MARGIN_M, StateSmoother


def run(s, frames):
    return [s.update(cmd, ahead) for cmd, ahead in frames]


class TestStateSmoother(unittest.TestCase):
    def test_noise_around_the_threshold_does_not_flicker(self):
        # Phone held still 2.5 m from a wall: readings jitter +-5 cm.
        rng = random.Random(1)
        s = StateSmoother()
        states = run(s, [("CENTER", USABLE_M + rng.uniform(-0.05, 0.05)) for _ in range(300)])
        changes = sum(a != b for a, b in zip(states, states[1:]))
        self.assertLessEqual(changes, 1, states)

    def test_without_smoothing_the_same_noise_flickers(self):
        # What the old per-frame rule did with the same readings.
        rng = random.Random(1)
        states = ["CAUTION" if USABLE_M + rng.uniform(-0.05, 0.05) < USABLE_M else "CLEAR" for _ in range(300)]
        self.assertGreater(sum(a != b for a, b in zip(states, states[1:])), 50)

    def test_stop_is_immediate(self):
        s = StateSmoother()
        run(s, [("CENTER", 4.0)] * 10)
        self.assertEqual(s.update("STOP", 0.9), "STOP")

    def test_caution_after_two_frames(self):
        s = StateSmoother()
        run(s, [("CENTER", 4.0)] * 10)
        self.assertEqual(s.update("CENTER", 2.0), "CLEAR")
        self.assertEqual(s.update("CENTER", 2.0), "CAUTION")

    def test_clear_needs_margin_and_frames(self):
        s = StateSmoother()
        run(s, [("CENTER", 2.0)] * 5)
        self.assertEqual(s.state, "CAUTION")
        run(s, [("CENTER", USABLE_M + 0.1)] * 20)  # past USABLE_M but inside the margin
        self.assertEqual(s.state, "CAUTION")
        out = run(s, [("CENTER", USABLE_M + CLEAR_MARGIN_M + 0.1)] * CLEAR_FRAMES)
        self.assertEqual(out[-2], "CAUTION")
        self.assertEqual(out[-1], "CLEAR")

    def test_one_odd_frame_is_ignored(self):
        s = StateSmoother()
        run(s, [("CENTER", 4.0)] * 10)
        self.assertEqual(run(s, [("CENTER", 1.8), ("CENTER", 4.0), ("CENTER", 4.0)]), ["CLEAR"] * 3)

    def test_turning_wheel_is_caution(self):
        s = StateSmoother()
        run(s, [("CENTER", 4.0)] * 10)
        self.assertEqual(run(s, [("RIGHT", 4.0)] * 2)[-1], "CAUTION")

    def test_unknown_ahead_is_uncertain(self):
        s = StateSmoother()
        run(s, [("CENTER", 4.0)] * 10)
        self.assertEqual(run(s, [("CENTER", None)] * 2)[-1], "UNCERTAIN")

    def test_leaving_stop_goes_through_caution(self):
        s = StateSmoother()
        s.update("STOP", 0.5)
        out = run(s, [("CENTER", 4.0)] * (CLEAR_FRAMES + 3))
        self.assertNotIn("STOP", out)
        self.assertEqual(out[-1], "CLEAR")


if __name__ == "__main__":
    unittest.main()

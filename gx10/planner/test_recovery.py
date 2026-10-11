"""python3 -m unittest planner.test_recovery (from gx10/)."""

import unittest

from navigator import fake

from .recovery import Recovery, turn_side, yaw_deg

ALL = (-30, -20, -10, 0, 10, 20, 30)
BLOCKED = {h: 0.6 for h in ALL}
LEFT_OPEN = {**BLOCKED, -30: 3.0, -20: 2.0}
OPEN = {h: 10.0 for h in ALL}
FPS = 15


def look(turn_right_deg):
    return fake.pose(yaw_deg=-turn_right_deg, pitch_deg=-25, height=0.9)  # fake.pose: yaw > 0 turns left


class Pieces(unittest.TestCase):
    def test_yaw_turning_right_is_positive(self):
        self.assertAlmostEqual(yaw_deg(look(0)), 0.0, places=6)
        self.assertAlmostEqual(yaw_deg(look(30)), 30.0, places=6)

    def test_side_with_more_room(self):
        self.assertEqual(turn_side(LEFT_OPEN), "left")
        self.assertEqual(turn_side({**BLOCKED, 20: 2.5}), "right")
        self.assertEqual(turn_side({**BLOCKED, -30: None, -20: None, -10: None}), "right")  # unknown is no room


class Sequence(unittest.TestCase):
    def run_frames(self, r, seconds, start, cmd, clearance, turn_from=0.0, turn_to=None):
        """Frames for `seconds`, the user turning steadily from turn_from to turn_to degrees (right positive)."""
        said, tones, n = [], [], int(seconds * FPS)
        for i in range(n):
            deg = turn_from if turn_to is None else turn_from + (turn_to - turn_from) * i / max(n - 1, 1)
            out = r.update(cmd, clearance, look(deg), start + i / FPS)
            if "speech" in out:
                said.append(out["speech"])
            if "earcon" in out:
                tones.append(out["earcon"])
        return said, tones

    def test_turn_left_with_a_tone_then_go(self):
        r = Recovery()
        self.assertEqual(r.start_words(LEFT_OPEN), "Turn left.")
        said, tones = self.run_frames(r, 3, 0, "STOP", LEFT_OPEN, 0, -40)  # turning left
        self.assertEqual(said, [])  # turning: no nagging
        self.assertEqual(tones, ["left", "left"])  # the indicator, every 1.5 s
        self.assertEqual(r.step, "turn left")
        said, _ = self.run_frames(r, 1.2, 3, "CENTER", OPEN, -40)
        self.assertEqual(said, ["Go ahead."])
        self.assertIsNone(r.step)

    def test_reminds_when_the_user_does_not_turn(self):
        r = Recovery()
        r.start_words(LEFT_OPEN)
        said, _ = self.run_frames(r, 13, 0, "STOP", LEFT_OPEN)
        self.assertEqual(said, ["Keep turning left.", "Keep turning left."])  # at most twice

    def test_tries_the_other_way_after_turning_a_long_way(self):
        r = Recovery()
        r.start_words(LEFT_OPEN)
        said, tones = self.run_frames(r, 6, 0, "STOP", BLOCKED, 0, -120)
        self.assertEqual(said, ["Nothing open that way. Turn right."])
        self.assertEqual(tones[-1], "right")

    def test_still_stuck(self):
        r = Recovery()
        r.start_words(BLOCKED)
        said, _ = self.run_frames(r, 21, 0, "STOP", BLOCKED, 0, -15)
        self.assertEqual(said[-1], "Step back, then turn slowly.")

    def test_a_flicker_is_the_same_stop(self):
        r = Recovery()
        r.start_words(LEFT_OPEN)
        self.run_frames(r, 2, 0, "STOP", LEFT_OPEN)
        said, _ = self.run_frames(r, 0.4, 2, "CENTER", OPEN)  # open for a moment only
        self.assertEqual((said, r.active), ([], True))
        self.run_frames(r, 1, 2.4, "STOP", LEFT_OPEN)
        self.assertTrue(r.active)

    def test_a_tracking_jump_is_not_a_turn(self):
        r = Recovery()
        r.start_words(LEFT_OPEN)
        self.run_frames(r, 1, 0, "STOP", BLOCKED, 0)
        said, _ = self.run_frames(r, 1, 1, "STOP", BLOCKED, -150)  # pose jumps 150 degrees in one frame
        self.assertNotIn("Nothing open that way. Turn right.", said)

    def test_tones_stop_once_stuck(self):
        r = Recovery()
        r.start_words(BLOCKED)
        _, tones = self.run_frames(r, 40, 0, "STOP", BLOCKED)
        self.assertLessEqual(len(tones), 14)  # every 1.5 s for the first 20 s only

    def test_no_steps_without_an_announced_stop(self):
        r = Recovery()
        said, tones = self.run_frames(r, 6, 0, "STOP", BLOCKED)  # a session that starts facing something
        self.assertEqual((said, tones, r.step), ([], [], None))

    def test_no_steps_for_a_stop_with_nothing_close(self):
        r = Recovery()
        said, tones = self.run_frames(r, 3, 0, "STOP", OPEN)  # every session starts in STOP
        self.assertEqual((said, tones, r.step), ([], [], None))


if __name__ == "__main__":
    unittest.main()

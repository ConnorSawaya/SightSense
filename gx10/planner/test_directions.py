"""Left and right, end to end, on ray-cast scenes. ../../venv-yolo/bin/python -m unittest planner.test_directions

Something close on one side must give: the obstacle on that side (near_side), a stop or a steer the other way,
"Turn <other way>" after a stop, and that side's tone. For every way the phone can sit in its mount.
On real recordings the same is checked against the picture by planner/check_directions.py.
"""

import unittest

from navigator import fake

from .fake_scene import arrays, render
from .obstacle import check
from .recovery import Recovery, turn_side

ROLLS = (0, 90, -90, 180)  # phone upright, on either side, upside down in the mount


def cane(roll=0, yaw=0.0):
    return fake.pose(pitch_deg=-25, height=0.9, roll_deg=roll, yaw_deg=yaw)


def run(pose, boxes, stopped=False):
    f = render(pose, boxes)
    d, c = arrays(f)
    return check(d, c, f.fx, f.fy, f.cx, f.cy, f.pose, stopped=stopped)


NEAR_RIGHT = [((0.05, 0, -0.75), (0.8, 1.2, -0.35))]  # a box 0.35-0.75 m ahead, covering the right side
NEAR_LEFT = [((-0.8, 0, -0.75), (-0.05, 1.2, -0.35))]
RIGHT_WALL_AND_BOX = [((0.35, 0, -4), (0.45, 2.5, 0.5)), ((-0.1, 0, -0.9), (0.4, 1.2, -0.6))]  # wall along the right


class Directions(unittest.TestCase):
    def test_close_on_the_right_means_go_left(self):
        for roll in ROLLS:
            with self.subTest(roll=roll):
                c = run(cane(roll), NEAR_RIGHT)
                self.assertEqual(c.near_side, "right")
                self.assertIn(c.raw_cmd, ("LEFT", "STOP"))
                self.assertEqual(turn_side(c.clearance, c.room, c.near_side), "left")

    def test_close_on_the_left_means_go_right(self):
        for roll in ROLLS:
            with self.subTest(roll=roll):
                c = run(cane(roll), NEAR_LEFT)
                self.assertEqual(c.near_side, "left")
                self.assertIn(c.raw_cmd, ("RIGHT", "STOP"))
                self.assertEqual(turn_side(c.clearance, c.room, c.near_side), "right")

    def test_a_wall_on_the_right_and_a_box_ahead(self):
        for roll in ROLLS:
            with self.subTest(roll=roll):
                c = run(cane(roll), RIGHT_WALL_AND_BOX)
                self.assertNotEqual(c.raw_cmd, "RIGHT")
                self.assertEqual(turn_side(c.clearance, c.room, c.near_side), "left")

    def test_turned_away_from_the_room_the_answer_turns_too(self):
        # a box about 48 degrees to the right; the user turns 75 degrees right, so it is now on their left
        c = run(cane(0, yaw=-75), [((0.25, 0, -0.75), (1.0, 1.2, -0.35))])
        self.assertEqual(c.near_side, "left")

    def test_the_spoken_step_and_the_tone_match(self):
        for boxes, side in ((NEAR_RIGHT, "left"), (NEAR_LEFT, "right")):
            c = run(cane(), boxes)
            r = Recovery()
            self.assertEqual(r.start_words(c.clearance, c.room, c.near_side), f"Turn {side}.")
            out = r.update("STOP", c.clearance, cane(), 0.0)
            self.assertEqual(out.get("earcon"), side)  # the tone plays in the ear of the side to turn to

    def test_nothing_close_nothing_decided_by_side(self):
        self.assertIsNone(run(cane(), []).near_side)


if __name__ == "__main__":
    unittest.main()

"""Obstacle check on ray-cast scenes. Needs numpy: ../../venv-yolo/bin/python -m unittest planner.test_obstacle (from gx10/)."""

import unittest

from navigator import fake

from .fake_scene import arrays, render
from .obstacle import FAR_M, USABLE_M, Smoother, check


def run(pose, boxes=(), glass=(), desired=0.0, last=0.0):
    f = render(pose, boxes, glass=glass)
    d, c = arrays(f)
    return check(d, c, f.fx, f.fy, f.cx, f.cy, f.pose, desired, last)


CANE = fake.pose(pitch_deg=-25, height=0.9)  # phone on a cane handle, looking down the path
WALL_AHEAD = ((-3, 0, -0.8), (3, 2.5, -0.6))  # wall 0.6 m ahead, 6 m wide
BOX = ((-0.1, 0, -1.5), (0.5, 1.2, -1.2))  # 1.2 m ahead, a little right of centre


class Check(unittest.TestCase):
    def test_open_floor(self):
        c = run(CANE)
        self.assertTrue(c.floor_seen)
        self.assertEqual(c.points, 0)
        self.assertEqual(c.clearance, {h: FAR_M for h in c.clearance})
        self.assertEqual((c.best, c.raw_cmd), (0, "CENTER"))

    def test_wall_ahead_stops(self):
        c = run(CANE, [WALL_AHEAD])
        self.assertEqual(c.usable, [])
        self.assertEqual(c.raw_cmd, "STOP")
        self.assertAlmostEqual(c.clearance[0], 0.6, delta=0.1)

    def test_tight_space_steers_to_the_most_open_side(self):
        # Nothing open to USABLE_M, but the right is open past STOP_AHEAD_M: steer right, no STOP.
        c = run(CANE, [((-3, 0, -1.0), (-0.1, 2.5, -0.9)), ((-0.1, 0, -1.3), (3, 2.5, -1.2))])
        self.assertEqual(c.usable, [])
        self.assertEqual(c.raw_cmd, "RIGHT")

    def test_leaving_stop_needs_more_room(self):
        wall = [((-3, 0, -1.0), (3, 2.5, -0.9))]  # 0.9 m: past STOP_AHEAD_M, short of LEAVE_STOP_M
        self.assertEqual(run(CANE, wall).raw_cmd, "CENTER")
        f = render(CANE, wall)
        d, c = arrays(f)
        self.assertEqual(check(d, c, f.fx, f.fy, f.cx, f.cy, f.pose, stopped=True).raw_cmd, "STOP")

    def test_wall_2_5_m_ahead_does_not_stop(self):
        # The team found stopping about 2.2 m from things too cautious (October 10).
        c = run(CANE, [((-3, 0, -2.7), (3, 2.5, -2.5))])
        self.assertEqual(c.raw_cmd, "CENTER")

    def test_right_up_against_a_wall_is_not_clear(self):
        c = run(CANE, [((-3, 0, -0.25), (3, 2.5, -0.15))])  # nearer than the 0.3 m the check keeps
        self.assertEqual(c.raw_cmd, "STOP")
        self.assertEqual(c.usable, [])

    def test_steers_round_a_box(self):
        c = run(CANE, [BOX])
        self.assertLess(c.clearance[0], USABLE_M)
        self.assertLess(c.best, 0)  # goes left, the side with more room
        self.assertEqual(c.raw_cmd, "LEFT")

    def test_desired_bearing_on_open_floor(self):
        self.assertEqual(run(CANE, desired=20).raw_cmd, "RIGHT")
        self.assertEqual(run(CANE, desired=-12).best, -10)

    def test_glass_is_unknown_so_blocked(self):
        c = run(CANE, glass=[((-3, 0, -2.1), (3, 2.5, -2.0))])
        self.assertTrue(all(v is None for v in c.clearance.values()), c.clearance)
        self.assertEqual(c.raw_cmd, "STOP")

    def test_sideways_phone_same_answer(self):
        c = run(fake.pose(pitch_deg=-25, height=0.9, roll_deg=90), [BOX])
        self.assertLess(c.clearance[0], USABLE_M)
        self.assertTrue(c.best is None or c.best < 0)

    def test_low_floor_items_ignored(self):
        mat = ((-0.5, 0, -2.5), (0.5, 0.05, -1.5))  # 5 cm high doormat
        self.assertEqual(run(CANE, [mat]).raw_cmd, "CENTER")


class Smoothing(unittest.TestCase):
    def test_change_needs_three_frames_and_stop_two(self):
        s = Smoother(cmd="CENTER")
        self.assertEqual(s.update("LEFT", -20, 0)[0], "CENTER")
        self.assertEqual(s.update("LEFT", -20, 0.1)[0], "CENTER")
        self.assertEqual(s.update("LEFT", -20, 0.2)[0], "LEFT")
        self.assertEqual(s.update("STOP", None, 0.3), ("LEFT", None))
        self.assertEqual(s.update("STOP", None, 0.4), ("STOP", "Obstacle ahead. Stop."))

    def test_flicker_does_not_change(self):
        s = Smoother(cmd="CENTER")
        for i, raw in enumerate(["LEFT", "LEFT", "CENTER", "LEFT", "LEFT", "RIGHT"]):
            self.assertEqual(s.update(raw, 0, i * 0.1)[0], "CENTER")

    def test_stuck_message_after_5_s(self):
        s = Smoother(cmd="STOP")
        said = [s.update("STOP", None, t / 10)[1] for t in range(60)]
        self.assertEqual([x for x in said if x], ["Path blocked. Turn slowly to scan."])


if __name__ == "__main__":
    unittest.main()

"""Obstacle check on ray-cast scenes. Needs numpy: ../../venv-yolo/bin/python -m unittest planner.test_obstacle (from gx10/)."""

import unittest

import numpy as np

from navigator import fake

from .fake_scene import arrays, render
from .obstacle import FAR_M, HEADINGS, MAP_FLOOR, MAP_OBSTACLE, Smoother, check


def run(pose, boxes=(), glass=(), desired=0.0, last=0.0):
    f = render(pose, boxes, glass=glass)
    d, c = arrays(f)
    return check(d, c, f.fx, f.fy, f.cx, f.cy, f.pose, desired, last)


CANE = fake.pose(pitch_deg=-25, height=0.9)  # phone on a cane handle, looking down the path
WALL_AHEAD = ((-3, 0, -1.7), (3, 2.5, -1.5))  # wall 1.5 m ahead, 6 m wide


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
        self.assertAlmostEqual(c.clearance[0], 1.5, delta=0.1)

    def test_right_up_against_a_wall_is_not_clear(self):
        c = run(CANE, [((-3, 0, -0.25), (3, 2.5, -0.15))])  # nearer than the 0.3 m the check keeps
        self.assertEqual(c.raw_cmd, "STOP")
        self.assertEqual(c.usable, [])

    def test_steers_round_a_box(self):
        box = ((-0.1, 0, -2.3), (0.5, 1.2, -2.0))  # 2 m ahead, a little right of centre
        c = run(CANE, [box])
        self.assertLess(c.clearance[0], 2.5)
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
        box = ((-0.1, 0, -2.3), (0.5, 1.2, -2.0))
        c = run(fake.pose(pitch_deg=-25, height=0.9, roll_deg=90), [box])
        self.assertLess(c.clearance[0], 2.5)
        self.assertTrue(c.best is None or c.best < 0)

    def test_low_floor_items_ignored(self):
        mat = ((-0.5, 0, -2.5), (0.5, 0.05, -1.5))  # 5 cm high doormat
        self.assertEqual(run(CANE, [mat]).raw_cmd, "CENTER")



class Maps(unittest.TestCase):
    """The dashboard's per-pixel maps: same decision with or without them, and sensible contents."""

    def run_maps(self, boxes=()):
        f = render(CANE, boxes)
        d, c = arrays(f)
        plain = check(d, c, f.fx, f.fy, f.cx, f.cy, f.pose)
        mapped = check(d, c, f.fx, f.fy, f.cx, f.cy, f.pose, want_maps=True)
        return plain, mapped

    def test_maps_do_not_change_the_decision(self):
        for boxes in ((), [WALL_AHEAD], [((-0.1, 0, -2.3), (0.5, 1.2, -2.0))]):
            plain, mapped = self.run_maps(boxes)
            self.assertIsNone(plain.maps)
            self.assertEqual((plain.clearance, plain.best, plain.raw_cmd), (mapped.clearance, mapped.best, mapped.raw_cmd))

    def test_open_floor_is_floor(self):
        m = self.run_maps()[1].maps
        self.assertGreater((m["kind"] == MAP_FLOOR).mean(), 0.3)
        self.assertEqual(int((m["kind"] == MAP_OBSTACLE).sum()), 0)

    def test_wall_pixels_are_obstacles_in_the_centre_corridor(self):
        m = self.run_maps([WALL_AHEAD])[1].maps
        ob = m["kind"] == MAP_OBSTACLE
        self.assertGreater(ob.sum(), 100)
        centre_bit = 1 << HEADINGS.index(0)
        self.assertTrue(((m["corridor"] & centre_bit) > 0)[ob].any())
        self.assertAlmostEqual(float(np.median(m["along"][ob & ((m["corridor"] & centre_bit) > 0)])), 1.5, delta=0.3)

    def test_headings_cover_the_middle(self):
        m = self.run_maps()[1].maps
        h, w = m["heading"].shape
        self.assertEqual(int(m["heading"][h // 2, w // 2]), HEADINGS.index(0))


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

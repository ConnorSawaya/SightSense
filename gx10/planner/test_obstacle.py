"""Obstacle check on ray-cast scenes. Needs numpy: ../../venv-yolo/bin/python -m unittest planner.test_obstacle (from gx10/)."""

import unittest

import numpy as np

from navigator import fake

from .fake_scene import arrays, render
from .obstacle import FAR_M, HEADINGS, MAP_FLOOR, MAP_OBSTACLE, USABLE_M, Smoother, check


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


class Floor(unittest.TestCase):
    """What the check makes of the ground itself, and of the cane's own lower end.

    Ray-cast scenes with depth noise (about 1 cm plus 1 percent of the distance, an estimate for the
    phone's LiDAR). Not the phone: these show the rules hold on known shapes, nothing more."""

    def noisy(self, true_pose, believed=None, boxes=(), far_m=8.0, **kw):
        rng = np.random.default_rng(7)
        f = render(true_pose, boxes, far_m=far_m)
        d, c = arrays(f)
        z = d / 1000.0
        d = np.where(d > 0, (z + rng.normal(0, 0.01 + 0.01 * z)) * 1000.0, 0).clip(0, 65535).astype(np.uint16)
        return check(d, c, f.fx, f.fy, f.cx, f.cy, list(believed or true_pose), **kw)

    def test_level_floor_is_never_an_obstacle(self):
        for height in (0.7, 0.9, 1.1, 1.3):
            for pitch in (-25, -35, -45, -60):
                for roll in (0, 90):
                    c = self.noisy(fake.pose(pitch_deg=pitch, height=height, roll_deg=roll))
                    self.assertEqual((c.points, c.raw_cmd, c.clearance[0]), (0, "CENTER", FAR_M), (height, pitch, roll))

    def test_it_reports_how_high_the_phone_is_above_the_floor(self):
        self.assertAlmostEqual(self.noisy(fake.pose(pitch_deg=-25, height=1.1)).cam_h, 1.1, delta=0.05)

    def test_phone_tilted_too_little_cannot_judge_open_space(self):
        # LiDAR reaches about 5 m. Tilted only 10 degrees down, most of the view is floor further off
        # than that, with no reading, and no reading is not clear. 25 degrees down is enough.
        c = self.noisy(fake.pose(pitch_deg=-10, height=0.9), far_m=5.0)
        self.assertEqual((c.clearance[0], c.raw_cmd), (None, "STOP"))
        self.assertEqual(self.noisy(fake.pose(pitch_deg=-25, height=0.9), far_m=5.0).raw_cmd, "CENTER")

    def test_gentle_ramp_up_does_not_stop_the_cane(self):
        c = self.noisy(fake.pose(pitch_deg=-30, height=0.9), believed=CANE)  # the floor rises 5 degrees ahead
        self.assertEqual(c.raw_cmd, "CENTER")
        self.assertGreaterEqual(c.clearance[0], USABLE_M)

    def test_ground_falling_away_is_not_called_clear(self):
        # A floor dropping 6 degrees ahead, as before a drop-off: the ground at the feet reads as
        # blocked. Wrong about that ground, but on the side of stopping. Do not change it towards clear.
        c = self.noisy(fake.pose(pitch_deg=-19, height=0.9), believed=CANE)
        self.assertLess(c.clearance[0], USABLE_M)

    OWN = ((-0.05, 0.2, -0.5), (0.05, 0.6, -0.35))  # where the cane's own lower end shows: thin, dead ahead, inside the tip

    def test_own_cane_is_ignored_only_when_asked(self):
        self.assertLess(self.noisy(CANE, boxes=[self.OWN]).clearance[0], 0.8)  # as it is by default: an obstacle
        masked = self.noisy(CANE, boxes=[self.OWN], own_cane_m=0.65)
        self.assertEqual((masked.clearance[0], masked.raw_cmd), (FAR_M, "CENTER"))

    def test_ignoring_the_own_cane_does_not_hide_a_wall_a_wide_box_or_a_post_further_off(self):
        self.assertEqual(self.noisy(CANE, boxes=[WALL_AHEAD], own_cane_m=0.65).raw_cmd, "STOP")
        wide = ((-0.3, 0, -0.6), (0.3, 0.5, -0.4))
        self.assertLess(self.noisy(CANE, boxes=[wide], own_cane_m=0.65).clearance[0], 0.8)
        post = ((-0.05, 0, -1.0), (0.05, 1.2, -0.9))
        self.assertLess(self.noisy(CANE, boxes=[post], own_cane_m=0.65).clearance[0], 1.2)
        self.assertLess(self.noisy(CANE, boxes=[post], own_cane_m=5.0).clearance[0], 1.2)  # the strip never reaches the stop distance


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
        c = self.run_maps([WALL_AHEAD])[1]
        m = c.maps
        ob = m["kind"] == MAP_OBSTACLE
        self.assertGreater(ob.sum(), 100)
        centre = ob & ((m["corridor"] & (1 << HEADINGS.index(0))) > 0)
        self.assertTrue(centre.any())
        self.assertAlmostEqual(float(np.percentile(m["along"][centre], 5)), c.clearance[0], delta=0.1)  # where the wall is

    def test_headings_cover_the_middle(self):
        m = self.run_maps()[1].maps
        h, w = m["heading"].shape
        self.assertEqual(int(m["heading"][h // 2, w // 2]), HEADINGS.index(0))


class Smoothing(unittest.TestCase):
    def test_turns_need_six_frames_and_stop_two(self):
        s = Smoother(cmd="CENTER")
        said = [s.update("LEFT", -20, i / 15)[0] for i in range(6)]
        self.assertEqual(said, ["CENTER"] * 5 + ["LEFT"])  # about 0.4 s
        self.assertEqual(s.update("STOP", None, 0.5), ("LEFT", None))
        self.assertEqual(s.update("STOP", None, 0.55), ("STOP", "Obstacle ahead. Stop."))  # stops stay quick

    def test_a_reversal_waits(self):
        s = Smoother(cmd="CENTER")
        for i in range(6):
            s.update("LEFT", -20, i / 15)
        cmds = [s.update("RIGHT", 20, 0.4 + i / 15)[0] for i in range(30)]  # RIGHT straight after turning LEFT
        first_right = cmds.index("RIGHT")
        self.assertGreaterEqual(0.4 + first_right / 15 - 5 / 15, 1.5)  # not within 1.5 s of starting the left turn
        self.assertGreaterEqual(first_right + 1, 15)  # and 15 agreeing frames

    def test_straightening_out_does_not_wait(self):
        s = Smoother(cmd="CENTER")
        for i in range(6):
            s.update("LEFT", -20, i / 15)
        cmds = [s.update("CENTER", 0, 0.4 + i / 15)[0] for i in range(6)]
        self.assertEqual(cmds[-1], "CENTER")

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

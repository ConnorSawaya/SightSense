"""Does the cane steer round things, or just stop? python3 -m unittest planner.test_walk (from gx10/; about 15 s).

A simulated walker follows the wheel through ray-cast scenes with depth noise: LEFT or RIGHT
turns them 30 degrees a second at 0.4 m/s, CENTER walks straight at 0.5 m/s, STOP stands still.
It shows how the rules behave on known shapes. It is not a test on the cane.
"""

import math
import unittest

import numpy as np

from navigator import fake

from .fake_scene import arrays, render
from .obstacle import STOP_AHEAD_M, Smoother, check

FPS, TURN_DEG_S = 15, 30.0


def wall(x0, x1, z):
    return ((x0, 0, z - 0.15), (x1, 2.2, z))


def gap(x, z, boxes):
    """Distance along the floor from the walker to the nearest box."""
    return min((math.hypot(max(x0 - x, 0, x - x1), max(z0 - z, 0, z - z1)) for (x0, _, z0), (x1, _, z1) in boxes), default=9.9)


def walk(boxes, goal_m, follows_the_wheel=True, roll=0, seconds=30):
    """Returns (reached the goal, seconds stopped after the start, nearest approach in metres, commands in order)."""
    rng = np.random.default_rng(3)
    x = z = yaw = t = stopped = 0.0
    sm, nearest, cmds = Smoother(), 9.9, []
    while t < seconds and -z < goal_m:
        f = render(fake.pose(x=x, z=z, yaw_deg=yaw, pitch_deg=-30, roll_deg=roll, height=0.9), boxes)
        d, c = arrays(f)
        m = d / 1000.0
        d = np.where(d > 0, (m + rng.normal(0, 0.01 + 0.01 * m)) * 1000.0, 0).clip(0, 65535).astype(np.uint16)
        k = check(d, c, f.fx, f.fy, f.cx, f.cy, f.pose, 0.0, sm.last_heading, stopped=sm.cmd == "STOP")
        cmd, _ = sm.update(k.raw_cmd, k.best, t)
        if not cmds or cmds[-1] != cmd:
            cmds.append(cmd)
        if cmd == "STOP":
            stopped += 1 / FPS if t > 0.5 else 0  # every session begins in STOP for two frames
            if stopped > 3:
                break
        else:
            turning = follows_the_wheel and cmd in ("LEFT", "RIGHT")
            if turning:
                yaw += (TURN_DEG_S if cmd == "LEFT" else -TURN_DEG_S) / FPS
            speed = 0.4 if turning else 0.5
            x -= math.sin(math.radians(yaw)) * speed / FPS
            z -= math.cos(math.radians(yaw)) * speed / FPS
        nearest = min(nearest, gap(x, z, boxes))
        t += 1 / FPS
    return -z >= goal_m, stopped, nearest, cmds


class SteersRound(unittest.TestCase):
    def passes(self, boxes, goal_m, **kw):
        reached, stopped, nearest, cmds = walk(boxes, goal_m, **kw)
        self.assertTrue(reached, cmds)
        self.assertEqual(stopped, 0, cmds)  # it steered; it did not stop
        self.assertGreater(nearest, 0.25, cmds)
        return cmds

    def test_round_a_box_in_the_path(self):
        cmds = self.passes([((-0.3, 0, -3.3), (0.3, 1.0, -3.0))], 6.0)
        self.assertTrue({"LEFT", "RIGHT"} & set(cmds))

    def test_through_a_doorway_off_to_one_side(self):
        self.assertIn("RIGHT", self.passes([wall(-3, 0.1, -3.0), wall(1.1, 3, -3.0)], 6.0))

    def test_along_a_corridor_past_a_box_with_the_phone_upright(self):
        corridor = [((-0.95, 0, -8), (-0.8, 2.2, 1)), ((0.8, 0, -8), (0.95, 2.2, 1)), ((-0.8, 0, -3.4), (-0.2, 1.0, -3.0))]
        self.passes(corridor, 6.5, roll=90)

    def test_straight_through_a_doorway_ahead_without_turning(self):
        self.assertEqual(self.passes([wall(-3, -0.5, -3.0), wall(0.5, 3, -3.0)], 6.0), ["STOP", "CENTER"])

    def test_someone_who_ignores_the_wheel_is_stopped_before_the_wall(self):
        reached, stopped, nearest, cmds = walk([wall(-4, 4, -3.0)], 6.0, follows_the_wheel=False)
        self.assertFalse(reached)
        self.assertEqual(cmds[-1], "STOP")
        self.assertGreater(nearest, 0.5)  # stopped with room to spare
        self.assertLess(nearest, STOP_AHEAD_M + 0.1)


if __name__ == "__main__":
    unittest.main()

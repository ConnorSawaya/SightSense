"""Runs the GX10's real frame pipeline against the Pi's steering rules.

    python3 -m unittest test_with_gx10 -v        (from this folder)

Frames from the GX10 code's fake phone go through its real pipeline (depth
obstacle check, navigator, smoothing), and the command it would send to the
Pi goes into the steering rules on the simulated wheel.

Skipped where the GX10 code's own requirements (numpy, OpenCV) are missing.
The vision-language model is stubbed out and YOLO is off. Neither decides the
wheel command: clear or blocked comes from depth.
"""

import sys
import unittest
from pathlib import Path

from steering import CENTER, COMMANDS, parse_command
from test_steering import Bench

GX10 = Path(__file__).resolve().parent.parent / "gx10"
try:
    sys.path.insert(0, str(GX10))
    import vlm
    from ingest.fake_phone import walk_frames
    from ingest.server import Pipeline
except Exception as problem:  # no gx10 folder, or numpy / OpenCV not installed
    Pipeline, WHY = None, repr(problem)
else:
    WHY = ""


@unittest.skipUnless(Pipeline, f"the GX10 code cannot be loaded here: {WHY}")
class WalkAtAWall(unittest.TestCase):
    """The fake phone walks at a wall 4 m away at 0.5 m/s for 8 seconds."""

    @classmethod
    def setUpClass(cls):
        vlm.warm = lambda *a, **k: "stubbed for the test"
        pipe = Pipeline(False)
        cls.bench = Bench().started()
        cls.commands, cls.walls = [], []
        for message, wall_m in walk_frames():
            cls.walls.append(wall_m)
            _, for_pi = pipe.process(message, 0.0)
            cmd, ttl_ms, _seq = parse_command(for_pi)
            cls.commands.append(cmd)
            cls.bench.steering.command(cmd, cls.bench.now, ttl_ms)
            cls.bench.run(1 / 15)

    def test_every_command_is_one_the_pi_knows(self):
        self.assertTrue(set(self.commands) <= set(COMMANDS))
        self.assertEqual(len(self.commands), 120)

    def test_goes_straight_while_clear_and_stops_at_the_wall(self):
        far = {cmd for cmd, wall_m in zip(self.commands, self.walls) if wall_m > 2.0}
        near = {cmd for cmd, wall_m in zip(self.commands, self.walls) if wall_m < 0.6}
        self.assertIn("CENTER", far)
        self.assertEqual(near, {"STOP"})  # the obstacle check stops for a wall inside 0.8 m (gx10/planner)
        self.assertEqual(self.commands[-1], "STOP")

    def test_wheel_ends_centred_and_inside_its_limits(self):
        self.assertEqual(self.bench.wheel.pressed(), {CENTER})
        self.assertFalse(self.bench.wheel.on)
        self.bench.check_limits(self)

    def test_driver_goes_off_when_the_frames_stop(self):
        self.bench.run(1.0)
        self.assertIsNone(self.bench.steering.want)
        self.assertTrue(self.bench.logged("no command for 400 ms"))


if __name__ == "__main__":
    unittest.main()

"""python3 -m unittest planner.test_cue   (from gx10/)"""

import unittest

from planner.cue import GAP_S, REPEAT_S, UNKNOWN_FRAMES, DirectionCue


def run(frames, start=0.0, fps=15, cue=None):
    """frames: list of (cmd, ahead). Returns the cues, one per frame."""
    cue = cue or DirectionCue()
    return [cue.update(cmd, ahead, start + i / fps) for i, (cmd, ahead) in enumerate(frames)]


def sounds(cues):
    return [(c.earcon, c.speech) for c in cues if c.earcon or c.speech]


class TestDirectionCue(unittest.TestCase):
    def test_straight_is_silent(self):
        cues = run([("CENTER", 4.0)] * 150)
        self.assertEqual(sounds(cues), [])
        self.assertEqual(cues[-1].direction, "STRAIGHT")

    def test_long_stop_sounds_once(self):
        # The old rule sent the stop beep with every frame; the app played it once a second.
        cues = run([("CENTER", 4.0)] * 5 + [("STOP", 0.5)] * 150)
        self.assertEqual(sounds(cues), [("stop", None)])

    def test_turn_is_said_once(self):
        cues = run([("CENTER", 4.0)] * 5 + [("LEFT", 1.0)] * 60)
        self.assertEqual(sounds(cues), [("left", "Bear left")])

    def test_back_to_straight_is_silent(self):
        cues = run([("RIGHT", 1.0)] * 30 + [("CENTER", 4.0)] * 60)
        self.assertEqual(sounds(cues), [("right", "Bear right")])

    def test_left_right_jitter_is_held_back(self):
        # Direction flips every half second: at most one spoken direction every GAP_S.
        frames = [("LEFT" if (i // 8) % 2 == 0 else "RIGHT", 1.0) for i in range(150)]
        cues = run(frames)
        times = [i / 15 for i, c in enumerate(cues) if c.speech]
        self.assertTrue(all(b - a >= GAP_S for a, b in zip(times, times[1:])), times)
        self.assertLessEqual(len(times), 10 / GAP_S + 1)

    def test_same_direction_not_repeated_soon(self):
        frames = [("LEFT", 1.0)] * 10 + [("CENTER", 4.0)] * 10 + [("LEFT", 1.0)] * 10
        self.assertEqual(len([c for c in run(frames) if c.speech]), 1)
        later = [("LEFT", 1.0)] * 10 + [("CENTER", 4.0)] * int(REPEAT_S * 15) + [("LEFT", 1.0)] * 10
        self.assertEqual(len([c for c in run(later) if c.speech]), 2)

    def test_stop_is_never_held_back(self):
        cues = run([("LEFT", 1.0)] * 3 + [("STOP", 0.5)])
        self.assertEqual(cues[0].speech, "Bear left")
        self.assertEqual((cues[-1].direction, cues[-1].earcon), ("STOP", "stop"))

    def test_turn_said_after_the_gap_if_still_true(self):
        # Right is said, then left comes 1 s later: held back, and said once GAP_S has passed.
        frames = [("RIGHT", 1.0)] * 15 + [("LEFT", 1.0)] * 30
        cues = run(frames)
        said = [(i / 15, c.speech) for i, c in enumerate(cues) if c.speech]
        self.assertEqual([s for _, s in said], ["Bear right", "Bear left"])
        self.assertGreaterEqual(said[1][0] - said[0][0], GAP_S)

    def test_unknown_needs_frames_and_is_said_once(self):
        cues = run([("CENTER", 4.0)] * 5 + [("CENTER", None)] * (UNKNOWN_FRAMES - 1) + [("CENTER", 4.0)] * 5)
        self.assertEqual(sounds(cues), [])
        cues = run([("CENTER", 4.0)] * 5 + [("CENTER", None)] * 60)
        self.assertEqual(sounds(cues), [("unknown", "Can't see ahead")])
        self.assertEqual(cues[-1].direction, "UNKNOWN")


if __name__ == "__main__":
    unittest.main()

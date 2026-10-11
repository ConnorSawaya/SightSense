"""The answer to "is the path clear". ../../venv-yolo/bin/python -m unittest ingest.test_path_answer (from gx10/)."""

import unittest

from planner.obstacle import FAR_M

from .server import path_answer


class PathAnswer(unittest.TestCase):
    def test_nothing_ahead_while_steering_to_one_side(self):
        # FAR_M is the end of the range: no obstacle points at all, not a thing that far away
        self.assertEqual(path_answer("LEFT", FAR_M),
                         "Nothing detected straight ahead as far as I can measure. Steering left. Keep using your cane.")

    def test_the_other_answers(self):
        self.assertEqual(path_answer("CENTER", FAR_M), "Nothing detected straight ahead as far as I can measure. Keep using your cane.")
        self.assertTrue(path_answer("CENTER", 2.0).startswith("Nothing detected straight ahead for about "))
        self.assertTrue(path_answer("RIGHT", 2.0).startswith("Something is "))
        self.assertTrue(path_answer("RIGHT", 2.0).endswith(" ahead. Steering right."))
        self.assertTrue(path_answer("STOP", 0.5).startswith("No. Something is "))
        self.assertTrue(path_answer("CENTER", None).startswith("I can't tell."))

    def test_it_never_says_safe_or_clear(self):
        for cmd in ("LEFT", "CENTER", "RIGHT", "STOP"):
            for ahead in (None, 0.2, 1.0, 2.0, FAR_M):
                answer = path_answer(cmd, ahead).lower()
                self.assertNotIn("safe", answer)
                self.assertNotIn("is clear", answer)


if __name__ == "__main__":
    unittest.main()

"""python3 -m unittest detector.test_stable (from gx10/). Standard library only."""

import unittest

from .detector import Detection
from .stable import Stabilizer, iou

CHAIR = [100, 100, 200, 300]


def chair(conf=0.8, dx=0):
    return Detection("chair", conf, [CHAIR[0] + dx, CHAIR[1], CHAIR[2] + dx, CHAIR[3]])


def labels(out):
    return [d.label for d in out]


class Steady(unittest.TestCase):
    def test_iou(self):
        self.assertEqual(iou(CHAIR, CHAIR), 1.0)
        self.assertEqual(iou(CHAIR, [300, 300, 400, 400]), 0.0)
        self.assertAlmostEqual(iou([0, 0, 10, 10], [5, 0, 15, 10]), 1 / 3)

    def test_appears_on_the_third_frame(self):
        s = Stabilizer()
        self.assertEqual([labels(s.update([chair()])) for _ in range(3)], [[], [], ["chair"]])

    def test_one_missed_frame_does_not_hide_it(self):
        s = Stabilizer()
        for _ in range(5):
            s.update([chair()])
        self.assertEqual(labels(s.update([])), ["chair"])
        self.assertEqual(labels(s.update([chair()])), ["chair"])

    def test_hidden_once_gone(self):
        s = Stabilizer()
        for _ in range(5):
            s.update([chair()])
        shown = [bool(s.update([])) for _ in range(6)]
        self.assertEqual(shown, [True, True, True, False, False, False])
        self.assertEqual(s.tracks, [])  # forgotten after a whole window

    def test_blinking_object_stays_hidden(self):
        s = Stabilizer()
        out = [s.update([chair()] if i % 3 == 0 else []) for i in range(12)]
        self.assertTrue(all(o == [] for o in out))

    def test_low_confidence_never_shown_but_dip_after_showing_is_kept(self):
        s = Stabilizer()
        self.assertTrue(all(s.update([chair(0.3)]) == [] for _ in range(6)))
        s = Stabilizer()
        for _ in range(3):
            s.update([chair(0.6)])
        self.assertEqual(labels(s.update([chair(0.27)])), ["chair"])

    def test_two_chairs_are_two_objects(self):
        s = Stabilizer()
        for _ in range(3):
            out = s.update([chair(), chair(dx=300)])
        self.assertEqual(len(out), 2)

    def test_different_label_is_a_different_object(self):
        s = Stabilizer()
        for _ in range(3):
            s.update([chair()])
        out = s.update([Detection("couch", 0.9, CHAIR)])
        self.assertEqual(labels(out), ["chair"])

    def test_box_follows_the_object(self):
        s = Stabilizer()
        for _ in range(3):
            s.update([chair()])
        box = s.update([chair(dx=20)])[0].box
        self.assertTrue(100 < box[0] < 120)  # moves most of the way, not all
        for _ in range(8):
            box = s.update([chair(dx=20)])[0].box
        self.assertEqual(box[0], 120)

    def test_hazards_shown_from_a_lower_confidence(self):
        s = Stabilizer()
        for _ in range(3):
            out = s.update([Detection("door", 0.32, CHAIR, "open"), chair(0.32)])
        self.assertEqual([(d.label, d.source) for d in out], [("door", "open")])

    def test_output_is_a_copy(self):
        s = Stabilizer()
        for _ in range(3):
            out = s.update([chair()])
        out[0].box[0] = 0
        self.assertEqual(s.update([chair()])[0].box[0], 100)


if __name__ == "__main__":
    unittest.main()

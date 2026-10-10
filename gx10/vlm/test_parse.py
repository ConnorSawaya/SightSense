"""Tests for reply parsing. No model needed: python3 -m unittest vlm.test_parse (from gx10/)."""

import unittest

from .core import _clean, jpeg_size, parse_box

SIZE = (640, 480)


class ParseBox(unittest.TestCase):
    def test_object_on_1000_scale(self):
        self.assertEqual(parse_box('{"bbox_2d": [500, 500, 750, 1000], "label": "apple"}', SIZE), ([320, 240, 480, 480], "apple"))

    def test_list_in_code_fence(self):
        raw = '```json\n[{"bbox_2d": [0, 0, 100, 100], "label": "apple"}]\n```'
        self.assertEqual(parse_box(raw, SIZE), ([0, 0, 64, 48], "apple"))

    def test_bare_box(self):
        self.assertEqual(parse_box("[500, 500, 750, 1000]", SIZE), ([320, 240, 480, 480], None))

    def test_pixels(self):
        self.assertEqual(parse_box('{"bbox_2d": [10, 20, 110, 220]}', SIZE, "pixels"), ([10, 20, 110, 220], None))

    def test_null_means_not_seen(self):
        self.assertEqual(parse_box('{"bbox_2d": null, "label": "apple"}', SIZE), (None, "apple"))
        self.assertEqual(parse_box("[]", SIZE), (None, None))

    def test_garbage_does_not_parse(self):
        for raw in ["", "I see an apple on the left.", '{"box": [1,2,3,4]}', '{"bbox_2d": [1, 2, 3]}',
                    '{"bbox_2d": ["a", 2, 3, 4]}', '{"bbox_2d": [0, 0, 1200, 50]}', '{"bbox_2d": [5, 5, 5, 5]}']:
            self.assertIsNone(parse_box(raw, SIZE), raw)

    def test_swapped_corners_are_sorted(self):
        self.assertEqual(parse_box('{"bbox_2d": [750, 1000, 500, 500]}', SIZE)[0], [320, 240, 480, 480])


class Other(unittest.TestCase):
    def test_clean_drops_reasoning(self):
        self.assertEqual(_clean('<think>hmm</think>\n "A hallway."'), "A hallway.")

    def test_jpeg_size(self):
        # smallest valid-looking header: SOI, SOF0 with height 480 and width 640
        sof = b"\xff\xc0\x00\x11\x08\x01\xe0\x02\x80" + b"\x00" * 12
        self.assertEqual(jpeg_size(b"\xff\xd8" + sof), (640, 480))
        png = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + (640).to_bytes(4, "big") + (480).to_bytes(4, "big")
        self.assertEqual(jpeg_size(png), (640, 480))
        with self.assertRaises(ValueError):
            jpeg_size(b"hello")


if __name__ == "__main__":
    unittest.main()

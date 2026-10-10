"""Turning pictures upright and mapping boxes back. Needs OpenCV: ../../venv-yolo/bin/python -m unittest ingest.test_upright"""

import unittest

import cv2
import numpy as np

from navigator import fake

from .upright import box_back, rotate_jpeg, turn_for


def white_box(img):
    ys, xs = np.nonzero(img[..., 0] > 128)
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


class Upright(unittest.TestCase):
    def test_turn_for_mounts(self):
        self.assertEqual(turn_for(fake.pose(pitch_deg=-25)), 0)
        self.assertEqual(turn_for(fake.pose(pitch_deg=-25, roll_deg=180)), 2)
        self.assertEqual({turn_for(fake.pose(pitch_deg=-25, roll_deg=r)) for r in (90, -90)}, {1, 3})

    def test_rolled_camera_turns_world_down_to_bottom(self):
        for roll in (90, -90, 180):
            p = fake.pose(pitch_deg=0, roll_deg=roll)
            k = turn_for(p)
            # a point below the camera, projected, then turned, must be in the lower half
            u, v, _ = fake.project(p, (0, 0.6, -2), 640, 480)  # 0.4 m below the camera, 2 m ahead
            img = np.zeros((480, 640, 3), np.uint8)
            cv2.circle(img, (int(u), int(v)), 6, (255, 255, 255), -1)
            turned = cv2.imdecode(np.frombuffer(rotate_jpeg(cv2.imencode(".png", img)[1].tobytes(), k), np.uint8), 1)
            box = white_box(turned)
            self.assertGreater((box[1] + box[3]) / 2, turned.shape[0] / 2, roll)

    def test_box_back_round_trip(self):
        img = np.zeros((480, 640, 3), np.uint8)
        img[100:180, 400:460] = 255
        jpeg = cv2.imencode(".png", img)[1].tobytes()
        for k in (0, 1, 2, 3):
            turned = cv2.imdecode(np.frombuffer(rotate_jpeg(jpeg, k), np.uint8), 1)
            back = box_back(white_box(turned), k, 640, 480)
            for got, want in zip(back, [400, 100, 460, 180]):
                self.assertLessEqual(abs(got - want), 2, (k, back))


if __name__ == "__main__":
    unittest.main()

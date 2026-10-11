"""Turn the phone's picture upright for YOLO and the vision-language model, and map boxes back.

ARKit sends the picture in the sensor's landscape direction. With the phone
upright on the cane it arrives turned 90 degrees (seen on the first real frames).
Gravity from the pose says which way is down; the picture is turned in 90-degree
steps so that down is at the bottom. Boxes found on the upright picture are mapped
back to the original picture, which is what the depth lines up with.
"""

import cv2
import numpy as np

# turn: 0 none, 1 = 90 clockwise, 2 = 180, 3 = 90 anticlockwise
_CV = {1: cv2.ROTATE_90_CLOCKWISE, 2: cv2.ROTATE_180, 3: cv2.ROTATE_90_COUNTERCLOCKWISE}


def turn_for(pose) -> int:
    """Which turn puts world-down at the bottom of the picture."""
    M = np.asarray(pose, dtype=np.float64).reshape(4, 4).T
    g = M[:3, :3].T @ np.array([0.0, -1.0, 0.0])  # world down, in camera axes
    du, dv = g[0], -g[1]  # in picture axes: u right, v down
    if abs(dv) >= abs(du):
        return 0 if dv > 0 else 2
    return 1 if du > 0 else 3  # down on the right: turn clockwise


def decode_upright(jpeg: bytes, turn: int):
    """The phone's JPEG decoded once and turned upright, as a BGR image array (None if it will not decode)."""
    img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
    if img is None or turn == 0:
        return img
    return cv2.rotate(img, _CV[turn])


def rotate_jpeg(jpeg: bytes, turn: int, quality: int = 85) -> bytes:
    if turn == 0:
        return jpeg
    img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return jpeg
    ok, out = cv2.imencode(".jpg", cv2.rotate(img, _CV[turn]), [cv2.IMWRITE_JPEG_QUALITY, quality])
    return out.tobytes() if ok else jpeg


def box_back(box, turn: int, w: int, h: int):
    """A box on the turned picture -> the same box on the original w x h picture."""
    if box is None or turn == 0:
        return box
    x1, y1, x2, y2 = box
    if turn == 1:  # original (u, v) went to (h - v, u)
        pts = [(y1, h - x1), (y2, h - x2)]
    elif turn == 3:  # original (u, v) went to (v, w - u)
        pts = [(w - y1, x1), (w - y2, x2)]
    else:  # 180
        pts = [(w - x1, h - y1), (w - x2, h - y2)]
    us, vs = sorted(p[0] for p in pts), sorted(p[1] for p in pts)
    return [round(us[0]), round(vs[0]), round(us[1]), round(vs[1])]

"""Are left and right the right way round? Checked on real phone recordings against the picture.

    ../../venv-yolo/bin/python -m planner.check_directions [recording ...]     (from gx10/, on the GX10)

The rear camera's picture, turned upright, is the ground truth: what is on its left is on the user's
left. Three things must agree with it:

1. LiDAR headings: the obstacle check's -30 degree wedge must lie on the left of the upright picture.
2. Object bearings: a detection on the left of the upright picture must get a negative bearing.
3. Turning: when the pose says the phone turned right, the picture must slide left.

Prints how many frames agree. Needs recordings in ../../recordings (not committed).
"""

import sys
from pathlib import Path

import cv2
import numpy as np

from ingest.server import locate
from ingest.upright import box_back, decode_upright, turn_for
from navigator.frame import decode
from planner.obstacle import HEADINGS, check
from planner.recovery import yaw_deg

REC = Path(__file__).resolve().parents[3] / "recordings"
_CV = {1: cv2.ROTATE_90_CLOCKWISE, 2: cv2.ROTATE_180, 3: cv2.ROTATE_90_COUNTERCLOCKWISE}


def arrays(f):
    d = np.frombuffer(f.depth_mm, np.uint16).reshape(f.depth_h, f.depth_w)
    c = np.frombuffer(f.conf, np.uint8).reshape(f.depth_h, f.depth_w)
    return d, c


def headings_vs_picture(frames):
    """Mean column, in the upright picture, of each heading's wedge: must rise from -30 to +30."""
    good = bad = 0
    for f in frames:
        d, c = arrays(f)
        r = check(d, c, f.fx, f.fy, f.cx, f.cy, f.pose, want_maps=True)
        if r.maps is None:
            continue
        turn = turn_for(f.pose)
        hm = r.maps["heading"]
        hm = cv2.rotate(hm, _CV[turn]) if turn else hm
        cols = [np.nonzero(hm == i)[1].mean() for i in range(len(HEADINGS)) if (hm == i).sum() > 50]
        if len(cols) < 3:
            continue
        rising = cols[-1] > cols[0]
        good, bad = good + rising, bad + (not rising)
    return good, bad


def objects_vs_picture(frames, det):
    """A detection clearly left of the upright picture's middle must have a negative bearing."""
    good = bad = 0
    examples = []
    for f in frames:
        turn = turn_for(f.pose)
        img = decode_upright(f.jpeg, turn)
        if img is None:
            continue
        d, c = arrays(f)
        w = img.shape[1]
        for x in det.detect_image(img, conf=0.5):
            cx = (x.box[0] + x.box[2]) / 2 / w - 0.5  # -0.5 left edge .. 0.5 right edge, upright
            if abs(cx) < 0.15:
                continue
            x.box = box_back(x.box, turn, f.rgb_w, f.rgb_h)
            locate(x, f, d, c)
            if x.bearing is None:
                continue
            ok = (cx < 0) == (x.bearing < 0)
            good, bad = good + ok, bad + (not ok)
            if not ok and len(examples) < 5:
                examples.append(f"{x.label} at {cx:+.2f} of the picture, bearing {x.bearing:+.0f}")
    return good, bad, examples


def turning_vs_picture(frames):
    """Pose says turned right (yaw up) -> the upright picture slides left (phase correlation dx < 0)."""
    good = bad = 0
    prev = None
    for f in frames:
        turn = turn_for(f.pose)
        img = decode_upright(f.jpeg, turn)
        yaw = yaw_deg(f.pose)
        if img is None or yaw is None:
            prev = None
            continue
        g = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (160, 120)).astype(np.float32)
        if prev is not None:
            dyaw = ((yaw - prev[1] + 180) % 360) - 180
            (dx, _dy), response = cv2.phaseCorrelate(prev[0], g)
            if 3 <= abs(dyaw) <= 25 and abs(dx) >= 2 and response > 0.1:
                ok = (dyaw > 0) == (dx < 0)
                good, bad = good + ok, bad + (not ok)
        prev = (g, yaw)
    return good, bad


def main():
    from detector.detector import Detector

    recs = sys.argv[1:] or ["20261010-190000", "20261011-105137", "20261011-002739"]
    det = Detector(hazards=[])
    for rec in recs:
        files = sorted((REC / rec).glob("*.bin"))
        frames = [decode(p.read_bytes()) for p in files[::10]]
        turning = [decode(p.read_bytes()) for p in files[: min(len(files), 1500) : 3]]
        h = headings_vs_picture(frames)
        o = objects_vs_picture(frames, det)
        t = turning_vs_picture(turning)
        print(f"{rec}: LiDAR headings left-to-right in the picture {h[0]}/{sum(h)}; "
              f"object bearings on the right side {o[0]}/{o[0] + o[1]}; turning matches the picture {t[0]}/{sum(t)}")
        for e in o[2]:
            print("   wrong side:", e)


if __name__ == "__main__":
    main()

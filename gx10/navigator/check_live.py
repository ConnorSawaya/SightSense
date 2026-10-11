"""Live check with the real vision-language model, no phone needed.

Uses the vlm test pictures (python3 vlm/make_test_images.py ...) with a made-up
depth picture: the wall at 4 m and the apple's true box at 2.5 m. Runs the
Navigator at 15 frames per second of real time and prints what it would say.

    cd gx10 && python3 -m navigator.check_live
    cd gx10 && ../../venv-yolo/bin/python -m navigator.check_live --yolo   # with YOLO every frame
"""

import json
import sys
import time
from array import array
from pathlib import Path

import vlm

from . import fake
from .navigator import Navigator

PICS = Path(__file__).parent.parent / "vlm" / "test_images"


def frame_from_picture(name, seq, box_depth_m=2.5):
    truth = json.loads((PICS / "truth.json").read_text()).get(name, {})
    f = fake.frame(fake.pose(pitch_deg=0), seq=seq, t=time.monotonic())
    f.jpeg = (PICS / name).read_bytes()
    box = truth.get("bbox_px")
    if box:
        sx, sy = f.depth_w / f.rgb_w, f.depth_h / f.rgb_h
        depth = array("H", f.depth_mm)
        for v in range(int(box[1] * sy), int(box[3] * sy) + 1):
            for u in range(int(box[0] * sx), int(box[2] * sx) + 1):
                depth[v * f.depth_w + u] = int(box_depth_m * 1000)
        f.depth_mm = depth
    return f


DETECTOR = None  # set by --yolo


def drive(nav, picture, seconds, seq, stop_when=None):
    t_end = time.monotonic() + seconds
    t0 = time.monotonic()
    while time.monotonic() < t_end:
        seq += 1
        f = frame_from_picture(picture, seq)
        dets = DETECTOR.detect(f.jpeg) if DETECTOR else None
        g = nav.on_frame(f, dets)
        if g.speech or g.lookup:
            extra = f"  bearing {g.desired_bearing:+.1f}" if g.desired_bearing is not None else ""
            print(f"  {time.monotonic() - t0:5.2f}s  [{g.state}] says: {g.speech!r}" + (f"  lookup {g.lookup!r}" if g.lookup else "") + extra)
        if stop_when and stop_when(g):
            return g, seq
        time.sleep(1 / 15)
    return g, seq


def main():
    global DETECTOR
    print("model:", vlm.warm())
    if "--yolo" in sys.argv:  # needs the project virtual environment (see detector/README.md)
        from detector.detector import Detector

        DETECTOR = Detector()
        print("yolo:", DETECTOR.using)
    nav = Navigator(vlm)
    seq = 0

    for picture, side in (("apple_left.jpg", "left"), ("apple_right.jpg", "right")):
        print(f'\n"guide me to the apple" on {picture}')
        nav.on_voice("guide me to the apple")
        g, seq = drive(nav, picture, 8, seq, lambda g: g.state == "CONFIRMING" and g.speech is None)
        nav.on_voice("yes")
        g, seq = drive(nav, picture, 1, seq)
        ok = g.state == "GUIDING" and g.desired_bearing is not None and (g.desired_bearing < 0) == (side == "left")
        print(f"  guiding, desired bearing {g.desired_bearing}  ->  {'PASS' if ok else 'FAIL'} (apple is {side})")
        nav.on_voice("stop")
        drive(nav, picture, 0.2, seq)

    print('\n"guide me to the apple" on empty_room.jpg (no apple; should keep searching, never confirm)')
    nav.on_voice("guide me to the apple")
    g, seq = drive(nav, "empty_room.jpg", 5, seq, lambda g: g.state == "CONFIRMING")
    print(f"  state after 5 s: {g.state}  ->  {'PASS' if g.state == 'SEARCHING' else 'FAIL'}")
    nav.on_voice("stop")
    drive(nav, "empty_room.jpg", 0.2, seq)

    for text, picture in (("what's in front of me", "street.jpg"), ("read the sign", "sign_exit.jpg")):
        print(f'\n"{text}" on {picture}')
        nav.on_voice(text)
        drive(nav, picture, 8, seq, lambda g: g.speech is not None)


if __name__ == "__main__":
    main()

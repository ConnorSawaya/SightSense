"""Run YOLO on the vlm test pictures and time it.

    ../venv-yolo/bin/python -m detector.check            # from gx10/
    ../venv-yolo/bin/python -m detector.check --export   # export a TensorRT engine first
"""

import statistics
import sys
import time
from pathlib import Path

from .detector import Detector, export_engine

PICS = Path(__file__).parent.parent / "vlm" / "test_images"
RUNS = 100


def main():
    if "--export" in sys.argv:
        print("exported:", export_engine())
    d = Detector()
    print("model:", d.using)
    for name in ("street.jpg", "apple_left.jpg", "apple_right.jpg", "empty_room.jpg"):
        jpeg = (PICS / name).read_bytes()
        dets = d.detect(jpeg)
        print(f"  {name:16s} " + (", ".join(f"{x.label} {x.conf:.2f} {x.box}" for x in dets) or "nothing"))
    jpeg = (PICS / "street.jpg").read_bytes()
    for _ in range(10):
        d.detect(jpeg)  # warm up
    times = []
    for _ in range(RUNS):
        t = time.monotonic()
        d.detect(jpeg)
        times.append((time.monotonic() - t) * 1000)
    times.sort()
    print(f"  per frame, JPEG decode included: median {statistics.median(times):.1f} ms, "
          f"95th percentile {times[int(RUNS * 0.95)]:.1f} ms over {RUNS} runs")


if __name__ == "__main__":
    main()

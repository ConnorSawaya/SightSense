"""Run describe / read / find on the saved test pictures and score them.

    python3 make_test_images.py apple.jpg street.jpg   # once
    cd .. && python3 -m vlm.check

Also prints each find box under both scales (0-1000 and pixels), which is how
the box scale for a model was checked.
"""

import json
from pathlib import Path

from . import core

PICS = Path(__file__).parent / "test_images"


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0


def main():
    truth = json.loads((PICS / "truth.json").read_text())
    print("model:", core.warm())
    passed = total = 0
    for name, t in truth.items():
        jpeg = (PICS / name).read_bytes()
        a = core.describe(jpeg)
        print(f"\n{name}\n  describe {a.seconds:4.1f}s  {a.text!r}" + (f"  [{a.error}]" if a.error else ""))
        total += 1
        passed += a.ok

        if "read" in t:
            a = core.read(jpeg)
            want = t["read"]
            ok = a.ok and (all(w.lower() in a.text.lower() for w in want) if want else a.text == "")
            print(f"  read     {a.seconds:4.1f}s  {a.text!r}  {'PASS' if ok else 'FAIL'}" + (f"  [{a.error}]" if a.error else ""))
            total += 1
            passed += ok

        if "find" in t:
            a = core.find(jpeg, t["find"])
            want = t["bbox_px"]
            if want is None:
                ok = a.ok and a.box is None
                detail = ""
            else:
                ok = a.ok and a.box is not None and iou(a.box, want) >= 0.5
                size = core.jpeg_size(jpeg)
                as_1000 = core.parse_box(a.raw, size, "1000")
                as_px = core.parse_box(a.raw, size, "pixels")
                detail = (f"  true {want}  IoU if 0-1000: {iou(as_1000[0], want) if as_1000 and as_1000[0] else 0:.2f}"
                          f"  IoU if pixels: {iou(as_px[0], want) if as_px and as_px[0] else 0:.2f}")
            print(f"  find     {a.seconds:4.1f}s  box {a.box}  {'PASS' if ok else 'FAIL'}  raw {a.raw.strip()!r}{detail}"
                  + (f"  [{a.error}]" if a.error else ""))
            total += 1
            passed += ok
    print(f"\n{passed}/{total} passed")


if __name__ == "__main__":
    main()

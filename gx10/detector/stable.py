"""Holds YOLO's answers steady from frame to frame.

YOLO judges each frame on its own, so an object near the confidence line blinks on
and off. This follows each object across frames (same label, overlapping box) and:
- shows it once it is seen in NEED of the last WINDOW frames with confidence SHOW or more,
- keeps showing it through a missed frame or a dip down to KEEP,
- hides it once it is missing from most of the last WINDOW frames.

On a recorded walk through a house (320 frames) label changes per frame went from
0.34 to 0.09 with these numbers. Standard library only; a few microseconds a frame.
"""

from collections import deque

from .detector import Detection

SHOW = 0.4  # confidence an object needs before it is first shown
KEEP = 0.25  # once shown, kept down to this confidence; YOLO runs at this threshold
SHOW_OPEN = 0.3  # the same for YOLOE's hazards, whose scores run lower (it runs at 0.2)
NEED, WINDOW = 3, 5  # seen in 3 of the last 5 frames to appear
DROP = 1  # hidden once seen in this many or fewer of the last 5
MATCH_IOU = 0.3  # boxes overlapping this much are the same object
FOLLOW = 0.6  # how far the shown box moves toward the new one each frame (1 = no smoothing)


def iou(a, b) -> float:
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    if w <= 0 or h <= 0:
        return 0.0
    inter = w * h
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter)


class _Track:
    def __init__(self, d: Detection):
        self.label, self.conf, self.box, self.source = d.label, d.conf, [float(v) for v in d.box], d.source
        self.show = SHOW if d.source == "yolo" else SHOW_OPEN
        self.best = d.conf
        self.hits = deque([True], maxlen=WINDOW)
        self.shown = False

    def see(self, d: Detection):
        self.box = [b + FOLLOW * (n - b) for b, n in zip(self.box, d.box)]
        self.conf = d.conf
        self.best = max(self.best, d.conf)
        self.hits.append(True)

    def miss(self):
        self.hits.append(False)


class Stabilizer:
    def __init__(self):
        self.tracks = []

    def reset(self):
        self.tracks = []

    def update(self, dets) -> list:
        """dets: this frame's Detections (YOLO run at KEEP). Returns the steady ones, as new
        Detection objects, so callers can change them without touching the tracks."""
        pairs = sorted(((iou(t.box, d.box), ti, di) for ti, t in enumerate(self.tracks)
                        for di, d in enumerate(dets) if t.label == d.label), reverse=True)
        used_t, used_d = set(), set()
        for overlap, ti, di in pairs:
            if overlap < MATCH_IOU:
                break
            if ti in used_t or di in used_d:
                continue
            used_t.add(ti), used_d.add(di)
            self.tracks[ti].see(dets[di])
        for ti, t in enumerate(self.tracks):
            if ti not in used_t:
                t.miss()
        self.tracks += [_Track(d) for di, d in enumerate(dets) if di not in used_d]

        out, keep = [], []
        for t in self.tracks:
            seen = sum(t.hits)
            if seen == 0:
                continue  # gone for a whole window: forget it
            keep.append(t)
            if not t.shown and seen >= NEED and t.best >= t.show:
                t.shown = True
            elif t.shown and seen <= DROP:
                t.shown = False
            if t.shown:
                out.append(Detection(t.label, round(t.conf, 3), [round(v) for v in t.box], t.source))
        self.tracks = keep
        return out

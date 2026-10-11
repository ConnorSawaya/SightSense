"""The dashboard's obstacle view: what the LiDAR obstacle check saw, pixel by pixel.

Drawn from the maps planner/obstacle.py returns with want_maps=True. For people
watching only; the wheel is decided in planner/obstacle.py, not here.

    green     floor
    red       obstacle nearer than STOP_AHEAD_M (0.8 m)
    amber     obstacle up to USABLE_M (1.5 m; a heading needs this much to be usable)
    yellow    obstacle farther than that
    magenta   nearer than 0.3 m: too close to measure, counted as blocked
    dark blue no good reading: unknown, counted as blocked
    grey      good reading beyond range, or above the cane (darker = farther)

Thin lines split the seven 10-degree headings; each is labelled with its
clearance. The side the wheel is turning to (or the side being held in manual
steering) stays bright, the rest is dimmed, and the obstacle points inside its
corridors are outlined.
"""

import cv2
import numpy as np

from planner.obstacle import (HEADINGS, MAP_FLOOR, MAP_NO_READING, MAP_OBSTACLE, MAP_TOO_CLOSE, STOP_AHEAD_M,
                              USABLE_M, FAR_M)

SIDES = {"LEFT": (-30, -20), "CENTER": (-10, 0, 10), "RIGHT": (20, 30)}
ARROW = {"LEFT": "<<", "RIGHT": ">>", "CENTER": "^", "STOP": "X", "FREE": "-"}
FONT = cv2.FONT_HERSHEY_SIMPLEX  # ASCII only: no arrows or degree signs
WHITE, BLACK = (255, 255, 255), (20, 20, 20)
NEAR_C, MID_C, FAR_C = (60, 60, 235), (40, 170, 250), (70, 220, 230)
FLOOR_C, CLOSE_C, NONE_C = (70, 170, 60), (220, 70, 220), (110, 50, 40)  # no reading: dark blue, not grey
_CV = {1: cv2.ROTATE_90_CLOCKWISE, 2: cv2.ROTATE_180, 3: cv2.ROTATE_90_COUNTERCLOCKWISE}


def _up(a, turn):
    return cv2.rotate(a, _CV[turn]) if turn else a


def focus_of(view, manual):
    """(headings to highlight, what is happening, manual or not)."""
    if manual in SIDES:
        return SIDES[manual], manual, True
    if manual in ("STOP", "FREE"):
        return (), manual, True
    cmd, best = view.get("cmd"), view.get("best")
    if cmd == "STOP" or cmd is None:
        return (0,), "STOP", False
    if best is not None and best in SIDES.get(cmd, ()):
        return (best,), cmd, False
    return SIDES.get(cmd, ()), cmd, False


def _metres(v):
    return "?" if v is None else "clear" if v >= FAR_M else f"{v:.1f}m"


def banner(view, manual):
    """One line saying why the wheel does what it does."""
    heads, what, by_hand = focus_of(view, manual)
    cl = view.get("clearance") or {}
    if what in ("STOP", "FREE") and by_hand:
        return f"{ARROW[what]} {what} (manual)"
    if what == "STOP":
        ahead = cl.get(0)
        return f"X STOP: no heading clear for {USABLE_M:g} m  (ahead {_metres(ahead)})"
    parts = [f"{h:+d}: {_metres(cl.get(h))}" for h in heads]
    open_ = [h for h in heads if cl.get(h) is not None and cl[h] >= USABLE_M]
    verdict = ("open" if open_ else "blocked") if by_hand else ""
    near = _objects_in(view, heads)
    return (f"{ARROW.get(what, '')} {what}{' (manual)' if by_hand else ''}  " + "  ".join(parts)
            + (f"  - {verdict}" if verdict else "") + (f"  - {near}" if near else ""))


def _objects_in(view, heads):
    """Named objects (YOLO / YOLOE) whose direction falls in the highlighted headings."""
    found = []
    for d in view.get("dets") or []:
        b, m = getattr(d, "bearing", None), getattr(d, "dist_m", None)
        if b is not None and any(abs(b - h) <= 5 for h in heads):
            found.append((m if m is not None else 99, f"{d.label} {m:.1f}m" if m is not None else d.label))
    return ", ".join(t for _, t in sorted(found)[:2])


def draw(view, out_h: int, manual=None):
    """BGR picture, out_h pixels high, upright like the camera picture. None if no maps."""
    maps = view.get("maps")
    if maps is None:
        return None
    kind, heading, corridor, along = maps["kind"], maps["heading"], maps["corridor"], maps["along"]
    depth = view["depth"]
    heads, _, _ = focus_of(view, manual)
    idx = [HEADINGS.index(h) for h in heads]

    # Colour at depth resolution: dim grey depth underneath, classes on top
    base = (215 - np.clip(depth.astype(np.float32) / 5000.0, 0, 1) * 115).astype(np.uint8)
    img = np.repeat(base[..., None], 3, 2)
    img[kind == MAP_NO_READING] = NONE_C
    floor = kind == MAP_FLOOR
    img[floor] = (0.55 * img[floor] + 0.45 * np.array(FLOOR_C)).astype(np.uint8)
    ob = kind == MAP_OBSTACLE
    col = np.where((along < STOP_AHEAD_M)[..., None], NEAR_C, np.where((along < USABLE_M)[..., None], MID_C, FAR_C))
    img[ob] = col[ob]
    img[kind == MAP_TOO_CLOSE] = CLOSE_C
    focus = np.isin(heading, idx) if idx else np.zeros_like(ob)
    if idx:
        img[~focus] = (img[~focus] * 0.45).astype(np.uint8)
    bits = np.uint8(sum(1 << i for i in idx))
    hit = ob & ((corridor & bits) > 0)

    # Upright, then scale up; lines and text are drawn at full size so they stay sharp
    img, heading_u, hit_u = _up(img, view["turn"]), _up(heading, view["turn"]), _up(hit.astype(np.uint8), view["turn"])
    w = round(img.shape[1] * out_h / img.shape[0])
    img = cv2.resize(img, (w, out_h), interpolation=cv2.INTER_NEAREST)
    hm = cv2.resize(heading_u, (w, out_h), interpolation=cv2.INTER_NEAREST)
    hit_big = cv2.resize(hit_u, (w, out_h), interpolation=cv2.INTER_NEAREST)

    edge = np.zeros(hm.shape, bool)
    edge[:, 1:] |= hm[:, 1:] != hm[:, :-1]
    edge[1:, :] |= hm[1:, :] != hm[:-1, :]
    img[edge] = (0.4 * img[edge] + 0.6 * np.array(WHITE)).astype(np.uint8)
    contours, _ = cv2.findContours(hit_big, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(img, contours, -1, WHITE, 2, cv2.LINE_AA)

    text = banner(view, manual)
    scale = max(0.45, min(0.7, w / 900))
    (tw, th), _ = cv2.getTextSize(text, FONT, scale, 1)
    while tw > w - 16 and scale > 0.32:  # long lines shrink to fit rather than run off the edge
        scale -= 0.03
        (tw, th), _ = cv2.getTextSize(text, FONT, scale, 1)
    cv2.rectangle(img, (0, 0), (w, th + 14), BLACK, -1)
    cv2.putText(img, text, (8, th + 6), FONT, scale, WHITE, 1, cv2.LINE_AA)

    cl = view.get("clearance") or {}
    ys = th + 36
    for i, h in enumerate(HEADINGS):
        xs = np.nonzero(hm[ys] == i)[0] if ys < out_h else []
        if not len(xs):
            continue
        v = cl.get(h)
        label = "?" if v is None else f"{v:.1f}"
        c = NONE_C if v is None else (70, 200, 90) if v >= USABLE_M else MID_C if v >= STOP_AHEAD_M else NEAR_C
        (lw, lh), _ = cv2.getTextSize(label, FONT, scale, 1)
        x = int(xs.mean()) - lw // 2
        cv2.rectangle(img, (x - 4, ys - lh - 4), (x + lw + 4, ys + 4), BLACK, -1)
        cv2.putText(img, label, (x, ys), FONT, max(scale, 0.45), c if v is not None else (180, 180, 180), 1, cv2.LINE_AA)
    return img

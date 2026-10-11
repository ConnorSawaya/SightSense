"""Obstacle check over seven headings, from LiDAR depth only (AGENTS.md, "Obstacle check").

Every number is a starting value to tune, not a measured result. Unknown counts
as blocked. Headings are measured in the floor plane from where the camera
points, positive to the user's right, so the phone's direction in its mount does
not matter (same convention as gx10/navigator).
"""

import os
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

HEADINGS = (-30, -20, -10, 0, 10, 20, 30)
# Keep depth readings in this range. FAR_M was 4.5. The LiDAR itself reaches about 5 m, but ARKit fills in
# farther depth from the camera: in the house recording of October 10, 5% of pixels read 5-8 m at medium or
# high confidence; beyond 8 m nearly all were low confidence, which is dropped below. So 10 m lets big rooms
# show their real far side; it does not change USABLE_M or STOP_AHEAD_M, which steer the wheel.
NEAR_M = 0.3
FAR_M = float(os.environ.get("SIGHTSENSE_FAR_M", "10"))
FLOOR_MARGIN_M = 0.15  # points lower than this above the floor are floor
ABOVE_CAMERA_M = 0.6  # points higher than this above the camera are ignored
CORRIDOR_W_M = 0.7
MIN_POINTS = 30  # fewer obstacle points than this in a corridor: clear to range
MIN_VALID = 0.6  # fewer good depth pixels than this in a heading's wedge: unknown (blocked)
MIN_WEDGE_PX = 150  # a wedge the camera barely sees is unknown too (estimate, to tune)
TOO_CLOSE_SHARE = 0.2  # this share of a wedge reading nearer than NEAR_M: blocked at 0 m
# Distances are from the phone. Was 2.5 m and 1.2 m; on October 10 that stopped about 2.2 m
# from things, which the team found too cautious for a cane whose tip is already ahead of the user.
USABLE_M = 1.5
# Nothing usable but some heading open past STOP_AHEAD_M: steer slowly that way instead of
# stopping. Once stopped, a heading must be open past LEAVE_STOP_M to go again, so it does
# not flip in and out of STOP. On the October 10 evening walk (indoors, 15 min) STOP fell
# from 51% to 28% of the time; what still stopped was about 0.3 m away (median).
STOP_AHEAD_M = 0.8
LEAVE_STOP_M = 1.0
CAMERA_HEIGHT_M = 0.9  # used only when the floor cannot be seen (estimate for a cane handle)
CHANGE_FRAMES, STOP_FRAMES = 3, 2
# The cane's own lower end (motor, wheel, Pi clamp) can show at the bottom of the picture once the
# phone is on the cane, and it then reads as an obstacle about 0.4 m ahead for ever. Set this to the
# distance along the floor from the phone to the cane's tip (about 0.65) to ignore a strip that long
# and 24 cm wide straight ahead. Off by default: with nothing of the cane in view it would only
# hide a thin post nearer than the tip. It is kept under STOP_AHEAD_M.
OWN_CANE_M = float(os.environ.get("SIGHTSENSE_OWN_CANE_M", "0"))
OWN_CANE_HALF_W_M = 0.12
STUCK_S = 5.0


@dataclass
class Check:
    clearance: dict  # heading -> metres, or None when unknown
    usable: list
    best: Optional[int]  # chosen heading this frame, None = nothing usable
    raw_cmd: str  # this frame's command before smoothing
    floor_seen: bool
    points: int
    cam_h: Optional[float] = None  # how far the phone is above the floor it found; None when no floor was seen
    maps: Optional[dict] = None  # per depth pixel, for the dashboard only; see MAP_* below


# maps["kind"]: what each depth pixel is, as the check saw it (MAP_NONE: above the cane, or the cane itself)
MAP_NONE, MAP_FLOOR, MAP_OBSTACLE, MAP_TOO_CLOSE, MAP_NO_READING, MAP_OUT = 0, 1, 2, 3, 4, 5
# maps["heading"]: index into HEADINGS of the 10-degree wedge a pixel looks along, or -1
# maps["corridor"]: bit i set if the pixel is an obstacle inside heading i's 0.7 m corridor
# maps["along"]: metres from the phone along the floor, for obstacle pixels (0 elsewhere)


def check(depth_mm: np.ndarray, conf: np.ndarray, fx, fy, cx, cy, pose, desired: float = 0.0, last: float = 0.0,
          stopped: bool = False, own_cane_m: Optional[float] = None, want_maps: bool = False) -> Check:
    """One frame. depth_mm and conf are (h, w) arrays; pose is 16 numbers, column by column.
    stopped: the smoothed command is STOP now (going again needs LEAVE_STOP_M).
    own_cane_m: see OWN_CANE_M; None means use that setting.
    want_maps: also return per-pixel maps for the dashboard (about 0.5 ms more); the decision does not use them."""
    h, w = depth_mm.shape
    M = np.asarray(pose, dtype=np.float64).reshape(4, 4).T  # column by column -> matrix
    R, t = M[:3, :3], M[:3, 3]

    # Ray of every pixel, in the world, flattened onto the floor
    u = np.arange(w, dtype=np.float64)[None, :].repeat(h, 0)
    v = np.arange(h, dtype=np.float64)[:, None].repeat(w, 1)
    rays_cam = np.stack([(u - cx) / fx, -(v - cy) / fy, -np.ones_like(u)], -1)
    rays = rays_cam @ R.T  # world direction of each pixel
    fwd = -R[:, 2]
    f2 = np.array([fwd[0], fwd[2]])
    if np.linalg.norm(f2) < 1e-6:  # camera pointing straight up or down
        return _nothing(raw_cmd="STOP")  # no maps: the dashboard shows depth only
    f2 /= np.linalg.norm(f2)
    r2 = np.array([-f2[1], f2[0]])  # forward turned 90 degrees clockwise seen from above
    ray_b = np.degrees(np.arctan2(rays[..., 0] * r2[0] + rays[..., 2] * r2[1], rays[..., 0] * f2[0] + rays[..., 2] * f2[1]))

    z = depth_mm.astype(np.float64) / 1000.0
    good = (conf >= 1) & (depth_mm > 0)
    keep = good & (z >= NEAR_M) & (z <= FAR_M)
    too_close = good & (z < NEAR_M)  # dropped from the points, but it is not open space

    # Points in the world (z is the distance along the camera's view axis)
    p = rays[keep] * z[keep][:, None] + t
    cam_y = t[1]

    # Floor: the 5th percentile height of points within 3 m, if it looks like a floor
    floor_y, floor_seen = cam_y - CAMERA_HEIGHT_M, False
    if len(p):
        near = p[np.hypot(p[:, 0] - t[0], p[:, 2] - t[2]) < 3.0]
        if len(near) > 200:
            guess = np.percentile(near[:, 1], 5)
            if cam_y - 1.6 <= guess <= cam_y - 0.3:
                floor_y, floor_seen = guess, True
    is_obst = (p[:, 1] > floor_y + FLOOR_MARGIN_M) & (p[:, 1] < cam_y + ABOVE_CAMERA_M)
    obst = p[is_obst]
    obst_px = np.flatnonzero(keep)[is_obst]  # depth pixel of each obstacle point, for the maps

    # Obstacle points in the user's floor frame: a = metres right, b = metres ahead
    d = obst[:, [0, 2]] - t[[0, 2]]
    a, b = d @ r2, d @ f2
    own = OWN_CANE_M if own_cane_m is None else own_cane_m
    if own > 0:  # the cane itself, not something in the way
        mine = (np.abs(a) <= OWN_CANE_HALF_W_M) & (b <= min(own, STOP_AHEAD_M - 0.05))
        a, b = a[~mine], b[~mine]
        obst_px = obst_px[~mine]

    corridor = np.zeros(len(a), np.uint8)
    clearance, usable = {}, []
    for i, hd in enumerate(HEADINGS):
        wedge = np.abs(ray_b - hd) <= 5.0
        n = int(wedge.sum())
        if n < MIN_WEDGE_PX or good[wedge].mean() < MIN_VALID:
            clearance[hd] = None  # unknown counts as blocked
            continue
        if too_close[wedge].mean() > TOO_CLOSE_SHARE:
            clearance[hd] = 0.0  # right up against something
            continue
        s, c = np.sin(np.radians(hd)), np.cos(np.radians(hd))
        along, side = a * s + b * c, a * c - b * s
        inside = (np.abs(side) <= CORRIDOR_W_M / 2) & (along > 0)
        corridor[inside] |= np.uint8(1 << i)
        clearance[hd] = float(np.percentile(along[inside], 5)) if inside.sum() >= MIN_POINTS else FAR_M
        if clearance[hd] >= USABLE_M:
            usable.append(hd)

    best = min(usable, key=lambda hd: abs(hd - desired) + 0.5 * abs(hd - last)) if usable else None
    if best is None:  # nothing usable: the most open heading, if it is open far enough
        known = {hd: v for hd, v in clearance.items() if v is not None}
        if known:
            hd = max(known, key=lambda k: (known[k], -abs(k - desired)))
            if known[hd] >= (LEAVE_STOP_M if stopped else STOP_AHEAD_M):
                best = hd
    maps = _maps(h, w, good, keep, too_close, p, floor_y, ray_b, obst_px, corridor, a, b) if want_maps else None
    return Check(clearance, usable, best, wheel(best), floor_seen, len(a), float(cam_y - floor_y) if floor_seen else None,
                 maps)


def _maps(h, w, good, keep, too_close, p, floor_y, ray_b, obst_px, corridor, a, b):
    """What the check saw, pixel by pixel. Drawing only; the decision above does not use it."""
    kind = np.full(h * w, MAP_OUT, np.uint8)  # good reading beyond range
    kind[~good.ravel()] = MAP_NO_READING
    kind[too_close.ravel()] = MAP_TOO_CLOSE
    flat = np.flatnonzero(keep)
    kind[flat] = np.where(p[:, 1] <= floor_y + FLOOR_MARGIN_M, MAP_FLOOR, MAP_NONE)
    kind[obst_px] = MAP_OBSTACLE  # after the cane's own end is taken out
    corr = np.zeros(h * w, np.uint8)
    corr[obst_px] = corridor
    along = np.zeros(h * w, np.float32)
    along[obst_px] = np.hypot(a, b)
    idx = np.rint((ray_b - HEADINGS[0]) / 10.0)
    heading = np.where((idx >= 0) & (idx < len(HEADINGS)) & (np.abs(ray_b - (HEADINGS[0] + 10 * idx)) <= 5.0), idx, -1)
    return {"kind": kind.reshape(h, w), "heading": heading.astype(np.int8), "corridor": corr.reshape(h, w),
            "along": along.reshape(h, w)}


def wheel(heading: Optional[float]) -> str:
    if heading is None:
        return "STOP"
    return "LEFT" if heading <= -15 else "RIGHT" if heading >= 15 else "CENTER"


def _nothing(raw_cmd):
    return Check({hd: None for hd in HEADINGS}, [], None, raw_cmd, False, 0)


@dataclass
class Smoother:
    """A change needs 3 agreeing frames; STOP needs 2. STOP for 5 s asks the user to scan."""

    cmd: str = "STOP"  # start stopped until the depth says otherwise
    _cand: str = ""
    _count: int = 0
    _stop_since: Optional[float] = None
    _stuck_said: bool = False
    last_heading: float = 0.0

    def update(self, raw: str, heading: Optional[float], now: float):
        """Returns (command, speech or None)."""
        speech = None
        if raw == self.cmd:
            self._cand, self._count = "", 0
        else:
            self._count = self._count + 1 if raw == self._cand else 1
            self._cand = raw
            if self._count >= (STOP_FRAMES if raw == "STOP" else CHANGE_FRAMES):
                if raw == "STOP":
                    speech = "Obstacle ahead. Stop."
                self.cmd, self._cand, self._count = raw, "", 0
        if self.cmd == "STOP":
            self._stop_since = self._stop_since if self._stop_since is not None else now
            if now - self._stop_since >= STUCK_S and not self._stuck_said:
                self._stuck_said, speech = True, "Path blocked. Turn slowly to scan."
        else:
            self._stop_since, self._stuck_said = None, False
            if heading is not None:
                self.last_heading = heading
        return self.cmd, speech

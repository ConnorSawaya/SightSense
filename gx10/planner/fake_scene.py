"""Fake depth frames of a simple scene: a floor at height 0 and box-shaped obstacles.

Ray-cast with numpy, so the obstacle check can be tested on known geometry
without the phone. Uses the navigator's Frame and camera pose helpers.
"""

import numpy as np

from navigator import fake
from navigator.frame import Frame


def render(pose, boxes=(), far_m=8.0, jpeg=b"", seq=0, t=0.0, glass=()):
    """boxes and glass: ((xmin, ymin, zmin), (xmax, ymax, zmax)) in world metres, y up.

    Glass boxes stop the ray but give no reading (depth 0, low confidence), like real glass.
    """
    w, h = fake.DEPTH_W, fake.DEPTH_H
    M = np.asarray(pose, dtype=np.float64).reshape(4, 4).T
    R, o = M[:3, :3], M[:3, 3]
    u = np.arange(w)[None, :].repeat(h, 0)
    v = np.arange(h)[:, None].repeat(w, 1)
    rays = np.stack([(u - fake.CX) / fake.FX, -(v - fake.CY) / fake.FY, -np.ones((h, w))], -1) @ R.T
    # ray parameter = distance along the view axis, since the camera-frame rays have z = -1
    with np.errstate(divide="ignore", invalid="ignore"):
        solid = np.where(rays[..., 1] < 0, -o[1] / rays[..., 1], np.inf)  # the floor
    for lo, hi in boxes:
        solid = np.minimum(solid, _slab(o, rays, np.array(lo, float), np.array(hi, float)))
    clear = np.full((h, w), np.inf)
    for lo, hi in glass:
        clear = np.minimum(clear, _slab(o, rays, np.array(lo, float), np.array(hi, float)))
    hit_glass = clear < solid
    depth = np.where(np.isfinite(solid) & (solid <= far_m) & ~hit_glass, solid * 1000, 0).astype(np.uint16)
    conf = np.where(depth > 0, 2, 0).astype(np.uint8)
    return Frame(seq=seq, t_capture=t, rgb_w=fake.RGB_W, rgb_h=fake.RGB_H, depth_w=w, depth_h=h,
                 fx=fake.FX, fy=fake.FY, cx=fake.CX, cy=fake.CY, pose=list(pose), jpeg=jpeg,
                 depth_mm=depth.ravel(), conf=conf.tobytes())


def _slab(o, rays, lo, hi):
    with np.errstate(divide="ignore", invalid="ignore"):
        t1 = (lo - o) / rays
        t2 = (hi - o) / rays
    tmin = np.nanmax(np.minimum(t1, t2), -1)
    tmax = np.nanmin(np.maximum(t1, t2), -1)
    return np.where((tmax >= np.maximum(tmin, 0)) & (tmax > 0), np.maximum(tmin, 0), np.inf)


def arrays(f: Frame):
    return (np.asarray(f.depth_mm, dtype=np.uint16).reshape(f.depth_h, f.depth_w),
            np.frombuffer(f.conf, np.uint8).reshape(f.depth_h, f.depth_w))

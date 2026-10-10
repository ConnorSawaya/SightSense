"""The phone's frame message (contracts/MESSAGES.md) and the geometry the navigator needs.

decode() and encode() follow the frame layout exactly, so the navigator can be
tested on fake frames. The frame receiver in ingest/ can hand over a Frame, or
any object with the same fields.

Camera conventions are ARKit's: in the camera frame x points right along the
picture's width, y up, and the camera looks down -z. The picture and depth come
in the sensor's own direction, the same one the pose uses. Bearings are worked
out in the room's floor plane (ground_bearing), so "left" means the user's left
however the phone sits in its mount.
"""

import json
import math
import struct
import sys
from array import array
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Frame:
    seq: int
    t_capture: float
    rgb_w: int
    rgb_h: int
    depth_w: int
    depth_h: int
    fx: float  # intrinsics scaled to the depth picture's size
    fy: float
    cx: float
    cy: float
    pose: list  # camera-to-world, 16 numbers, column by column, metres
    jpeg: bytes = b""
    depth_mm: array = field(default_factory=lambda: array("H"))  # row by row
    conf: bytes = b""  # 0 low, 1 medium, 2 high
    tracking: str = "normal"
    lat: Optional[float] = None
    lon: Optional[float] = None
    gps_acc_m: Optional[float] = None
    heading_deg: Optional[float] = None
    thermal: str = "nominal"


def decode(msg: bytes) -> Frame:
    (hlen,) = struct.unpack_from("<I", msg, 0)
    h = json.loads(msg[4 : 4 + hlen])
    i = 4 + hlen
    jpeg = msg[i : i + h["jpeg_len"]]
    i += h["jpeg_len"]
    depth = array("H")
    depth.frombytes(msg[i : i + h["depth_len"]])
    if sys.byteorder == "big":
        depth.byteswap()
    i += h["depth_len"]
    conf = msg[i : i + h["conf_len"]]
    if len(depth) != h["depth_w"] * h["depth_h"] or len(conf) != len(depth):
        raise ValueError(f"frame {h.get('seq')}: depth or confidence size does not match depth_w x depth_h")
    names = Frame.__dataclass_fields__
    return Frame(jpeg=jpeg, depth_mm=depth, conf=conf, **{k: v for k, v in h.items() if k in names})


def encode(f: Frame) -> bytes:
    depth = array("H", f.depth_mm)
    if sys.byteorder == "big":
        depth.byteswap()
    d = depth.tobytes()
    h = {k: getattr(f, k) for k in Frame.__dataclass_fields__ if k not in ("jpeg", "depth_mm", "conf")}
    h.update(jpeg_len=len(f.jpeg), depth_len=len(d), conf_len=len(f.conf))
    hb = json.dumps(h).encode()
    return struct.pack("<I", len(hb)) + hb + f.jpeg + d + bytes(f.conf)


# ---------------------------------------------------------------- depth


def box_distance(f: Frame, box_rgb, min_conf: int = 1, near_m: float = 0.2, far_m: float = 5.0):
    """Median LiDAR distance (metres) inside the middle half of a box given in picture pixels.

    Returns (distance_m, u, v) with (u, v) the box centre in depth pixels, or
    (None, u, v) if fewer than 5 good readings. Only the middle half of the box is
    used, because objects are not rectangles and the corners are often background.
    """
    sx, sy = f.depth_w / f.rgb_w, f.depth_h / f.rgb_h
    x1, y1, x2, y2 = box_rgb[0] * sx, box_rgb[1] * sy, box_rgb[2] * sx, box_rgb[3] * sy
    u, v = (x1 + x2) / 2, (y1 + y2) / 2
    hw, hh = max((x2 - x1) / 4, 0.5), max((y2 - y1) / 4, 0.5)
    good = []
    for row in range(max(0, int(v - hh)), min(f.depth_h, int(math.ceil(v + hh)))):
        base = row * f.depth_w
        for col in range(max(0, int(u - hw)), min(f.depth_w, int(math.ceil(u + hw)))):
            i = base + col
            z = f.depth_mm[i] / 1000
            if f.conf[i] >= min_conf and near_m <= z <= far_m:
                good.append(z)
    if len(good) < 5:
        return None, u, v
    good.sort()
    return good[len(good) // 2], u, v


# ---------------------------------------------------------------- pose maths


def pixel_to_camera(f: Frame, u: float, v: float, z: float):
    """Depth pixel and distance -> point in the ARKit camera frame (metres)."""
    return ((u - f.cx) * z / f.fx, -(v - f.cy) * z / f.fy, -z)


def camera_to_world(pose, p):
    x, y, z = p
    return tuple(pose[r] * x + pose[4 + r] * y + pose[8 + r] * z + pose[12 + r] for r in range(3))


def world_to_camera(pose, p):
    d = [p[r] - pose[12 + r] for r in range(3)]
    # inverse of a rotation is its transpose: camera axis c is column c of the pose
    return tuple(sum(pose[c * 4 + r] * d[r] for r in range(3)) for c in range(3))


def camera_position(pose):
    return (pose[12], pose[13], pose[14])


def ground_bearing(pose, p_world) -> Optional[float]:
    """Bearing of a world point from the camera, in the floor plane, in degrees.

    0 is where the camera points (flattened onto the floor), positive is to the
    user's right. Worked out in the world frame, so it does not depend on how
    the phone is turned in its mount or how far the cane is tilted down.
    None if the camera points straight up or down.
    """
    fx, fz = -pose[8], -pose[10]  # camera forward is -z, the pose's third column
    if math.hypot(fx, fz) < 1e-6:
        return None
    rx, rz = -fz, fx  # forward turned 90 degrees clockwise seen from above (world y is up)
    dx, dz = p_world[0] - pose[12], p_world[2] - pose[14]
    return math.degrees(math.atan2(dx * rx + dz * rz, dx * fx + dz * fz))


def ground_distance(a, b) -> float:
    """Distance ignoring height (ARKit's world y is up)."""
    return math.hypot(a[0] - b[0], a[2] - b[2])

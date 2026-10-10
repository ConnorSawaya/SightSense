"""A fake room for testing without the phone: camera poses, depth frames and a fake find().

The room has a wall all round at a fixed distance and one object (a ball of
some radius) at a known world point. Depth is rendered for that, so
box_distance and the guide can be checked against the true answer.
"""

import json
import math
from array import array
from dataclasses import dataclass

from .frame import Frame, world_to_camera

# The example intrinsics in contracts/MESSAGES.md
DEPTH_W, DEPTH_H, FX, FY, CX, CY = 256, 192, 212.4, 212.4, 127.6, 95.8
RGB_W, RGB_H = 640, 480


def pose(x=0.0, z=0.0, yaw_deg=0.0, pitch_deg=-20.0, roll_deg=0.0, height=1.0):
    """Camera-to-world, column by column. yaw > 0 turns left (ARKit: y up, camera looks down -z).

    pitch < 0 looks down, like a phone on a cane. roll 90 turns the phone on its side
    in the mount, which changes the picture's direction but not the room.
    """
    cy, sy = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    cp, sp = math.cos(math.radians(pitch_deg)), math.sin(math.radians(pitch_deg))
    cr, sr = math.cos(math.radians(roll_deg)), math.sin(math.radians(roll_deg))
    ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    rx = [[1, 0, 0], [0, cp, -sp], [0, sp, cp]]
    rz = [[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]]
    m = _mul(_mul(ry, rx), rz)
    t = (x, height, z)
    cols = [[m[0][c], m[1][c], m[2][c], 0.0] for c in range(3)] + [[t[0], t[1], t[2], 1.0]]
    return [v for col in cols for v in col]


def _mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def project(p_pose, p_world, w=DEPTH_W, h=DEPTH_H):
    """World point -> (u, v, distance) in a picture of size w x h, or None if behind the camera."""
    s = w / DEPTH_W
    x, y, z = world_to_camera(p_pose, p_world)
    if -z < 0.05:
        return None
    return CX * s + FX * s * x / -z, CY * s - FY * s * y / -z, -z


def frame(p_pose, obj=None, radius=0.05, wall_m=4.0, seq=0, t=0.0, tracking="normal",
          lat=None, lon=None, gps_acc_m=None, heading_deg=None):
    """A frame seeing a flat wall at wall_m and, if obj is given, a ball of `radius` at that world point."""
    depth = array("H", [int(wall_m * 1000)]) * (DEPTH_W * DEPTH_H)
    conf = bytearray([2]) * (DEPTH_W * DEPTH_H)
    if obj is not None:
        pr = project(p_pose, obj)
        if pr is not None:
            u0, v0, d = pr
            r_px = max(1.0, FX * radius / d)
            for v in range(max(0, int(v0 - r_px)), min(DEPTH_H, int(v0 + r_px) + 1)):
                for u in range(max(0, int(u0 - r_px)), min(DEPTH_W, int(u0 + r_px) + 1)):
                    if (u - u0) ** 2 + (v - v0) ** 2 <= r_px**2:
                        depth[v * DEPTH_W + u] = int(d * 1000)
    jpeg = b"FAKE" + json.dumps(p_pose).encode()  # FakeFinder reads the pose back from the "picture"
    return Frame(seq=seq, t_capture=t, rgb_w=RGB_W, rgb_h=RGB_H, depth_w=DEPTH_W, depth_h=DEPTH_H,
                 fx=FX, fy=FY, cx=CX, cy=CY, pose=p_pose, jpeg=jpeg, depth_mm=depth, conf=bytes(conf),
                 tracking=tracking, lat=lat, lon=lon, gps_acc_m=gps_acc_m, heading_deg=heading_deg)


@dataclass
class FakeAnswer:
    ok: bool
    text: str
    box: list = None


class FakeFinder:
    """Stands in for vlm.find on fake frames. Knows where the object is and whether the camera sees it."""

    def __init__(self, obj, radius=0.05):
        self.obj, self.radius, self.calls, self.fail = obj, radius, 0, False

    def __call__(self, jpeg, name):
        self.calls += 1
        if self.fail:
            return FakeAnswer(False, "I couldn't tell")
        p_pose = json.loads(jpeg[4:])
        pr = project(p_pose, self.obj, RGB_W, RGB_H) if self.obj else None
        if pr is None:
            return FakeAnswer(True, f"I don't see the {name}.")
        u, v, d = pr
        r = FX * (RGB_W / DEPTH_W) * self.radius / d
        if not (0 <= u < RGB_W and 0 <= v < RGB_H):
            return FakeAnswer(True, f"I don't see the {name}.")
        return FakeAnswer(True, f"I see the {name}.", [round(u - r), round(v - r), round(u + r), round(v + r)])

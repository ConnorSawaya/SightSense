"""Renders the review views of the handle and pole-mounted camera mount into previews/.

Run after walking_stick.py:  python preview.py     (needs numpy and matplotlib)
Reference geometry (phone, stick, hand envelope, screws, strap, camera view)
is drawn here only; it is never exported for printing.
"""

from math import cos, radians, sin
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc

import walking_stick as ws
from walking_stick import Pos, Rot, box

OUT = Path(__file__).parent / "previews"
COLORS = {
    "handle": (0.20, 0.47, 0.80),
    "collar": (0.95, 0.55, 0.15),
    "cradle": (0.25, 0.68, 0.45),
    "phone": (0.22, 0.22, 0.25),
    "stick": (0.45, 0.45, 0.48),
    "hardware": (0.82, 0.80, 0.72),
    "strap": (0.75, 0.25, 0.30),
    "hand": (0.95, 0.75, 0.60),
    "view": (1.00, 0.85, 0.20),
    "bed": (0.86, 0.86, 0.88),
    "motor": (0.55, 0.40, 0.75),
}
T = ws.PHONE_TILT_DEG


def item(shape, color, alpha=1.0):
    shapes = shape if isinstance(shape, (list, tuple)) else [shape]
    tris = []
    for s in shapes:
        verts, faces = s.tessellate(0.06, 0.25)
        v = np.array([(p.X, p.Y, p.Z) for p in verts])
        tris.append(v[np.array(faces)])
    return np.concatenate(tris), np.array(COLORS[color]), alpha


def basis(eye, up=(0, 0, 1)):
    eye = np.array(eye, float) / np.linalg.norm(eye)
    right = np.cross(up, eye)
    right /= np.linalg.norm(right)
    return right, np.cross(eye, right), eye


def raster(tris, color, cam, origin, scale, shape):
    """Flat-shaded z-buffer pass for one item. Returns colour, depth and normal buffers."""
    right, up, eye = cam
    h, w = shape
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    length = np.linalg.norm(n, axis=1)
    keep = length > 1e-9
    tris, n = tris[keep], n[keep] / length[keep][:, None]
    light = eye + 0.45 * right + 0.7 * up
    shade = 0.38 + 0.62 * np.abs(n @ (light / np.linalg.norm(light)))
    px = (tris @ right - origin[0]) * scale
    py = (origin[1] - tris @ up) * scale
    pz = tris @ eye
    rgb = np.ones((h, w, 3))
    depth = np.full((h, w), -np.inf)
    normal = np.zeros((h, w, 3))
    for i in range(len(tris)):
        x, y, z = px[i], py[i], pz[i]
        x0, x1 = max(int(x.min()), 0), min(int(x.max()) + 1, w - 1)
        y0, y1 = max(int(y.min()), 0), min(int(y.max()) + 1, h - 1)
        if x0 > x1 or y0 > y1:
            continue
        area = (x[1] - x[0]) * (y[2] - y[0]) - (x[2] - x[0]) * (y[1] - y[0])
        if abs(area) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        b0 = ((x[1] - gx) * (y[2] - gy) - (x[2] - gx) * (y[1] - gy)) / area
        b1 = ((x[2] - gx) * (y[0] - gy) - (x[0] - gx) * (y[2] - gy)) / area
        b2 = 1 - b0 - b1
        zz = b0 * z[0] + b1 * z[1] + b2 * z[2]
        sub = depth[y0 : y1 + 1, x0 : x1 + 1]
        hit = (b0 >= -1e-4) & (b1 >= -1e-4) & (b2 >= -1e-4) & (zz > sub)
        if hit.any():
            sub[hit] = zz[hit]
            rgb[y0 : y1 + 1, x0 : x1 + 1][hit] = color * shade[i]
            normal[y0 : y1 + 1, x0 : x1 + 1][hit] = n[i]
    return rgb, depth, normal


def outline(mask_a, mask_b):
    edge = np.zeros_like(mask_a)
    edge[:, 1:] |= mask_a[:, 1:] & mask_b[:, 1:]
    edge[1:, :] |= mask_a[1:, :] & mask_b[1:, :]
    return edge


def render(items, eye, up=(0, 0, 1), scale=5.0, window=None, margin=8.0):
    """Orthographic render. Returns the image and its extent in view millimetres."""
    cam = basis(eye, up)
    right, upv, _ = cam
    pts = np.concatenate([t.reshape(-1, 3) for t, _, _ in items])
    u, v = pts @ right, pts @ upv
    u0, u1, v0, v1 = window or (u.min() - margin, u.max() + margin, v.min() - margin, v.max() + margin)
    shape = (int((v1 - v0) * scale), int((u1 - u0) * scale))
    rgb = np.ones(shape + (3,))
    depth = np.full(shape, -np.inf)
    ident = np.zeros(shape, int)
    normal = np.zeros(shape + (3,))
    solid = [it for it in items if it[2] >= 1]
    for k, (tris, color, _) in enumerate(solid, 1):
        c, d, n = raster(tris, color, cam, (u0, v1), scale, shape)
        near = d > depth
        rgb[near], depth[near], ident[near], normal[near] = c[near], d[near], k, n[near]
    # dark lines at part boundaries, depth steps and sharp creases
    edge = np.zeros(shape, bool)
    for axis in (0, 1):
        s1 = (slice(1, None), slice(None)) if axis == 0 else (slice(None), slice(1, None))
        s0 = (slice(None, -1), slice(None)) if axis == 0 else (slice(None), slice(None, -1))
        with np.errstate(invalid="ignore"):
            dz = np.abs(np.nan_to_num(depth[s1] - depth[s0], nan=99, posinf=99, neginf=99))
        crease = (normal[s1] * normal[s0]).sum(-1) < 0.6
        both = (ident[s1] > 0) | (ident[s0] > 0)
        edge[s1] |= both & ((ident[s1] != ident[s0]) | (dz > 1.2) | crease)
    rgb[edge] *= 0.25
    for tris, color, alpha in (it for it in items if it[2] < 1):
        c, d, _ = raster(tris, color, cam, (u0, v1), scale, shape)
        front = d > depth
        rgb[front] = (1 - alpha) * rgb[front] + alpha * c[front]
        inside = np.isfinite(d)
        rim = np.zeros(shape, bool)
        rim[1:, :] |= inside[1:, :] != inside[:-1, :]
        rim[:, 1:] |= inside[:, 1:] != inside[:, :-1]
        rgb[rim & (front | ~inside)] *= 0.6
    return np.clip(rgb, 0, 1), (u0, u1, v0, v1), cam


def show(ax, items, eye, title, **kw):
    img, extent, cam = render(items, eye, **kw)
    ax.imshow(img, extent=extent, interpolation="bilinear")
    ax.set_title(title, fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    return lambda p: (float(np.dot(tuple(p), cam[0])), float(np.dot(tuple(p), cam[1])))


def label(ax, proj, point, text, offset, color="black"):
    u, v = proj(point)
    ax.annotate(
        text, xy=(u, v), xytext=(u + offset[0], v + offset[1]), fontsize=8.5, color=color, ha="center", va="center",
        arrowprops=dict(arrowstyle="-", lw=0.7, color="0.2"), bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.6", lw=0.6),
    )


def save(fig, name):
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / name, dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", OUT / name)


# ---------------------------------------------------------------------------
# scene
# ---------------------------------------------------------------------------
PARTS = ws.printable_parts()
COLLAR_R, PIVOT_X = ws.collar_layout()
PIVOT = np.array((PIVOT_X, 0, ws.CAM_COLLAR_Z))
SCREEN_X, BACK_X, POCKET_W, BOTTOM_Z, BACK_H = ws.cradle_layout()
LEAN = ws.STICK_LEAN_DEG
WORLD_UP = (sin(radians(LEAN)), 0, cos(radians(LEAN)))  # vertical, seen from the leaning stick frame
WORLD_FWD = (cos(radians(LEAN)), 0, -sin(radians(LEAN)))


def at(tilt, shape):
    return ws.cradle_location(tilt) * shape


def pivot_point(x, y, z, tilt=T):
    """A point given in the pivot frame, returned in the stick frame."""
    return tuple((ws.cradle_location(tilt) * Pos(x, y, z)).position)


def assembly(tilt=T, hand=True, hardware=True, stick=True, handle=True):
    items = [
        item(ws.collar_location() * PARTS["camera_collar"], "collar"),
        item(at(tilt, PARTS["phone_cradle"]), "cradle"),
        item(at(tilt, ws.ref_phone()), "phone"),
        item(at(tilt, ws.ref_strap()), "strap"),
    ]
    if handle:
        items.append(item(PARTS["stick_handle"], "handle"))
    if stick:
        items.append(item(ws.ref_stick(), "stick"))
    if hardware:
        items.append(item(ws.ref_hardware(tilt), "hardware"))
    if hand and handle:
        items.append(item(ws.ref_hand(), "hand", 0.35))
    return items


def phone_top(tilt=T):
    return pivot_point(SCREEN_X + ws.PHONE_T / 2, 0, BOTTOM_Z + ws.PHONE_H, tilt)


def camera_centre(tilt=T):
    y0, y1, z0, z1 = ws.camera_rect()
    return pivot_point(SCREEN_X + ws.PHONE_T + ws.CAM_BUMP_T, (y0 + y1) / 2, (z0 + z1) / 2, tilt)


def view_isometric():
    fig, axes = plt.subplots(1, 2, figsize=(17, 11))
    eye = np.array(WORLD_FWD) * 0.75 + np.array((0, -0.6, 0)) + np.array(WORLD_UP) * 0.3
    proj = show(axes[0], assembly(), eye, f"1a. As used: pole leaning {LEAN:.0f} deg, seen from the front right", up=WORLD_UP)
    label(axes[0], proj, camera_centre(), "camera bump\n(reference, UNCONFIRMED)", (70, 30))
    label(axes[0], proj, pivot_point(BACK_X + ws.BACK_T, -20, BOTTOM_Z + 30), "phone cradle", (75, -20))
    label(axes[0], proj, (PIVOT_X, -10, ws.CAM_COLLAR_Z), "tilt joint", (60, -40))
    label(axes[0], proj, (0, -COLLAR_R, ws.CAM_COLLAR_Z), "collar clamped\non the pole", (-70, -20))
    label(axes[0], proj, (-60, -15, 55), "level grip +\nhand envelope", (-40, 50))
    eye = -np.array(WORLD_FWD) * 0.7 + np.array((0, -0.6, 0)) + np.array(WORLD_UP) * 0.35
    proj = show(axes[1], assembly(), eye, "1b. As used, from behind the user's right side", up=WORLD_UP)
    label(axes[1], proj, pivot_point(SCREEN_X, 0, BOTTOM_Z + 120), "phone screen faces\nback at the pole", (-80, 30))
    label(axes[1], proj, (-(COLLAR_R + 7), -9, ws.CAM_COLLAR_Z), "2 x M3 clamp screws", (-70, -30))
    save(fig, "1_assembled_isometric.png")


def view_side():
    fig, axes = plt.subplots(1, 2, figsize=(18, 11))
    ghosts = [item(at(t, ws.ref_phone()), "phone", 0.16) for t in (ws.TILT_MIN, ws.TILT_MAX) if t != T]
    view = [item(at(T, ws.ref_camera_view(140)), "view", 0.25)]

    ax = axes[0]
    proj = show(ax, assembly() + view, (0, -1, 0), f"2a. In use: pole leaning back {LEAN:.0f} deg, grip level", up=WORLD_UP)
    cam = np.array(proj(camera_centre()))
    pitch = T - LEAN
    aim = np.array([cos(radians(pitch)), -sin(radians(pitch))])
    ax.plot([cam[0] - 30, cam[0] + 170], [cam[1], cam[1]], "k--", lw=0.9)
    ax.text(cam[0] + 120, cam[1] + 5, "horizontal", fontsize=9)
    ax.annotate("", xy=cam + 160 * aim, xytext=cam, arrowprops=dict(arrowstyle="-|>", color="crimson", lw=2))
    ax.add_patch(Arc(cam, 170, 170, theta1=-pitch, theta2=0, color="crimson", lw=1.3))
    ax.text(cam[0] + 60, cam[1] - 50, f"camera looks {pitch:.0f} deg below the horizon\n= PHONE_TILT_DEG {T:.0f} - lean {LEAN:.0f}",
            color="crimson", fontsize=10, va="top", bbox=dict(fc="white", ec="none", pad=1))
    s0, s1 = np.array(proj((0, 0, -360))), np.array(proj((0, 0, 60)))
    ax.plot([s0[0], s1[0]], [s0[1], s1[1]], "k-.", lw=0.9)
    ax.plot([s0[0], s0[0]], [s0[1], s0[1] + 170], color="0.4", lw=0.9, ls=":")
    ax.text(s0[0] + 5, s0[1] + 25, f"vertical\n(lean {LEAN:.0f} deg)", fontsize=9, color="0.3")
    label(ax, proj, (-60, 0, 60), "hand clearance envelope", (-20, 50))
    label(ax, proj, tuple(PIVOT), "pivot on the collar:\nM3 pivot screw + M3 index screw", (95, -45))
    label(ax, proj, (-COLLAR_R - 8, 0, ws.CAM_COLLAR_Z), "pole collar,\nslides and turns\nbefore clamping", (-75, -25))

    ax = axes[1]
    proj = show(ax, assembly() + ghosts, (0, -1, 0), "2b. Stick frame: +Z up the pole, +X its forward normal")
    cam = np.array(proj(camera_centre()))
    aim = np.array([cos(radians(T)), -sin(radians(T))])
    ax.plot([0, 0], [-370, 110], "k-.", lw=0.9)
    ax.text(-5, 100, "pole axis (+Z)", fontsize=9, ha="right")
    ax.plot([cam[0], cam[0] + 150], [cam[1], cam[1]], "k--", lw=0.9)
    ax.text(cam[0] + 95, cam[1] + 5, "pole normal (+X)", fontsize=9)
    ax.annotate("", xy=cam + 150 * aim, xytext=cam, arrowprops=dict(arrowstyle="-|>", color="crimson", lw=2))
    ax.add_patch(Arc(cam, 150, 150, theta1=-T, theta2=0, color="crimson", lw=1.3))
    ax.text(cam[0] + 85, cam[1] - 30, f"PHONE_TILT_DEG = {T:.0f}", color="crimson", fontsize=10, bbox=dict(fc="white", ec="none", pad=1))
    label(ax, proj, phone_top(ws.TILT_MIN), f"tilt {ws.TILT_MIN} (ghost)", (45, 35))
    label(ax, proj, phone_top(ws.TILT_MAX), f"tilt {ws.TILT_MAX} (ghost)", (40, -45))
    label(ax, proj, (-60, 0, 45), f"grip turned {ws.GRIP_TILT_DEG:.0f} deg\nnose-down", (-60, -50))
    save(fig, "2_side_view_tilt.png")


def view_front():
    c, s = cos(radians(T)), sin(radians(T))
    aim, long_axis = (c, 0, -s), (s, 0, c)
    fig, axes = plt.subplots(1, 2, figsize=(16, 10))
    ax = axes[0]
    proj = show(ax, assembly(hand=False, handle=False, stick=False), aim, "3a. Front view, looking back along the camera axis", up=long_axis, margin=45)

    def band(y0, y1, z0, z1, text, color, where):
        corners = [proj(pivot_point(BACK_X + ws.BACK_T + 3, y, z)) for y, z in ((y0, z0), (y1, z0), (y1, z1), (y0, z1), (y0, z0))]
        ax.plot(*zip(*corners), color=color, ls="--", lw=1.4)
        mid = np.mean(corners[:4], axis=0)
        if not text:
            return
        ax.annotate(text, xy=mid, xytext=mid + where, fontsize=8.5, color=color, ha="center",
                    arrowprops=dict(arrowstyle="-", lw=0.7, color=color), bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color, lw=0.6))

    w, top = ws.PHONE_W / 2, BOTTOM_Z + ws.PHONE_H
    band(-w, w, top - ws.CAM_KEEPOUT_H, top, f"camera keep-out, top {ws.CAM_KEEPOUT_H:.0f} mm", "crimson", np.array((0, 38)))
    for side in (1, -1):
        band(side * w, side * (w + 5), BOTTOM_Z + ws.BUTTON_KEEPOUT[0], BOTTOM_Z + ws.BUTTON_KEEPOUT[1],
             "side-button keep-out\n(both sides)" if side > 0 else "", "darkorange", np.array((-38, 0)))
    band(-ws.PORT_KEEPOUT_W / 2, ws.PORT_KEEPOUT_W / 2, BOTTOM_Z - 14, BOTTOM_Z, f"port gap {ws.PORT_KEEPOUT_W:.0f} mm", "purple", np.array((-60, -6)))
    label(ax, proj, pivot_point(BACK_X + ws.BACK_T, 20, BOTTOM_Z + BACK_H), f"back plate top\n{BACK_H:.0f} mm up", (45, 12))
    label(ax, proj, pivot_point(BACK_X + ws.BACK_T, 0, BOTTOM_Z + ws.STRAP_Z), "strap in edge notches", (70, -4))
    label(ax, proj, pivot_point(BACK_X + ws.BACK_T, 0, BOTTOM_Z + BACK_H * 0.5), "push-out window", (62, -22))

    ax = axes[1]
    items = [item(at(T, PARTS["phone_cradle"]), "cradle"), item(at(T, ws.ref_phone()), "phone"), item(at(T, ws.ref_strap()), "strap")]
    proj = show(ax, items, tuple(-a for a in aim), "3b. Screen side (pole and collar hidden)", up=long_axis)
    label(ax, proj, pivot_point(SCREEN_X - ws.LIP_T, POCKET_W / 2, BOTTOM_Z + 30), f"side lips, {ws.SIDE_H:.0f} mm tall", (-55, 25))
    label(ax, proj, pivot_point(SCREEN_X - ws.FRONT_BAR_T, 25, BOTTOM_Z + 4), "bottom lip", (55, -22))
    label(ax, proj, pivot_point(0, 0, 0), "clevis for the collar's tongue", (-45, -30))
    label(ax, proj, pivot_point(SCREEN_X, 0, BOTTOM_Z + 115), "screen stays open\nabove the strap", (0, 0))
    save(fig, "3_front_view_retention.png")


def view_exploded():
    fig, ax = plt.subplots(figsize=(16, 11))
    hw = ws.ref_hardware()
    items = [
        item(Pos(0, 0, 60) * PARTS["stick_handle"], "handle"),
        item(ws.ref_stick(), "stick"),
        item(Pos(45, 0, 0) * ws.collar_location() * PARTS["camera_collar"], "collar"),
        item(Pos(105, 0, 0) * at(T, PARTS["phone_cradle"]), "cradle"),
        item(Pos(170, 0, 30) * at(T, ws.ref_phone()), "phone"),
        item(Pos(225, 0, -40) * at(T, ws.ref_strap()), "strap"),
        item([Pos(105, 45 if i % 2 == 0 else -40, 0) * h for i, h in enumerate(hw[:4])], "hardware"),
        item([Pos(45, 45 if i % 2 == 0 else -40, 0) * h for i, h in enumerate(hw[4:])], "hardware"),
    ]
    proj = show(ax, items, (0.55, 0.75, 0.4), f"4. Exploded view (parts in colour, hardware in beige, tilt {T:.0f} deg)")
    label(ax, proj, (-60, 15, 110), "stick_handle", (70, 30))
    label(ax, proj, (45 + PIVOT_X, 4, ws.CAM_COLLAR_Z - 12), "camera_collar", (-10, -70))
    label(ax, proj, tuple(np.array(pivot_point(SCREEN_X, 0, 30)) + (105, 0, 0)), "phone_cradle", (-20, 85))
    label(ax, proj, tuple(np.array(phone_top()) + (170, 0, 30)), "phone (reference)", (-40, 20))
    label(ax, proj, tuple(np.array(pivot_point(SCREEN_X, 40, ws.STRAP_Z)) + (225, 0, -40)), "20 mm hook-and-loop strap", (-20, -55))
    label(ax, proj, (105 + PIVOT_X, 60, ws.CAM_COLLAR_Z), "2 x M3 x 20 screws + M3 nuts (far side):\npivot and index", (10, -95))
    label(ax, proj, (45 - COLLAR_R - 7, 60, ws.CAM_COLLAR_Z), "2 x M3 x 20 screws\n+ M3 nuts (far side)", (80, -60))
    label(ax, proj, (0, 9, -330), "18 mm carbon tube", (70, -10))
    save(fig, "4_exploded.png")


def view_sections():
    fig, axes = plt.subplots(1, 3, figsize=(21, 9))
    keep = box(-300, 500, 0, 200, -500, 300)
    cut = lambda s: s & keep
    z = ws.CAM_COLLAR_Z
    items = [
        item(cut(ws.collar_location() * PARTS["camera_collar"]), "collar"),
        item(cut(at(T, PARTS["phone_cradle"])), "cradle"),
        item(cut(at(T, ws.ref_phone())), "phone"),
        item(cut(ws.ref_stick()), "stick"),
    ]
    ax = axes[0]
    proj = show(ax, items, (0, -1, 0), "5a. Joint and collar, section on the centre plane (y = 0)", window=(-45, 95, z - 60, z + 60), scale=9)
    label(ax, proj, (PIVOT_X, 0, z), "M3 pivot", (-8, -45))
    label(ax, proj, (PIVOT_X, 0, z + ws.INDEX_R), f"{len(ws.tongue_hole_angles())} index holes\nin the tongue", (-15, 42))
    label(ax, proj, (COLLAR_R + 4, 0, z - 8), "tongue, one piece\nwith the collar", (5, -42))
    label(ax, proj, (-COLLAR_R - 6, 0, z), "clamp slit\nand ears", (-12, 38))
    label(ax, proj, (0, 0, z + 30), "18 mm tube", (-25, 15))
    label(ax, proj, pivot_point(SCREEN_X - 2, 0, 0), "cradle front bar", (30, -40))

    ax = axes[1]
    keep = box(-300, PIVOT_X, -200, 200, -500, 300)
    hw = ws.ref_hardware()
    items = [
        item(cut(ws.collar_location() * PARTS["camera_collar"]), "collar"),
        item(cut(at(T, PARTS["phone_cradle"])), "cradle"),
        item(cut(hw[0]), "hardware"),
        item(cut(hw[1]), "hardware"),
    ]
    proj = show(ax, items, (1, 0, 0), "5b. Section through the pivot axis, seen from the front", window=(-32, 32, z - 26, z + 26), scale=14)
    half = (ws.TONGUE_T + ws.JOINT_GAP) / 2 + ws.CHEEK_T
    label(ax, proj, (PIVOT_X, 0, z - 9), f"tongue, {ws.TONGUE_T:.0f} mm", (0, -13))
    label(ax, proj, (PIVOT_X, half - 2, z + 8), f"cheek, {ws.CHEEK_T:.0f} mm", (10, 14))
    label(ax, proj, (PIVOT_X, half + 3, z), "M3 screw head", (12, -12))
    label(ax, proj, (PIVOT_X, -half + 1, z), "M3 nut\nin hex pocket", (-12, -12))
    label(ax, proj, (PIVOT_X, 0, z), f"hole {ws.PIVOT_BOLT_D} mm for M3", (0, 17))

    ax = axes[2]
    keep = box(-300, 500, 0, 200, -500, 300)
    items = [item(cut(PARTS["stick_handle"]), "handle"), item(cut(ws.ref_stick()), "stick"), item(cut(PARTS["socket_plug"]), "collar")]
    proj = show(ax, items, (0, -1, 0), "5c. Handle on the tube, section on the centre plane", window=(-125, 45, -65, 95), scale=8)
    label(ax, proj, (9, 0, -30), "tube wall between\nbore and plug", (45, -25))
    label(ax, proj, (0, 0, -18), "plug: a separate part,\nglued in the tube", (48, 22))
    label(ax, proj, (-60, 0, 50), f"grip turned {ws.GRIP_TILT_DEG:.0f} deg", (20, 35))
    save(fig, "5_sections_joint.png")


def view_print_orientation():
    notes = {
        "stick_handle": "on its side; supports under the grip and socket",
        "socket_plug": "standing up; no supports",
        "camera_collar": "upright; no supports",
        "phone_cradle": "back plate down; supports under the lips only",
        "cradle_fit_test": "back plate down; supports under the lips only",
        "handle_fit_test": "socket mouth up; no supports",
        "motor_mount": "motor plate down; supports in the collar",
    }
    colors = {"stick_handle": "handle", "socket_plug": "collar", "camera_collar": "collar", "phone_cradle": "cradle", "cradle_fit_test": "cradle", "handle_fit_test": "handle", "motor_mount": "motor"}
    fig, axes = plt.subplots(2, 4, figsize=(24, 11))
    for ax in axes.flat[len(PARTS):]:
        ax.axis("off")
    for ax, (name, part) in zip(axes.flat, PARTS.items()):
        laid = ws.as_printed(name, part)
        bb = laid.bounding_box()
        bed = box(bb.min.X - 8, bb.max.X + 8, bb.min.Y - 8, bb.max.Y + 8, -1.5, 0)
        show(ax, [item(bed, "bed"), item(laid, colors[name])], (0.6, -0.7, 0.5),
             f"{name}\n{bb.size.X:.0f} x {bb.size.Y:.0f} x {bb.size.Z:.0f} mm on the bed: {notes[name]}", scale=6)
    fig.suptitle("6. Print orientations (grey slab = print bed)", fontsize=13)
    save(fig, "6_print_orientations.png")


def dim(ax, a, b, text, off=(0, 0), text_off=(0, 0), color="navy"):
    """Dimension line between two points in view millimetres, pushed out by off."""
    a, b, off = np.array(a, float), np.array(b, float), np.array(off, float)
    for p in (a, b):
        ax.plot(*zip(p, p + off * 1.08), color=color, lw=0.6)
    ax.annotate("", xy=a + off, xytext=b + off, arrowprops=dict(arrowstyle="<->", color=color, lw=1.0, shrinkA=0, shrinkB=0))
    mid = (a + b) / 2 + off + np.array(text_off, float)
    ax.text(*mid, text, fontsize=9, color=color, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=1.2))


def note(ax, point, text, offset):
    ax.annotate(text, xy=point, xytext=(point[0] + offset[0], point[1] + offset[1]), fontsize=9, color="navy", ha="center", va="center",
                arrowprops=dict(arrowstyle="->", lw=0.8, color="navy"), bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="navy", lw=0.6))


SIDE, TOP, FRONT = (0, -1, 0), (0, 0, 1), (1, 0, 0)  # view coordinates: (x, z), (x, y), (y, z)


def drawing_handle():
    part = PARTS["stick_handle"]
    bb = part.bounding_box()
    bore, plug = ws.STICK_OD + ws.STICK_FIT, ws.STICK_ID - ws.PLUG_FIT
    fig, axes = plt.subplots(1, 2, figsize=(18, 10))
    ax = axes[0]
    keep = box(-300, 300, 0, 100, -300, 300)
    show(ax, [item(part & keep, "handle"), item(PARTS["socket_plug"] & keep, "collar")], SIDE,
         "stick_handle: section on the centre plane, with the separate plug (orange) where it sits in the tube", margin=38, scale=7)
    dim(ax, (bb.min.X, bb.max.Z), (bb.max.X, bb.max.Z), f"{bb.size.X:.1f} overall", off=(0, 14))
    dim(ax, (bb.max.X, bb.min.Z), (bb.max.X, bb.max.Z), f"{bb.size.Z:.1f}\noverall", off=(16, 0), text_off=(8, 0))
    d = ws.SOCKET_DEPTH
    dim(ax, (-ws.SOCKET_OD / 2, -d), (ws.SOCKET_OD / 2, -d), f"socket {ws.SOCKET_OD:.0f} dia", off=(0, -26))
    dim(ax, (-bore / 2, -d), (bore / 2, -d), f"bore {bore:.1f} dia", off=(0, -16))
    dim(ax, (-plug / 2, -d + ws.PLUG_RECESS), (plug / 2, -d + ws.PLUG_RECESS), f"plug {plug:.1f} dia", off=(0, -4.5))
    dim(ax, (-ws.SOCKET_OD / 2, -d), (-ws.SOCKET_OD / 2, 0), f"tube goes in {d:.0f}", off=(-12, 0), text_off=(-16, 0))
    note(ax, (-55, 16 + 55 * 0.577 - 12), f"grip {ws.GRIP_W:.0f} wide x {ws.GRIP_H:.0f} tall,\nturned {ws.GRIP_TILT_DEG:.0f} deg nose-down", (-15, -40))
    note(ax, ((bore / 2 + ws.SOCKET_OD / 2) / 2, -d / 2), f"hole {ws.SET_SCREW_D} dia through one\nside wall: M3 screw cuts\nits own thread", (48, 8))
    b = (ws.button_location() * Pos(0, 0, 4)).position
    note(ax, (b.X, b.Z), f"thumb button: {ws.BUTTON_HOLE_D} mm hole for its 7 mm thread,\n{ws.BUTTON_SEAT_D:.0f} mm flat on top for its nut,\n{ws.BUTTON_POCKET_D:.0f} mm pocket underneath for its body", (30, 42))
    ax = axes[1]
    show(ax, [item(part, "handle")], (0, 0, -1), "stick_handle: seen from below", up=(0, 1, 0), margin=30, scale=7)
    dim(ax, (-bb.min.X, -ws.GRIP_W / 2), (-bb.min.X, ws.GRIP_W / 2), f"{ws.GRIP_W:.0f}", off=(12, 0), text_off=(6, 0))
    save(fig, "7_dimensions_handle.png")


def drawing_collar():
    part = PARTS["camera_collar"]
    bb = part.bounding_box()
    bore = ws.STICK_OD + ws.STICK_FIT
    ear_x = COLLAR_R + 14
    bolt_x = -(COLLAR_R + 7)
    fig, axes = plt.subplots(1, 2, figsize=(18, 9))
    ax = axes[0]
    show(ax, [item(part, "collar")], TOP, "camera_collar: seen from above", up=(0, 1, 0), margin=30, scale=12)
    dim(ax, (bb.min.X, bb.max.Y), (bb.max.X, bb.max.Y), f"{bb.size.X:.1f} overall", off=(0, 16))
    dim(ax, (-bore / 2, 0), (bore / 2, 0), f"bore {bore:.1f} dia", off=(0, 0))
    dim(ax, (-COLLAR_R, -COLLAR_R), (COLLAR_R, -COLLAR_R), f"collar {2 * COLLAR_R:.1f} dia", off=(0, -8))
    dim(ax, (0, -COLLAR_R), (PIVOT_X, -COLLAR_R), f"pole axis to pivot {PIVOT_X:.1f}", off=(0, -19))
    dim(ax, (bb.max.X, -ws.TONGUE_T / 2), (bb.max.X, ws.TONGUE_T / 2), f"tongue {ws.TONGUE_T:.0f}", off=(8, 0), text_off=(11, 0))
    dim(ax, (-ear_x, -9), (-ear_x, 9), "ears 18", off=(-8, 0), text_off=(-10, 0))
    note(ax, (-ear_x + 3, 0), f"clamp slit {ws.SLIT:.0f}", (-2, 24))
    ax = axes[1]
    show(ax, [item(part, "collar")], SIDE, "camera_collar: side view", margin=30, scale=12)
    h = ws.CAM_COLLAR_H
    dim(ax, (bb.max.X, -h / 2), (bb.max.X, h / 2), f"{h:.0f} tall", off=(10, 0), text_off=(10, 0))
    dim(ax, (bolt_x, -h / 4), (bolt_x, h / 4), f"{h / 2:.1f}", off=(-16, 0), text_off=(-8, 0))
    note(ax, (bolt_x, h / 4), f"2 clamp holes {ws.CLAMP_BOLT_D} dia\nfor M3, nut pockets\n{ws.CLAMP_NUT_AF} across flats on this face", (0, 24))
    note(ax, (PIVOT_X, 0), f"pivot hole {ws.PIVOT_BOLT_D} dia for M3", (5, -27))
    x, z = ws.polar_xz(ws.INDEX_R, 90)
    note(ax, (PIVOT_X + x, z), f"{len(ws.tongue_hole_angles())} index holes {ws.INDEX_D} dia for M3,\non a {ws.INDEX_R:.0f} radius, 30 deg apart", (0, 22))
    dim(ax, (PIVOT_X - ws.JOINT_R, -h / 2), (PIVOT_X + ws.JOINT_R, -h / 2), f"joint disc {2 * ws.JOINT_R:.0f} dia", off=(0, -9))
    save(fig, "8_dimensions_collar.png")


def drawing_cradle():
    part = PARTS["phone_cradle"]
    bb = part.bounding_box()
    half_w = POCKET_W / 2 + ws.CRADLE_WALL
    depth = BACK_X - SCREEN_X
    clevis = ws.TONGUE_T + ws.JOINT_GAP
    fig, axes = plt.subplots(1, 3, figsize=(21, 10))
    ax = axes[0]
    show(ax, [item(part, "cradle")], (-1, 0, 0), "phone_cradle: screen side", margin=34, scale=7)
    flip = lambda y, z: (-y, z)  # this view looks along +X, so left and right swap
    dim(ax, flip(half_w, bb.max.Z), flip(-half_w, bb.max.Z), f"{2 * half_w:.1f} overall", off=(0, 20))
    dim(ax, flip(POCKET_W / 2, bb.max.Z), flip(-POCKET_W / 2, bb.max.Z), f"phone pocket {POCKET_W:.1f} wide", off=(0, 9))
    lip = POCKET_W / 2 - ws.LIP_OVER
    dim(ax, flip(lip, BOTTOM_Z + ws.SIDE_H), flip(-lip, BOTTOM_Z + ws.SIDE_H), f"{2 * lip:.1f} between lips", off=(0, 6))
    dim(ax, flip(-half_w, BOTTOM_Z), flip(-half_w, BOTTOM_Z + ws.SIDE_H), f"lips {ws.SIDE_H:.0f}", off=(14, 0), text_off=(11, 0))
    dim(ax, flip(half_w, bb.min.Z), flip(half_w, bb.max.Z), f"{bb.size.Z:.0f}\noverall", off=(-16, 0), text_off=(-9, 0))
    dim(ax, flip(clevis / 2, -ws.JOINT_R), flip(-clevis / 2, -ws.JOINT_R), f"slot {clevis:.1f}", off=(0, -9))
    w = clevis / 2 + ws.CHEEK_T
    dim(ax, flip(w, -ws.JOINT_R), flip(-w, -ws.JOINT_R), f"clevis {2 * w:.1f} wide", off=(0, -19))
    ax = axes[1]
    show(ax, [item(part, "cradle")], SIDE, "phone_cradle: side view", margin=34, scale=7)
    dim(ax, (bb.min.X, bb.max.Z), (bb.max.X, bb.max.Z), f"{bb.size.X:.1f} overall", off=(0, 14))
    dim(ax, (SCREEN_X, BOTTOM_Z + ws.SIDE_H), (BACK_X, BOTTOM_Z + ws.SIDE_H), f"pocket {depth:.1f} deep", off=(0, 12))
    dim(ax, (0, 0), (SCREEN_X, 0), f"pivot to screen {SCREEN_X:.1f}", off=(0, -26))
    dim(ax, (BACK_X + ws.BACK_T, BOTTOM_Z), (BACK_X + ws.BACK_T, BOTTOM_Z + BACK_H), f"back plate\n{BACK_H:.0f} above\nphone bottom", off=(12, 0), text_off=(14, 0))
    note(ax, (0, 0), f"pivot hole {ws.PIVOT_BOLT_D} dia for M3", (-18, -38))
    x, z = ws.polar_xz(ws.INDEX_R, ws.INDEX_PIN_ANGLES[1])
    note(ax, (x, z), f"2 index holes {ws.INDEX_D} dia for M3;\nnut pockets {ws.INDEX_NUT_AF} across flats\non this cheek", (-22, 34))
    ax = axes[2]
    show(ax, [item(part, "cradle")], (0, 0, -1), "phone_cradle: seen from below", up=(0, 1, 0), margin=30, scale=7)
    g = ws.PORT_KEEPOUT_W / 2
    dim(ax, (-BACK_X, -g), (-BACK_X, g), f"port gap {ws.PORT_KEEPOUT_W:.0f}", off=(-22, 0), text_off=(-12, 0))
    note(ax, (-(BACK_X + ws.BACK_T / 2), half_w - ws.CRADLE_R - ws.TETHER_HOLE_D / 2 - 3), f"tether hole {ws.TETHER_HOLE_D:.0f} dia", (-32, 14))
    fig.suptitle("Pocket sizes are for the UNCONFIRMED placeholder phone: 78 x 162 x 12 mm in its case", fontsize=12, color="crimson")
    save(fig, "9_dimensions_cradle.png")


if __name__ == "__main__":
    view_isometric()
    view_side()
    view_front()
    view_exploded()
    view_sections()
    view_print_orientation()
    drawing_handle()
    drawing_collar()
    drawing_cradle()

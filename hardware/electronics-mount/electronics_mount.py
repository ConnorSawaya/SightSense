"""Tip electronics mount: a two-piece clamp for the bottom of the cane tube that carries
the Raspberry Pi 5 on one side and the 12 V battery pack on the other.

Run with build123d installed:  python electronics_mount.py            (exports + checks)
                               python electronics_mount.py --preview  (also renders a drawing)
All dimensions are millimetres.

RESEARCH PROTOTYPE. Nothing here has been printed or load tested.

Two printed halves close around the 18 mm tube like a clamshell and are pulled
together by four M3 x 20 screws. Nothing has to slide over the end of the tube,
so the mount can go on or come off with the handle and the wheel in place, and
it can be turned to any angle before tightening.

Mount frame: the tube runs up +Z through the origin, z=0 is the bottom of the mount.
  Pi half       on +X: a plate with four standoffs on the Raspberry Pi 5's hole pattern
  battery half  on -X: a plain flat plate; the pack is stuck to it with foam tape or hook-and-loop
"""

import sys
from pathlib import Path

from build123d import (
    Circle,
    Cylinder,
    Plane,
    Polygon,
    Pos,
    RectangleRounded,
    Rot,
    export_step,
    export_stl,
    extrude,
)

# the motor receiver, shared helpers and the preview renderer live in neighbouring folders
for _folder in ("cane-coupler", "handle-phone-mount"):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / _folder))
import coupler_motor_mount as cm  # noqa: E402
from walking_stick import box, hex_pocket, overlap, ref_bolt, ref_nut  # noqa: E402

# --- tube ---
TUBE_OD = 18.0
TUBE_ID = 16.0
SADDLE_FIT = 0.1  # the saddles are this much bigger than the tube, so they grip before the halves meet
HALF_GAP = 2.0  # gap left between the two halves when they grip the tube

# --- Raspberry Pi 5: published board dimensions ---
PI_L = 85.0
PI_W = 56.0
PI_T = 1.6
PI_HOLE_L = 58.0  # hole spacing along the board
PI_HOLE_W = 49.0  # hole spacing across the board
PI_HOLE_EDGE = 3.5  # holes from the board's edges, at the microSD end
PI_STANDOFF_D = 6.5
PI_STANDOFF_H = 5.0  # room for the parts and the microSD slot under the board
PI_PILOT_D = 2.2  # an M2.5 screw cuts its own thread; the Pi's holes are 2.7 mm, too small for M3
PI_BOTTOM_MARGIN = 3.0  # board's microSD end above the bottom of the mount

# --- battery: 18650 3S1P 12 V pack ---
BATT_W = 55.2  # measured by the team
BATT_L = 70.0  # UNCONFIRMED: sellers list about 70
BATT_T = 19.5  # UNCONFIRMED: sellers list about 19
BATT_PAD_T = 2.0  # foam tape or hook-and-loop between the pack and the plate, for the drawings

# --- body ---
MOUNT_H = 92.0
HALF_W = 37.0  # half the mount's width, along Y
PLATE_T = 3.0
PLATE_IN = 12.5  # inner face of each plate, from the tube axis
BAR_H = 10.0  # two clamp bars per half, at the top and the bottom
RIB_T = 4.0  # ribs under the top bar, so it prints without support
RIB_Y = (-32.0, -16.0, 0.0, 16.0, 32.0)
WINDOW_R = 5.0

# --- M3 clamp screws ---
BOLT_Y = 32.0  # outside the Pi's edge, so a hex key reaches the heads with the Pi fitted
SCREW_D = 3.6
HEAD_BORE_D = 6.5
HEAD_SEAT_X = 9.0  # under-head face, measured from the tube axis: an M3 x 20 then reaches through its nut
NUT_AF = 5.8
NUT_T = 3.2
NUT_X = 5.4  # near face of the nut slot, from the tube axis

# --- where it sits on the cane, in the motor frame of coupler_motor_mount.py ---
MOUNT_Z = 40.0  # bottom of the mount above the top of the gearbox: 5 mm over the motor's terminals
MOUNT_TURN = 180.0  # battery over the motor, Pi at the back where its microSD slot is clear


def bolt_positions():
    return [(side * BOLT_Y, z) for z in (BAR_H / 2, MOUNT_H - BAR_H / 2) for side in (1, -1)]


def pi_hole_positions():
    """Pi mounting holes as (y, z): microSD end down, USB and Ethernet up."""
    z0 = PI_BOTTOM_MARGIN + PI_HOLE_EDGE
    return [(side * PI_HOLE_W / 2, z) for z in (z0, z0 + PI_HOLE_L) for side in (1, -1)]


def half_blank(sign):
    """Plate, two clamp bars and ribs under the top bar, on the +X (sign=1) or -X (sign=-1) side."""
    def xs(a, b):
        return sorted((sign * a, sign * b))

    g = HALF_GAP / 2
    part = box(*xs(PLATE_IN, PLATE_IN + PLATE_T), -HALF_W, HALF_W, 0, MOUNT_H)
    part += box(*xs(g, PLATE_IN), -HALF_W, HALF_W, 0, BAR_H)
    part += box(*xs(g, PLATE_IN), -HALF_W, HALF_W, MOUNT_H - BAR_H, MOUNT_H)
    # 45 degree ribs: the top bar then prints as short bridges when the half stands upright
    z1 = MOUNT_H - BAR_H
    wedge = Polygon((sign * PLATE_IN, z1 - (PLATE_IN - g)), (sign * PLATE_IN, z1), (sign * g, z1), align=None)
    rib = extrude(Plane.XZ * wedge, RIB_T / 2, both=True)
    for y in RIB_Y:
        part += Pos(0, y, 0) * rib
    saddle = Cylinder((TUBE_OD + SADDLE_FIT) / 2, MOUNT_H + 2)
    return part - Pos(0, 0, MOUNT_H / 2) * saddle


def window(width, z0, z1, x_face, sign):
    """Rounded opening through a plate, to save plastic and print time."""
    outline = Pos(0, (z0 + z1) / 2) * RectangleRounded(width, z1 - z0, WINDOW_R)
    start = x_face - 1 if sign > 0 else x_face - PLATE_T - 1
    return extrude(Plane.YZ.offset(start) * outline, PLATE_T + 2)


def teardrop(radius):
    """Circle with a point underneath: a boss of this shape prints sideways without support."""
    k = radius / 2**0.5
    return Circle(radius) + Polygon((-k, -k), (k, -k), (0, -2 * k), align=None)


def make_pi_half():
    part = half_blank(1)
    face = PLATE_IN + PLATE_T
    along_x = Rot(0, 90, 0)

    for y, z in pi_hole_positions():
        part += extrude(Plane.YZ.offset(face) * (Pos(y, z) * teardrop(PI_STANDOFF_D / 2)), PI_STANDOFF_H)
    for y, z in pi_hole_positions():
        depth = PI_STANDOFF_H + PLATE_T
        part -= Pos(face + PI_STANDOFF_H - depth / 2 + 0.5, y, z) * along_x * Cylinder(PI_PILOT_D / 2, depth + 1)

    holes = pi_hole_positions()
    z_low, z_high = holes[0][1], holes[-1][1]
    part -= window(PI_HOLE_W - 14, z_low + 13, z_high - 7, face, 1)

    # clamp screws: clearance through the bars, heads sunk in from the outside face
    for y, z in bolt_positions():
        part -= Pos(HEAD_SEAT_X / 2, y, z) * along_x * Cylinder(SCREW_D / 2, HEAD_SEAT_X + 2)
        part -= Pos((HEAD_SEAT_X + face + 1) / 2, y, z) * along_x * Cylinder(HEAD_BORE_D / 2, face + 1 - HEAD_SEAT_X)
    return part


def battery_face_x():
    """The flat face the pack is stuck to."""
    return -(PLATE_IN + PLATE_T)


def make_battery_half():
    """A plain flat plate with the clamp bars behind it. Nothing stands up from the
    outer face, so the pack can be stuck anywhere on it with foam tape or hook-and-loop."""
    part = half_blank(-1)
    along_x = Rot(0, 90, 0)

    # clamp screws: clearance, and a slot each nut slides into from the side
    for y, z in bolt_positions():
        part -= Pos(-PLATE_IN / 2, y, z) * along_x * Cylinder(SCREW_D / 2, PLATE_IN + 1)
        side = 1 if y > 0 else -1
        # the nut goes in corner first, so the slot runs half a corner-to-corner width past the screw
        y0, y1 = sorted((side * (BOLT_Y - NUT_AF / 3**0.5 - 0.1), side * (HALF_W + 1)))
        part -= box(-NUT_X - NUT_T, -NUT_X, y0, y1, z - NUT_AF / 2, z + NUT_AF / 2)
    return part


# ---------------------------------------------------------------------------
# reference geometry, never exported
# ---------------------------------------------------------------------------


def ref_pi():
    """Raspberry Pi 5 as a board with blocks for its tallest parts, on the standoffs."""
    x0 = PLATE_IN + PLATE_T + PI_STANDOFF_H
    z0 = PI_BOTTOM_MARGIN
    board = box(x0, x0 + PI_T, -PI_W / 2, PI_W / 2, z0, z0 + PI_L)
    for y, z in pi_hole_positions():
        board -= Pos(x0 + PI_T / 2, y, z) * Rot(0, 90, 0) * Cylinder(1.35, PI_T + 1)
    ports = box(x0 + PI_T, x0 + PI_T + 16, -PI_W / 2 + 2, PI_W / 2 - 2, z0 + 66, z0 + PI_L + 2)  # USB and Ethernet
    header = box(x0 + PI_T, x0 + PI_T + 8.5, PI_W / 2 - 6, PI_W / 2 - 1, z0 + 7, z0 + 58)  # GPIO pins
    return board + ports + header


def ref_battery():
    """The pack on the plate, centred, standing off by the foam or hook-and-loop."""
    x1 = battery_face_x() - BATT_PAD_T
    z0 = (MOUNT_H - BATT_L) / 2
    return box(x1 - BATT_T, x1, -BATT_W / 2, BATT_W / 2, z0, z0 + BATT_L)


def ref_pad():
    """Foam tape or hook-and-loop between the pack and the plate."""
    x1 = battery_face_x()
    z0 = (MOUNT_H - BATT_L) / 2
    return box(x1 - BATT_PAD_T, x1, -BATT_W / 2 + 3, BATT_W / 2 - 3, z0 + 3, z0 + BATT_L - 3)


def ref_tube(z0=-10.0, z1=None):
    z1 = MOUNT_H + 10 if z1 is None else z1
    return Pos(0, 0, (z0 + z1) / 2) * (Cylinder(TUBE_OD / 2, z1 - z0) - Cylinder(TUBE_ID / 2, z1 - z0))


def ref_bolts():
    """Four M3 x 20 screws with their nuts. ref_bolt runs along Y, so turn it to run along -X."""
    out = []
    for y, z in bolt_positions():
        out.append(Pos(HEAD_SEAT_X, y, z) * Rot(0, 0, -90) * ref_bolt(3, 20, 5.5, 3))
        out.append(Pos(-NUT_X, y, z) * Rot(0, 0, -90) * ref_nut(5.5, 2.4, 3))  # flats up and down, a corner leading in
    return out


def on_cane():
    """Moves anything from the mount frame onto the cane, in the motor frame."""
    return Pos(cm.receiver_x(), 0, MOUNT_Z) * Rot(0, 0, MOUNT_TURN)


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------


def run_checks(parts):
    ok = True

    def report(passed, text):
        nonlocal ok
        ok &= bool(passed)
        print(f"  [{'ok' if passed else 'FAIL'}] {text}")

    pi_half, batt_half = parts["electronics_mount_pi_half"], parts["electronics_mount_battery_half"]
    for name, part in parts.items():
        bb = part.bounding_box().size
        report(part.is_valid and len(part.solids()) == 1, f"{name}: {bb.X:.1f} x {bb.Y:.1f} x {bb.Z:.1f} mm, {part.volume / 1000:.1f} cm3, valid={part.is_valid}, solids={len(part.solids())}")

    tube = ref_tube()
    report(overlap(pi_half, tube) < 1e-6 and overlap(batt_half, tube) < 1e-6, f"both saddles clear the tube by {SADDLE_FIT / 2:.2f} mm, so they grip before the halves meet")
    report(overlap(pi_half, batt_half) < 1e-6, f"the halves do not touch: {pi_half.distance_to(batt_half):.1f} mm gap left for clamping")
    bolts = ref_bolts()
    report(all(overlap(b, pi_half) < 1e-6 and overlap(b, batt_half) < 1e-6 for b in bolts), "four M3 x 20 screws and their nuts sit in their holes and slots")
    tip = HEAD_SEAT_X - 20
    report(tip <= -(NUT_X + 2.4), f"each M3 x 20 reaches {-(NUT_X + 2.4) - tip:.1f} mm past its nut")

    pi = ref_pi()
    report(overlap(pi, pi_half) < 1e-6, f"Pi 5 sits on four standoffs {PI_STANDOFF_H:.0f} mm off the plate, holes on {PI_HOLE_L:.0f} x {PI_HOLE_W:.0f} mm")
    report(all(overlap(b, pi) < 1e-6 for b in bolts), f"screw heads are {BOLT_Y - HEAD_BORE_D / 2 - PI_W / 2:.2f} mm outside the Pi's edge, reachable with the Pi fitted")
    report(2 * HALF_W >= BATT_W + 6 and MOUNT_H >= BATT_L + 6,
           f"the flat plate is {2 * HALF_W:.0f} x {MOUNT_H:.0f} mm, bigger than the {BATT_W} x {BATT_L:.0f} mm pack all round")
    flat = box(battery_face_x() - 30, battery_face_x() - 0.01, -HALF_W - 1, HALF_W + 1, -1, MOUNT_H + 1)
    report(overlap(flat, batt_half) < 1e-6, "nothing stands up from the battery plate's outer face: it is completely flat")
    report(overlap(ref_battery(), batt_half) < 1e-6 and overlap(ref_pad(), batt_half) < 1e-6, "the pack and its pad sit on the plate without collision")

    place = on_cane()
    printed = {"motor receiver": cm.make_motor_receiver()}
    for side in (-1, 1):
        printed[f"motor (can on the {'-Y' if side < 0 else '+Y'} side)"] = cm.ref_motor(side)
    everything = [place * s for s in (pi_half, batt_half, pi, ref_battery())]
    for name, other in printed.items():
        hit = sum(overlap(s, other) for s in everything)
        gap = min(s.distance_to(other) for s in everything)
        report(hit < 1e-6, f"on the cane: clears the {name} by {gap:.1f} mm")
    print(f"  mount spans {MOUNT_Z:.0f} to {MOUNT_Z + MOUNT_H:.0f} mm above the top of the gearbox; the lower clamp bar sits over the glued-in insert")
    return ok


def as_printed(name, part):
    """The Pi half stands upright; the battery half lies on its flat face."""
    if name.endswith("battery_half"):
        part = Rot(0, -90, 0) * part
    return Pos(0, 0, -part.bounding_box().min.Z) * part


def render(parts, out):
    import matplotlib.pyplot as plt

    import preview as pv

    pi_half, batt_half = parts["electronics_mount_pi_half"], parts["electronics_mount_battery_half"]
    pi, batt, pad, bolts = ref_pi(), ref_battery(), ref_pad(), ref_bolts()
    place = on_cane()
    fig, axes = plt.subplots(1, 3, figsize=(22, 10))

    ax = axes[0]
    items = [
        pv.item(place * pi_half, "handle"), pv.item(place * batt_half, "cradle"),
        pv.item(place * pi, "phone"), pv.item(place * batt, "view"), pv.item(place * pad, "strap"),
        pv.item([place * b for b in bolts], "hardware"),
        pv.item(cm.make_motor_receiver(), "collar"), pv.item(cm.ref_motor(-1), "bed"),
        pv.item(Pos(cm.receiver_x(), 0, 0) * ref_tube(cm.RECEIVER_LEN, MOUNT_Z + MOUNT_H + 25), "stick"),
    ]
    proj = pv.show(ax, items, (0.45, -0.8, 0.3), "On the cane, above the motor (shaft pointing right)")
    x_r = cm.receiver_x()
    pv.label(ax, proj, (x_r + PLATE_IN + PLATE_T + BATT_T, -20, MOUNT_Z + 60), "battery pack, stuck\nto the flat plate", (45, 25))
    pv.label(ax, proj, (x_r - PLATE_IN - 10, -28, MOUNT_Z + 75), "Raspberry Pi 5\n(ports up)", (-45, 30))
    pv.label(ax, proj, (x_r, -HALF_W, MOUNT_Z + BAR_H / 2), "clamp bars and\n4 x M3 x 20", (-48, -12))
    pv.label(ax, proj, (-13, -12, 15), "motor", (38, 12))
    pv.label(ax, proj, (x_r - 5, -8, -8), "motor receiver", (-42, -14))

    ax = axes[1]
    keep = box(-80, 80, -80, 80, -5, BAR_H / 2)
    items = [pv.item(pi_half & keep, "handle"), pv.item(batt_half & keep, "cradle"), pv.item(ref_tube() & keep, "stick"),
             pv.item([b & keep for b in bolts[:4]], "hardware")]  # the lower pair of screws and nuts
    pv.show(ax, items, (0, 0, 1), "Looking down the tube, cut through the lower clamp screws", up=(0, 1, 0), margin=18, scale=9)
    face = battery_face_x()
    pv.dim(ax, (-HALF_GAP / 2, -HALF_W), (HALF_GAP / 2, -HALF_W), f"{HALF_GAP:.0f} gap", off=(0, -5))
    pv.dim(ax, (PLATE_IN + PLATE_T, -HALF_W), (PLATE_IN + PLATE_T, HALF_W), f"{2 * HALF_W:.0f} wide", off=(9, 0), text_off=(6, 0))
    pv.dim(ax, (face, 0), (PLATE_IN + PLATE_T, 0), f"{PLATE_IN + PLATE_T - face:.0f} plate to plate", off=(0, HALF_W + 7))
    pv.dim(ax, (-TUBE_OD / 2, 0), (TUBE_OD / 2, 0), f"{TUBE_OD:.0f} tube", off=(0, 0))
    pv.note(ax, (face, -12), "flat face for the battery:\nfoam tape or hook-and-loop", (-17, -6))
    pv.note(ax, (PLATE_IN + PLATE_T + PI_STANDOFF_H / 2, PI_HOLE_W / 2), "Pi standoff", (11, 4))
    pv.note(ax, (HEAD_SEAT_X + 3, BOLT_Y), "screw head, sunk in", (10, 9))
    pv.note(ax, (-NUT_X - NUT_T / 2, -BOLT_Y - 3), "nut slides in\nfrom the side", (-14, -9))

    ax = axes[2]
    items = [pv.item(Pos(34, 0, 0) * pi_half, "handle"), pv.item(Pos(-34, 0, 0) * batt_half, "cradle")]
    proj = pv.show(ax, items, (-0.35, -0.8, 0.35), "The two printed halves, seen from the battery side")
    pv.label(ax, proj, (-34 + face, 0, MOUNT_H * 0.55), f"battery half: plain flat plate,\n{2 * HALF_W:.0f} x {MOUNT_H:.0f} mm", (-48, 28))
    pv.label(ax, proj, (34 + 4, -HALF_W, MOUNT_H - BAR_H / 2), "Pi half, with its\nstandoffs on the far face", (44, 30))
    pv.label(ax, proj, (-34 - NUT_X - 1.5, -HALF_W, BAR_H / 2), "nut slots", (-34, -22))
    fig.suptitle(f"Battery width {BATT_W} mm measured; its length ({BATT_L:.0f}) and thickness ({BATT_T}) are UNCONFIRMED. Pi 5 sizes are the published board dimensions.", fontsize=12, color="crimson")
    fig.savefig(out, dpi=110, bbox_inches="tight", facecolor="white")
    print("wrote", out)


def printable_parts():
    return {"electronics_mount_pi_half": make_pi_half(), "electronics_mount_battery_half": make_battery_half()}


if __name__ == "__main__":
    here = Path(__file__).parent
    out = here / "export"
    out.mkdir(exist_ok=True)
    parts = printable_parts()
    passed = run_checks(parts)
    for name, part in parts.items():
        export_step(part, str(out / f"{name}.step"))
        export_stl(as_printed(name, part), str(out / f"{name}.stl"), tolerance=0.01, angular_tolerance=0.1)
    print("exported", ", ".join(parts), "to", out)
    print("all geometric checks passed" if passed else "SOME CHECKS FAILED")
    if "--preview" in sys.argv:
        (here / "previews").mkdir(exist_ok=True)
        render(parts, here / "previews" / "electronics_mount.png")

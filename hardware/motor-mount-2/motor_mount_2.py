"""Motor mount 2: a sturdier version of the v4 motor receiver, on the same idea.

Run with build123d installed:  python motor_mount_2.py            (exports + checks)
                               python motor_mount_2.py --preview  (also renders a drawing)
All dimensions are millimetres. Same motor frame as coupler_motor_mount.py:
+X along the output shaft, +Z up the motor, z=0 at the top of the gearbox.

RESEARCH PROTOTYPE. Nothing here has been printed or load tested.

Same idea as v4: the receiver takes the main insert's keyed tongue and one M3
cross bolt, the motor slides up into a band from below and two M3 screws go
through the front wall into the gearbox's own threaded holes.

What is sturdier:
  - a sleeve above the socket goes over the end of the cane tube, so bending
    goes from the mount straight into the tube instead of through the tongue
  - the receiver body is 22 mm across instead of 15.7, with no glue grooves
  - the gearbox is held along its whole length by two side walls and a back
    plate, not just by a band round its top
  - a sloped spine runs from the back plate up into the receiver
  - walls are 5 mm instead of 4, and the shelf the gearbox stops against is 5 mm
  - the cross bolt's head and nut are sunk into the body

The tongue socket and the cross-bolt position are unchanged, so it takes the
same v4 main insert.
"""

import sys
from math import sqrt
from pathlib import Path

from build123d import (
    Circle,
    Cone,
    Cylinder,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    RectangleRounded,
    Rot,
    export_step,
    export_stl,
    extrude,
    make_hull,
)

# the coupler, the wheel adapter, the battery and Pi mount, shared helpers and the preview renderer live in neighbouring folders
for _folder in ("cane-coupler", "wheel-adapter", "electronics-mount", "handle-phone-mount"):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / _folder))
import coupler_motor_mount as cm  # noqa: E402
from walking_stick import box, hex_pocket, overlap, ref_bolt, ref_nut  # noqa: E402

# --- receiver body and tube sleeve ---
BODY_D = 22.0  # v4 kept the coupler's 15.7 mm
SLEEVE_FIT = 0.3  # added to the tube's 18 mm for the sleeve's bore, as on the handle
SLEEVE_OD = 25.0
SLEEVE_LEN = 20.0  # how far the sleeve reaches up over the tube
BOLT_D = 3.6  # cross bolt, M3 with room to spare
HEAD_BORE_D = 6.5
HEAD_BORE_DEPTH = 3.5  # the head and the nut sit this deep, so an M3 x 20 still reaches through the nut
NUT_POCKET_DEPTH = 3.0
NUT_AF = 5.8

# --- gearbox channel ---
FIT = 0.3  # clearance per side around the gearbox
WALL = 5.0  # v4: 4
BACK_T = 3.5  # plate behind the motor can's channel
FRONT_T = 5.0  # front wall the two motor screws pass through
BAND_H = 18.0  # the closed band round the top of the gearbox (v4: 16)
FRONT_H = 13.0  # the front wall stays this short, to clear the wheel adapter's collar
LEDGE_T = 5.0  # shelf the gearbox's top end stops against (v4: 4)
SCREW_D = 3.6  # M3 motor screws
FLARE_H = 12.0  # blend from the block up onto the receiver body
FLARE_R = 18.0
MOUNT_ABOVE_SLEEVE = 4.0  # gap left between the sleeve and the battery and Pi mount clamped above it


def layout():
    can_x = -(cm.CAN_FRONT_INSET + cm.CAN_D / 2)
    reach = cm.CAN_D / 2 + BODY_D / 2 + cm.CAN_GAP
    x_r = can_x - sqrt(reach**2 - cm.CAN_Y**2)  # receiver axis, at y=0 behind the can
    cav_x0 = -(cm.GB_T + FIT)
    cav_x1 = cm.BOSS_H + 0.2  # the front wall rests on top of the two bosses
    cav_y = cm.GB_W / 2 + FIT
    chan_x = can_x - cm.CAN_D / 2 - cm.CAN_GAP  # rear of the channel the motor can slides up
    return x_r, cav_x0, cav_x1, cav_y, chan_x, chan_x - BACK_T


def bolt_z():
    return cm.RECEIVER_LEN - cm.BOLT_FROM_MOUTH


def make_motor_mount_2():
    x_r, cav_x0, cav_x1, cav_y, chan_x, back_x = layout()
    out_y = cav_y + WALL
    front_x = cav_x1 + FRONT_T
    low = -cm.GB_L  # bottom of the gearbox

    # block behind the gearbox, running from the back plate to under the receiver
    back_rect = Pos((back_x + cav_x0) / 2, 0) * Rectangle(cav_x0 - back_x, 2 * out_y)
    footprint = make_hull((Pos(x_r, 0) * Circle(BODY_D / 2) + back_rect).edges())

    # closed band round the top of the gearbox, with the shelf above it
    band = footprint + Pos((back_x + front_x) / 2, 0) * Rectangle(front_x - back_x, 2 * out_y)
    body = Pos(0, 0, -BAND_H) * extrude(band, BAND_H + LEDGE_T)

    # channel down the rest of the gearbox: two side walls and a back plate
    body += Pos(0, 0, low) * extrude(Pos(back_x / 2, 0) * Rectangle(-back_x, 2 * out_y), cm.GB_L - BAND_H)

    # sloped spine from the back plate up into the block; the slope prints without support
    rear = x_r - BODY_D / 2
    spine = Pos(0, 0, low) * extrude(footprint, cm.GB_L - BAND_H)
    rise = (cm.GB_L - BAND_H) / (back_x - rear)
    far = rear - 2
    under = Polygon((back_x, low - 0.01), (far, low - 0.01), (far, low + (back_x - far) * rise), align=None)
    body += spine - extrude(Plane.XZ * under, out_y + 1, both=True)

    # 45 degree gussets where the band's side walls step forward past the gearbox's front face
    step = Polygon((0, -BAND_H - front_x), (0, -BAND_H), (front_x, -BAND_H), align=None)
    for side in (1, -1):
        body += Pos(0, side * (cav_y + WALL / 2), 0) * extrude(Plane.XZ * step, WALL / 2, both=True)

    # pocket for the gearbox, open at the bottom, and open at the front below the front wall
    body -= box(cav_x0, cav_x1, -cav_y, cav_y, low - 1, 0)
    body -= box(cav_x1 - 0.01, front_x + 1, -cav_y, cav_y, low - 1, -FRONT_H)

    # receiver body, the blend up onto it, and the sleeve that goes over the tube
    top = cm.RECEIVER_LEN
    body += Pos(x_r, 0, top / 2) * Cylinder(BODY_D / 2, top)
    flare = Pos(x_r, 0, FLARE_H / 2) * Cone(FLARE_R, BODY_D / 2, FLARE_H)
    body += flare & extrude(footprint, FLARE_H)
    body += Pos(x_r, 0, top - 0.75) * Cone(BODY_D / 2, SLEEVE_OD / 2, 1.5)
    body += Pos(x_r, 0, top + SLEEVE_LEN / 2) * Cylinder(SLEEVE_OD / 2, SLEEVE_LEN)
    bore_r = (cm.TUBE_OD + SLEEVE_FIT) / 2
    body -= Pos(x_r, 0, top + SLEEVE_LEN / 2 + 0.5) * Cylinder(bore_r, SLEEVE_LEN + 1)
    body -= Pos(x_r, 0, top + SLEEVE_LEN - 0.4) * Cone(bore_r, bore_r + 0.8, 0.8)  # lead-in for the tube

    # tongue socket, exactly as the v3 coupler: mouth at the bottom of the sleeve
    socket = Pos(0, 0, -0.1) * extrude(RectangleRounded(cm.SOCKET_W, cm.SOCKET_H, 1.0), cm.SOCKET_DEPTH + 0.2)
    socket += Pos(0, 0, -0.1) * extrude(RectangleRounded(cm.LEAD_W, cm.LEAD_H, 1.1), cm.LEAD_DEPTH)
    body -= Pos(x_r, 0, top) * Rot(180, 0, 0) * socket

    # room for the motor can: where it sits, and the path it takes as the motor slides up from below
    for x, y in cm.can_axes():
        height = cm.CAN_L + 6 - low + 1
        body -= Pos(x, y, low - 1 + height / 2) * Cylinder(cm.CAN_D / 2 + cm.CAN_GAP, height)

    # cross bolt through the body and the tongue, head and nut sunk in
    z = bolt_z()
    across = Rot(90, 0, 0)
    body -= Pos(x_r, 0, z) * across * Cylinder(BOLT_D / 2, BODY_D + 6)
    body -= Pos(x_r, BODY_D / 2 - HEAD_BORE_DEPTH + 3, z) * across * Cylinder(HEAD_BORE_D / 2, 6)
    body -= Pos(x_r, -(BODY_D / 2 - NUT_POCKET_DEPTH), z) * hex_pocket(NUT_AF, 6)

    # shock-cord hole, carried on down and out through the spine
    body -= Pos(x_r, 0, (top + low) / 2) * Cylinder(cm.CORD_HOLE_D / 2, top - low + 2)

    # two M3 screws into the gearbox's own threaded bosses
    for side in (1, -1):
        body -= Pos(cav_x1 + FRONT_T / 2, side * cm.HOLE_SPACING_W / 2, -cm.HOLE_FROM_TOP) * Rot(0, 90, 0) * Cylinder(SCREW_D / 2, FRONT_T + 2)
    return body


# ---------------------------------------------------------------------------
# reference geometry, never exported
# ---------------------------------------------------------------------------


def main_location():
    """v4 main insert fully seated: tongue root on the socket's mouth."""
    return Pos(layout()[0], 0, cm.RECEIVER_LEN + cm.MAIN_BARREL_LEN) * Rot(180, 0, 0)


def ref_tube(length=80.0):
    """End of the cane tube, sitting in the sleeve on the socket's mouth."""
    tube = Cylinder(cm.TUBE_OD / 2, length) - Cylinder(cm.TUBE_ID / 2, length)
    return Pos(layout()[0], 0, cm.RECEIVER_LEN + length / 2) * tube


def ref_cross_bolt():
    """M3 x 20 through body and tongue, with its nut, both sunk in."""
    x_r = layout()[0]
    bolt = Pos(x_r, BODY_D / 2 - HEAD_BORE_DEPTH, bolt_z()) * ref_bolt(3, 20, 5.5, 3)
    nut = Pos(x_r, -(BODY_D / 2 - NUT_POCKET_DEPTH), bolt_z()) * ref_nut(5.5, 2.4, 3)
    return bolt, nut


def ref_motor_screws(length=12.0):
    cav_x1 = layout()[2]
    out = []
    for side in (1, -1):
        y, z = side * cm.HOLE_SPACING_W / 2, -cm.HOLE_FROM_TOP
        screw = Pos(cav_x1 + FRONT_T - length / 2, y, z) * Rot(0, 90, 0) * Cylinder(1.5, length)
        out.append(screw + Pos(cav_x1 + FRONT_T + 1.5, y, z) * Rot(0, 90, 0) * Cylinder(2.75, 3))
    return out


def ref_wheel_adapter():
    """The wheel adapter and its clamp screw, on the shaft."""
    import wheel_adapter as wa

    place = Pos(cm.BOSS_H + wa.GEARBOX_GAP, 0, -cm.SHAFT_FROM_TOP) * Rot(0, 90, 0)
    return place * wa.make_wheel_adapter(), place * wa.ref_screws()[0]


def ref_electronics_mount():
    """The battery and Pi mount with the Pi and the battery on it, clamped on the tube just above the sleeve."""
    import electronics_mount as em

    z = cm.RECEIVER_LEN + SLEEVE_LEN + MOUNT_ABOVE_SLEEVE
    place = Pos(layout()[0], 0, z) * Rot(0, 0, em.MOUNT_TURN)
    return z, [place * s for s in (*em.printable_parts().values(), em.ref_pi(), em.ref_battery())]


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------


def run_checks(mount):
    ok = True

    def report(passed, text):
        nonlocal ok
        ok &= bool(passed)
        print(f"  [{'ok' if passed else 'FAIL'}] {text}")

    x_r, cav_x0, cav_x1, cav_y, chan_x, back_x = layout()
    bb = mount.bounding_box().size
    report(mount.is_valid and len(mount.solids()) == 1, f"motor_mount_2: {bb.X:.1f} x {bb.Y:.1f} x {bb.Z:.1f} mm, {mount.volume / 1000:.1f} cm3, valid={mount.is_valid}, solids={len(mount.solids())}")

    seated = main_location() * cm.make_main_insert()
    tube = ref_tube()
    report(overlap(mount, seated) < 1e-6, "the v4 main insert's tongue seats fully in the socket without collision")
    report(overlap(mount, tube) < 1e-6, f"the tube end sits in the sleeve, {SLEEVE_LEN:.0f} mm deep, with {SLEEVE_FIT / 2:.2f} mm clearance each side")
    bolt, nut = ref_cross_bolt()
    report(overlap(bolt, mount) < 1e-6 and overlap(bolt, seated) < 1e-6 and overlap(nut, mount) < 1e-6,
           "an M3 x 20 passes through the body and the tongue; its head and nut sit sunk in their pockets")
    grip = BODY_D - HEAD_BORE_DEPTH - NUT_POCKET_DEPTH
    report(20 - grip >= 2.4, f"that M3 x 20 clamps {grip:.1f} mm, leaving {20 - grip:.1f} mm of thread for the 2.4 mm nut")
    socket_wall = BODY_D / 2 - cm.SOCKET_W / 2
    report(socket_wall >= 5, f"{socket_wall:.1f} mm of plastic round the tongue socket at its thinnest (v4 had {cm.INSERT_OD / 2 - cm.SOCKET_W / 2:.1f} mm)")

    for side in (-1, 1):
        motor = cm.ref_motor(side)
        label = f"motor, can flush with the {'-Y' if side < 0 else '+Y'} side"
        report(overlap(motor, mount) < 1e-6, f"{label}: sits in the mount without collision")
        stuck = [d for d in range(2, 81, 2) if overlap(Pos(0, 0, -d) * motor, mount) > 1e-6]
        report(not stuck, f"{label}: slides up into the mount from below" + (f" (collides when {stuck[0]} mm short)" if stuck else ""))
        report(overlap(motor, seated) < 1e-6 and overlap(motor, tube) < 1e-6 and overlap(bolt, motor) < 1e-6 and overlap(nut, motor) < 1e-6,
               f"{label}: clears the tube, the main insert and the cross bolt")
    report(all(overlap(s, mount) < 1e-6 for s in ref_motor_screws()), "both motor screws pass through the front wall")

    adapter, clamp = ref_wheel_adapter()
    spin = lambda deg, s: Pos(0, 0, -cm.SHAFT_FROM_TOP) * Rot(deg, 0, 0) * Pos(0, 0, cm.SHAFT_FROM_TOP) * s
    gap = min(min(spin(d, adapter).distance_to(mount), spin(d, clamp).distance_to(mount)) for d in range(0, 360, 15))
    hit = max(overlap(spin(d, adapter), mount) + overlap(spin(d, clamp), mount) for d in range(0, 360, 15))
    report(hit < 1e-6 and gap >= 1.0, f"the wheel adapter, with its clamp screw, turns a full revolution {gap:.1f} mm clear of the mount")

    z, carried = ref_electronics_mount()
    others = [mount, cm.ref_motor(-1), cm.ref_motor(1)]
    hit = sum(overlap(s, o) for s in carried for o in others)
    gap = min(s.distance_to(o) for s in carried for o in others)
    report(hit < 1e-6 and gap >= 2.0, f"the battery and Pi mount, clamped {z:.0f} mm above the top of the gearbox, clears this mount and the motor by {gap:.1f} mm")

    side_len = cm.GB_L
    print(f"  the gearbox is held along {side_len:.0f} mm of its {cm.GB_L:.0f} mm length (v4: 16 mm)")
    print(f"  receiver axis is {-x_r:.1f} mm behind the gearbox's front face (v4: {-cm.receiver_x():.1f} mm), {cm.CAN_GAP} mm off the motor can")
    print(f"  the sleeve covers the tube up to {cm.RECEIVER_LEN + SLEEVE_LEN:.0f} mm above the top of the gearbox, so anything else clamped on the tube sits above that")
    return ok


def render(mount, out):
    import matplotlib.pyplot as plt

    import preview as pv

    x_r, cav_x0, cav_x1, cav_y, chan_x, back_x = layout()
    seated = main_location() * cm.make_main_insert()
    motor, tube = cm.ref_motor(-1), ref_tube()
    bolt, nut = ref_cross_bolt()
    screws = ref_motor_screws()
    adapter, clamp = ref_wheel_adapter()
    fig, axes = plt.subplots(1, 3, figsize=(23, 11))

    ax = axes[0]
    items = [pv.item(mount, "collar"), pv.item(seated, "cradle"), pv.item(tube, "stick"), pv.item(motor, "bed"),
             pv.item([bolt, nut] + screws, "strap"), pv.item(adapter, "handle")]
    proj = pv.show(ax, items, (0.4, -0.8, 0.35), "Motor mount 2 on the cane, with the motor and wheel adapter")
    pv.label(ax, proj, (x_r, -9, cm.RECEIVER_LEN + 60), "cane tube", (-32, 6))
    pv.label(ax, proj, (x_r, -12.5, cm.RECEIVER_LEN + 10), f"sleeve over the tube end,\n{SLEEVE_LEN:.0f} mm deep", (-46, 2))
    pv.label(ax, proj, (x_r, -11, bolt_z()), "M3 cross bolt,\nhead and nut sunk in", (-48, -6))
    pv.label(ax, proj, (-12, -cav_y - WALL, -32), "side walls and back plate\nrun the gearbox's full length", (-52, -34))
    pv.label(ax, proj, (cav_x1 + FRONT_T, -9, -cm.HOLE_FROM_TOP), "2 x M3 into the\ngearbox's own holes", (46, 30))
    pv.label(ax, proj, (cm.BOSS_H + 18, 0, -cm.SHAFT_FROM_TOP), "wheel adapter", (34, -22))

    ax = axes[1]
    keep = box(-120, 120, 0, 100, -120, 200)
    items = [pv.item(mount & keep, "collar"), pv.item(seated & keep, "cradle"), pv.item(tube & keep, "stick"),
             pv.item(motor & keep, "bed"), pv.item(bolt & keep, "strap")]
    top = cm.RECEIVER_LEN
    pv.show(ax, items, (0, -1, 0), "Section on the centre plane (y = 0), shaft pointing right", window=(x_r - 30, 30, -56, top + SLEEVE_LEN + 14), scale=8)
    rear = x_r - BODY_D / 2
    pv.dim(ax, (rear, top), (rear, top + SLEEVE_LEN), f"sleeve {SLEEVE_LEN:.0f}", off=(-6, 0), text_off=(-8, 0))
    pv.dim(ax, (rear, 0), (rear, top), f"socket body {top:.0f}", off=(-6, 0), text_off=(-10, 0))
    pv.dim(ax, (rear, -cm.GB_L), (rear, 0), f"gearbox channel {cm.GB_L:.0f}", off=(-6, 0), text_off=(-13, 0))
    pv.dim(ax, (x_r - BODY_D / 2, top - 6), (x_r + BODY_D / 2, top - 6), f"{BODY_D:.0f}", off=(0, 0))
    pv.note(ax, (x_r - 8, -30), "sloped spine from the\nback plate into the body", (-14, -18))
    pv.note(ax, (back_x + BACK_T / 2, -38), f"back plate, {BACK_T} mm", (20, -14))
    pv.note(ax, (-cm.GB_T / 2, -28), "gearbox", (0, 0))
    pv.note(ax, (-13, 18), "motor can", (0, 0))

    ax = axes[2]
    proj = pv.show(ax, [pv.item(mount, "collar")], (0.55, -0.5, -0.45), "Motor mount 2 alone, seen from the front and below")
    pv.label(ax, proj, (-10, -cav_y - WALL, -40), f"{WALL:.0f} mm side walls", (-46, -20))
    pv.label(ax, proj, (cav_x1 + FRONT_T / 2, 0, -FRONT_H), "front wall", (40, 18))
    pv.label(ax, proj, (x_r, 0, top + SLEEVE_LEN - 4), "sleeve for the tube", (46, 10))
    fig.suptitle("Motor dimensions are from a published JGY-370 outline drawing, not measured on this motor. The tongue socket and cross-bolt position are the same as v4.", fontsize=12, color="crimson")
    fig.savefig(out, dpi=110, bbox_inches="tight", facecolor="white")
    print("wrote", out)


if __name__ == "__main__":
    here = Path(__file__).parent
    out = here / "export"
    out.mkdir(exist_ok=True)
    mount = make_motor_mount_2()
    passed = run_checks(mount)
    export_step(mount, str(out / "motor_mount_2.step"))
    laid = Pos(0, 0, -mount.bounding_box().min.Z) * mount  # prints standing upright, as modelled
    export_stl(laid, str(out / "motor_mount_2.stl"), tolerance=0.01, angular_tolerance=0.1)
    print("exported motor_mount_2 to", out)
    print("all geometric checks passed" if passed else "SOME CHECKS FAILED")
    if "--preview" in sys.argv:
        (here / "previews").mkdir(exist_ok=True)
        render(mount, here / "previews" / "motor_mount_2.png")

"""Cane tip: the keyed coupler with an M3 cross bolt, and its receiver grown into a motor mount.

Run with build123d installed:  python coupler_motor_mount.py            (exports + checks)
                               python coupler_motor_mount.py --preview  (also renders a drawing)
All dimensions are millimetres.

RESEARCH PROTOTYPE. Nothing here has been printed or load tested.

Two printed parts:
  main insert      the PathSense v3 male insert, unchanged except for an M3 hole across its tongue
  motor receiver   the PathSense v3 receiver, unchanged above its base, with the same M3 hole,
                   standing on a band that holds the JGY-370 gearmotor beside it

The coupler geometry is copied from PathSense_Keyed_ShockCord_Coupler_v3.scad.

Motor frame (used for the motor receiver):
  +X  the output shaft's direction; the gearbox's flat front face is x=0
  +Z  along the motor, from the gearbox up into the motor can; the gearbox's top end is z=0
  +Y  across the gearbox's width; the output shaft is at y=0
The receiver stands behind the motor can (at -X), parallel to it, its closed end
level with the top of the gearbox, as in the team's photo.

Motor dimensions marked DRAWING come from a published JGY-370 outline drawing, not
from measuring this motor.
"""

import sys
from math import sqrt
from pathlib import Path

from build123d import (
    Circle,
    Cone,
    Cylinder,
    Plane,
    Pos,
    Rectangle,
    RectangleRounded,
    Rot,
    export_step,
    export_stl,
    extrude,
    loft,
    make_hull,
)

# shared helpers and the preview renderer live with the handle and phone mount
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "handle-phone-mount"))
from walking_stick import box, hex_pocket, overlap, ref_bolt, ref_nut  # noqa: E402

# --- coupler: values from PathSense_Keyed_ShockCord_Coupler_v3.scad ---
TUBE_OD = 18.0
TUBE_ID = 16.0
INSERT_OD = 15.70
MAIN_BARREL_LEN = 42.0
MALE_LEN = 20.0
MALE_W = 10.0
MALE_H = 8.5
MALE_TIP_LEN = 2.0
RECEIVER_LEN = 34.0
SOCKET_DEPTH = 20.5
SOCKET_W = 10.35
SOCKET_H = 8.85
LEAD_DEPTH = 2.0
LEAD_W = 10.85
LEAD_H = 9.35
CORD_HOLE_D = 4.20
GROOVE_COUNT = 3
GROOVE_DEPTH = 0.35
GROOVE_WIDTH = 1.4
GROOVE_START = 7.0
GROOVE_PITCH = 8.0

# --- new: M3 cross bolt through the receiver and the tongue ---
BOLT_D = 3.2  # M3 close fit
BOLT_FROM_MOUTH = 11.7  # measured from the receiver's mouth = from the tongue's root; between two glue grooves
SEAT_DEPTH = 1.0  # flats cut into the round barrel so the head and nut sit square
HEAD_SEAT_D = 6.6
NUT_AF = 5.8  # M3 nut, 5.5 across flats

# --- motor: JGY-370 worm gearmotor (DRAWING) ---
GB_L = 46.0  # gearbox length, along the motor
GB_W = 32.0  # gearbox width
GB_T = 21.0  # gearbox body thickness, without bosses (25.2 over the bosses)
BOSS_H = 2.0  # mounting bosses stand this far off the front face
BOSS_D = 7.4
HOLE_FROM_TOP = 7.0  # the two M3 holes nearest the motor, below the gearbox's top end
HOLE_SPACING_W = 18.0
HOLE_SPACING_L = 33.0
SHAFT_FROM_TOP = 31.0  # output shaft below the gearbox's top end (7 + 33 - 9)
SHAFT_D = 6.0
SHAFT_LEN = 14.0  # beyond the bosses
CAN_D = 24.4
CAN_L = 30.8
CAN_FRONT_INSET = 0.8  # the can sits this far behind the front face, so it overhangs the rear face
CAN_Y = GB_W / 2 - CAN_D / 2  # the can is flush with one side of the gearbox
CAN_SIDE = 0  # -1 or +1 if you know which side the can is flush with; 0 clears both, so either motor fits

# --- mount ---
FIT = 0.3  # clearance per side around the gearbox
CAN_GAP = 0.6  # between the can and the receiver, and between the can and anything printed
WALL = 4.0
FRONT_T = 5.0  # front wall the two motor screws pass through
BAND_H = 16.0  # how far the band reaches down the gearbox
FRONT_H = 13.0  # the front wall is shorter, to stay clear of the wheel adapter's collar
LEDGE_T = 4.0  # shelf the gearbox's top end stops against
FLARE_H = 8.0  # blend from the block up onto the receiver barrel
FLARE_R = 13.0
SCREW_D = 3.4  # M3 clearance for the motor screws


# ---------------------------------------------------------------------------
# coupler, as in the .scad source
# ---------------------------------------------------------------------------


def barrel(length):
    body = extrude(Circle(INSERT_OD / 2), length)
    groove = extrude(Circle(INSERT_OD / 2 + 0.2) - Circle(INSERT_OD / 2 - GROOVE_DEPTH), GROOVE_WIDTH)
    for i in range(GROOVE_COUNT):
        body -= Pos(0, 0, GROOVE_START + i * GROOVE_PITCH) * groove
    return body


def make_main_v3():
    """Male insert exactly as the .scad builds it: barrel at z 0..42, tongue above."""
    straight = MALE_LEN - MALE_TIP_LEN
    tongue = extrude(RectangleRounded(MALE_W, MALE_H, 0.9), straight)
    tongue += loft([
        Plane.XY.offset(straight) * RectangleRounded(MALE_W, MALE_H, 0.9),
        Plane.XY.offset(MALE_LEN) * RectangleRounded(MALE_W - 1.0, MALE_H - 1.0, 0.8),
    ])
    part = barrel(MAIN_BARREL_LEN) + Pos(0, 0, MAIN_BARREL_LEN) * tongue
    total = MAIN_BARREL_LEN + MALE_LEN
    return part - Pos(0, 0, total / 2) * Cylinder(CORD_HOLE_D / 2, total + 1)


def make_receiver_v3():
    """Receiver exactly as the .scad builds it: socket mouth at z=0, closed end at z=34."""
    part = barrel(RECEIVER_LEN)
    part -= Pos(0, 0, -0.1) * extrude(RectangleRounded(SOCKET_W, SOCKET_H, 1.0), SOCKET_DEPTH + 0.2)
    part -= Pos(0, 0, -0.1) * extrude(RectangleRounded(LEAD_W, LEAD_H, 1.1), LEAD_DEPTH)
    return part - Pos(0, 0, RECEIVER_LEN / 2) * Cylinder(CORD_HOLE_D / 2, RECEIVER_LEN + 1)


def cross_bolt_cut(z):
    """M3 hole along Y (through the tongue's thin direction) with a head flat on -Y and a nut pocket on +Y."""
    seat_y = INSERT_OD / 2 - SEAT_DEPTH
    across = Rot(90, 0, 0)
    cut = Pos(0, 0, z) * across * Cylinder(BOLT_D / 2, INSERT_OD + 6)
    cut += Pos(0, -(seat_y + 2), z) * across * Cylinder(HEAD_SEAT_D / 2, 4)
    return cut + Pos(0, seat_y + 4, z) * hex_pocket(NUT_AF, 4)


def make_main_insert():
    """v3 male insert plus the M3 cross hole through its tongue."""
    z = MAIN_BARREL_LEN + BOLT_FROM_MOUTH
    return make_main_v3() - Pos(0, 0, z) * Rot(90, 0, 0) * Cylinder(BOLT_D / 2, MALE_H + 4)


# ---------------------------------------------------------------------------
# motor receiver
# ---------------------------------------------------------------------------


def can_axes():
    """Where the motor can's axis may be: (x, y). Both sides unless CAN_SIDE says which."""
    x = -(CAN_FRONT_INSET + CAN_D / 2)
    return [(x, side * CAN_Y) for side in ((-1, 1) if CAN_SIDE == 0 else (CAN_SIDE,))]


def receiver_x():
    """Receiver axis: at y=0, behind the can with CAN_GAP between them."""
    reach = CAN_D / 2 + INSERT_OD / 2 + CAN_GAP
    return can_axes()[0][0] - sqrt(reach**2 - CAN_Y**2)


def bolt_z():
    return RECEIVER_LEN - BOLT_FROM_MOUTH


def receiver_location():
    """Stands the .scad receiver on its closed end at the receiver axis, mouth up."""
    return Pos(receiver_x(), 0, RECEIVER_LEN) * Rot(180, 0, 0)


def main_location():
    """Main insert fully seated in the receiver: tongue root on the receiver's mouth."""
    return Pos(receiver_x(), 0, RECEIVER_LEN + MAIN_BARREL_LEN) * Rot(180, 0, 0)


def mount_layout():
    cav_x0 = -(GB_T + FIT)  # cavity faces around the gearbox
    cav_x1 = BOSS_H + 0.2  # front wall rests on top of the two bosses
    cav_y = GB_W / 2 + FIT
    can_reach = can_axes()[0][0] - CAN_D / 2 - CAN_GAP  # rear of the can, with clearance
    back_x = min(cav_x0 - WALL, can_reach)
    return cav_x0, cav_x1, cav_y, back_x


def make_motor_receiver():
    cav_x0, cav_x1, cav_y, back_x = mount_layout()
    x_r = receiver_x()
    out_y = cav_y + WALL
    front_x = cav_x1 + FRONT_T

    # block behind the gearbox, running from the back wall to under the receiver
    back_wall = Pos((back_x + cav_x0) / 2, 0) * Rectangle(cav_x0 - back_x, 2 * out_y)
    footprint = make_hull((Pos(x_r, 0) * Circle(INSERT_OD / 2) + back_wall).edges())
    outline = footprint + Pos((back_x + front_x) / 2, 0) * Rectangle(front_x - back_x, 2 * out_y)

    # band around the top of the gearbox, then the shelf its top end stops against
    body = Pos(0, 0, -BAND_H) * extrude(outline, BAND_H + LEDGE_T)
    body -= box(cav_x0, cav_x1, -cav_y, cav_y, -BAND_H - 1, 0)
    body -= box(cav_x1 - 0.01, front_x + 1, -out_y - 1, out_y + 1, -BAND_H - 1, -FRONT_H)

    # blend up onto the receiver barrel, kept inside the block's footprint
    flare = Pos(x_r, 0, FLARE_H / 2) * Cone(FLARE_R, INSERT_OD / 2, FLARE_H)
    body += flare & extrude(footprint, FLARE_H)

    # the receiver itself, unchanged, with the cross-bolt hole
    receiver = make_receiver_v3() - cross_bolt_cut(BOLT_FROM_MOUTH)
    body += receiver_location() * receiver

    # room for the motor can: where it sits, and the path it takes when the motor slides up from below
    for x, y in can_axes():
        body -= Pos(x, y, (CAN_L + 6 - BAND_H - 1) / 2) * Cylinder(CAN_D / 2 + CAN_GAP, CAN_L + 6 + BAND_H + 1)

    # shock-cord hole carried on down through the block
    body -= Pos(x_r, 0, (RECEIVER_LEN - BAND_H) / 2) * Cylinder(CORD_HOLE_D / 2, RECEIVER_LEN + BAND_H + 2)

    # two M3 screws into the gearbox's own threaded bosses
    for side in (1, -1):
        body -= Pos(cav_x1 + FRONT_T / 2, side * HOLE_SPACING_W / 2, -HOLE_FROM_TOP) * Rot(0, 90, 0) * Cylinder(SCREW_D / 2, FRONT_T + 2)
    return body


# ---------------------------------------------------------------------------
# reference geometry, never exported
# ---------------------------------------------------------------------------


def ref_motor(side=-1):
    """JGY-370 from the outline drawing, can flush with the given side."""
    along_x = Rot(0, 90, 0)
    motor = box(-GB_T, 0, -GB_W / 2, GB_W / 2, -GB_L, 0)
    motor += Pos(-(CAN_FRONT_INSET + CAN_D / 2), side * CAN_Y, CAN_L / 2) * Cylinder(CAN_D / 2, CAN_L)
    for z in (-HOLE_FROM_TOP, -HOLE_FROM_TOP - HOLE_SPACING_L):
        for y in (-HOLE_SPACING_W / 2, HOLE_SPACING_W / 2):
            motor += Pos(BOSS_H / 2, y, z) * along_x * Cylinder(BOSS_D / 2, BOSS_H)
    motor += Pos(BOSS_H / 2, 0, -SHAFT_FROM_TOP) * along_x * Cylinder(6.0, BOSS_H)  # boss around the shaft
    motor += Pos(-GB_T - 1.1, 0, -SHAFT_FROM_TOP) * along_x * Cylinder(5.0, 2.2)  # rear bearing boss
    motor += Pos((BOSS_H + SHAFT_LEN) / 2, 0, -SHAFT_FROM_TOP) * along_x * Cylinder(SHAFT_D / 2, BOSS_H + SHAFT_LEN)
    return motor


def ref_tube(length=70.0):
    """End of the cane tube, with the main insert's barrel glued flush inside it."""
    tube = Cylinder(TUBE_OD / 2, length) - Cylinder(TUBE_ID / 2, length)
    return Pos(receiver_x(), 0, RECEIVER_LEN + length / 2) * tube


def ref_cross_bolt():
    """M3 x 20 through receiver and tongue, with its nut."""
    seat_y = INSERT_OD / 2 - SEAT_DEPTH
    bolt = Pos(receiver_x(), seat_y, bolt_z()) * ref_bolt(3, 20, 5.5, 3)
    nut = Pos(receiver_x(), -seat_y, bolt_z()) * ref_nut(5.5, 2.4, 3)
    return bolt, nut


def ref_motor_screws(length=12.0):
    """Two M3 screws through the front wall into the gearbox bosses."""
    _, cav_x1, _, _ = mount_layout()
    out = []
    for side in (1, -1):
        y, z = side * HOLE_SPACING_W / 2, -HOLE_FROM_TOP
        screw = Pos(cav_x1 + FRONT_T - length / 2, y, z) * Rot(0, 90, 0) * Cylinder(1.5, length)
        out.append(screw + Pos(cav_x1 + FRONT_T + 1.5, y, z) * Rot(0, 90, 0) * Cylinder(2.75, 3))
    return out


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------


def run_checks(parts):
    ok = True

    def report(passed, text):
        nonlocal ok
        ok &= bool(passed)
        print(f"  [{'ok' if passed else 'FAIL'}] {text}")

    mount, main = parts["PathSense_Keyed_ShockCord_MotorReceiver_v4"], parts["PathSense_Keyed_ShockCord_Main_v4"]
    for name, part in parts.items():
        bb = part.bounding_box().size
        report(part.is_valid and len(part.solids()) == 1, f"{name}: {bb.X:.1f} x {bb.Y:.1f} x {bb.Z:.1f} mm, {part.volume / 1000:.2f} cm3, valid={part.is_valid}, solids={len(part.solids())}")

    seated = main_location() * main
    report(overlap(mount, seated) < 1e-6, "main insert's tongue seats fully in the receiver socket without collision")
    bolt, nut = ref_cross_bolt()
    report(overlap(bolt, mount) < 1e-6 and overlap(bolt, seated) < 1e-6 and overlap(nut, mount) < 1e-6,
           "an M3 x 20 passes straight through the receiver and the tongue; head and nut sit in their seats")

    sides = (-1, 1) if CAN_SIDE == 0 else (CAN_SIDE,)
    for side in sides:
        motor = ref_motor(side)
        label = f"motor, can flush with the {'-Y' if side < 0 else '+Y'} side"
        report(overlap(motor, mount) < 1e-6, f"{label}: sits in the mount without collision")
        stuck = [d for d in range(2, 61, 2) if overlap(Pos(0, 0, -d) * motor, mount) > 1e-6]
        report(not stuck, f"{label}: slides up into the mount from below" + (f" (collides when {stuck[0]} mm short)" if stuck else ""))
        report(overlap(motor, seated) < 1e-6 and overlap(motor, ref_tube()) < 1e-6, f"{label}: clears the main insert and the tube")
        report(overlap(bolt, motor) < 1e-6 and overlap(nut, motor) < 1e-6, f"{label}: cross bolt and nut are clear of the motor")
    screws = ref_motor_screws()
    report(all(overlap(s, mount) < 1e-6 for s in screws), "both motor screws pass through the front wall")

    # the wheel adapter's collar and its clamp screw head sweep this disc around the shaft
    sweep = Pos(BOSS_H + 1 + 4.5, 0, -SHAFT_FROM_TOP) * Rot(0, 90, 0) * Cylinder(16.0, 9)
    gap = mount.distance_to(sweep)
    report(overlap(sweep, mount) < 1e-6, f"wheel adapter's collar and clamp screw (16 mm radius) pass {gap:.1f} mm below the mount")

    cav_x0, cav_x1, cav_y, back_x = mount_layout()
    print(f"  receiver axis is {-receiver_x():.1f} mm behind the gearbox's front face and {CAN_GAP} mm off the motor can")
    print(f"  cross bolt is {bolt_z():.1f} mm above the top of the gearbox, running along Y")
    return ok


def compare_with_stl(name, part, path):
    """Volume and size of a rebuilt v3 part against the team's STL."""
    try:
        import numpy as np
        from stl import mesh
    except ImportError:
        print(f"  [skip] {name}: numpy-stl not installed")
        return
    if not Path(path).exists():
        print(f"  [skip] {name}: {path} not found")
        return
    m = mesh.Mesh.from_file(str(path))
    pts = m.vectors.reshape(-1, 3)
    size = pts.max(0) - pts.min(0)
    volume = abs(float(m.get_mass_properties()[0]))
    bb = part.bounding_box().size
    diff = 100 * (part.volume - volume) / volume
    print(f"  {name}: STL {size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f} mm, {volume:.1f} mm3 | "
          f"rebuilt {bb.X:.2f} x {bb.Y:.2f} x {bb.Z:.2f} mm, {part.volume:.1f} mm3 ({diff:+.2f}%)")


def render(parts, out):
    import matplotlib.pyplot as plt

    import preview as pv

    mount, main = parts["PathSense_Keyed_ShockCord_MotorReceiver_v4"], parts["PathSense_Keyed_ShockCord_Main_v4"]
    seated = main_location() * main
    motor, tube = ref_motor(-1), ref_tube()
    bolt, nut = ref_cross_bolt()
    screws = ref_motor_screws()
    cav_x0, cav_x1, cav_y, back_x = mount_layout()
    x_r = receiver_x()

    fig, axes = plt.subplots(1, 3, figsize=(22, 10))
    items = [pv.item(mount, "collar"), pv.item(seated, "cradle"), pv.item(tube, "stick"), pv.item(motor, "bed"),
             pv.item([bolt, nut] + screws, "strap")]
    proj = pv.show(axes[0], items, (0.35, -0.8, 0.35), "Assembled: tube, main insert, motor receiver, motor")
    pv.label(axes[0], proj, (x_r, -8, 60), "cane tube", (-28, 8))
    pv.label(axes[0], proj, (x_r, -6, RECEIVER_LEN + 3), "main insert\n(glued in the tube)", (-36, -2))
    pv.label(axes[0], proj, (x_r, -9, bolt_z()), "M3 cross bolt:\nhead one side,\nnut the other", (-36, -14))
    pv.label(axes[0], proj, (x_r - 4, -10, -8), "motor receiver", (-30, -22))
    pv.label(axes[0], proj, (cav_x1 + ws_front(), -9, -HOLE_FROM_TOP), "2 x M3 into the\ngearbox's own holes", (34, 22))
    pv.label(axes[0], proj, (BOSS_H + 10, 0, -SHAFT_FROM_TOP), "output shaft\n(wheel adapter goes here)", (30, -18))
    pv.label(axes[0], proj, (-13, -16, 18), "motor", (34, 22))

    ax = axes[1]
    keep = box(-100, 100, 0, 100, -100, 150)
    items = [pv.item(mount & keep, "collar"), pv.item(seated & keep, "cradle"), pv.item(tube & keep, "stick"),
             pv.item(motor & keep, "bed"), pv.item(bolt & keep, "strap")]
    pv.show(ax, items, (0, -1, 0), "Section on the centre plane (y = 0), shaft pointing right", window=(x_r - 22, 26, -52, 62), scale=9)
    pv.dim(ax, (x_r, RECEIVER_LEN), (0, RECEIVER_LEN), f"receiver axis to gearbox front {-x_r:.1f}", off=(0, 22))
    pv.dim(ax, (x_r - INSERT_OD / 2, 0), (x_r - INSERT_OD / 2, RECEIVER_LEN), f"receiver {RECEIVER_LEN:.0f}\n(as v3)", off=(-5, 0), text_off=(-8, 0))
    pv.dim(ax, (x_r - INSERT_OD / 2, -BAND_H), (x_r - INSERT_OD / 2, 0), f"band {BAND_H:.0f}", off=(-5, 0), text_off=(-7, 0))
    pv.note(ax, (x_r, bolt_z()), f"M3 hole {BOLT_D} dia through receiver\nand tongue, {BOLT_FROM_MOUTH} below the mouth", (2, -36))
    pv.note(ax, (cav_x1 + FRONT_T / 2, -FRONT_H + 2), f"front wall {FRONT_T:.0f} thick,\nsits on the bosses", (10, -22))
    pv.note(ax, (-GB_T / 2, -25), "gearbox", (0, 0))
    pv.note(ax, (-13, 18), "motor can", (0, 0))

    ax = axes[2]
    pv.show(ax, [pv.item(mount, "collar")], (0, 0, 1), "Motor receiver from above", up=(0, 1, 0), margin=14, scale=9)
    out_y = cav_y + WALL
    pv.dim(ax, (cav_x0, -out_y), (cav_x1, -out_y), f"gearbox pocket {cav_x1 - cav_x0:.1f}", off=(0, -6))
    pv.dim(ax, (cav_x1 + FRONT_T, -cav_y), (cav_x1 + FRONT_T, cav_y), f"{2 * cav_y:.1f}", off=(6, 0), text_off=(5, 0))
    pv.dim(ax, (back_x, out_y), (cav_x1 + FRONT_T, out_y), f"band {cav_x1 + FRONT_T - back_x:.1f} x {2 * out_y:.1f}", off=(0, 6))
    pv.note(ax, (x_r, 0), "receiver socket\n(as v3)", (-6, 26))
    pv.note(ax, (-13, 0), "cut-outs for the motor can,\neither way round", (4, -34))
    fig.suptitle("Motor dimensions are from a published JGY-370 outline drawing, not measured on this motor. Coupler geometry is copied from the v3 .scad.", fontsize=12, color="crimson")
    fig.savefig(out, dpi=110, bbox_inches="tight", facecolor="white")
    print("wrote", out)


def ws_front():
    return FRONT_T


def printable_parts():
    return {
        "PathSense_Keyed_ShockCord_MotorReceiver_v4": make_motor_receiver(),
        "PathSense_Keyed_ShockCord_Main_v4": make_main_insert(),
    }


if __name__ == "__main__":
    here = Path(__file__).parent
    out = here  # next to the v3 files
    parts = printable_parts()
    passed = run_checks(parts)
    for name, part in parts.items():
        export_step(part, str(out / f"{name}.step"))
        laid = Pos(0, 0, -part.bounding_box().min.Z) * part  # both print upright, as modelled
        export_stl(laid, str(out / f"{name}.stl"), tolerance=0.01, angular_tolerance=0.1)
    print("exported", ", ".join(parts), "to", out)
    print("all geometric checks passed" if passed else "SOME CHECKS FAILED")
    stls = [a for a in sys.argv[1:] if a.lower().endswith(".stl")]
    if stls:
        print("rebuilt v3 parts against the team's STL files")
        for path in stls:
            which = ("receiver", make_receiver_v3()) if "receiver" in path.lower() else ("main", make_main_v3())
            compare_with_stl(which[0], which[1], path)
    if "--preview" in sys.argv:
        render(parts, here / "PathSense_MotorReceiver_v4_preview.png")

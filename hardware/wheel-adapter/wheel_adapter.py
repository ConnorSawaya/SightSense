"""Printed hub adapter: omni wheel's hex socket onto the JGY-370 gearmotor's 6 mm D-shaft.

Run with build123d installed:  python wheel_adapter.py            (exports + checks)
                               python wheel_adapter.py --preview  (also renders a drawing)
All dimensions are millimetres. The adapter's axis is +Z, z=0 at the gearbox end.

RESEARCH PROTOTYPE. Not load tested.

Shape, from the gearbox outwards: hexagonal collar, 12 mm hex that drives the
wheel, then a 10 mm round pilot that goes inwards through the wheel's centre hole.

How it carries load
  torque   D-shaped bore on the shaft's flat, then the hex into the wheel
  bending  the steel shaft runs inside the collar and the first part of the hex;
           beyond the shaft tip a steel M3 screw runs down the middle of solid
           plastic (no slots are cut into the hex or the pilot)
  pull-off an M3 screw and captured nut clamp onto the shaft's flat. The wheel
           screw's head sits at the bottom of the bore, trapped by the shaft; its
           nut goes on the far side of the wheel, in the open, over the cap.

v3 changes, after the first print: every screw hole is larger, the bore is
matched to the published shaft drawing and has a proper seat for the wheel
screw's head, the collar is bigger with the clamp screw's head sunk into it,
and the part is exported standing upright so the bore prints true.

v4 changes: the nut slot sits further out from the bore, and the wall between
them is flat on both faces. To allow that the bore is D-shaped right from its
mouth, so the adapter now starts where the shaft's flat starts.

v5 changes: the nut slot is thicker and sits a little further out again.

Shaft sizes marked DRAWING come from a published JGY-370 outline drawing.
"""

import sys
from pathlib import Path

from build123d import (
    Axis,
    Circle,
    Cone,
    Cylinder,
    Pos,
    Rectangle,
    RegularPolygon,
    Rot,
    chamfer,
    export_step,
    export_stl,
    extrude,
    fillet,
)

# shared helpers and the preview renderer live with the handle and phone mount
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "handle-phone-mount"))
from walking_stick import box, hex_pocket, overlap  # noqa: E402

# --- motor shaft: JGY-370 worm gearmotor (DRAWING) ---
SHAFT_D = 6.0
SHAFT_ACROSS_FLAT = 5.4  # flat to the opposite side; one seller's photo says 5.5, and the bore takes either
SHAFT_LEN = 14.0  # beyond the gearbox's bosses
SHAFT_FLAT_LEN = 12.0  # the flat stops 2 mm short of the bosses
SHAFT_FIT = 0.3  # slack on the bore diameter
FLAT_FIT = 0.25  # slack on the flat; the clamp screw takes it up
GEARBOX_GAP = SHAFT_LEN - SHAFT_FLAT_LEN + 0.3  # adapter starts just past the round base of the shaft, on the flat

# --- wheel hub ---
HEX_AF = 12.0  # measured: wheel's hex socket across flats
HEX_FIT = 0.2  # total slack between the printed hex and the socket
HEX_LEN = 12.0  # longer than the socket is deep on purpose: the step to the pilot seats in the socket
PILOT_HOLE_D = 10.0  # measured: round hole inwards of the hex
PILOT_FIT = 0.2
PILOT_LEN = 10.0  # UNCONFIRMED: must be shorter than the round hole is deep

# --- body ---
COLLAR_AF = 28.0  # hexagonal collar across flats
COLLAR_CORNER_R = 3.0  # rounded corners, to pass under the motor receiver
COLLAR_LEN = 8.0
END_CHAMFER = 0.8

# --- M3 hardware ---
SCREW_D = 3.6  # M3 with room to spare: screws would not go through 3.2 mm holes as printed
NUT_AF = 5.8  # slot width for an M3 nut (5.5 across flats)
NUT_T = 3.2  # slot thickness for an M3 nut (2.4 thick), with room to drop it in
HEAD_D = 5.5  # M3 socket-head cap screw
HEAD_H = 3.0
HEAD_PASS_D = 5.9  # round passage down the bore for the wheel screw's head
NUT_WALL_IN = 3.75  # plastic between the bore's flat and the clamp nut's slot
NUT_WALL_OUT = 2.0  # plastic between the slot and the screw head; an M3 x 10 leaves room for no more
CLAMP_HEAD_D = 6.2  # counterbore that sinks the clamp screw's head into the collar

# --- far-side cap ---
CAP_D = 20.0
CAP_T = 3.0
CAP_HEX_LEN = 4.0


def layout():
    shaft_in = SHAFT_LEN - GEARBOX_GAP  # how far the shaft reaches into the adapter
    bore_depth = shaft_in + HEAD_H + 0.3  # room for the wheel screw's head past the shaft tip
    hex_end = COLLAR_LEN + HEX_LEN
    return shaft_in, bore_depth, hex_end


def clamp_layout():
    """Height of the clamp screw, inner face of its nut slot, where the bore's flat is,
    and the floor of the head counterbore (the last three measured from the axis)."""
    clamp_z = COLLAR_LEN / 2
    bore_flat_x = SHAFT_ACROSS_FLAT - SHAFT_D / 2 + FLAT_FIT
    slot_x = bore_flat_x + NUT_WALL_IN
    return clamp_z, slot_x, bore_flat_x, slot_x + NUT_T + NUT_WALL_OUT


def collar_corner_radius():
    """How far the collar's rounded corners reach from the axis."""
    return COLLAR_AF / 3**0.5 - COLLAR_CORNER_R * (2 / 3**0.5 - 1)


def d_profile(extra=0.0, flat_extra=None):
    """Shaft cross-section, flat facing +X. `extra` grows the radius, `flat_extra` the flat."""
    flat_extra = extra if flat_extra is None else flat_extra
    r = SHAFT_D / 2 + extra
    flat_x = SHAFT_ACROSS_FLAT - SHAFT_D / 2 + flat_extra
    return Circle(r) & Pos(flat_x - r, 0) * Rectangle(2 * r, 2 * r)


def head_pass_x():
    """Centre of the round passage for the wheel screw's head: it just touches the bore's flat."""
    return clamp_layout()[2] - HEAD_PASS_D / 2


def bore_profile():
    """D for the shaft, plus a round passage opposite the flat for the wheel screw's head.
    The passage leaves two edges for the shaft to seat on when the clamp screw pushes it back."""
    return d_profile(SHAFT_FIT / 2, FLAT_FIT) + Pos(head_pass_x(), 0) * Circle(HEAD_PASS_D / 2)


def hexagon(across_flats):
    """Hexagon with flats facing +Y and -Y."""
    return RegularPolygon(across_flats / 3**0.5, 6)


def make_wheel_adapter():
    shaft_in, bore_depth, hex_end = layout()
    clamp_z, slot_x, bore_flat_x, seat_r = clamp_layout()
    assert hex_end - bore_depth >= 2.0, "HEX_LEN is too short: the bore would run into the pilot"
    end = hex_end + PILOT_LEN
    bore_r = (SHAFT_D + SHAFT_FIT) / 2

    collar = hexagon(COLLAR_AF)
    body = extrude(fillet(collar.vertices(), COLLAR_CORNER_R), COLLAR_LEN)
    body += Pos(0, 0, COLLAR_LEN) * extrude(hexagon(HEX_AF - HEX_FIT), HEX_LEN)
    pilot = Pos(0, 0, hex_end) * extrude(Circle((PILOT_HOLE_D - PILOT_FIT) / 2), PILOT_LEN)
    body += chamfer(pilot.edges().group_by(Axis.Z)[-1], END_CHAMFER)

    # bore: D-shaped from the mouth, so the wall under the nut slot is flat on both
    # faces, then a round pocket past the shaft tip where the wheel screw's head sits centred
    body -= extrude(bore_profile(), shaft_in + 0.5)
    body -= Pos(0, 0, shaft_in) * extrude(Circle(bore_r), bore_depth - shaft_in)
    lead_in = Pos(0, 0, 0.3) * Cone(bore_r + 0.6, bore_r, 0.6)
    body -= lead_in & box(-10, bore_flat_x, -10, 10, -1, 1)  # on the round side only; the flat stays flat

    # clamp onto the shaft's flat: M3 screw from +X through a captured nut, head sunk into the collar
    reach = COLLAR_AF  # well past the collar's corner
    body -= Pos((bore_flat_x + reach) / 2, 0, clamp_z) * Rot(0, 90, 0) * Cylinder(SCREW_D / 2, reach - bore_flat_x)
    body -= box(slot_x, slot_x + NUT_T, -NUT_AF / 2, NUT_AF / 2, -1, clamp_z + NUT_AF / 2)
    body -= Pos((seat_r + reach) / 2, 0, clamp_z) * Rot(0, 90, 0) * Cylinder(CLAMP_HEAD_D / 2, reach - seat_r)

    # wheel screw: its shank runs out through the pilot
    body -= Pos(0, 0, (bore_depth + end) / 2) * Cylinder(SCREW_D / 2, end - bore_depth + 2)
    return body


def make_wheel_cap():
    """Far-side cap: a flange over the wheel's hub with a short hex into the far socket.
    The wheel screw's nut tightens against its outer face."""
    cap = extrude(Circle(CAP_D / 2), CAP_T)
    cap = chamfer(cap.edges().group_by(Axis.Z)[0], 0.8)
    stub = Pos(0, 0, CAP_T) * extrude(hexagon(HEX_AF - HEX_FIT), CAP_HEX_LEN)
    cap += chamfer(stub.edges().group_by(Axis.Z)[-1], END_CHAMFER)
    return cap - Pos(0, 0, (CAP_T + CAP_HEX_LEN) / 2) * Cylinder(SCREW_D / 2, CAP_T + CAP_HEX_LEN + 2)


def make_fit_test():
    """Short hex and pilot with the D-bore through the hex: try it on the shaft's
    tip, and in the wheel's hex socket and round hole."""
    stub = extrude(hexagon(HEX_AF - HEX_FIT), 7)
    pilot = Pos(0, 0, 7) * extrude(Circle((PILOT_HOLE_D - PILOT_FIT) / 2), 5)
    stub += chamfer(pilot.edges().group_by(Axis.Z)[-1], END_CHAMFER)
    stub -= Pos(0, 0, -1) * extrude(bore_profile(), 8)
    return stub - Pos(0, 0, 9) * Cylinder(SCREW_D / 2, 8)


def as_printed(part):
    """Standing on the collar's gearbox face: the bore and the wheel-screw hole print vertically."""
    return Pos(0, 0, -part.bounding_box().min.Z) * part


# --- reference geometry, never exported ---


def ref_shaft():
    """Motor shaft: round near the gearbox, flat over the outer SHAFT_FLAT_LEN."""
    round_len = SHAFT_LEN - SHAFT_FLAT_LEN
    shaft = extrude(Circle(SHAFT_D / 2), round_len) + Pos(0, 0, round_len) * extrude(d_profile(), SHAFT_FLAT_LEN)
    return Pos(0, 0, -GEARBOX_GAP) * shaft


def wheel_screw_len():
    """Wheel screw length used for the drawings."""
    return 35.0


def ref_screws(clamp_len=10.0):
    """Clamp screw bearing on the shaft's flat, and the wheel screw seated at the bottom of the bore."""
    shaft_in, bore_depth, hex_end = layout()
    clamp_z = clamp_layout()[0]
    flat_x = SHAFT_ACROSS_FLAT - SHAFT_D / 2  # tip of the clamp screw rests on the shaft's flat
    along_x = Rot(0, 90, 0)
    clamp = Pos(flat_x + clamp_len / 2, 0, clamp_z) * along_x * Cylinder(1.5, clamp_len)
    clamp += Pos(flat_x + clamp_len + HEAD_H / 2, 0, clamp_z) * along_x * Cylinder(HEAD_D / 2, HEAD_H)
    length = wheel_screw_len()
    wheel = Pos(0, 0, bore_depth - HEAD_H / 2) * Cylinder(HEAD_D / 2, HEAD_H)
    wheel += Pos(0, 0, bore_depth + length / 2) * Cylinder(1.5, length)
    return clamp, wheel


def run_checks(parts):
    ok = True

    def report(passed, text):
        nonlocal ok
        ok &= bool(passed)
        print(f"  [{'ok' if passed else 'FAIL'}] {text}")

    adapter = parts["wheel_adapter"]
    shaft_in, bore_depth, hex_end = layout()
    for name, part in parts.items():
        bb = part.bounding_box().size
        report(part.is_valid and len(part.solids()) == 1, f"{name}: {bb.X:.1f} x {bb.Y:.1f} x {bb.Z:.1f} mm, {part.volume / 1000:.2f} cm3, valid={part.is_valid}, solids={len(part.solids())}")
    report(overlap(adapter, ref_shaft()) < 1e-6, f"shaft (round base, then flat) enters the bore without collision, {shaft_in:.1f} mm deep")
    clamp, wheel = ref_screws()
    report(overlap(adapter, wheel) < 1e-6, "wheel screw sits centred at the bottom of the bore, head and shank clear")
    report(overlap(adapter, clamp) < 1e-6, "M3 x 10 clamp screw reaches the shaft's flat through its hole and counterbore")

    # the wheel screw's head travels down the passage beside the flat, then centres in its pocket
    head = Cylinder(HEAD_D / 2, HEAD_H)
    stuck = [z for z in range(0, int(shaft_in)) if overlap(adapter, Pos(head_pass_x(), 0, z + HEAD_H / 2) * head) > 1e-6]
    margin = (HEAD_PASS_D - HEAD_D) / 2
    report(not stuck, f"a {HEAD_D} mm screw head slides down the bore with {margin:.2f} mm to spare each side")

    clamp_z, slot_x, bore_flat_x, seat_r = clamp_layout()
    flat_x = SHAFT_ACROSS_FLAT - SHAFT_D / 2
    under_head = flat_x + 10
    report(under_head - seat_r >= 0.6 and under_head + HEAD_H <= collar_corner_radius(),
           f"M3 x 10 clamp screw: presses the flat with its head {under_head - seat_r:.1f} mm above the counterbore floor and {collar_corner_radius() - under_head - HEAD_H:.1f} mm below the collar's corner")
    report(slot_x - bore_flat_x >= 2.5 and seat_r - slot_x - NUT_T >= 2.0,
           f"nut slot is {NUT_T} mm thick, with {slot_x - bore_flat_x:.2f} mm of plastic towards the bore and {seat_r - slot_x - NUT_T:.1f} mm towards the screw head, flat faces on both")
    wall_hex = (HEX_AF - HEX_FIT) / 2 - (SHAFT_D + SHAFT_FIT) / 2
    report(wall_hex >= 2.5, f"{wall_hex:.2f} mm of plastic between the bore and the hex flats")
    report(hex_end - bore_depth >= 2.0, f"{hex_end - bore_depth:.1f} mm of solid hex under the screw head before the pilot starts")
    print(f"  bore: {SHAFT_D + SHAFT_FIT:.1f} dia, {(SHAFT_D + SHAFT_FIT) / 2 + bore_flat_x:.2f} across the flat, for a {SHAFT_D:.0f} mm shaft that is {SHAFT_ACROSS_FLAT} across its flat")
    print(f"  adapter starts {GEARBOX_GAP:.1f} mm off the gearbox bosses, where the shaft's flat begins; the shaft goes in {shaft_in:.1f} mm")
    print(f"  screw holes are {SCREW_D} mm; collar is {COLLAR_AF:.0f} across flats and sweeps a {collar_corner_radius():.1f} mm radius")
    return ok


def render(adapter, out):
    import matplotlib.pyplot as plt

    import preview as pv

    shaft_in, bore_depth, hex_end = layout()
    clamp_z, slot_x, bore_flat_x, seat_r = clamp_layout()
    end = hex_end + PILOT_LEN
    shaft, (clamp, wheel) = ref_shaft(), ref_screws()
    fig, axes = plt.subplots(1, 3, figsize=(22, 9))
    cut_y = box(-50, 50, 0, 50, -50, 90)
    items = [pv.item(adapter & cut_y, "collar"), pv.item(shaft & cut_y, "stick"), pv.item(clamp & cut_y, "hardware"), pv.item(wheel & cut_y, "hardware")]
    ax = axes[0]
    pv.show(ax, items, (0, -1, 0), "Section through the clamp screw (shaft dark grey, screws light)", margin=17, scale=18)
    c = collar_corner_radius()
    pv.dim(ax, (-c, 0), (-c, COLLAR_LEN), f"collar {COLLAR_LEN:.0f}", off=(-3, 0), text_off=(-4.5, 0))
    pv.dim(ax, (-c, COLLAR_LEN), (-c, hex_end), f"hex {HEX_LEN:.0f}", off=(-3, 0), text_off=(-4, 0))
    pv.dim(ax, (-c, hex_end), (-c, end), f"pilot {PILOT_LEN:.0f}", off=(-3, 0), text_off=(-4.5, 0))
    pv.dim(ax, (-c, 0), (-c, shaft_in), f"shaft goes in {shaft_in:.1f}", off=(-12, 0), text_off=(-7.5, 0))
    pv.dim(ax, (-c, 0), (c, 0), f"collar {COLLAR_AF:.0f} across flats ({2 * c:.1f} over the corners)", off=(0, -5))
    pv.note(ax, (seat_r + 2, clamp_z), f"M3 x 10 clamp screw,\nhead sunk in a {CLAMP_HEAD_D} mm\ncounterbore", (8, -16))
    pv.note(ax, (slot_x + NUT_T / 2, 1.0), f"nut slot, {NUT_T} mm thick", (21, 9))
    pv.note(ax, (0, bore_depth - HEAD_H / 2), "wheel screw's head, centred\nin its own round pocket", (20, 18))
    pv.note(ax, (1.8, end + 12), f"{SCREW_D} mm hole; to the far side of the\nwheel: cap, then the M3 nut", (14, 0))

    ax = axes[1]
    pv.show(ax, [pv.item(adapter, "collar"), pv.item(shaft & box(-50, 50, -50, 50, 0.05, 90), "stick")], (0, 0, -1), "Gearbox end, seen square on (shaft in dark grey)", up=(1, 0, 0), window=(-9, 9, -8, 14), scale=38)
    bore_r = (SHAFT_D + SHAFT_FIT) / 2
    # this view looks up the axis: across the page is -Y, up the page is +X
    pv.dim(ax, (bore_r, bore_flat_x), (bore_r, slot_x), f"{slot_x - bore_flat_x:.1f} wall,\nflat both faces", off=(2.6, 0), text_off=(3.0, 0))
    pv.dim(ax, (-NUT_AF / 2, slot_x + NUT_T), (NUT_AF / 2, slot_x + NUT_T), f"nut slot {NUT_AF} x {NUT_T}", off=(0, 2.0))
    pv.dim(ax, (-bore_r, -bore_r), (-bore_r, bore_flat_x), f"{bore_r + bore_flat_x:.2f} across\nthe flat", off=(-2.2, 0), text_off=(-2.6, 0))
    pv.note(ax, (0, bore_flat_x), "bore's flat, straight from the mouth", (-1.5, -11.5))

    ax = axes[2]
    pv.show(ax, [pv.item(adapter, "collar")], (0.5, -0.45, -0.75), "wheel_adapter, gearbox end towards you", margin=6, scale=18)
    fig.suptitle(f"Measured: wheel hex {HEX_AF:.0f} mm, round hole {PILOT_HOLE_D:.0f} mm.   From the JGY-370 drawing: shaft {SHAFT_D:.0f} dia, {SHAFT_ACROSS_FLAT} across the flat, {SHAFT_LEN:.0f} long, flat {SHAFT_FLAT_LEN:.0f} long.   UNCONFIRMED: pilot length {PILOT_LEN:.0f} mm.", fontsize=12, color="crimson")
    fig.savefig(out, dpi=110, bbox_inches="tight", facecolor="white")
    print("wrote", out)


def printable_parts():
    return {"wheel_adapter": make_wheel_adapter(), "wheel_cap": make_wheel_cap(), "wheel_adapter_fit_test": make_fit_test()}


if __name__ == "__main__":
    here = Path(__file__).parent
    out = here / "export"
    out.mkdir(exist_ok=True)
    parts = printable_parts()
    passed = run_checks(parts)
    for name, part in parts.items():
        export_step(part, str(out / f"{name}.step"))
        export_stl(as_printed(part), str(out / f"{name}.stl"), tolerance=0.01, angular_tolerance=0.1)
    print("exported", ", ".join(parts), "to", out)
    print("all geometric checks passed" if passed else "SOME CHECKS FAILED")
    if "--preview" in sys.argv:
        (here / "previews").mkdir(exist_ok=True)
        render(parts["wheel_adapter"], here / "previews" / "wheel_adapter.png")

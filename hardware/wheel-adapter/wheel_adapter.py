"""Printed hub adapter: omni wheel's hex socket onto the JGY-370 gearmotor's 6 mm D-shaft.

Run with build123d installed:  python wheel_adapter.py            (exports + checks)
                               python wheel_adapter.py --preview  (also renders a drawing)
All dimensions are millimetres. The adapter's axis is +Z, z=0 at the gearbox end.

RESEARCH PROTOTYPE. Nothing here has been printed or load tested.

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

Values marked UNCONFIRMED are read off photos or seller listings, not measured.
"""

import sys
from pathlib import Path

from build123d import (
    Axis,
    Circle,
    Cylinder,
    Pos,
    Rectangle,
    RegularPolygon,
    Rot,
    chamfer,
    export_step,
    export_stl,
    extrude,
)

# shared helpers and the preview renderer live with the handle and phone mount
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "handle-phone-mount"))
from walking_stick import box, hex_pocket, overlap  # noqa: E402

# --- motor shaft: JGY-370 worm gearmotor ---
SHAFT_D = 6.0  # seller listings agree on 6 mm
SHAFT_ACROSS_FLAT = 5.5  # UNCONFIRMED: flat to the opposite side of the shaft
SHAFT_LEN = 14.0  # UNCONFIRMED: listings say 14 to 15 mm
SHAFT_FLAT_LEN = 11.5  # UNCONFIRMED: the flat stops short of the gearbox; one listing says 11.5
SHAFT_FIT = 0.2  # slack on the bore diameter
FLAT_FIT = 0.15  # slack on the flat; also lets the wheel screw's head pass down the bore
GEARBOX_GAP = 1.0  # adapter stops this far short of the gearbox face

# --- wheel hub ---
HEX_AF = 12.0  # measured: wheel's hex socket across flats
HEX_FIT = 0.2  # total slack between the printed hex and the socket
HEX_LEN = 12.0  # longer than the socket is deep on purpose: the step to the pilot seats in the socket
PILOT_HOLE_D = 10.0  # measured: round hole inwards of the hex
PILOT_FIT = 0.2
PILOT_LEN = 10.0  # UNCONFIRMED: must be shorter than the round hole is deep

# --- body ---
COLLAR_AF = 22.0  # hexagonal collar, so the part can lie on a flat to print
COLLAR_LEN = 8.0
END_CHAMFER = 0.8

# --- M3 hardware ---
SCREW_D = 3.2  # M3 close fit
NUT_AF = 5.8  # slot width for an M3 nut (5.5 across flats)
NUT_T = 2.7  # slot thickness for an M3 nut (2.4 thick)
HEAD_D = 5.5  # M3 socket-head cap screw
HEAD_H = 3.0

# --- far-side cap ---
CAP_D = 20.0
CAP_T = 3.0
CAP_HEX_LEN = 4.0


def layout():
    shaft_in = SHAFT_LEN - GEARBOX_GAP  # how far the shaft reaches into the adapter
    bore_depth = shaft_in + HEAD_H + 0.3  # room for the wheel screw's head past the shaft tip
    hex_end = COLLAR_LEN + HEX_LEN
    return shaft_in, bore_depth, hex_end


def d_profile(extra=0.0, flat_extra=None):
    """Shaft cross-section, flat facing +X. `extra` grows the radius, `flat_extra` the flat."""
    flat_extra = extra if flat_extra is None else flat_extra
    r = SHAFT_D / 2 + extra
    flat_x = SHAFT_ACROSS_FLAT - SHAFT_D / 2 + flat_extra
    return Circle(r) & Pos(flat_x - r, 0) * Rectangle(2 * r, 2 * r)


def bore_profile():
    return d_profile(SHAFT_FIT / 2, FLAT_FIT)


def hexagon(across_flats):
    """Hexagon with flats facing +Y and -Y."""
    return RegularPolygon(across_flats / 3**0.5, 6)


def make_wheel_adapter():
    shaft_in, bore_depth, hex_end = layout()
    assert hex_end - bore_depth >= 2.0, "HEX_LEN is too short: the bore would run into the pilot"
    end = hex_end + PILOT_LEN

    body = extrude(hexagon(COLLAR_AF), COLLAR_LEN)
    body += Pos(0, 0, COLLAR_LEN) * extrude(hexagon(HEX_AF - HEX_FIT), HEX_LEN)
    pilot = Pos(0, 0, hex_end) * extrude(Circle((PILOT_HOLE_D - PILOT_FIT) / 2), PILOT_LEN)
    body += chamfer(pilot.edges().group_by(Axis.Z)[-1], END_CHAMFER)

    # bore: D-shaped where the shaft has its flat, round near the gearbox where it does not
    round_len = max(SHAFT_LEN - SHAFT_FLAT_LEN - GEARBOX_GAP, 0) + 0.5
    body -= extrude(bore_profile(), bore_depth)
    body -= extrude(Circle((SHAFT_D + SHAFT_FIT) / 2), round_len)

    # clamp onto the shaft's flat: M3 screw from +X through a captured nut
    flat_x = SHAFT_ACROSS_FLAT - SHAFT_D / 2
    clamp_z = max(COLLAR_LEN / 2, round_len + SCREW_D / 2 + 0.3)
    slot_x = flat_x + 1.9
    body -= Pos((flat_x + COLLAR_AF) / 2, 0, clamp_z) * Rot(0, 90, 0) * Cylinder(SCREW_D / 2, COLLAR_AF - flat_x)
    body -= box(slot_x, slot_x + NUT_T, -NUT_AF / 2, NUT_AF / 2, -1, clamp_z + NUT_AF / 2)

    # wheel screw: its head rests on the bottom of the bore, its shank runs out through the pilot
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
    """Lying on a collar flat, so the layers run along the axis."""
    turned = Rot(90, 0, 0) * part
    return Pos(0, 0, -turned.bounding_box().min.Z) * turned


# --- reference geometry, never exported ---


def ref_shaft():
    """Motor shaft: round near the gearbox, flat over the outer SHAFT_FLAT_LEN."""
    round_len = SHAFT_LEN - SHAFT_FLAT_LEN
    shaft = extrude(Circle(SHAFT_D / 2), round_len) + Pos(0, 0, round_len) * extrude(d_profile(), SHAFT_FLAT_LEN)
    return Pos(0, 0, -GEARBOX_GAP) * shaft


def wheel_screw_len():
    """Shortest standard M3 length that reaches through the pilot plus 20 mm, for the drawing."""
    return 35.0


def ref_screws():
    """Clamp screw (M3 x 10) and wheel screw with its head at the bottom of the bore."""
    shaft_in, bore_depth, hex_end = layout()
    flat_x = SHAFT_ACROSS_FLAT - SHAFT_D / 2
    clamp_z = max(COLLAR_LEN / 2, max(SHAFT_LEN - SHAFT_FLAT_LEN - GEARBOX_GAP, 0) + 0.5 + SCREW_D / 2 + 0.3)
    clamp = Pos(flat_x + 5, 0, clamp_z) * Rot(0, 90, 0) * Cylinder(1.5, 10)
    length = wheel_screw_len()
    head = Pos(-0.22, 0, bore_depth - HEAD_H / 2) * Cylinder(HEAD_D / 2, HEAD_H)
    wheel = head + Pos(0, 0, bore_depth + length / 2) * Cylinder(1.5, length)
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
    report(overlap(adapter, clamp) < 1e-6 and overlap(adapter, wheel) < 1e-6, "clamp screw and wheel screw, head included, sit in the part without collision")
    # the wheel screw's head has to travel the whole bore to reach its seat
    head = Cylinder(HEAD_D / 2, HEAD_H)
    stuck = [z for z in range(0, int(bore_depth) - 2) if overlap(adapter, Pos(-0.22, 0, z + HEAD_H / 2) * head) > 1e-6]
    report(not stuck, f"a {HEAD_D} mm screw head slides down the bore to its seat (bore is {SHAFT_ACROSS_FLAT + FLAT_FIT + SHAFT_FIT / 2:.2f} across the flat)")
    wall_hex = (HEX_AF - HEX_FIT) / 2 - (SHAFT_D + SHAFT_FIT) / 2
    report(wall_hex >= 2.5, f"{wall_hex:.2f} mm of plastic between the bore and the hex flats")
    report(hex_end - bore_depth >= 2.0, f"{hex_end - bore_depth:.1f} mm of solid hex under the screw head before the pilot starts")
    print(f"  shaft reaches {shaft_in - COLLAR_LEN:.1f} mm into the hex; no slot is cut in the hex or the pilot")
    print(f"  nothing but the nut is on the far side of the wheel: it stays reachable with the wheel fitted")
    return ok


def render(adapter, out):
    import matplotlib.pyplot as plt

    import preview as pv

    shaft_in, bore_depth, hex_end = layout()
    end = hex_end + PILOT_LEN
    shaft, (clamp, wheel) = ref_shaft(), ref_screws()
    fig, axes = plt.subplots(1, 3, figsize=(21, 9))
    cut_y = box(-50, 50, 0, 50, -50, 90)
    items = [pv.item(adapter & cut_y, "collar"), pv.item(shaft & cut_y, "stick"), pv.item(clamp & cut_y, "hardware"), pv.item(wheel & cut_y, "hardware")]
    ax = axes[0]
    pv.show(ax, items, (0, -1, 0), "Section through the clamp screw (shaft dark grey, screws light)", margin=15, scale=20)
    c = COLLAR_AF / 3**0.5
    pv.dim(ax, (-c, 0), (-c, COLLAR_LEN), f"collar {COLLAR_LEN:.0f}", off=(-3, 0), text_off=(-4.5, 0))
    pv.dim(ax, (-c, COLLAR_LEN), (-c, hex_end), f"hex {HEX_LEN:.0f}", off=(-3, 0), text_off=(-4, 0))
    pv.dim(ax, (-c, hex_end), (-c, end), f"pilot {PILOT_LEN:.0f}", off=(-3, 0), text_off=(-4.5, 0))
    pv.dim(ax, (-c, 0), (-c, shaft_in), f"shaft goes in {shaft_in:.0f}", off=(-12, 0), text_off=(-7, 0))
    pv.dim(ax, (-SHAFT_D / 2, 0), (SHAFT_ACROSS_FLAT - SHAFT_D / 2, 0), f"bore {SHAFT_D + SHAFT_FIT:.1f} dia, {SHAFT_ACROSS_FLAT + FLAT_FIT + SHAFT_FIT / 2:.2f} across the flat;\nround for the first {max(SHAFT_LEN - SHAFT_FLAT_LEN - GEARBOX_GAP, 0) + 0.5:.0f} mm", off=(0, -7))
    pv.note(ax, (SHAFT_ACROSS_FLAT - SHAFT_D / 2 + 3.2, COLLAR_LEN / 2), "M3 nut slides in from the\ngearbox end; M3 x 10 screw\nbears on the shaft's flat", (19, -3))
    pv.note(ax, (0, bore_depth - HEAD_H / 2), "wheel screw's head, dropped\ndown the bore before the\nadapter goes on the shaft", (14, 4))
    pv.note(ax, (1.5, end + 12), "to the far side of the wheel:\ncap, then the M3 nut, in the open", (12, 0))
    ax = axes[1]
    pv.show(ax, [pv.item(adapter, "collar")], (0.55, 0.6, 0.5), "wheel_adapter", margin=6, scale=20)
    ax = axes[2]
    cap = make_wheel_cap()
    pv.show(ax, [pv.item(cap & cut_y, "cradle")], (0, -1, 0), "wheel_cap, section (far side of the wheel)", margin=12, scale=20)
    pv.dim(ax, (-CAP_D / 2, 0), (CAP_D / 2, 0), f"flange {CAP_D:.0f} dia", off=(0, -4))
    pv.dim(ax, (-(HEX_AF - HEX_FIT) / 3**0.5, CAP_T + CAP_HEX_LEN), ((HEX_AF - HEX_FIT) / 3**0.5, CAP_T + CAP_HEX_LEN), f"hex {HEX_AF - HEX_FIT:.1f} across flats", off=(0, 4))
    pv.dim(ax, (CAP_D / 2, 0), (CAP_D / 2, CAP_T), f"{CAP_T:.0f}", off=(3, 0), text_off=(2, 0))
    pv.note(ax, (0, 0.3), "nut tightens on this face", (-9, -9))
    fig.suptitle(f"Measured: hex {HEX_AF:.0f} mm across flats, round hole {PILOT_HOLE_D:.0f} mm.   UNCONFIRMED: shaft flat {SHAFT_ACROSS_FLAT} mm, shaft length {SHAFT_LEN:.0f} mm, flat length {SHAFT_FLAT_LEN} mm, pilot length {PILOT_LEN:.0f} mm.", fontsize=12, color="crimson")
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
        laid = as_printed(part) if name == "wheel_adapter" else part
        export_stl(laid, str(out / f"{name}.stl"), tolerance=0.01, angular_tolerance=0.1)
    print("exported", ", ".join(parts), "to", out)
    print("all geometric checks passed" if passed else "SOME CHECKS FAILED")
    if "--preview" in sys.argv:
        (here / "previews").mkdir(exist_ok=True)
        render(parts["wheel_adapter"], here / "previews" / "wheel_adapter.png")

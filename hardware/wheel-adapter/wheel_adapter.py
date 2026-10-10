"""Printed hub adapter: omni wheel's hex socket onto the JGY-370 gearmotor's 6 mm D-shaft.

Run with build123d installed:  python wheel_adapter.py            (exports + checks)
                               python wheel_adapter.py --preview  (also renders a drawing)
All dimensions are millimetres. The adapter's axis is +Z, z=0 at the gearbox end.

RESEARCH PROTOTYPE. Nothing here has been printed or load tested.

How it carries load
  torque   D-shaped bore on the shaft's flat, then the hex into the wheel
  bending  the steel shaft runs inside the collar and the first part of the hex;
           beyond the shaft tip a steel M3 screw runs down the middle
  pull-off an M3 screw and captured nut clamp onto the shaft's flat; a second M3
           screw from the far side of the wheel pulls the wheel onto the hex

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
SHAFT_FIT = 0.15  # total slack in the D-bore; keep it tight, this is what carries torque
GEARBOX_GAP = 1.0  # adapter stops this far short of the gearbox face

# --- wheel hub ---
HEX_AF = 12.0  # UNCONFIRMED: wheel's hex socket across flats
HEX_FIT = 0.2  # total slack between the printed hex and the socket
HEX_LEN = 12.0  # longer than the socket is deep on purpose: the hex bottoms in the socket
PILOT_D = 0.0  # set to the wheel's centre hole (minus 0.3) to add a pilot through the hub; 0 = none
PILOT_LEN = 0.0

# --- body ---
COLLAR_AF = 22.0  # hexagonal collar, so the part can lie on a flat to print
COLLAR_LEN = 8.0
END_CHAMFER = 0.8

# --- M3 hardware ---
SCREW_D = 3.2  # M3 close fit
NUT_AF = 5.8  # slot width for an M3 nut (5.5 across flats)
NUT_T = 2.7  # slot thickness for an M3 nut (2.4 thick)


def layout():
    bore_depth = SHAFT_LEN - GEARBOX_GAP
    nut_z0 = bore_depth + 1.6  # web between the shaft tip and the wheel-screw nut
    hex_end = COLLAR_LEN + HEX_LEN
    return bore_depth, nut_z0, hex_end


def d_profile(extra=0.0):
    """Shaft cross-section grown by `extra`, flat facing +X."""
    r = SHAFT_D / 2 + extra
    flat_x = SHAFT_ACROSS_FLAT - SHAFT_D / 2 + extra
    return Circle(r) & Pos(flat_x - r, 0) * Rectangle(2 * r, 2 * r)


def hexagon(across_flats):
    """Hexagon with flats facing +Y and -Y."""
    return RegularPolygon(across_flats / 3**0.5, 6)


def make_wheel_adapter():
    bore_depth, nut_z0, hex_end = layout()
    assert nut_z0 + NUT_T + 2.0 <= hex_end, "HEX_LEN is too short to hold the wheel-screw nut"

    body = extrude(hexagon(COLLAR_AF), COLLAR_LEN)
    drive = Pos(0, 0, COLLAR_LEN) * extrude(hexagon(HEX_AF - HEX_FIT), HEX_LEN)
    tip = PILOT_LEN if PILOT_D else 0.0
    if tip:
        drive += Pos(0, 0, hex_end) * extrude(Circle(PILOT_D / 2), PILOT_LEN)
    drive = chamfer(drive.edges().group_by(Axis.Z)[-1], END_CHAMFER)
    body += drive

    # D-bore for the shaft
    body -= extrude(d_profile(SHAFT_FIT / 2), bore_depth)

    # clamp onto the shaft's flat: M3 screw from +X through a captured nut
    flat_x = SHAFT_ACROSS_FLAT - SHAFT_D / 2
    clamp_z = COLLAR_LEN / 2
    slot_x = flat_x + 1.9
    body -= Pos((flat_x + COLLAR_AF) / 2, 0, clamp_z) * Rot(0, 90, 0) * Cylinder(SCREW_D / 2, COLLAR_AF - flat_x)
    body -= box(slot_x, slot_x + NUT_T, -NUT_AF / 2, NUT_AF / 2, -1, clamp_z + NUT_AF / 2)

    # wheel screw: M3 down the axis from the far side into a nut dropped in from +Y
    body -= Pos(0, 0, (bore_depth + hex_end + tip) / 2) * Cylinder(SCREW_D / 2, hex_end + tip - bore_depth + 2)
    body -= box(-NUT_AF / 2, NUT_AF / 2, -NUT_AF / 2, HEX_AF, nut_z0, nut_z0 + NUT_T)
    return body


def make_fit_test():
    """Short hex with the D-bore right through: try it on the shaft and in the wheel."""
    stub = extrude(hexagon(HEX_AF - HEX_FIT), 8)
    stub = chamfer(stub.edges().group_by(Axis.Z)[-1], END_CHAMFER)
    return stub - Pos(0, 0, -1) * extrude(d_profile(SHAFT_FIT / 2), 10)


def as_printed(part):
    """Lying on a collar flat, nut slot for the wheel screw opening upwards."""
    turned = Rot(90, 0, 0) * part
    return Pos(0, 0, -turned.bounding_box().min.Z) * turned


# --- reference geometry, never exported ---


def ref_shaft():
    return Pos(0, 0, -GEARBOX_GAP) * extrude(d_profile(), SHAFT_LEN)


def ref_screws():
    """Clamp screw (M3 x 10) and wheel screw, as plain cylinders."""
    bore_depth, nut_z0, hex_end = layout()
    flat_x = SHAFT_ACROSS_FLAT - SHAFT_D / 2
    clamp = Pos(flat_x + 5, 0, COLLAR_LEN / 2) * Rot(0, 90, 0) * Cylinder(1.5, 10)
    wheel = Pos(0, 0, nut_z0 - 0.5 + 15) * Cylinder(1.5, 30)
    return clamp, wheel


def run_checks(adapter, test):
    ok = True

    def report(passed, text):
        nonlocal ok
        ok &= bool(passed)
        print(f"  [{'ok' if passed else 'FAIL'}] {text}")

    bore_depth, nut_z0, hex_end = layout()
    for name, part in (("wheel_adapter", adapter), ("wheel_adapter_fit_test", test)):
        bb = part.bounding_box().size
        report(part.is_valid and len(part.solids()) == 1, f"{name}: {bb.X:.1f} x {bb.Y:.1f} x {bb.Z:.1f} mm, {part.volume / 1000:.2f} cm3, valid={part.is_valid}, solids={len(part.solids())}")
    report(overlap(adapter, ref_shaft()) < 1e-6, f"shaft enters the D-bore without collision, {bore_depth:.1f} mm deep")
    clamp, wheel = ref_screws()
    report(overlap(adapter, clamp) < 1e-6 and overlap(adapter, wheel) < 1e-6, "both M3 screws pass through their holes")
    wall_hex = (HEX_AF - HEX_FIT) / 2 - (SHAFT_D + SHAFT_FIT) / 2
    report(wall_hex >= 2.5, f"{wall_hex:.2f} mm of plastic between the bore and the hex flats")
    print(f"  shaft is inside the adapter for {bore_depth:.1f} mm; it reaches {bore_depth - COLLAR_LEN:.1f} mm into the hex")
    print(f"  the hex runs {hex_end - bore_depth:.1f} mm past the shaft tip, carried by plastic and the M3 wheel screw")
    return ok


def render(adapter, out):
    import matplotlib.pyplot as plt

    import preview as pv

    bore_depth, nut_z0, hex_end = layout()
    shaft, (clamp, wheel) = ref_shaft(), ref_screws()
    fig, axes = plt.subplots(1, 3, figsize=(20, 8))
    cut_y = box(-50, 50, 0, 50, -50, 80)
    items = [pv.item(adapter & cut_y, "collar"), pv.item(shaft & cut_y, "stick"), pv.item(clamp & cut_y, "hardware"), pv.item(wheel & cut_y, "hardware")]
    ax = axes[0]
    pv.show(ax, items, (0, -1, 0), "Section through the clamp screw (shaft and screws in grey)", margin=14, scale=22)
    h, c = (HEX_AF - HEX_FIT) / 2, COLLAR_AF / 3**0.5
    pv.dim(ax, (-c, 0), (-c, COLLAR_LEN), f"collar {COLLAR_LEN:.0f}", off=(-3, 0), text_off=(-4, 0))
    pv.dim(ax, (-c, COLLAR_LEN), (-c, hex_end), f"hex {HEX_LEN:.0f}", off=(-3, 0), text_off=(-4, 0))
    pv.dim(ax, (c, 0), (c, bore_depth), f"shaft goes in {bore_depth:.0f}", off=(4, 0), text_off=(7, 0))
    pv.dim(ax, (-SHAFT_D / 2, 0), (SHAFT_ACROSS_FLAT - SHAFT_D / 2, 0), f"D-bore {SHAFT_D + SHAFT_FIT:.2f} dia,\n{SHAFT_ACROSS_FLAT + SHAFT_FIT:.2f} across the flat", off=(0, -5.5))
    pv.note(ax, (SHAFT_ACROSS_FLAT - SHAFT_D / 2 + 3.2, COLLAR_LEN / 2), "M3 nut slides in from the\ngearbox end; M3 x 10 screw\nbears on the shaft's flat", (9, 13))
    ax = axes[1]
    cut_x = box(-50, 0, -50, 50, -50, 80)
    items = [pv.item(adapter & cut_x, "collar"), pv.item(shaft & cut_x, "stick"), pv.item(wheel & cut_x, "hardware")]
    pv.show(ax, items, (1, 0, 0), "Section through the wheel-screw nut slot", margin=14, scale=22)
    pv.dim(ax, (-h, hex_end), (h, hex_end), f"hex {HEX_AF - HEX_FIT:.1f} across flats", off=(0, 12))
    pv.dim(ax, (-COLLAR_AF / 2, 0), (COLLAR_AF / 2, 0), f"collar {COLLAR_AF:.0f} across flats", off=(0, -5))
    pv.note(ax, (h - 1.5, nut_z0 + NUT_T / 2), "M3 nut drops in from this side;\nwheel screw comes down the axis\nfrom the far side of the wheel", (11, 9))
    pv.note(ax, (0, (bore_depth + nut_z0) / 2), f"{nut_z0 - bore_depth:.1f} web past the shaft tip", (-13, -13))
    ax = axes[2]
    pv.show(ax, [pv.item(adapter, "collar")], (0.55, 0.6, 0.55), "wheel_adapter", margin=6, scale=22)
    fig.suptitle(f"UNCONFIRMED: wheel hex {HEX_AF:.0f} mm across flats, shaft flat {SHAFT_ACROSS_FLAT} mm, shaft length {SHAFT_LEN:.0f} mm. Measure before printing the full part.", fontsize=12, color="crimson")
    fig.savefig(out, dpi=110, bbox_inches="tight", facecolor="white")
    print("wrote", out)


if __name__ == "__main__":
    here = Path(__file__).parent
    out = here / "export"
    out.mkdir(exist_ok=True)
    adapter, test = make_wheel_adapter(), make_fit_test()
    passed = run_checks(adapter, test)
    for name, part, laid in (("wheel_adapter", adapter, as_printed(adapter)), ("wheel_adapter_fit_test", test, test)):
        export_step(part, str(out / f"{name}.step"))
        export_stl(laid, str(out / f"{name}.stl"), tolerance=0.01, angular_tolerance=0.1)
    print("exported wheel_adapter and wheel_adapter_fit_test to", out)
    print("all geometric checks passed" if passed else "SOME CHECKS FAILED")
    if "--preview" in sys.argv:
        (here / "previews").mkdir(exist_ok=True)
        render(adapter, here / "previews" / "wheel_adapter.png")

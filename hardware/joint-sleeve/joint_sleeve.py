"""Joint sleeve: a split clamp that goes over a joint between two cane tubes and carries the bending there.

Run with build123d installed:  python joint_sleeve.py            (exports + checks)
                               python joint_sleeve.py --preview  (also renders a drawing)
All dimensions are millimetres. The sleeve is built about its own centre: the pole
runs up +Z and the joint between the two tubes is at z=0. The clamp's ears and slit
are on -X, as on the camera collar.

RESEARCH PROTOTYPE. Nothing here has been printed or load tested.

Why it exists. At a joint the two tubes only butt end to end, so all the bending
passes through the coupler's printed tongue: 10 x 8.5 mm with a 4.2 mm hole down
it. Carrying a four-tube cane level by its handle is estimated to put 8 to 12 N.m
on the top joint from the cane's own weight, and that tongue is estimated to
break at 2 to 7 N.m (see README.md for the sums). This sleeve clamps over the
ends of both tubes, where the glued-in inserts back the thin carbon wall, and
takes that bending instead.

It is the camera collar's clamp, made longer and without the tilt joint.
"""

import sys
from math import pi
from pathlib import Path

from build123d import Axis, Box, Cylinder, Pos, Rot, export_step, export_stl, fillet

# the coupler and the shared helpers live in neighbouring folders
for _folder in ("cane-coupler", "handle-phone-mount"):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / _folder))
import coupler_motor_mount as cm  # noqa: E402
from walking_stick import box, hex_pocket, overlap, ref_bolt, ref_nut  # noqa: E402

SLEEVE_LEN = 60.0  # 30 mm over each tube: inside the length the glued-in inserts back the wall (34 and 42 mm)
BORE_FIT = 0.3  # added to the tube's 18 mm for the bore, as on the camera collar; the slit takes up the rest
WALL = 5.0
SLIT = 3.0
EAR_W = 18.0  # across both ears: an M3 x 20 then reaches through its nut
EAR_OUT = 14.0  # how far the ears stand out past the ring
BOLT_D = 3.6  # M3 with room to spare: 3.2 mm holes printed too small on the wheel adapter
NUT_AF = 5.8
NUT_POCKET = 3.5
BOLT_Z = (-20.0, 0.0, 20.0)  # three pinch bolts
WINDOW_D = 5.0  # hole opposite the clamp, on the joint line, to see or feel that the sleeve is centred


def layout():
    """Bore radius, outside radius of the ring, and where the pinch bolts sit in x."""
    bore_r = (cm.TUBE_OD + BORE_FIT) / 2
    ring_r = bore_r + WALL
    return bore_r, ring_r, -(ring_r + EAR_OUT / 2)


def make_joint_sleeve():
    bore_r, ring_r, bolt_x = layout()
    ear_x0, ear_x1 = ring_r - 4, ring_r + EAR_OUT
    ears = Pos(-(ear_x0 + ear_x1) / 2, 0, 0) * Box(ear_x1 - ear_x0, EAR_W, SLEEVE_LEN)
    ears = fillet(ears.edges().filter_by(Axis.Z), 3)

    sleeve = Cylinder(ring_r, SLEEVE_LEN) + ears
    sleeve -= Cylinder(bore_r, SLEEVE_LEN + 2)
    sleeve -= box(-ear_x1 - 1, 0, -SLIT / 2, SLIT / 2, -SLEEVE_LEN / 2 - 1, SLEEVE_LEN / 2 + 1)
    for z in BOLT_Z:
        sleeve -= Pos(bolt_x, 0, z) * Rot(90, 0, 0) * Cylinder(BOLT_D / 2, EAR_W + 12)
        sleeve -= Pos(bolt_x, -EAR_W / 2 + NUT_POCKET, z) * hex_pocket(NUT_AF, NUT_POCKET)
    # window through the wall opposite the clamp
    sleeve -= Pos(ring_r - WALL / 2, 0, 0) * Rot(0, 90, 0) * Cylinder(WINDOW_D / 2, WALL + 2)
    return sleeve


# ---------------------------------------------------------------------------
# reference geometry, never exported
# ---------------------------------------------------------------------------


def ref_tubes(length=60.0):
    """The ends of the two tubes that meet at z=0: (tube above, tube below)."""
    wall = Cylinder(cm.TUBE_OD / 2, length) - Cylinder(cm.TUBE_ID / 2, length)
    return Pos(0, 0, length / 2) * wall, Pos(0, 0, -length / 2) * wall


def ref_coupler():
    """The v3 coupler at the joint: main insert glued in the tube above, tongue down; receiver in the tube below."""
    flip = Rot(180, 0, 0)
    return Pos(0, 0, cm.MAIN_BARREL_LEN) * flip * cm.make_main_v3(), flip * cm.make_receiver_v3()


def ref_bolts():
    """Three M3 x 20 screws with their nuts: screw, nut, screw, nut..."""
    bolt_x = layout()[2]
    out = []
    for z in BOLT_Z:
        out.append(Pos(bolt_x, EAR_W / 2, z) * ref_bolt(3, 20, 5.5, 3))
        out.append(Pos(bolt_x, -EAR_W / 2 + NUT_POCKET, z) * ref_nut(5.5, 2.4, 3))
    return out


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------


def run_checks(sleeve):
    """Geometric checks only. They say nothing about how strong the printed part is."""
    ok = True

    def report(passed, text):
        nonlocal ok
        ok &= bool(passed)
        print(f"  [{'ok' if passed else 'FAIL'}] {text}")

    bore_r, ring_r, bolt_x = layout()
    bb = sleeve.bounding_box().size
    report(sleeve.is_valid and len(sleeve.solids()) == 1, f"joint_sleeve: {bb.X:.1f} x {bb.Y:.1f} x {bb.Z:.1f} mm, {sleeve.volume / 1000:.1f} cm3, valid={sleeve.is_valid}, solids={len(sleeve.solids())}")
    above, below = ref_tubes()
    report(overlap(sleeve, above) + overlap(sleeve, below) < 1e-6, f"both tube ends sit in the bore with {BORE_FIT / 2:.2f} mm clearance each side before clamping")
    bolts = ref_bolts()
    report(all(overlap(b, sleeve) < 1e-6 for b in bolts), "three M3 x 20 screws and their nuts sit in their holes and pockets")
    report(all(overlap(b, above) + overlap(b, below) < 1e-6 for b in bolts), f"the screws pass {-bolt_x - 1.5 - cm.TUBE_OD / 2:.1f} mm clear of the tube")
    grip = EAR_W - NUT_POCKET
    report(20 - grip >= 2.4 + 1, f"each M3 x 20 clamps {grip:.1f} mm, leaving {20 - grip:.1f} mm of thread for the 2.4 mm nut, and {SLIT:.0f} mm of slit to close")
    half = SLEEVE_LEN / 2
    report(half <= cm.MAIN_BARREL_LEN and half <= cm.RECEIVER_LEN,
           f"the sleeve covers {half:.0f} mm of each tube; the inserts back the wall for {cm.MAIN_BARREL_LEN:.0f} mm above the joint and {cm.RECEIVER_LEN:.0f} mm below")
    inertia = pi / 64 * ((2 * ring_r) ** 4 - (2 * bore_r) ** 4)
    modulus = inertia / ring_r
    tongue = (cm.MALE_W * cm.MALE_H**3 / 12 - pi * cm.CORD_HOLE_D**4 / 64) / (cm.MALE_H / 2)
    print(f"  ring section, ignoring the slit and the ears: {2 * ring_r:.1f} mm outside, {2 * bore_r:.1f} mm bore, section modulus {modulus:.0f} mm3;")
    print(f"  the coupler's tongue alone has {tongue:.0f} mm3, so for the same stress the sleeve's section carries about {modulus / tongue:.0f} times the bending")
    print(f"  ESTIMATE, not a test: at 15 to 35 MPa across the layers (printed upright) the ring would carry {modulus * 15 / 1000:.0f} to {modulus * 35 / 1000:.0f} N.m")
    return ok


def render(sleeve, out):
    import matplotlib.pyplot as plt

    import preview as pv

    bore_r, ring_r, bolt_x = layout()
    above, below = ref_tubes(80.0)
    main, receiver = ref_coupler()
    bolts = ref_bolts()
    fig, axes = plt.subplots(1, 3, figsize=(22, 11))

    ax = axes[0]
    items = [pv.item(sleeve, "collar"), pv.item(above, "stick"), pv.item(below, "stick"), pv.item(bolts, "hardware")]
    proj = pv.show(ax, items, (-0.55, -0.75, 0.3), "On a joint, seen from the clamp side", scale=5.5, margin=22)
    pv.label(ax, proj, (0, -9, 60), "tube above", (-46, 8))
    pv.label(ax, proj, (0, -9, -60), "tube below", (-46, -8))
    pv.label(ax, proj, (bolt_x, -EAR_W / 2, BOLT_Z[0]), "3 x M3 x 20,\nnuts in pockets", (-50, -26))
    pv.label(ax, proj, (-ring_r, -SLIT, 26), f"{SLIT:.0f} mm slit", (-44, 30))

    ax = axes[1]
    keep = box(-80, 80, 0, 80, -120, 120)
    items = [pv.item(sleeve & keep, "collar"), pv.item(above & keep, "stick"), pv.item(below & keep, "stick"),
             pv.item(main & keep, "cradle"), pv.item(receiver & keep, "handle")]
    pv.show(ax, items, (0, -1, 0), "Cut down the middle: the sleeve bridges the joint", window=(-48, 44, -48, 54), scale=8)
    pv.dim(ax, (ring_r, -SLEEVE_LEN / 2), (ring_r, SLEEVE_LEN / 2), f"sleeve {SLEEVE_LEN:.0f}", off=(8, 0), text_off=(10, 0))
    pv.dim(ax, (-bore_r, SLEEVE_LEN / 2), (bore_r, SLEEVE_LEN / 2), f"bore {2 * bore_r:.1f}", off=(0, 12))
    pv.note(ax, (cm.TUBE_OD / 2 - 0.5, 0), "the tubes meet here", (30, -6))
    pv.note(ax, (3, 20), "main insert, glued\nin the tube above", (-34, 26))
    pv.note(ax, (5.5, -26), "receiver, glued\nin the tube below", (-36, -20))
    pv.note(ax, (2.5, -9), "the tongue: the only thing\ncrossing the joint without the sleeve", (-38, 8))
    pv.note(ax, (ring_r - WALL / 2, 0), "window on the\njoint line", (22, 20))

    ax = axes[2]
    proj = pv.show(ax, [pv.item(sleeve, "collar")], (0.6, -0.7, 0.35), "The sleeve alone, as it prints: standing up", scale=5.5, margin=18)
    pv.label(ax, proj, (ring_r, 0, 0), "window", (40, 14))
    pv.label(ax, proj, (0, -ring_r, 20), f"{WALL:.0f} mm wall", (-46, 22))
    fig.suptitle("Joint sleeve: a clamp over the joint between two tubes. Strength figures in the README are estimates; nothing has been printed or load tested.", fontsize=12, color="crimson")
    fig.savefig(out, dpi=110, bbox_inches="tight", facecolor="white")
    print("wrote", out)


if __name__ == "__main__":
    here = Path(__file__).parent
    out = here / "export"
    out.mkdir(exist_ok=True)
    sleeve = make_joint_sleeve()
    passed = run_checks(sleeve)
    export_step(sleeve, str(out / "joint_sleeve.step"))
    laid = Pos(0, 0, -sleeve.bounding_box().min.Z) * sleeve  # prints standing upright, bore vertical
    export_stl(laid, str(out / "joint_sleeve.stl"), tolerance=0.01, angular_tolerance=0.1)
    print("exported joint_sleeve to", out)
    print("all geometric checks passed" if passed else "SOME CHECKS FAILED")
    if "--preview" in sys.argv:
        (here / "previews").mkdir(exist_ok=True)
        render(sleeve, here / "previews" / "joint_sleeve.png")

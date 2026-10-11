"""Renders previews/mount_assembly_steps.png: how the battery and Pi mount goes on the stick.

Run after electronics_mount.py:  python electronics_mount_steps.py   (needs numpy and matplotlib)
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import electronics_mount as em  # also puts the neighbouring folders on the path

import coupler_motor_mount as cm  # noqa: E402
import preview as pv  # noqa: E402
from build123d import Cylinder  # noqa: E402
from walking_stick import Pos  # noqa: E402

EYE = (0.3, -0.85, 0.4)  # from the side, a little above: motor shaft points right
PLACE = em.on_cane()
PARTS = em.printable_parts()
PI_HALF, BATT_HALF = PARTS["electronics_mount_pi_half"], PARTS["electronics_mount_battery_half"]


def placed(shape, dx=0.0, dy=0.0, dz=0.0):
    """A shape from the mount frame put on the cane, optionally pulled away by an offset in the mount frame."""
    return PLACE * Pos(dx, dy, dz) * shape


def point(x, y, z):
    return tuple((PLACE * Pos(x, y, z)).position)


def context():
    tube = Pos(cm.receiver_x(), 0, 0) * em.ref_tube(cm.RECEIVER_LEN, em.MOUNT_Z + em.MOUNT_H + 28)
    return [pv.item(cm.make_motor_receiver(), "collar"), pv.item(cm.ref_motor(-1), "bed"), pv.item(tube, "stick")]


def arrow(ax, proj, start, end, color="crimson"):
    ax.annotate("", xy=proj(end), xytext=proj(start), arrowprops=dict(arrowstyle="-|>", color=color, lw=2.2, shrinkA=0, shrinkB=0))


def pi_screws(dx):
    """The four M2.5 x 12 screws pulled out by dx, and their nuts in place on the inside of the plate."""
    hardware = em.ref_pi_screws()
    return [placed(s, dx) for s in hardware[0::2]] + [placed(n) for n in hardware[1::2]]


def step_1(ax):
    gap = 42.0
    bolts = em.ref_bolts()
    screws, nuts = bolts[0::2], bolts[1::2]
    tape = Pos(0, 0, em.MOUNT_H / 2) * (Cylinder(em.TUBE_OD / 2 + 0.6, em.MOUNT_H) - Cylinder(em.TUBE_OD / 2 + 0.05, em.MOUNT_H))
    items = context() + [
        pv.item(placed(tape), "hand"),
        pv.item(placed(BATT_HALF, -gap), "cradle"),
        pv.item(placed(PI_HALF, gap), "handle"),
        pv.item([placed(n, -gap, 16 if y > 0 else -16) for n, (y, _) in zip(nuts, em.bolt_positions())], "strap"),
        pv.item([placed(s, gap + 26) for s in screws], "hardware"),
    ]
    proj = pv.show(ax, items, EYE, "Steps 1 to 4: tape, nuts, halves, screws", margin=22)
    pv.label(ax, proj, point(0, 9, em.MOUNT_H * 0.55), "1. Wrap tape round the tube\nwhere the mount will sit", (-4, 44))
    y_near = em.HALF_W + 16
    for _, z in em.bolt_positions()[::2]:
        arrow(ax, proj, point(-gap - em.NUT_X - 1.5, y_near - 2, z), point(-gap - em.NUT_X - 1.5, em.HALF_W + 1, z))
    pv.label(ax, proj, point(-gap - em.NUT_X, y_near, em.MOUNT_H - em.BAR_H / 2), "2. Slide an M3 nut into each of\nthe 4 side slots (2 each side)", (34, 30))
    arrow(ax, proj, point(-gap + 2, em.HALF_W, 45), point(-12, em.HALF_W, 45))
    arrow(ax, proj, point(gap - 2, em.HALF_W, 45), point(12, em.HALF_W, 45))
    pv.label(ax, proj, point(-gap - 20, em.HALF_W, 30), "battery half", (36, -22))
    pv.label(ax, proj, point(gap + 8, em.HALF_W, 30), "Pi half", (-30, -30))
    pv.label(ax, proj, point(0, em.HALF_W, 45), "3. Close the two halves\nround the tube", (-2, -52))
    for y, z in em.bolt_positions()[:1] + em.bolt_positions()[2:3]:
        arrow(ax, proj, point(gap + 26 + em.HEAD_SEAT_X - 22, y, z), point(gap + 17, y, z))
    pv.label(ax, proj, point(gap + 34, em.BOLT_Y, em.MOUNT_H - em.BAR_H / 2), "4. Four M3 x 20 screws\ngo in from the Pi side", (-40, 26))


def step_2(ax):
    items = context() + [pv.item(placed(BATT_HALF), "cradle"), pv.item(placed(PI_HALF), "handle"),
                         pv.item([placed(b) for b in em.ref_bolts()], "hardware")]
    proj = pv.show(ax, items, EYE, "Steps 5 and 6: set the position, then tighten", margin=22)
    low, top = (0, em.HALF_W, 0), (0, em.HALF_W, -(em.MOUNT_Z - 35))
    arrow(ax, proj, point(*low), point(*top), color="navy")
    arrow(ax, proj, point(*top), point(*low), color="navy")
    pv.label(ax, proj, point(0, em.HALF_W, -2.5), "5. Slide it down until it is about\n5 mm above the motor's terminals,\nbattery side over the motor", (-62, -6))
    pv.label(ax, proj, point(em.PLATE_IN + em.PLATE_T, em.BOLT_Y, em.MOUNT_H - em.BAR_H / 2), "6. Tighten the 4 screws a little\nat a time, corner to corner,\nuntil it will not slide or twist", (-58, 22))
    pv.label(ax, proj, point(0, em.HALF_W, em.MOUNT_H - 3), "a 2 mm gap stays between\nthe halves: that is intended", (48, 30))


def step_3(ax):
    items = context() + [
        pv.item(placed(BATT_HALF), "cradle"), pv.item(placed(PI_HALF), "handle"),
        pv.item([placed(b) for b in em.ref_bolts()], "hardware"),
        pv.item(placed(em.ref_pi(), 38), "phone"),
        pv.item(pi_screws(60), "hardware"),
        pv.item(placed(em.ref_pad()), "strap"),
        pv.item(placed(em.ref_battery(), -34), "view"),
    ]
    proj = pv.show(ax, items, EYE, "Steps 7 and 8: fit the Pi and the battery", margin=22)
    x_pi = em.PLATE_IN + em.PLATE_T + em.PI_STANDOFF_H
    arrow(ax, proj, point(x_pi + 36, em.PI_W / 2, 45), point(x_pi + 4, em.PI_W / 2, 45))
    pv.label(ax, proj, point(x_pi + 40, em.PI_W / 2, 70), "7. Pi 5 onto the 4 standoffs,\nUSB and Ethernet ports up,\n4 M2.5 x 12 screws through,\na nut on each from the inside", (-46, 34))
    face = em.battery_face_x()
    arrow(ax, proj, point(face - 32, em.BATT_W / 2, 46), point(face - em.BATT_PAD_T - 1, em.BATT_W / 2, 46))
    pv.label(ax, proj, point(face - 34 - em.BATT_T, 0, 70), "8. Stick the battery to the flat plate:\nfoam tape on one side of the pad,\nhook-and-loop on the other", (42, 34))
    pv.label(ax, proj, point(face - 1, 0, 18), "pad on the plate", (30, -26))


def step_4(ax):
    items = context() + [
        pv.item(placed(BATT_HALF), "cradle"), pv.item(placed(PI_HALF), "handle"),
        pv.item([placed(b) for b in em.ref_bolts()], "hardware"),
        pv.item(placed(em.ref_pi()), "phone"), pv.item(pi_screws(0), "hardware"),
        pv.item(placed(em.ref_pad()), "strap"), pv.item(placed(em.ref_battery()), "view"),
    ]
    proj = pv.show(ax, items, EYE, "Finished: everything in place", margin=22)
    face = em.battery_face_x()
    pv.label(ax, proj, point(face - em.BATT_PAD_T - em.BATT_T, 20, 55), "battery, stuck to\nthe flat plate", (44, 30))
    pv.label(ax, proj, point(em.PLATE_IN + em.PLATE_T + 12, em.PI_W / 2, 80), "Raspberry Pi 5", (-42, 26))
    pv.label(ax, proj, (-13, -12, 15), "motor", (40, -10))
    pv.label(ax, proj, (cm.receiver_x() - 5, -8, -8), "motor receiver", (-44, -14))


if __name__ == "__main__":
    fig, axes = plt.subplots(2, 2, figsize=(20, 22))
    for ax, step in zip(axes.flat, (step_1, step_2, step_3, step_4)):
        step(ax)
    fig.suptitle("Fitting the battery and Pi mount to the stick. Hardware: 4 x M3 x 20 screws and nuts, 4 x M2.5 x 12 screws and nuts, foam tape and hook-and-loop, tape for the tube.", fontsize=14)
    out = Path(__file__).parent / "previews" / "mount_assembly_steps.png"
    fig.savefig(out, dpi=100, bbox_inches="tight", facecolor="white")
    print("wrote", out)

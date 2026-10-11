"""Renders previews/10_handle_button.png: the handle's thumb button and how the switch goes in.

Run after walking_stick.py:  python handle_button_view.py   (needs numpy and matplotlib)
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import preview as pv
import walking_stick as ws
from walking_stick import Pos, box

HANDLE = pv.PARTS["stick_handle"]
UP = pv.WORLD_UP  # drawn as held: pole leaning, grip level
LOC = ws.button_location()


def at(x, y, z):
    """A point given in the button frame, returned in the stick frame."""
    return tuple((LOC * Pos(x, y, z)).position)


def arrow(ax, proj, start, end):
    ax.annotate("", xy=proj(end), xytext=proj(start), arrowprops=dict(arrowstyle="-|>", color="crimson", lw=2.2, shrinkA=0, shrinkB=0))


if __name__ == "__main__":
    switch, leads, nut = ws.ref_button_parts()
    seat_z = ws.GRIP_H / 2 - ws.BUTTON_SEAT_DROP
    under = seat_z - ws.BUTTON_PANEL_T
    low = ws.button_drop()
    stick = ws.ref_stick(90)
    keep = box(-300, 300, 0, 100, -300, 300)
    fig, axes = plt.subplots(1, 3, figsize=(23, 10))

    ax = axes[0]
    items = [pv.item(HANDLE & keep, "handle"), pv.item(stick & keep, "stick"),
             pv.item((LOC * (switch + leads)) & keep, "phone"), pv.item((LOC * nut) & keep, "hardware")]
    b = np.array(at(0, 0, 0))
    u, v = float(b @ np.array(pv.WORLD_FWD)), float(b @ np.array(UP))  # this view's axes: forward and up, as held
    proj = pv.show(ax, items, (0, -1, 0), "Cut through the middle, drawn as held: the switch in place", up=UP, window=(u - 78, u + 52, v - 62, v + 46), scale=9)
    pv.label(ax, proj, at(0, 0, under + ws.BUTTON_THREAD_LEN + ws.BUTTON_CAP_H), "button cap", (-22, 16))
    pv.label(ax, proj, at(5, 0, seat_z + 1), f"nut on a {ws.BUTTON_SEAT_D:.0f} mm flat", (36, 16))
    pv.label(ax, proj, at(-3.6, 0, seat_z - ws.BUTTON_PANEL_T / 2), f"{ws.BUTTON_HOLE_D} mm hole through\n{ws.BUTTON_PANEL_T} mm of plastic", (-44, 30))
    pv.label(ax, proj, at(0, 0, under - ws.BUTTON_BODY_LEN / 2), f"switch body in a\n{ws.BUTTON_POCKET_D:.0f} mm pocket", (38, -8))
    pv.label(ax, proj, at(0, 0, under - ws.BUTTON_BODY_LEN - 9), "wires out underneath,\nthen down the pole", (30, -30))
    pv.label(ax, proj, (0, 0, -22), "pole socket, untouched", (-52, -16))

    ax = axes[1]
    eye = np.array(pv.WORLD_FWD) * 0.65 + np.array((0, -0.6, 0)) + np.array(UP) * 0.3
    start = Pos(30, 0, -low)
    items = [pv.item(HANDLE, "handle"), pv.item(stick, "stick"), pv.item(LOC * start * (switch + leads), "phone"),
             pv.item(LOC * Pos(0, 0, 16) * nut, "hardware")]
    proj = pv.show(ax, items, eye, "How the switch goes in: from the front, then up, then the nut", up=UP, margin=48, scale=8)
    mid = under - ws.BUTTON_BODY_LEN / 2
    arrow(ax, proj, at(24, 0, mid - low), at(9, 0, mid - low))
    pv.label(ax, proj, at(30, 0, mid - low), "1. slide the switch in\nthrough the open front\nof the nose", (14, -46))
    arrow(ax, proj, at(0, -9, mid - low + 2), at(0, -9, mid - 1))
    pv.label(ax, proj, at(0, -9, mid - low), f"2. lift it {low:.0f} mm so the cap\nand thread come up\nthrough the hole", (-58, -40))
    arrow(ax, proj, at(0, 0, seat_z + 14), at(0, 0, seat_z + 4))
    pv.label(ax, proj, at(0, 0, seat_z + 17), "3. nut on from the top", (30, 24))

    ax = axes[2]
    eye = np.array(pv.WORLD_FWD) * 0.6 + np.array((0, -0.5, 0)) - np.array(UP) * 0.65
    items = [pv.item(HANDLE, "handle"), pv.item(stick, "stick"), pv.item(LOC * (switch + leads), "phone"), pv.item(LOC * nut, "hardware")]
    proj = pv.show(ax, items, eye, "From the front, below: the open front and the pocket", up=UP, margin=24, scale=8)
    pv.label(ax, proj, at(12, 0, -4), f"front slot, {ws.BUTTON_SLOT_W} mm wide", (44, -26))

    fig.suptitle(f"Sized for the 7 mm prewired mini push button. Its 7 mm thread is from the listing; body {ws.BUTTON_BODY_D:.0f} x {ws.BUTTON_BODY_LEN:.0f} mm, thread length {ws.BUTTON_THREAD_LEN:.0f} mm and nut {ws.BUTTON_NUT_AF:.0f} mm are UNCONFIRMED.", fontsize=12, color="crimson")
    out = Path(__file__).parent / "previews" / "10_handle_button.png"
    fig.savefig(out, dpi=110, bbox_inches="tight", facecolor="white")
    print("wrote", out)

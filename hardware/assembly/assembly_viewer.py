"""Writes assembly_viewer.html: a self-contained 3D viewer for the whole cane with
every printed part in place (handle, phone mount, the keyed coupler at each tube
joint, main insert, motor mount 2, wheel adapter and cap, battery and Raspberry
Pi mount).

Run:  python assembly_viewer.py     then open assembly_viewer.html in a browser.

Stick frame, as in walking_stick.py: +Z up the pole with z=0 at the top end of
the tube, +X the pole's forward normal. The viewer leans the pole back by
STICK_LEAN_DEG, as it is held.

The pole is TUBE_SECTIONS tubes of SECTION_LEN, meeting end to end. At each joint
the tube above carries a v3 main insert, tongue down, and the tube below a v3
receiver, mouth up, both glued in flush with the tube's end.

The Pi is held by M2.5 x 12 screws and nuts. The v4 motor receiver is left out:
motor mount 2 goes in the same place.
"""

import json
import sys
from math import cos, radians, sin
from pathlib import Path

import numpy as np
from build123d import Cylinder, extrude

# every part's source, and the viewer page it is drawn with, live in neighbouring folders
for _folder in ("cane-coupler", "wheel-adapter", "electronics-mount", "motor-mount-2", "handle-phone-mount"):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / _folder))
import coupler_motor_mount as cm  # noqa: E402
import electronics_mount as em  # noqa: E402
import motor_mount_2 as mm2  # noqa: E402
import viewer  # noqa: E402
import walking_stick as ws  # noqa: E402
import wheel_adapter as wa  # noqa: E402
from walking_stick import Pos, Rot, overlap  # noqa: E402

TUBE_SECTIONS = 4  # the team's carbon tubes
SECTION_LEN = 400.0
TUBE_LEN = TUBE_SECTIONS * SECTION_LEN  # the sections meet end to end; the couplers are inside them
WHEEL_D = 58.0  # NOT MEASURED: the omni wheel looked 50 to 60 mm across in the team's photos
WHEEL_HUB_W = wa.wheel_screw_len() - 8.0  # as the wheel adapter's drawings assume
GROUND_R = 230.0
LEAN = radians(ws.STICK_LEAN_DEG)
T = ws.PHONE_TILT_DEG


def ref_wheel():
    """Double-row omni wheel in the wheel adapter's frame (axle along Z): hub, then rollers."""
    _, bore_depth, _ = wa.layout()
    outer = bore_depth + wa.wheel_screw_len() - 4.0 - wa.CAP_T  # the face the cap's flange sits on
    inner = outer - WHEEL_HUB_W
    mid = (inner + outer) / 2
    hub = Pos(0, 0, mid) * Cylinder(WHEEL_D / 2 - 9, WHEEL_HUB_W)
    hub -= Pos(0, 0, mid) * Cylinder(wa.PILOT_HOLE_D / 2, WHEEL_HUB_W + 2)
    for face in (inner, outer):  # the hex socket on each side
        hub -= Pos(0, 0, face) * extrude(wa.hexagon(wa.HEX_AF), 4.2, both=True)
    roller_r = 6.5
    rollers = []
    for row, z in enumerate((mid - WHEEL_HUB_W / 4, mid + WHEEL_HUB_W / 4)):
        rim = Pos(0, 0, z) * Cylinder(WHEEL_D / 2, WHEEL_HUB_W / 2 - 1)
        for i in range(5):
            barrel = Pos(WHEEL_D / 2 - roller_r, 0, z) * Rot(90, 0, 0) * Cylinder(roller_r, 22)
            rollers.append(Rot(0, 0, 72 * i + 36 * row) * (barrel & rim))
    return [hub] + rollers


def top_items():
    """Everything at the handle end, in the stick frame."""
    parts = ws.printable_parts()
    at = ws.cradle_location(T)
    return [
        ("Handle", (0.20, 0.47, 0.80), True, True, parts["stick_handle"]),
        ("Handle plug, in the tube", (0.55, 0.75, 0.30), True, True, parts["socket_plug"]),
        ("Camera collar", (0.95, 0.55, 0.15), True, True, ws.collar_location() * parts["camera_collar"]),
        ("Phone cradle", (0.25, 0.68, 0.45), True, True, at * parts["phone_cradle"]),
        ("Thumb button, 7 mm", (0.80, 0.25, 0.30), True, False, ws.ref_button()),
        ("Phone (stand-in)", (0.36, 0.38, 0.44), True, False, at * ws.ref_phone()),
        ("Phone strap", (0.75, 0.25, 0.30), False, False, at * ws.ref_strap()),
        ("Screws and nuts, top", (0.82, 0.80, 0.72), True, False, ws.ref_hardware(T)),
    ]


def pole_items():
    """The tube sections and the keyed coupler at each joint, in the stick frame."""
    wall = Cylinder(ws.STICK_OD / 2, SECTION_LEN) - Cylinder(ws.STICK_ID / 2, SECTION_LEN)
    tubes = [Pos(0, 0, -(i + 0.5) * SECTION_LEN) * wall for i in range(TUBE_SECTIONS)]
    flip = Rot(180, 0, 0)
    mains, receivers = [], []
    for j in range(1, TUBE_SECTIONS):
        z = -j * SECTION_LEN  # where tube j meets tube j + 1
        mains.append(Pos(0, 0, z + cm.MAIN_BARREL_LEN) * flip * cm.make_main_v3())  # barrel in the tube above, tongue below
        receivers.append(Pos(0, 0, z) * flip * cm.make_receiver_v3())  # in the tube below, mouth up
        above, below = tubes[j - 1], tubes[j]
        hit = overlap(mains[-1], receivers[-1]) + overlap(mains[-1], above) + overlap(mains[-1], below) + overlap(receivers[-1], below)
        print(f"  joint {j}, {-z:.0f} mm below the top: " + ("the tongue seats in the socket and both inserts sit inside their tubes"
                                                         if hit < 1e-6 else f"parts overlap by {hit:.1f} mm3"))
    out = [
        (f"Coupler main inserts v3, {len(mains)}", (0.86, 0.30, 0.55), True, True, mains),
        (f"Coupler receivers v3, {len(receivers)}", (0.93, 0.62, 0.78), True, True, receivers),
    ]
    for i, section in enumerate(tubes):  # two greys in turn, so the joints show
        shade = (0.22, 0.22, 0.25) if i % 2 == 0 else (0.31, 0.31, 0.35)
        out.append((f"Tube {i + 1} of {TUBE_SECTIONS}, {SECTION_LEN:.0f} mm", shade, True, False, section))
    return out


def tip_items():
    """Everything at the wheel end, in the motor frame of coupler_motor_mount.py."""
    x_r = mm2.layout()[0]
    on_shaft = Pos(cm.BOSS_H + wa.GEARBOX_GAP, 0, -cm.SHAFT_FROM_TOP) * Rot(0, 90, 0)
    _, bore_depth, _ = wa.layout()
    far = bore_depth + wa.wheel_screw_len()  # tip of the wheel screw
    cap = Pos(0, 0, far - 4.0) * Rot(180, 0, 0) * wa.make_wheel_cap()
    clamp, wheel_screw = wa.ref_screws()
    clamp_z, slot_x, _, _ = wa.clamp_layout()
    wheel_nuts = [
        Pos(slot_x + wa.NUT_T - 2.45, 0, clamp_z) * Rot(0, 0, 90) * ws.ref_nut(5.5, 2.4, 3),
        Pos(0, 0, far - 1.0) * Rot(90, 0, 0) * ws.ref_nut(5.5, 2.4, 3),
    ]
    mount_z = cm.RECEIVER_LEN + mm2.SLEEVE_LEN + mm2.MOUNT_ABOVE_SLEEVE
    place = Pos(x_r, 0, mount_z) * Rot(0, 0, em.MOUNT_TURN)
    mount = em.printable_parts()
    bolt, nut = mm2.ref_cross_bolt()
    screws = [bolt, nut] + mm2.ref_motor_screws() + [place * s for s in em.ref_bolts() + em.ref_pi_screws()]
    screws += [on_shaft * s for s in [clamp, wheel_screw] + wheel_nuts]
    return [
        ("Main insert v4, in the tube", (0.55, 0.75, 0.30), True, True, mm2.main_location() * cm.make_main_insert()),
        ("Motor mount 2", (0.85, 0.33, 0.25), True, True, mm2.make_motor_mount_2()),
        ("Wheel adapter", (0.30, 0.62, 0.85), True, True, on_shaft * wa.make_wheel_adapter()),
        ("Wheel cap", (0.93, 0.76, 0.20), True, True, on_shaft * cap),
        ("Mount, Raspberry Pi half", (0.50, 0.38, 0.80), True, True, place * mount["electronics_mount_pi_half"]),
        ("Mount, battery half", (0.15, 0.60, 0.62), True, True, place * mount["electronics_mount_battery_half"]),
        ("Omni wheel (stand-in)", (0.42, 0.44, 0.48), True, False, [on_shaft * s for s in ref_wheel()]),
        ("Gearmotor", (0.62, 0.63, 0.67), True, False, cm.ref_motor(-1)),
        ("Raspberry Pi 5", (0.20, 0.42, 0.25), True, False, place * em.ref_pi()),
        ("Battery pack", (0.25, 0.30, 0.38), True, False, [place * em.ref_battery(), place * em.ref_pad()]),
        ("Screws and nuts, tip", (0.82, 0.80, 0.72), True, False, screws),
    ]


def onto_tube(tris, turn_deg):
    """Motor-frame triangles moved to the bottom of the tube, turned about the tube by turn_deg."""
    x_r = mm2.layout()[0]
    c, s = cos(radians(turn_deg)), sin(radians(turn_deg))
    p = tris + np.array([-x_r, 0, -cm.RECEIVER_LEN], dtype=np.float32)
    out = np.empty_like(p)
    out[..., 0] = p[..., 0] * c - p[..., 1] * s
    out[..., 1] = p[..., 0] * s + p[..., 1] * c
    out[..., 2] = p[..., 2] - TUBE_LEN
    return out


def height(tris):
    """Height of each corner above the top of the tube once the pole leans back by LEAN."""
    return tris[..., 0] * sin(LEAN) + tris[..., 2] * cos(LEAN)


def build():
    top = [(name, color, visible, printed, "top", viewer.triangles(shape, 0.03 if printed else 0.15, 0.12)) for name, color, visible, printed, shape in top_items()]
    raw = [(name, color, visible, printed, viewer.triangles(shape, 0.05 if printed else 0.15, 0.15)) for name, color, visible, printed, shape in tip_items()]

    # which way round the wheel end goes on the tube: the wheel has to reach the ground first
    best = None
    for turn in (0.0, 180.0):
        wheel = min(height(onto_tube(t, turn)).min() for name, *_, t in raw if name.startswith("Omni wheel"))
        rest = min(height(onto_tube(t, turn)).min() for name, *_, t in raw if not name.startswith("Omni wheel"))
        side = "in front of" if turn == 0 else "behind"
        if rest > wheel:
            print(f"  motor {side} the tube: the wheel reaches the ground first, with {rest - wheel:.1f} mm to spare")
        else:
            print(f"  motor {side} the tube: something else at the wheel end is {wheel - rest:.1f} mm lower than the wheel")
        if best is None or rest - wheel > best[1]:
            best = (turn, rest - wheel, wheel)
    turn, margin, ground_h = best
    print(f"  drawn with the wheel end turned {turn:.0f} degrees; the wheel touches the ground with {margin:.1f} mm to spare, for a {WHEEL_D:.0f} mm wheel")
    tip = [(name, color, visible, printed, "tip", onto_tube(t, turn)) for name, color, visible, printed, t in raw]

    pole = [(name, color, visible, printed, "pole", viewer.triangles(shape, 0.05 if printed else 0.2, 0.15))
            for name, color, visible, printed, shape in pole_items()]

    # ground under the wheel, level once the pole leans
    wheel_tris = next(t for name, *_, t in tip if name.startswith("Omni wheel"))
    low = wheel_tris.reshape(-1, 3)[height(wheel_tris).argmin()]
    normal = np.array([sin(LEAN), 0.0, cos(LEAN)])
    centre = low - normal * 1.0
    disc = Pos(*[float(v) for v in centre]) * Rot(0, ws.STICK_LEAN_DEG, 0) * Cylinder(GROUND_R, 2.0)
    ground = ("Ground", (0.70, 0.72, 0.75), True, False, "ground", viewer.triangles(disc, 0.5))
    reach = -ground_h
    print(f"  top of the tube is {reach:.0f} mm above the ground with the pole leaning {ws.STICK_LEAN_DEG:.0f} degrees")

    scene = top + tip + pole + [ground]
    scene.sort(key=lambda item: not item[3])  # printed parts first
    out = []
    for name, color, visible, printed, group, tris in scene:
        pos, nor = viewer.encode(tris)
        out.append({"name": name, "color": color, "visible": visible, "printed": printed, "group": group, "leanOnly": group == "ground", "pos": pos, "nor": nor})
    print(f"  {sum(len(t) for *_, t in scene):,} triangles in {len(scene)} parts")
    return out, reach


PANEL = """<div id="panel"><h1>SightSense cane assembly</h1>
  <div class="row" id="views"></div>
  <div class="row"><button id="zin" aria-label="Zoom in">Zoom +</button><button id="zout" aria-label="Zoom out">Zoom −</button><button id="lean">Lean pole: on</button></div>
  <details open id="parts"><summary>Parts</summary><div id="list"></div>
  <div class="row"><button id="only">Printed parts only</button><button id="all">Show all</button></div></details>
  <div id="size"></div>
  <details open id="about"><summary>About this model</summary><div id="note">__NOTE__</div></details></div>
"""

SWAPS = (
    ("<title>Walking Stick CAD</title>", "<title>SightSense Cane Assembly</title>"),
    ("  #help {", "  h1 { margin: 2px 0 0; font-size: 15px; font-weight: 600; }\n"
                "  details { margin-top: 8px; }\n"
                "  .head { margin: 8px 0 2px; font-size: 12px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; color: var(--muted); }\n"
                "  #note { margin-top: 4px; color: var(--muted); font-size: 12.5px; }\n  #help {"),
    ("let yaw = -0.9, pitch = 0.25, dist = 600, target = [0, 0, 0], lean = false;",
     "let yaw = -1.05, pitch = 0.16, dist = 600, target = [0, 0, 0], lean = true;\n"
     "const shown = p => p.visible && (lean || !p.leanOnly);"),
    ("function bounds() {", "function bounds(group) {"),
    ("  for (const p of PARTS) if (p.visible) for (let k = 0; k < 3; k++) { lo[k]",
     "  for (const p of PARTS) if (shown(p) && !p.leanOnly && (!group || !p.group || p.group === group)) for (let k = 0; k < 3; k++) { lo[k]"),
    ("function fit() {\n  const [lo, hi] = bounds();", "function fit(group) {\n  const [lo, hi] = bounds(group);"),
    ("  for (const p of PARTS) { if (!p.visible) continue;", "  for (const p of PARTS) { if (!shown(p)) continue;"),
    ("PARTS.forEach((p, i) => {\n  const l = document.createElement('label')",
     "PARTS.forEach((p, i) => {\n"
     "  if (i === 0 || PARTS[i - 1].printed !== p.printed) { const h = document.createElement('div'); h.className = 'head';\n"
     "    h.textContent = p.printed ? 'Printed' : 'Bought parts and stand-ins'; list.append(h); }\n"
     "  const l = document.createElement('label')"),
    ("setVisible((p, i) => i < 3)", "setVisible(p => p.printed)"),
    ("document.getElementById('fit').onclick = fit;",
     "for (const [name, group] of [['Whole cane', null], ['Handle and phone', 'top'], ['Wheel end', 'tip']]) {\n"
     "  const b = document.createElement('button'); b.textContent = name; b.onclick = () => fit(group); document.getElementById('views').append(b); }"),
    ("document.getElementById('parts').open = false;", "{ document.getElementById('parts').open = false; document.getElementById('about').open = false; }"),
    # a link ending in #handle or #wheel opens on that end of the cane
    ("sizeText(); fit();\n</script>", "sizeText(); fit({'#handle': 'top', '#wheel': 'tip'}[location.hash] || null);\n</script>"),
)

NOTE = (f"{TUBE_SECTIONS} tubes of {SECTION_LEN:.0f} mm, joined by the keyed coupler: hide a tube to see the inserts inside it. "
        "The wheel and the phone are stand-ins: their sizes are not measured. "
        "Motor sizes are from a published drawing. Research prototype: nothing here has been printed or load tested.")


def page_from(data):
    page = viewer.HTML.replace("__DATA__", json.dumps(data)).replace("__LEAN__", str(ws.STICK_LEAN_DEG))
    start, end = page.index('<div id="panel">'), page.index('<div id="help">')
    page = page[:start] + PANEL.replace("__NOTE__", NOTE) + page[end:]
    for old, new in SWAPS:
        assert page.count(old) == 1, old
        page = page.replace(old, new)
    return page


if __name__ == "__main__":
    data, reach = build()
    page = page_from(data)
    out = Path(__file__).parent / "assembly_viewer.html"
    out.write_text(viewer.WRAP.format(page))
    print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB)")
    if len(sys.argv) > 1:  # optional second copy without the wrapper, for hosting as a page fragment
        Path(sys.argv[1]).write_text(page)

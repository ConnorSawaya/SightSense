"""Writes wheel_adapter_viewer.html: a self-contained 3D viewer for the wheel adapter.

Run:  python wheel_adapter_viewer.py     then open wheel_adapter_viewer.html in a browser.
"""

import json
import sys
from pathlib import Path

import wheel_adapter as wa  # also puts the handle and phone mount's folder on the path

import viewer  # noqa: E402
import walking_stick as ws  # noqa: E402
from walking_stick import Pos, Rot  # noqa: E402


def build():
    shaft_in, bore_depth, hex_end = wa.layout()
    clamp, wheel = wa.ref_screws()
    clamp_z, slot_x, _, _ = wa.clamp_layout()
    far = bore_depth + wa.wheel_screw_len()  # tip of the wheel screw
    cap_z = far - 4.0 - wa.CAP_T  # cap sits just under the far nut
    nuts = [
        Pos(slot_x + wa.NUT_T - 2.45, 0, clamp_z) * Rot(0, 0, 90) * ws.ref_nut(5.5, 2.4, 3),  # drawn up against the outer face
        Pos(0, 0, far - 1.0) * Rot(90, 0, 0) * ws.ref_nut(5.5, 2.4, 3),
    ]
    cap = Pos(0, 0, cap_z + wa.CAP_T) * Rot(180, 0, 0) * wa.make_wheel_cap()
    scene = [
        ("Wheel adapter (printed)", (0.95, 0.55, 0.15), True, wa.make_wheel_adapter()),
        ("Far-side cap (printed)", (0.25, 0.68, 0.45), True, cap),
        ("Motor shaft, 6 mm D (reference)", (0.55, 0.56, 0.60), True, wa.ref_shaft()),
        ("M3 screws (reference)", (0.82, 0.80, 0.72), True, [clamp, wheel]),
        ("M3 nuts (reference)", (0.30, 0.62, 0.85), True, nuts),
        ("Fit-test piece (printed)", (0.75, 0.25, 0.30), False, Pos(32, 0, 0) * wa.make_fit_test()),
    ]
    out = []
    for name, color, visible, shape in scene:
        pos, nor = viewer.mesh(shape)
        out.append({"name": name, "color": color, "visible": visible, "pos": pos, "nor": nor})
    return out


if __name__ == "__main__":
    page = viewer.HTML.replace("__DATA__", json.dumps(build())).replace("__LEAN__", "0")
    for old, new in (
        ("<title>Walking Stick CAD</title>", "<title>Wheel Adapter CAD</title>"),
        ("<summary>Walking stick CAD</summary>", "<summary>Wheel adapter CAD</summary>"),
        ('<button id="lean">Lean pole: off</button>', '<button id="lean" hidden>Lean</button>'),
        ("setVisible((p, i) => i < 3)", "setVisible((p, i) => i < 2)"),
        ("let yaw = -0.9, pitch = 0.25", "let yaw = -0.7, pitch = 0.45"),
    ):
        assert old in page, old
        page = page.replace(old, new)
    out = Path(__file__).parent / "wheel_adapter_viewer.html"
    out.write_text(viewer.WRAP.format(page))
    print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB)")
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(page)

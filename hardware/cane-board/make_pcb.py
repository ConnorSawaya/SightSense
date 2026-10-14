"""Places the cane board's parts on a board and renders it in 3D.

Takes the parts and nets from make_board.py, loads each footprint from KiCad's
libraries, puts it where the table below says, joins every pad to its net, and
writes cane-board.kicad_pcb. Then runs KiCad's design rules check and renders
the pictures in previews/.

Run it with the Python that ships inside KiCad, which has the board library:

    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 make_pcb.py

The board is placed, not routed: only the ground fill joins anything. Tracks
drawn in KiCad are lost when this is run again.
"""

import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

import pcbnew

sys.argv = sys.argv[:1]
with contextlib.redirect_stdout(io.StringIO()):
    import make_board as mb

    mb.write_drv8876()
    mb.draw()

HERE = Path(__file__).resolve().parent
NAME = mb.NAME
W, H, RADIUS = 40.0, 100.0, 2.0  # board size and corner radius, mm

# Where each part goes: centre of its courtyard in mm from the board's top-left corner, and its turn in degrees.
# The top edge (y = 0) points up the cane, toward the handle. The bottom edge is the motor end.
PLACE = {
    # Processor. Its aerial is the top 6 mm; nothing else sits beside that strip.
    "U1": (20.0, 12.75, 0),
    "J3": (4.0, 12.0, 90), "J4": (4.0, 21.0, 90),            # kill switch, talk button: wires go up to the handle
    "C20": (8.8, 8.6, 90), "C19": (8.8, 12.9, 90),            # processor supply
    "R28": (8.8, 17.2, 90), "R29": (8.8, 20.4, 90), "C24": (8.8, 23.6, 90),
    "J11": (35.24, 13.0, 90),                                 # firmware socket, on the right edge
    "D8": (32.2, 20.1, 0), "D9": (32.2, 21.9, 0), "R19": (37.6, 20.1, 0), "R20": (37.6, 21.9, 0), "D6": (34.6, 24.6, 0),
    "SW2": (15.0, 29.5, 0), "SW1": (25.0, 29.5, 0),
    "R21": (12.0, 34.3, 0), "C21": (15.3, 34.3, 0), "R22": (18.6, 34.3, 0), "R23": (21.9, 34.3, 0), "LED3": (25.2, 34.3, 0),
    "R24": (28.5, 34.3, 0), "R25": (31.8, 34.3, 0), "C22": (35.1, 34.3, 0),
    "R26": (28.5, 36.3, 0), "R27": (31.8, 36.3, 0), "C23": (35.1, 36.3, 0),
    # Handle buzzer.
    "J7": (4.0, 38.0, 90), "Q3": (10.0, 39.5, 0), "R32": (14.2, 38.6, 0), "R33": (14.2, 40.4, 0), "D7": (11.5, 43.2, 0),
    # 3.3 V.
    "U4": (19.0, 40.0, 0), "C15": (19.0, 43.4, 0), "D5": (24.2, 38.9, 0), "C16": (24.2, 41.7, 0),
    "R14": (28.6, 38.6, 0), "LED2": (28.6, 40.4, 0),
    # Phone socket: pads only.
    "J10": (35.8, 46.0, 90), "U5": (28.0, 44.6, 0), "C17": (28.0, 47.8, 0), "C18": (28.0, 50.4, 0),
    "R15": (23.4, 45.0, 0), "R16": (23.4, 46.8, 0), "R17": (23.4, 48.6, 0), "R18": (23.4, 50.4, 0),
    # 12 V to 5 V.
    "J8": (2.3, 47.5, 0), "J6": (2.3, 58.5, 0), "R30": (6.2, 61.5, 0), "R31": (6.2, 63.2, 0),
    "C10": (9.5, 46.6, 0), "C11": (14.2, 46.4, 0), "U3": (10.0, 50.2, 0),
    "C12": (14.5, 49.3, 0), "C25": (14.5, 51.1, 0), "R12": (18.0, 49.3, 0), "R13": (18.0, 51.1, 0),
    "L1": (9.0, 56.2, 0), "C13": (15.2, 54.9, 0), "C14": (15.2, 57.5, 0),
    "SW3": (36.97, 57.5, 90),                                # power switch, slider on the right edge
    # Motor supply and kill switch.
    "R4": (28.1, 59.6, 0), "LED1": (31.4, 59.6, 0),
    "R2": (21.5, 61.6, 0), "C26": (24.8, 61.6, 0), "R3": (28.1, 61.6, 0),
    "Q2": (24.0, 66.0, 0), "C3": (33.5, 71.0, 0), "C27": (33.5, 73.6, 0),      # C3 and C27 sit by the driver's supply pin
    # Battery in.
    "J5": (4.0, 71.5, 90),                                    # encoder, toward the motor
    "C1": (13.5, 65.2, 0), "R34": (12.0, 71.2, 0), "R1": (16.5, 71.2, 0), "Q1": (14.5, 74.3, 0), "Q4": (19.5, 74.3, 0),
    "F1": (13.2, 80.5, 0), "D1": (4.2, 83.5, 90), "J1": (12.9, 91.9, 90),
    # Motor driver.
    "U2": (27.0, 78.5, 0), "C4": (21.5, 77.2, 0), "C5": (21.5, 79.0, 0), "C6": (21.5, 80.8, 0),
    "R5": (32.6, 76.4, 0), "R6": (32.6, 78.2, 0), "C7": (32.6, 80.0, 0), "R7": (32.6, 81.8, 0),
    "R8": (36.0, 76.4, 0), "R9": (36.0, 78.2, 0), "R10": (36.0, 80.0, 0), "C8": (36.0, 81.8, 0),
    "D4": (36.2, 85.0, 0), "C9": (32.6, 84.0, 0), "R11": (32.6, 85.8, 0), "JP1": (26.0, 85.8, 0),
    "J2": (27.0, 94.5, 0),
    "H1": (3.5, 29.5, 0), "H2": (36.5, 29.5, 0), "H3": (3.5, 96.5, 0), "H4": (36.5, 96.5, 0),
}
BY_ORIGIN = {"U1"}  # placed by its own origin: its courtyard includes the clear space the aerial wants

# Words printed on the board: text, x, y, turn, height. Part numbers are printed only for the chips.
SILK = [
    ("SightSense", 26.0, 54.3, 0, 1.3), ("cane board v0.1", 26.0, 56.4, 0, 0.9),
    ("KILL", 4.0, 6.9, 0, 0.9), ("TALK", 4.0, 26.1, 0, 0.9), ("BUZZ", 4.0, 33.0, 0, 0.9),
    ("USB", 35.5, 6.9, 0, 0.9), ("BOOT", 9.2, 29.5, 90, 0.8), ("RST", 30.9, 29.5, 90, 0.8),
    ("SER", 5.3, 47.5, 90, 0.8), ("I2C", 4.85, 56.0, 90, 0.8), ("ENC", 8.5, 70.6, 90, 0.8),
    ("PWR", 33.2, 57.5, 90, 0.8), ("BATT 12V", 20.0, 93.5, 90, 0.9), ("MOTOR", 27.0, 88.2, 0, 0.9),
]
# KiCad ships no 3D model for these parts. A part of the same kind and size stands in for each in the pictures.
MODELS = "${KICAD10_3DMODEL_DIR}/"
STAND_IN = {"J11": (MODELS + "Connector_USB.3dshapes/USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.step", 0),
            "SW1": (MODELS + "Button_Switch_SMD.3dshapes/SW_SPST_TL3342.step", 0),
            "SW2": (MODELS + "Button_Switch_SMD.3dshapes/SW_SPST_TL3342.step", 0),
            "SW3": (MODELS + "Button_Switch_SMD.3dshapes/SW_SPDT_PCM12.step", 0)}


def mm(v):
    return pcbnew.FromMM(float(v))


def point(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def net_name(net):
    return net if net in mb.POWER else "/" + net


def build():
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    nets = {}
    for name in sorted(set(mb.expect.values())):
        nets[name] = pcbnew.NETINFO_ITEM(board, net_name(name))
        board.Add(nets[name])

    library = str(mb.KICAD / "footprints")
    refs = {p["ref"]: p for p in mb.parts}
    holes = {f"H{i}": {"ref": f"H{i}", "value": "M3", "fp": "MountingHole:MountingHole_3.2mm_M3", "fitted": True} for i in range(1, 5)}
    if set(refs) - set(PLACE):
        sys.exit(f"no place given for {sorted(set(refs) - set(PLACE))}")
    for ref, (x, y, turn) in PLACE.items():
        one = refs.get(ref) or holes[ref]
        lib, name = one["fp"].split(":")
        fp = pcbnew.FootprintLoad(f"{library}/{lib}.pretty", name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(one["value"])
        fp.SetPath(pcbnew.KIID_PATH("/" + mb.uid("s", ref)))
        fp.SetOrientationDegrees(turn)
        fp.SetPosition(point(0, 0))
        if ref in BY_ORIGIN:
            fp.SetPosition(point(x, y))
        else:
            fp.BuildCourtyardCaches()
            box = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
            cx, cy = (box.GetLeft() + box.GetRight()) / 2, (box.GetTop() + box.GetBottom()) / 2
            fp.SetPosition(pcbnew.VECTOR2I(int(mm(x) - cx), int(mm(y) - cy)))
        fp.Reference().SetVisible(ref.startswith("U"))
        if ref in STAND_IN:
            model = pcbnew.FP_3DMODEL()
            model.m_Filename, turn_z = STAND_IN[ref]
            model.m_Rotation = pcbnew.VECTOR3D(0, 0, turn_z)
            fp.Models().clear()
            fp.Models().push_back(model)
        if not one["fitted"]:
            fp.SetDNP(True)
            fp.SetExcludedFromBOM(True)
            fp.SetExcludedFromPosFiles(True)
        for pad in fp.Pads():
            net = mb.expect.get((ref, pad.GetNumber()))
            if net:
                pad.SetNet(nets[net])
        board.Add(fp)

    # Outline: a rectangle with rounded corners.
    r = RADIUS
    k = r * (1 - 0.7071068)
    def line(a, b):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(point(*a)); s.SetEnd(point(*b))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        board.Add(s)
    def arc(a, m, b):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetArcGeometry(point(*a), point(*m), point(*b))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        board.Add(s)
    line((r, 0), (W - r, 0)); arc((W - r, 0), (W - k, k), (W, r))
    line((W, r), (W, H - r)); arc((W, H - r), (W - k, H - k), (W - r, H))
    line((W - r, H), (r, H)); arc((r, H), (k, H - k), (0, H - r))
    line((0, H - r), (0, r)); arc((0, r), (k, k), (r, 0))

    # Ground on both sides. The processor's footprint keeps copper away from its aerial.
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNetCode(nets["GND"].GetNetCode())
        outline = zone.Outline()
        outline.NewOutline()
        for x, y in ((0, 0), (W, 0), (W, H), (0, H)):
            outline.Append(mm(x), mm(y))
        board.Add(zone)

    for text, x, y, turn, size in SILK:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetPosition(point(x, y))
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(size * 0.15))
        t.SetTextAngleDegrees(turn)
        board.Add(t)

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    path = HERE / f"{NAME}.kicad_pcb"
    pcbnew.SaveBoard(str(path), board)
    return path


def check(path):
    report = HERE / "export" / "drc.json"
    subprocess.run([mb.CLI, "pcb", "drc", "--format", "json", "--severity-all", "--all-track-errors", "-o", str(report), str(path)],
                   capture_output=True, text=True)
    data = json.loads(report.read_text())
    kinds = {}
    for v in data.get("violations", []):
        kinds.setdefault(v["type"], []).append("; ".join(i.get("description", "") for i in v.get("items", [])))
    report.unlink()
    return kinds, len(data.get("unconnected_items", []))


def render(path):
    out = HERE / "previews"
    out.mkdir(exist_ok=True)
    shots = {"board-top.png": ["--side", "top", "--width", "1100", "--height", "2400", "--zoom", "0.95"],
             "board-3d.png": ["--side", "top", "--perspective", "--rotate", "-55,0,-35", "--width", "2000", "--height", "1500",
                              "--zoom", "1.25"],
             "board-3d-handle-end.png": ["--side", "top", "--perspective", "--rotate", "-60,0,150", "--width", "2000",
                                        "--height", "1500", "--zoom", "1.25"]}
    for name, args in shots.items():
        done = subprocess.run([mb.CLI, "pcb", "render", "--quality", "high", "--background", "opaque", *args, "-o", str(out / name),
                               str(path)], capture_output=True, text=True)
        if done.returncode:
            print(f"render {name} failed: {done.stderr.strip()[-300:]}")


if __name__ == "__main__":
    board = build()
    kinds, open_nets = check(board)
    print(f"board {W:g} x {H:g} mm, {len(PLACE)} footprints")
    print(f"not yet joined by copper: {open_nets} connections")
    for kind, found in sorted(kinds.items()):
        print(f"  {kind}: {len(found)}")
        if kind in ("courtyards_overlap", "malformed_courtyard", "pth_inside_courtyard", "npth_inside_courtyard", "copper_edge_clearance",
                    "silk_edge_clearance", "hole_clearance", "items_not_allowed"):
            for line in found[:12]:
                print("     " + line)
    if "--no-render" not in sys.argv:
        render(board)

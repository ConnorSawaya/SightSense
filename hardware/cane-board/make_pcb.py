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
W, H, RADIUS = 46.0, 100.0, 2.0  # board size and corner radius, mm

# Where each part goes: centre of its courtyard in mm from the board's top-left corner, and its turn in degrees.
# The top edge (y = 0) points up the cane, toward the handle. The bottom edge is the motor end.
PLACE = {
    # Processor. Its aerial is the top 6 mm; nothing else sits beside that strip.
    "U1": (23, 12.75, 0),
    "J3": (4.6, 12.0, 90), "J4": (4.6, 21.0, 90),            # kill switch, talk button: wires go up to the handle
    "C20": (10.12, 8.6, 90), "C19": (10.12, 12.9, 90),            # processor supply
    "R28": (10.12, 17.2, 90), "R29": (10.12, 20.4, 90), "C24": (10.12, 23.6, 90),
    "J11": (41.24, 13.0, 90),                                 # firmware socket, on the right edge
    "D8": (37.03, 20.1, 0), "D9": (37.03, 21.9, 0), "R19": (43.24, 20.1, 0), "R20": (43.24, 21.9, 0), "D6": (39.79, 24.6, 0),
    "SW2": (17.25, 29.5, 0), "SW1": (28.75, 29.5, 0),
    "R21": (13.8, 34.3, 0), "C21": (17.59, 34.3, 0), "R22": (21.39, 34.3, 0), "R23": (25.18, 34.3, 0), "LED3": (28.98, 34.3, 0),
    "R24": (32.77, 34.3, 0), "R25": (36.57, 34.3, 0), "C22": (40.37, 34.3, 0),
    "R27": (36.57, 36.3, 0), "C23": (40.37, 36.3, 0),
    # Handle buzzer.
    "J7": (4.6, 38.0, 90), "Q3": (11.5, 39.5, 0), "R32": (16.33, 38.6, 0), "R33": (16.33, 40.4, 0), "D7": (13.22, 43.2, 0),
    # 3.3 V.
    "U4": (21.85, 40.0, 0), "C15": (21.85, 43.4, 0), "D5": (27.83, 38.9, 0), "C16": (27.83, 41.7, 0),
    "R14": (32.89, 38.6, 0), "LED2": (32.89, 40.4, 0),
    # Phone socket: pads only.
    "J10": (41.8, 46.0, 90), "U5": (32.2, 44.6, 0), "C17": (32.2, 47.8, 0), "C18": (32.2, 50.4, 0),
    "R15": (26.91, 45.0, 0), "R16": (26.91, 46.8, 0), "R17": (26.91, 48.6, 0), "R18": (26.91, 50.4, 0),
    # 12 V to 5 V.
    "J8": (2.64, 47.5, 0), "J6": (2.64, 58.5, 0), "R30": (7.13, 61.5, 0), "R31": (7.13, 63.2, 0),
    "C10": (10.92, 46.6, 0), "C11": (16.33, 46.4, 0), "U3": (13.0, 52.5, 0),      # sealed 5 V module, pins along the bottom
    "R12": (20.7, 47.6, 0),
    "C13": (22.6, 54.9, 0), "C14": (22.6, 57.5, 0),
    "SW3": (42.97, 57.5, 90),                                # power switch, slider on the right edge
    # Motor supply and kill switch.
    "R4": (32.31, 59.6, 0), "LED1": (36.11, 59.6, 0),
    "R2": (24.72, 61.6, 0), "C26": (28.52, 61.6, 0), "R3": (32.31, 61.6, 0),
    "Q2": (27.6, 66.0, 0), "C3": (29.32, 72.6, 0), "C27": (34.84, 72.6, 0), "R26": (34.5, 69.5, 0),  # motor-supply capacitors between the switch and the driver
    # Battery in.
    "J5": (4.6, 71.5, 90),                                    # encoder, toward the motor
    "C1": (15.52, 65.2, 0), "R34": (13.8, 71.2, 0), "R1": (18.97, 71.2, 0), "Q1": (16.67, 74.3, 0), "Q4": (22.42, 74.3, 0),
    "F1": (15.18, 80.5, 0), "D1": (4.83, 83.5, 90), "J1": (14.83, 91.9, 90),
    # Motor driver.
    "U2": (31.05, 78.5, 180), "C4": (23.92, 77.2, 180), "C5": (23.92, 79.0, 0), "C6": (23.92, 80.8, 0),
    "R5": (38.41, 76.4, 0), "R6": (38.41, 78.2, 0), "C7": (38.41, 80.0, 0), "R7": (38.41, 81.8, 0),
    "R8": (42.55, 76.4, 0), "R9": (42.55, 78.2, 0), "R10": (42.55, 80.0, 0), "C8": (42.55, 81.8, 0),
    "D4": (42.55, 85.2, 0), "C9": (38.41, 84.0, 0), "R11": (38.41, 85.8, 0), "JP1": (29.9, 85.8, 0),
    "J2": (31.05, 94.5, 180),  # pad 1 (MOT_A) on the right, under the driver's MOT_A pin
    "H1": (3.5, 29.5, 0), "H2": (42.5, 29.5, 0), "H3": (3.5, 96.5, 0), "H4": (42.5, 96.5, 0),
}
BY_ORIGIN = {"U1"}  # placed by its own origin: its courtyard includes the clear space the aerial wants

# Words printed on the board: text, x, y, turn, height. JLCPCB wants text 1.0 mm or taller with 0.15 mm lines.
# Part numbers are printed only for the chips.
SILK = [
    ("SightSense", 29.9, 54.3, 0, 1.3), ("board v0.1", 29.9, 56.2, 0, 1.0),
    ("KILL", 4.6, 6.9, 0, 1.0), ("TALK", 4.6, 26.1, 0, 1.0), ("BUZZ", 4.6, 33.0, 0, 1.0),
    ("USB", 40.82, 6.9, 0, 1.0), ("BOOT", 10.58, 29.5, 90, 1.0), ("RST", 35.53, 29.5, 90, 1.0),
    ("SER", 6.09, 47.5, 90, 1.0), ("I2C", 5.58, 56.0, 90, 1.0), ("ENC", 9.77, 70.6, 90, 1.0),
    ("PWR", 38.18, 57.5, 90, 1.0), ("BATT 12V", 23.0, 93.5, 90, 1.0), ("MOTOR", 31.05, 88.2, 0, 1.0),
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
        fp.Reference().SetVisible(ref.startswith("U") and ref != "U3")  # the module has its own print; U3 would sit on C10
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
            for pad in fp.Pads():  # no solder paste where no part goes, so the stencil leaves those pads bare
                layers = pad.GetLayerSet()
                layers.RemoveLayer(pcbnew.F_Paste)
                pad.SetLayerSet(layers)
        for pad in fp.Pads():
            net = mb.expect.get((ref, pad.GetNumber()))
            if net:
                pad.SetNet(nets[net])
        if ref == "J1":  # XKB's drawing asks for 1.0 x 3.5 mm slots; KiCad's generic jack has 3.0 mm ones
            for pad in fp.Pads():
                long_x = pad.GetDrillSize().x > pad.GetDrillSize().y
                pad.SetDrillSize(pcbnew.VECTOR2I(mm(3.5 if long_x else 1.0), mm(1.0 if long_x else 3.5)))
                pad.SetSize(pcbnew.F_Cu, pcbnew.VECTOR2I(mm(4.0 if long_x else 3.5), mm(3.5 if long_x else 4.0)))
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
        t.SetTextThickness(mm(max(0.15, size * 0.15)))
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

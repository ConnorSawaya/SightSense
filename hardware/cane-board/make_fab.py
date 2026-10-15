"""Writes the files JLCPCB needs to make and assemble the cane board, into export/fab/.

Run it with the Python inside KiCad, which has the board library:

    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 make_fab.py

Gerbers and drill file (zipped for upload), the placement file in JLCPCB's column
names, and a copy of the bill of materials. Needs kicad-cli (KiCad 10).

The placement file is not KiCad's own. KiCad gives each part's origin, which for
the connectors and the 5 V module is pin 1, and its own rotation. JLCPCB wants the
centre of the part's body, and measures rotation from its own library footprint,
which for some parts is KiCad's turned round. ROTATE below holds those turns.
"""

import csv
import math
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
BOARD = HERE / "cane-board.kicad_pcb"
OUT = HERE / "export" / "fab"
CLI = os.environ.get("KICAD_CLI", "kicad-cli")
LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"

# Degrees to add to KiCad's rotation so JLCPCB's footprint lands the way KiCad's does, by footprint.
# Read on October 14, 2026 from JLCPCB's footprint previews for the exact LCSC parts on this board
# (jlcpcb.com/user-center/lcsvg/svg.html?code=...), against KiCad 10's footprints:
#   AO3401A C15127, AO3400A C20917, BAT54S C7420333: pin 1 bottom right, KiCad top left -> 180
#   AP2112K C51118, DRV8876 C575551: pins 1 up along the bottom, KiCad down the left side -> 270
#   JST XH C158012, C144395 and XT30 C108769: pin 1 and the housing's key on the other side -> 180
#   pin headers C2691448, C2937625: a row with pin 1 on the left, KiCad a column with pin 1 at the top -> 270
#     (missed on the first pass and found by an outside review; a header turned a quarter misses its holes)
# Checked and the same as KiCad (0): the LEDs C2286, B5819W C8598, SMBJ15A C19077569 (cathode left),
# the 220 uF can C724620 (+ left), USB-C C165948 (A1 top left), ESP32-S3 C2913197 (aerial up),
# MSK12C02 C431540, K7805 C2992391 (pin 1 left) and the barrel jack C381116.
# Also the same as KiCad: the push buttons C318884 (pins 1-2 along the top, as KiCad's pads 1), the fuse
# C20539726, the USB TVS diodes C7420372, and the 0603 and 1206 parts (pads side by side).
# The generic tables in other tools disagree for SOT-23-5 (180), the electrolytic (180) and this USB-C (180);
# those would have turned U4 a quarter, and C1 and J11 round. Recheck in JLCPCB's preview before paying.
ROTATE = {
    "SOT-23": 180,
    "SOT-23-5": 270,
    "HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask3x3mm_ThermalVias": 270,
    "JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical": 180,
    "JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical": 180,
    "AMASS_XT30UPB-F_1x02_P5.0mm_Vertical": 180,
    "PinHeader_1x03_P2.54mm_Vertical": 270,
    "PinHeader_1x04_P2.54mm_Vertical": 270,
}

# Where the body's centre really is, in mm in the footprint's own frame, where its outline misleads (found by
# an outside review, October 15). SW3: KiCad's outline includes the lever; the housing is centred on the two
# locating holes, which is the footprint's origin. U3: the outline is RECOM's 11.6 x 8.5 mm module; the
# YLPTEC K7805's drawing (page 3) gives 11.5 x 7.55 mm with the pins 2.00 mm from one face and 3.20 and 3.22 mm
# from the ends, so its centre is 2.55 mm along from pin 1 and 1.775 mm into the body.
CENTRE = {
    "SW_SPDT_Shouhan_MSK12C02": (0.0, 0.0),
    "Converter_DCDC_RECOM_R-78E-0.5_THT": (2.55, -1.775),
}


def run(*args):
    done = subprocess.run([CLI, *args], capture_output=True, text=True)
    if done.returncode:
        sys.exit(f"kicad-cli {' '.join(args)} failed:\n{done.stdout}{done.stderr}")


def body_centre(fp):
    """Centre of the part's outline on the fabrication layer, or of its pads if it has none."""
    name = fp.GetFPIDAsString().split(":")[1]
    if name in CENTRE:  # a point in the footprint's frame, turned and moved as the footprint is
        dx, dy = CENTRE[name]
        a = math.radians(fp.GetOrientationDegrees())
        o = fp.GetPosition()
        return pcbnew.VECTOR2I(o.x + pcbnew.FromMM(dx * math.cos(a) + dy * math.sin(a)),
                               o.y + pcbnew.FromMM(-dx * math.sin(a) + dy * math.cos(a)))
    shapes = [d for d in fp.GraphicalItems() if d.GetLayer() == pcbnew.F_Fab and d.Type() == pcbnew.PCB_SHAPE_T]
    items = shapes or list(fp.Pads())
    box = items[0].GetBoundingBox()
    for item in items[1:]:
        box.Merge(item.GetBoundingBox())
    return box.GetCenter()


def placement(path):
    """JLCPCB's placement file: every fitted part on the top, by body centre, with JLCPCB's rotation."""
    board = pcbnew.LoadBoard(str(BOARD))
    rows = []
    for fp in board.GetFootprints():
        if fp.IsDNP() or fp.IsExcludedFromPosFiles() or fp.IsBoardOnly():
            continue
        name = fp.GetFPIDAsString().split(":")[1]
        turn = (fp.GetOrientationDegrees() + ROTATE.get(name, 0)) % 360
        c = body_centre(fp)
        rows.append((fp.GetReference(), pcbnew.ToMM(c.x), -pcbnew.ToMM(c.y), turn))  # y up, as in the Gerbers
    rows.sort(key=lambda r: (r[0].rstrip("0123456789"), int(r[0][len(r[0].rstrip("0123456789")):] or 0)))
    with open(path, "w", newline="") as f:
        out = csv.writer(f)
        out.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for ref, x, y, turn in rows:
            out.writerow([ref, f"{x:.4f}mm", f"{y:.4f}mm", "Top", f"{turn:.0f}"])
    return len(rows)


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    gerbers = OUT / "gerbers"
    gerbers.mkdir(parents=True)
    run("pcb", "export", "gerbers", "--layers", LAYERS, "--subtract-soldermask", "--no-x2", "-o", str(gerbers) + "/", str(BOARD))
    run("pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th", "--generate-map", "--map-format", "gerberx2",
        "-o", str(gerbers) + "/", str(BOARD))
    with zipfile.ZipFile(OUT / "cane-board-gerbers.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(gerbers.iterdir()):
            z.write(f, f.name)
    parts = placement(OUT / "cane-board-cpl.csv")
    shutil.copy(HERE / "export" / "bom-jlcpcb.csv", OUT / "cane-board-bom.csv")
    print("wrote", ", ".join(sorted(p.name for p in OUT.iterdir())))
    print("gerber files:", len(list(gerbers.iterdir())), "; parts placed:", parts)


if __name__ == "__main__":
    main()

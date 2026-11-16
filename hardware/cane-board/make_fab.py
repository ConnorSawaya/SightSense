"""Writes the files JLCPCB needs to make and assemble the cane board, into export/fab/.

Run it with the Python inside KiCad, which has the board library:

    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 make_fab.py

Gerbers and drill file (zipped for upload), the placement file in JLCPCB's column
names, and a copy of the bill of materials. Needs kicad-cli (KiCad 10).

The placement file is not KiCad's own. KiCad gives each part's origin, which for
the connectors and the 5 V module is pin 1, and its own rotation. JLCPCB centres
its footprints on their pads, and measures rotation from its own library footprint,
which for some parts is KiCad's turned round. ROTATE below holds those turns.
"""

import csv
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

def run(*args):
    done = subprocess.run([CLI, *args], capture_output=True, text=True)
    if done.returncode:
        sys.exit(f"kicad-cli {' '.join(args)} failed:\n{done.stdout}{done.stderr}")


def pad_centre(fp):
    """Centre of the part's pads. JLCPCB's footprints are centred on their pads, not on the body: in its
    placement viewer on October 15, body centres put U1 3.6 mm, J11 1.5 mm, J1 about 4 mm and U3 1.8 mm off
    their pads, and pad centres are what line them up."""
    pads = list(fp.Pads())
    box = pads[0].GetBoundingBox()
    for pad in pads[1:]:
        box.Merge(pad.GetBoundingBox())
    return box.GetCenter()


def placement(path):
    """JLCPCB's placement file: every fitted part on the top, by pad centre, with JLCPCB's rotation."""
    board = pcbnew.LoadBoard(str(BOARD))
    rows = []
    for fp in board.GetFootprints():
        if fp.IsDNP() or fp.IsExcludedFromPosFiles() or fp.IsBoardOnly():
            continue
        name = fp.GetFPIDAsString().split(":")[1]
        turn = (fp.GetOrientationDegrees() + ROTATE.get(name, 0)) % 360
        c = pad_centre(fp)
        rows.append((fp.GetReference(), pcbnew.ToMM(c.x), -pcbnew.ToMM(c.y), turn))  # y up, as in the Gerbers
    rows.sort(key=lambda r: (r[0].rstrip("0123456789"), int(r[0][len(r[0].rstrip("0123456789")):] or 0)))
    with open(path, "w", newline="") as f:
        out = csv.writer(f)
        out.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for ref, x, y, turn in rows:
            out.writerow([ref, f"{x:.4f}mm", f"{y:.4f}mm", "Top", f"{turn:.0f}"])
    return len(rows)


# For assemblers other than JLCPCB: who makes each part, by maker's number. Blank where not checked; the LCSC
# number in the same row identifies the exact part.
MAKER = {
    "ESP32-S3-WROOM-1-N4": "Espressif", "DRV8876PWPR": "Texas Instruments", "K7805-1000R3": "YLPTEC",
    "AP2112K-3.3TRG1": "Diodes Incorporated", "AO3401A": "Alpha & Omega Semiconductor",
    "AO3400A": "Alpha & Omega Semiconductor", "H5VL10B": "R+O", "KT-0603R": "Hubei KENTO",
    "EMK1EM221FB0D00R": "AISHI", "DC-005-5A-2.0": "XKB Connection", "XT30UPB-F30.G.Y": "Changzhou Amass",
    "B2B-XH-A": "JST", "B4B-XH-A": "JST", "TYPE-C-31-M-12": "Korean Hroparts Elec",
    "TS-1187A-B-A-B": "XKB Connection", "MSK12C02": "SHOU HAN",
}
THT = ("BarrelJack", "AMASS_XT30", "JST_XH", "PinHeader", "Converter_DCDC")


def maker(mpn):
    if mpn in MAKER:
        return MAKER[mpn]
    if mpn.startswith("0603WAF"):
        return "UNI-ROYAL"
    if mpn.startswith("CL"):
        return "Samsung Electro-Mechanics"
    if mpn.startswith("CC0603"):
        return "YAGEO"
    return ""


def generic(out_dir):
    """Files for an assembler that is not JLCPCB (PCBWay and the like): a BOM by maker's part number, a
    placement file in KiCad's own rotations and pad centres (their engineers place by the drawing, not by
    JLCPCB's library), and a top assembly drawing showing pin 1 and polarity."""
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(HERE / "export" / "parts.csv") as f:
        lines = [r for r in csv.DictReader(f)]
    with open(out_dir / "cane-board-bom.csv", "w", newline="") as f:
        out = csv.writer(f)
        out.writerow(["Item", "Designator", "Qty", "Manufacturer", "Manufacturer Part Number", "Description",
                      "Package", "Type", "LCSC Part #", "Notes"])
        n = 0
        for r in lines:
            if r["Fitted"] != "yes":  # the phone socket and its parts: pads only, nothing to buy or place
                continue
            n += 1
            kind = "THT" if any(k in r["Footprint"] for k in THT) else "SMD"
            out.writerow([n, ",".join(r["References"].split()), r["Qty"], maker(r["Part number"]), r["Part number"],
                          r["Value"], r["Footprint"], kind, r["LCSC"], ""])
    board = pcbnew.LoadBoard(str(BOARD))
    rows = []
    for fp in board.GetFootprints():
        if fp.IsDNP() or fp.IsExcludedFromPosFiles() or fp.IsBoardOnly():
            continue
        c = pad_centre(fp)
        rows.append((fp.GetReference(), fp.GetFPIDAsString().split(":")[1], pcbnew.ToMM(c.x), -pcbnew.ToMM(c.y),
                     fp.GetOrientationDegrees() % 360, fp.GetValue()))
    rows.sort(key=lambda r: (r[0].rstrip("0123456789"), int(r[0][len(r[0].rstrip("0123456789")):] or 0)))
    with open(out_dir / "cane-board-cpl.csv", "w", newline="") as f:
        out = csv.writer(f)
        out.writerow(["Designator", "Footprint", "Mid X", "Mid Y", "Layer", "Rotation", "Comment"])
        for ref, name, x, y, turn, value in rows:
            out.writerow([ref, name, f"{x:.4f}mm", f"{y:.4f}mm", "T", f"{turn:.0f}", value])
    run("pcb", "export", "pdf", "--layers", "F.Fab,F.SilkS,Edge.Cuts", "--mode-single", "--black-and-white",
        "-o", str(out_dir / "cane-board-assembly-top.pdf"), str(BOARD))
    shutil.copy(OUT / "cane-board-gerbers.zip", out_dir / "cane-board-gerbers.zip")
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
    other = HERE / "export" / "fab-other"
    shutil.rmtree(other, ignore_errors=True)
    print("for other assemblers, in export/fab-other/:", generic(other), "parts placed")


if __name__ == "__main__":
    main()

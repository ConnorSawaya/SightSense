"""Writes the files JLCPCB needs to make and assemble the cane board, into export/fab/.

    python3 make_fab.py

Gerbers and drill file (zipped for upload), the placement file in JLCPCB's column
names, and a copy of the bill of materials. Needs kicad-cli (KiCad 10).
"""

import csv
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOARD = HERE / "cane-board.kicad_pcb"
OUT = HERE / "export" / "fab"
CLI = os.environ.get("KICAD_CLI", "kicad-cli")
LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"


def run(*args):
    done = subprocess.run([CLI, *args], capture_output=True, text=True)
    if done.returncode:
        sys.exit(f"kicad-cli {' '.join(args)} failed:\n{done.stdout}{done.stderr}")


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

    raw = OUT / "positions-kicad.csv"
    run("pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "front", "--exclude-dnp", "-o", str(raw), str(BOARD))
    with open(raw) as f, open(OUT / "cane-board-cpl.csv", "w", newline="") as g:  # JLCPCB's placement columns
        out = csv.writer(g)
        out.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for row in csv.DictReader(f):
            out.writerow([row["Ref"], row["PosX"] + "mm", row["PosY"] + "mm", "Top" if row["Side"] == "top" else "Bottom", row["Rot"]])
    raw.unlink()
    shutil.copy(HERE / "export" / "bom-jlcpcb.csv", OUT / "cane-board-bom.csv")
    print("wrote", ", ".join(sorted(p.name for p in OUT.iterdir())))
    print("gerber files:", len(list(gerbers.iterdir())))


if __name__ == "__main__":
    main()

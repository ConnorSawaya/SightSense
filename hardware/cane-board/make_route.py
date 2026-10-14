"""Routes the cane board with the Freerouting autorouter, then pours ground and checks it.

Run make_pcb.py first; this takes its placed board, sets track widths, hands the
board to Freerouting, reads the tracks back, pours ground on both sides and runs
KiCad's design rules check. Run it with the Python inside KiCad:

    .../KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 make_route.py

Needs Java and the Freerouting jar. Set FREEROUTING_JAR and JAVA if they are not
where this script looks.
"""

import json
import re
import os
import subprocess
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
BOARD = HERE / "cane-board.kicad_pcb"
JAVA = os.environ.get("JAVA", "/opt/homebrew/opt/openjdk/bin/java")
JAR = os.environ.get("FREEROUTING_JAR", "")
CLI = os.environ.get("KICAD_CLI", "kicad-cli")

# Nets that carry motor or battery current get wide tracks.
POWER = ["VIN_RAW", "VIN_F", "+BATT", "MOT_A", "MOT_B", "BUCK_SW", "+5V", "VSYS", "VBUS", "GND"]


def mm(v):
    return pcbnew.FromMM(v)


def classes(board):
    ns = board.GetDesignSettings().m_NetSettings
    default = ns.GetDefaultNetclass()
    default.SetTrackWidth(mm(0.2))
    default.SetClearance(mm(0.15))
    default.SetViaDiameter(mm(0.6))
    default.SetViaDrill(mm(0.3))
    power = pcbnew.NETCLASS("Power")
    power.SetTrackWidth(mm(0.3))
    power.SetClearance(mm(0.2))
    power.SetViaDiameter(mm(0.8))
    power.SetViaDrill(mm(0.4))
    ns.SetNetclass("Power", power)
    for net in POWER:
        ns.SetNetclassPatternAssignment(net if net in ("GND", "+BATT", "+5V", "VBUS") else "/" + net, "Power")
    ns.RecomputeEffectiveNetclasses()
    bds = board.GetDesignSettings()
    bds.m_MinThroughDrill = mm(0.3)
    bds.m_TrackMinWidth = mm(0.15)


def widen_small_holes(board):
    """KiCad's ESP32 footprint has 0.2 mm ground holes; JLCPCB's standard minimum is 0.3 mm."""
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            drill = pad.GetDrillSize()
            if 0 < drill.x < mm(0.3):
                pad.SetDrillSize(pcbnew.VECTOR2I(mm(0.3), mm(0.3)))
                size = pad.GetSize(pcbnew.F_Cu)
                if size.x < mm(0.6):
                    pad.SetSize(pcbnew.F_Cu, pcbnew.VECTOR2I(mm(0.6), mm(0.6)))


def edge_keepout(board, width=0.5):
    """A strip along the board edge where the router may not put copper (JLCPCB wants 0.3 mm or more)."""
    box = board.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = box.GetLeft(), box.GetTop(), box.GetRight(), box.GetBottom()
    w = mm(width)
    strips = [(x0, y0, x1, y0 + w), (x0, y1 - w, x1, y1), (x0, y0, x0 + w, y1), (x1 - w, y0, x1, y1)]
    out = []
    for a, b, c, d in strips:
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowZoneFills(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetLayerSet(pcbnew.LSET.AllCuMask())
        o = z.Outline()
        o.NewOutline()
        for x, y in ((a, b), (c, b), (c, d), (a, d)):
            o.Append(x, y)
        board.Add(z)
        out.append(z)
    return out


def widen_thin_tracks(board, least=0.15):
    """Freerouting narrows a few tracks where they meet fine-pitch pads; bring them up to the minimum."""
    for t in board.GetTracks():
        if t.GetClass() == "PCB_TRACK" and t.GetWidth() < mm(least):
            t.SetWidth(mm(least))


STACKUP = """(stackup
			(layer "F.SilkS" (type "Top Silk Screen") (color "White"))
			(layer "F.Paste" (type "Top Solder Paste"))
			(layer "F.Mask" (type "Top Solder Mask") (color "Black") (thickness 0.01))
			(layer "F.Cu" (type "copper") (thickness 0.035))
			(layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
			(layer "B.Cu" (type "copper") (thickness 0.035))
			(layer "B.Mask" (type "Bottom Solder Mask") (color "Black") (thickness 0.01))
			(layer "B.Paste" (type "Bottom Solder Paste"))
			(layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
			(copper_finish "HAL SnPb")
			(dielectric_constraints no)
		)"""


def black_board():
    """Black solder mask, white print, 1.6 mm FR-4, leaded HASL: what the order will ask for."""
    text = BOARD.read_text()
    if "(stackup" not in text:
        text = text.replace("(setup", "(setup\n\t\t" + STACKUP, 1)
        BOARD.write_text(text)


def render():
    out = HERE / "previews"
    shots = {"board-top.png": ["--side", "top", "--width", "1100", "--height", "2400", "--zoom", "0.95"],
             "board-bottom.png": ["--side", "bottom", "--width", "1100", "--height", "2400", "--zoom", "0.95"],
             "board-3d.png": ["--side", "top", "--perspective", "--rotate", "-55,0,-35", "--width", "2000", "--height", "1500",
                              "--zoom", "1.25"]}
    for name, args in shots.items():
        subprocess.run([CLI, "pcb", "render", "--quality", "high", "--background", "opaque", "--use-board-stackup-colors",
                        *args, "-o", str(out / name), str(BOARD)], capture_output=True, text=True)


def inner_ground(board):
    """Ground poured on both inner layers round whatever tracks the router puts there."""
    gnd = board.FindNet("GND")
    box = board.GetBoardEdgesBoundingBox()
    out = []
    for layer in (pcbnew.In1_Cu, pcbnew.In2_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNetCode(gnd.GetNetCode())
        o = z.Outline()
        o.NewOutline()
        for x, y in ((box.GetLeft(), box.GetTop()), (box.GetRight(), box.GetTop()), (box.GetRight(), box.GetBottom()),
                     (box.GetLeft(), box.GetBottom())):
            o.Append(x, y)
        board.Add(z)
        out.append(z)
    return out


def drop_ground(dsn):
    """Ground is left to the copper pours on both sides; the router only wires everything else."""
    text = dsn.read_text()
    start = text.index("(net GND")
    depth, i = 0, start
    while True:
        depth += {"(": 1, ")": -1}.get(text[i], 0)
        i += 1
        if depth == 0:
            break
    text = text[:start] + text[i:]
    text = re.sub(r"(\(class [^()]*?)\sGND(?=[\s)])", r"\1", text)
    dsn.write_text(text)


def stitch(board, pitch=2.5, clearance=0.25):
    """Vias tying the top and bottom ground pours together, beside every ground pad and on a grid."""
    gnd = board.FindNet("GND")
    r = mm(0.3) + mm(clearance)
    box = board.GetBoardEdgesBoundingBox()
    blockers = [t for t in board.GetTracks()] + [p for fp in board.GetFootprints() for p in fp.Pads()]
    keep_out = [fp for fp in board.GetFootprints() if fp.GetReference() == "U1"]

    def free(pt):
        if not (box.GetLeft() + mm(1.2) < pt.x < box.GetRight() - mm(1.2) and box.GetTop() + mm(1.2) < pt.y < box.GetBottom() - mm(1.2)):
            return False
        for fp in keep_out:  # nothing near the aerial
            if pt.y < fp.GetPosition().y - mm(5.5):
                return False
        for item in blockers:
            if item.HitTest(pt, r):
                return False
        return True

    added = []
    def put(pt):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pt)
        v.SetWidth(mm(0.6))
        v.SetDrill(mm(0.3))
        v.SetNet(gnd)
        board.Add(v)
        blockers.append(v)
        added.append(v)

    # one via next to each surface-mount ground pad, so each reaches the bottom pour
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() != "GND" or pad.HasHole():
                continue
            c = pad.GetPosition()
            for dx, dy in ((0, -1.1), (0, 1.1), (-1.1, 0), (1.1, 0), (-1.1, -1.1), (1.1, 1.1), (1.1, -1.1), (-1.1, 1.1)):
                pt = pcbnew.VECTOR2I(c.x + mm(dx), c.y + mm(dy))
                if free(pt):
                    put(pt)
                    break
    y = box.GetTop() + mm(2)
    while y < box.GetBottom() - mm(1):
        x = box.GetLeft() + mm(2)
        while x < box.GetRight() - mm(1):
            pt = pcbnew.VECTOR2I(int(x), int(y))
            if free(pt):
                put(pt)
            x += mm(pitch)
        y += mm(pitch)
    return len(added)


def widen_where_room(board, net, widths=(0.5, 0.4, 0.3)):
    """VM is routed at the normal width so it can reach the driver's fine-pitch pin; then widened wherever it fits."""
    tracks = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == net]
    others = [t for t in board.GetTracks() if t.GetNetname() != net] + \
             [p for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetname() != net]
    widened = 0
    for t in tracks:
        base = t.GetWidth()
        for w in widths:
            t.SetWidth(mm(w))
            seg = t.GetEffectiveShape()
            clash = False
            for o in others:
                if not o.IsOnLayer(t.GetLayer()):
                    continue
                if seg.Collide(o.GetEffectiveShape(t.GetLayer()), mm(0.2)):
                    clash = True
                    break
            if not clash:
                widened += 1
                break
        else:
            t.SetWidth(base)
    print(f"{net}: {widened} of {len(tracks)} tracks widened")


def main():
    jar = JAR or next((str(p) for p in Path(os.environ.get("TMPDIR", "/tmp")).rglob("freerouting-*.jar")), "")
    if not jar or not Path(jar).exists():
        sys.exit("set FREEROUTING_JAR to the Freerouting jar")
    board = pcbnew.LoadBoard(str(BOARD))
    zones = list(board.Zones())
    for z in zones:
        board.Remove(z)
    for t in list(board.GetTracks()):
        board.Remove(t)
    board.SetCopperLayerCount(4)
    planes = inner_ground(board)
    classes(board)
    widen_small_holes(board)
    fence = edge_keepout(board)

    work = HERE / "export" / "route"
    work.mkdir(parents=True, exist_ok=True)
    dsn, ses = work / "cane-board.dsn", work / "cane-board.ses"
    if not pcbnew.ExportSpecctraDSN(board, str(dsn)):
        sys.exit("DSN export failed")
    best = None
    for attempt in range(int(os.environ.get("ROUTE_TRIES", "5"))):  # the router is not deterministic; keep the best run
        out = work / f"try{attempt}.ses"
        extra = [] if attempt == 0 else ["-is", "random", "-us", ["greedy", "global", "hybrid"][attempt % 3]]
        run = subprocess.run([JAVA, "-jar", jar, "-de", str(dsn), "-do", str(out), "-mp", "100", *extra, "--gui.enabled=false"],
                             capture_output=True, text=True, timeout=1800)
        found = re.findall(r"\((\d+) unrouted", run.stdout + run.stderr)
        left = int(found[-1]) if found else 999
        print(f"try {attempt}: {left} unrouted")
        if out.exists() and (best is None or left < best[0]):
            best = (left, out)
        if left == 0:
            break
    if not best:
        sys.exit("Freerouting wrote no session file")
    ses.write_bytes(best[1].read_bytes())
    if not pcbnew.ImportSpecctraSES(board, str(ses)):
        sys.exit("SES import failed")

    for z in fence:
        board.Remove(z)
    widen_thin_tracks(board)
    widen_where_room(board, "/VM")
    for z in zones:
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print(f"ground vias added: {stitch(board)}")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD), board)

    for fp in board.GetFootprints():  # the driver's footprint asks 0.2 mm; JLCPCB makes 0.127 mm, the routed board keeps 0.18
        if fp.GetReference() == "U2":
            fp.SetLocalClearance(mm(0.18))
    pcbnew.SaveBoard(str(BOARD), board)
    black_board()
    report = work / "drc.json"
    subprocess.run([CLI, "pcb", "drc", "--format", "json", "--severity-all", "--refill-zones", "--save-board",
                    "-o", str(report), str(BOARD)], capture_output=True, text=True)
    data = json.loads(report.read_text())
    kinds = {}
    for v in data.get("violations", []):
        kinds.setdefault((v["severity"], v["type"]), []).append("; ".join(i.get("description", "") for i in v.get("items", [])))
    print(f"tracks: {len(board.GetTracks())}, unconnected: {len(data.get('unconnected_items', []))}")
    for (sev, kind), found in sorted(kinds.items()):
        print(f"  {sev} {kind}: {len(found)}")
        if sev == "error":
            for line in found[:6]:
                print("     " + line)


if __name__ == "__main__":
    main()
    if "--no-render" not in sys.argv:
        render()

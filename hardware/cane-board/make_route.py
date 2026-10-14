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
POWER = ["VIN_RAW", "VIN_F", "+BATT", "MOT_A", "MOT_B", "+5V", "VSYS", "VBUS", "GND"]


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


def aerial_keepout(board):
    """The ESP32 footprint keeps copper from under its aerial on the outer layers only; do the same on the inner ones."""
    u1 = next(fp for fp in board.GetFootprints() if fp.GetReference() == "U1")
    box = board.GetBoardEdgesBoundingBox()
    top = u1.GetPosition().y - mm(12.75)  # module body is 25.5 mm long, aerial in its top 6 mm
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    z.SetLayerSet(pcbnew.LSET.AllCuMask())
    o = z.Outline()
    o.NewOutline()
    for x, y in ((box.GetLeft(), box.GetTop()), (box.GetRight(), box.GetTop()), (box.GetRight(), top + mm(6.5)),
                 (box.GetLeft(), top + mm(6.5))):
        o.Append(x, y)
    board.Add(z)


def outer_only(dsn):
    """Battery and motor current stays on the outer layers, which have twice the copper of the inner ones."""
    text = dsn.read_text()
    text = text.replace('(circuit\n        (use_via "Via[0-3]_800:400_um")\n      )',
                        '(circuit\n        (use_via "Via[0-3]_800:400_um")\n        (use_layer F.Cu B.Cu)\n      )', 1)
    text = re.sub(r"(\(class kicad_default[^()]*?)\s/VM(?=[\s)])", r"\1", text)
    supply = ('    (class Supply /VM\n      (circuit\n        (use_via "Via[0-3]_800:400_um")\n        (use_layer F.Cu B.Cu)\n'
              '      )\n      (rule\n        (width 200)\n        (clearance 150)\n      )\n    )\n')
    text = text.replace("    (class Power", supply + "    (class Power", 1)
    dsn.write_text(text)


SUPPLY = ["+BATT", "/VIN_RAW", "/VIN_F", "/VM", "/MOT_A", "/MOT_B", "+5V"]


def blocks(text, head):
    """Start and end of every balanced (head ...) block in a Specctra file."""
    out, i = [], 0
    while True:
        i = text.find("(" + head + " ", i)
        if i < 0:
            return out
        depth, j = 0, i
        while True:
            depth += {"(": 1, ")": -1}.get(text[j], 0)
            j += 1
            if depth == 0:
                break
        out.append((i, j))
        i = j


def supply_only(dsn):
    """First pass: only the battery, motor and converter nets, 0.4 mm wide, on the outer layers."""
    text = dsn.read_text()
    for a, b in reversed(blocks(text, "net")):
        name = text[a + 5:text.index("\n", a)].strip().strip('"')
        if name not in SUPPLY:
            text = text[:a] + text[b:]
    cls = blocks(text, "class")
    first = cls[0][0]
    for a, b in reversed(cls):
        text = text[:a] + text[b:]
    mine = ("(class Supply " + " ".join(SUPPLY) + '\n      (circuit\n        (use_via "Via[0-3]_800:400_um")\n'
            "        (use_layer F.Cu B.Cu)\n      )\n      (rule\n        (width 400)\n        (clearance 200)\n      )\n    )")
    text = text[:first] + mine + text[first:]
    dsn.write_text(text)


def freeroute(jar, dsn, work, tag, tries):
    best = None
    for attempt in range(tries):  # the router is not deterministic between strategies; keep the best run
        out = work / f"{tag}-try{attempt}.ses"
        extra = [] if attempt == 0 else ["-is", "random", "-us", ["greedy", "global", "hybrid"][attempt % 3]]
        run = subprocess.run([JAVA, "-jar", jar, "-de", str(dsn), "-do", str(out), "-mp", "100", *extra, "--gui.enabled=false"],
                             capture_output=True, text=True, timeout=1800)
        found = re.findall(r"\((\d+) unrouted", run.stdout + run.stderr)
        left = int(found[-1]) if found else 999
        print(f"{tag} try {attempt}: {left} unrouted")
        if out.exists() and (best is None or left < best[0]):
            best = (left, out)
        if left == 0:
            break
    if not best:
        sys.exit("Freerouting wrote no session file")
    return best[1]


# Motor and battery current, drawn by hand before the autorouter runs: (net, layer, width, points).
# The autorouter left these 0.15 to 0.3 mm wide in places; these runs are 0.6 to 1.0 mm, except at the driver's pins.
HAND = [
    # Reverse-plug FETs: fuse up between Q1 and Q4 to both drains.
    ("/VIN_F", "F.Cu", 0.8, [(18.57, 80.5), (19.5, 79.6), (19.5, 74.3)]),
    ("/VIN_F", "F.Cu", 0.6, [(17.61, 74.3), (23.36, 74.3)]),
    # Both sources to the kill-switch FET, on the bottom (the drains' track is in the way on top).
    ("+BATT", "F.Cu", 0.8, [(15.73, 75.25), (15.73, 76.6)]),
    ("+BATT", "F.Cu", 0.8, [(21.48, 75.25), (21.48, 76.6)]),
    ("+BATT", "B.Cu", 1.0, [(15.73, 76.6), (21.48, 76.6), (22.4, 76.6), (25.3, 70.0), (25.3, 67.9)]),
    ("+BATT", "F.Cu", 0.8, [(25.3, 67.9), (26.66, 66.95)]),
    # Kill-switch FET to the 22 uF capacitor, then to C4 and the driver's VM pin, approached from the left.
    ("/VM", "F.Cu", 0.8, [(28.54, 66.0), (28.54, 68.0), (27.84, 70.0), (27.84, 72.6)]),
    ("/VM", "F.Cu", 0.6, [(27.84, 72.6), (24.7, 75.7), (24.7, 77.2)]),
    ("/VM", "F.Cu", 0.6, [(24.7, 77.2), (25.2, 77.47), (26.9, 77.47)]),
    ("/VM", "F.Cu", 0.4, [(26.9, 77.47), (28.27, 77.47)]),
    ("/VM", "F.Cu", 0.4, [(24.7, 77.2), (24.7, 79.0)]),
    # Motor outputs: a short hop off the pin to a via, then straight down the bottom to the XT30.
    ("/MOT_B", "F.Cu", 0.4, [(28.27, 76.83), (27.4, 76.83), (26.2, 76.2)]),
    ("/MOT_B", "B.Cu", 1.0, [(26.2, 76.2), (26.2, 92.2), (28.55, 94.5)]),
    ("/MOT_A", "F.Cu", 0.4, [(33.83, 76.17), (34.9, 76.17), (35.5, 76.0)]),
    ("/MOT_A", "B.Cu", 1.0, [(35.5, 76.0), (35.5, 92.5), (33.55, 94.5)]),
]
HAND_VIAS = [("+BATT", (15.73, 76.6)), ("+BATT", (21.48, 76.6)), ("+BATT", (25.3, 67.9)),
             ("/MOT_B", (26.2, 76.2)), ("/MOT_A", (35.5, 76.0))]


def hand_route(board):
    """Lay the HAND tracks and vias, locked so the autorouter treats them as fixed."""
    layer = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
    for net, side, width, points in HAND:
        for a, z in zip(points, points[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
            t.SetEnd(pcbnew.VECTOR2I(mm(z[0]), mm(z[1])))
            t.SetWidth(mm(width))
            t.SetLayer(layer[side])
            t.SetNet(board.FindNet(net))
            t.SetLocked(True)
            board.Add(t)
    for net, at in HAND_VIAS:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(mm(at[0]), mm(at[1])))
        v.SetWidth(mm(0.8))
        v.SetDrill(mm(0.4))
        v.SetNet(board.FindNet(net))
        v.SetLocked(True)
        board.Add(v)


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
    hand_route(board)
    fence = edge_keepout(board)

    work = HERE / "export" / "route"
    work.mkdir(parents=True, exist_ok=True)
    dsn, ses = work / "cane-board.dsn", work / "cane-board.ses"
    tries = int(os.environ.get("ROUTE_TRIES", "2"))
    if not pcbnew.ExportSpecctraDSN(board, str(dsn)):
        sys.exit("DSN export failed")
    outer_only(dsn)  # battery, motor and converter tracks only on the outer layers
    ses.write_bytes(freeroute(jar, dsn, work, "all", tries).read_bytes())
    if not pcbnew.ImportSpecctraSES(board, str(ses)):
        sys.exit("SES import failed")

    for z in fence:
        board.Remove(z)
    widen_thin_tracks(board)
    for net in SUPPLY + ["VBUS", "/VSYS"]:
        widen_where_room(board, net, widths=(1.0, 0.8, 0.6, 0.5, 0.4))
    aerial_keepout(board)
    for z in zones:
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print(f"ground vias added: {stitch(board)}")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD), board)

    for fp in board.GetFootprints():  # the driver's footprint asks 0.2 mm; JLCPCB makes 0.127 mm, the routed board keeps 0.15
        if fp.GetReference() == "U2":
            fp.SetLocalClearance(mm(0.15))
    pcbnew.SaveBoard(str(BOARD), board)
    black_board()
    data = drc(work)
    if tie_ground(data):
        data = drc(work)
    report_drc(board, data)


def drc(work):
    report = work / "drc.json"
    subprocess.run([CLI, "pcb", "drc", "--format", "json", "--severity-all", "--refill-zones", "--save-board",
                    "-o", str(report), str(BOARD)], capture_output=True, text=True)
    return json.loads(report.read_text())


def tie_pad(board, pad, width=mm(0.3), gap=mm(0.2)):
    """A straight track from a ground pad to the nearest ground via it can reach without passing other copper."""
    at = pad.GetPosition()
    layer = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
    others = [t for t in board.GetTracks() if t.GetNetname() != "GND" and t.IsOnLayer(layer)]
    others += [p for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetname() != "GND" and p.IsOnLayer(layer)]
    vias = sorted((v for v in board.GetTracks() if v.Type() == pcbnew.PCB_VIA_T and v.GetNetname() == "GND"),
                  key=lambda v: (v.GetPosition() - at).EuclideanNorm())
    for v in vias:
        end = v.GetPosition()
        if (end - at).EuclideanNorm() > mm(3):
            return False
        steps = 40
        points = [at + pcbnew.VECTOR2I(int((end.x - at.x) * k / steps), int((end.y - at.y) * k / steps)) for k in range(steps + 1)]
        if any(o.HitTest(pt, width // 2 + gap) for pt in points for o in others):
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(at)
        t.SetEnd(end)
        t.SetWidth(width)
        t.SetLayer(layer)
        t.SetNet(board.FindNet("GND"))
        board.Add(t)
        return True
    return False


def tie_ground(data):
    """Ground pads the pour could not join to the rest: by name from the DRC report, or inside a stranded piece of pour."""
    board = pcbnew.LoadBoard(str(BOARD))
    pads = [p for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetname() == "GND"]
    stranded = []
    for item in data.get("unconnected_items", []):
        for part in item.get("items", []):
            if "[GND]" in part.get("description", "") and "Pad" in part["description"]:
                at = pcbnew.VECTOR2I(mm(part["pos"]["x"]), mm(part["pos"]["y"]))
                stranded += [p for p in pads if (p.GetPosition() - at).EuclideanNorm() < mm(0.05)]
    anchors = [t.GetPosition() for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND"]
    anchors += [p.GetPosition() for p in pads if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    vias = set((a.x, a.y) for a in anchors)
    for t in board.GetTracks():  # a pad already tied counts as reached
        if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() == "GND":
            if (t.GetEnd().x, t.GetEnd().y) in vias:
                anchors.append(pcbnew.VECTOR2I(t.GetStart().x, t.GetStart().y))
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != "GND":
            continue
        for layer in z.GetLayerSet().Seq():
            if layer not in (pcbnew.F_Cu, pcbnew.B_Cu):
                continue
            poly = z.GetFilledPolysList(layer)
            for i in range(poly.OutlineCount()):
                outline = poly.Outline(i)
                if not any(outline.PointInside(a) for a in anchors):
                    stranded += [p for p in pads if p.IsOnLayer(layer) and outline.PointInside(p.GetPosition())][:1]
    tied = sum(tie_pad(board, p) for p in stranded)
    if tied:
        pcbnew.SaveBoard(str(BOARD), board)
        print(f"ground pads tied to a via: {tied} of {len(stranded)}")
    return tied


def report_drc(board, data):
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

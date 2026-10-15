"""Draws the schematic of the cane board and checks it.

Every part, its value, its footprint and the net on each of its pins is listed
in this file, block by block. Running it:

1. writes cane-board.kicad_sym (the one symbol KiCad does not ship),
   cane-board.kicad_sch and, if missing, the project files;
2. asks KiCad for the netlist and compares it pin by pin with the nets listed
   here, so a part drawn in the wrong place cannot go unnoticed;
3. checks that every pin has a pad of the same name on its footprint;
4. runs KiCad's electrical rules check;
5. exports the PDF, the parts lists and the tables in BOM.md.

    python3 make_board.py

Needs KiCad 10 (its symbol and footprint libraries and kicad-cli). Set
KICAD_SHARE if KiCad is not in /Applications. Nothing else: standard library only.

Edits made to the schematic in KiCad are lost when this is run again. Change
the list here, or stop using the script once the drawing is done by hand.
"""

import csv
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = "cane-board"
KICAD = Path(os.environ.get("KICAD_SHARE", "/Applications/KiCad/KiCad.app/Contents/SharedSupport"))
CLI = os.environ.get("KICAD_CLI", "kicad-cli")
U = 2.54  # one grid step; every position below is in these
NS = uuid.UUID("5b1f6e0c-7c50-4f5e-9b53-51c97a1d0001")
ROOT = str(uuid.uuid5(NS, "root"))

# Nets drawn with a power symbol, and which way that symbol points when unrotated.
POWER = {"GND": "down", "+BATT": "up", "+5V": "up", "+3V3": "up", "VBUS": "up"}

R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
SOD123 = "Diode_SMD:D_SOD-123"
SOT23 = "Package_TO_SOT_SMD:SOT-23"
SO8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
LED0603 = "LED_SMD:LED_0603_1608Metric"
XH2 = "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"
XH4 = "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical"
# TI's land pattern for the DRV8876 (PWP0016A): 3.4 x 5 mm copper under the chip, 3 x 3 mm opening, vias.
DRV_FP = "Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask3x3mm_ThermalVias"
# What to buy for each value and footprint: LCSC order code, maker's part number, JLCPCB's price in US
# dollars for one piece, and JLCPCB's class. Basic and Preferred parts carry no fee; each Extended
# surface-mount line carries one. Read from JLCPCB's parts library on October 13, 2026.
# Keyed by value and footprint, or by the maker's number for connectors, switches, the inductor and the fuse.
BUY = {
    "DC-005-5A-2.0": {"lcsc": "C381116", "price": 0.262, "jlc": "Extended"},
    "XT30UPB-F30.G.Y": {"lcsc": "C108769", "price": 0.2333, "jlc": "Extended"},
    "K7805-1000R3": {"lcsc": "C2992391", "price": 2.3475, "jlc": "Extended"},
    "B2B-XH-A": {"lcsc": "C158012", "price": 0.0407, "jlc": "Extended"},
    "B4B-XH-A": {"lcsc": "C144395", "price": 0.0594, "jlc": "Extended"},
    "PZ254V-11-04P": {"lcsc": "C2691448", "price": 0.0275, "jlc": "Extended"},
    "PZ254V-11-03P": {"lcsc": "C2937625", "price": 0.0198, "jlc": "Extended"},
    "TYPE-C-31-M-12": {"lcsc": "C165948", "price": 0.1863, "jlc": "Extended"},
    "TS-1187A-B-A-B": {"lcsc": "C318884", "price": 0.0206, "jlc": "Basic"},
    "MSK12C02": {"lcsc": "C431540", "price": 0.0568, "jlc": "Extended"},
    "FNR6045S100MT": {"lcsc": "C168076", "price": 0.0731, "jlc": "Extended"},
    "BSMD2920-400-30V": {"lcsc": "C20539726", "price": 0.2261, "jlc": "Extended"},
    "USB4125-GF-A": {"lcsc": "C3151650", "price": 1.039, "jlc": "Extended"},
    ("ESP32-S3-WROOM-1-N4", "ESP32-S3-WROOM-1"): {"lcsc": "C2913197", "mpn": "ESP32-S3-WROOM-1-N4", "price": 4.1297, "jlc": "Extended"},
    ("DRV8876PWPR", DRV_FP.split(":")[1]): {"lcsc": "C575551", "mpn": "DRV8876PWPR", "price": 0.7797, "jlc": "Extended"},
    ("TPS54302DDCR", "SOT-23-6"): {"lcsc": "C311983", "mpn": "TPS54302DDCR", "price": 0.3011, "jlc": "Extended"},
    ("AP2112K-3.3", "SOT-23-5"): {"lcsc": "C51118", "mpn": "AP2112K-3.3TRG1", "price": 0.1716, "jlc": "Extended"},
    ("TPS2069CDBVR", "SOT-23-5"): {"lcsc": "C181752", "mpn": "TPS2069CDBVR", "price": 0.1369, "jlc": "Extended"},
    ("AO3401A", "SOT-23"): {"lcsc": "C15127", "mpn": "AO3401A", "price": 0.102, "jlc": "Basic"},
    ("AO3400A", "SOT-23"): {"lcsc": "C20917", "mpn": "AO3400A", "price": 0.0891, "jlc": "Basic"},
    ("SMBJ15A", "D_SMB"): {"lcsc": "C19077569", "mpn": "SMBJ15A", "price": 0.055, "jlc": "Preferred"},
    ("BAT54S", "SOT-23"): {"lcsc": "C7420333", "mpn": "BAT54S", "price": 0.0137, "jlc": "Preferred"},
    ("B5819W", "D_SOD-123"): {"lcsc": "C8598", "mpn": "B5819W SL", "price": 0.0283, "jlc": "Basic"},
    ("H5VL10B", "D_SOD-882"): {"lcsc": "C7420372", "mpn": "H5VL10B", "price": 0.0064, "jlc": "Preferred"},
    ("Red", "LED_0603_1608Metric"): {"lcsc": "C2286", "mpn": "KT-0603R", "price": 0.0076, "jlc": "Basic"},
    ("100pF", "C_0603_1608Metric"): {"lcsc": "C14858", "mpn": "CL10C101JB8NNNC", "price": 0.0086, "jlc": "Basic"},
    ("22nF 50V", "C_0603_1608Metric"): {"lcsc": "C21122", "mpn": "CL10B223KB8NNNC", "price": 0.0075, "jlc": "Basic"},
    ("100nF 50V", "C_0603_1608Metric"): {"lcsc": "C14663", "mpn": "CC0603KRX7R9BB104", "price": 0.014, "jlc": "Basic"},
    ("1uF 50V", "C_0603_1608Metric"): {"lcsc": "C15849", "mpn": "CL10A105KB8NNNC", "price": 0.0158, "jlc": "Basic"},
    ("22uF 6.3V", "C_0603_1608Metric"): {"lcsc": "C59461", "mpn": "CL10A226MQ8NRNC", "price": 0.0312, "jlc": "Basic"},
    ("10uF 25V", "C_0805_2012Metric"): {"lcsc": "C15850", "mpn": "CL21A106KAYNNNE", "price": 0.0689, "jlc": "Basic"},
    ("10uF 50V", "C_1206_3216Metric"): {"lcsc": "C13585", "mpn": "CL31A106KBHNNNE", "price": 0.1586, "jlc": "Basic"},
    ("22uF 25V", "C_1206_3216Metric"): {"lcsc": "C12891", "mpn": "CL31A226KAHNNNE", "price": 0.1284, "jlc": "Basic"},
    ("220uF 25V", "CP_Elec_8x10"): {"lcsc": "C724620", "mpn": "EMK1EM221FB0D00R", "price": 0.1139, "jlc": "Extended"},
    ("100", "R_0603_1608Metric"): {"lcsc": "C22775", "mpn": "0603WAF1000T5E", "price": 0.0031, "jlc": "Basic"},
    ("220", "R_0603_1608Metric"): {"lcsc": "C22962", "mpn": "0603WAF2200T5E", "price": 0.0035, "jlc": "Basic"},
    ("1k", "R_0603_1608Metric"): {"lcsc": "C21190", "mpn": "0603WAF1001T5E", "price": 0.0019, "jlc": "Basic"},
    ("2.2k", "R_0603_1608Metric"): {"lcsc": "C4190", "mpn": "0603WAF2201T5E", "price": 0.0018, "jlc": "Basic"},
    ("4.7k", "R_0603_1608Metric"): {"lcsc": "C23162", "mpn": "0603WAF4701T5E", "price": 0.0028, "jlc": "Basic"},
    ("5.1k", "R_0603_1608Metric"): {"lcsc": "C23186", "mpn": "0603WAF5101T5E", "price": 0.0015, "jlc": "Basic"},
    ("10k", "R_0603_1608Metric"): {"lcsc": "C25804", "mpn": "0603WAF1002T5E", "price": 0.0052, "jlc": "Basic"},
    ("13k", "R_0603_1608Metric"): {"lcsc": "C22797", "mpn": "0603WAF1302T5E", "price": 0.0029, "jlc": "Basic"},
    ("22k", "R_0603_1608Metric"): {"lcsc": "C31850", "mpn": "0603WAF2202T5E", "price": 0.0041, "jlc": "Basic"},
    ("47k", "R_0603_1608Metric"): {"lcsc": "C25819", "mpn": "0603WAF4702T5E", "price": 0.0021, "jlc": "Basic"},
    ("100k", "R_0603_1608Metric"): {"lcsc": "C25803", "mpn": "0603WAF1003T5E", "price": 0.0031, "jlc": "Basic"},
    ("1M", "R_0603_1608Metric"): {"lcsc": "C22935", "mpn": "0603WAF1004T5E", "price": 0.0008, "jlc": "Basic"},  # LCSC price, October 14
    ("1.5k", "R_0603_1608Metric"): {"lcsc": "C22843", "mpn": "0603WAF1501T5E", "price": 0.002, "jlc": "Basic"},
}

# DRV8876 in the HTSSOP-16 (PWP) package: pin number, name, type, side, place on that side.
# From TI's datasheet SLVSDS7B, section 5, "Pin Functions".
DRV8876_PINS = [
    ("1", "EN/IN1", "input", "L", 4), ("2", "PH/IN2", "input", "L", 3), ("3", "nSLEEP", "input", "L", 2),
    ("16", "PMODE", "input", "L", 0), ("7", "IMODE", "input", "L", -1), ("5", "VREF", "input", "L", -3),
    ("8", "OUT1", "output", "R", 4), ("10", "OUT2", "output", "R", 3), ("12", "VCP", "passive", "R", 1),
    ("13", "CPH", "passive", "R", 0), ("14", "CPL", "passive", "R", -1), ("6", "IPROPI", "passive", "R", -3),
    ("4", "nFAULT", "open_collector", "R", -4), ("11", "VM", "power_in", "T", 0), ("15", "GND", "power_in", "B", 0),
    ("9", "PGND", "passive", "B", 0), ("17", "PAD", "passive", "B", 0),
]


# ---------------------------------------------------------------- KiCad's file format

TOKEN = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+')


def parse(text):
    stack = [[]]
    for m in TOKEN.finditer(text):
        t = m.group(0)
        if t == "(":
            stack.append([])
        elif t == ")":
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(t)
    return stack[0][0]


def dump(node, depth=0):
    if not isinstance(node, list):
        return node
    if all(not isinstance(c, list) for c in node):
        return "(" + " ".join(node) + ")"
    pad = "\n" + "\t" * (depth + 1)
    out = "(" + node[0]
    for c in node[1:]:
        out += pad + dump(c, depth + 1) if isinstance(c, list) else " " + c
    return out + "\n" + "\t" * depth + ")"


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def unq(s):
    return s[1:-1].replace('\\"', '"').replace("\\\\", "\\") if s.startswith('"') else s


def kids(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def num(v):
    v = round(v, 4)
    return str(int(v)) if v == int(v) else repr(v)


def uid(*key):
    return str(uuid.uuid5(NS, "/".join(str(k) for k in key)))


# ---------------------------------------------------------------- symbols from the libraries

_libs = {}


def library(name):
    if name not in _libs:
        path = HERE / f"{NAME}.kicad_sym" if name == NAME else KICAD / "symbols" / f"{name}.kicad_sym"
        _libs[name] = {unq(s[1]): s for s in kids(parse(path.read_text()), "symbol")}
    return _libs[name]


def flat_symbol(lib_id):
    """The symbol as a schematic stores it: a derived symbol takes its parent's drawing."""
    lib, name = lib_id.split(":")
    node = library(lib)[name]
    body = node
    while kids(body, "extends"):
        body = library(lib)[unq(kids(body, "extends")[0][1])]
    out = ["symbol", q(lib_id)]
    out += [c for c in body[2:] if isinstance(c, list) and c[0] not in ("property", "symbol", "extends", "embedded_fonts")]
    out += kids(node, "property")
    for unit in kids(body, "symbol"):
        out.append(["symbol", q(name + unq(unit[1])[len(unq(body[1])):])] + unit[2:])
    out.append(["embedded_fonts", "no"])
    return out


def pins_of(symbol):
    pins = []
    for unit in kids(symbol, "symbol"):
        for p in kids(unit, "pin"):
            at = kids(p, "at")[0]
            pins.append({
                "number": unq(kids(p, "number")[0][1]),
                "name": unq(kids(p, "name")[0][1]),
                "x": float(at[1]), "y": float(at[2]), "angle": int(float(at[3])),
                "hidden": bool(kids(p, "hide")) or "hide" in p,
            })
    return pins


def turn(rot, x, y):
    """A point in a symbol's own frame (y up), as an offset on the sheet (y down)."""
    return {0: (x, -y), 90: (-y, -x), 180: (-x, y), 270: (y, x)}[rot]


def write_drv8876():
    place = {"L": lambda i: (-12.7, i * U, 0), "R": lambda i: (12.7, i * U, 180),
             "T": lambda i: (i * U, 17.78, 270), "B": lambda i: (i * U, -17.78, 90)}
    font = "(effects (font (size 1.27 1.27)))"
    pins = ""
    for number, name, kind, side, i in DRV8876_PINS:
        x, y, a = place[side](i)
        hide = "(hide yes)" if name in ("PGND", "PAD") else ""
        pins += (f'(pin {kind} line (at {num(x)} {num(y)} {a}) (length 2.54) {hide}'
                 f'(name {q(name)} {font}) (number {q(number)} {font}))\n')

    def prop(key, value, x, y, hide=False, just=""):
        return (f'(property {q(key)} {q(value)} (at {x} {y} 0) (show_name no) (do_not_autoplace no) '
                f'{"(hide yes)" if hide else ""} (effects (font (size 1.27 1.27)) {just}))\n')

    text = (
        '(kicad_symbol_lib (version 20251024) (generator "make_board") (generator_version "10.0")\n'
        '(symbol "DRV8876PWP" (exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes) '
        '(duplicate_pin_numbers_are_jumpers no)\n'
        + prop("Reference", "U", -10.16, 16.51, just="(justify left)")
        + prop("Value", "DRV8876PWP", 2.54, 16.51, just="(justify left)")
        + prop("Footprint", DRV_FP, 0, 0, hide=True)
        + prop("Datasheet", "https://www.ti.com/lit/ds/symlink/drv8876.pdf", 0, 0, hide=True)
        + prop("Description", "H-bridge motor driver, 4.5 to 37 V, 3.5 A peak, current sense and regulation, HTSSOP-16", 0, 0, hide=True)
        + prop("ki_keywords", "motor driver H-bridge brushed DC current sense", 0, 0, hide=True)
        + prop("ki_fp_filters", "HTSSOP*4.4x5mm*P0.65mm*", 0, 0, hide=True)
        + '(symbol "DRV8876PWP_0_1" (rectangle (start -10.16 15.24) (end 10.16 -15.24) '
          '(stroke (width 0.254) (type default)) (fill (type background))))\n'
        + f'(symbol "DRV8876PWP_1_1"\n{pins})\n(embedded_fonts no)))\n'
    )
    (HERE / f"{NAME}.kicad_sym").write_text(dump(parse(text)) + "\n")


# ---------------------------------------------------------------- the drawing

items = []        # schematic items, as text
used = {}         # lib_id -> flattened symbol
expect = {}       # (ref, pin number) -> net
parts = []        # (ref, value, footprint, pin numbers)
org = [0.0, 0.0]  # origin of the block being drawn, in grid steps
counter = {"pwr": 0, "flag": 0}


def xy(gx, gy):
    return round((org[0] + gx) * U, 4), round((org[1] + gy) * U, 4)


def wire(a, b):
    items.append(f'(wire (pts (xy {num(a[0])} {num(a[1])}) (xy {num(b[0])} {num(b[1])})) '
                 f'(stroke (width 0) (type default)) (uuid {q(uid("w", a, b))}))')


def label(net, at, d):
    angle, just = (180, "right") if d[0] < 0 else (0, "left")
    items.append(f'(label {q(net)} (at {num(at[0])} {num(at[1])} {angle}) '
                 f'(effects (font (size 1.27 1.27)) (justify {just} bottom)) (uuid {q(uid("l", net, at))}))')


def note(text, gx, gy, size=1.27, bold=False):
    x, y = xy(gx, gy)
    items.append(f'(text {q(text)} (exclude_from_sim no) (at {num(x)} {num(y)} 0) '
                 f'(effects (font (size {size} {size}){" (bold yes)" if bold else ""}) (justify left bottom)) '
                 f'(uuid {q(uid("t", text, x, y))}))')


def block(title, gx, gy, w, h):
    org[0], org[1] = gx, gy
    x0, y0 = xy(0, 0)
    x1, y1 = xy(w, h)
    items.append(f'(rectangle (start {num(x0)} {num(y0)}) (end {num(x1)} {num(y1)}) '
                 f'(stroke (width 0) (type dash)) (fill (type none)) (uuid {q(uid("box", title))}))')
    note(title, 1, 2, size=2, bold=True)


def instance(ref, lib_id, value, fp, x, y, rot, fields, texts, dnp=False, bom=True):
    """One symbol on the sheet. texts: {"Reference": (x, y, angle, justify), "Value": ...}."""
    symbol = used.setdefault(lib_id, flat_symbol(lib_id))
    out = (f'(symbol (lib_id {q(lib_id)}) (at {num(x)} {num(y)} {rot}) (unit 1) (body_style 1) (exclude_from_sim no) '
           f'(in_bom {"yes" if bom and not ref.startswith("#") else "no"}) (on_board yes) (in_pos_files yes) '
           f'(dnp {"yes" if dnp else "no"}) (uuid {q(uid("s", ref))})\n')
    values = {"Reference": ref, "Value": value, "Footprint": fp}
    seen = set()
    for p in kids(symbol, "property"):
        key = unq(p[1])
        if key.startswith("ki_"):
            continue
        seen.add(key)
        at = kids(p, "at")[0]
        hidden = bool(kids(p, "hide")) or (ref.startswith("#") and key == "Reference")
        effects = dump(kids(p, "effects")[0])
        if key in texts:
            px, py, angle, just = texts[key]
            effects = f'(effects (font (size 1.27 1.27)){f" (justify {just})" if just else ""})'
        else:
            dx, dy = turn(rot, float(at[1]), float(at[2]))
            px, py, angle = x + dx, y + dy, int(float(at[3]))
        out += (f'(property {q(key)} {q(values.get(key, unq(p[2])))} (at {num(px)} {num(py)} {angle}) '
                f'{"(hide yes) " if hidden else ""}(show_name no) (do_not_autoplace no) {effects})\n')
    for key, text in fields.items():
        if text and key not in seen:
            out += (f'(property {q(key)} {q(text)} (at {num(x)} {num(y)} 0) (hide yes) (show_name no) '
                    f'(do_not_autoplace no) (effects (font (size 1.27 1.27))))\n')
    for p in pins_of(symbol):
        out += f'(pin {q(p["number"])} (uuid {q(uid("p", ref, p["number"]))}))\n'
    out += f'(instances (project {q(NAME)} (path {q("/" + ROOT)} (reference {q(ref)}) (unit 1)))))'
    items.append(out)
    return symbol


def power(net, at, d):
    natural = (0, 1) if POWER[net] == "up" else (0, -1)
    rot = next(r for r in (0, 90, 180, 270) if turn(r, *natural) == d)
    counter["pwr"] += 1
    reach = 3.81 if POWER[net] == "up" else 6.35
    if d[0]:
        text = (at[0] + d[0] * 6.985, at[1] - 1.016, 90, "")  # above its own wire, like a net name
    else:
        text = (at[0], at[1] + d[1] * reach, 0, "")
    instance(f'#PWR{counter["pwr"]:03d}', f"power:{net}", net, "", at[0], at[1], rot, {}, {"Value": text})


def connect(tip, d, net, stub):
    if net in POWER:
        end = (tip[0] + d[0] * stub, tip[1] + d[1] * stub)
        if stub:
            wire(tip, end)
        power(net, end, d)
        return
    if d[1] > 0:
        stub = max(stub, U)  # room for the name beside the wire, clear of the part
    end = (round(tip[0] + d[0] * stub, 4), round(tip[1] + d[1] * stub, 4))
    wire(tip, end)
    label(net, end, d)


def part(ref, lib_id, value, fp, at, nets, rot=0, nc=(), mpn="", stub=1.0, texts=None, dnp=False, bom=True):
    """Place a symbol and put a named stub, a power symbol or a no-connect mark on every pin."""
    x, y = xy(*at)
    buy = BUY.get((value, fp.split(":")[-1])) or BUY.get(mpn, {})
    mpn = mpn or buy.get("mpn", "")
    symbol = instance(ref, lib_id, value, fp, x, y, rot, {"MPN": mpn, "LCSC": buy.get("lcsc", "")}, texts or {}, dnp, bom)
    pins = pins_of(symbol)
    if not ref.startswith("#"):
        parts.append({"ref": ref, "value": value, "fp": fp, "pins": [p["number"] for p in pins], "mpn": mpn,
                      "fitted": not dnp, "bom": bom, "hole": fp.split(":")[0] in THROUGH_HOLE,
                      **{k: buy.get(k, "") for k in ("lcsc", "price", "jlc")}})
    left = dict(nets)
    spot = {}
    for p in pins:
        if p["hidden"]:
            continue
        dx, dy = turn(rot, p["x"], p["y"])
        tip = (round(x + dx, 4), round(y + dy, 4))
        a = p["angle"]
        out = turn(rot, *{0: (-1, 0), 90: (0, -1), 180: (1, 0), 270: (0, 1)}[a])
        key = p["name"] if p["name"] in nets else p["number"]
        if key in nets:
            left.pop(key, None)
            connect(tip, out, nets[key], stub * U)
            expect[(ref, p["number"])] = spot[tip] = nets[key]
        elif p["name"] in nc or p["number"] in nc:
            items.append(f'(no_connect (at {num(tip[0])} {num(tip[1])}) (uuid {q(uid("nc", ref, p["number"]))}))')
        else:
            sys.exit(f'{ref}: pin {p["number"]} ({p["name"]}) has no net and is not marked unconnected')
    for p in pins:  # hidden pins sit on a visible pin and share its net
        if p["hidden"]:
            dx, dy = turn(rot, p["x"], p["y"])
            tip = (round(x + dx, 4), round(y + dy, 4))
            if tip in spot:
                expect[(ref, p["number"])] = spot[tip]
    if left:
        sys.exit(f"{ref}: no pin called {sorted(left)}")


SIDE = {"Reference": (1.0, -0.5), "Value": (1.0, 0.5)}


def beside(at, rot, dx=1.0, just="left"):
    """Name and value to the side of a turned part, reading left to right."""
    x, y = xy(*at)
    angle = 90 if rot in (90, 270) else 0
    if rot in (90, 180):  # KiCad mirrors the justification of text on parts turned this way
        just = {"left": "right", "right": "left"}[just]
    return {k: (x + dx * U, y + oy * U, angle, just) for k, (_, oy) in SIDE.items()}


def two(ref, kind, value, at, top, bottom, fp=None, mpn="", dnp=False):
    """An upright two-pin part: top net, bottom net."""
    lib, default = {"R": ("Device:R", R0603), "C": ("Device:C", C0603), "CP": ("Device:C_Polarized", None),
                    "L": ("Device:L", None), "F": ("Device:Polyfuse", None)}[kind]
    texts = beside(at, 0, dx=0.7) if kind in "RLF" else None
    part(ref, lib, value, fp or default, at, {"1": top, "2": bottom}, mpn=mpn, stub=0.5, texts=texts, dnp=dnp)


def diode(ref, lib, value, fp, at, k, a, k_up=True, mpn=""):
    """An upright diode or LED. k_up puts the cathode at the top."""
    rot = 270 if k_up else 90
    part(ref, lib, value, fp, at, {"K": k, "A": a}, rot=rot, mpn=mpn, stub=0.5, texts=beside(at, rot))


def flag(net, at):
    """Tells the rules check that this net is a supply, where no regulator output says so."""
    counter["flag"] += 1
    x, y = xy(*at)
    ref = f'#FLG{counter["flag"]:02d}'
    if net in POWER and POWER[net] == "up":
        instance(ref, "power:PWR_FLAG", "PWR_FLAG", "", x, y, 180, {}, {"Value": (x, y + 5.08, 0, "")})
        power(net, (x, y), (0, -1))
    elif net in POWER:
        instance(ref, "power:PWR_FLAG", "PWR_FLAG", "", x, y, 0, {}, {})
        power(net, (x, y), (0, 1))
    else:
        instance(ref, "power:PWR_FLAG", "PWR_FLAG", "", x, y, 0, {}, {})
        connect((x, y), (0, 1), net, U)


# ---------------------------------------------------------------- the board, block by block


def draw():
    # Battery in: the pack's barrel plug, fuse, and a P-FET that blocks a reversed plug.
    block("Battery in: fuse and reverse-plug protection", 5, 8, 44, 33)
    part("J1", "Connector:Barrel_Jack_Switch", "12V battery", "Connector_BarrelJack:BarrelJack_Horizontal",
         (6, 10), {"1": "VIN_RAW", "2": "GND"}, nc=("3",), mpn="DC-005-5A-2.0")
    two("F1", "F", "PTC 4A", (14, 10), "VIN_RAW", "VIN_F", fp="Fuse:Fuse_2920_7451Metric", mpn="BSMD2920-400-30V")
    for ref, x in (("Q1", 25), ("Q4", 34)):  # two in parallel share the current and stay cool
        part(ref, "Transistor_FET:AO3401A", "AO3401A", SOT23, (x, 10), {"S": "+BATT", "D": "VIN_F", "G": "Q1_G"},
             rot=180, texts=beside((x, 10), 180, dx=-2.5, just="right"))
    two("R34", "R", "47k", (41, 10), "+BATT", "Q1_G")
    two("R1", "R", "100k", (41, 24), "Q1_G", "GND")
    diode("D1", "Device:D_Zener", "SMBJ15A", "Diode_SMD:D_SMB", (8, 24), "+BATT", "GND", mpn="SMBJ15A")
    two("C1", "CP", "220uF 25V", (16, 24), "+BATT", "GND", fp="Capacitor_SMD:CP_Elec_8x10")
    flag("+BATT", (26, 23))
    flag("GND", (33, 24))
    note("3S lithium-ion pack, 9.0 to 12.6 V, on its barrel plug (centre positive). Q1 and Q4 stay off\n"
         "if the plug is wired the other way round. R34 and R1 hold their gates at a third of the battery.", 1, 32)

    # Motor supply: a second P-FET that is on only while the kill-switch loop is closed.
    block("Motor supply and kill switch", 50, 8, 40, 33)
    part("Q2", "Transistor_FET:AO3401A", "AO3401A", SOT23, (8, 10), {"S": "+BATT", "D": "VM", "G": "KILL_G"},
         rot=180, texts=beside((8, 10), 180, dx=-2.5, just="right"))
    two("R2", "R", "10k", (17, 10), "+BATT", "KILL_G")
    two("C26", "C", "100nF 50V", (24, 10), "+BATT", "KILL_G")
    two("R3", "R", "13k", (33, 10), "KILL_G", "KILL_A")
    part("J3", "Connector_Generic:Conn_01x02", "Kill switch", XH2, (36, 23), {"1": "KILL_A", "2": "GND"}, mpn="B2B-XH-A")
    two("C3", "C", "22uF 25V", (4, 24), "VM", "GND", fp=C1206)
    two("C27", "C", "22uF 25V", (10, 24), "VM", "GND", fp=C1206)
    two("R4", "R", "4.7k", (16, 24), "VM", "LED1_A")
    diode("LED1", "Device:LED", "Red", LED0603, (22, 24), "GND", "LED1_A", k_up=False)
    flag("VM", (27, 23))
    note("Switch closed (or a jumper on J3): motor supply on, Q2's gate at 0.43 of the battery.\n"
         "Open, unplugged or a broken wire: off within about 2 ms. C26 keeps Q2 off at plug-in.", 1, 32)

    # Motor driver with a current limit set by R5, and a watchdog on its sleep pin.
    block("Motor driver, current limit and watchdog", 91, 8, 69, 33)
    part("U2", f"{NAME}:DRV8876PWP", "DRV8876PWPR", DRV_FP, (20, 15),
         {"EN/IN1": "MOT_EN", "PH/IN2": "MOT_PH", "nSLEEP": "DRV_SLP", "PMODE": "GND", "IMODE": "GND", "VREF": "+3V3",
          "OUT1": "MOT_A", "OUT2": "MOT_B", "VCP": "DRV_VCP", "CPH": "DRV_CPH", "CPL": "DRV_CPL", "IPROPI": "IPROPI",
          "nFAULT": "DRV_FLT", "VM": "VM", "GND": "GND"}, mpn="DRV8876PWPR")
    two("C4", "C", "100nF 50V", (35, 11), "VM", "GND")
    two("C5", "C", "100nF 50V", (41, 11), "DRV_VCP", "VM")
    two("C6", "C", "22nF 50V", (47, 11), "DRV_CPH", "DRV_CPL")
    part("J2", "Connector_Generic:Conn_01x02", "Motor", "Connector_AMASS:AMASS_XT30UPB-F_1x02_P5.0mm_Vertical",
         (64, 12), {"1": "MOT_A", "2": "MOT_B"}, mpn="XT30UPB-F30.G.Y")
    two("R5", "R", "1.5k", (35, 20), "IPROPI", "GND")
    two("R6", "R", "10k", (41, 20), "IPROPI", "I_ADC")
    two("C7", "C", "100nF 50V", (47, 20), "I_ADC", "GND")
    two("R7", "R", "10k", (53, 20), "+3V3", "DRV_FLT")
    two("R8", "R", "10k", (3, 28), "MOT_EN", "GND")
    two("R9", "R", "10k", (9, 28), "MOT_PH", "GND")
    two("R10", "R", "220", (16, 28), "HBEAT", "HB_R")
    two("C8", "C", "1uF 50V", (22, 28), "HB_R", "HB_AC")
    part("D4", "Diode:BAT54S", "BAT54S", SOT23, (33, 28), {"A": "GND", "K": "HB_DC", "COM": "HB_AC"}, mpn="BAT54S")
    two("C9", "C", "1uF 50V", (41, 28), "HB_DC", "GND")
    two("R11", "R", "100k", (46, 28), "HB_DC", "GND")
    part("JP1", "Jumper:SolderJumper_3_Bridged12", "Sleep source", "Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm",
         (58, 28), {"A": "HB_DC", "C": "DRV_SLP", "B": "HBEAT"}, bom=False)
    note("Current limit = 3.3 V / R5 / 1000 uA/A: 1.5k gives 2.2 A. All resistors 1%.", 33, 5.5)

    # 12 V to 5 V, built in.
    block("12 V to 5 V: ready-made module", 5, 42, 54, 32)
    part("U3", "Converter_DCDC:R-78E5.0-1.0", "K7805-1000R3", "Converter_DCDC:Converter_DCDC_RECOM_R-78E-0.5_THT", (22, 12),
         {"IN": "+BATT", "OUT": "+5V", "GND": "GND"}, mpn="K7805-1000R3")
    two("C10", "C", "10uF 50V", (5, 24), "+BATT", "GND", fp=C1206)
    two("C11", "C", "100nF 50V", (10, 24), "+BATT", "GND")
    two("C13", "C", "22uF 25V", (29, 24), "+5V", "GND", fp=C1206)
    two("C14", "C", "22uF 25V", (34, 24), "+5V", "GND", fp=C1206)
    note("A sealed switching module (YLPTEC K7805-1000R3: 8-36 V in, 5 V 1 A out, pins 1 in, 2 ground, 3 out).\n"
         "The converter's layout is inside it, so the board's layout cannot spoil it.", 1, 31)

    # 3.3 V for the processor, from the 5 V rail or from the programming socket.
    block("3.3 V", 60, 42, 34, 32)
    diode("D5", "Device:D_Schottky", "B5819W", SOD123, (5, 10), "VSYS", "+5V", k_up=False, mpn="B5819W")
    diode("D6", "Device:D_Schottky", "B5819W", SOD123, (12, 10), "VSYS", "VBUS", k_up=False, mpn="B5819W")
    part("U4", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5", (24, 10),
         {"VIN": "VSYS", "EN": "LDO_EN", "VOUT": "+3V3", "GND": "GND"}, mpn="AP2112K-3.3TRG1")
    two("R12", "R", "100k", (17, 18), "VSYS", "LDO_EN")
    part("SW3", "Switch:SW_SPDT", "Power", "Button_Switch_SMD:SW_SPDT_Shouhan_MSK12C02", (27, 18), {"B": "LDO_EN", "C": "GND"},
         nc=("A",), mpn="MSK12C02")
    two("C15", "C", "10uF 25V", (5, 24), "VSYS", "GND", fp=C0805)
    two("C16", "C", "10uF 25V", (11, 24), "+3V3", "GND", fp=C0805)
    two("R14", "R", "1k", (16, 24), "+3V3", "LED2_A")
    diode("LED2", "Device:LED", "Red", LED0603, (22, 24), "GND", "LED2_A", k_up=False)
    flag("VSYS", (30, 23))

    # 5 V out for the phone, switched and current limited.
    block("5 V out for the phone (not fitted)", 95, 42, 33, 32)
    part("J10", "Connector:USB_C_Receptacle_PowerOnly_6P", "Phone power", "Connector_USB:USB_C_Receptacle_GCT_USB4125-xx-x_6P_TopMnt_Horizontal",
         (6, 14), {"VBUS": "PH_VBUS", "CC1": "PH_CC1", "CC2": "PH_CC2", "GND": "GND", "SHIELD": "GND"}, mpn="USB4125-GF-A", dnp=True)
    part("U5", "Power_Management:TPS2069CDBV", "TPS2069CDBVR", "Package_TO_SOT_SMD:SOT-23-5", (24, 9),
         {"IN": "+5V", "EN": "PH_EN", "OUT": "PH_VBUS", "~{FLT}": "PH_FLT", "GND": "GND"}, mpn="TPS2069CDBVR", dnp=True)
    two("R17", "R", "22k", (22, 18), "+5V", "PH_CC1", dnp=True)
    two("R18", "R", "22k", (27, 18), "+5V", "PH_CC2", dnp=True)
    two("C17", "C", "10uF 50V", (13, 27), "+5V", "GND", fp=C1206, dnp=True)
    two("C18", "C", "22uF 25V", (18, 27), "PH_VBUS", "GND", fp=C1206, dnp=True)
    two("R15", "R", "10k", (23, 27), "+3V3", "PH_EN", dnp=True)
    two("R16", "R", "10k", (28, 27), "+3V3", "PH_FLT", dnp=True)

    # USB-C for loading firmware.
    block("USB-C for firmware", 129, 42, 31, 32)
    part("J11", "Connector:USB_C_Receptacle_USB2.0_16P", "Firmware", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
         (6, 16), {"VBUS": "VBUS", "CC1": "UP_CC1", "CC2": "UP_CC2", "D+": "USB_DP", "D-": "USB_DN", "GND": "GND", "SHIELD": "GND"},
         nc=("SBU1", "SBU2"), mpn="TYPE-C-31-M-12")
    for ref, net, x in (("D8", "USB_DN", 20), ("D9", "USB_DP", 27)):
        part(ref, "Device:D_TVS", "H5VL10B", "Diode_SMD:D_SOD-882", (x, 9), {"A1": net, "A2": "GND"}, rot=270, stub=0.5,
             texts=beside((x, 9), 270))
    two("R19", "R", "5.1k", (19, 25), "UP_CC1", "GND")
    two("R20", "R", "5.1k", (25, 25), "UP_CC2", "GND")
    flag("VBUS", (27, 18))

    # The processor.
    block("Processor: ESP32-S3", 5, 75, 84, 37)
    part("U1", "RF_Module:ESP32-S3-WROOM-1", "ESP32-S3-WROOM-1-N4", "RF_Module:ESP32-S3-WROOM-1", (24, 19),
         {"3V3": "+3V3", "GND": "GND", "EN": "ESP_EN", "IO0": "BOOT", "IO1": "I_ADC", "IO2": "VBAT_ADC", "IO4": "VM_ADC",
          "IO5": "MOT_EN", "IO6": "MOT_PH", "IO7": "HBEAT", "IO8": "SDA", "IO9": "SCL", "IO10": "HAPTIC", "IO11": "PH_EN",
          "IO12": "PH_FLT", "IO13": "ENC_A", "IO14": "ENC_B", "IO15": "DRV_FLT", "IO16": "TALK", "IO21": "LED_ST",
          "USB_D-": "USB_DN", "USB_D+": "USB_DP", "TXD0": "UART_TX", "RXD0": "UART_RX"},
         nc=("IO3", "IO17", "IO18", "IO35", "IO36", "IO37", "IO38", "IO39", "IO40", "IO41", "IO42", "IO45", "IO46", "IO47", "IO48"),
         mpn="ESP32-S3-WROOM-1-N4")
    two("C19", "C", "22uF 6.3V", (42, 11), "+3V3", "GND")
    two("C20", "C", "100nF 50V", (47, 11), "+3V3", "GND")
    two("R21", "R", "10k", (53, 11), "+3V3", "ESP_EN")
    two("C21", "C", "1uF 50V", (59, 11), "ESP_EN", "GND")
    part("SW1", "Switch:SW_Push", "Reset", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", (68, 11), {"1": "ESP_EN", "2": "GND"}, mpn="TS-1187A-B-A-B")
    two("R22", "R", "10k", (42, 20), "+3V3", "BOOT")
    part("SW2", "Switch:SW_Push", "Boot", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", (52, 20), {"1": "BOOT", "2": "GND"}, mpn="TS-1187A-B-A-B")
    two("R23", "R", "1k", (61, 20), "LED_ST", "LED3_A")
    diode("LED3", "Device:LED", "Red", LED0603, (67, 20), "GND", "LED3_A", k_up=False)
    part("J8", "Connector_Generic:Conn_01x03", "Serial", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
         (79, 20), {"1": "GND", "2": "UART_TX", "3": "UART_RX"}, mpn="PZ254V-11-03P")
    two("R24", "R", "1M", (42, 29), "+BATT", "VBAT_ADC")
    two("R25", "R", "100k", (47, 29), "VBAT_ADC", "GND")
    two("C22", "C", "100nF 50V", (53, 29), "VBAT_ADC", "GND")
    two("R26", "R", "1M", (60, 29), "VM", "VM_ADC")
    two("R27", "R", "100k", (65, 29), "VM_ADC", "GND")
    two("C23", "C", "100nF 50V", (71, 29), "VM_ADC", "GND")
    note("IO3, IO45, IO46 are boot-mode pins: left open. IO35 to IO37 are left open so a module with more memory also fits.\n"
         "Dividers 1M/100k: 2.2 V at the 24.4 V clamp, and only microamps into the processor when it is off.", 40, 36)

    # Everything that leaves the board for the handle or the motor end.
    block("Talk button, encoder, I2C, handle buzzer", 90, 75, 70, 22)
    part("J4", "Connector_Generic:Conn_01x02", "Talk button", XH2, (10, 8), {"1": "TALK_IN", "2": "GND"}, mpn="B2B-XH-A")
    two("R28", "R", "10k", (16, 8), "+3V3", "TALK_IN")
    two("R29", "R", "1k", (21, 8), "TALK_IN", "TALK")
    two("C24", "C", "100nF 50V", (26, 8), "TALK", "GND")
    part("J5", "Connector_Generic:Conn_01x04", "Encoder", XH4, (38, 8), {"1": "+3V3", "2": "GND", "3": "ENC_A", "4": "ENC_B"}, mpn="B4B-XH-A")
    part("J6", "Connector_Generic:Conn_01x04", "I2C", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
         (50, 8), {"1": "GND", "2": "+3V3", "3": "SDA", "4": "SCL"}, mpn="PZ254V-11-04P")
    two("R30", "R", "4.7k", (56, 8), "+3V3", "SDA")
    two("R31", "R", "4.7k", (61, 8), "+3V3", "SCL")
    part("J7", "Connector_Generic:Conn_01x02", "Buzzer motor", XH2, (10, 17), {"1": "+3V3", "2": "HAP_D"}, mpn="B2B-XH-A")
    part("Q3", "Transistor_FET:AO3400A", "AO3400A", SOT23, (21, 17), {"G": "HAP_G", "D": "HAP_D", "S": "GND"}, mpn="AO3400A")
    two("R32", "R", "100", (31, 17), "HAPTIC", "HAP_G")
    two("R33", "R", "100k", (36, 17), "HAP_G", "GND")
    diode("D7", "Device:D_Schottky", "B5819W", SOD123, (41, 17), "+3V3", "HAP_D", mpn="B5819W")
    for i in range(4):
        x, y = xy(50 + 5 * i, 17)
        instance(f"H{i + 1}", "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", x, y, 0, {}, {}, bom=False)


def schematic():
    libs = "\n".join(dump(used[k], 2) for k in sorted(used))
    return (f'(kicad_sch (version 20260306) (generator "eeschema") (generator_version "10.0") (uuid {q(ROOT)}) (paper "A3")\n'
            f'(title_block (title "SightSense cane board") (date "2026-10-13") (rev "0.1") '
            f'(comment 1 "Drawn by make_board.py. Not built or tested."))\n'
            f'(lib_symbols\n{libs}\n)\n' + "\n".join(items) +
            '\n(sheet_instances (path "/" (page "1")))\n(embedded_fonts no))\n')


# ---------------------------------------------------------------- checks


def run(*args):
    done = subprocess.run([CLI, *args], capture_output=True, text=True)
    if done.returncode:
        sys.exit(f"kicad-cli {' '.join(args)} failed:\n{done.stdout}{done.stderr}")
    return done.stdout


def check_netlist(sch, tmp):
    net_file = tmp / "check.net"
    run("sch", "export", "netlist", "--format", "kicadsexpr", "-o", str(net_file), str(sch))
    got = {}
    for net in kids(kids(parse(net_file.read_text()), "nets")[0], "net"):
        name = unq(kids(net, "name")[0][1]).lstrip("/")
        for node in kids(net, "node"):
            got[(unq(kids(node, "ref")[0][1]), unq(kids(node, "pin")[0][1]))] = name
    wrong = [f"{ref} pin {pin}: wanted {net}, drawn on {got.get((ref, pin), 'nothing')}"
             for (ref, pin), net in sorted(expect.items()) if got.get((ref, pin)) != net]
    stray = [f"{ref} pin {pin} is on {net} but should be unconnected"
             for (ref, pin), net in sorted(got.items()) if (ref, pin) not in expect and not net.startswith("unconnected-")]
    return wrong + stray, len(expect), len(set(expect.values()))


def check_footprints():
    wrong = []
    for one in parts:
        ref, fp, pins = one["ref"], one["fp"], one["pins"]
        lib, name = fp.split(":")
        path = KICAD / "footprints" / f"{lib}.pretty" / f"{name}.kicad_mod"
        if not path.exists():
            wrong.append(f"{ref}: no footprint {fp}")
            continue
        pads = set(re.findall(r'\(pad "([^"]+)"', path.read_text()))
        missing = sorted(set(pins) - pads)
        if missing:
            wrong.append(f"{ref}: {fp} has no pad {missing}")
    return wrong


def check_rules(sch, tmp):
    report = tmp / "erc.json"
    subprocess.run([CLI, "sch", "erc", "--format", "json", "--severity-all", "-o", str(report), str(sch)],
                   capture_output=True, text=True)
    found = []
    for sheet in json.loads(report.read_text()).get("sheets", []):
        for v in sheet.get("violations", []):
            where = "; ".join(i.get("description", "") for i in v.get("items", []))
            found.append(f'{v["severity"]}: {v["description"]} ({where})')
    return found


THROUGH_HOLE = ("Connector_BarrelJack", "TerminalBlock_Phoenix", "Connector_JST", "Connector_PinHeader_2.54mm", "Connector_AMASS", "Converter_DCDC")
PACKAGE = {"R_0603_1608Metric": "0603", "C_0603_1608Metric": "0603", "LED_0603_1608Metric": "0603", "C_1206_3216Metric": "1206", "C_0805_2012Metric": "0805",
           "CP_Elec_6.3x7.7": "6.3 x 7.7 mm can", "CP_Elec_8x10": "8 x 10 mm can", "D_SOD-123": "SOD-123", "D_SMB": "SMB",
           "SOIC-8_3.9x4.9mm_P1.27mm": "SO-8", "ESP32-S3-WROOM-1": "Module", "Fuse_2920_7451Metric": "2920",
           "L_Changjiang_FNR6045S": "6 x 6 x 4.5 mm", "D_SOD-882": "DFN1006", "SW_Push_1P1T_XKB_TS-1187A": "SMD, 5.1 mm square",
           "SW_SPDT_Shouhan_MSK12C02": "SMD, side slider",
           "Converter_DCDC_RECOM_R-78E-0.5_THT": "Through-hole, 3 pins"}
KIND = {"R": "Resistor, 1%,", "C": "Capacitor,", "L": "Inductor,", "F": "Fuse,", "LED": "LED,", "D": "Diode,", "J": "Connector:",
        "SW": "Switch:"}
ORDER = ["U", "Q", "D", "LED", "L", "F", "C", "R", "J", "SW"]


def lines():
    """The parts grouped into lines to buy: same value, same footprint, fitted or not."""
    groups = {}
    for one in parts:
        if one["bom"]:
            same = one["mpn"] if one["ref"][0] in "JS" and one["mpn"] else one["value"]
            groups.setdefault((one["fitted"], same, one["fp"].split(":")[1]), []).append(one)
    out = []
    for (fitted, _, fp), members in groups.items():
        first = members[0]
        value = " / ".join(dict.fromkeys(m["value"] for m in members))
        prefix = re.match(r"[A-Z]+", first["ref"]).group(0)
        package = PACKAGE.get(fp, "HTSSOP-16" if fp.startswith("HTSSOP") else fp if fp.startswith("SOT") else "Through-hole"
                              if prefix == "J" and "USB" not in fp else "SMD")
        out.append({"fitted": fitted, "qty": len(members), "refs": [m["ref"] for m in members], "value": value, "fp": fp,
                    "what": f'{KIND.get(prefix, "")} {value}'.strip(), "package": package, "prefix": prefix,
                    "hole": first["hole"],
                    **{k: first[k] for k in ("mpn", "lcsc", "price", "jlc")}})
    out.sort(key=lambda g: (not g["fitted"], ORDER.index(g["prefix"]), int(re.search(r"\d+", g["refs"][0]).group(0))))
    return out


def write_lists():
    rows = lines()
    with open(HERE / "export" / "parts.csv", "w", newline="") as f:
        out = csv.writer(f)
        out.writerow(["Fitted", "Qty", "References", "Value", "Footprint", "Part number", "LCSC", "JLCPCB class", "Each USD", "Line USD"])
        for g in rows:
            line = f'{g["qty"] * g["price"]:.2f}' if g["price"] != "" else ""
            out.writerow(["yes" if g["fitted"] else "no", g["qty"], " ".join(g["refs"]), g["value"], g["fp"], g["mpn"], g["lcsc"],
                          g["jlc"], g["price"], line])
    with open(HERE / "export" / "bom-jlcpcb.csv", "w", newline="") as f:  # the columns JLCPCB's assembly order form reads
        out = csv.writer(f)
        out.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for g in rows:
            if g["fitted"]:
                out.writerow([g["mpn"] or g["value"], ",".join(g["refs"]), g["fp"], g["lcsc"]])

    def table(wanted):
        text = ("| Qty | Ref | Part | Package | Maker's number | LCSC | JLCPCB class | Each | Line |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
        for g in rows:
            if g["fitted"] == wanted:
                each = f'${g["price"]:.3f}' if g["price"] != "" else "not chosen"
                cost = g["qty"] * g["price"] if g["price"] != "" else None
                line = "" if cost is None else f"${cost:.2f}" if cost >= 0.01 else f"${cost:.3f}"
                text += (f'| {g["qty"]} | {", ".join(g["refs"])} | {g["what"]} | {g["package"]} | {g["mpn"]} | {g["lcsc"]} | '
                         f'{g["jlc"]} | {each} | {line} |\n')
        return text

    fitted = [g for g in rows if g["fitted"]]
    priced = [g for g in fitted if g["price"] != ""]
    total = sum(g["qty"] * g["price"] for g in priced)
    summary = (f'{sum(g["qty"] for g in fitted)} parts on {len(fitted)} lines. The {len(priced)} lines with a price come to '
               f'${total:.2f} for one board at JLCPCB\'s price for one piece.')
    if len(priced) < len(fitted):
        summary += f' {len(fitted) - len(priced)} lines have no part chosen yet.'
    basic = sum(1 for g in fitted if g["jlc"] == "Basic")
    surface = [g for g in fitted if not g["hole"]]
    extended = sum(1 for g in surface if g["jlc"] == "Extended")
    holes = [g for g in fitted if g["hole"]]
    preferred = sum(1 for g in fitted if g["jlc"] == "Preferred")
    summary += (f' {len(holes)} lines ({sum(g["qty"] for g in holes)} parts) are through-hole and cost '
                f'${sum(g["qty"] * g["price"] for g in holes if g["price"] != ""):.2f} of that. JLCPCB classes {basic} lines as Basic '
                f'and {preferred} as Preferred, which carry no fee; {extended} surface-mount lines are Extended and carry its '
                f'per-line fee.')
    print("bill of materials: " + summary)
    joints = {"smd": 0, "hole": 0}
    for one in parts:
        if one["bom"] and one["fitted"]:
            lib, name = one["fp"].split(":")
            text = (KICAD / "footprints" / f"{lib}.pretty" / f"{name}.kicad_mod").read_text()
            joints["hole" if one["hole"] else "smd"] += len(re.findall(r'\(pad "[^"]+" (?:smd|thru_hole)', text))
    print(f'solder joints on fitted parts: {joints["smd"]} surface-mount, {joints["hole"]} through-hole')
    bom = HERE / "BOM.md"
    if bom.exists():
        text = bom.read_text()
        for mark, body in (("fitted", summary + "\n\n" + table(True)), ("not fitted", table(False))):
            start, end = f"<!-- {mark}: written by make_board.py -->\n", f"<!-- end {mark} -->"
            if start in text and end in text:
                text = text[:text.index(start) + len(start)] + body + text[text.index(end):]
        bom.write_text(text)


def main():
    write_drv8876()
    draw()
    sch = HERE / f"{NAME}.kicad_sch"
    sch.write_text(schematic())
    table = HERE / "sym-lib-table"
    if not table.exists():
        table.write_text(f'(sym_lib_table\n\t(version 7)\n\t(lib (name "{NAME}")(type "KiCad")(uri "${{KIPRJMOD}}/{NAME}.kicad_sym")'
                         '(options "")(descr "Symbols KiCad does not ship"))\n)\n')
    project = HERE / f"{NAME}.kicad_pro"
    if not project.exists():
        project.write_text(json.dumps({"meta": {"filename": project.name, "version": 3}}, indent=2) + "\n")
    run("sch", "upgrade", "--force", str(sch))  # KiCad's own layout of the file, so later saves change little

    tmp = Path(os.environ.get("TMPDIR", "/tmp")) / f"{NAME}-check"
    tmp.mkdir(parents=True, exist_ok=True)
    failed = False
    wrong, pins, nets = check_netlist(sch, tmp)
    print(f"netlist: {pins} pins on {nets} nets, {len(wrong)} wrong")
    wrong_fp = check_footprints()
    print(f"footprints: {len(parts)} parts, {len(wrong_fp)} wrong")
    rules = check_rules(sch, tmp)
    errors = [r for r in rules if r.startswith("error")]
    print(f"rules check: {len(errors)} errors, {len(rules) - len(errors)} warnings")
    for line in wrong + wrong_fp + rules:
        print("  " + line)
        failed = failed or not line.startswith("warning")

    (HERE / "export").mkdir(exist_ok=True)
    run("sch", "export", "pdf", "-o", str(HERE / "export" / f"{NAME}.pdf"), str(sch))
    write_lists()
    print(f"wrote {sch.name}, export/{NAME}.pdf, export/parts.csv, export/bom-jlcpcb.csv")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

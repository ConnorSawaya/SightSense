"""SightSense v2: the cane's shaft, two carbon tubes and one joint, redone so the joint stops snapping.

The old joint (SightSense hardware/cane-coupler v3/v4) put all the bending through a 10 x 8.5 mm printed
tongue with a hole down it: about 2-4 N*m printed upright, against an estimated 8-12 N*m when the cane is
lifted by the handle. Here a smaller carbon tube (a spigot, like a tent pole's ferrule) carries the bending: it is
glued deep into one carbon tube and slides deep into the next. The two printed collars only stop the sections
twisting (an off-centre key, so it only goes together one way) and hoop the tube mouths so the carbon cannot
split where the spigot bears on it.

Frame: the cane's axis is Z, the joint is at z = 0, the upper section (A) is above it and holds the glued
spigot; the lower section (B) slides on. Two 400 mm tubes (v1 had three or four, too long).
Run: .venv/bin/python projects/sightsense-v2/model.py
"""
import math
from ftccad import *
from ftccad.cli import run
import ftccad.check as _check

_orig_check = _check.check


def _cane_check(asm, **kw):
    kw.setdefault("size_box", None)   # a cane is longer than the FTC 18 in box the kit checks by default
    return _orig_check(asm, **kw)


_check.check = _cane_check

# ------------------------------------------------------------------ numbers you might change
TUBE_OD, TUBE_ID = 18.0, 16.0          # the carbon tubes now on the cane (hardware/BOM.md); measure yours
SPIGOT_BOUGHT = (16.0, 13.0)           # carbon tube 16 x 13 mm (bought 420 mm long, 2 per pack)
SPIGOT_OD = 15.9                       # its sliding half sanded down to slide in a 16.0 mm bore
SPIGOT_WALL = (SPIGOT_OD - SPIGOT_BOUGHT[1]) / 2
GLUED, FREE = 65.0, 65.0               # spigot glued into A / sliding into B (both over 3.5 x the tube size)
TUBE_LEN = 400.0                       # each of the two carbon tubes (the 400 mm tubes v1 used)
COLLAR_LEN, COLLAR_OD = 14.0, 24.0     # printed collar over each tube end
GLUE_GAP = 0.15                        # collar bore over the tube, a side, for epoxy
LUG_H, LUG_CLEAR = 3.0, 0.25           # key height; clearance a side round each lug in its notch
LUGS = [(0.0, 40.0), (180.0, 24.0)]    # (centre angle, width in degrees): a wide and a narrow lug = one way only
CORD = 3.2                             # 1/8 in shock cord, through the spigot

# ------------------------------------------------------------------ strength (estimates, not measurements)
LOAD = (8.0, 12.0)                     # N*m at an upper joint, cane carried level: hardware/joint-sleeve/README.md
OLD_TONGUE = (2.0, 4.0)                # N*m the old printed tongue takes, printed upright (same README)
CF_STRENGTH = 500.0                    # MPa, typical for roll-wrapped carbon tube in bending (assumed)

R_BORE = TUBE_OD / 2 + GLUE_GAP
SPIGOT_ID = SPIGOT_OD - 2 * SPIGOT_WALL


def section_modulus(od, id_):
    return math.pi * (od ** 4 - id_ ** 4) / (32 * od)


def tube(od, id_, z0, length):
    return Pos(0, 0, z0) * (Cylinder(od / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN))
                            - Cylinder(id_ / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN)))


def sector(r_in, r_out, mid_deg, width_deg, z0, h):
    """A ring segment centred on mid_deg, width_deg wide, from z0 up h."""
    a0, a1 = math.radians(mid_deg - width_deg / 2), math.radians(mid_deg + width_deg / 2)
    n = 24
    outer = [(r_out * math.cos(a0 + (a1 - a0) * i / n), r_out * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    inner = [(r_in * math.cos(a1 - (a1 - a0) * i / n), r_in * math.sin(a1 - (a1 - a0) * i / n)) for i in range(n + 1)]
    return Pos(0, 0, z0) * extrude(Polygon(*(outer + inner), align=None), h)


def collar_a():
    """On the upper tube's end (z 0..14); the two lugs stick down past the joint into collar B."""
    body = tube(COLLAR_OD, 2 * R_BORE, 0, COLLAR_LEN)
    for mid, w in LUGS:
        body += sector(R_BORE, COLLAR_OD / 2, mid, w, -LUG_H, LUG_H)
    return body


def collar_b():
    """On the lower tube's end (z -14..0), with the two notches the lugs drop into."""
    body = tube(COLLAR_OD, 2 * R_BORE, -COLLAR_LEN, COLLAR_LEN)
    r_mid = (R_BORE + COLLAR_OD / 2) / 2
    for mid, w in LUGS:
        widen = math.degrees(2 * LUG_CLEAR / r_mid)
        body -= sector(R_BORE - 0.5, COLLAR_OD / 2 + 0.5, mid, w + widen, -(LUG_H + 0.3), LUG_H + 0.4)
    return body


def build():
    a = Assembly("sightsense-v2")
    carbon = "#2B2D31"
    tube_a = a.add(tube(TUBE_OD, TUBE_ID, 0, TUBE_LEN), "carbon tube A (upper)", kind="other", color=carbon)
    tube_b = a.add(tube(TUBE_OD, TUBE_ID, -TUBE_LEN, TUBE_LEN), "carbon tube B (lower)", kind="other", color=carbon)
    spigot = a.add(tube(SPIGOT_OD, SPIGOT_ID, -FREE, GLUED + FREE), "spigot: carbon tube 16 x 13 mm",
                   kind="other", color="#3A3D42")
    ca = a.add(collar_a(), "collar A (keyed)", kind="printed")
    cb = a.add(collar_b(), "collar B (notched)", kind="printed")
    a.add(Pos(0, 0, -TUBE_LEN) * Cylinder(CORD / 2, 2 * TUBE_LEN, align=(Align.CENTER, Align.CENTER, Align.MIN)),
          "shock cord", kind="context", color="#C23B22")

    # meant to touch: the tube ends butt at the joint, the collars' faces meet, each collar sits on its tube
    a.allow(tube_a, tube_b)
    a.allow(ca, cb)
    a.allow(ca, tube_a)
    a.allow(cb, tube_b)
    a.watch(spigot, tube_b, "spigot in tube B (sliding fit)")
    a.watch(spigot, tube_a, "spigot in tube A (glue line)")

    # strength: the spigot now carries the bending, not printed plastic
    z_sp = section_modulus(SPIGOT_OD, SPIGOT_ID)
    m_sp = z_sp * CF_STRENGTH / 1000
    m_cf = section_modulus(TUBE_OD, TUBE_ID) * CF_STRENGTH / 1000
    a.require(m_sp >= 3 * LOAD[1],
              f"spigot bends at about {m_sp:.0f} N*m (Z {z_sp:.0f} mm^3, carbon, assumed {CF_STRENGTH:.0f} MPa): {m_sp / LOAD[1]:.1f}x the "
              f"{LOAD[1]:.0f} N*m load estimate; the old tongue took {OLD_TONGUE[0]:.0f}-{OLD_TONGUE[1]:.0f}")
    a.require(m_cf >= 0.9 * m_sp, f"the outer carbon tube is about as strong: about {m_cf:.0f} N*m (assumed {CF_STRENGTH:.0f} MPa)")
    a.require(min(GLUED, FREE) >= 3.5 * TUBE_OD,
              f"spigot reaches {GLUED:.0f} mm into A and {FREE:.0f} mm into B (rule of thumb: 3.5 x {TUBE_OD:.0f} mm)")
    play = (TUBE_ID - SPIGOT_OD) / 2
    a.require(0 < play <= 0.15, f"spigot to tube clearance {play:.3f} mm a side (sliding, little wobble)")
    a.require(LUG_CLEAR >= 0.2, f"lugs have {LUG_CLEAR} mm clearance a side in their notches (prints go together)")
    a.require(SPIGOT_ID > CORD + 2, f"cord {CORD} mm runs through the spigot's {SPIGOT_ID:.1f} mm bore")
    a.hardware("carbon tube 16 x 13 mm, cut to 130 mm, sliding half sanded to fit (one per joint; a 420 mm tube makes three)", 1)
    a.hardware("1/8 in shock cord, through both tubes", 1)
    a.hardware("2-part epoxy: spigot into tube A, collars onto their tubes", 1)
    return a


run(build, __file__)

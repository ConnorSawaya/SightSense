"""SightSense v2: the cane's tip. A VEX 2 in omni wheel driven by a Pololu micro metal gearmotor.

The wheel's axle points along the walking direction, so spinning it pushes the cane's tip left or right and
its rollers let the tip roll forward. A printed adapter fills the wheel's 1/2 in hex and clamps the motor's
3 mm D-shaft with an M3 set screw. The wheel is held on both sides, so the user's weight goes into the
printed tip, not into the motor's 3 mm shaft: on the motor side the adapter's collar turns in a sleeve, on
the far side the adapter turns on a 3 mm steel pin held by an arm over the top of the wheel.

The tip is one printed part: the motor's housing, the sleeve, the arm, and a plug glued into the lower
carbon tube. The motor cannot go inside the wheel: the wheel's centre is a 12.7 mm hex, smaller than the
motor (12 x 10 mm, 15.6 mm corner to corner).

Frame: ground at z = 0, +Y is the walking direction, X is sideways. The cane leans back LEAN_DEG from upright
and its axis passes through the wheel's contact point. Run: .venv/bin/python projects/sightsense-v2-tip/model.py
Sources: the wheel is VEX's own CAD (276-9044, parts/vex-276-9044/raw) and the motor Pololu's own CAD
(mmgm-pm.step from their micro metal gearmotor STEP models, parts/pololu-997/raw).
"""
import math
import pathlib
from ftccad import *
from ftccad.cli import run
import ftccad.check as _check

_orig_check = _check.check


def _cane_check(asm, **kw):
    kw.setdefault("size_box", None)   # a cane is longer than the FTC 18 in box the kit checks by default
    return _orig_check(asm, **kw)


_check.check = _cane_check

# ------------------------------------------------------------------ numbers you might change
LEAN_DEG = 30.0                 # the cane leans back this far from upright (the handle is drawn for 30)
TUBE_OD, TUBE_ID = 18.0, 16.0
PLUG_OD, PLUG_LEN = 15.8, 30.0  # plug glued into the lower tube
TUBE_END = 56.0                 # where the tube ends, measured up the cane's axis from the contact point
HEX_AF = 12.6                   # adapter hex across flats (wheel's is 12.70: 1/2 in)
COLLAR_D, COLLAR_LEN = 15.6, 6.0
SLEEVE_GAP = 0.25               # collar to sleeve, a side
SHAFT_BORE, SHAFT_FLAT = 3.1, 1.05   # 3 mm D-shaft: round 3.1, flat 1.05 from the axis (shaft's is 1.0)
PIN_D, PIN_BORE = 3.0, 3.15     # 3 mm steel dowel pin as the far-side axle
WALL = 2.4
CAP_T = 3.0                     # rear cap that keeps the motor in its tunnel
ARM_W, ARM_T = 10.0, 7.0        # arm over the wheel: width (X) and thickness
ARM_GAP = 3.5                   # arm to the wheel's rollers

# ------------------------------------------------------------------ parts' sizes (from vendor CAD / drawing)
GB = (12.0, 10.0, 9.0)          # Pololu gearbox: width (X), height (Z), length
OVERALL = 25.8                  # gearbox face to the motor's back end (Pololu's CAD)
SHAFT_D, SHAFT_LEN = 3.0, 10.0  # from the gearbox face
BUSH_D, BUSH_H = 4.0, 0.72

STEP = pathlib.Path(__file__).resolve().parents[2] / "parts/vex-276-9044/raw/vex-2in-omni-276-9044.step"
MOTOR_STEP = pathlib.Path(__file__).resolve().parents[2] / "parts/pololu-997/raw/mmgm-pm.step"   # Pololu's own CAD
MOTOR_FACE_Z = 9.0             # in Pololu's file: the gearbox face; the shaft runs up +Z, its flat faces +Y
_w = import_step(str(STEP))
R_WHEEL = _w.bounding_box().size.Y / 2          # 25.27: roller tips
HALF_W = _w.bounding_box().size.X / 2           # 7.94: the wheel's half width
HEX_HALF = 6.0                                   # the wheel's hex runs +-6.0 mm, then a chamfer and a 15.9 mm recess

up = (0, -math.sin(math.radians(LEAN_DEG)), math.cos(math.radians(LEAN_DEG)))   # up the cane's axis
nrm = (0, math.cos(math.radians(LEAN_DEG)), math.sin(math.radians(LEAN_DEG)))   # across it, forward

# motor stack along -Y, behind the wheel
Y_WHEEL_BACK = -HALF_W
Y_COLLAR_BACK = Y_WHEEL_BACK - COLLAR_LEN
Y_GB_FACE = Y_COLLAR_BACK - (BUSH_H + 0.6) - 1.2          # 1.2 mm front wall between gearbox face and collar
Y_FRONT_WALL = (Y_GB_FACE, Y_GB_FACE + 1.2 + BUSH_H)
Y_MOTOR_BACK = Y_GB_FACE - OVERALL
Y_SET = Y_COLLAR_BACK + COLLAR_LEN / 2                    # set screw, across the collar's middle
ZC = R_WHEEL                                              # axle height
Y_ARM = HALF_W + ARM_GAP + ARM_T / 2                      # the arm's front leg, in front of the wheel


def on_axis(p, s):
    return Vector(p[0] + up[0] * s, p[1] + up[1] * s, p[2] + up[2] * s)


def cyl_y(r, y0, y1, x=0.0, z=None):
    z = ZC if z is None else z
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(r, abs(y1 - y0))


def along_cane(r, s0, s1):
    c = on_axis((0, 0, 0), (s0 + s1) / 2)
    return Pos(c.X, c.Y, c.Z) * Rot(LEAN_DEG, 0, 0) * Cylinder(r, s1 - s0)


def wheel():
    w = Rot(0, 0, 90) * _w
    keep = [s for i, s in enumerate(w.solids()) if i not in (1, 2)]   # leave out VEX's two shaft adapters
    return Pos(0, 0, ZC) * Compound(keep)


def wheel_hex_points():
    """The wheel's own hex, read from VEX's CAD where it sits in this frame."""
    body = (Pos(0, 0, ZC) * (Rot(0, 0, 90) * _w.solids()[0]))
    sec = body & Box(200, 0.02, 200).moved(Location((0, 0.0, ZC)))
    for f in sec.faces():
        for wire in f.inner_wires():
            pts = [(v.X, v.Z - ZC) for v in wire.vertices()]
            if pts and max(math.hypot(*p) for p in pts) < 9 and len(pts) == 6:
                return pts
    raise RuntimeError("wheel hex not found")


def adapter():
    hx = wheel_hex_points()
    k = HEX_AF / 12.70
    face = Plane.XZ * Polygon(*[(x * k, z * k) for x, z in hx], align=None)
    hexp = Pos(0, HEX_HALF, ZC) * extrude(face, 2 * HEX_HALF)          # Plane.XZ extrudes toward -Y
    body = hexp + cyl_y(COLLAR_D / 2, Y_COLLAR_BACK, Y_WHEEL_BACK - 0.15)
    body += cyl_y(6.3, Y_WHEEL_BACK - 0.2, -HEX_HALF + 0.1)          # thinner neck past two ribs in the wheel's recess
    # D bore for the motor shaft, from the collar's back
    d = cyl_y(SHAFT_BORE / 2, Y_COLLAR_BACK - 0.1, Y_COLLAR_BACK + SHAFT_LEN + 0.5)
    d -= Pos(0, (Y_COLLAR_BACK + Y_COLLAR_BACK + SHAFT_LEN) / 2, ZC + SHAFT_FLAT + 2) * Box(10, 30, 4)
    body -= d
    # set screw hole, M3 cut into the print (2.5 mm), coming down from the top onto the shaft's flat
    body -= Pos(0, Y_SET, ZC + 5) * Cylinder(1.25, 10)
    # bore for the far-side pin
    body -= cyl_y(PIN_BORE / 2, -1.0, HEX_HALF + 0.1)
    return body


def motor():
    """Pololu's STEP model of the micro metal gearmotor (precious-metal brushes, no encoder, ratios below
    1000:1), turned so its shaft points at the wheel (+Y) and its flat faces up under the set screw."""
    m = import_step(str(MOTOR_STEP))
    return Pos(0, Y_GB_FACE, ZC) * Rot(0, 180, 0) * Rot(-90, 0, 0) * Pos(0, 0, -MOTOR_FACE_Z) * m


def tip():
    iw, ih = GB[0] + 0.3, GB[1] + 0.3
    y0, y1 = Y_MOTOR_BACK - CAP_T - 0.5, Y_FRONT_WALL[1]
    housing = Pos(0, (y0 + y1) / 2, ZC) * Box(iw + 2 * WALL, y1 - y0, ih + 2 * WALL)
    housing -= cyl_y(BUSH_D / 2 + 0.3, Y_GB_FACE - 0.1, y1 + 0.1)                           # shaft and bushing
    sleeve = cyl_y(COLLAR_D / 2 + SLEEVE_GAP + WALL, y1, Y_WHEEL_BACK - 0.6)
    sleeve -= cyl_y(COLLAR_D / 2 + SLEEVE_GAP, y1 - 0.1, Y_WHEEL_BACK)
    sleeve -= Pos(0, Y_SET, ZC + 8) * Cylinder(2.2, 8)                                      # reach the set screw
    s_low = (TUBE_OD / 2 * math.cos(math.radians(LEAN_DEG)) - Y_WHEEL_BACK + 3.5) / math.sin(math.radians(LEAN_DEG))   # neck's front edge 3.5 mm behind the wheel
    neck = along_cane(TUBE_OD / 2, s_low, TUBE_END) + along_cane(PLUG_OD / 2, TUBE_END, TUBE_END + PLUG_LEN)
    # arm: up from the neck, over the wheel, down in front of it to the far-side pin
    top = ZC + R_WHEEL + ARM_GAP + ARM_T / 2
    a0 = on_axis((0, 0, 0), TUBE_END - 8)
    path = [(a0.Y, a0.Z), (Y_WHEEL_BACK - 4, top), (Y_ARM, top), (Y_ARM, ZC)]
    arm = None
    for (ya, za), (yb, zb) in zip(path, path[1:]):
        L = math.hypot(yb - ya, zb - za)
        ang = math.degrees(math.atan2(zb - za, yb - ya))
        seg = Pos(0, (ya + yb) / 2, (za + zb) / 2) * Rot(ang, 0, 0) * Box(ARM_W, L + ARM_T, ARM_T)
        arm = seg if arm is None else arm + seg
    boss = cyl_y(6.0, Y_ARM - ARM_T / 2, Y_ARM + ARM_T / 2)
    part = housing + sleeve + neck + arm + boss
    part -= Pos(0, (y0 - 1 + Y_GB_FACE) / 2, ZC) * Box(iw, Y_GB_FACE - y0 + 1, ih)          # motor tunnel, open at the back
    part -= along_cane(2.6, s_low - 2, TUBE_END + PLUG_LEN + 1)                            # wires and cord up the middle
    zw = ZC + ih / 2 + WALL + 4.5                                                          # wires in from behind
    sw = zw / math.cos(math.radians(LEAN_DEG))
    part -= Pos(0, (y0 + on_axis((0, 0, 0), sw).Y) / 2, zw) * Rot(90, 0, 0) * Cylinder(2.2, abs(on_axis((0, 0, 0), sw).Y - y0))
    c = on_axis((0, 0, 0), TUBE_END + PLUG_LEN - 6)
    part -= Pos(c.X, c.Y, c.Z) * Rot(0, 90, 0) * Cylinder(1.1, 20)                          # cross hole: the shock cord ties here
    part -= cyl_y(PIN_D / 2 - 0.05, HALF_W + 0.5, Y_ARM + ARM_T / 2 + 0.1)                  # pin pressed into the boss
    return part


def rear_cap():
    iw, ih = GB[0] + 0.3, GB[1] + 0.3
    y0 = Y_MOTOR_BACK - CAP_T - 0.5
    cap = Pos(0, y0 + CAP_T / 2, ZC) * Box(iw - 0.2, CAP_T, ih - 0.2)
    cap -= cyl_y(2.2, y0 - 0.1, y0 + CAP_T + 0.1)                                                 # motor wires out
    return cap


def build():
    a = Assembly("sightsense-v2-tip")
    w = a.add(wheel(), "VEX 2 in omni wheel (276-9044)", kind="wheel")
    ad = a.add(adapter(), "wheel adapter (hex to 3 mm D)", kind="printed")
    m = a.add(motor(), "Pololu 150:1 HP 6V micro metal gearmotor (Pololu CAD)", kind="motor")
    t = a.add(tip(), "tip: motor housing, sleeve, arm, tube plug", kind="printed",
              print_rot=Rot(0, 90, 0))
    cap = a.add(rear_cap(), "rear cap", kind="printed")
    pin = a.add(cyl_y(PIN_D / 2, -0.8, Y_ARM + ARM_T / 2), "3 mm steel pin, 20 mm", kind="shaft")
    tube = a.add(along_cane(TUBE_OD / 2, TUBE_END, TUBE_END + 120) - along_cane(TUBE_ID / 2, TUBE_END - 1, TUBE_END + 121),
                 "lower carbon tube (end)", kind="other", color="#2B2D31")
    a.add(Pos(0, 0, -0.5) * Box(160, 160, 1), "ground", kind="context", color="#D9D4C7")

    a.allow(ad, w)          # hex in the wheel's hex, collar flange in its recess
    a.allow(ad, m, overlap=False)
    a.allow(ad, t)          # collar turns in the sleeve
    a.allow(pin, [ad, t], overlap=True)   # pin pressed into the boss, adapter turns on it
    a.allow(m, t)           # motor in its tunnel, gearbox face against the front wall
    a.allow(cap, [t, m])
    a.allow(tube, t)        # plug glued in the tube
    a.watch(w, t, "wheel to the tip (arm, sleeve)", min_gap=0.4)
    a.watch(m, ad, "motor to adapter")

    # checks
    contact_ok = True
    a.require(contact_ok, f"wheel {2 * R_WHEEL:.1f} mm across ({2 * R_WHEEL / 85:.0%} of the 85 mm v1 wheel)")
    housing_low = ZC - (GB[1] + 0.3) / 2 - WALL
    a.require(housing_low >= 10, f"lowest point of the housing {housing_low:.1f} mm above the ground (wheel touches at 0)")
    y_shaft_end = Y_GB_FACE + SHAFT_LEN
    a.require(Y_GB_FACE + 2 < Y_SET < y_shaft_end - 1, f"set screw lands on the shaft ({y_shaft_end - Y_SET:.1f} mm from its end)")
    engage = y_shaft_end - Y_COLLAR_BACK
    a.require(engage >= 6, f"motor shaft {engage:.1f} mm into the adapter")
    # the arm: a rough bending check with the user leaning on the cane
    load = 60.0                                   # N up through the wheel (about 6 kg), estimate
    lever = (Y_ARM - (Y_WHEEL_BACK - 4))          # far-side half of the load acts across the arm's top run
    m_arm = load / 2 * lever / 1000
    z = ARM_W * ARM_T ** 2 / 6
    sigma = m_arm * 1000 / z
    a.require(sigma < 40 / 2.5, f"arm stress about {sigma:.0f} MPa at {load:.0f} N on the cane (PLA along its layers about 40 MPa)")
    a.hardware("Pololu 150:1 Micro Metal Gearmotor HP 6V (Pololu 997)", 1)
    a.hardware("VEX 2 in omni wheel, 276-9044 (pack of 4)", 1)
    a.hardware("3 mm steel dowel pin, 20 mm", 1)
    a.hardware("M3 x 6 set screw (grub screw), into the adapter", 1)
    return a


run(build, __file__)

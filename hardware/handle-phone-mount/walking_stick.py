"""Parametric walking stick: tilted handle, pole-mounted phone camera mount, motor mount.

Run with build123d installed:  python walking_stick.py
Writes every printable part into export/ (STEP in the design frame, STL already
turned to its print orientation), runs the geometric checks and prints them.
preview.py renders the views. All dimensions are millimetres.

RESEARCH PROTOTYPE. Nothing here has been load tested or validated as a
mobility aid.

Stick frame (used by the handle, collar and phone cradle):
  +Z  up the pole, z=0 at the top end of the tube
  +X  the pole's forward normal: square to the pole, on the side the user walks towards
  +Y  to the user's left
In use the pole leans back: its top comes towards the user by STICK_LEAN_DEG
and its tip is out in front. The grip is turned by the same angle, so it is
level when the pole leans.

The camera collar clamps on the pole below the handle. The phone stands up from
a pivot on the collar, in portrait, screen facing back at the pole and rear
camera facing forward.

PHONE_TILT_DEG is the angle between the camera axis and +X, in the X-Z plane.
0 = phone parallel to the pole; positive = phone top swings forward and the
camera pitches down. With the pole leaning back by L, the camera looks
(tilt - L) degrees below the horizon.

Motor-mount frame: pole up +Z with its bottom end at z=0, wheel axle along X,
wheel centred under the pole.
"""

from math import atan2, cos, degrees, radians, sin
from pathlib import Path

from build123d import (
    Axis,
    Box,
    Circle,
    Compound,
    Cylinder,
    Ellipse,
    GeomType,
    Plane,
    PolarLocations,
    Pos,
    Rectangle,
    RectangleRounded,
    RegularPolygon,
    Rot,
    Spline,
    chamfer,
    export_step,
    export_stl,
    extrude,
    fillet,
    loft,
    make_hull,
    sweep,
)

# --- stick ---
STICK_OD = 18.0  # carbon tube outside diameter
STICK_ID = 16.0  # carbon tube inside diameter
STICK_FIT = 0.3  # added to every bore that goes over the tube (0.15 per side)
PLUG_FIT = 0.3  # removed from the plug that goes inside the tube

# --- handle ---
GRIP_W = 30.0  # across the palm
GRIP_H = 26.0
# Rear to nose, before tilting. The pole joins near the front, so all four
# fingers wrap the grip behind it; the third point sits on the pole axis. The
# nose runs on level ahead of the pole to carry the thumb button.
GRIP_PATH = [(-102, 0, 9), (-66, 0, 15), (0, 0, 16), (24, 0, 16), (52, 0, 14.5)]
STICK_LEAN_DEG = 30.0  # how far the pole leans back in use (top towards the user)
GRIP_TILT_DEG = STICK_LEAN_DEG  # grip is turned nose-down by this, so it is level in use
SOCKET_OD = 28.0
SOCKET_DEPTH = 45.0  # how far the tube goes in
PLUG_RECESS = 2.0  # plug stops short of the mouth so the tube starts easily
BLEND_R = 6.0  # fillet where the socket meets the grip
SET_SCREW_D = 2.6  # M3 screw cuts its own thread and pinches the tube against the plug

# --- thumb button in the nose ---  UNCONFIRMED: sized for a 12 mm panel-mount push button
BUTTON_HOLE_D = 12.3  # mounting hole for the button's threaded body
BUTTON_FROM_POLE = 34.0  # along the grip, ahead of the pole axis; any closer and its pocket cuts into the socket
BUTTON_SEAT_D = 17.0  # flat cut into the top of the grip for the button's head to sit on
BUTTON_SEAT_DROP = 2.0  # how far that flat sits below the crown of the grip
BUTTON_PANEL_T = 4.0  # plastic clamped between the button's head and its nut
BUTTON_POCKET_D = 17.5  # pocket under the nose for the nut (14 mm across flats) and the wires
BUTTON_HEAD_D = 15.0  # reference model only
BUTTON_HEAD_H = 2.5
BUTTON_BODY_LEN = 21.0  # below the head, reference model only

# --- motor: 37 mm DC gearmotor (JGB37 style) ---
MOTOR_D = 37.0
MOTOR_BOLT_CIRCLE = 31.0
MOTOR_BOLTS = 6
MOTOR_BOLT_D = 3.2  # M3 close fit
MOTOR_HEAD_D = 6.2
MOTOR_HEAD_DEPTH = 2.0
SHAFT_OFFSET = 7.0  # output shaft is off the gearbox centre
SHAFT_BOSS_D = 13.0  # clearance for the 12 mm boss around the shaft

# --- wheel ---
WHEEL_D = 65.0
WHEEL_W = 26.0
WHEEL_GAP = 4.0  # wheel side to mounting plate
WHEEL_CLEARANCE = 6.0  # wheel top to underside of the stick cup

# --- mount ---
PLATE_T = 5.0
PLATE_W = 46.0
COLLAR_WALL = 5.0
COLLAR_H = 45.0
CUP_FLOOR = 4.0  # the stick end bears on this
SLIT = 3.0
CLAMP_BOLT_D = 3.2  # M3 close fit: printed holes come out a little small, so this ends up near 3.0
CLAMP_NUT_AF = 5.7  # M3 nut across flats

# --- phone, INCLUDING its case ---  UNCONFIRMED placeholders: measure yours
PHONE_ORIENTATION = "portrait"  # only portrait is modelled so far
PHONE_W = 78.0
PHONE_H = 162.0
PHONE_T = 12.0
PHONE_MASS_G = 230.0
PHONE_FIT = 0.8  # total slack added to the pocket width and depth
# camera bump on the phone's back, for the reference model and the view check
CAM_BUMP_W = 40.0
CAM_BUMP_H = 40.0
CAM_BUMP_T = 2.5
CAM_BUMP_FROM_TOP = 8.0
CAM_BUMP_FROM_SIDE = 8.0  # from the +Y edge
CAM_KEEPOUT_H = 60.0  # band at the top of the back that the cradle never covers
CAM_FOV_HALF_DEG = 35.0  # half angle of the view volume used in the obstruction check
BUTTON_KEEPOUT = (70.0, 140.0)  # side-button band, heights above the phone's bottom edge
PORT_KEEPOUT_W = 44.0  # gap in the bottom shelf: charging port, bottom mics and speaker

# --- phone tilt ---
PHONE_TILT_DEG = 45.0  # see module docstring for the reference
TILT_MIN = 0
TILT_MAX = 75
TILT_STEP = 15

# --- camera collar: split clamp on the pole with the tilt joint's tongue ---
CAM_COLLAR_Z = -240.0  # collar centre, measured from the top end of the tube
TONGUE_T = 8.0  # thickness of the tongue the cradle pivots on
HAND_CLEARANCE = 22.0  # finger thickness around the grip, for the clearance envelope

# --- tilt joint: M3 pivot screw plus an M3 index screw ---
JOINT_R = 14.5  # tongue disc radius
JOINT_GAP = 0.4  # total side slack between tongue and cheeks
CAM_COLLAR_H = 2 * JOINT_R  # collar height, flush with the tongue disc so it prints flat
CHEEK_T = 5.5  # sets the clevis width so an M3 x 20 screw reaches fully through its nut
PIVOT_BOLT_D = 3.2  # M3 close fit
PIVOT_NUT_AF = 5.7  # M3 nut across flats
PIVOT_NUT_DEPTH = 2.4
INDEX_R = 10.0  # index holes sit on this radius around the pivot
INDEX_D = 3.2  # M3 close fit
INDEX_NUT_AF = 5.7  # M3 nut across flats
INDEX_NUT_DEPTH = 2.4
INDEX_PIN_ANGLES = (90.0, 135.0)  # two pin holes in the cheeks, used on alternate steps

# --- cradle ---
CRADLE_WALL = 3.0
BACK_T = 4.0
BACK_H = 95.0  # back plate height above the phone's bottom edge
SHELF_T = 4.0
SIDE_H = 40.0  # side walls and lips, above the phone's bottom edge
LIP_T = 3.0
LIP_OVER = 2.5  # how far the lips reach over the screen edge
FRONT_BAR_T = 5.0
FRONT_LIP_H = 8.0  # bottom lip over the screen
CRADLE_R = 8.0  # outline corner radius
EDGE_R = 3.0  # rounding on lip and bar tops
STRAP_W = 20.0  # hook-and-loop strap
STRAP_T = 2.0
STRAP_Z = 58.0  # strap centre above the phone's bottom edge
STRAP_NOTCH = 1.5  # depth of the guide notches in the plate edges
TETHER_HOLE_D = 4.0


def grip_path():
    return Spline(*GRIP_PATH)


def hex_pocket(across_flats, depth):
    """Hexagonal pocket that opens towards -Y from y=0."""
    return Rot(90, 0, 0) * extrude(RegularPolygon(across_flats / 3**0.5, 6), depth)


def grip_location():
    """Turns the grip nose-down about the point where the pole axis meets it."""
    centre = GRIP_PATH[2][2]
    return Pos(0, 0, centre) * Rot(0, GRIP_TILT_DEG, 0) * Pos(0, 0, -centre)


def path_param_at_x(x):
    """Where along the untilted grip path the centreline reaches this x."""
    path = grip_path()
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if (path @ mid).X < x else (lo, mid)
    return (lo + hi) / 2


def button_location():
    """Button frame in the stick frame: origin on the grip centreline, +Z out through the top of the grip."""
    path = grip_path()
    u = path_param_at_x(BUTTON_FROM_POLE)
    tangent = path % u
    frame = Plane(origin=path @ u, x_dir=tangent, z_dir=(-tangent.Z, 0, tangent.X))
    return grip_location() * frame.location


def button_cut():
    """Hole for the button's thread, a flat for its head, and a pocket for its nut and wires."""
    seat_z = GRIP_H / 2 - BUTTON_SEAT_DROP
    # the thread hole only spans the clamped plastic; any longer and it would run on into the pole socket
    cut = Pos(0, 0, seat_z - BUTTON_PANEL_T / 2) * Cylinder(BUTTON_HOLE_D / 2, BUTTON_PANEL_T + 1)
    cut += Pos(0, 0, seat_z + GRIP_H / 2) * Cylinder(BUTTON_SEAT_D / 2, GRIP_H)
    return cut + button_pocket()


def button_pocket():
    """The nut pocket alone, in the button frame: from under the clamped plastic down through the nose."""
    pocket_top = GRIP_H / 2 - BUTTON_SEAT_DROP - BUTTON_PANEL_T
    depth = pocket_top + GRIP_H / 2 + 1
    return Pos(0, 0, pocket_top - depth / 2) * Cylinder(BUTTON_POCKET_D / 2, depth)


def make_handle():
    path = grip_path()
    section = Plane(origin=path @ 0, x_dir=(0, 1, 0), z_dir=path % 0) * Ellipse(GRIP_W / 2, GRIP_H / 2)
    grip = sweep(section, path)
    ends = grip.edges().sort_by(Axis.X)
    grip = grip_location() * fillet([ends[0], ends[-1]], 9)

    socket_top = GRIP_PATH[2][2]
    socket_len = SOCKET_DEPTH + socket_top
    socket = Pos(0, 0, socket_top - socket_len / 2) * Cylinder(SOCKET_OD / 2, socket_len)
    handle = grip + socket

    # blend where the socket runs into the grip: the seam is every curved edge
    # lying on the socket's cylinder above its mouth
    def on_socket(edge):
        points = [edge @ t for t in (0.1, 0.5, 0.9)]
        return all(abs((p.X**2 + p.Y**2) ** 0.5 - SOCKET_OD / 2) < 1e-3 and p.Z > 1 - SOCKET_DEPTH for p in points)

    seam = [e for e in handle.edges() if e.geom_type != GeomType.LINE and on_socket(e)]
    for radius in (BLEND_R, BLEND_R / 2, 1.5):
        try:
            blended = fillet(seam, radius)
            if blended.is_valid:
                handle = blended
                break
        except Exception:
            continue
    handle = cut_tube_socket(handle, SOCKET_DEPTH, set_screw_z=-SOCKET_DEPTH / 2)
    return handle - button_location() * button_cut()


def cut_tube_socket(body, depth, set_screw_z=None):
    """Cut a pocket for the tube into the underside of body (mouth at z=-depth).

    The tube wall slides into a ring-shaped slot: a bore around its outside and
    a plug up its inside, so the thin carbon wall is supported on both faces.
    """
    bore_r = (STICK_OD + STICK_FIT) / 2
    plug_r = (STICK_ID - PLUG_FIT) / 2
    plug_len = depth - PLUG_RECESS

    body -= Pos(0, 0, -depth / 2) * Cylinder(bore_r, depth)
    mouth = body.edges().filter_by(GeomType.CIRCLE).filter_by(lambda e: abs(e.radius - bore_r) < 1e-3)
    body = chamfer(mouth.sort_by(Axis.Z)[0], 0.8)

    plug = Pos(0, 0, -plug_len / 2) * Cylinder(plug_r, plug_len)
    plug = chamfer(plug.edges().sort_by(Axis.Z)[0], 1.2)
    body += plug

    if set_screw_z is not None:
        wall = SOCKET_OD / 2 - bore_r
        body -= Pos(0, SOCKET_OD / 2, set_screw_z) * Rot(90, 0, 0) * Cylinder(SET_SCREW_D / 2, 2 * wall + 2)
    return body


def make_fit_test():
    """Short slice of the handle socket: print this first and try it on the tube."""
    depth = 12.0
    ring = Pos(0, 0, (2 - depth) / 2) * Cylinder(SOCKET_OD / 2, depth + 2)
    return cut_tube_socket(ring, depth)


def tilt_positions():
    return list(range(TILT_MIN, TILT_MAX + 1, TILT_STEP))


def index_pin_angle(tilt):
    """Which cheek pin hole (angle in the cradle frame) locks this tilt step."""
    return INDEX_PIN_ANGLES[tilt_positions().index(int(tilt)) % 2]


def tongue_hole_angles():
    """Index hole angles on the collar's tongue, in the stick frame, from +X towards +Z.

    Tilting by T moves a cheek hole from angle a to a - T. Using the two cheek
    holes on alternate steps keeps neighbouring tongue holes 30 degrees apart, so
    they do not run into each other at this radius.
    """
    return sorted({index_pin_angle(t) - t for t in tilt_positions()})


def polar_xz(radius, angle_deg):
    return radius * cos(radians(angle_deg)), radius * sin(radians(angle_deg))


def collar_layout():
    """Collar outside radius and the pivot's distance from the pole axis."""
    collar_r = (STICK_OD + STICK_FIT) / 2 + COLLAR_WALL
    return collar_r, collar_r + JOINT_R + 1.5


def make_collar():
    """Split clamp for the pole with the tilt joint's tongue, built about its own centre.

    Tongue forward (+X), clamp ears and slit to the rear (-X), two M3 pinch screws.
    """
    collar_r, pivot_x = collar_layout()
    bore_r = (STICK_OD + STICK_FIT) / 2
    h = CAM_COLLAR_H

    # straight bar as tall as the collar, ending in the joint disc: flat top and bottom, so it prints upright
    root_x = collar_r - 3
    tongue = Pos((root_x + pivot_x) / 2, 0) * Rectangle(pivot_x - root_x, h) + Pos(pivot_x, 0) * Circle(JOINT_R)
    tongue -= Pos(pivot_x, 0) * Circle(PIVOT_BOLT_D / 2)
    for angle in tongue_hole_angles():
        x, z = polar_xz(INDEX_R, angle)
        tongue -= Pos(pivot_x + x, z) * Circle(INDEX_D / 2)

    ear_x0, ear_x1 = collar_r - 4, collar_r + 14
    ears = Pos(-(ear_x0 + ear_x1) / 2, 0, 0) * Box(ear_x1 - ear_x0, 18, h)
    ears = fillet(ears.edges().filter_by(Axis.Z), 3)

    collar = Cylinder(collar_r, h) + ears + extrude(Plane.XZ * tongue, TONGUE_T / 2, both=True)
    collar -= Cylinder(bore_r, h + 2)
    collar -= box(-ear_x1 - 1, 0, -SLIT / 2, SLIT / 2, -h / 2 - 1, h / 2 + 1)
    bolt_x = -(collar_r + 7)
    for z in (-h / 4, h / 4):
        collar -= Pos(bolt_x, 0, z) * Rot(90, 0, 0) * Cylinder(CLAMP_BOLT_D / 2, 30)
        collar -= Pos(bolt_x, -9 + 3.5, z) * hex_pocket(CLAMP_NUT_AF, 3.5)
    return collar


def collar_location():
    return Pos(0, 0, CAM_COLLAR_Z)


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def cradle_layout():
    """Cradle dimensions in the pivot frame: pivot axis is Y through the origin,
    phone long axis is +Z and its screen faces -X (tilt 0 matches the handle frame)."""
    if PHONE_ORIENTATION != "portrait":
        raise NotImplementedError("only PHONE_ORIENTATION = 'portrait' is modelled")
    screen_x = JOINT_R + 1.0 + FRONT_BAR_T
    back_x = screen_x + PHONE_T + PHONE_FIT
    pocket_w = PHONE_W + PHONE_FIT
    bottom_z = -(FRONT_LIP_H - SHELF_T) / 2  # centres the front bar on the pivot
    back_h = min(BACK_H, PHONE_H - CAM_KEEPOUT_H - 5)
    return screen_x, back_x, pocket_w, bottom_z, back_h


def make_cradle():
    screen_x, back_x, pocket_w, bottom_z, back_h = cradle_layout()
    half_w = pocket_w / 2 + CRADLE_WALL
    floor_z = bottom_z - SHELF_T
    bar_x = screen_x - FRONT_BAR_T
    bar_top = bottom_z + FRONT_LIP_H
    plate_x1 = back_x + BACK_T

    body = box(back_x, plate_x1, -half_w, half_w, floor_z, bottom_z + back_h)  # back plate
    body += box(bar_x, screen_x, -half_w, half_w, floor_z, bar_top)  # front bar and bottom lip
    for side in (1, -1):
        y_in, y_out = sorted((side * pocket_w / 2, side * half_w))
        lip_in, lip_out = sorted((side * (pocket_w / 2 - LIP_OVER), side * half_w))
        foot_in, foot_out = sorted((side * PORT_KEEPOUT_W / 2, side * half_w))
        body += box(screen_x - LIP_T, back_x, y_in, y_out, bottom_z, bottom_z + SIDE_H)  # side wall
        body += box(screen_x - LIP_T, screen_x, lip_in, lip_out, bottom_z, bottom_z + SIDE_H)  # lip
        body += box(screen_x, back_x, foot_in, foot_out, floor_z, bottom_z)  # shelf foot

    # round the tops of the lips and the bottom lip: a square bar minus a cylinder
    for x0, top in ((screen_x - LIP_T, bottom_z + SIDE_H), (bar_x, bar_top)):
        corner = box(x0 - 1, x0 + EDGE_R, -half_w - 1, half_w + 1, top - EDGE_R, top + 1)
        corner -= Pos(x0 + EDGE_R, 0, top - EDGE_R) * Rot(90, 0, 0) * Cylinder(EDGE_R, 2 * half_w + 4)
        body -= corner

    # one rounded outline for everything seen from the front
    total_h = back_h + SHELF_T
    outline = Pos(0, floor_z + total_h / 2) * RectangleRounded(2 * half_w, total_h, CRADLE_R)
    body &= extrude(Plane.YZ.offset(bar_x - 1) * outline, plate_x1 - bar_x + 2)

    # push-out window in the back plate
    window = Pos(0, bottom_z + back_h * 0.55) * RectangleRounded(pocket_w * 0.42, back_h * 0.4, CRADLE_R)
    body -= extrude(Plane.YZ.offset(back_x - 1) * window, BACK_T + 2)

    # strap guide notches in both plate edges
    strap_z = bottom_z + STRAP_Z
    for side in (1, -1):
        y0, y1 = sorted((side * (half_w - STRAP_NOTCH), side * (half_w + 1)))
        body -= box(back_x - 0.01, plate_x1 + 1, y0, y1, strap_z - STRAP_W / 2 - 1, strap_z + STRAP_W / 2 + 1)

    # clevis cheeks around the collar's tongue
    bar_mid = (floor_z + bar_top) / 2
    cheek = make_hull((Circle(JOINT_R - 0.5) + Pos(bar_x + 1, bar_mid) * Rectangle(2, bar_top - floor_z)).edges())
    clevis_w = TONGUE_T + JOINT_GAP + 2 * CHEEK_T
    cheeks = extrude(Plane.XZ * cheek, clevis_w / 2, both=True)
    gap = (TONGUE_T + JOINT_GAP) / 2
    cheeks -= box(-JOINT_R - 1, bar_x, -gap, gap, -JOINT_R - 1, JOINT_R + 1)
    body += cheeks

    across = Rot(90, 0, 0)
    body -= across * Cylinder(PIVOT_BOLT_D / 2, clevis_w + 2)
    body -= Pos(0, -clevis_w / 2 + PIVOT_NUT_DEPTH, 0) * hex_pocket(PIVOT_NUT_AF, PIVOT_NUT_DEPTH + 1)
    for angle in INDEX_PIN_ANGLES:
        x, z = polar_xz(INDEX_R, angle)
        body -= Pos(x, 0, z) * across * Cylinder(INDEX_D / 2, clevis_w + 2)
        body -= Pos(x, -clevis_w / 2 + INDEX_NUT_DEPTH, z) * hex_pocket(INDEX_NUT_AF, INDEX_NUT_DEPTH + 1)

    # tether eyelet under the back plate, clear of the port gap
    lug_r = TETHER_HOLE_D / 2 + 3
    lug_y = half_w - CRADLE_R - lug_r
    lug_x = (back_x + plate_x1) / 2
    along_x = Rot(0, 90, 0)
    body += Pos(lug_x, lug_y, floor_z - 2) * along_x * Cylinder(lug_r, BACK_T)
    body += box(back_x, plate_x1, lug_y - lug_r, lug_y + lug_r, floor_z - 2, floor_z + 1)
    body -= Pos(lug_x, lug_y, floor_z - 2) * along_x * Cylinder(TETHER_HOLE_D / 2, BACK_T + 2)
    return body


def make_cradle_fit_test():
    """Bottom slice of the cradle: checks the phone's width and thickness in the
    channel, and the tilt joint against the printed collar."""
    _, back_x, pocket_w, bottom_z, _ = cradle_layout()
    half_w = pocket_w / 2 + CRADLE_WALL
    return make_cradle() & box(-JOINT_R - 2, back_x + BACK_T + 1, -half_w - 1, half_w + 1, -JOINT_R - 2, bottom_z + 14)


def cradle_location(tilt=PHONE_TILT_DEG):
    """Moves anything built in the pivot frame onto the collar at the given tilt."""
    return Pos(collar_layout()[1], 0, CAM_COLLAR_Z) * Rot(0, tilt, 0)


# ---------------------------------------------------------------------------
# Reference geometry: never exported for printing
# ---------------------------------------------------------------------------


def ref_phone():
    """Phone with case and camera bump, in the pivot frame."""
    screen_x, _, _, bottom_z, _ = cradle_layout()
    x0 = screen_x + PHONE_FIT / 2
    body = box(x0, x0 + PHONE_T, -PHONE_W / 2, PHONE_W / 2, bottom_z, bottom_z + PHONE_H)
    return body + box(x0 + PHONE_T, x0 + PHONE_T + CAM_BUMP_T, *camera_rect())


def camera_rect():
    """Camera bump outline on the phone's back: y0, y1, z0, z1 in the pivot frame."""
    bottom_z = cradle_layout()[3]
    y1 = PHONE_W / 2 - CAM_BUMP_FROM_SIDE
    z1 = bottom_z + PHONE_H - CAM_BUMP_FROM_TOP
    return y1 - CAM_BUMP_W, y1, z1 - CAM_BUMP_H, z1


def ref_camera_view(length=200.0):
    """Volume the cameras look through, widening at CAM_FOV_HALF_DEG, pivot frame."""
    screen_x = cradle_layout()[0]
    x0 = screen_x + PHONE_FIT / 2 + PHONE_T + CAM_BUMP_T
    y0, y1, z0, z1 = camera_rect()
    grow = 2 * length * sin(radians(CAM_FOV_HALF_DEG)) / cos(radians(CAM_FOV_HALF_DEG))
    centre = Pos((y0 + y1) / 2, (z0 + z1) / 2)
    near = Plane.YZ.offset(x0 + 0.05) * centre * Rectangle(y1 - y0, z1 - z0)
    far = Plane.YZ.offset(x0 + length) * centre * Rectangle(y1 - y0 + grow, z1 - z0 + grow)
    return loft([near, far])


def ref_stick(length=360.0):
    return Pos(0, 0, -length / 2) * (Cylinder(STICK_OD / 2, length) - Cylinder(STICK_ID / 2, length))


def ref_hand():
    """Space a gripping hand needs: the grip grown by HAND_CLEARANCE all round."""
    path = grip_path()
    u_front = path_param_at_x(SOCKET_OD / 2 + 6)  # the hand ends just ahead of the pole; the nose beyond is the thumb's
    sub = Spline(*[path @ (0.1 + (u_front - 0.1) * i / 6) for i in range(7)])
    section = Plane(origin=sub @ 0, x_dir=(0, 1, 0), z_dir=sub % 0) * Ellipse(
        GRIP_W / 2 + HAND_CLEARANCE, GRIP_H / 2 + HAND_CLEARANCE
    )
    return grip_location() * sweep(section, sub)


def ref_button():
    """12 mm panel-mount push button in the nose: head on the flat, threaded body through the hole."""
    seat_z = GRIP_H / 2 - BUTTON_SEAT_DROP
    head = Pos(0, 0, seat_z + BUTTON_HEAD_H / 2) * Cylinder(BUTTON_HEAD_D / 2, BUTTON_HEAD_H)
    body = Pos(0, 0, seat_z - BUTTON_BODY_LEN / 2) * Cylinder(BUTTON_HOLE_D / 2 - 0.3, BUTTON_BODY_LEN)
    nut = Pos(0, 0, seat_z - BUTTON_PANEL_T - 1.5) * (Cylinder(8.0, 3.0) - Cylinder(BUTTON_HOLE_D / 2 - 0.2, 4.0))
    return button_location() * (head + body + nut)


def ref_strap():
    """Strap band around phone and back plate, pivot frame."""
    screen_x, back_x, pocket_w, bottom_z, _ = cradle_layout()
    half_w = pocket_w / 2 + CRADLE_WALL - STRAP_NOTCH
    z0, z1 = bottom_z + STRAP_Z - STRAP_W / 2, bottom_z + STRAP_Z + STRAP_W / 2
    outer = box(screen_x - STRAP_T, back_x + BACK_T + STRAP_T, -half_w - STRAP_T, half_w + STRAP_T, z0, z1)
    return outer - box(screen_x, back_x + BACK_T, -half_w, half_w, z0 - 1, z1 + 1)


def ref_bolt(d, length, head_d, head_h):
    """Socket-head screw along Y: head on the +Y side, under-head face at y=0."""
    across = Rot(90, 0, 0)
    return Pos(0, -length / 2, 0) * across * Cylinder(d / 2, length) + Pos(0, head_h / 2, 0) * across * Cylinder(
        head_d / 2, head_h
    )


def ref_nut(across_flats, height, d):
    """Nut on a screw along Y: top face at y=0, body towards -Y."""
    return hex_pocket(across_flats, height) - Rot(90, 0, 0) * Cylinder(d / 2 + 0.05, 3 * height)


def ref_hardware(tilt=PHONE_TILT_DEG):
    """Screws and nuts as plain shapes in the stick frame: pivot, index pin, collar clamp."""
    collar_r, pivot_x = collar_layout()
    clevis_w = TONGUE_T + JOINT_GAP + 2 * CHEEK_T
    x, z = polar_xz(INDEX_R, index_pin_angle(tilt) - tilt)
    at_pivot = Pos(pivot_x, 0, CAM_COLLAR_Z)
    parts = [
        at_pivot * Pos(0, clevis_w / 2, 0) * ref_bolt(3, 20, 5.5, 3),
        at_pivot * Pos(0, -clevis_w / 2 + PIVOT_NUT_DEPTH, 0) * ref_nut(5.5, 2.4, 3),
        at_pivot * Pos(x, clevis_w / 2, z) * ref_bolt(3, 20, 5.5, 3),
        at_pivot * Pos(x, -clevis_w / 2 + INDEX_NUT_DEPTH, z) * ref_nut(5.5, 2.4, 3),
    ]
    for dz in (-CAM_COLLAR_H / 4, CAM_COLLAR_H / 4):
        parts.append(Pos(-(collar_r + 7), 9, CAM_COLLAR_Z + dz) * ref_bolt(3, 20, 5.5, 3))
        parts.append(Pos(-(collar_r + 7), -9 + 3.5, CAM_COLLAR_Z + dz) * ref_nut(5.5, 2.4, 3))
    return parts


def mount_layout():
    """Key positions shared by the mount and anything drawn around it."""
    axle_z = -(CUP_FLOOR + WHEEL_CLEARANCE + WHEEL_D / 2)
    plate_inner_x = -(WHEEL_W / 2 + WHEEL_GAP)  # face nearest the wheel
    return axle_z, axle_z + SHAFT_OFFSET, plate_inner_x


def make_motor_mount():
    axle_z, motor_z, plate_inner_x = mount_layout()
    plate_x = plate_inner_x - PLATE_T / 2
    bore_r = (STICK_OD + STICK_FIT) / 2
    collar_r = bore_r + COLLAR_WALL

    plate_bottom = motor_z - MOTOR_D / 2 - 4
    plate_h = COLLAR_H - plate_bottom
    plate = Pos(plate_x, 0, plate_bottom + plate_h / 2) * Box(PLATE_T, PLATE_W, plate_h)
    plate = fillet(plate.edges().filter_by(Axis.X).group_by(Axis.Z)[0], 14)

    cup_h = COLLAR_H + CUP_FLOOR
    cup_z = -CUP_FLOOR + cup_h / 2
    collar = Pos(0, 0, cup_z) * Cylinder(collar_r, cup_h)
    web_len = -(plate_inner_x - PLATE_T)
    web = Pos(-web_len / 2, 0, cup_z) * Box(web_len, collar_r * 2, cup_h)

    ear_x0, ear_x1 = collar_r - 4, collar_r + 14
    ear_z0, ear_z1 = 4.0, COLLAR_H - 4
    ears = Pos((ear_x0 + ear_x1) / 2, 0, (ear_z0 + ear_z1) / 2) * Box(ear_x1 - ear_x0, 18, ear_z1 - ear_z0)

    mount = plate + collar + web + ears

    # stick pocket, clamp slit and pinch bolts
    mount -= Pos(0, 0, COLLAR_H / 2 + 0.5) * Cylinder(bore_r, COLLAR_H + 1)
    mount -= Pos(ear_x1 / 2 + 1, 0, COLLAR_H / 2 + 0.5) * Box(ear_x1 + 2, SLIT, COLLAR_H + 1)
    bolt_x = collar_r + 6
    for z in (ear_z0 + 9, ear_z1 - 9):
        mount -= Pos(bolt_x, 0, z) * Rot(90, 0, 0) * Cylinder(CLAMP_BOLT_D / 2, 30)
        mount -= Pos(bolt_x, -9 + 3.5, z) * hex_pocket(CLAMP_NUT_AF, 3.5)

    # motor face: shaft boss clearance plus the bolt circle around the gearbox centre
    along_x = Rot(0, 90, 0)
    mount -= Pos(plate_x, 0, axle_z) * along_x * Cylinder(SHAFT_BOSS_D / 2, PLATE_T + 2)
    for loc in PolarLocations(MOTOR_BOLT_CIRCLE / 2, MOTOR_BOLTS, start_angle=30):
        y, z = loc.position.X, loc.position.Y + motor_z
        mount -= Pos(plate_x, y, z) * along_x * Cylinder(MOTOR_BOLT_D / 2, PLATE_T + 2)
        head_x = plate_inner_x - MOTOR_HEAD_DEPTH / 2 + 0.01
        mount -= Pos(head_x, y, z) * along_x * Cylinder(MOTOR_HEAD_D / 2, MOTOR_HEAD_DEPTH)
    return mount


# rotation that lays each part on the bed the way it should be printed
PRINT_ROTATIONS = {
    "stick_handle": (90, 0, 0),  # on its side, layers running along the grip
    "camera_collar": (0, 0, 0),  # upright, bore vertical
    "phone_cradle": (0, 90, 0),  # back plate on the bed
    "cradle_fit_test": (0, 90, 0),
    "handle_fit_test": (180, 0, 0),  # closed end down, socket mouth up
    "motor_mount": (0, -90, 0),  # motor plate on the bed
}


def as_printed(name, part):
    turned = Rot(*PRINT_ROTATIONS[name]) * part
    return Pos(0, 0, -turned.bounding_box().min.Z) * turned


def printable_parts():
    return {
        "stick_handle": make_handle(),
        "camera_collar": make_collar(),
        "phone_cradle": make_cradle(),
        "cradle_fit_test": make_cradle_fit_test(),
        "handle_fit_test": make_fit_test(),
        "motor_mount": make_motor_mount(),
    }


def overlap(a, b):
    """Shared volume of two shapes in mm3."""
    common = a & b
    return sum(solid.volume for solid in common.solids()) if common else 0.0


def run_checks(parts):
    """Geometric checks only. A valid, non-colliding solid says nothing about strength."""
    ok = True

    def report(passed, text):
        nonlocal ok
        ok &= bool(passed)
        print(f"  [{'ok' if passed else 'FAIL'}] {text}")

    print("solids")
    for name, part in parts.items():
        bb = part.bounding_box().size
        report(
            part.is_valid and len(part.solids()) == 1,
            f"{name}: {bb.X:.1f} x {bb.Y:.1f} x {bb.Z:.1f} mm, {part.volume / 1000:.1f} cm3, "
            f"valid={part.is_valid}, solids={len(part.solids())}",
        )

    handle, cradle = parts["stick_handle"], parts["phone_cradle"]
    collar = collar_location() * parts["camera_collar"]
    stick, hand, phone, view = ref_stick(), ref_hand(), ref_phone(), ref_camera_view()
    collar_r, pivot_x = collar_layout()

    print("thumb button")
    cut = button_location() * button_cut()
    socket_len = SOCKET_DEPTH + GRIP_PATH[2][2]
    socket = Pos(0, 0, GRIP_PATH[2][2] - socket_len / 2) * Cylinder(SOCKET_OD / 2, socket_len)
    report(overlap(cut, socket) < 1e-6, f"everything cut for the button stays {cut.distance_to(socket):.1f} mm clear of the pole socket, so the socket's wall is untouched")
    blank_socket = cut_tube_socket(socket, SOCKET_DEPTH, set_screw_z=-SOCKET_DEPTH / 2)
    lost = overlap(blank_socket, socket) - overlap(handle, socket)
    report(abs(lost) < 0.5, f"the socket in the finished handle has all its plastic ({lost:+.2f} mm3 against a plain socket)")
    button = ref_button()
    report(overlap(button, handle) < 1e-6, "a 12 mm button with its nut sits in the hole, flat and pocket without collision")
    top = (button_location() * Pos(0, 0, GRIP_H / 2)).position
    print(f"  button is {BUTTON_FROM_POLE:.0f} mm ahead of the pole axis along the grip; its top is at x={top.X:.0f}, z={top.Z:.0f} in the stick frame")

    print("keep-outs (from the parameters)")
    _, _, _, _, back_h = cradle_layout()
    report(back_h <= PHONE_H - CAM_KEEPOUT_H, f"back plate top {back_h:.0f} is below the camera band at {PHONE_H - CAM_KEEPOUT_H:.0f}")
    report(SIDE_H <= BUTTON_KEEPOUT[0], f"side walls stop at {SIDE_H:.0f}, buttons start at {BUTTON_KEEPOUT[0]:.0f}")
    strap = (STRAP_Z - STRAP_W / 2, STRAP_Z + STRAP_W / 2)
    report(SIDE_H <= strap[0] and strap[1] <= min(BUTTON_KEEPOUT[0], back_h), f"strap band {strap[0]:.0f}-{strap[1]:.0f} sits between side walls and buttons")
    holes = tongue_hole_angles()
    pitch = min(2 * INDEX_R * sin(radians((b - a) / 2)) for a, b in zip(holes, holes[1:]))
    report(pitch - INDEX_D >= 1.2, f"tongue index holes at {holes} deg, {pitch - INDEX_D:.2f} mm of plastic between neighbours")

    print("fixed parts")
    report(overlap(collar, stick) < 1e-6, "collar bore clears the tube")
    report(overlap(collar, handle) < 1e-6 and overlap(collar, hand) < 1e-6, f"collar is {collar.distance_to(hand):.0f} mm below the hand envelope")
    for lift in range(0, int(SIDE_H) + 21, 10):
        if overlap(Pos(0, 0, lift) * phone, cradle) > 1e-6:
            report(False, f"phone collides with the cradle when lifted {lift} mm")
            break
    else:
        report(True, f"phone slides straight up and out of the cradle (checked every 10 mm to {lift} mm)")
    report(overlap(view, cradle) < 1e-6, f"camera view volume ({CAM_FOV_HALF_DEG:.0f} deg half angle) misses the cradle")

    print("each tilt step")
    tool = Rot(90, 0, 0) * Cylinder(4.5, 120)
    clevis_w = TONGUE_T + JOINT_GAP + 2 * CHEEK_T
    for tilt in tilt_positions():
        loc = cradle_location(tilt)
        c, p, v = loc * cradle, loc * phone, loc * view
        hits = {}
        for a_name, a in (("cradle", c), ("phone", p), ("view", v)):
            for b_name, b in (("collar", collar), ("handle", handle), ("tube", stick), ("hand", hand)):
                hits[f"{a_name}/{b_name}"] = overlap(a, b)
        # the index pin must line up with a hole in the tongue
        x, z = polar_xz(INDEX_R, index_pin_angle(tilt))
        pin = loc * Pos(x, 0, z) * Rot(90, 0, 0) * Cylinder(INDEX_D / 2 - 0.05, 30)
        hits["index pin/collar"] = overlap(pin, collar)
        # a straight tool must reach every screw head and nut from the side
        for side in (1, -1):
            reach = Pos(0, side * (clevis_w / 2 + 61), 0) * tool
            hits[f"tool/pivot {side:+d}"] = overlap(Pos(pivot_x, 0, CAM_COLLAR_Z) * reach, c + p + stick)
            hits[f"tool/pin {side:+d}"] = overlap(loc * Pos(x, 0, z) * reach, c + p + stick)
            for dz in (-CAM_COLLAR_H / 4, CAM_COLLAR_H / 4):
                clear = Pos(-(collar_r + 7), side * 70, CAM_COLLAR_Z + dz) * tool
                hits[f"tool/clamp {dz:+.0f} {side:+d}"] = overlap(clear, c + p)
        bad = {k: round(val, 1) for k, val in hits.items() if val > 1e-6}
        gap = min(c.distance_to(hand), p.distance_to(hand), c.distance_to(handle), p.distance_to(handle))
        report(not bad, f"tilt {tilt:2d}: {'no collisions' if not bad else bad}; phone and cradle stay {gap:.0f} mm from the handle and hand envelope")

    print("estimates (calculated, not measured)")
    cg = cradle_location() * Pos(phone.center())
    lever = cg.position.X
    print(f"  phone centre is {lever:.0f} mm off the pole axis and {-cg.position.Z:.0f} mm below the tube top at tilt {PHONE_TILT_DEG:.0f}")
    print(f"  camera looks {PHONE_TILT_DEG - STICK_LEAN_DEG:.0f} deg below the horizon when the pole leans {STICK_LEAN_DEG:.0f} deg")
    return ok


if __name__ == "__main__":
    out = Path(__file__).parent / "export"
    out.mkdir(exist_ok=True)
    parts = printable_parts()
    passed = run_checks(parts)
    for name, part in parts.items():
        export_step(part, str(out / f"{name}.step"))
        export_stl(as_printed(name, part), str(out / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.1)

    placed = {
        "stick_handle": parts["stick_handle"],
        "camera_collar": collar_location() * parts["camera_collar"],
        "phone_cradle": cradle_location() * parts["phone_cradle"],
    }
    for name, part in placed.items():
        part.label = name
    export_step(Compound(label="handle_camera_mount", children=list(placed.values())), str(out / "assembly.step"))
    print(f"exported {len(parts)} parts and assembly.step to {out}")
    print("all geometric checks passed" if passed else "SOME CHECKS FAILED")

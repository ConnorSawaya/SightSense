"""Draws the wiring diagrams in this folder as standalone SVG files.

    python make_diagrams.py

The tables at the top hold the pins and the wire colours, and must match
../wiring.md and ../../pi/hardware.py. A colour can be changed there alone.
Moving a wire to another pin also needs its path in pi_to_driver() redrawn.
"""

from pathlib import Path

# Pi header pin, what the pin is, IBT-2 pin, wire colour on the team's cane
DRIVER_WIRES = [
    (12, "GPIO18", "R_EN", "brown"),
    (16, "GPIO23", "RPWM", "red"),
    (17, "3.3 V", "VCC", "black"),
    (18, "GPIO24", "LPWM", "orange"),
    (20, "Ground", "GND", "yellow"),
    (22, "GPIO25", "L_EN", "green"),
]
# Pi header pin, what the pin is, where it goes
SWITCH_WIRES = [
    (29, "GPIO5", "Left switch"),
    (31, "GPIO6", "Right switch"),
    (33, "GPIO13", "Centre switch"),
    (39, "Ground", "All 3 switches"),
]
# Pi header pin, what the pin is: the two leads of the talk button in the handle. Must match ../../pi/talk_button.py
BUTTON_WIRES = [
    (9, "Ground"),
    (11, "GPIO17"),
]
PIN_NAMES = {
    1: "3.3 V", 2: "5 V", 3: "GPIO2 (I2C data)", 4: "5 V", 5: "GPIO3 (I2C clock)",
    6: "Ground", 7: "GPIO4", 8: "GPIO14 (serial out)", 9: "Ground",
    10: "GPIO15 (serial in)", 11: "GPIO17", 12: "GPIO18", 13: "GPIO27", 14: "Ground",
    15: "GPIO22", 16: "GPIO23", 17: "3.3 V", 18: "GPIO24", 19: "GPIO10 (SPI)",
    20: "Ground", 21: "GPIO9 (SPI)", 22: "GPIO25", 23: "GPIO11 (SPI)", 24: "GPIO8 (SPI)",
    25: "Ground", 26: "GPIO7 (SPI)", 27: "GPIO0 (reserved)", 28: "GPIO1 (reserved)",
    29: "GPIO5", 30: "Ground", 31: "GPIO6", 32: "GPIO12", 33: "GPIO13", 34: "Ground",
    35: "GPIO19", 36: "GPIO16", 37: "GPIO26", 38: "GPIO20", 39: "Ground", 40: "GPIO21",
}
# The IBT-2's 2 x 4 header seen from above: top row, then the row at the board's edge.
DRIVER_HEADER = [["VCC", "R_IS", "R_EN", "RPWM"], ["GND", "L_IS", "L_EN", "LPWM"]]

WIRE = {"brown": "#A9743B", "red": "#E24B4A", "black": "#1B1B1B",
        "orange": "#F28C28", "yellow": "#F2C230", "green": "#1D9E75"}
DARK_TEXT_ON = {"orange", "yellow"}  # wire colours that need dark lettering

BG, CARD, EDGE = "#161616", "#1E1E1E", "#5F5E5A"
TEXT, MUTED, PIN = "#E8E6DF", "#B4B2A9", "#2C2C2A"
SWITCH, GROUND, PLUS12, USB5, MOTOR = "#7F77DD", "#888780", "#E24B4A", "#378ADD", "#D85A30"
BUTTON, BUTTON_PIN, BUTTON_EDGE = "#3BC9DB", "#0B5563", "#66D9E8"
FONT = "Segoe UI, Helvetica, Arial, sans-serif"

by_pin = {pin: colour for pin, _, _, colour in DRIVER_WIRES}
by_driver_pin = {name: colour for _, _, name, colour in DRIVER_WIRES}
switch_pins = {pin for pin, _, _ in SWITCH_WIRES}
button_pins = {pin for pin, _ in BUTTON_WIRES}


def text(x, y, s, size=12, fill=TEXT, anchor="middle", weight=400):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" dominant-baseline="central">{s}</text>')


def rect(x, y, w, h, fill=CARD, stroke=EDGE, rx=4, sw=1, extra=""):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}" {extra}/>')


def line(d, colour, width=2.5):
    """A wire. Black gets a pale outline so it shows on a dark background."""
    out = ""
    if colour == WIRE["black"]:
        out += f'<path d="{d}" fill="none" stroke="{MUTED}" stroke-width="{width + 2.5}" stroke-linejoin="round"/>'
    return out + f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="{width}" stroke-linejoin="round"/>'


def lettering(colour_name):
    return "#1B1B1B" if colour_name in DARK_TEXT_ON else "#FFFFFF"


def svg(width, height, title, desc, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" '
            f'height="{height}" role="img"><title>{title}</title><desc>{desc}</desc>'
            f'<rect width="{width}" height="{height}" fill="{BG}"/>' + "".join(body) + "</svg>\n")


def ibt2_board():
    """The IBT-2 from above, terminals at the top, header at the bottom right."""
    metal, chip = "#C8C9CC", "#2A2A2A"
    b = ['<rect x="140" y="30" width="400" height="290" rx="6" fill="#0E0E0E"/>',
         '<rect x="150" y="20" width="380" height="290" rx="10" fill="#163E6E" stroke="#3B7DCC"/>']
    for cx, cy, r in ((168, 40, 10), (514, 112, 9), (165, 284, 9), (514, 284, 9)):  # mounting holes
        b.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#E8E6DF"/><circle cx="{cx}" cy="{cy}" r="{r / 2}" fill="#0E0E0E"/>')
    b.append('<circle cx="215" cy="62" r="30" fill="#26282B"/><circle cx="215" cy="62" r="21" fill="#C4C7CC"/>')  # capacitor
    b.append('<rect x="262" y="30" width="236" height="58" rx="4" fill="#3FA34D" stroke="#2C7A37"/>')  # screw terminals
    for cx, name in zip((291.5, 350.5, 409.5, 468.5), ("B−", "B+", "M+", "M−")):
        b.append(f'<circle cx="{cx}" cy="52" r="13" fill="#D9DADC" stroke="#8D9096"/>'
                 f'<line x1="{cx - 8.5}" y1="52" x2="{cx + 8.5}" y2="52" stroke="#6B6E73" stroke-width="2"/>')
        b.append(text(cx, 104, name, 14, "#FFFFFF", weight=500))
    b += [text(321, 122, "Battery", fill="#B5D4F4"), text(439, 122, "Motor", fill="#B5D4F4"),
          text(186, 150, "IBT-2", 14, "#FFFFFF", "start", 500)]
    for x in (250, 332):  # the two BTS7960 chips and their legs
        b.append(f'<rect x="{x + 6}" y="140" width="60" height="12" fill="{metal}"/>'
                 f'<rect x="{x}" y="150" width="72" height="54" rx="2" fill="{chip}" stroke="#111111"/>')
        b += [f'<rect x="{x + 4 + 9.5 * k}" y="204" width="5" height="12" fill="{metal}"/>' for k in range(7)]
    for cx in (228, 426):  # screws holding the chips to the heatsink
        b.append(f'<circle cx="{cx}" cy="176" r="9" fill="#D9DADC" stroke="#8D9096"/>')
    b.append(f'<rect x="440" y="188" width="74" height="34" rx="2" fill="{chip}" stroke="#111111"/>')  # 74HC244
    b += [f'<rect x="{444 + 7 * k}" y="{y}" width="3" height="6" fill="{metal}"/>' for k in range(10) for y in (182, 222)]
    b += [f'<rect x="{262 + 13 * k}" y="226" width="9" height="10" fill="{metal}"/>' for k in range(7)]
    # the printed table, coloured to match the wire on each pin
    for r, row in enumerate(DRIVER_HEADER):
        for c, name in enumerate(row):
            x, y = 180 + 40 * c, 250 + 22 * r
            colour = by_driver_pin.get(name)
            if colour:
                b.append(f'<rect x="{x}" y="{y}" width="40" height="22" fill="{WIRE[colour]}"/>')
            b.append(text(x + 20, y + 11, name, fill=lettering(colour) if colour else "#FFFFFF"))
    b.append('<rect x="180" y="250" width="160" height="44" fill="none" stroke="#FFFFFF"/>'
             '<line x1="180" y1="272" x2="340" y2="272" stroke="#FFFFFF"/>')
    b += [f'<line x1="{x}" y1="250" x2="{x}" y2="294" stroke="#FFFFFF"/>' for x in (220, 260, 300)]
    b += [text(346, 261, "7", fill="#FFFFFF"), text(346, 283, "8", fill="#FFFFFF"),
          text(496, 261, "1", fill="#FFFFFF"), text(496, 283, "2", fill="#FFFFFF")]
    # the header itself
    b.append('<rect x="358" y="246" width="130" height="52" rx="3" fill="#111111"/>')
    for r, row in enumerate(DRIVER_HEADER):
        for c, name in enumerate(row):
            x, y = 362 + 34 * c, 250 + 26 * r
            colour = by_driver_pin.get(name)
            if colour:
                b.append(f'<rect x="{x}" y="{y}" width="20" height="18" rx="2" fill="{WIRE[colour]}" stroke="#FFFFFF" stroke-width="1.2"/>')
            else:
                b.append(f'<rect x="{x}" y="{y}" width="20" height="18" rx="2" fill="#3A3A3A"/>'
                         f'<rect x="{x + 6}" y="{y + 5}" width="8" height="8" fill="#C9A227"/>')
    return b


def pi_board(top, button=False):
    """The Pi 5 from above with the header along the top edge and the USB ports on the right."""
    b = [rect(60, top, 560, 330, CARD, EDGE, 12)]
    for i in range(20):
        for row, pin in ((0, 2 * i + 2), (1, 2 * i + 1)):
            x, y = 80 + 24 * i, top + 10 + 24 * row
            colour = by_pin.get(pin)
            if colour:
                b.append(rect(x, y, 22, 20, WIRE[colour], "#FFFFFF", 3, 1.2))
                b.append(text(x + 11, y + 10, pin, fill=lettering(colour)))
            elif button and pin in button_pins:
                b.append(rect(x, y, 22, 20, BUTTON_PIN, BUTTON_EDGE, 3, 1.6))
                b.append(text(x + 11, y + 10, pin, fill="#FFFFFF", weight=500))
            else:
                b.append(rect(x, y, 22, 20, PIN, EDGE, 3, 0.8))
                b.append(text(x + 11, y + 10, pin, fill="#D3D1C7"))
    for x, y, w, h, name in ((60, top + 130, 100, 30, "SD card slot"), (60, top + 230, 100, 30, "Power button"),
                             (100, top + 300, 100, 30, "USB-C power"), (220, top + 300, 60, 30, "HDMI"),
                             (300, top + 300, 60, 30, "HDMI"), (290, top + 140, 110, 80, "Processor"),
                             (540, top + 90, 80, 56, "USB 2"), (540, top + 158, 80, 56, "USB 3"),
                             (540, top + 226, 80, 56, "Ethernet")):
        b += [rect(x, y, w, h, "#444441", "#888780"), text(x + w / 2, y + h / 2, name, fill="#D3D1C7")]
    return b


def pi_to_driver():
    """The six wires between the Pi's header and the driver's header, in their real places."""
    hop = "A5 5 0 0 1"  # a small bump where one wire crosses another without joining it
    routes = {
        17: "M283 484 L283 496 L70 496 L70 326 L354 326 L354 259 L362 259",
        20: "M307 440 L307 390 L372 390 L372 294",
        22: "M331 440 L331 406 L440 406 L440 294",
        12: f"M211 440 L211 342 L367 342 {hop} 377 342 L423 342 L423 259 L430 259",
        16: f"M259 440 L259 358 L367 358 {hop} 377 358 L435 358 {hop} 445 358 L457 358 L457 259 L464 259",
        18: f"M283 440 L283 374 L367 374 {hop} 377 374 L435 374 {hop} 445 374 L474 374 L474 294",
    }
    b = ibt2_board() + pi_board(430) + [line(routes[pin], WIRE[by_pin[pin]]) for pin in routes]
    for i, (pin, _, name, colour) in enumerate(DRIVER_WIRES):
        x, y = 70 + 200 * (i % 3), 788 + 26 * (i // 3)
        b.append(rect(x, y - 6, 14, 12, WIRE[colour], "#FFFFFF" if colour != "black" else MUTED, 2))
        b.append(text(x + 22, y, f"{colour.capitalize()}: pin {pin} to {name}", anchor="start"))
    return svg(680, 840, "Raspberry Pi 5 to IBT-2 driver: the six wires",
               "Brown: Pi pin 12 to R_EN. Red: pin 16 to RPWM. Black: pin 17, 3.3 volts, to VCC. Orange: pin 18 to LPWM. "
               "Yellow: pin 20, ground, to GND. Green: pin 22 to L_EN. R_IS and L_IS stay empty.", b)


def full_wiring():
    """Everything on the cane: power, the six driver wires, the switches and the motor."""
    b = []
    for x, y, w, title, sub in ((40, 40, 190, "12 V to 5 V converter", "USB-C plug into the Pi"),
                                (270, 40, 150, "Green adapter", "+ and − screws"),
                                (460, 40, 180, "12 V battery", "Barrel plug")):
        b += [rect(x, y, w, 56, rx=8), text(x + w / 2, y + 19, title, 14, weight=500), text(x + w / 2, y + 38, sub, fill=MUTED)]
    b += [line(f"M{x1} 58 L{x2} 58", PLUS12, 3.5) + line(f"M{x1} 78 L{x2} 78", GROUND, 3.5) for x1, x2 in ((460, 420), (270, 230))]
    b.append(line("M135 96 L135 170", USB5, 3.5))
    b += [line("M395 96 L395 130 L430 130", PLUS12, 3.5), rect(430, 116, 80, 28, extra='stroke-dasharray="4 3"'), text(470, 130, "5 A fuse"),
          line("M510 130 L530 130", PLUS12, 3.5), rect(530, 116, 100, 28, extra='stroke-dasharray="4 3"'), text(580, 130, "Kill switch"),
          line("M630 130 L660 130 L660 225 L640 225", PLUS12, 3.5), line("M375 96 L375 156 L652 156 L652 250 L640 250", GROUND, 3.5)]
    b += [rect(40, 170, 190, 395, rx=8), text(105, 192, "Raspberry Pi 5", 14, weight=500),
          rect(450, 170, 190, 240, rx=8), text(545, 192, "IBT-2 driver", 14, weight=500)]
    for i, (pin, _, name, colour) in enumerate(DRIVER_WIRES):
        y = 225 + 25 * i
        b += [rect(170, y - 10, 60, 20, WIRE[colour], "#FFFFFF", 3), text(200, y, f"Pin {pin}", fill=lettering(colour)),
              rect(450, y - 10, 70, 20, WIRE[colour], "#FFFFFF", 3), text(485, y, name, fill=lettering(colour)),
              line(f"M230 {y} L450 {y}", WIRE[colour], 2)]
    for y, name in ((225, "B+"), (250, "B−"), (325, "M+"), (350, "M−")):
        b += [rect(585, y - 10, 55, 20, PIN), text(612, y, name)]
    for i, (pin, _, name) in enumerate(SWITCH_WIRES):
        y = 400 + 25 * i if i < 3 else 475
        b += [rect(170, y - 10, 60, 20, PIN), text(200, y, f"Pin {pin}")]
        if i < 3:
            b += [rect(280, y - 10, 130, 20, PIN, extra='stroke-dasharray="4 3"'), text(345, y, name), line(f"M230 {y} L280 {y}", SWITCH, 2),
                  line(f"M410 {y} L430 {y}", GROUND, 2)]
    b.append(line("M430 400 L430 475 L230 475", GROUND, 2))
    for (pin, _), y, colour in zip(reversed(BUTTON_WIRES), (520, 545), (BUTTON, GROUND)):
        b += [rect(170, y - 10, 60, 20, PIN), text(200, y, f"Pin {pin}"), line(f"M230 {y} L280 {y}", colour, 2)]
    b += [rect(280, 508, 130, 49, PIN, extra='stroke-dasharray="4 3"'), text(345, 525, "Talk button"),
          text(345, 542, "in the handle", 11, MUTED)]
    b += [rect(450, 450, 190, 56, rx=8), text(545, 478, "12 V gear motor", 14, weight=500),
          line("M640 325 L664 325 L664 485 L640 485", MOTOR, 3.5), line("M640 350 L652 350 L652 470 L640 470", MOTOR, 3.5)]
    key = [(PLUS12, "12 V positive (thick)"), (GROUND, "Negative or ground"), (USB5, "5 V USB-C"), (MOTOR, "Motor wires"),
           (SWITCH, "Switch signal"), (BUTTON, "Talk button signal"), (None, "Thin wires: real colours"),
           ("dash", "Dashed box: not fitted yet")]
    for i, (colour, label) in enumerate(key):
        x, y = 40 + 215 * (i % 3), 600 + 24 * (i // 3)
        if colour == "dash":
            b.append(rect(x, y - 7, 18, 14, CARD, EDGE, 3, extra='stroke-dasharray="4 3"'))
        elif colour:
            b.append(line(f"M{x} {y} L{x + 18} {y}", colour, 3.5))
        else:
            b += [line(f"M{x + 6 * k} {y - 6} L{x + 6 * k} {y + 6}", WIRE[c], 2.5) for k, c in enumerate(("brown", "orange", "green"))]
        b.append(text(x + 26, y, label, anchor="start"))
    return svg(680, 690, "Full wiring of the cane",
               "The 12 volt battery feeds the green screw adapter. One pair of wires goes to the 12 volt to 5 volt converter, whose "
               "USB-C plug powers the Raspberry Pi. The other goes through a 5 amp fuse and a kill switch to B plus and B minus on the "
               "IBT-2 driver. Six wires join the Pi's header to the driver, three limit switches go to Pi pins 29, 31 and 33 with their "
               "other legs on pin 39, the talk button in the handle goes to pins 11 and 9, and the driver's M plus and M minus "
               "go to the motor.", b)


def pi_pinout():
    """Every pin on the Pi's header, with the cane's wires marked."""
    b = [text(340, 26, "SD card end of the board", fill=MUTED), text(330, 48, "Inner row", fill=MUTED, anchor="end"),
         text(350, 48, "Edge row", fill=MUTED, anchor="start")]
    driver = {pin: (name, colour) for pin, _, name, colour in DRIVER_WIRES}
    switches = {pin: name for pin, _, name in SWITCH_WIRES}
    for pin in range(1, 41):
        y = 60 + 24 * ((pin - 1) // 2)
        label_x, pin_x = (40, 300) if pin % 2 else (390, 350)
        label, fill, edge, ink, weight = PIN_NAMES[pin], PIN, EDGE, "#D3D1C7", 400
        if pin in driver:
            name, colour = driver[pin]
            label, fill, edge, ink, weight = f"{label} · driver {name} · {colour}", WIRE[colour], "#FFFFFF", lettering(colour), 500
        elif pin in switches:
            label, fill, edge, ink, weight = f"{label} · {switches[pin].lower()}", "#3C3489", "#AFA9EC", "#FFFFFF", 500
        elif pin in button_pins:
            label, fill, edge, ink, weight = f"{label} · talk button", BUTTON_PIN, BUTTON_EDGE, "#FFFFFF", 500
        b += [rect(label_x, y, 250, 18, fill, edge, 3), rect(pin_x, y, 30, 18, fill, edge, 3),
              text(label_x + 125, y + 9, label, 12 if weight == 400 else 13, ink, weight=weight),
              text(pin_x + 15, y + 9, pin, 12 if weight == 400 else 13, ink, weight=weight)]
    b.append(text(340, 556, "USB ports end of the board", fill=MUTED))
    for x, y, fill, edge, label in ((60, 576, WIRE["orange"], "#FFFFFF", "Wire to the driver, in its colour"),
                                    (340, 576, "#3C3489", "#AFA9EC", "Wire to a limit switch"),
                                    (60, 598, BUTTON_PIN, BUTTON_EDGE, "Wire to the talk button"),
                                    (340, 598, PIN, EDGE, "Leave empty")):
        b += [rect(x, y, 14, 12, fill, edge, 2), text(x + 22, y + 6, label, anchor="start")]
    return svg(680, 628, "Raspberry Pi 5 header pins used by the cane",
               "All 40 header pins. The cane uses pin 12 for driver R_EN, 16 for RPWM, 17 for VCC, 18 for LPWM, 20 for GND, 22 for L_EN, "
               "29, 31 and 33 for the left, right and centre limit switches, 39 as the switches' ground, and 11 and 9 for the "
               "talk button. Pins 2 and 4 are 5 volts.", b)


def talk_button():
    """The talk button's two leads on the Pi's header."""
    top = 150
    b = pi_board(top, button=True)
    # the switch, seen from the side: cap, threaded neck, nut, body, two leads
    b += [rect(120, 26, 20, 12, "#D8484F", "#F09595", 3), rect(123, 38, 14, 10, "#C8C9CC", "#8D9096", 1),
          rect(112, 48, 36, 6, "#C8C9CC", "#8D9096", 1), rect(115, 54, 30, 32, "#2A2A2A", "#5F5E5A", 3)]
    b += [text(160, 34, "Talk button, in the handle", 14, anchor="start", weight=500),
          text(160, 54, "7 mm momentary push button with two leads", fill=MUTED, anchor="start"),
          text(160, 72, "Either lead can go to either pin", fill=MUTED, anchor="start")]
    ground_x, signal_x = (80 + 24 * ((pin - 1) // 2) + 11 for pin, _ in BUTTON_WIRES)
    foot = top + 54  # bottom edge of the inner row of pins
    b.append(line(f"M138 86 L138 124 L44 124 L44 {foot + 12} L{ground_x} {foot + 12} L{ground_x} {foot}", GROUND, 3))
    b.append(line(f"M122 86 L122 112 L32 112 L32 {foot + 26} L{signal_x} {foot + 26} L{signal_x} {foot}", BUTTON, 3))
    for y, colour, label in ((96, GROUND, f"One lead to pin {BUTTON_WIRES[0][0]}: ground"),
                             (118, BUTTON, f"The other lead to pin {BUTTON_WIRES[1][0]}: {BUTTON_WIRES[1][1]}")):
        b += [line(f"M400 {y} L424 {y}", colour, 3), text(432, y, label, anchor="start")]
    b += [text(240, top + 72, "Inner row, 5th and 6th pins from the SD card end.", anchor="start"),
          text(240, top + 90, "Pin 11 is directly beside the brown wire on pin 12.", anchor="start"),
          text(240, top + 108, "No resistor: the Pi supplies its own pull-up.", fill=MUTED, anchor="start")]
    b.append(text(340, top + 356, "Keep both leads off pins 1 and 17 (3.3 V) and pins 2 and 4 (5 V).", 13, PLUS12, weight=500))
    return svg(680, top + 380, "The talk button on the Raspberry Pi 5",
               "A momentary push button in the handle. One lead goes to header pin 9, which is ground. The other goes to header "
               "pin 11, which is GPIO17. Both are on the inner row, the fifth and sixth pins from the SD card end. Pin 11 is beside "
               "pin 12, which carries the brown driver wire. Neither lead may go on pin 1, 2, 4 or 17.", b)


if __name__ == "__main__":
    here = Path(__file__).parent
    for name, draw in (("pi-to-driver", pi_to_driver), ("full-wiring", full_wiring), ("pi-pinout", pi_pinout),
                       ("talk-button", talk_button)):
        (here / f"{name}.svg").write_text(draw(), encoding="utf-8", newline="\n")
        print("wrote", name + ".svg")

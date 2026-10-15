# Cane board: bill of materials

Everything needed to build the cane's electronics around the [cane board](README.md), and what the board lets you drop. The cane's tubes, printed parts and screws are unchanged and stay in [`../BOM.md`](../BOM.md).

Nothing here has been ordered. Order codes, prices, stock and JLCPCB's class for each part were read from JLCPCB's parts library on October 13, 2026, and will drift. Prices are US dollars for one piece, before shipping, duty and tax.

## What changes on the cane

| Item | Cane as built | With the cane board |
| --- | --- | --- |
| Raspberry Pi 5, cooler, case, microSD card | In use | Not needed: the ESP32-S3 on the board does the job |
| Converter, 12 V to 5 V | In use | Not needed: built into the board |
| Motor driver, IBT-2 | In use | Not needed: DRV8876 on the board |
| Barrel-to-screw adapter, six jumper wires | In use | Not needed: the battery plugs into the board |
| Battery, 12 V 3 Ah | In use | Keep |
| Gearmotor and omni wheel | In use | Keep. Solder the two motor wires to an XT30 plug; it plugs into the board |
| Talk button and its two wires | In use | Keep. Needs a 2-way JST XH plug on the board end |
| Kill switch | Not fitted | Buy: see section 4 |
| iPhone 16 Pro, ASUS Ascent GX10 | In use | Keep. The phone runs on its own battery |
| Electronics mount (printed) | Holds the Pi and battery | Has to be redrawn for the board |

## 1. On the board

<!-- fitted: written by make_board.py -->
82 parts on 40 lines. The 40 lines with a price come to $10.48 for one board at JLCPCB's price for one piece. 7 lines (9 parts) are through-hole and cost $3.07 of that. JLCPCB classes 23 lines as Basic and 3 as Preferred, which carry no fee; 7 surface-mount lines are Extended and carry its per-line fee.

| Qty | Ref | Part | Package | Maker's number | LCSC | JLCPCB class | Each | Line |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | U1 | ESP32-S3-WROOM-1-N4 | Module | ESP32-S3-WROOM-1-N4 | C2913197 | Extended | $4.130 | $4.13 |
| 1 | U2 | DRV8876PWPR | HTSSOP-16 | DRV8876PWPR | C575551 | Extended | $0.780 | $0.78 |
| 1 | U3 | K7805-1000R3 | Through-hole, 3 pins | K7805-1000R3 | C2992391 | Extended | $2.348 | $2.35 |
| 1 | U4 | AP2112K-3.3 | SOT-23-5 | AP2112K-3.3TRG1 | C51118 | Extended | $0.172 | $0.17 |
| 3 | Q1, Q4, Q2 | AO3401A | SOT-23 | AO3401A | C15127 | Basic | $0.102 | $0.31 |
| 1 | Q3 | AO3400A | SOT-23 | AO3400A | C20917 | Basic | $0.089 | $0.09 |
| 1 | D1 | Diode, SMBJ15A | SMB | SMBJ15A | C19077569 | Preferred | $0.055 | $0.06 |
| 1 | D4 | Diode, BAT54S | SOT-23 | BAT54S | C7420333 | Preferred | $0.014 | $0.01 |
| 3 | D5, D6, D7 | Diode, B5819W | SOD-123 | B5819W | C8598 | Basic | $0.028 | $0.08 |
| 2 | D8, D9 | Diode, H5VL10B | DFN1006 | H5VL10B | C7420372 | Preferred | $0.006 | $0.01 |
| 3 | LED1, LED2, LED3 | LED, Red | 0603 | KT-0603R | C2286 | Basic | $0.008 | $0.02 |
| 1 | F1 | Fuse, PTC 4A | 2920 | BSMD2920-400-30V | C20539726 | Extended | $0.226 | $0.23 |
| 1 | C1 | Capacitor, 220uF 25V | 8 x 10 mm can | EMK1EM221FB0D00R | C724620 | Extended | $0.114 | $0.11 |
| 4 | C3, C27, C13, C14 | Capacitor, 22uF 25V | 1206 | CL31A226KAHNNNE | C12891 | Basic | $0.128 | $0.51 |
| 1 | C6 | Capacitor, 22nF 50V | 0603 | CL10B223KB8NNNC | C21122 | Basic | $0.007 | $0.007 |
| 3 | C8, C9, C21 | Capacitor, 1uF 50V | 0603 | CL10A105KB8NNNC | C15849 | Basic | $0.016 | $0.05 |
| 1 | C10 | Capacitor, 10uF 50V | 1206 | CL31A106KBHNNNE | C13585 | Basic | $0.159 | $0.16 |
| 2 | C15, C16 | Capacitor, 10uF 25V | 0805 | CL21A106KAYNNNE | C15850 | Basic | $0.069 | $0.14 |
| 1 | C19 | Capacitor, 22uF 6.3V | 0603 | CL10A226MQ8NRNC | C59461 | Basic | $0.031 | $0.03 |
| 9 | C26, C4, C5, C7, C11, C20, C22, C23, C24 | Capacitor, 100nF 50V | 0603 | CC0603KRX7R9BB104 | C14663 | Basic | $0.014 | $0.13 |
| 6 | R1, R11, R12, R24, R26, R33 | Resistor, 1%, 100k | 0603 | 0603WAF1003T5E | C25803 | Basic | $0.003 | $0.02 |
| 8 | R2, R6, R7, R8, R9, R21, R22, R28 | Resistor, 1%, 10k | 0603 | 0603WAF1002T5E | C25804 | Basic | $0.005 | $0.04 |
| 1 | R3 | Resistor, 1%, 13k | 0603 | 0603WAF1302T5E | C22797 | Basic | $0.003 | $0.003 |
| 3 | R4, R30, R31 | Resistor, 1%, 4.7k | 0603 | 0603WAF4701T5E | C23162 | Basic | $0.003 | $0.008 |
| 1 | R5 | Resistor, 1%, 1.5k | 0603 | 0603WAF1501T5E | C22843 | Basic | $0.002 | $0.002 |
| 1 | R10 | Resistor, 1%, 220 | 0603 | 0603WAF2200T5E | C22962 | Basic | $0.004 | $0.004 |
| 3 | R14, R23, R29 | Resistor, 1%, 1k | 0603 | 0603WAF1001T5E | C21190 | Basic | $0.002 | $0.006 |
| 2 | R19, R20 | Resistor, 1%, 5.1k | 0603 | 0603WAF5101T5E | C23186 | Basic | $0.002 | $0.003 |
| 2 | R25, R27 | Resistor, 1%, 22k | 0603 | 0603WAF2202T5E | C31850 | Basic | $0.004 | $0.008 |
| 1 | R32 | Resistor, 1%, 100 | 0603 | 0603WAF1000T5E | C22775 | Basic | $0.003 | $0.003 |
| 1 | R34 | Resistor, 1%, 47k | 0603 | 0603WAF4702T5E | C25819 | Basic | $0.002 | $0.002 |
| 1 | J1 | Connector: 12V battery | Through-hole | DC-005-5A-2.0 | C381116 | Extended | $0.262 | $0.26 |
| 1 | J2 | Connector: Motor | Through-hole | XT30UPB-F30.G.Y | C108769 | Extended | $0.233 | $0.23 |
| 3 | J3, J4, J7 | Connector: Kill switch / Talk button / Buzzer motor | Through-hole | B2B-XH-A | C158012 | Extended | $0.041 | $0.12 |
| 1 | J5 | Connector: Encoder | Through-hole | B4B-XH-A | C144395 | Extended | $0.059 | $0.06 |
| 1 | J6 | Connector: I2C | Through-hole | PZ254V-11-04P | C2691448 | Extended | $0.028 | $0.03 |
| 1 | J8 | Connector: Serial | Through-hole | PZ254V-11-03P | C2937625 | Extended | $0.020 | $0.02 |
| 1 | J11 | Connector: Firmware | SMD | TYPE-C-31-M-12 | C165948 | Extended | $0.186 | $0.19 |
| 2 | SW1, SW2 | Switch: Reset / Boot | SMD, 5.1 mm square | TS-1187A-B-A-B | C318884 | Basic | $0.021 | $0.04 |
| 1 | SW3 | Switch: Power | SMD, side slider | MSK12C02 | C431540 | Extended | $0.057 | $0.06 |
<!-- end fitted -->

- This table is written by `make_board.py` from the same list that draws the schematic. `export/bom-jlcpcb.csv` holds the same lines in the columns JLCPCB's order form reads.
- Every resistor is 1%. Capacitors are X7R or X5R, except the 100 pF one, which is C0G.
- No part is needed for the four mounting holes or the solder jumper JP1.
- JLCPCB charges a fee for each Extended surface-mount line, and none for Basic or Preferred lines. Its FAQ says Preferred parts "are exempt from the Feeders Loading fee for Economic PCB assembly".

## 2. Pads on the board, parts not fitted

The 5 V socket for the phone. The pads stay on the board so it can be added later.

<!-- not fitted: written by make_board.py -->
| Qty | Ref | Part | Package | Maker's number | LCSC | JLCPCB class | Each | Line |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | U5 | TPS2069CDBVR | SOT-23-5 | TPS2069CDBVR | C181752 | Extended | $0.137 | $0.14 |
| 1 | C17 | Capacitor, 10uF 50V | 1206 | CL31A106KBHNNNE | C13585 | Basic | $0.159 | $0.16 |
| 1 | C18 | Capacitor, 22uF 25V | 1206 | CL31A226KAHNNNE | C12891 | Basic | $0.128 | $0.13 |
| 2 | R15, R16 | Resistor, 1%, 10k | 0603 | 0603WAF1002T5E | C25804 | Basic | $0.005 | $0.01 |
| 2 | R17, R18 | Resistor, 1%, 22k | 0603 | 0603WAF2202T5E | C31850 | Basic | $0.004 | $0.008 |
| 1 | J10 | Connector: Phone power | SMD | USB4125-GF-A | C3151650 | Extended | $1.039 | $1.04 |
<!-- end not fitted -->

## 3. How the cost was cut, and what it changed

The first parts list, earlier on October 13, had 16 fee-carrying lines and cost about $11 a board. The cut-down list had 9 and cost $8.49. On October 14 the converter built from parts was swapped for a ready-made module (last row): 7 fee-carrying lines and $10.48 a board. Each change below was checked against JLCPCB's library, but none has been built.

| Change | Saves, on five boards | What it costs in the design |
| --- | --- | --- |
| Three protection FETs are AO3401A (Basic) in place of two AO4407A, and their two zeners are gone | $6.14 in fees and $2.17 | They are smaller and run warmer. Two share the battery current. Their gates stand only 12 V, so resistors hold Q1 and Q4's gates at a third of the battery voltage and Q2's at 0.43 (10k and 13k since October 14, for a cooler kill switch); the two 12 V zeners are gone |
| TVS and the watchdog's diode pair are the Preferred versions of the same parts | $6.14 in fees and $0.10 | Nothing: same parts, other makers |
| One 220 µF can on the battery side in place of two cans; two 22 µF ceramics by the motor driver | $3.07 fee, less $0.98 | The motor supply now switches on and off in milliseconds, which also let the two slow-start capacitors go |
| Two single protection diodes (Preferred) on the USB data lines in place of the USBLC6 array | $3.07 fee and $0.82 | The USB supply line is no longer clamped. Each data line carries 15 pF, which full-speed USB allows |
| Battery jack is the XKB DC-005-5A-2.0 in place of the CUI PJ-102AH | $4.13 | Same 5 A rating and 2.0 mm pin. Its drawing was checked against KiCad's footprint: pins 5.9 mm apart on pads drawn 6.0 mm apart |
| Processor module with 4 MB of flash in place of 8 MB | $3.89 | Half the program space, which is still several times what this firmware needs |
| Smaller capacitors on the 5 V and 3.3 V rails | $1.38 | Lower voltage rating, on rails that never exceed 5.5 V |
| October 14: sealed YLPTEC K7805-1000R3 module in place of the TPS54302 converter, its inductor and six small parts | $6.14 in fees, but parts cost about $2 a board more | Its layout is done inside the module, which removes the board's hardest layout job. 1 A, so the phone socket can no longer be fitted without a bigger converter. Through-hole, soldered by JLCPCB |

Still Extended, because JLCPCB's library has no Basic or Preferred part of the kind: the processor module, the motor driver, the fuse, the 220 µF can, the USB-C socket and the slide switch. The 3.3 V regulator is also Extended; the only Basic one that is big enough, the AMS1117-3.3, needs 1.1 V of headroom. This board gives it 1.5 V on the battery, but only about 1.0 to 1.3 V on USB alone.

More that could be cut, not done:

- **Leave the power switch off the board:** $3.35. The board is then switched off by pulling the battery plug, as on the cane today.
- **Use the AMS1117-3.3 regulator anyway:** $2.89. It may sag when the board runs from USB alone.
- **Order more boards.** The fees are per order, so ten boards cost much less each than five.

## 4. Off the board

Keep from the cane as built: the 12 V 3 Ah battery, the gearmotor, the omni wheel, the talk button and its wires. See [`../BOM.md`](../BOM.md).

To buy. None of these was looked up, so no prices:

| Qty | Item | What to look for |
| --- | --- | --- |
| 1 | Kill switch | One that stays where it is put, with two terminals. Closed means the motor can run. It carries about 0.5 mA, so any small switch rated for 12 V will do. Mount it within reach of the hand |
| 2 | JST XH 2-way plug with wire leads | One for the kill switch, one for the talk button |
| 1 | 100 nF ceramic capacitor, 50 V, through-hole | Solder it straight across the motor's two terminals, at the motor, under the same solder as the leads. It takes the brush noise out before it reaches the wire. Any 0.1 µF ceramic rated 50 V or more |
| 1 | JST XH 2-way plug with leads, and a 3 V coin buzzer motor | Only if the handle buzzer is wanted |
| 1 | JST XH 4-way plug with leads, and an encoder for the motor | Only if wheel speed is to be measured |
| 4 | M3 screws, M3 nuts and 5 mm nylon spacers | Mount the board on its four 3.2 mm holes (two below the processor, two at the motor-end corners). Nylon keeps metal away from the aerial and off the carbon tube |

## 5. Bench test, before any board is ordered

| Item | Price | State on October 13 |
| --- | --- | --- |
| Pololu DRV8876 motor driver carrier, item 4036 | $8.15 | In stock at Pololu. Brings out the current reading, VREF, nSLEEP, nFAULT and PMODE. Its current-sense resistor is 2.49 kΩ, not the board's 1.5 kΩ |
| ESP32-S3 development board | About $15 to $20 | The DevKitC-1-N8 is listed as obsolete at Mouser and no longer stocked at Adafruit; DigiKey was not checked. The N8R8 version is $15.00 at Mouser, on back order until December 7, and $19.95 at Adafruit, out of stock. Any ESP32-S3 board will do for the test |

## 6. Having five boards made

JLCPCB's economic assembly, from its price page on October 13, 2026, for the board as it stands on October 14: 4 layers, black, all parts on the top side.

| Item | Cost |
| --- | --- |
| Five bare boards, 4 layers, black (quoted at 40 × 100 mm) | $16.00 |
| Set-up $8.18 and stencil $1.53 | $9.71 |
| Fee for Extended parts: 7 surface-mount lines at $3.07 | $21.49 |
| Surface-mount soldering: about 260 joints a board at $0.0016 | $2.08 |
| Through-hole soldering: $3.58 an order and about 25 joints a board at $0.0164 | $5.63 |
| Parts: five boards at $10.48 | $52.40 |
| **Total before shipping, duty and tax** | **$107.31** |

- With the 35% tariff and $26.64 UPS shipping that is about $172, or $34 a board. See [`COST.md`](COST.md).
- JLCPCB's pages do not say whether the through-hole lines also pay the Extended fee. The fee is for loading a part onto the placing machine and these are soldered by hand, so I have not counted it. If it does apply, add $3.07 a line.
- Joint counts are estimates.
- JLCPCB will assemble as few as two boards.

## Notes on the parts

- **Stock.** Every line was in stock in JLCPCB's library on October 13. The thinnest were the processor module (2,543) and the Preferred TVS (8,094). The 5 V module and the XT30 socket were found in JLCPCB's library on October 14; recheck stock on the day. Rechecked on LCSC the evening of October 14: the processor module 2,222, the motor driver 29,627, the 5 V module 9,427 (now $1.37 there), the XT30 43,520, the 220 µF can 21,915.
- **Motor socket, J2.** AMASS XT30UPB-F, upright, rated 15 A continuous. Its footprint is KiCad's own for that exact part.
- **Fuse, F1.** Holds 4 A at 25 °C, 3.4 A at 40 °C and 2.7 A at 60 °C, and trips at 8 A. The board's worst case is about 2.5 A, with the motor at its 2.2 A limit.
- **Battery jack, J1.** 2.0 mm pin, for a 5.5 mm plug. Measure the pack's plug first: the same jack comes with a 2.5 mm pin as C381115.
- **Lights.** All three are red. Green and blue ones need about 3.1 to 3.3 V and would barely light from the 3.3 V rail.
- **Slide switch, SW3.** Rated 50 mA at 12 V. It only pulls the 3.3 V regulator's enable pin to ground, which is microamps. The 5 V module stays on while the battery is plugged in, drawing a few milliamps (not measured).

## Where the prices come from

- Part codes, prices, stock and class: JLCPCB's parts library, asked for each code in the tables on October 13, 2026. The same codes order the parts loose from LCSC, at slightly different prices.
- The fee rule for Preferred parts: <https://jlcpcb.com/help/article/pcb-assembly-faqs>.
- Assembly fees: <https://jlcpcb.com/help/article/pcb-assembly-price> and <https://jlcpcb.com/capabilities/pcb-assembly-capabilities>.
- Bare-board price: JLCPCB's online quote for FR-4, 1.6 mm, green, leaded HASL.
- The battery jack's drawing: XKB's datasheet for the DC-005-5A-2.0, from LCSC's page for C381116.
- Bench-test items: <https://www.pololu.com/product/4036>, <https://www.adafruit.com/product/5312>, <https://www.adafruit.com/product/5336> and Mouser's listing for the ESP32-S3-DevKitC-1.

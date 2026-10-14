# Cane board: potential problems

What could make the board fail, what has been checked, and what is still open. Written October 14, 2026, for the routed 46 × 100 mm, 4-layer board in commit `c1d0e60`. Nothing has been built.

Severity: **High** means the board may not work or may be damaged; **Medium** means it may work badly or need a hand fix; **Low** means it is an annoyance.

## 1. Checked and lined up

| What | How it was checked | Result |
| --- | --- | --- |
| Every pin on the right net in the schematic | Script reads KiCad's netlist back and compares 267 pins | 0 wrong |
| Board copper matches the schematic | KiCad design rules check with schematic comparison | 0 wiring differences (only unused-pin names and descriptions differ) |
| Spacing, widths, holes, edges | KiCad design rules check | 0 errors, 0 unconnected |
| Every symbol pin has a pad on its footprint | Script, all 95 parts | 0 missing |
| Motor driver DRV8876 pin numbers | TI datasheet SLVSDS7B, pin table | Match |
| 5 V converter TPS54302 pins | TI datasheet and KiCad's symbol | Match (1 GND, 2 SW, 3 VIN, 4 FB, 5 EN, 6 BOOT) |
| 3.3 V regulator AP2112K pins | Diodes datasheet | Match |
| ESP32-S3-WROOM-1 pins, boot pins | Espressif datasheet | Match; IO0 pulled up, IO3, IO45, IO46 left open as required |
| Protection FETs AO3401A: pins and gate limit | AOS datasheet rev. 3.1 | G 1, S 2, D 3 match; gate held to 4.0 V at a full battery and 7.8 V at the protection diode's clamp, under the ±12 V limit |
| Battery jack pins | XKB drawing for DC-005-5A-2.0 | Centre pin = pad 1, sleeve = 2, switch = 3; hole spacing within 0.1 mm of the footprint |
| USB-C socket pads | KiCad footprint pad names | Match the symbol, shield included |
| Polarised parts (diodes, LEDs, TVS, electrolytic) | KiCad convention: pad 1 is cathode or + on symbol and footprint | Consistent |
| Capacitor voltage ratings | Each against its rail, including the 24.4 V spike clamp | All rated above the rail; the 220 µF and 22 µF 25 V parts sit at the clamp only during a spike |
| Copper under the Wi-Fi aerial | Script, all four layers | None |
| Battery and motor current on outer layers | Script | None on inner layers |
| Copper under the four M3 screw heads | Script, 3.2 mm radius | Only ground |
| Parts in stock | JLCPCB parts library, October 13 | All 42 lines in stock |

## 2. Problems found that need fixing before ordering

| # | Problem | Severity | Fix |
| --- | --- | --- | --- |
| 1 | Short runs of the motor-supply (VM, down to 0.15 mm) and one motor-output track (MOT_A, 0.25–0.3 mm) are narrow. At the full 1.5 A limit they could warm by an estimated 20–80 °C | Medium | Widen to 0.5 mm or more by hand in KiCad |
| 2 | Converter layout is loose: the 100 nF input capacitor is 7 mm from VIN, the output capacitor 8 mm from the inductor, the inductor 6.4 mm from SW. TI's layout wants these within 1–2 mm. Can cause noise, ripple or an unstable 5 V | Medium | Move C10, C11, L1, C13, C14 tight round U3 following TI's layout example, re-route that corner |
| 3 | Motor-driver capacitors are 5 mm from their pins (VM, VCP, flying cap). TI wants them as close as possible | Medium | Move C4, C5, C6 against U2 |
| 4 | No extra vias under the motor driver's thermal pad on the board (the footprint has 15) | Low | Fine for 1.5 A; add more if it runs hot |
| 5 | Battery pack plug not measured: if centre-negative the board will not turn on (it is protected, not damaged); if its pin is 2.5 mm the jack is loose | High until measured | Measure; the same jack comes with a 2.5 mm pin (LCSC C381115) |
| 6 | Motor stall current not measured; the 1.5 A limit (R5 = 2.2 kΩ) is a guess | Medium | Measure; R5 = 3.3 V ÷ (limit × 0.001) |
| 7 | Motor terminal: the Kefa block wants 1.4 mm holes, the footprint has 1.3 mm, and its body is 0.9 mm deeper than drawn | Low | Enlarge holes to 1.4 mm |

## 3. Risks that cannot be checked on screen

| # | Risk | Severity | How to catch it |
| --- | --- | --- | --- |
| 8 | **JLCPCB places a part turned the wrong way.** KiCad and JLCPCB disagree on rotation for many packages (SOT-23, SOIC, the ESP32 module, USB-C, electrolytics). This is the most common cause of dead assembled boards | High | Check every part in JLCPCB's placement preview before paying; correct rotations there |
| 9 | A real part differs from its footprint (LED cathode mark, switch pin order, alternate maker) | Medium | Compare JLCPCB's preview pictures; the slide switch and LEDs most of all |
| 10 | ESP32 resets when the motor starts (the Pi did this) | Medium | Bench test with the real motor and battery; watch the 3.3 V rail |
| 11 | Watchdog charge pump holds the driver asleep, or never sleeps it. Calculated, not simulated or built | Medium | Simulate; on the first board, jumper JP1 bypasses it |
| 12 | Firmware drives the watchdog pin from a hardware PWM timer, which keeps toggling even if the program hangs, defeating the watchdog | High (safety) | Firmware rule: toggle it from the main control loop only |
| 13 | Kill-switch wire shorted to ground (for example to the carbon tube) reads as "switch closed" and lets the motor run | Medium (safety) | Insulate the wire; consider a normally-open contact that must be held |
| 14 | When the board is switched off with SW3 but the battery stays plugged in, the kill-switch loop, the red "motor armed" light and the dividers draw about 2.5 mA: a full 3 Ah pack flat in about 7 weeks | Low | Unplug the battery when stored, or switch the kill switch off |
| 15 | No battery cut-off on the board; deep discharge is left to the pack's own protection | Medium | Confirm the pack has protection; firmware warns on low voltage from VBAT_ADC |
| 16 | Motor current reading saturates near the limit (2.2 V/A × 1.5 A = 3.3 V, above the ESP32's ~3.1 V range) | Low | Fine for detecting stall; change R5/R6 if exact current matters |
| 17 | Wi-Fi/Bluetooth range cut by metal screws or the carbon tube near the aerial | Low | Nylon screws and spacers; mount aerial end clear of the tube |
| 18 | Hidden solder joints under the ESP32 module and the motor driver | Low | JLCPCB inspection; power up one block at a time |
| 19 | The board does not fit the cane: the electronics mount is drawn for the Pi | Medium | Redesign the mount; test with a printed blank first |
| 20 | Wheel encoder header supplies 3.3 V; many motor encoders need 5 V | Low | Check the encoder before buying |
| 21 | Parts go out of stock or change before ordering | Low | Recheck stock on the day |

## 4. First power-up checklist

Do these in order on one board before trusting the rest.

1. Look over the board against the 3D picture: every part present, ESP32 and motor driver the right way round, LED and diode marks matching.
2. With nothing connected, measure resistance between +BATT and GND, +5V and GND, +3V3 and GND: none should read near 0 Ω.
3. Power from a bench supply set to 12 V with a 0.2 A current limit, not the battery. Kill switch open.
4. Check 5.2 V on the 5 V rail and 3.3 V on the 3.3 V rail, and that the power light (LED2, red like the others) is on.
5. Plug in USB-C and load the firmware. Check the talk button, the battery reading and the status light.
6. Close the kill switch: the red "motor armed" light comes on and VM_ADC reads the battery voltage.
7. With the motor disconnected, command the driver and check that both outputs switch, and that the watchdog puts it to sleep within about 0.1 s when the firmware stops toggling.
8. Connect the motor, raise the supply limit to 2 A, run short pulses at low power, then check the current limit by stalling the wheel.
9. Only then use the real battery, and only then fit it to the cane.

## Confidence

Estimates, not measurements:

- About 85–90% that the board is built exactly as designed.
- About 50–60% that the first boards work with no hand fixes, as the board stands now.
- About 70–80% after fixing items 1–7 and checking item 8 in JLCPCB's preview.

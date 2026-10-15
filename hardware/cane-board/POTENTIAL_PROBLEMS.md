# Cane board: potential problems

What could make the board fail, what has been checked, and what is still open. Written October 14, 2026, and updated the same day for the board with the 5 V module, the XT30 motor socket, the 2.2 A limit and hand-drawn power tracks, then again after a review of the schematic against the DRV8876 datasheet and KiCad's pin maps (items 24 to 30). Nothing has been built.

Severity: **High** means the board may not work or may be damaged; **Medium** means it may work badly or need a hand fix; **Low** means it is an annoyance.

## 1. Checked and lined up

| What | How it was checked | Result |
| --- | --- | --- |
| Every pin on the right net in the schematic | Script reads KiCad's netlist back and compares 256 pins | 0 wrong |
| Board copper matches the schematic | KiCad design rules check with schematic comparison | 0 wiring differences (only unused-pin names and descriptions differ) |
| Spacing, widths, holes, edges | KiCad design rules check | 0 errors, 0 unconnected |
| Every symbol pin has a pad on its footprint | Script, all 95 parts | 0 missing |
| Motor driver DRV8876 pin numbers | TI datasheet SLVSDS7B, pin table | Match |
| 5 V module K7805-1000R3 pins | YLPTEC datasheet against the footprint | Match (1 in, 2 ground, 3 out, 2.54 mm apart). 8 to 36 V in covers the pack |
| Motor socket XT30UPB-F | KiCad's own AMASS footprint for this exact part | Match |
| 3.3 V regulator AP2112K pins | Diodes datasheet | Match |
| ESP32-S3-WROOM-1 pins, boot pins | Espressif datasheet | Match; IO0 pulled up, IO3, IO45, IO46 left open as required |
| Protection FETs AO3401A: pins and gate limit | AOS datasheet rev. 3.1 | G 1, S 2, D 3 match; Q1 and Q4's gates held to 4.0 V at a full battery and 7.8 V at the protection diode's clamp; Q2's to 5.5 V and 10.6 V. All under the ±12 V limit |
| Battery jack pins | XKB drawing for DC-005-5A-2.0 | Centre pin = pad 1, sleeve = 2, switch = 3; hole spacing within 0.1 mm of the footprint |
| USB-C socket pads | KiCad footprint pad names | Match the symbol, shield included |
| Polarised parts (diodes, LEDs, TVS, electrolytic) | KiCad convention: pad 1 is cathode or + on symbol and footprint | Consistent |
| Capacitor voltage ratings | Each against its rail, including the 24.4 V spike clamp | All rated above the rail; the 220 µF and 22 µF 25 V parts sit at the clamp only during a spike |
| Copper under the Wi-Fi aerial | Script, all four layers | None |
| Battery and motor current on outer layers | Script | None on inner layers |
| Width of every motor-current path, pad to pad | Script follows the copper from part to part | 0.6 to 1.0 mm, except 0.4 mm for the last 1 to 1.4 mm into the driver's 0.3 mm pins |
| Copper under the four M3 screw heads | Script, 3.2 mm radius | Only ground |
| Parts in stock | JLCPCB parts library, October 13 and 14 | All lines found; recheck on the day |
| Motor driver IMODE, PMODE and the current-limit formula | TI datasheet SLVSDS7B, read October 14 | IMODE = GND is fixed off-time current chopping with automatic retry, so R5 sets a real limit; PMODE = GND is PH/EN mode; A_IPROPI = 1000 µA/A; VREF at 3.3 V is under its 3.6 V limit; IPROPI's 2.2 mA is under its 3 mA limit |
| Motor driver capacitors | Same datasheet | 100 nF rated 16 V or more on VCP to VM, 22 nF rated for VM on CPH to CPL, 100 nF bypass and bulk on VM: match |
| Watchdog against nSLEEP | Same datasheet: 100 kΩ internal pull-down, 1.5 V logic high, 0.8 V logic low | The pump gives about 2.6 V into the 50 kΩ it sees; nSLEEP falls below logic low about 65 ms after the toggling stops |
| Pin order of the slide switch, the diode pair, the FETs, the 3.3 V regulator, the 5 V module and JP1 | KiCad's symbols read against the footprints and the makers' pinouts | All match: the switch's common is pin 2, the middle pad; BAT54S A, K, COM = 1, 2, 3; AO3401A G, S, D = 1, 2, 3; JP1's middle pad is DRV_SLP |
| Design rules check, rerun October 14 | kicad-cli 10.0.6 on the committed board | 0 errors, 0 unconnected, 5 silkscreen warnings; the ordering files were made after the last board save |

## 2. Problems found that need fixing before ordering

| # | Problem | Severity | Fix |
| --- | --- | --- | --- |
| 1 | ~~Narrow motor-supply and motor tracks~~ | Fixed October 14 | The battery, motor-supply and motor tracks are now drawn by hand, 0.6 to 1.0 mm, before the autorouter runs. The motor connector was turned round so both motor tracks run straight to it |
| 2 | ~~Converter layout is loose~~ | Fixed October 14 | The converter built from parts is replaced by a sealed ready-made module, so there is no switching layout left on the board |
| 3 | Motor-driver capacitors are about 3.5 mm from their pins (VM, VCP, flying cap). TI wants them as close as possible. Moving them closer was tried on October 14: the driver's motor and supply pins then had no way out and the board could not be routed | Low | Left as is. The charge-pump caps carry tiny currents, and the 22 µF VM capacitors sit about 4 mm away |
| 4 | No extra vias under the motor driver's thermal pad on the board (the footprint has 15) | Low | Fine for normal running; a stall heats the driver either way (item 22) |
| 5 | Battery pack plug not measured: if centre-negative the board will not turn on (it is protected, not damaged); if its pin is 2.5 mm the jack is loose | Low | Looked up October 14, not measured. The pack is the common blue 12 V 3000 mAh 3S1P pack; a listing for it gives 68 × 56 × 22 mm (ours measures 55.2 mm wide) and a 5.5 × 2.1 mm plug, which is what J1 takes. Polarity is not stated; packs of this kind are centre positive, and a reversed plug only leaves the board off. To be sure: a 2.0 mm drill bit should fit the plug's hole snugly (loose means 2.5 mm: the same jack comes with a 2.5 mm pin, LCSC C381115), and `../wiring.md` step 5 gives the polarity |
| 6 | Motor stall current not measured. The limit is now 2.2 A (R5 = 1.5 kΩ), above the 1.0 to 1.7 A seller figures, so the motor should push at least as hard as on the IBT-2 | Low | Measure; R5 = 3.3 V ÷ (limit × 0.001) |
| 7 | ~~Motor terminal holes too small~~ | Fixed October 14 | The screw terminal is replaced by an XT30 socket, so the motor wires are soldered to a plug, not to the board |

## 3. Risks that cannot be checked on screen

| # | Risk | Severity | How to catch it |
| --- | --- | --- | --- |
| 8 | **JLCPCB places a part turned the wrong way.** KiCad and JLCPCB disagree on rotation for many packages (SOT-23, SOIC, the ESP32 module, USB-C, electrolytics). This is the most common cause of dead assembled boards | High | Check every part in JLCPCB's placement preview before paying; correct rotations there |
| 9 | A real part differs from its footprint (LED cathode mark, switch pin order, alternate maker) | Medium | Compare JLCPCB's preview pictures; the slide switch and LEDs most of all |
| 10 | ESP32 resets when the motor starts (the Pi did this) | Medium | Bench test with the real motor and battery; watch the 3.3 V rail |
| 11 | Watchdog charge pump holds the driver asleep, or never sleeps it. Calculated, not simulated or built | Medium | Simulate; on the first board, jumper JP1 bypasses it |
| 12 | Firmware drives the watchdog pin from a hardware PWM timer, which keeps toggling even if the program hangs, defeating the watchdog | High (safety) | Firmware rule: toggle it from the main control loop only |
| 13 | Kill-switch wire shorted to ground (for example to the carbon tube) reads as "switch closed" and lets the motor run | Medium (safety) | Insulate the wire; consider a normally-open contact that must be held |
| 14 | SW3 now switches off only the 3.3 V regulator. With the battery plugged in, the 5 V module's idle draw (a few mA, not in its datasheet summary, not measured), the kill-switch loop, the red "motor armed" light and the dividers stay on: a full pack could go flat in a few weeks | Low | Unplug the battery when stored |
| 15 | No battery cut-off on the board; deep discharge is left to the pack's own protection | Medium | Confirm the pack has protection; firmware warns on low voltage from VBAT_ADC |
| 16 | Motor current reading saturates near the limit (1.5 V/A, so it reads up to about 2.0 A of the 2.2 A limit) | Low | Fine for detecting stall |
| 22 | A stalled motor heats the driver: about 2 W at 1.7 A, 3.4 W at the 2.2 A limit. Its own over-temperature cut-out switches it off | Medium | Firmware stops the motor when the current reading stays high; the Pi had no limit at all |
| 23 | The 5 V module is the only through-hole part carrying power that JLCPCB hand-solders; a cold joint would leave the board dead | Low | Look at its three joints; step 4 of the checklist catches it |
| 17 | Wi-Fi/Bluetooth range cut by metal screws or the carbon tube near the aerial | Low | Nylon screws and spacers; mount aerial end clear of the tube |
| 18 | Hidden solder joints under the ESP32 module and the motor driver | Low | JLCPCB inspection; power up one block at a time |
| 19 | The board does not fit the cane: the electronics mount is drawn for the Pi | Medium | Redesign the mount; test with a printed blank first |
| 20 | Wheel encoder header supplies 3.3 V; many motor encoders need 5 V | Low | Check the encoder before buying |
| 21 | Parts go out of stock or change before ordering | Low | Recheck stock on the day |
| 24 | In PH/EN mode, EN low brakes the motor (both low-side switches on). There is no coast state short of putting the driver to sleep, so `FREE` and `STOP`/`CENTER` are the same in hardware | Decided October 14 | Kept as is. The worm gear holds the wheel whether the driver brakes or coasts, so they differ only in the last few milliseconds of spin-down. A dropped link still sleeps the driver, which coasts, as the IBT-2 did. Firmware that wants a coast for `FREE` stops the heartbeat. See "Brake or coast" in the README |
| 25 | ~~Q2, the kill-switch FET, has only −2.9 V on its gate from a 9 V pack~~ | Fixed October 14 | R2 and R3 changed from 47k and 100k to 10k and 13k: the gate now gets 0.43 of the battery, 3.9 V from 9 V, so about 60 mΩ and 0.3 W at the 2.2 A limit. Values only; the routed board is unchanged. The kill switch now carries about 0.5 mA and opens the supply in about 2 ms |
| 26 | The 3.3 V regulator drops about 1.35 V while feeding the processor (120 to 355 mA) and the 80 mA buzzer: 0.2 to 0.35 W in a SOT-23-5, a 30 to 90 °C rise depending on the copper under it | Medium | Feel it on the bench with Wi-Fi and the buzzer running; feed the buzzer from 5 V with a 5 V motor if it runs hot |
| 27 | The watchdog pump's output falls with the toggle rate: below about 30 Hz nSLEEP drops under its 1.5 V logic high | Low (safety) | Firmware rule: toggle HBEAT at 200 Hz or more, from the main loop |
| 28 | nFAULT does not report the 2.2 A chopping in this IMODE, only overcurrent (3.5 to 5.5 A), undervoltage and over-temperature | Low | Detect a stall from I_ADC; IMODE = 20 kΩ to ground would also flag chopping on nFAULT |
| 29 | With the power switch off, the battery and motor-supply dividers push about 20 µA each into the unpowered processor through its protection diodes | Low | Harmless in practice; out of specification on paper |
| 30 | No ESD parts on the kill-switch, talk, buzzer and encoder plugs, whose wires run up the cane | Low | Fine for v0.1; TVS diodes on a later board |

## 4. First power-up checklist

Do these in order on one board before trusting the rest.

1. Look over the board against the 3D picture: every part present, ESP32 and motor driver the right way round, LED and diode marks matching.
2. With nothing connected, measure resistance between +BATT and GND, +5V and GND, +3V3 and GND: none should read near 0 Ω.
3. Power from a bench supply set to 12 V with a 0.2 A current limit, not the battery. Kill switch open.
4. Check 5.0 V on the 5 V rail and 3.3 V on the 3.3 V rail, and that the power light (LED2, red like the others) is on.
5. Plug in USB-C and load the firmware. Check the talk button, the battery reading and the status light.
6. Close the kill switch: the red "motor armed" light comes on and VM_ADC reads the battery voltage.
7. With the motor disconnected, command the driver and check that both outputs switch, and that the watchdog puts it to sleep within about 0.1 s when the firmware stops toggling.
8. Connect the motor, raise the supply limit to 2.5 A, run short pulses at low power, then check the current limit by stalling the wheel.
9. Only then use the real battery, and only then fit it to the cane.

## Confidence

Estimates, not measurements:

- About 85–90% that the board is built exactly as designed.
- About 75–80% that the first boards work with no hand fixes, now that items 1, 2, 6, 7 and 25 are fixed.
- About 85% if item 8 is checked in JLCPCB's preview and item 10 is checked on the bench first. What is left is mostly things no screen check can catch: a part placed the wrong way and the processor resetting when the motor starts.

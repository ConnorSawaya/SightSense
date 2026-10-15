# Cane board: potential problems

What could make the board fail, what has been checked, and what is still open. Written October 14, 2026, and updated the same day for the board with the 5 V module, the XT30 motor socket, the 2.2 A limit and hand-drawn power tracks, then again after a review of the schematic against the DRV8876 datasheet and KiCad's pin maps (items 24 to 30), and after looking up the supply chain's margins (items 10 and 31 to 33), and again after an outside review the same evening (items 29, 36 and 37, and the watchdog's timing). Nothing has been built.

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
| Battery jack pins | XKB drawing for DC-005-5A-2.0, read again October 14 | Centre pin = pad 1, sleeve = 2, switch = 3; hole spacing within 0.1 mm of the footprint (5.9 against 6.0, and 2.9 against 3.0, with 4.7 down for pin 3). Slots now 1.0 × 3.5 mm, as the drawing asks (item 34) |
| Slide switch SW3 land pattern | Shouhan's MSK12C02 drawing | KiCad's footprint matches: pads 0.6 mm wide at 3.0 and 1.5 mm spacing (drawing 3 and 1.45), two 0.85 mm locating holes 3 mm apart, tabs 8.4 mm across. Pin 2, the middle one, is the common |
| ADC inputs during a supply spike | Sums | With the 1M/100k dividers (item 29), the 24.4 V clamp puts 2.2 V on IO2 and IO4, under the 3.3 V rail, and a full pack 1.15 V |
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
| Watchdog against nSLEEP | Same datasheet: 100 kΩ internal pull-down, 1.5 V logic high, 0.8 V logic low | The pump gives about 2.6 V into the 50 kΩ it sees; nSLEEP falls below logic low about 60 ms after the toggling stops with the pin low, and about 125 ms with it left high, when C8 still feeds the load |
| Pin order of the slide switch, the diode pair, the FETs, the 3.3 V regulator, the 5 V module and JP1 | KiCad's symbols read against the footprints and the makers' pinouts | All match: the switch's common is pin 2, the middle pad; BAT54S A, K, COM = 1, 2, 3; AO3401A G, S, D = 1, 2, 3; JP1's middle pad is DRV_SLP |
| Design rules check, rerun October 14 | kicad-cli 10.0.6 on the committed board | 0 errors, 0 unconnected, board matches the schematic. 16 warnings, none electrical: 10 footprints differ from KiCad's library copies on purpose (the jack's longer slots, no paste on the unfitted parts, the module's widened holes), the jack's outline print runs over its larger pads (the ordering files cut print off pads), and the module's print meets the board edge. The ordering files were made after the last board save |
| Watchdog pump | `check_watchdog.py`, a time-step model with the BAT54S diode law and the driver's 100 kΩ pull-down | nSLEEP holds 2.5 V at 200 Hz and 2.2 V at 100 Hz, above the 1.5 V threshold; falls below it under about 40 Hz; wakes in under 1 ms; asleep about 60 ms after the toggling stops low, about 125 ms after it stops high. An outside review got the same figures by hand |
| Supply chain under motor load | Sums from the datasheets: pack sag, fuse and FET drops, the 5 V module's 8 V minimum, the Schottky and regulator drops, ESP-IDF's 2.44 V brownout default | About 1.1 V to spare on the 3.3 V rail; only a pack under about 8 V at the jack can reset the processor |
| Board against JLCPCB's 4-layer limits | Their capabilities page, October 14, against the board's rules and its smallest features | Tracks 0.15 mm (limit 0.09), gaps 0.15 (0.09), vias 0.6/0.3 mm (0.25/0.15), smallest hole 0.3 (0.15), copper to edge 0.5 (0.2), no copper on the inner layers for the motor or battery. Solder-mask dams 0.2 mm at the tightest pins, the driver and the USB socket; black mask needs 0.13. Silkscreen text raised to their 1.0 mm / 0.15 mm minimum |
| Ordering files against the board | Script: fitted parts on the board, the placement file and the BOM | 82 parts in all three, the same 82; the 8 unfitted parts in none; JP1 (a solder jumper, no part) in neither, as it should be |
| JLCPCB's rotation for each part | JLCPCB's own footprint previews for the exact LCSC parts, against KiCad's footprints, October 14 | SOT-23 parts (Q1 to Q4, D4) 180°; U4 (AP2112K) and U2 (DRV8876) 270°; the JST plugs and the XT30 180°; everything else as KiCad has it, including C1, J11, the LEDs and diodes. The generic tables in other tools would have turned U4 a quarter and C1 and J11 round. `make_fab.py` applies these |
| Stock, evening of October 14 | LCSC's pages for the six parts that matter most | ESP32 module 2,222 (was 2,543), motor driver 29,627, 5 V module 9,427, XT30 43,520, 220 µF can 21,915, USB TVS 10 million. The can is 8 mm across, as the footprint expects |

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
| 34 | ~~Battery jack slots 1.0 × 3.0 mm; XKB's drawing asks for 1.0 × 3.5 mm~~ | Fixed October 14 | KiCad's footprint is for a generic jack. With 3.0 mm slots the jack's blades may not go in, or only by force. Slots lengthened to 3.5 mm and the pads to 4.0 mm to keep the copper ring; `make_pcb.py` does the same. DRC 0 errors |
| 35 | ~~Solder paste printed on the unfitted parts' pads~~ | Fixed October 14 | The phone socket, its switch and its four resistors and two capacitors are not fitted, but their pads were on the stencil, leaving solder lumps that can short the socket's fine USB-C pads. Paste removed from all 27 of those pads; `make_pcb.py` does the same |

## 3. Risks that cannot be checked on screen

| # | Risk | Severity | How to catch it |
| --- | --- | --- | --- |
| 8 | **JLCPCB places a part turned the wrong way.** KiCad and JLCPCB measure rotation from different footprints, and this is the most common cause of dead assembled boards | Medium | The placement file now carries JLCPCB's rotations, checked part by part (section 1, and item 36). Still tick "confirm parts placement" and check every part in the preview before paying. Looking down on the board with the aerial at the top: **U1** pin 1 top-left; **U2** pin 1 bottom-right (turned round); **U3** pin 1 (IN) on the left; **U4**, **Q1 to Q4** and **D4** pin 1 top-left; **C1** + on the left, so its stripe, which marks −, is on the **right**; **D5 to D9** and **LED1 to LED3** cathode on the left; **D1** cathode at the bottom; **J11** pad A1 at the lower left of its row of pads; **SW3** pin 1 at the bottom. The XT30's chamfered end is on the right; the JST plugs and the XT30 should match their printed outlines |
| 9 | A real part differs from its footprint (LED cathode mark, switch pin order, alternate maker) | Low | The slide switch and the battery jack are now checked against their makers' drawings (section 1). Compare JLCPCB's preview pictures for the LEDs |
| 10 | ESP32 resets when the motor starts. The Pi was feared to, and logged under-voltage on a weak USB supply, but a reset from the motor was never seen. A Pi 5 wants 5.1 V at up to 3 A and warns below 4.63 V; this board's chain is pack → 5 V module (8 to 36 V in) → Schottky → 3.3 V regulator with about 1.1 V to spare, at 0.3 A at most, and the processor's brownout trips at 2.44 V (ESP-IDF default). By these sums only a pack below about 8 V at the jack can brown it out | Low | Bench test with the real motor and battery; watch the 3.3 V rail. See item 31 for the one case that can |
| 11 | Watchdog charge pump holds the driver asleep, or never sleeps it. Simulated October 14 (`check_watchdog.py`, section 1), not built | Low | On the first board, jumper JP1 bypasses it if the model is wrong |
| 12 | Firmware drives the watchdog pin from a hardware PWM timer, which keeps toggling even if the program hangs, defeating the watchdog | High (safety) | Firmware rule 1 in the README: toggle it from the main control loop only |
| 13 | Kill-switch wire shorted to ground (for example to the carbon tube) reads as "switch closed" and lets the motor run | Medium (safety) | Insulate the wire; consider a normally-open contact that must be held |
| 14 | SW3 now switches off only the 3.3 V regulator. With the battery plugged in, the 5 V module's idle draw (a few mA, not in its datasheet summary, not measured), the kill-switch loop, the red "motor armed" light and the dividers stay on: a full pack could go flat in a few weeks. The dividers now take about 11 µA each, down from about 100 µA | Low | Unplug the battery when stored |
| 15 | No battery cut-off on the board; deep discharge is left to the pack's own protection | Medium | Confirm the pack has protection; firmware warns on low voltage from VBAT_ADC |
| 16 | Motor current reading saturates near the limit (1.5 V/A, so it reads up to about 2.0 A of the 2.2 A limit) | Low | Fine for detecting stall |
| 22 | A stalled motor heats the driver: about 2 W at 1.7 A, 3.4 W at the 2.2 A limit. Its own over-temperature cut-out switches it off | Medium | Firmware rule 3 in the README: stop when the current reading stays high; the Pi had no limit at all |
| 23 | The 5 V module is the only through-hole part carrying power that JLCPCB hand-solders; a cold joint would leave the board dead | Low | Look at its three joints; step 4 of the checklist catches it |
| 17 | Wi-Fi/Bluetooth range cut by metal screws or the carbon tube near the aerial | Low | Nylon screws and spacers; mount aerial end clear of the tube |
| 18 | Hidden solder joints under the ESP32 module and the motor driver | Low | JLCPCB inspection; power up one block at a time |
| 19 | The board does not fit the cane: the electronics mount is drawn for the Pi | Medium | Redesign the mount; test with a printed blank first |
| 20 | Wheel encoder header supplies 3.3 V; many motor encoders need 5 V | Low | Check the encoder before buying |
| 21 | Parts go out of stock or change before ordering. The processor module is the thinnest line: 2,222 on the evening of October 14, down 321 in a day | Low | Recheck stock on the day; JLCPCB shows it at upload |
| 24 | In PH/EN mode, EN low brakes the motor (both low-side switches on). There is no coast state short of putting the driver to sleep, so `FREE` and `STOP`/`CENTER` are the same in hardware | Decided October 14 | Kept as is. The worm gear holds the wheel whether the driver brakes or coasts, so they differ only in the last few milliseconds of spin-down. A dropped link still sleeps the driver, which coasts, as the IBT-2 did. Firmware that wants a coast for `FREE` stops the heartbeat. See "Brake or coast" in the README |
| 25 | ~~Q2, the kill-switch FET, has only −2.9 V on its gate from a 9 V pack~~ | Fixed October 14 | R2 and R3 changed from 47k and 100k to 10k and 13k: the gate now gets 0.43 of the battery, 3.9 V from 9 V, so about 60 mΩ and 0.3 W at the 2.2 A limit. Values only; the routed board is unchanged. The kill switch now carries about 0.5 mA and opens the supply in about 2 ms |
| 26 | The 3.3 V regulator drops about 1.35 V while feeding the processor (120 to 355 mA) and the 80 mA buzzer: 0.2 to 0.35 W in a SOT-23-5, a 30 to 90 °C rise depending on the copper under it | Medium | Feel it on the bench with Wi-Fi and the buzzer running; feed the buzzer from 5 V with a 5 V motor if it runs hot |
| 27 | The watchdog pump's output falls with the toggle rate: the simulation puts nSLEEP under its 1.5 V logic high below about 40 Hz | Low (safety) | Firmware rule 1 in the README: a 200 Hz square wave or faster (400 toggles a second), from the main loop, stopped low |
| 28 | nFAULT does not report the 2.2 A chopping in this IMODE, only overcurrent (3.5 to 5.5 A), undervoltage and over-temperature | Low | Detect a stall from I_ADC; IMODE = 20 kΩ to ground would also flag chopping on nFAULT |
| 29 | ~~The voltage dividers overdrive IO2 and IO4~~ (found by an outside review) | Fixed October 14 | With 100k/22k, the 24.4 V clamp put 4.4 V on the pins, over Espressif's 3.6 V limit, and with the power switch off the dividers pushed current into the unpowered processor, which Espressif does not allow for. Now 1M/100k (R24 to R27, values only, all Basic parts): 2.2 V at the clamp, 1.15 V at a full pack, and about 7 µA into an unpowered pin. The 100 nF capacitors at the pins keep the readings steady. Espressif gives no injection limit, so that last figure is small rather than specified |
| 36 | ~~The placement file used KiCad's origins and rotations~~ (found by an outside review) | Fixed October 14 | KiCad puts the connectors' and the 5 V module's origin on pin 1, and its rotations differ from JLCPCB's for several parts. `make_fab.py` now writes each part's body centre and JLCPCB's rotation. Q1 to Q4 and D4 were 0° and are now 180°, U4 0° → 270°, U2 180° → 90°, the JST plugs and the XT30 turned 180° |
| 37 | ~~The pin-1 list for the placement preview had C1's stripe and J11's A1 wrong~~ (found by an outside review) | Fixed October 14 | C1's stripe marks −, which is on the right; J11's A1 is at the lower left. Following the old list would have put C1 in backwards across the battery |
| 30 | No ESD parts on the kill-switch, talk, buzzer and encoder plugs, whose wires run up the cane | Low | Fine for v0.1; TVS diodes on a later board |
| 31 | A nearly flat pack under motor load. A 3S pack sags about 0.4 to 0.6 V at the 2.2 A limit, and the fuse and FETs take another 0.1 V, so a 9.0 V pack reaches about 8.3 V at the 5 V module, whose lowest input is 8 V. Below that the 5 V rail falls and the processor resets | Medium (firmware) | Firmware rule 2 in the README: stop driving the motor when VBAT_ADC reads under 9.3 V, and warn aloud before that. Estimates; measure the pack's sag on the bench |
| 32 | Brush noise from the motor on a 20 cm lead. Rarely resets a processor with its own decoupling, but can upset the current, battery and motor-supply readings and Wi-Fi | Low | A 100 nF ceramic across the motor's terminals, at the motor, is now in the BOM's off-board list. Nothing to change on the board |
| 33 | The board holds about 300 µF, which looks like a short for about 100 µs when the battery is plugged in. Small 3S packs sometimes latch off on this | Low | Unplug and plug in again. The cane as built had a converter and the IBT-2 on the same pack, with similar capacitance, and the pack coped |

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
- About 80% that the first boards work with no hand fixes, now that items 1, 2, 6, 7, 25, 29, 36 and 37 are fixed and the watchdog and supply chain are modelled.
- About 90% if item 8 is checked in JLCPCB's preview and the firmware keeps the rules in the README. What is left is what no screen check can catch: a part placed the wrong way, a model that is wrong, and the real pack and motor. The remaining 10% is why there is a first power-up checklist, and why JP1 and R5 exist.

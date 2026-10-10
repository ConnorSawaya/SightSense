# Wheel adapter (v1)

A printed hub that puts the omni wheel's hex socket onto the JGY-370 worm gearmotor's 6 mm D-shaft, so the wheel mounts directly on the motor.

Experimental prototype. Nothing here has been printed, fitted or load tested.

**Not ready to print.** Three sizes are estimates, not measurements: the wheel's hex socket (12 mm across flats, read off photos), the shaft's flat (5.5 mm across, a common size for 6 mm D-shafts) and the shaft length (14 mm, from seller listings that say 14 to 15 mm). Print `wheel_adapter_fit_test.stl` first and try it on the shaft and in the wheel.

![Sections of the adapter](previews/wheel_adapter.png)

## Files

| File | What it is |
| --- | --- |
| `wheel_adapter.py` | build123d source. Running it exports the parts and runs the geometric checks; `--preview` also renders the drawing. It imports helpers from `../handle-phone-mount/`. |
| `export/wheel_adapter.stl` | The adapter, turned to its print orientation |
| `export/wheel_adapter_fit_test.stl` | Short hex with the D-bore through it, to check both fits |
| `export/*.step` | The same parts for CAD |

## Dimensions (from the source)

| Feature | Value |
| --- | --- |
| D-bore | 6.15 mm diameter, 5.65 mm across the flat, 13 mm deep |
| Hex for the wheel | 11.8 mm across flats, 12 mm long, 0.8 mm chamfer on the end |
| Collar | Hexagon, 22 mm across flats, 8 mm long |
| Overall | 25.4 × 22.0 × 20.0 mm |
| Screw holes | 3.2 mm, for M3 |
| Nut slots | 5.8 × 2.7 mm, for M3 nuts |

The hex is longer than the wheel's socket is deep on purpose, so it bottoms in the socket.

## How it carries load

- **Torque:** the D-bore on the shaft's flat, then the hex into the wheel.
- **Bending:** the steel shaft runs through the collar and 5 mm into the hex, so the step between them has steel inside it. Past the shaft tip an M3 screw runs down the middle.
- **Pull-off:** an M3 screw through a captured nut presses on the shaft's flat. A second M3 screw comes through the wheel from the far side into a captured nut in the hex and holds the wheel on.

**Weak point:** the slot for the wheel-screw nut cuts into the hex just past the shaft tip, with 1.6 mm of plastic between them. That is where it would break in a hard impact. The shaft is too short to reach further into the wheel. A bought 6 mm metal hex hub of the right size is the fallback.

## Hardware

| Qty | Item | Where |
| --- | --- | --- |
| 1 | M3 × 10 screw + M3 nut | Clamp onto the shaft's flat |
| 1 | M3 screw, long enough to pass through the wheel, + M3 nut | Holds the wheel on the hex |
| 1 | Washer or the wheel kit's flanged cap | Under the wheel screw's head, on the far side of the wheel |

## Printing notes

These are suggestions, not tested settings.

- **Material:** PETG-CF, hardened nozzle.
- **Orientation:** lying on a collar flat, as exported, so the layers run along the axis. It needs a little support under the hex.
- **Walls and infill:** 100% infill, or 5 walls or more.

## To measure before printing the full part

1. The wheel's hex socket: across flats and depth (or the same on the aluminium coupler that came with the wheel).
2. The motor shaft: from the flat to the opposite side, and the length sticking out of the gearbox.
3. The wheel's centre hole diameter and the hub thickness between the two hex sockets.

Set `HEX_AF`, `SHAFT_ACROSS_FLAT` and `SHAFT_LEN` at the top of `wheel_adapter.py` and re-export. `PILOT_D` and `PILOT_LEN` add a round pilot through the hub.

## Note on the wheel design

`AGENTS.md` records the wheel decision as one motor steering a free-rolling wheel. This adapter mounts an omni wheel directly on the motor shaft instead. The decisions table has not been changed.

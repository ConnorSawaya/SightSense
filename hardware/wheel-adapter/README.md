# Wheel adapter (v2)

A printed hub that puts the omni wheel onto the JGY-370 worm gearmotor's 6 mm D-shaft, so the wheel mounts directly on the motor. From the gearbox outwards it is a hexagonal collar, a 12 mm hex that drives the wheel, and a 10 mm round pilot that goes inwards through the wheel's centre hole. A small cap goes on the far side of the wheel.

Experimental prototype. Nothing here has been printed, fitted or load tested.

![Sections of the adapter](previews/wheel_adapter.png)

## Where the sizes come from

| Size | Value | Source |
| --- | --- | --- |
| Wheel hex socket | 12 mm across flats | Measured by the team |
| Wheel centre hole | 10 mm | Measured by the team |
| Shaft diameter, length | 6 mm, 14 mm beyond the bosses | Published JGY-370 outline drawing |
| Shaft flat | 12 mm long; 5.4 mm across in the drawing, 5.5 mm in one seller's photo | Published drawing; not measured on this motor |
| Pilot length | 10 mm | Estimate. It must be shorter than the 10 mm hole is deep |

The bore is 5.75 mm across the flat, so it takes a 5.4 or a 5.5 mm shaft; the clamp screw takes up the slack. Print `wheel_adapter_fit_test.stl` first and try it on the shaft tip and in the wheel.

## Files

| File | What it is |
| --- | --- |
| `wheel_adapter.py` | build123d source. Running it exports the parts and runs the geometric checks; `--preview` also renders the drawing. It imports helpers from `../handle-phone-mount/`. |
| `export/wheel_adapter.stl` | The adapter, turned to its print orientation |
| `export/wheel_cap.stl` | Cap for the far side of the wheel; the nut tightens against it |
| `export/wheel_adapter_fit_test.stl` | Short hex and pilot with the D-bore through the hex, to check the fits |
| `export/*.step` | The same parts for CAD |

## Dimensions (from the source)

| Feature | Value |
| --- | --- |
| Bore | 6.2 mm diameter, 5.75 mm across the flat, round for the first 2 mm, 16.3 mm deep |
| Shaft engagement | 13 mm |
| Hex for the wheel | 11.8 mm across flats, 12 mm long |
| Pilot | 9.8 mm diameter, 10 mm long, 0.8 mm chamfer on the end |
| Collar | Hexagon, 22 mm across flats, 8 mm long |
| Overall | 25.4 × 22.0 × 30.0 mm |
| Screw holes | 3.2 mm, for M3 |
| Cap | 20 mm flange, 3 mm thick, with a 4 mm long hex of 11.8 mm across flats |

The hex is longer than the wheel's socket is deep on purpose, so the step to the pilot seats in the socket.

## How it carries load

- **Torque:** the D-bore on the shaft's flat, then the hex into the wheel.
- **Bending:** the steel shaft runs through the collar and 5 mm into the hex. Past the shaft tip an M3 screw runs down the middle of solid plastic. No slot is cut into the hex or the pilot.
- **Pull-off:** an M3 screw through a captured nut presses on the shaft's flat. The wheel screw's head sits at the bottom of the bore, trapped behind the motor shaft, and its nut goes on the far side of the wheel, in the open.

## Hardware

| Qty | Item | Where |
| --- | --- | --- |
| 1 | M3 × 10 screw + M3 nut | Clamp onto the shaft's flat. Do not use a longer screw: it sweeps past the motor receiver |
| 1 | M3 socket-head screw, about 8 mm longer than the wheel hub is wide, + M3 nut | Holds the wheel on |
| 1 | `wheel_cap`, the wheel kit's flanged piece, or a large washer | Under the nut, on the far side of the wheel |

## Assembly

1. Drop the wheel screw, head last, down the bore so its thread comes out of the pilot. The 5.5 mm head only just clears the bore, which may need cleaning out after printing.
2. Push the wheel onto the hex and pilot, add the cap, and tighten the nut while holding the screw head with a hex key through the bore.
3. Slide the assembly onto the motor shaft and tighten the clamp screw onto the flat.

## Printing notes

These are suggestions, not tested settings.

- **Material:** PETG-CF, hardened nozzle.
- **Orientation:** the adapter lying on a collar flat, as exported, so the layers run along the axis. It needs a little support under the hex and pilot. The cap prints flange down.
- **Walls and infill:** 100% infill, or 5 walls or more.

## Still to check

1. The depth of the wheel's 10 mm hole and of its hex socket.
2. That the far side of the wheel has the same 12 mm hex socket. If not, use a washer instead of the cap.
3. The shaft's flat, measured from the flat to the opposite side.

## Note on the wheel design

`AGENTS.md` records the wheel decision as one motor steering a free-rolling wheel. This adapter mounts an omni wheel directly on the motor shaft instead. The decisions table has not been changed.

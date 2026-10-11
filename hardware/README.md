# Hardware

Printable parts, wiring and build notes for the cane.

| Folder / file | Contents | Status |
| --- | --- | --- |
| [`cane-coupler/`](cane-coupler/) | Keyed two-piece insert that joins 18 mm carbon-fibre tube sections. v4 adds an M3 cross bolt and a receiver that holds the gearmotor at the tip | v3: design in, not yet printed. v4: design in, not printed; motor sizes from a published drawing |
| [`wiring.md`](wiring.md) | Raspberry Pi, L298N motor driver, motor, switches and power | Planned wiring |
| [`wheel-adapter/`](wheel-adapter/) | Hub and cap that put the omni wheel onto the gearmotor's 6 mm D-shaft | Design in, not printed; wheel hex and centre hole measured, shaft sizes from a published drawing |
| `motor-bracket/` | Holds the 12 V motor above the steering fork | To design |
| `pi-plate/` | Carries the Pi and the L298N on the tube | To design |
| [`handle-phone-mount/`](handle-phone-mount/) | Tilted handle, pole collar and adjustable phone cradle (camera forward) | Design in, not yet printed; cradle is oversize and the phone is strapped in |
| [`electronics-mount/`](electronics-mount/) | Two-piece clamp on the tube above the motor: Raspberry Pi 5 on standoffs on one side, a flat plate for the battery on the other | Design in, not printed |
| [`motor-mount-2/`](motor-mount-2/) | Sturdier version of the v4 motor receiver: adds a sleeve over the end of the tube and holds the gearbox along its whole length. Takes the same v4 main insert | Design in, not printed; motor sizes from a published drawing |
| [`joint-sleeve/`](joint-sleeve/) | Clamp that goes over the joint between two tubes and takes the bending that the coupler's printed tongue cannot. One per joint | Design in, not printed; its strength figures are estimates |
| [`assembly/`](assembly/) | Interactive 3D model of the whole cane with every printed part in place, as one HTML file to open in a browser | Model only; the tube length, the wheel and the phone are stand-ins |

## Conventions

- Put each part in its own folder with its source file (`.scad`, `.step` or `.f3d`), the exported `.stl`, and a short `README.md`.
- Put the version in the file name (`_v1`, `_v2`), and keep old versions until the new one has been printed and fitted.
- Rigid parts in PETG-CF; soft pads and the tyre in TPU.
- Keep bare circuit boards off carbon-fibre parts, which can conduct electricity. Use standoffs.
- Every printed part needs a bought fallback (metal bracket, bike phone mount, project box) in case it is not ready.

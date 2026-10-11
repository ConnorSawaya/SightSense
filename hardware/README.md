# Hardware

Printable parts, wiring and build notes for the cane.

| Folder / file | Contents | Status |
| --- | --- | --- |
| [`cane-coupler/`](cane-coupler/) | Keyed two-piece insert that joins 18 mm carbon-fibre tube sections. v4 adds an M3 cross bolt and a receiver that holds the gearmotor at the tip | v3: design in, not yet printed. v4: design in, not printed; motor sizes from a published drawing |
| [`wiring.md`](wiring.md) | Raspberry Pi, IBT-2 motor driver, motor, switches and power, with a check list and first tests | Six Pi-to-driver wires fitted; switches, fuse and kill switch not fitted; not tested under power |
| [`diagrams/`](diagrams/) | The wiring diagrams used in `wiring.md`, and the script that draws them | Drawn |
| [`wheel-adapter/`](wheel-adapter/) | Hub and cap that put the omni wheel onto the gearmotor's 6 mm D-shaft | Design in, not printed; wheel hex and centre hole measured, shaft sizes from a published drawing |
| `motor-bracket/` | Holds the 12 V motor above the steering fork | To design |
| `pi-plate/` | Carries the Pi and the motor driver on the tube | To design |
| [`handle-phone-mount/`](handle-phone-mount/) | Tilted handle, pole collar and adjustable phone cradle (camera forward) | Design in, not yet printed; cradle is oversize and the phone is strapped in |
| [`electronics-mount/`](electronics-mount/) | Two-piece clamp on the tube above the motor: Raspberry Pi 5 on standoffs on one side, a flat plate for the battery on the other | Design in, not printed |

## Conventions

- Put each part in its own folder with its source file (`.scad`, `.step` or `.f3d`), the exported `.stl`, and a short `README.md`.
- Put the version in the file name (`_v1`, `_v2`), and keep old versions until the new one has been printed and fitted.
- Rigid parts in PETG-CF; soft pads and the tyre in TPU.
- Keep bare circuit boards off carbon-fibre parts, which can conduct electricity. Use standoffs.
- Every printed part needs a bought fallback (metal bracket, bike phone mount, project box) in case it is not ready.

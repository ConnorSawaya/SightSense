# Hardware

Printable parts, wiring and build notes for the cane.

| Folder / file | Contents | Status |
| --- | --- | --- |
| [`cane-coupler/`](cane-coupler/) | Keyed two-piece insert that joins 18 mm carbon-fibre tube sections | Design in, not yet printed |
| [`wiring.md`](wiring.md) | Raspberry Pi, L298N motor driver, motor, switches and power | Planned wiring |
| [`wheel-adapter/`](wheel-adapter/) | Hub that puts the omni wheel's hex onto the gearmotor's 6 mm D-shaft | Design in, not printed; hex and shaft sizes are estimates |
| `motor-bracket/` | Holds the 12 V motor above the steering fork | To design |
| `pi-plate/` | Carries the Pi and the L298N on the tube | To design |
| [`handle-phone-mount/`](handle-phone-mount/) | Tilted handle, pole collar and adjustable phone cradle (camera forward) | Design in, not yet printed; cradle is oversize and the phone is strapped in |

## Conventions

- Put each part in its own folder with its source file (`.scad`, `.step` or `.f3d`), the exported `.stl`, and a short `README.md`.
- Put the version in the file name (`_v1`, `_v2`), and keep old versions until the new one has been printed and fitted.
- Rigid parts in PETG-CF; soft pads and the tyre in TPU.
- Keep bare circuit boards off carbon-fibre parts, which can conduct electricity. Use standoffs.
- Every printed part needs a bought fallback (metal bracket, bike phone mount, project box) in case it is not ready.

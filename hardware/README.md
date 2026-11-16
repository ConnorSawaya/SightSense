# Hardware

Printable parts, wiring and build notes for the cane.

| Folder / file | Contents | Status |
| --- | --- | --- |
| [`tip/`](tip/) | v2 tip: VEX 2 in omni wheel on a Pololu micro gearmotor, in one printed part that plugs into the lower tube; the wheel is held on both sides | Design in (November 15), not printed or tested; figures are estimates |
| [`tube-joint/`](tube-joint/) | v2 joint between the cane's two tubes: a thinner carbon tube inside carries the bending, two printed collars key it | Design in (November 15), not printed or tested; strength figures are estimates |
| [`cane-coupler/`](cane-coupler/) | v1: keyed two-piece insert that joined the tube sections. v4 adds an M3 cross bolt and a receiver that holds the gearmotor at the tip | v1 joint snapped; replaced by [`tube-joint/`](tube-joint/) and [`tip/`](tip/) in v2 |
| [`BOM.md`](BOM.md) | Bill of materials: electronics, tubes, printed parts, screws and nuts, with the page each line comes from | No prices or shop links |
| [`wiring.md`](wiring.md) | Raspberry Pi, IBT-2 motor driver, motor, switches and power, with a check list and first tests | Six Pi-to-driver wires fitted; switches, fuse and kill switch not fitted; not tested under power |
| [`diagrams/`](diagrams/) | The wiring diagrams used in `wiring.md`, and the script that draws them | Drawn |
| [`wheel-adapter/`](wheel-adapter/) | Hub and cap that put the omni wheel onto the gearmotor's 6 mm D-shaft | v1; replaced by [`tip/`](tip/) in v2 |
| [`handle-phone-mount/`](handle-phone-mount/) | Tilted handle, pole collar and adjustable phone cradle (camera forward) | Design in, not yet printed; cradle is oversize and the phone is strapped in |
| [`electronics-mount/`](electronics-mount/) | Two-piece clamp on the tube above the motor: Raspberry Pi 5 on standoffs on one side, a flat plate for the battery on the other | Design in, not printed |
| [`motor-mount-2/`](motor-mount-2/) | Sturdier version of the v4 motor receiver: adds a sleeve over the end of the tube and holds the gearbox along its whole length. Takes the same v4 main insert | v1; replaced by [`tip/`](tip/) in v2 |
| [`joint-sleeve/`](joint-sleeve/) | v1: clamp over the joint between two tubes, to take the bending the coupler's printed tongue could not | Not needed with the v2 joint; kept for reference |
| [`cane-board/`](cane-board/) | One circuit board to replace the Raspberry Pi, its converter, the IBT-2 driver and the jumper wires: ESP32-S3, motor driver with a current limit, built-in 12 V to 5 V, kill-switch and battery protection | Drawn after the event. Schematic passes KiCad's checks; routed on a 46 × 100 mm 4-layer board with 0 design-rule errors; ordering files made but nothing ordered; no firmware; not built. Has its own [bill of materials](cane-board/BOM.md) |
| [`assembly/`](assembly/) | Interactive 3D model of the whole cane with every printed part in place, as one HTML file to open in a browser | v1 model only, drawn with four 400 mm tubes and their couplers; the wheel and the phone are stand-ins |

The whole cane, with its electronics and wiring, can be turned round and stepped through at <https://connorsawaya.github.io/SightSense/>.

## Conventions

- Put each part in its own folder with its source file (`.scad`, `.step` or `.f3d`), the exported `.stl`, and a short `README.md`.
- Put the version in the file name (`_v1`, `_v2`), and keep old versions until the new one has been printed and fitted.
- Rigid parts in PETG-CF; soft pads and the tyre in TPU.
- Keep bare circuit boards off carbon-fibre parts, which can conduct electricity. Use standoffs.
- Every printed part needs a bought fallback (metal bracket, bike phone mount, project box) in case it is not ready.

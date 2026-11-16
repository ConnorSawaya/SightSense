# Tube joint (v2)

The joint between the cane's two carbon tubes, redone because the v1 joint snapped. An aluminium tube inside the joint, like a tent pole's, takes the bending; two small printed collars only stop the sections twisting and keep the tube mouths from splitting. The cane still comes apart into its two sections, held together by the shock cord.

Experimental prototype. Nothing here has been printed, fitted or load tested. The strength figures are estimates from the model and from typical material values, not measurements.

![The joint cut through the middle](previews/tube_joint_section.png)

## Why the v1 joint snapped

In [`../cane-coupler/`](../cane-coupler/) the tubes only butt end to end, and the one thing that crosses the joint is a printed tongue:

- **All the bending goes through plastic:** a 10 × 8.5 mm tongue, 20 mm long.
- **Its layer lines run across it** when printed standing up, which is plastic's weakest direction.
- **A 4.2 mm hole runs down its middle** for the cord, leaving walls of about 2 mm.
- **It has a sharp corner at its root,** where the bending is largest; on the motor end, the v4 cross-bolt hole takes more away.
- **It has 0.35 mm of play,** so it rattles and takes knocks.
- **The motor, wheel and battery sit far from the joint.** Lifting the cane by the handle puts an estimated 8 to 12 N·m on an upper joint; the tongue takes about 2 to 4 N·m ([`../joint-sleeve/`](../joint-sleeve/) works these out).

## How this one works

| Part | What it does |
| --- | --- |
| Aluminium spigot | A 130 mm length of 5/8 in × 0.049 in 6061-T6 tube. Glued 65 mm into the upper tube; the other 65 mm slides into the lower tube. It carries all the bending across the joint |
| Collar A | Printed ring glued over the upper tube's end. Two lugs, one wide and one narrow, stick down past the joint |
| Collar B | Printed ring glued over the lower tube's end, with the two matching notches. The lugs stop the sections twisting, and only fit one way, so the wheel always ends up facing forward |
| Shock cord | 1/8 in, through both tubes and the spigot, pulls the sections together |

| | Estimate |
| --- | --- |
| Spigot, bending before it yields | about 47 N·m (section modulus 194 mm³, 240 MPa): about 4 times the 12 N·m load estimate, and about 12 times what the v1 tongue took |
| The carbon tube itself | about 108 N·m (assuming 500 MPa) |
| Spigot to tube clearance | 0.06 mm a side, in a 16.00 mm bore |

## Dimensions

| Feature | Value |
| --- | --- |
| Tubes | Two, 18 mm outside, 16 mm inside, 400 mm long: 800 mm of tube, half of v1's four |
| Spigot | 15.875 mm outside (5/8 in), 1.245 mm wall (0.049 in), 130 mm long |
| Collars | 24 mm outside, 18.3 mm bore (0.15 mm a side for epoxy), 14 mm long |
| Key | Lugs 3 mm tall, 40° and 24° wide; notches 0.25 mm wider a side and 3.3 mm deep |

## Files

| File | What it is |
| --- | --- |
| `model.py` | The source, in build123d. It runs in Connor's ftc-cad CAD workspace (project `sightsense-v2`), which checks it and exports the files below; it does not run on its own here |
| `export/tube_joint.step` | The joint with both tubes, for CAD |
| `export/collar_a_keyed.stl`, `export/collar_b_notched.stl` | The two printed parts, standing as they print |

## Buy

| Qty | Item |
| --- | --- |
| 1 | 6061-T6 aluminium tube, 5/8 in outside, 0.049 in wall, cut to 130 mm |
| 1 | 1/8 in shock cord, as long as both tubes |
| — | Two-part epoxy |

## Building it

1. **Measure the carbon tubes' bore** before buying the spigot. It must be 16.0 mm or a hair more. If the spigot is tight, sand its free half lightly; if it rattles, a turn of thin tape on the free half takes up the play.
2. File a small chamfer round both ends of the spigot so it slides in without catching.
3. Sand the inside of the upper tube's end and the outside of the spigot's glued half, then glue the spigot 65 mm into the upper tube.
4. Glue collar A over the upper tube's end and collar B over the lower tube's end, flush with the tube ends. Push the two together while the glue sets, so the lugs line up with the notches; keep glue off the spigot's free half.
5. Thread the shock cord through both tubes and tie it off at each end.

## Printing

These are suggestions, not tested settings.

- **Material:** PETG-CF or PLA. The collars carry only twisting and hoop loads, not the bending.
- **Orientation:** standing upright, as exported, no supports. Each prints in about 2 g.

## Still to check

1. The carbon tubes' real bore, against the spigot.
2. That the joint does not wobble with the spigot's 0.06 mm clearance, once the cord pulls it closed.
3. How it holds up when the cane is lifted, leaned on and knocked: a load test, with the result written here.

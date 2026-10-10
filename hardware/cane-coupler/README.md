# Cane coupler (keyed, shock-cord, v3)

A two-piece insert that joins two sections of carbon-fibre tube so the cane can fold, like a tent pole. One piece is glued into each tube. A keyed tongue stops the sections twisting against each other, and a hole through the middle carries the shock cord that pulls them together.

The files use the project's earlier working name, PathSense.

## Files

| File | What it is |
| --- | --- |
| `PathSense_Keyed_ShockCord_Main_v3.stl` | Male insert: barrel plus keyed tongue. Glue into tube A. |
| `PathSense_Keyed_ShockCord_Receiver_v3.stl` | Female insert with the matching socket. Glue into tube B. |
| `PathSense_Keyed_ShockCord_Coupler_v3.scad` | OpenSCAD source for both parts. Change `MODE` to export each one. |

## Dimensions (from the `.scad` source)

| Feature | Value |
| --- | --- |
| Tube it fits | 18 mm outside, 16 mm inside, carbon fibre |
| Insert diameter | 15.70 mm (clearance for epoxy) |
| Main insert | 42 mm barrel + 20 mm tongue = 62 mm long |
| Tongue | 10.0 × 8.5 mm, rounded, with a 2 mm tapered tip |
| Receiver insert | 34 mm long |
| Socket | 10.35 × 8.85 mm, 20.5 mm deep, with a wider 2 mm lead-in |
| Tongue-to-socket clearance | 0.35 mm total |
| Shock-cord hole | 4.2 mm, for 1/8 in (3.2 mm) cord |
| Glue grooves | 3 per barrel, 0.35 mm deep, 1.4 mm wide, 8 mm apart |

The STL files were checked against these numbers: the main part measures 15.7 × 15.7 × 62.0 mm and the receiver 15.7 × 15.7 × 34.0 mm.

## Exporting from OpenSCAD

Set `MODE` near the top of the `.scad` file, then render and export:

| `MODE` | Shows |
| --- | --- |
| `"main"` | The male insert only |
| `"receiver"` | The female insert only |
| `"exploded"` | Both parts, spaced apart |
| `"assembled"` | Both parts engaged |
| `"demo"` | Both parts in tube sections with the cord (default) |

## Printing notes

These are suggestions, not tested settings.

- **Material:** PETG-CF. TPU is too soft for this part.
- **Nozzle:** hardened steel, because carbon-fibre filament wears out brass.
- **Walls and infill:** 4 walls or more. The tongue is small enough that it will print nearly solid.
- **Orientation:** the tongue takes the bending load when the cane is leaned on. Printed standing upright, the layer lines run across the tongue, which is its weakest direction. Printing the main insert lying on its side makes the tongue stronger, at the cost of a less round barrel and some support material.
- **Thin wall:** the cord hole leaves about 2.15 mm of wall on the tongue's short side. This is the part most likely to crack.
- **Fit check before gluing:** the insert should slide into the tube with slight resistance, and the tongue should enter the socket without forcing. Adjust `insert_od`, `socket_w` and `socket_h` for your printer and reprint if needed.

## Assembly

1. Lightly sand the inside of each tube end and wipe it clean.
2. Test-fit both inserts dry, with the cord threaded through.
3. Apply epoxy to the barrel and its grooves, push the insert in, and wipe off the excess. Keep epoxy out of the socket and the cord hole.
4. Let it cure fully before loading the joint.

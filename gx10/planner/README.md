# planner

The obstacle check from AGENTS.md, from LiDAR depth only, with numpy. The vision-language model is never involved.

- Seven headings, −30° to +30°, each a 0.7 m corridor. Clearance is the 5th-percentile distance of obstacle points in it.
- Floor: the 5th-percentile height of points within 3 m, if it is 0.3–1.6 m below the camera; otherwise 0.9 m below the camera (estimate for a cane handle). Points less than 15 cm above the floor, or more than 0.6 m above the camera, are not obstacles.
- **Unknown is blocked:** a heading whose wedge of pixels has under 60% good readings (glass, missing depth) has no clearance. A wedge with over 20% of readings nearer than 0.3 m is blocked at 0 m (found by the fake walk: without it, a wall 0.13 m away read as clear).
- Usable from 2.5 m; cost `|heading − desired| + 0.5 · |heading − last|`; nothing usable → `STOP`.
- Smoothing: a change needs 3 agreeing frames, `STOP` 2. `STOP` for 5 s → "Path blocked. Turn slowly to scan."
- Headings are measured in the floor plane from where the camera points (positive right), so the phone's direction in its mount does not matter.

All numbers are starting values at the top of `obstacle.py`, to tune on real recordings.

```bash
../../venv-yolo/bin/python -m unittest planner.test_obstacle   # ray-cast scenes (fake_scene.py)
```

Tested on ray-cast scenes: open floor, a wall 1.5 m ahead, a box to go round, glass, a wall nearer than 0.3 m, a doormat, a phone turned sideways. On one real phone frame (the phone 0.23 m from a laptop) it gave `STOP` in 14.6 ms. Not yet tested on a real walk.

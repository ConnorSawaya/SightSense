# planner

The obstacle check from AGENTS.md, from LiDAR depth only, with numpy. The vision-language model is never involved.

- Seven headings, −30° to +30°, each a 0.7 m corridor. Clearance is the 5th-percentile distance of obstacle points in it.
- Floor: the 5th-percentile height of points within 3 m, if it is 0.3–1.6 m below the camera; otherwise 0.9 m below the camera (estimate for a cane handle). Points less than 15 cm above the floor, or more than 0.6 m above the camera, are not obstacles.
- **Unknown is blocked:** a heading whose wedge of pixels has under 60% good readings (glass, missing depth) has no clearance. A wedge with over 20% of readings nearer than 0.3 m is blocked at 0 m (found by the fake walk: without it, a wall 0.13 m away read as clear).
- Usable from 1.5 m (was 2.5 m, too cautious on the cane). Nothing usable: steer slowly to the most open heading if it is open past 0.8 m (1.0 m to leave STOP), else `STOP`. On the October 10 evening walk STOP fell from 82% of the time (old) to 28%, and what still stopped was about 0.3 m away. Cost `|heading − desired| + 0.5 · |heading − last|`.
- Smoothing: a change needs 3 agreeing frames, `STOP` 2. `STOP` for 5 s → "Path blocked. Turn slowly to scan."
- Direction cues (`cue.py`): the phone is told which way to go (`LEFT`, `STRAIGHT`, `RIGHT`, `STOP`, `UNKNOWN`, the same as the wheel), with a sound only when it changes. "Bear left" / "Bear right" with a tone in that ear, once; straight ahead is silent; one stop tone per stop, and none for the STOP every session starts in unless the depth says stop; at most one spoken direction every 2 s and the same one not again within 4.5 s (longer than the phone's own hold on a repeated sentence). Before this the stop beep came with every frame and indoors it beeped nearly all the time.
- Phone state (`state.py`), for the colours on screen only: STOP follows the command at once both ways (leaving STOP goes to CAUTION first). CAUTION needs 2 frames; back to CLEAR needs the way ahead past 1.8 m (1.5 m + 0.3 m) for 15 frames in a row (about 1 s), judged by the nearest reading of the last 8 frames. Before this, holding the phone still about 2.5 m from something flickered CLEAR/CAUTION and replayed the caution earcon (iPhone test, October 10).
- Headings are measured in the floor plane from where the camera points (positive right), so the phone's direction in its mount does not matter.

All numbers are starting values at the top of `obstacle.py`, to tune on real recordings.

```bash
../../venv-yolo/bin/python -m unittest planner.test_obstacle   # ray-cast scenes (fake_scene.py)
../../venv-yolo/bin/python -m unittest planner.test_state   # state hold (imports obstacle.py, so needs numpy)
python3 -m unittest planner.test_cue                         # direction cues: when the phone is told what
```

Tested on ray-cast scenes: open floor, a wall 1.5 m ahead, a box to go round, glass, a wall nearer than 0.3 m, a doormat, a phone turned sideways. On one real phone frame (the phone 0.23 m from a laptop) it gave `STOP` in 14.6 ms. Not yet tested on a real walk.

## The ground, and where the phone has to point

Checked on October 11 on ray-cast scenes with depth noise added (about 1 cm plus 1% of the distance, an estimate for the phone's LiDAR), on a laptop. Not on recordings from the phone. `test_obstacle.py` (class `Floor`) repeats the main cases.

- **A level floor is never taken for an obstacle.** 504 poses: the phone 0.6 to 1.4 m up, tilted 5 to 70 degrees down, upright, on either side or upside down, with and without noise and missing far readings. No obstacle point and no command other than CENTER in any pose where the way ahead could be judged.
- **Tilt the phone at least 25 degrees below the horizon.** LiDAR reaches about 5 m. With less tilt, in open space most of the view is floor further away than that, with no reading, and no reading counts as blocked: at 15 degrees most heights give "Can't see ahead" and STOP, at 10 degrees all do. In a room with walls inside 5 m it matters less. 25 and 30 degrees worked at every height tried (0.6 to 1.4 m).
- **Ground that falls away reads as blocked.** If the floor drops more than about 3 degrees ahead, or a twentieth of the nearby readings are lower than the floor (a step down, a drop-off, a mirror-like floor; this part is from how the floor is found, not from a run), the floor is put too low and the ground at the feet reads as an obstacle about 0.8 m ahead. That is wrong about the ground but on the side of stopping, so it is left as it is. A ramp up of 5 degrees reads as something 2.3 m ahead and does not stop the cane; 10 degrees reads 1.6 m.
- **Low things.** A thing 15 cm high or more is seen out to 3 m. 10 cm is seen at 1 m only. 5 cm is not seen. The cane does not handle kerbs, steps or drop-offs.
- **The cane's own lower end.** The mount's own check of the camera's view covers only the top 360 mm of the tube. By the geometry, at the 60 degree step with the phone upright the motor, wheel and Pi clamp are at the very bottom edge of the depth picture, and at 75 degrees they are well inside it (an estimate; not looked at on the cane). Anything of the cane in view reads as an obstacle about 0.4 m ahead for ever. Look at the depth picture on the dashboard with open floor ahead: every bar should read 4.5. If the middle bars read under 1 m with nothing there, start the service with `SIGHTSENSE_OWN_CANE_M=0.65` (the distance along the floor from the phone to the cane's tip). That ignores a strip 24 cm wide and that long straight ahead, never as far as the 0.8 m stop distance. A wall, a wide box, or a post further off are still seen. It is off by default, because with nothing of the cane in view it would only hide a thin post nearer than the tip.
- The dashboard and the once-a-second line now show how far the floor is below the phone (`floor 0.92m`, or `n` when no floor is seen). If that number jumps about, or is far from the phone's real height, the floor is being misjudged.

## Steering round things

Checked on October 11 with a simulated walker that follows the wheel (LEFT or RIGHT turns them 30 degrees a second), on ray-cast scenes with depth noise, on a laptop. `test_walk.py` repeats five of them. Not a test on the cane.

| Scene | What happened |
| --- | --- |
| A box in the path, room either side | Steered round it, no stop |
| A person-sized thing a little right of centre | Steered left of it, no stop |
| A doorway 1.0 m wide straight ahead | Straight through, no turn |
| The same doorway 0.6 m to the right | Steered right and through, no stop |
| A corridor 1.6 m wide with a box on the left | Steered past it, no stop |
| Two boxes staggered | Steered round both, no stop |
| A wall right across | Turned and walked along the wall. Someone who ignores the wheel and keeps walking is stopped about 0.75 m from it |

The same with the phone upright or on its side. The walker passed 0.28 to 0.33 m from the nearest edge, measured from the middle of the walker, which is close: the corridor the check keeps clear is 0.7 m wide. So when the cane stops a lot, look first at the phone's tilt and at whether the cane or a hand is in its view (the section above), not at the steering rules.

# ingest

The GX10 frame service. Receives the phone's frames, runs the obstacle check, YOLO and the navigator on the newest one, and sends guidance back to the phone and a command to the Pi for every processed frame.

First version, written by the GX10 + models owner to get the end-to-end loop going; the obstacle check owner may replace any of it.

## Run

```bash
cd ~/SightSense-work/SightSense/gx10
export YOLO_CONFIG_DIR=~/SightSense-work/.ultralytics
../../venv-yolo/bin/python -m ingest.server                       # phone 8765, Pi 8766
../../venv-yolo/bin/python -m ingest.server --record ../../recordings   # also save every frame and voice message
../../venv-yolo/bin/python -m ingest.server --no-yolo --phone-port 8775 --pi-port 8776
```

It needs the project virtual environment (numpy, OpenCV, YOLO, `websockets`); see `../detector/README.md`. Ports can also be set with `SIGHTSENSE_PHONE_PORT` and `SIGHTSENSE_PI_PORT`. Nothing is hard-coded to an address: the phone and the Pi connect to whatever address the GX10 has.

In the app, enter the GX10's address on the network the phone is on, e.g. `169.233.72.156:8765` on the venue Wi-Fi (the GX10's address there on October 10). Keep the phone on the same Wi-Fi: over a hotspot the first test got 0.3–0.7 frames a second.

## What it does with each frame

1. Keeps only the newest frame; any older one still waiting is dropped and counted.
2. Turns the picture upright for YOLO and the vision-language model using gravity from the pose (`upright.py`); boxes are mapped back to the original picture, which the depth lines up with. With the phone upright on the cane the picture arrives turned 90°.
3. YOLO → navigator → obstacle check (`../planner/`), with the navigator's desired bearing.
4. Sends the phone `{"seq", "state", "earcon", "speech"}` (and `{"lookup": ...}` when needed) and the Pi `{"seq", "cmd", "ttl_ms": 400}`.
5. After a gap of more than 1 s it starts again from `STOP`.

Prints one line a second: frames in, processing time, command, state, clearance per heading, navigator state, detections, Pis connected, frames dropped.

## Test without the phone

```bash
../../venv-yolo/bin/python -m unittest ingest.test_upright
../../venv-yolo/bin/python -m ingest.fake_phone --port 8775 --pi-port 8776                # walk at a wall
../../venv-yolo/bin/python -m ingest.fake_phone --port 8775 --say "what is in front of me"
../../venv-yolo/bin/python -m ingest.fake_phone --port 8775 --replay ../../recordings/<session>
```

Result on the GX10, October 10 (fake walk at 0.5 m/s toward a wall 4 m away, YOLO on):

```
  seq    3  CLEAR     earcon None    speech None  (wall 3.93 m)
  seq   46  CAUTION   earcon caution speech None  (wall 2.50 m)
  seq   53  STOP      earcon stop    speech 'Obstacle ahead. Stop.'  (wall 2.27 m)
120 frames sent, 120 guidance replies
send -> guidance back: median 10 ms, max 41 ms (local, includes processing)
pi got 120 commands: STOP -> CENTER -> LEFT -> STOP
```

The 10 ms is on the GX10 only; the phone-to-GX10 network and the phone's own delay come on top and have not been measured.

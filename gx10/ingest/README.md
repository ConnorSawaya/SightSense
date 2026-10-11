# ingest

The GX10 frame service. Receives the phone's frames, runs the obstacle check, YOLO and the navigator on the newest one, and sends guidance back to the phone and a command to the Pi for every processed frame.

First version, written by the GX10 + models owner to get the end-to-end loop going; the obstacle check owner may replace any of it.

## Run

```bash
cd ~/SightSense-work/SightSense/gx10
export YOLO_CONFIG_DIR=~/SightSense-work/.ultralytics
../../venv-yolo/bin/python -m ingest.server --phone-port 8775                          # for the cane: phone 8775, Pi 8766
../../venv-yolo/bin/python -m ingest.server --phone-port 8775 --record ../../recordings   # also save every frame and voice message
../../venv-yolo/bin/python -m ingest.server                                            # the ports in the contract: phone 8765, Pi 8766
../../venv-yolo/bin/python -m ingest.server --no-yolo --phone-port 18775 --pi-port 18776 --dashboard-port 0   # a second copy for tests, beside the live one (dashboard off: the live one holds 8000)
```

**Use the first line for the cane.** The app's presets connect to port 8775 and the Pi is set up for 8766, so one service started with `--phone-port 8775` serves both. Checked on the GX10 over Tailscale on October 11 at 8:50 AM, from a laptop: 8775, 8766 and the dashboard on 8000 are one running service (a silent test client on 8775 showed as the phone in the dashboard's status, and one on 8766 as a Pi). Port 8765 also accepts connections but is not that service, so do not point the phone at it. The service running then was older code than this branch.

If Ollama is not running the service still starts, prints `vision-language model NOT loaded`, and guides from depth; describe, read and find fail until Ollama is up and the service is restarted.

Set `SIGHTSENSE_OWN_CANE_M=0.65` before starting if the cane's own lower end shows in the depth picture and holds the cane at STOP; see "The ground, and where the phone has to point" in `../planner/README.md`. The service prints whether it is on when it starts.

Each press of the cane's talk button shows in the dashboard's conversation as `(talk button down: phone told to listen)`, or `no phone connected`, so the button and its wiring can be checked from the dashboard without the phone.

It needs the project virtual environment (numpy, OpenCV, YOLO, `websockets`); see `../detector/README.md`. Ports can also be set with `SIGHTSENSE_PHONE_PORT` and `SIGHTSENSE_PI_PORT`. Nothing is hard-coded to an address: the phone and the Pi connect to whatever address the GX10 has.

In the app, enter the GX10's address on the network the phone is on, e.g. `169.233.72.156:8775` on the venue Wi-Fi (the GX10's address there on October 10). Keep the phone on the same Wi-Fi: over a hotspot the first test got 0.3–0.7 frames a second.

## What it does with each frame

1. Keeps only the newest frame; any older one still waiting is dropped and counted.
2. Turns the picture upright for YOLO and the vision-language model using gravity from the pose (`upright.py`); boxes are mapped back to the original picture, which the depth lines up with. With the phone upright on the cane the picture arrives turned 90°.
3. YOLO → navigator → obstacle check (`../planner/`), with the navigator's desired bearing.
4. Sends the phone `{"seq", "state", "direction", "earcon", "speech"}` (and `{"lookup": ...}` when needed). The Pi command keeps the same `seq`, `cmd`, `ttl_ms` fields, but its TTL is the remainder of the frame's 400 ms receive-time budget. Expired frames send no motor command. Slow Pi peers are closed without holding up other peers.
5. After a gap of more than 1 s it starts again from `STOP`.

The cane's talk button: the Pi sends `{"button": "down"}` and `{"button": "up"}` on its connection. Down sends the phone `{"listen": true}`. Up sends `{"listen": false}` only if the button was held for 0.6 s or longer; after a shorter click the phone stops listening by itself. What the phone heard comes back as an ordinary `{"text": ...}` message. Tested with stand-ins for the Pi and the phone (`ingest.test_talk_button`), not with the real ones.

Prints one line a second: frames in, processing time, command, state, clearance per heading, navigator state, detections, Pis connected, frames dropped.

## Test without the phone

```bash
../../venv-yolo/bin/python -m unittest ingest.test_upright
../../venv-yolo/bin/python -m ingest.fake_phone --port 18775 --pi-port 18776              # walk at a wall, against the test copy above
../../venv-yolo/bin/python -m ingest.fake_phone --port 18775 --say "what is in front of me"
../../venv-yolo/bin/python -m ingest.fake_phone --port 18775 --replay ../../recordings/<session>
```

Result on the GX10, October 10, with the obstacle check as it was then (usable from 2.5 m, a caution beep; fake walk at 0.5 m/s toward a wall 4 m away, YOLO on):

```
  seq    3  CLEAR     earcon None    speech None  (wall 3.93 m)
  seq   46  CAUTION   earcon caution speech None  (wall 2.50 m)
  seq   53  STOP      earcon stop    speech 'Obstacle ahead. Stop.'  (wall 2.27 m)
120 frames sent, 120 guidance replies
send -> guidance back: median 10 ms, max 41 ms (local, includes processing)
pi got 120 commands: STOP -> CENTER -> LEFT -> STOP
```

Since then the check counts a heading usable from 1.5 m and stops inside 0.8 m, and direction cues replaced the caution beep. The same walk on October 11 (a Windows laptop, YOLO off, Ollama not running; not re-run on the GX10):

```
  seq    1  STOP      earcon None    speech None  (wall 4.00 m)
  seq    3  CAUTION   earcon None    speech None  (wall 3.93 m)
  seq   18  CLEAR     earcon None    speech None  (wall 3.43 m)
  seq   77  CAUTION   earcon None    speech None  (wall 1.47 m)
  seq   80  CAUTION   earcon right   speech 'Bear right'  (wall 1.37 m)
  seq   98  STOP      earcon stop    speech 'Obstacle ahead. Stop.'  (wall 0.77 m)
120 frames sent, 120 guidance replies
pi got 120 commands: STOP -> CENTER -> RIGHT -> CENTER -> STOP
```

The 10 ms is on the GX10 only; the phone-to-GX10 network and the phone's own delay come on top and have not been measured.

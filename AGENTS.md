# SightSense — context for AI coding assistants

Read this file first. It tells you what the project is, what has been decided, what exists, and the rules you must not break. The reasons behind each decision and how the plan changed over time are in [`docs/PROJECT_HISTORY.md`](docs/PROJECT_HISTORY.md).

## What this is

A smart guide cane for people who are blind or have low vision, built by a four-person team at the UCSC AI Hackathon @ SF Tech Week (October 10–11, 2026) for the ASUS Local AI track.

- An **iPhone 16 Pro** on the cane captures the camera picture, LiDAR depth and position.
- An **ASUS Ascent GX10** on the team's table does all the thinking.
- A **Raspberry Pi 5** on the cane drives the mecanum wheel at the tip. The user confirmed direct wheel drive on October 11: opposite motor directions produce left/right guidance.
- The user says "guide me to the apple", "take me to the door" or "take me to Safeway"; the cane confirms, then steers them there around obstacles.

```
iPhone ──frame (JPEG + depth + pose + GPS)──► GX10 ──LEFT/CENTER/RIGHT/STOP──► Pi ──► motor ──► wheel
   ▲                                           │
   └──────────── beeps and speech ◄────────────┘
```

## Current status

| Area | State |
| --- | --- |
| Repo layout, message formats, wiring plan | Documented in this repository |
| Cane parts (`hardware/`) | CAD designs and assembly notes are included; verify fit and strength on the actual build |
| iPhone app (`ios-app/`) | Camera, LiDAR, frame transport, guidance, speech and location code are present; verify the current build on a supported iPhone |
| GX10 software (`gx10/`) | Ingest, planner, dashboard, model, navigation and detection modules are present; validate the current integration on the target GX10 |
| Pi motor controller (`pi/`) | Direct-wheel mode, command watchdog, setup tools and mock tests are present; verify motor direction and hardware behavior before use |
| Whole-system checks | Use the synthetic phone, simulated walk and mock GPIO tests; do not claim a physical end-to-end result unless it has been observed |
| Bill of materials ([`hardware/BOM.md`](hardware/BOM.md)) | Collected from the hardware pages on October 12; no prices or shop links |
| 3D pictures and model page | README pictures in `docs/media/` and a GitHub Pages page (`gh-pages` branch) that shows the interactive model. Made on October 12, after the event; see `docs/DISCLOSURE.md` |
| Result | 1st place overall at the UCSC AI Hackathon @ SF Tech Week, as reported by the team |

Update this table when you finish something.

## Rules you must not break

These come from the hackathon and from the team. Breaking one can get the project disqualified.

1. **No pre-event code or parts without confirmation.** Hacking started at 12:00 PM on October 10, 2026. The organizers have not confirmed in writing whether earlier work is allowed. Do not copy code in from anywhere outside this repository unless the user says the organizers approved it, and then record it in `docs/DISCLOSURE.md`.
2. **Never fabricate history.** Do not backdate commits, invent commit history, or claim work was done at a time it was not.
3. **The project must be developed and demoed on the GX10.** All AI inference and all guidance decisions run there. Do not move inference to a laptop, the phone or the cloud.
4. **The vision-language model never controls the wheel.** It finds objects, reads text and answers questions. Whether the way is clear is decided from LiDAR depth only. If the two disagree, depth wins.
5. **Unknown is not clear.** A direction with too few good depth readings counts as blocked.
6. **Fail safe.** The Pi switches the motor driver off if no command arrives for 0.4 seconds. Never send raw motor power over the network.
7. **No cloud AI.** Devices already use Tailscale for transport; place lookup uses Apple MapKit. Do not add any other cloud service.
8. **No secrets in the repo.** No passwords, tokens, Wi-Fi keys or Apple credentials. Use environment variables.
9. **Do not change system settings on the GX10.** It is borrowed. Keep project files in one folder.
10. **Report honestly.** Say only that something works if you ran it. Label estimates as estimates.
11. **Safety claims.** This is an experimental supplement to a white cane, tested with a sighted observer. Never describe it as safe for independent travel, and never claim it handles stairs, kerbs, drop-offs or street crossings.

## How to work in this repo

- Do one small task at a time. Read the files you will change before editing.
- Message formats live in [`contracts/MESSAGES.md`](contracts/MESSAGES.md). Do not change them without the user's say-so; four people build against them.
- Every piece must run against a fake version of what it depends on (recorded frames, typed commands, a simulated walk), so nobody waits on anybody.
- Work on a branch and open a pull request; do not push to `main` directly.
- Run what you write. Report which files changed and what you tested.
- Match the plain, short style of the existing READMEs.
- Ask before adding a dependency. On the GX10, prefer ready-made containers; it has an ARM64 processor and many Python packages lack builds for it.

## Machines

| Machine | Role | Notes |
| --- | --- | --- |
| ASUS Ascent GX10 | AI inference and guidance host | NVIDIA GB10, ARM64 Linux (DGX OS) |
| Raspberry Pi 5 | Motor controller | Raspberry Pi OS Lite 64-bit; use `gpiozero` + `lgpio` |
| iPhone 16 Pro | Camera, LiDAR, position and voice input | Requires a supported iPhone and a signed app build |
| Development computers | Build and maintenance | Keep actual hostnames, addresses and credentials in local configuration, outside Git |

Device addresses depend on the local router or Tailscale network. Use the GX10's local DNS name, MagicDNS name or assigned address in local configuration. The phone frame service uses port 8775 in the cane setup; the Pi command connection uses port 8766. The dashboard and model service use ports 8000 and 11434 on the GX10.

## Decisions already made

| Topic | Decision |
| --- | --- |
| Transport | WebSocket. One binary message per camera frame holding picture, depth and position together. No WebRTC, no video codec. |
| Capture | Own ARKit app. Fallback: the Record3D streaming app (no voice or maps on the fallback). |
| Network | Planned: the team's own router, no internet needed. The router was not at the venue; the Pi is on a phone hotspot and the network for the whole system is not settled. See Known traps. |
| Depth | iPhone LiDAR (`sceneDepth`). No depth model. |
| Vision-language model | `qwen3-vl:30b` through Ollama; `qwen3-vl:8b` as the fast fallback. Check what the preloaded Nemotron can do first. Exact Ollama tag names are unverified. |
| Detector | Ultralytics YOLO (YOLO26s or YOLO11s) in the `ultralytics/ultralytics:latest-nvidia-arm64` container, exported to TensorRT. |
| Obstacle check | Seven headings from −30° to +30°, chosen every frame from depth. |
| Wheel | User confirmed October 11: one 12 V 120 rpm gear motor directly drives the mecanum wheel. LEFT and RIGHT spin opposite ways; CENTER/STOP/FREE switch off. Use `--wheel-drive`; `--swap` reverses the physical mapping. No position switches or homing in this mode. |
| Motor driver | IBT-2 board (BTS7960). The plan said L298N; the IBT-2 is what the team has. It passes the full 12 V, so the software limits are the only limits. |
| Power | 12 V 3 Ah pack → fuse → kill switch → IBT-2. Pi from the same pack through a 12 V to 5 V USB-C converter; back to its own power bank if the motor makes it reset. Grounds joined. |
| Voice | Push-to-talk, on-device speech recognition on the iPhone. A text box on the dashboard does the same job if voice is not ready. |
| Places | Apple MapKit walking directions, looked up on the phone. |
| Cane | 18 mm carbon-fibre tube sections joined by the printed keyed coupler. |
| Printing | PETG-CF for rigid parts, TPU for pads and the tyre. |

## The algorithms, with starting numbers

Every number is a starting value to tune, not a measured result.

### Obstacle check (every frame, GX10)

Input: a depth frame and a desired bearing in degrees relative to the camera (0 = straight ahead).

1. Keep depth pixels with medium or high confidence, between 0.3 and 4.5 m.
2. For pixel column `u`, row `v`, distance `z`: `x = (u − cx) · z / fx` (metres right), `y = (cy − v) · z / fy` (metres up).
3. Drop the floor (lower than 15 cm above the ground) and anything more than about 0.6 m above the camera.
4. Candidate headings: −30, −20, −10, 0, 10, 20, 30 degrees.
5. Each heading has a corridor 0.7 m wide. Clearance = 5th-percentile distance of points inside it (at least 30 points; none means clear to range).
6. A corridor with under 60% valid depth pixels is unknown, which counts as blocked.
7. Usable if clearance ≥ 1.5 m (2.5 m until October 10, which stopped about 2.2 m from things).
8. Choose the usable heading with the lowest cost: `|heading − desired| + 0.5 · |heading − last choice|`.
9. Nothing usable: steer towards the most open heading if it is open past 0.8 m (1.0 m once stopped); otherwise `STOP`.
10. Wheel: ≤ −15° → `LEFT`; ≥ +15° → `RIGHT`; else `CENTER`.
11. A change needs 3 agreeing frames; `STOP` needs 2.
12. `STOP` for 5 seconds → say "Path blocked. Turn slowly to scan."

Build it first with three headings and a desired bearing of 0.

### Guide to an object ("guide me to the apple")

1. Ask the vision-language model for a box around the named object.
2. Distance = median LiDAR depth inside the box. Bearing = `atan((u − cx) / fx)` at the box centre.
3. Confirm aloud: "Apple, 3 metres, slightly left. Say yes to go."
4. Store the target as a point in the ARKit world frame; recompute its bearing from the pose every frame.
5. Feed that bearing to the obstacle check as the desired bearing.
6. Re-run the find every 2 seconds (1.5 while scanning). For objects YOLO knows, use YOLO's box every frame.
7. Not seen for 10 seconds with no stored point → "I lost the apple."
8. Under 1.2 m → `STOP` and "The apple is within reach." (0.8 m until October 11; it has to be more than the 0.8 m of the obstacle stop.)

### Route follower ("take me to Safeway", about once a second)

1. Nearest point on the route line, then the point 12 m further along.
2. Desired bearing = bearing to that point − phone heading, wrapped to ±180°.
3. More than 60° off → say "Turn left/right" and hold `CENTER`.
4. Speak a step within 10 m of it. Arrived within 15 m of the destination.
5. Off route: farther than `max(15 m, 2 × gps_acc_m)` for 5 seconds → new lookup, "Rerouting."
6. GPS accuracy worse than 25 m → stop sending a desired bearing.

### Pi motor controller

See [`pi/README.md`](pi/README.md) and [`hardware/wiring.md`](hardware/wiring.md). Direct wheel mode: duty ≤ 25%, pulses ≤ 0.4 s with 50 ms rests, opposite directions for LEFT/RIGHT, all other commands off. Reverse only after a rest. Finite TTL required; silence or disconnection switches off. The earlier position-steering modes remain available separately. RPM is unmeasured without an encoder or counted-turn measurement.

### Prompts for the vision-language model

- Describe: "In under 20 words, say what is directly ahead of the camera. Do not estimate distances."
- Read: "Read any text or signs in this image. If there is none, reply NONE."
- Find: "Locate the apple. Reply only as JSON with bbox_2d as [x1, y1, x2, y2] and a label, or bbox_2d as null." The coordinates may be on a 0–1000 scale, not pixels; verify on a test picture.

One request at a time, 6-second timeout, keep the model loaded.

## Known traps

- **Picture direction.** ARKit's picture and depth are in the sensor's landscape direction. If the phone is mounted upright, data arrives turned 90° and left/right become up/down. Test with a hand on one side.
- **Intrinsics.** ARKit gives them for the full camera picture; scale them to the depth picture's size.
- **Depth size.** Commonly 256 × 192 but unverified; read it from the buffer.
- **Never queue frames.** Keep only the newest; skip a send if the last one has not finished.
- **Thinking mode.** If the model's reply starts with reasoning, turn thinking off; it adds seconds.
- **Slow model.** A few tokens per second means the setup is wrong, not the model. Check `ollama ps`.
- **Empty is not clear.** No points in a corridor can mean open space or missing readings.
- **Stale targets.** If ARKit tracking resets, stored positions are wrong. Clear them.
- **Pi resets when the motor starts.** The Pi now shares the motor's battery through a converter. If it resets or reports under-voltage when the motor runs, put it back on its own power bank.
- **Network setup.** A headless Pi needs a trusted network without a captive portal. Provide Wi-Fi credentials through a private NetworkManager profile and keep that profile out of Git. Use addresses assigned by the router or Tailscale; do not put active host addresses in examples.
- **Pi will not start.** Count the green light's blinks before changing anything else. Three long and one short is a bootloader error; the fix is in [`pi/README.md`](pi/README.md).
- **Phone tilt.** The phone has to look at least 25 degrees below the horizon. With less, in open space the obstacle check cannot judge the way ahead and stops ("Can't see ahead"). On the printed mount that is the 60 degree step, not the 45 the drawings show.
- **The cane in its own view.** Anything fixed in the depth picture (the cane's lower end, a hand, a strap) reads as an obstacle about 0.4 m ahead for ever. With open floor ahead every clearance bar on the dashboard should read 4.5. `SIGHTSENSE_OWN_CANE_M=0.65` ignores the cane's own strip; see `gx10/planner/README.md`.
- **Pi under-voltage.** A weak supply or long cable makes the Pi throttle and can reset it. `vcgencmd get_throttled` should print `0x0`.

## Priorities

**Must work:** obstacle stop with a measured delay · "guide me to the object" in a room · describe and read · dashboard (live view, decision, delay, GPU use) · wheel free when the link drops.

**Aiming for:** the wheel · voice commands · "take me to a place" with route following.

**If there is time:** automatic re-routing · person tracking · wake word.

**Cut in this order when behind:** wake word → person tracking → automatic re-routing → place routing → voice → wheel → YOLO.

## Checkpoints (Saturday October 10)

| Time | Must be true |
| --- | --- |
| 2:30 PM | A live frame from the phone shows on the GX10. If not, switch to the streaming app. |
| 5:00 PM | A real obstacle makes it beep "stop", with the delay measured. |
| 7:00 PM | "Guide me to the apple" works in the room. The wheel follows live guidance or leaves the demo. |
| 8:30 PM | Feature freeze. Bug fixes only. |
| 10:00 PM | Venue closes. The GX10 stays. |

Sunday: test at 9:00 AM, code freeze 11:00 AM, submit on Devpost by 12:45 PM (deadline 1:30 PM), judging at the table at 2:00 PM, hardware returned at 3:45 PM.

## Open questions

- Organizers: earlier code or parts, own router, 3D printer, whether finalists keep the GX10 past 3:45 PM, which Nemotron is preloaded.
- Does the iPhone keep cellular internet while on the no-internet router (needed for the place lookup)?
- Do MapKit directions work under a free Apple ID?
- Can the battery pack handle the motor at stall, and does the Pi stay up when it shares that pack?
- The motor has a worm gear and holds its position with the driver off. Is "driver off" still the right response to a dropped link, or should the wheel be centred first?
- All delays: typical estimates are 0.3–0.45 s for a stop beep and 1.5–3 s for a model answer. Replace with measurements.

## Where to find more

- [`docs/PROJECT_HISTORY.md`](docs/PROJECT_HISTORY.md): how the plan got here and why.
- [`contracts/MESSAGES.md`](contracts/MESSAGES.md): message formats between the phone, GX10 and Pi.
- [`pi/README.md`](pi/README.md): Pi setup and operation.
- [`hardware/BOM.md`](hardware/BOM.md): everything the cane is built from.
- [3D model](https://connorsawaya.github.io/SightSense/): the interactive model and guided tour.

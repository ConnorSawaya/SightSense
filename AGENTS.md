# SightSense — context for AI coding assistants

Read this file first. It tells you what the project is, what has been decided, what exists, and the rules you must not break. The reasons behind each decision and how the plan changed over time are in [`docs/PROJECT_HISTORY.md`](docs/PROJECT_HISTORY.md).

## What this is

A smart guide cane for people who are blind or have low vision, built by a four-person team at the UCSC AI Hackathon @ SF Tech Week (October 10–11, 2026) for the ASUS Local AI track.

- An **iPhone 16 Pro** on the cane captures the camera picture, LiDAR depth and position.
- An **ASUS Ascent GX10** on the team's table does all the thinking.
- A **Raspberry Pi 5** on the cane turns a small steering wheel at the tip.
- The user says "guide me to the apple", "take me to the door" or "take me to Safeway"; the cane confirms, then steers them there around obstacles.

```
iPhone ──frame (JPEG + depth + pose + GPS)──► GX10 ──LEFT/CENTER/RIGHT/STOP──► Pi ──► motor ──► steering wheel
   ▲                                           │
   └──────────── beeps and speech ◄────────────┘
```

## Current status

As of the commit that added this file, the repository holds structure and documentation only. No application code has been written yet.

| Area | State |
| --- | --- |
| Repo layout, message formats, wiring plan | Written |
| Cane coupler (`hardware/cane-coupler/`) | Designed, STL checked against source, not printed |
| iPhone app (`ios-app/`) | Not started |
| GX10 software (`gx10/`) | Not started |
| Pi motor controller (`pi/`) | Not started |
| Handle and phone mount (`hardware/handle-phone-mount/`) | Designed, geometric checks only, not printed; cradle is oversize and the phone is strapped in |
| Motor bracket, Pi plate | Not designed |

Update this table when you finish something.

## Rules you must not break

These come from the hackathon and from the team. Breaking one can get the project disqualified.

1. **No pre-event code or parts without confirmation.** Hacking started at 12:00 PM on October 10, 2026. The organizers have not confirmed in writing whether earlier work is allowed. Do not copy code in from anywhere outside this repository unless the user says the organizers approved it, and then record it in `docs/DISCLOSURE.md`. Earlier project folders named `PathSense` and `PathSense-iOS` exist on the user's home desktop; they have not been imported.
2. **Never fabricate history.** Do not backdate commits, invent commit history, or claim work was done at a time it was not.
3. **The project must be developed and demoed on the GX10.** All AI inference and all guidance decisions run there. Do not move inference to a laptop, the phone or the cloud.
4. **The vision-language model never controls the wheel.** It finds objects, reads text and answers questions. Whether the way is clear is decided from LiDAR depth only. If the two disagree, depth wins.
5. **Unknown is not clear.** A direction with too few good depth readings counts as blocked.
6. **Fail safe.** The Pi switches the motor driver off if no command arrives for 0.4 seconds. Never send raw motor power over the network.
7. **No cloud AI.** The only internet use is the Apple MapKit place lookup. Do not add any other cloud service.
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

| Machine | Where | Notes |
| --- | --- | --- |
| ASUS Ascent GX10 | Venue, on the team's router by Ethernet | NVIDIA GB10, 128 GB shared memory, ARM64 Linux (DGX OS). Stays at the venue; closes 10 PM Saturday. |
| Raspberry Pi 5 | On the cane, on the team's router | Raspberry Pi OS Lite 64-bit. No audio jack. Use `gpiozero` + `lgpio`; `RPi.GPIO` and `pigpio` do not work on a Pi 5. |
| iPhone 16 Pro | On the cane | App built on a teammate's Mac with Xcode, free Apple ID (7-day signing). |
| Mac | Venue | Only for building the iPhone app. |
| Team laptops | Venue | Development, SSH to the Pi and GX10. |
| Home desktop | Not at the venue | i7-14700F, RTX 4060 (8 GB), 32 GB RAM, Windows 11. Cannot reach the Pi or GX10. Useful for testing the 8B model and for overnight tuning on recordings. |

Planned addresses (reserve in the router; the subnet depends on the router): GX10 `192.168.8.10`, Pi `192.168.8.20`, iPhone `192.168.8.30`. Ports on the GX10: 8765 frames in, 8766 commands out, 8000 dashboard, 11434 Ollama.

## Decisions already made

| Topic | Decision |
| --- | --- |
| Transport | WebSocket. One binary message per camera frame holding picture, depth and position together. No WebRTC, no video codec. |
| Capture | Own ARKit app. Fallback: the Record3D streaming app (no voice or maps on the fallback). |
| Network | The team's own router, no internet needed. |
| Depth | iPhone LiDAR (`sceneDepth`). No depth model. |
| Vision-language model | `qwen3-vl:30b` through Ollama; `qwen3-vl:8b` as the fast fallback. Check what the preloaded Nemotron can do first. Exact Ollama tag names are unverified. |
| Detector | Ultralytics YOLO (YOLO26s or YOLO11s) in the `ultralytics/ultralytics:latest-nvidia-arm64` container, exported to TensorRT. |
| Obstacle check | Seven headings from −30° to +30°, chosen every frame from depth. |
| Wheel | One 12 V 120 rpm gear motor steers a normal free-rolling wheel to three positions with limit switches. Not a mecanum wheel. |
| Motor driver | L298N (about 2 A, loses about 2 V). |
| Power | 12 V 3 Ah pack → fuse → kill switch → L298N. Pi on its own USB-C power bank. Grounds joined. |
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
7. Usable if clearance ≥ 2.5 m.
8. Choose the usable heading with the lowest cost: `|heading − desired| + 0.5 · |heading − last choice|`.
9. Nothing usable, or under 1.2 m straight ahead with no usable side → `STOP`.
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
8. Under 0.8 m → `STOP` and "The apple is within reach."

### Route follower ("take me to Safeway", about once a second)

1. Nearest point on the route line, then the point 12 m further along.
2. Desired bearing = bearing to that point − phone heading, wrapped to ±180°.
3. More than 60° off → say "Turn left/right" and hold `CENTER`.
4. Speak a step within 10 m of it. Arrived within 15 m of the destination.
5. Off route: farther than `max(15 m, 2 × gps_acc_m)` for 5 seconds → new lookup, "Rerouting."
6. GPS accuracy worse than 25 m → stop sending a desired bearing.

### Pi motor controller

See [`pi/README.md`](pi/README.md) and [`hardware/wiring.md`](hardware/wiring.md). Duty ≤ 25%, each move ≤ 0.4 s, stop on switch, home to centre at start and after any timeout.

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
- **Pi resets when the motor starts.** Keep the Pi on its own power bank and fit the capacitor.

## Priorities

**Must work:** obstacle stop with a measured delay · "guide me to the object" in a room · describe and read · dashboard (live view, decision, delay, GPU use) · wheel free when the link drops.

**Aiming for:** steering wheel · voice commands · "take me to a place" with route following.

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
- Can the L298N and the battery pack handle the motor at stall?
- All delays: typical estimates are 0.3–0.45 s for a stop beep and 1.5–3 s for a model answer. Replace with measurements.

## Where to find more

- [`docs/PROJECT_HISTORY.md`](docs/PROJECT_HISTORY.md): how the plan got here and why.
- [SightSense Team Handbook](https://claude.ai/code/artifact/25e30a5a-561f-4f03-b7df-020e1d7d422b): the full plan in plain language, with the build guide, tests and checklists. The link is private until its owner shares it; if you cannot open it, ask the user to paste the part you need.

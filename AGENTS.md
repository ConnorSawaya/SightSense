# SightSense — context for AI coding assistants

Read this file first. It tells you what the project is, what has been decided, what exists, and the rules you must not break. The reasons behind each decision and how the plan changed over time are in [`docs/PROJECT_HISTORY.md`](docs/PROJECT_HISTORY.md).

## What this is

A smart guide cane for people who are blind or have low vision, built by a four-person team at the UCSC AI Hackathon @ SF Tech Week (October 10–11, 2026) for the ASUS Local AI track.

The user says "guide me to the apple", "take me to the door" or "take me to Safeway"; the cane confirms, then steers them there around obstacles.

### The plan since October 14

The GX10 was borrowed for the event and is no longer part of the plan. Decided by Connor on October 14:

- The **iPhone 16 Pro** on the cane does the thinking: it reads the LiDAR depth and runs the obstacle check itself, with plain maths, no AI.
- The **cane board** ([`hardware/cane-board/`](hardware/cane-board/)), an ESP32-S3 board that replaces the Raspberry Pi, drives the wheel. The phone sends it `LEFT`, `CENTER`, `RIGHT`, `STOP` or `FREE` over **Bluetooth LE**. No router, Wi-Fi or Tailscale.
- The **talk button** sends its questions (find this object, describe, read) from the phone to a **cloud AI**. The wheel never waits on the cloud.

```
iPhone: LiDAR + obstacle check ──LEFT/CENTER/RIGHT/STOP (Bluetooth LE)──► cane board ──► motor ──► wheel
   │  ▲                                                                       │
   │  └────────────────────── talk button press ◄─────────────────────────────┘
   └──► cloud AI (talk button questions only) ──► answer spoken by the phone
```

None of this is built yet. The cane as it stands is the hackathon build below.

### At the hackathon

- An **iPhone 16 Pro** on the cane captured the camera picture, LiDAR depth and position.
- An **ASUS Ascent GX10** on the team's table did all the thinking.
- A **Raspberry Pi 5** on the cane drives the mecanum wheel at the tip. The user confirmed direct wheel drive on October 11: opposite motor directions produce left/right guidance.

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
| iPhone app (`ios-app/`) | Camera, LiDAR, frame transport, guidance, speech and location code are present; verify the current build on a supported iPhone. Moving the obstacle check onto the phone and the Bluetooth link to the cane board: not started |
| GX10 software (`gx10/`) | Hackathon code: ingest, planner, dashboard, model, navigation and detection. Not part of the plan since October 14; the planner's obstacle check is the one to move to the phone |
| Pi motor controller (`pi/`) | Direct-wheel mode, command watchdog, setup tools and mock tests are present; verify motor direction and hardware behavior before use |
| Whole-system checks | Use the synthetic phone, simulated walk and mock GPIO tests; do not claim a physical end-to-end result unless it has been observed |
| Cane board ([`hardware/cane-board/`](hardware/cane-board/)) | Schematic for one board to replace the Pi, its converter and the IBT-2, drawn on October 13 after the event. The schematic passes KiCad's checks. Routed on October 14: 46 × 100 mm, 4 layers, black, ready-made 5 V module, XT30 motor socket; KiCad's design rules check reports 0 errors and 0 unconnected. Ordering files in `export/fab/` (JLCPCB) and `export/fab-other/` (other assemblers). Quoted in green at JLCPCB and PCBWay on October 15; nothing ordered. Not built; the cane as built still uses the Pi |
| Cane board firmware | Not started. Arduino / PlatformIO (decided October 14); Bluetooth LE to the phone. The rules it must keep are in the cane board's README |
| Talk button's cloud AI | Not started. Provider not chosen |
| Bill of materials ([`hardware/BOM.md`](hardware/BOM.md)) | Collected from the hardware pages on October 12; no prices or shop links |
| 3D pictures and model page | README pictures in `docs/media/` and a GitHub Pages page (`gh-pages` branch) that shows the interactive model. Made on October 12, after the event; see `docs/DISCLOSURE.md` |
| Result | 1st place overall at the UCSC AI Hackathon @ SF Tech Week, as reported by the team |

Update this table when you finish something.

## Rules you must not break

These came from the hackathon and from the team. After the event Connor changed rules 3, 7 and 9 for the new plan (October 14); the others stand.

1. **No pre-event code or parts without confirmation.** Hacking started at 12:00 PM on October 10, 2026. The organizers have not confirmed in writing whether earlier work is allowed. Do not copy code in from anywhere outside this repository unless the user says the organizers approved it, and then record it in `docs/DISCLOSURE.md`.
2. **Never fabricate history.** Do not backdate commits, invent commit history, or claim work was done at a time it was not.
3. **Guidance runs on the cane.** The obstacle check and every wheel decision run on the iPhone, from LiDAR depth. Never in the cloud, and never waiting on a network. (Until October 14 this rule said everything runs on the GX10.)
4. **The AI never controls the wheel.** The talk button's cloud AI finds objects, reads text and answers questions. Whether the way is clear is decided from LiDAR depth only. If the two disagree, depth wins.
5. **Unknown is not clear.** A direction with too few good depth readings counts as blocked.
6. **Fail safe.** The motor controller (the Pi today, the cane board later) switches the motor off if no command arrives for 0.4 seconds or the link drops. Never send raw motor power over the link.
7. **Cloud AI for the talk button only.** Its questions go from the phone to a cloud AI (decided October 14). Place lookup uses Apple MapKit. Ask before adding any other cloud service. (Until October 14 this rule said no cloud AI at all.)
8. **No secrets in the repo.** No passwords, tokens, API keys, Wi-Fi keys or Apple credentials, including the cloud AI's key. Use environment variables or local configuration.
9. **Retired October 14.** It said not to change system settings on the GX10, which was borrowed and is no longer used.
10. **Report honestly.** Say only that something works if you ran it. Label estimates as estimates.
11. **Safety claims.** This is an experimental supplement to a white cane, tested with a sighted observer. Never describe it as safe for independent travel, and never claim it handles stairs, kerbs, drop-offs or street crossings.

## How to work in this repo

- Do one small task at a time. Read the files you will change before editing.
- Message formats live in [`contracts/MESSAGES.md`](contracts/MESSAGES.md). Do not change them without the user's say-so; four people build against them.
- Every piece must run against a fake version of what it depends on (recorded frames, typed commands, a simulated walk), so nobody waits on anybody.
- Work on a branch and open a pull request; do not push to `main` directly.
- Run what you write. Report which files changed and what you tested.
- Match the plain, short style of the existing READMEs.
- Ask before adding a dependency. The cane board's firmware uses Arduino / PlatformIO.

## Machines

| Machine | Role | Notes |
| --- | --- | --- |
| iPhone 16 Pro | Camera, LiDAR, position, voice input; from October 14 also the obstacle check and the link to the cane board | Requires a supported iPhone and a signed app build |
| Cane board (ESP32-S3) | Motor controller to replace the Pi | Designed, not built. Bluetooth LE to the phone; firmware in Arduino / PlatformIO |
| Raspberry Pi 5 | Motor controller on the cane as built | Raspberry Pi OS Lite 64-bit; use `gpiozero` + `lgpio` |
| ASUS Ascent GX10 | AI inference and guidance host at the hackathon | No longer used. NVIDIA GB10, ARM64 Linux (DGX OS) |
| Development computers | Build and maintenance | Keep actual hostnames, addresses and credentials in local configuration, outside Git |

At the hackathon, device addresses depended on the local router or Tailscale network, kept in local configuration. The phone frame service used port 8775; the Pi command connection uses port 8766; the GX10's dashboard and model service used ports 8000 and 11434. The cane board needs no addresses: Bluetooth LE pairs the phone with it.

## Decisions already made

| Topic | Decision |
| --- | --- |
| Where the thinking runs | On the iPhone (October 14). At the hackathon: the GX10. |
| Phone to motor controller | Bluetooth LE between the phone and the cane board (October 14). The message format is not written yet; it goes in `contracts/MESSAGES.md`, which needs Connor's say-so. Photos never cross the link: the camera is on the phone. |
| Transport at the hackathon | WebSocket. One binary message per camera frame holding picture, depth and position together. No WebRTC, no video codec. |
| Capture | Own ARKit app. Fallback: the Record3D streaming app (no voice or maps on the fallback). |
| Network | None needed on the cane: Bluetooth LE. The phone's own mobile data carries the cloud questions and MapKit. At the hackathon the Pi was on a phone hotspot and the devices used Tailscale. |
| Depth | iPhone LiDAR (`sceneDepth`). No depth model. |
| Talk button questions | Cloud AI only, asked from the phone (October 14). Provider not chosen. At the hackathon: `qwen3-vl` through Ollama on the GX10. |
| Detector | None for now; the cloud AI finds named objects. At the hackathon: Ultralytics YOLO on the GX10. |
| Obstacle check | Seven headings from −30° to +30°, chosen every frame from depth. |
| Wheel | User confirmed October 11: one 12 V 120 rpm gear motor directly drives the mecanum wheel. LEFT and RIGHT spin opposite ways; CENTER/STOP/FREE switch off. Use `--wheel-drive`; `--swap` reverses the physical mapping. No position switches or homing in this mode. |
| Motor driver | On the cane as built: IBT-2 board (BTS7960), which passes the full 12 V, so the software limits are the only limits. On the cane board: a DRV8876 with a 2.2 A hardware limit. A commanded stop brakes; a dropped link sleeps the driver, which coasts. |
| Power | As built: 12 V 3 Ah pack → fuse → kill switch → IBT-2, and the Pi from the same pack through a 12 V to 5 V USB-C converter. With the cane board: the pack plugs into the board, which has its own fuse, reverse-plug protection, kill-switch loop and 5 V supply. |
| Kill switch | A switch in the handle, wired to the cane board's KILL plug (October 14). To buy. |
| Cane board firmware | Arduino / PlatformIO (October 14). |
| Voice | Push-to-talk, on-device speech recognition on the iPhone. |
| Places | Apple MapKit walking directions, looked up on the phone. |
| Cane | 18 mm carbon-fibre tube sections joined by the printed keyed coupler. |
| Printing | PETG-CF for rigid parts, TPU for pads and the tyre. |

## The algorithms, with starting numbers

Every number is a starting value to tune, not a measured result.

### Obstacle check (every frame; on the iPhone from October 14, on the GX10 at the hackathon)

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

1. Ask the AI for a box around the named object (the cloud AI from October 14; the vision-language model on the GX10 at the hackathon).
2. Distance = median LiDAR depth inside the box. Bearing = `atan((u − cx) / fx)` at the box centre.
3. Confirm aloud: "Apple, 3 metres, slightly left. Say yes to go."
4. Store the target as a point in the ARKit world frame; recompute its bearing from the pose every frame.
5. Feed that bearing to the obstacle check as the desired bearing.
6. Re-run the find every 2 seconds (1.5 while scanning). At the hackathon, YOLO's box was used every frame for objects it knew; there is no detector in the new plan yet. Between finds, the stored point keeps the bearing.
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

The cane board's firmware keeps the same command, TTL and silence rules, plus rules of its own for its watchdog, battery and stall limits: see [`hardware/cane-board/README.md`](hardware/cane-board/README.md).

### Prompts for the AI

- Describe: "In under 20 words, say what is directly ahead of the camera. Do not estimate distances."
- Read: "Read any text or signs in this image. If there is none, reply NONE."
- Find: "Locate the apple. Reply only as JSON with bbox_2d as [x1, y1, x2, y2] and a label, or bbox_2d as null." The coordinates may be on a 0–1000 scale, not pixels; verify on a test picture.

One request at a time, 6-second timeout. Written for `qwen3-vl` at the hackathon; check the box format against whichever cloud AI is chosen.

## Known traps

- **Picture direction.** ARKit's picture and depth are in the sensor's landscape direction. If the phone is mounted upright, data arrives turned 90° and left/right become up/down. Test with a hand on one side.
- **Intrinsics.** ARKit gives them for the full camera picture; scale them to the depth picture's size.
- **Depth size.** Commonly 256 × 192 but unverified; read it from the buffer.
- **Never queue frames.** Keep only the newest; skip a send if the last one has not finished.
- **Thinking mode.** If the model's reply starts with reasoning, turn thinking off; it adds seconds.
- **Slow model (hackathon, Ollama on the GX10).** A few tokens per second meant the setup was wrong, not the model. Check `ollama ps`.
- **Bluetooth with the screen off.** iOS pauses an app's Bluetooth in the background unless the app declares background Bluetooth use. The cane board stops the motor when commands stop, so this fails safe, but the cane goes quiet.
- **API key in the app.** A cloud AI key built into an iPhone app can be read out of it. Keep it out of the repo (rule 8), and plan how the app gets it.
- **Empty is not clear.** No points in a corridor can mean open space or missing readings.
- **Stale targets.** If ARKit tracking resets, stored positions are wrong. Clear them.
- **Pi resets when the motor starts.** The Pi now shares the motor's battery through a converter. If it resets or reports under-voltage when the motor runs, put it back on its own power bank.
- **Network setup.** A headless Pi needs a trusted network without a captive portal. Provide Wi-Fi credentials through a private NetworkManager profile and keep that profile out of Git. Use addresses assigned by the router or Tailscale; do not put active host addresses in examples.
- **Pi will not start.** Count the green light's blinks before changing anything else. Three long and one short is a bootloader error; the fix is in [`pi/README.md`](pi/README.md).
- **Phone tilt.** The phone has to look at least 25 degrees below the horizon. With less, in open space the obstacle check cannot judge the way ahead and stops ("Can't see ahead"). On the printed mount that is the 60 degree step, not the 45 the drawings show.
- **The cane in its own view.** Anything fixed in the depth picture (the cane's lower end, a hand, a strap) reads as an obstacle about 0.4 m ahead for ever. With open floor ahead every clearance bar on the dashboard should read 4.5. `SIGHTSENSE_OWN_CANE_M=0.65` ignores the cane's own strip; see `gx10/planner/README.md`.
- **Pi under-voltage.** A weak supply or long cable makes the Pi throttle and can reset it. `vcgencmd get_throttled` should print `0x0`.

## Priorities at the hackathon

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

- Which cloud AI answers the talk button, and how the app gets its key without it being in the repo or easy to read out of the app.
- The Bluetooth LE message format between the phone and the cane board. It goes in `contracts/MESSAGES.md`; ask Connor before writing it.
- Does iOS keep the LiDAR session and the Bluetooth link running with the screen off?
- Do MapKit directions work under a free Apple ID?
- Can the battery pack handle the motor at stall? On the cane board the stall is limited to 2.2 A; measure it.
- All delays: typical estimates are 0.3–0.45 s for a stop beep and 1.5–3 s for a model answer. Replace with measurements.
- From the event, now moot: the organizers' position on earlier work, own router and 3D printer, and which Nemotron was preloaded on the GX10.

## Where to find more

- [`docs/PROJECT_HISTORY.md`](docs/PROJECT_HISTORY.md): how the plan got here and why.
- [`contracts/MESSAGES.md`](contracts/MESSAGES.md): message formats between the phone, GX10 and Pi at the hackathon. The Bluetooth format is not written yet.
- [`hardware/cane-board/README.md`](hardware/cane-board/README.md): the cane board, its firmware rules and what is not done.
- [`pi/README.md`](pi/README.md): Pi setup and operation.
- [`hardware/BOM.md`](hardware/BOM.md): everything the cane is built from.
- [3D model](https://connorsawaya.github.io/SightSense/): the interactive model and guided tour.

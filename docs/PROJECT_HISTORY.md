# Project history

How the plan reached its current shape, in the order things were decided, with the reason for each change. This is a record of planning and decisions. It is not a record of code written; see the git log for that.

Planning happened on October 9 and the morning of October 10, 2026. Hacking began at 12:00 PM on October 10.

## 1. The starting idea (October 9)

SightSense began as a wearable: an iPhone on a chest strap, a Raspberry Pi in a backpack, and the ASUS GX10 as the AI server. Goals were obstacle warnings, a 3D map with route planning, and a large local vision-language model.

A review of that plan found:

- **The hard part was not AI.** It was getting synchronized camera, LiDAR and position data off the iPhone, with only Windows computers and no Mac.
- **WebRTC was unnecessary.** ARKit hands over picture, depth and position together for each frame, so sending them as one message keeps them matched for free.
- **The big model should not be in the safety loop.** Stopping for a chair is geometry on depth data. The model's job is finding named objects, reading signs and answering questions.
- **Unknown space must count as blocked.** Glass and mirrors return no depth; treating that as clear is the dangerous error.
- **The model choice was out of date.** Qwen3-VL 30B-A3B was still reasonable, but newer options (Qwen3.6-35B-A3B, Nemotron 3 Nano Omni) existed. Decision: test on the GX10 rather than assume.
- **Full 3D mapping (Nvblox, SLAM) was too much for one weekend.**
- **The Pi added little** in that design, beyond a watchdog and buttons.

## 2. The real rules (October 9, evening)

The organizers published the Hacker Guide, Track Challenges and Prizes. What changed the plan:

- The project must be **developed and demoed on the GX10**.
- Borrowed hardware **stays at the venue**, which closes at 10 PM Saturday. Overnight work is possible only on recordings.
- Judging happens **at the team's table**: 3 minutes plus 3 minutes of questions. The demo must fit in table space.
- **Every member must be able to explain the project**, or the team is not placed.
- ASUS judges look for a real problem, a new use of the GX10's hardware, a clear reason to run locally, and something useful or inspiring.
- The guide **does not say** whether earlier code is allowed. Decision: write no project code before 12:00 PM Saturday.

## 3. It became a cane (October 9)

The team's actual concept is a cane with a motor-driven wheel that steers the user. That changed several things:

- **The Pi became essential.** It controls the motor and switches it off if the network drops.
- **Control was split.** The GX10 sends a direction; the Pi alone handles the motor, its limits and its fail-safe.
- **The phone moved onto the cane**, near the handle, so the camera points where the cane points.

## 4. The wheel (October 9)

- The first idea was a **mecanum wheel**. A passive mecanum wheel slides sideways freely, so steering it gives no guidance. A driven pair could push sideways but needs two motors.
- The team has **one 12 V 120 rpm gear motor and one L298N driver**. At 120 rpm a small wheel cannot roll at walking speed, so the motor cannot drive the wheel.
- Decision: the motor **steers a normal free-rolling wheel** to three positions (left, centre, right), found with limit switches. Three positions match the left / centre / right decision and need no angle sensor.

## 5. Power and parts (October 9)

- 12 V 3 Ah battery pack for the motor, through a fuse and a kill switch.
- A 12 V to 5 V converter is available, but the Pi goes on its own USB-C power bank to avoid resets when the motor starts.
- The team has its own 3D printer with PETG-CF and TPU. Rigid parts in PETG-CF, pads and the tyre in TPU. Every printed part has a bought fallback.

## 6. Voice and places (October 9)

- **Voice commands** were added, with push-to-talk instead of a wake word because a hackathon hall is loud.
- **Apple Maps routing** was first rejected: it needs internet, an app of our own, and GPS that fails indoors.
- A teammate then offered a **Mac**, which makes an app of our own possible. That brought back on-phone speech recognition and MapKit.
- "Take me to Safeway" was added. Its limit is stated openly: the GX10 stays on the table, so the cane only works within the router's range, and the lookup uses the internet.

## 7. Adaptive route following (October 9)

The user asked that it work out a walking route and follow it while avoiding obstacles. This produced the two-layer design:

- A **route follower** that turns the route into a desired bearing.
- An **obstacle check over seven headings** that picks the clear heading closest to that bearing.

The seven-heading check replaced the earlier plan for A* path planning. It is simpler and serves all three sources of a desired bearing: none, an object, or a route.

## 8. "Guide me to the apple" became the core (October 9)

The user made indoor object guidance the feature that must work. It moved above the wheel, voice and place routing, and became the demo: an apple across the aisle, a chair in between.

Design: the model finds the object, the LiDAR measures it, and ARKit's tracking remembers where it is so guidance continues when it leaves view.

## 9. Team and tools (October 9–10)

- Four roles: iPhone app; GX10 and models; obstacle check and plumbing; cane, Pi and team lead.
- The iPhone app is being written with AI coding help by someone new to iOS. The Record3D streaming app stays as the fallback, decided at the 2:30 PM checkpoint.

## 10. Day of the event (October 10)

- The GitHub repository was created at about 12:05 PM.
- The cane's keyed coupler design (for 18 mm carbon-fibre tube) was added, and the repository layout, message formats and wiring plan were written.
- Work that needed physical devices moved to a development computer connected to the hardware.
- Earlier work outside this repository was not imported, pending the organizers' answer on whether pre-event work was allowed.

## 11. Getting the Pi running (October 10, afternoon)

- The expected private router was unavailable, and venue Wi-Fi was not suitable for a headless Pi. The team used a temporary private network while arranging device connectivity. Network names, passwords and live addresses are kept out of this repository.
- The Pi reported a bootloader fault before reading the SD card. Official recovery files restored it.
- The motor driver and gearbox differed from the initial plan, so the wiring notes and controller were updated for the hardware on hand.
- The motor controller was first developed against a simulated wheel and mock GPIO. The driver, fuse, kill switch and limit switches still needed physical checks at that point.

## 12. Direct wheel drive and the Pi update (October 11)

- The 12 V motor connects directly to the mecanum wheel. Opposite rotations are intended to produce left/right guidance. This replaces the earlier three-position steering plan.
- Added `--wheel-drive`: LEFT/RIGHT spin opposite ways; CENTER/STOP/FREE switch off. Duty stays capped at 25%, each pulse at 400 ms, with a 50 ms rest and a finite command watchdog.
- Added tests using local WebSockets, synthetic phone frames, the Pi control loop and mock GPIO. Those tests did not exercise the physical motor or a real AI model.
- Added an SD update tool that backs up boot files, validates the expected root PARTUUID and installs the Pi files on its next boot. Supply the GX10 address and any Wi-Fi profile from local configuration; do not commit those values.
- The GX10 and Pi communicated over the private device network on the command port. The actual host addresses are intentionally omitted. Motor RPM and lateral direction still require physical measurement.
- The Pi's boot configuration needed an explicit installer target. The updater now selects that target directly. Verify network connectivity and physical wheel behavior on the target hardware.

## Ideas considered and dropped

| Idea | Why it was dropped |
| --- | --- |
| WebRTC and H.264 video | Extra delay and setup for no gain on a local network |
| Full 3D mapping, Nvblox, SLAM | Too much to learn and build in a weekend |
| A* path planning | Replaced by the seven-heading check |
| A depth-estimating AI model | The LiDAR measures depth directly |
| Mecanum wheel | Slides sideways; needs two motors to be useful |
| Driving the wheel with the motor | 120 rpm is too slow for walking pace |
| Wake word as the main trigger | Unreliable in a noisy hall |
| Cloud text-to-speech | Breaks the local-only claim |
| Video relayed through the Pi | Adds delay and a failure point |
| Stairs and drop-off detection | Too risky to claim; left to the white cane |
| Carrying the GX10 in a backpack | Borrowed hardware; future work |

## Still unverified

- The organizers' position on earlier work, own router, 3D printer and finalists keeping the GX10.
- The exact Ollama model names.
- The iPhone depth picture's size and usable range in the venue.
- Every delay and accuracy figure.
- The names of earlier research guide canes (GuideCane, Co-Robotic Cane), which were recalled from memory.

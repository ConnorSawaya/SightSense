# Disclosure

What in this project we did not make ourselves, and what existed before the event. Keep this current; it goes into the Devpost submission.

## Tools and models we use but did not make

| Tool | Used for |
| --- | --- |
| Apple ARKit | Camera, LiDAR depth and position tracking on the iPhone |
| Apple MapKit | Walking directions for "take me to a place" (uses Apple's servers) |
| Apple Speech framework | On-device speech recognition |
| Ollama | Running the vision-language model on the GX10 |
| Qwen3-VL (Alibaba) | Describing scenes, reading signs, finding named objects (`qwen3-vl:30b-a3b-instruct` is the default; `qwen3-vl:8b-instruct` tested as the fallback) |
| Ultralytics YOLO (YOLO26s, COCO-trained weights) | Detecting common objects |
| Ultralytics YOLOE (YOLOE-26s-seg weights) | Finding hazards YOLO has no name for: door, stairs, pole, curb and others |
| Apple MobileCLIP2 (via Ultralytics) and the `clip` package | Turning the hazard names into YOLOE's prompts, once; Ultralytics installed `clip` and its helpers itself |
| PyTorch, OpenCV | Running YOLO on the GX10 (`gx10/detector/`) |
| NumPy, websockets | Obstacle check and the frame service on the GX10 (`gx10/planner/`, `gx10/ingest/`) |
| NVIDIA Nemotron | Preloaded on the GX10 (`nemotron3:33b`, Nemotron 3 Nano Omni); tested as a vision-language model |
| Qwen3.6 (Alibaba) | Preloaded on the GX10 (`qwen3.6:35b`); tested as a vision-language model |
| Pillow | Making test pictures for `gx10/vlm/` |
| Wikimedia Commons `Red_Apple.jpg`, Ultralytics sample `bus.jpg` | Source photos for the `gx10/vlm/` test pictures; not committed |
| gpiozero | Motor and switch control on the Raspberry Pi |
| websockets (Python library) | The Raspberry Pi's link to the GX10's command port |
| Tailscale | Private network between the phone, the Pi, the laptops and the GX10, used from October 10 because the team's router was not at the venue |
| OpenSCAD | Designing the cane coupler |
| build123d | Designing the handle and phone mount |
| Raspberry Pi OS Lite, Raspberry Pi Imager | The Raspberry Pi's operating system, and writing it to the SD card |
| Raspberry Pi bootloader recovery files (rpi-eeprom) | Repairing the Raspberry Pi's bootloader when it would not start |

Update this table as tools are added or dropped.

## What uses the internet

Two things. The place lookup ("take me to Safeway") goes through Apple Maps. And since October 10 the phone reaches the GX10 over Tailscale, and the Pi is set up to, so camera frames, depth and commands travel encrypted between the team's own devices over the internet, through Tailscale's relay servers when no direct path exists. The obstacle check and all AI models run on the GX10. No cloud AI is used.

## Work done before the event

- **Handle and phone mount** (`hardware/handle-phone-mount/`): the build123d script was started at about 10:55 AM on October 10, 2026, roughly an hour before hacking opened, as a plain handle and a motor mount, outside this repository. The tilted handle, pole collar and phone cradle in that folder were designed after 12:00 PM the same day. Whether the pre-noon start is allowed has not been confirmed with the organizers.
- **Raspberry Pi SD card**: Raspberry Pi OS Lite was written to the card with Raspberry Pi Imager at about 10:00 PM on October 9, 2026. This was set-up only; no project code was on it. The Pi first started from it on October 10.

The rest is to be completed by the team. State plainly what existed before 12:00 PM on October 10, 2026 (ideas, designs, code, printed parts), and what was built during the event.

## Added after the event

- **3D pictures in the README** (`docs/media/`): made on October 12, 2026, the day after the event, with an AI coding assistant. They are rendered from a model built for a team member's portfolio page. That model starts from `hardware/assembly/assembly_viewer.html` and adds a Raspberry Pi 5 (Raspberry Pi's official STEP model, MIT licence), a gearmotor, battery, phone, wheel, motor driver and wiring drawn from published sizes and from `hardware/wiring.md`. The scripts that build it are in the portfolio's repository, not this one. Nothing in the pictures was part of the judged submission.
- **3D model page** (<https://connorsawaya.github.io/SightSense/>): added on October 12, 2026. It is one page on the `gh-pages` branch that shows the same model, which is served from the portfolio's site and not stored in this repository.
- **Photos from the event** (`docs/media/photos/`): taken by the team at the event and added to the README on October 12, 2026. They are captures of the photos as shown in a browser, resized, not the original files. Two are trimmed to leave out an event badge's QR code. The name tags over the three people in the team photo are not in the original: they were made with an online Minecraft name tag generator and added to the picture afterwards.
- **The result**: the README records that the project placed 1st overall, as reported by the team.

## AI assistance

Parts of this repository's documentation and code were written with AI coding assistants.

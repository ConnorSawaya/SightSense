# Disclosure

What in this project we did not make ourselves, and what existed before the event. Keep this current; it goes into the Devpost submission.

## Tools and models we use but did not make

| Tool | Used for |
| --- | --- |
| Apple ARKit | Camera, LiDAR depth and position tracking on the iPhone |
| Apple MapKit | Walking directions for "take me to a place" (uses Apple's servers) |
| Apple Speech framework | On-device speech recognition |
| Ollama | Running the vision-language model on the GX10 |
| Qwen3-VL (Alibaba) | Describing scenes, reading signs, finding named objects |
| Ultralytics YOLO | Detecting common objects |
| NVIDIA Nemotron | Preloaded on the GX10 |
| gpiozero | Motor and switch control on the Raspberry Pi |
| OpenSCAD | Designing the cane coupler |

Update this table as tools are added or dropped.

## What uses the internet

Only the place lookup ("take me to Safeway"), through Apple Maps. The camera video, depth data, obstacle check and all AI models stay on the local network.

## Work done before the event

To be completed by the team. State plainly what existed before 12:00 PM on October 10, 2026 (ideas, designs, code, printed parts), and what was built during the event.

## AI assistance

Parts of this repository's documentation and code were written with AI coding assistants.

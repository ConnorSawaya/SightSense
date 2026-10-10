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
| NVIDIA Nemotron | Preloaded on the GX10 (`nemotron3:33b`, Nemotron 3 Nano Omni); tested as a vision-language model |
| Qwen3.6 (Alibaba) | Preloaded on the GX10 (`qwen3.6:35b`); tested as a vision-language model |
| Pillow | Making test pictures for `gx10/vlm/` |
| Wikimedia Commons `Red_Apple.jpg`, Ultralytics sample `bus.jpg` | Source photos for the `gx10/vlm/` test pictures; not committed |
| gpiozero | Motor and switch control on the Raspberry Pi |
| OpenSCAD | Designing the cane coupler |
| build123d | Designing the handle and phone mount |

Update this table as tools are added or dropped.

## What uses the internet

Only the place lookup ("take me to Safeway"), through Apple Maps. The camera video, depth data, obstacle check and all AI models stay on the local network.

## Work done before the event

- **Handle and phone mount** (`hardware/handle-phone-mount/`): the build123d script was started at about 10:55 AM on October 10, 2026, roughly an hour before hacking opened, as a plain handle and a motor mount, outside this repository. The tilted handle, pole collar and phone cradle in that folder were designed after 12:00 PM the same day. Whether the pre-noon start is allowed has not been confirmed with the organizers.

The rest is to be completed by the team. State plainly what existed before 12:00 PM on October 10, 2026 (ideas, designs, code, printed parts), and what was built during the event.

## AI assistance

Parts of this repository's documentation and code were written with AI coding assistants.

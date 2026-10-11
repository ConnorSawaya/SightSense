# detector

YOLO on every frame, for the 80 objects it knows (apple, chair, bottle, cup, person, bus …). When the user asks for one of those, its box refreshes the target every frame instead of every 2 seconds (`Navigator.on_frame(frame, detections)`).

It needs PyTorch, so unlike `vlm/` and `navigator/` it runs in a virtual environment in the project folder, not the system Python. The planned `ultralytics/ultralytics:latest-nvidia-arm64` container was not used: the `asus` user cannot run Docker without being added to the `docker` group, which would change the borrowed GX10's settings.

## Setup (once, on the GX10)

```bash
cd ~/SightSense-work
python3 -m venv venv-yolo
venv-yolo/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
venv-yolo/bin/pip install ultralytics onnx
export YOLO_CONFIG_DIR=~/SightSense-work/.ultralytics   # keeps Ultralytics' settings in the project folder
```

Installed: PyTorch 2.14.1+cu130 (sees the GB10), Ultralytics 8.4.175, OpenCV 5.0. About 5.7 GB. Weights (`yolo26s.pt`, `yolo11s.pt`) download into this folder on first use and are not committed.

## Use

```python
from detector.detector import Detector
d = Detector()                  # SIGHTSENSE_YOLO_MODEL, default yolo26s.pt
dets = d.detect(jpeg_bytes)     # [Detection(label="apple", conf=0.93, box=[110, 300, 195, 384]), ...]
g = nav.on_frame(frame, dets)
```

## Hazards and steady answers (October 11)

YOLO only knows its 80 trained objects, so a hallway with a door and a pillar showed nothing. Alongside it, **YOLOE-26s** (an open-vocabulary Ultralytics model) looks for the names in `SIGHTSENSE_HAZARDS`: door, stairs, pole, pillar, curb, railing, trash can, traffic cone, sign. The names are turned into prompts once by MobileCLIP, and the result is saved as `yoloe-26s-seg-hazards-<hash>.pt` next to this file (not committed), so later starts need neither the text encoder nor the internet. Asking YOLOE for all 80 objects too was tried and rejected: label changes went up to 1.18 a frame and it added wrong labels (toaster, handbag). "Elevator" was dropped from the list after it named an arched front door.

`stable.py` follows each object across frames (same label, overlapping box). An object is shown once it is seen in 3 of the last 5 frames at confidence 0.4 or more (0.3 for hazards), kept through a missed frame or a dip to 0.25, and hidden once missing from 4 of the last 5. Its box moves 60 % of the way to the newest one each frame.

Both models run in half precision (`quantize=16`): it found the same 3030 of 3030 objects as full precision on recordings, with confidence changed by 0.001 on average.

Measured on 320-frame stretches of two phone recordings, GPU otherwise idle:

| | House walk (`20261010-190000`) | Table scene (`20261010-165037`) |
| --- | --- | --- |
| Label changes per frame, threshold only | 0.38 | 0.75 |
| Label changes per frame, `stable.py` | 0.12 | 0.13 |
| Both models, per frame | 7.7 ms median, 8.2 ms 95th percentile | same |

Bigger YOLO models were tried on the house walk and were not steadier: label changes per frame 0.34 (26s), 0.48 (26m), 0.46 (26l), 0.38 (26x), with the same objects found, at 2 to 4 times the time.

## Measured on the GX10 (October 10, PyTorch, no TensorRT)

`../../venv-yolo/bin/python -m detector.check` from `gx10/`:

| Model | Street picture | Apple pictures | Empty room | Per frame (JPEG decode included) |
| --- | --- | --- | --- | --- |
| `yolo26s.pt` (default) | bus 0.93, 4 people 0.82–0.92 | apple 0.93 and 0.91, boxes within 5 px | nothing | 5.9 ms median, 6.3 ms 95th percentile |
| `yolo11s.pt` | bus 0.94, 4 people 0.64–0.90 | apple 0.90 and 0.88 | nothing | 5.9 ms median, 6.5 ms 95th percentile |

With YOLO, `navigator.check_live --yolo` confirmed the apple 0.09 s after "guide me to the apple", against 1.3–1.8 s with the vision-language model alone.

TensorRT export (`export_engine()`) has not been run. It needs the TensorRT Python package, a large download on the venue Wi-Fi, and at 5.9 ms a frame there is little to gain against the phone's 66 ms between frames.

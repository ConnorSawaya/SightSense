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

## Measured on the GX10 (October 10, PyTorch, no TensorRT)

`../../venv-yolo/bin/python -m detector.check` from `gx10/`:

| Model | Street picture | Apple pictures | Empty room | Per frame (JPEG decode included) |
| --- | --- | --- | --- | --- |
| `yolo26s.pt` (default) | bus 0.93, 4 people 0.82–0.92 | apple 0.93 and 0.91, boxes within 5 px | nothing | 5.9 ms median, 6.3 ms 95th percentile |
| `yolo11s.pt` | bus 0.94, 4 people 0.64–0.90 | apple 0.90 and 0.88 | nothing | 5.9 ms median, 6.5 ms 95th percentile |

With YOLO, `navigator.check_live --yolo` confirmed the apple 0.09 s after "guide me to the apple", against 1.3–1.8 s with the vision-language model alone.

TensorRT export (`export_engine()`) has not been run. It needs the TensorRT Python package, a large download on the venue Wi-Fi, and at 5.9 ms a frame there is little to gain against the phone's 66 ms between frames.

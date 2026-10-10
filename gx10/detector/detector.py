"""YOLO on every frame, for objects it knows (the 80 COCO classes: apple, chair, bottle, person ...).

Runs in the project's own virtual environment (see README.md), on the GPU.
Uses a TensorRT engine if one has been exported, otherwise the PyTorch model.

Settings (environment variables):
    SIGHTSENSE_YOLO_MODEL   default yolo26s.pt (downloaded by Ultralytics on first use); yolo11s.pt also works
    SIGHTSENSE_YOLO_CONF    minimum confidence, default 0.4
"""

import os
from dataclasses import dataclass
from pathlib import Path

MODEL = os.environ.get("SIGHTSENSE_YOLO_MODEL", "yolo26s.pt")
CONF = float(os.environ.get("SIGHTSENSE_YOLO_CONF", "0.4"))
HERE = Path(__file__).parent


@dataclass
class Detection:
    label: str
    conf: float
    box: list  # [x1, y1, x2, y2] in picture pixels


class Detector:
    def __init__(self, model: str = MODEL):
        from ultralytics import YOLO  # imported here so the rest of gx10/ does not need it

        path = Path(model)
        if not path.is_absolute() and not path.exists():
            path = HERE / model  # weights and engines live next to this file (not committed)
        engine = path.with_suffix(".engine")
        self.using = str(engine if engine.exists() else path)
        self.model = YOLO(self.using, task="detect")
        self.names = self.model.names
        import numpy as np

        self.model.predict(np.zeros((480, 640, 3), np.uint8), verbose=False)  # the first run on the GPU takes about 1 s

    def detect(self, jpeg: bytes, conf: float = CONF) -> list:
        import cv2
        import numpy as np

        img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return []
        r = self.model.predict(img, conf=conf, verbose=False)[0]
        out = []
        for box, c, k in zip(r.boxes.xyxy.tolist(), r.boxes.conf.tolist(), r.boxes.cls.tolist()):
            out.append(Detection(self.names[int(k)], round(c, 3), [round(v) for v in box]))
        return out

    def knows(self, name: str) -> bool:
        return name.lower() in {n.lower() for n in self.names.values()}


def export_engine(model: str = MODEL, half: bool = True) -> str:
    """Export a TensorRT engine next to the weights. Not yet run: needs the TensorRT
    Python package (a large download), and PyTorch is already 5.9 ms per frame."""
    from ultralytics import YOLO

    path = Path(model)
    if not path.is_absolute() and not path.exists():
        path = HERE / model
    return YOLO(str(path)).export(format="engine", half=half, imgsz=640)

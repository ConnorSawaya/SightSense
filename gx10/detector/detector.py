"""Two detectors on every frame, on the GPU:
- YOLO26s for the 80 everyday objects it was trained on (apple, chair, bottle, person ...),
- YOLOE-26s, an open-vocabulary model, for hazards YOLO has no name for (door, stairs, pole ...).
Neither decides the wheel: clear or blocked comes from depth. stable.py holds their answers steady.

Runs in the project's own virtual environment (see README.md).
Uses a TensorRT engine if one has been exported, otherwise the PyTorch model.

Settings (environment variables):
    SIGHTSENSE_YOLO_MODEL   default yolo26s.pt (downloaded by Ultralytics on first use); yolo11s.pt also works
    SIGHTSENSE_YOLO_CONF    minimum confidence, default 0.4
    SIGHTSENSE_HAZARDS      comma-separated names for YOLOE; empty turns it off
    SIGHTSENSE_YOLOE_MODEL  default yoloe-26s-seg.pt
"""

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

MODEL = os.environ.get("SIGHTSENSE_YOLO_MODEL", "yolo26s.pt")
CONF = float(os.environ.get("SIGHTSENSE_YOLO_CONF", "0.4"))
HAZARDS = [h.strip() for h in os.environ.get(
    "SIGHTSENSE_HAZARDS", "door,stairs,pole,pillar,curb,railing,trash can,traffic cone,sign").split(",") if h.strip()]
YOLOE_MODEL = os.environ.get("SIGHTSENSE_YOLOE_MODEL", "yoloe-26s-seg.pt")
FP16 = 16  # half precision: 7.4 ms for both models instead of 11.1, same objects (3030 of 3030 on recordings)
HAZARD_CONF = 0.2  # YOLOE scores run lower than YOLO's; stable.py shows them from 0.3
HERE = Path(__file__).parent


@dataclass
class Detection:
    label: str
    conf: float
    box: list  # [x1, y1, x2, y2] in picture pixels
    source: str = "yolo"  # "yolo" (80 trained objects) or "open" (YOLOE, named in HAZARDS)


def _weights(name: str) -> Path:
    path = Path(name)
    return path if path.is_absolute() or path.exists() else HERE / name  # weights live next to this file (not committed)


def hazard_model(names=None, base: str = YOLOE_MODEL):
    """YOLOE with the hazard names built in, saved next to this file so the text encoder
    (MobileCLIP, about 250 MB of memory) is needed only the first time a list is used."""
    from ultralytics import YOLOE

    names = list(names or HAZARDS)
    tag = hashlib.sha1((base + "|" + ",".join(names)).encode()).hexdigest()[:8]
    saved = HERE / f"{Path(base).stem}-hazards-{tag}.pt"
    if saved.exists():
        return YOLOE(str(saved))
    m = YOLOE(str(_weights(base)))
    m.set_classes(names, m.get_text_pe(names))
    m.save(str(saved))
    return YOLOE(str(saved))


class Detector:
    def __init__(self, model: str = MODEL, hazards=None):
        from ultralytics import YOLO  # imported here so the rest of gx10/ does not need it

        path = _weights(model)
        engine = path.with_suffix(".engine")
        self.using = str(engine if engine.exists() else path)
        self.model = YOLO(self.using, task="detect")
        self.names = self.model.names
        hazards = HAZARDS if hazards is None else hazards
        self.open = hazard_model(hazards) if hazards else None
        if self.open is not None:
            self.using += f" + {YOLOE_MODEL} ({', '.join(hazards)})"
        import numpy as np

        blank = np.zeros((480, 640, 3), np.uint8)
        self.model.predict(blank, quantize=FP16, verbose=False)  # the first run on the GPU takes about 1 s
        if self.open is not None:
            self.open.predict(blank, quantize=FP16, verbose=False)

    def detect(self, jpeg: bytes, conf: float = CONF) -> list:
        import cv2
        import numpy as np

        img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR) if jpeg else None
        return self.detect_image(img, conf) if img is not None else []

    def detect_image(self, img, conf: float = CONF) -> list:
        """Same as detect(), on a BGR image array that is already decoded."""
        out = _boxes(self.model.predict(img, conf=conf, quantize=FP16, verbose=False)[0], "yolo")
        if self.open is not None:
            out += _boxes(self.open.predict(img, conf=min(conf, HAZARD_CONF), quantize=FP16, verbose=False)[0], "open")
        return out

    def knows(self, name: str) -> bool:
        names = set(self.names.values()) | (set(self.open.names.values()) if self.open is not None else set())
        return name.lower() in {n.lower() for n in names}


def _boxes(r, source: str) -> list:
    return [Detection(r.names[int(k)], round(c, 3), [round(v) for v in box], source)
            for box, c, k in zip(r.boxes.xyxy.tolist(), r.boxes.conf.tolist(), r.boxes.cls.tolist())]


def export_engine(model: str = MODEL, half: bool = True) -> str:
    """Export a TensorRT engine next to the weights. Not yet run: needs the TensorRT
    Python package (a large download), and PyTorch is already 5.9 ms per frame."""
    from ultralytics import YOLO

    path = Path(model)
    if not path.is_absolute() and not path.exists():
        path = HERE / model
    return YOLO(str(path)).export(format="engine", half=half, imgsz=640)

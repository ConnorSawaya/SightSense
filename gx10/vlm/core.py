"""Describe, read and find with a vision-language model through Ollama.

Standard library only. The model never decides whether the way is clear and is
never asked for a distance; find() returns a box, and the distance comes from
the LiDAR depth inside it.

Settings (environment variables):
    SIGHTSENSE_OLLAMA_URL      default http://127.0.0.1:11434
    SIGHTSENSE_VLM_MODEL       default qwen3-vl:30b-a3b-instruct (fastest in check.py and bench.py)
    SIGHTSENSE_VLM_FALLBACK    default qwen3-vl:8b-instruct (used if the main model is not installed)
    SIGHTSENSE_VLM_TIMEOUT     seconds per request, default 6
    SIGHTSENSE_VLM_CTX         context length in tokens, default 8192 (one picture and a prompt)
    SIGHTSENSE_VLM_BOX_SCALE   "1000" (boxes on a 0-1000 scale) or "pixels"; default picks by model
"""

import base64
import json
import os
import re
import struct
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

OLLAMA_URL = os.environ.get("SIGHTSENSE_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.environ.get("SIGHTSENSE_VLM_MODEL", "qwen3-vl:30b-a3b-instruct")
FALLBACK = os.environ.get("SIGHTSENSE_VLM_FALLBACK", "qwen3-vl:8b-instruct")
TIMEOUT_S = float(os.environ.get("SIGHTSENSE_VLM_TIMEOUT", "6"))
# Ollama's default context for these models is 262144 tokens, which made qwen3-vl:8b
# take 48 GB. Every request must send the same value or Ollama reloads the model.
CTX = int(os.environ.get("SIGHTSENSE_VLM_CTX", "8192"))
BOX_SCALE = os.environ.get("SIGHTSENSE_VLM_BOX_SCALE", "")

COULDNT_TELL = "I couldn't tell"

PROMPTS = {
    "describe": "In under 20 words, say what is directly ahead of the camera. Do not estimate distances.",
    "read": "Read any text or signs in this image. If there is none, reply NONE.",
    "find": "Locate the {name}. Reply only as JSON with bbox_2d as [x1, y1, x2, y2] and a label, or bbox_2d as null.",
    # Asked before "find": the box prompt alone always returns a box, even for things
    # that are not there (it boxed an exit sign as an apple). See README.md.
    "present": "Is there a {name} in this image? Reply only yes or no.",
    # Voice commands the rules in navigator/commands.py did not understand. Text only, no picture.
    "interpret": (
        'A blind person said this to their smart guide cane: "{text}"\n'
        "Pick the one command they mean:\n"
        '- object: go to or find a thing nearby (target: the thing, like "door" or "red cup")\n'
        "- place: go to a named place, shop or address (target: the place)\n"
        "- describe: what is around or ahead\n"
        "- read: read signs or text\n"
        "- yes or no: answering a question the cane asked\n"
        "- cancel: stop guiding\n"
        "- status: how the trip is going (am I going the right way, how far is it, are we there yet)\n"
        "- question: another question about what is in front of them (target: the question)\n"
        "- unknown: none of these\n"
        'Reply only as JSON: {{"command": "...", "target": "..." or null}}'
    ),
    "ask": (
        'A blind person asks about this picture: "{question}"\n'
        "Answer in under 20 words. Do not estimate distances, and never say whether it is safe "
        "or clear to walk. If you cannot tell, say so."
    ),
}

INTENTS = ("object", "place", "describe", "read", "yes", "no", "cancel", "status", "question", "unknown")
DISTANCE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:m|cm|metres?|meters?|feet|foot|ft|steps?|yards?)\b", re.IGNORECASE)
NO_DISTANCES = "I can't judge distances from the picture. The cane measures them."

# Box scale checked with check.py on test pictures with a known apple position.
KNOWN_BOX_SCALES = {"qwen3-vl": "1000", "qwen3.6": "1000", "nemotron3": "1000"}

_lock = threading.Lock()  # one model request at a time
_active_model = None


@dataclass
class Answer:
    ok: bool  # False: timed out, busy, unparseable or error; say `text` ("I couldn't tell")
    text: str  # what to say to the user
    box: Optional[list] = None  # find only: [x1, y1, x2, y2] in picture pixels, or None if not seen
    label: Optional[str] = None
    model: str = ""
    seconds: float = 0.0
    raw: str = ""  # the model's reply, for the dashboard and debugging
    error: Optional[str] = None


# ---------------------------------------------------------------- public API


def describe(jpeg: bytes) -> Answer:
    """Say in a few words what is ahead. Returns text only."""
    a = _one(jpeg, PROMPTS["describe"])
    if not a.ok:
        return a
    text = _clean(a.raw)
    if not text:
        return _fail(a, "empty reply")
    words = text.split()
    if len(words) > 25:  # the prompt asks for under 20; cut runaway answers
        text = " ".join(words[:25])
    a.text = text
    return a


def read(jpeg: bytes) -> Answer:
    """Read text and signs. text is "" when there is none."""
    a = _one(jpeg, PROMPTS["read"])
    if not a.ok:
        return a
    text = _clean(a.raw)
    if not text:
        return _fail(a, "empty reply")
    if re.fullmatch(r"[\s\"'`*.]*NONE[\s\"'`*.]*", text, re.IGNORECASE):
        text = ""
    a.text = text
    return a


def find(jpeg: bytes, name: str) -> Answer:
    """Find a named object. box is in picture pixels, or None if not seen."""
    name = re.sub(r"[^\w\s'-]", "", name).strip()[:40] or "object"
    try:
        size = jpeg_size(jpeg)
    except ValueError as e:
        return Answer(False, COULDNT_TELL, model=active_model(), error=str(e))
    if not _lock.acquire(blocking=False):
        return _busy()
    try:
        deadline = time.monotonic() + TIMEOUT_S  # both questions share one timeout
        gate = _ask(jpeg, PROMPTS["present"].format(name=name), deadline)
        if not gate.ok:
            return gate
        yes_no = _clean(gate.raw).lower().strip(".! ")
        if yes_no == "no":
            gate.text, gate.label = f"I don't see the {name}.", name
            return gate
        if yes_no != "yes":
            return _fail(gate, "unparseable yes/no reply")
        a = _ask(jpeg, PROMPTS["find"].format(name=name), deadline)
        a.seconds += gate.seconds
    finally:
        _lock.release()
    if not a.ok:
        return a
    parsed = parse_box(a.raw, size, box_scale(a.model))
    if parsed is None:
        return _fail(a, "unparseable find reply")
    box, label = parsed
    a.box, a.label = box, label or name
    a.text = f"I see the {name}." if box else f"I don't see the {name}."
    return a


def interpret(text: str) -> Answer:
    """What a sentence the rules did not understand asks for. Text only, no picture.

    label is one of INTENTS; text is its target or the question ("" if none).
    The model only picks a command; it never steers and never says whether the way is clear.
    """
    text = re.sub(r"\s+", " ", text or "").strip()[:200].replace('"', "'")
    a = _one(None, PROMPTS["interpret"].format(text=text))
    if not a.ok:
        return a
    obj = _first_json(a.raw)
    if not isinstance(obj, dict) or obj.get("command") not in INTENTS:
        return _fail(a, "unparseable interpret reply")
    target = obj.get("target")
    a.label = obj["command"]
    a.text = re.sub(r"\s+", " ", target).strip(" .!?,")[:80] if isinstance(target, str) else ""
    return a


def ask(jpeg: bytes, question: str) -> Answer:
    """Answer a question about the picture in a few words. Never a distance, never whether it is safe."""
    question = re.sub(r"\s+", " ", question or "").strip()[:200].replace('"', "'")
    a = _one(jpeg, PROMPTS["ask"].format(question=question))
    if not a.ok:
        return a
    text = _clean(a.raw)
    if not text:
        return _fail(a, "empty reply")
    words = text.split()
    if len(words) > 30:
        text = " ".join(words[:30])
    if DISTANCE.search(text):
        text = NO_DISTANCES  # distances come from the LiDAR, never from the model
    a.text = text
    return a


def warm(timeout_s: float = 300) -> str:
    """Pick the model, load it onto the GPU and keep it loaded. Call once at start.

    Returns the model name in use. Loading takes far longer than the 6-second
    request timeout, so do it before the first real request.
    """
    global _active_model
    installed = installed_models()
    model = MODEL if MODEL in installed else FALLBACK if FALLBACK in installed else None
    if model is None:
        raise RuntimeError(f"Neither {MODEL} nor {FALLBACK} is installed in Ollama ({OLLAMA_URL})")
    _post("/api/generate", {"model": model, "keep_alive": -1, "options": {"num_ctx": CTX}}, timeout_s)
    _active_model = model
    return model


def active_model() -> str:
    return _active_model or MODEL


def installed_models() -> list:
    with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=5) as r:
        return [m["name"] for m in json.load(r)["models"]]


def box_scale(model: str) -> str:
    if BOX_SCALE:
        return BOX_SCALE
    for prefix, scale in KNOWN_BOX_SCALES.items():
        if model.startswith(prefix):
            return scale
    return "1000"


# ---------------------------------------------------------------- parsing


def parse_box(raw: str, size: tuple, scale: str = "1000"):
    """Turn a find reply into (box_in_pixels_or_None, label). None if it does not parse.

    Accepts {"bbox_2d": [...], "label": ...}, a list of those (first one wins),
    a bare [x1, y1, x2, y2], or bbox_2d null, optionally inside a ```json fence.
    """
    obj = _first_json(raw)
    if isinstance(obj, list) and len(obj) == 4 and all(isinstance(v, (int, float)) for v in obj):
        obj = {"bbox_2d": obj}  # Nemotron sometimes replies with the bare box
    if isinstance(obj, list):
        if not obj:
            return None, None  # an empty list means nothing found
        obj = obj[0]
    if not isinstance(obj, dict) or "bbox_2d" not in obj:
        return None
    label = obj.get("label") if isinstance(obj.get("label"), str) else None
    b = obj["bbox_2d"]
    if b is None:
        return None, label
    if not (isinstance(b, list) and len(b) == 4 and all(isinstance(v, (int, float)) for v in b)):
        return None
    w, h = size
    x1, y1, x2, y2 = (float(v) for v in b)
    if scale == "1000":
        if max(x1, y1, x2, y2) > 1000 or min(x1, y1, x2, y2) < 0:
            return None
        x1, x2 = x1 * w / 1000, x2 * w / 1000
        y1, y2 = y1 * h / 1000, y2 * h / 1000
    x1, x2 = sorted((max(0.0, min(w, x1)), max(0.0, min(w, x2))))
    y1, y2 = sorted((max(0.0, min(h, y1)), max(0.0, min(h, y2))))
    if x2 - x1 < 1 or y2 - y1 < 1:
        return None
    return [round(x1), round(y1), round(x2), round(y2)], label


def jpeg_size(data: bytes) -> tuple:
    """(width, height) of a JPEG or PNG, read from its header."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:2] != b"\xff\xd8":
        raise ValueError("not a JPEG or PNG")
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seg_len = struct.unpack(">H", data[i + 2 : i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", data[i + 5 : i + 9])
            return w, h
        i += 2 + seg_len
    raise ValueError("JPEG size not found")


def _first_json(raw: str):
    text = re.sub(r"```(?:json)?", "", raw)
    for start, ch in enumerate(text):  # the outermost bracket comes first
        if ch in "[{":
            try:
                return json.JSONDecoder().raw_decode(text[start:])[0]
            except json.JSONDecodeError:
                continue
    return None


def _clean(raw: str) -> str:
    # Drop any reasoning block in case thinking mode slipped back on
    text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    return text.strip().strip('"').strip()


# ---------------------------------------------------------------- Ollama


def _one(jpeg: bytes, prompt: str) -> Answer:
    if not _lock.acquire(blocking=False):
        return _busy()
    try:
        return _ask(jpeg, prompt, time.monotonic() + TIMEOUT_S)
    finally:
        _lock.release()


def _busy() -> Answer:
    # Never queue: the caller asks again later with a newer picture
    return Answer(False, COULDNT_TELL, model=active_model(), error="busy: another request is running")


def _ask(jpeg: bytes, prompt: str, deadline: float) -> Answer:
    model = active_model()
    t0 = time.monotonic()
    if deadline - t0 <= 0.05:
        return Answer(False, COULDNT_TELL, model=model, error="timeout: no time left")
    try:
        r = _post(
            "/api/chat",
            {
                "model": model,
                "stream": False,
                "think": False,  # reasoning adds seconds
                "keep_alive": -1,
                "options": {"temperature": 0, "num_predict": 200, "num_ctx": CTX},
                "messages": [_message(prompt, jpeg)],
            },
            deadline - t0,
        )
        msg = r.get("message", {})
        a = Answer(True, "", model=model, seconds=time.monotonic() - t0, raw=msg.get("content", ""))
        if msg.get("thinking"):
            a.error = "thinking mode is on"  # still usable, but slow; check the model settings
        return a
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        reason = getattr(e, "reason", e)
        kind = "timeout" if "timed out" in str(reason) else "error"
        return Answer(False, COULDNT_TELL, model=model, seconds=time.monotonic() - t0, error=f"{kind}: {reason}")


def _message(prompt: str, jpeg: Optional[bytes]) -> dict:
    m = {"role": "user", "content": prompt}
    if jpeg:
        m["images"] = [base64.b64encode(jpeg).decode()]
    return m


def _post(path: str, body: dict, timeout_s: float) -> dict:
    req = urllib.request.Request(
        OLLAMA_URL + path, json.dumps(body).encode(), {"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as r:
        return json.load(r)


def _fail(a: Answer, why: str) -> Answer:
    a.ok, a.text, a.box, a.error = False, COULDNT_TELL, None, why
    return a

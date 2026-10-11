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
BUSY_WAIT_S = 3.0  # a spoken question waits this long for a find() that is running; find() itself never waits
# Ollama's default context for these models is 262144 tokens, which made qwen3-vl:8b
# take 48 GB. Every request must send the same value or Ollama reloads the model.
CTX = int(os.environ.get("SIGHTSENSE_VLM_CTX", "8192"))
BOX_SCALE = os.environ.get("SIGHTSENSE_VLM_BOX_SCALE", "")

COULDNT_TELL = "I couldn't tell"

# Every spoken answer starts from this. Measured with vlm/eval_voice.py on recorded cane frames: without
# it, most answers said "in the image" or "ahead of the camera", and object lists came in no order.
VOICE = ("You are the voice of a smart guide cane, talking to a blind person who is holding it. "
         "Speak to them as \"you\" in plain, short words. Never mention an image, photo, picture or camera. "
         "Never give distances, and never say whether it is safe to walk or whether the way is clear. ")

PROMPTS = {
    "describe": VOICE + "In one sentence of under 20 words, tell them what is in front of them. "
    "Put what matters for walking first: people, doors, steps, and furniture or things in the way.",
    "objects": VOICE + "Name the main things in front of them, grouped by where they are. Reply in exactly this form, "
    "leaving out any group with nothing in it: \"On your left: ... Ahead: ... On your right: ...\" "
    "Use one or two words for each thing, never the same thing twice, at most 3 things in each group, "
    "most noticeable first. Leave out walls, floors and ceilings.",
    # Asked before "read": without it the model read jacket logos and made up words from blurry letters
    "has_text": "Is there a sign, label, notice or screen in this picture with text large and clear enough to read? "
    "Writing on clothing, bags or logos does not count. Reply only yes or no.",
    "read": "Read out the text in this picture that is large and clear enough to read with confidence: signs, labels, "
    "screens, posters. Ignore small, blurry, cut-off or partly hidden text, and writing on clothing. "
    "Reply with only that text, most prominent first, one item per line. If there is none, reply NONE.",
    "find": "Locate the {name}. Reply only as JSON with bbox_2d as [x1, y1, x2, y2] and a label, or bbox_2d as null.",
    # Asked before "find": the box prompt alone always returns a box, even for things
    # that are not there (it boxed an exit sign as an apple). See README.md.
    "present": "Is there a {name} in this image? Reply only yes or no.",
    # Voice that navigator/commands.py could not place. Text only, no picture. Same command names.
    # Speech recognition makes mistakes, so the examples include some.
    "interpret": (
        'A blind person said this to their smart guide cane: "{text}"\n'
        "The words came from speech recognition and may have small mistakes. Pick the one command they mean:\n"
        '- object: go to or find a thing nearby (target: just the thing, like "door" or "red cup", without "on the left")\n'
        "- place: go to a named place, shop or address outside (target: the place). A room or thing inside "
        "the building, such as a bathroom, kitchen, exit or lift, is an object, not a place\n"
        "- describe: a general request to describe what is around or ahead\n"
        "- objects: a request to list the things that are around\n"
        "- read: read signs or text\n"
        "- status: how the trip is going, or where they are being taken\n"
        "- path: whether the way ahead is clear or safe to walk\n"
        "- ask: a specific question about what is in front of them, such as a colour, a count "
        "or whether something is there\n"
        "- chat: a greeting, thanks, or small talk such as how are you\n"
        "- help: what the cane can do\n"
        "- plan: getting somewhere in several steps or in a particular way, such as around something, "
        "out of a room, past people, or slowly\n"
        "- yes: agreeing, or saying go ahead\n"
        "- no: refusing\n"
        "- cancel: stop guiding\n"
        "- unknown: none of these\n"
        "Examples: \"lead me out the door\" -> object door; \"hiya\" -> chat; \"wat do u see\" -> describe; "
        "\"get me to target\" -> place Target; \"whats all around\" -> objects; \"is the floor wet\" -> ask; "
        "\"somewhere to sit\" -> object chair; \"I need the bathroom\" -> object bathroom.\n"
        'Reply only as JSON: {{"command": "...", "target": "..." or null}}'
    ),
    "ask": VOICE + 'They asked: "{question}" Answer in one sentence of under 20 words. If it is a yes-or-no '
    "question, start with Yes or No. Answer only what they asked: if they ask about one side, talk about that side only. "
    "If you cannot see what they ask about, say you can't see it.",
}

# A request with several parts, or about how to get somewhere ("get me around the table to the window").
# The model only plans: navigator/plan.py turns the steps into preferred directions, extra stops and a lower
# speed, and the LiDAR obstacle check still decides what is clear (AGENTS.md rule 4).
PROMPTS["plan"] = (
    VOICE + 'They said: "{request}"\n'
    "What the cane senses now, from its depth sensor (reliable; trust it over the picture for distances): {scene}\n"
    "Plan how the cane should guide them, as a short list of steps it can do:\n"
    '- {{"do": "find", "target": "door"}}: find a thing and lead them to it\n'
    '- {{"do": "go", "way": "left" or "ahead" or "right", "seconds": 1 to 8}}: lean that way while walking\n'
    '- {{"do": "turn", "way": "left" or "right"}}: turn that way\n'
    '- {{"do": "slow"}} or {{"do": "normal"}}: walking speed, e.g. slow near people\n'
    '- {{"do": "wait", "seconds": 1 to 5}}: stand still\n'
    '- {{"do": "say", "text": "..."}}: tell them something short\n'
    "The cane stops for obstacles by itself. Never plan to go or turn towards a side the depth sensor calls blocked, "
    "unless after a find step, when they will be somewhere else. "
    "Use at most 6 steps, as few as will do.\n"
    'Reply only as JSON: {{"say": "one short sentence telling them the plan", "steps": [...]}}'
)

INTENTS = ("object", "place", "describe", "objects", "read", "status", "path", "ask", "chat", "help", "plan", "yes",
           "no", "cancel", "unknown")

# A distance in an answer is thrown away: distances come from the LiDAR only
_DISTANCE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:m|cm|metres?|meters?|feet|foot|ft|inch(?:es)?|yards?|steps?|paces?)\b", re.I)

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
    steps: Optional[dict] = None  # plan only: {"say": ..., "steps": [...]}, checked by navigator/plan.py
    error: Optional[str] = None


# ---------------------------------------------------------------- public API


def describe(jpeg: bytes) -> Answer:
    """Say in a few words what is ahead. Returns text only."""
    a = _one(jpeg, PROMPTS["describe"])
    if not a.ok:
        return a
    text = tidy(_clean(a.raw), max_words=25)
    if not text:
        return _fail(a, "empty reply")
    a.text = text
    return a


def objects(jpeg: bytes) -> Answer:
    """The main things in view, grouped by side: "On your left: a chair. Ahead: a table." Text only."""
    a = _one(jpeg, PROMPTS["objects"])
    if not a.ok:
        return a
    text = _sides(_clean(a.raw))
    if not text:
        return _fail(a, "empty reply")
    a.text = text
    return a


def read(jpeg: bytes) -> Answer:
    """Read text and signs. text is "" when there is none."""
    if not _lock.acquire(timeout=BUSY_WAIT_S):
        return _busy()
    try:
        deadline = time.monotonic() + TIMEOUT_S  # both questions share one timeout
        gate = _ask(jpeg, PROMPTS["has_text"], deadline)
        if not gate.ok:
            return gate
        if _clean(gate.raw).lower().strip(".! ") == "no":
            gate.text = ""
            return gate
        a = _ask(jpeg, PROMPTS["read"], deadline)
        a.seconds += gate.seconds
    finally:
        _lock.release()
    if not a.ok:
        return a
    text = _clean(a.raw)
    if not text:
        return _fail(a, "empty reply")
    lines = [re.sub(r"^[\s\"'`*\-\u2022]+|[\s\"'`*]+$", "", s) for s in text.splitlines()]
    lines = [s for s in lines if s and not re.fullmatch(r"NONE\.?", s, re.IGNORECASE)]
    # Fragments with no real word in them ("HE SK CLE") are misreads, not text
    lines = [s for s in lines if re.search(r"[A-Za-z]{3,}|\d{2,}", s)]
    text = ". ".join(s.rstrip(".") for s in list(dict.fromkeys(lines))[:3])  # the 3 most prominent, once each
    a.text = " ".join(text.split()[:20])  # a bus covered in adverts is not read out in full
    return a


def ask(jpeg: bytes, question: str) -> Answer:
    """Answer a free question about the picture, e.g. "is there a chair here?". Text only.

    Sentences that state a distance are dropped. The caller must not send questions
    about whether the way is clear here; those are answered from depth.
    """
    question = re.sub(r'["\n]', " ", question).strip()[:200]
    a = _one(jpeg, PROMPTS["ask"].format(question=question))
    if not a.ok:
        return a
    text = _clean(a.raw)
    kept = [s for s in re.split(r"(?<=[.!?])\s+", text) if s and not _DISTANCE.search(s)]
    if not kept:
        return _fail(a, "empty reply" if not text else "reply only gave a distance")
    a.text = tidy(" ".join(kept), max_words=30)
    return a


def plan(jpeg: bytes, request: str, scene: str) -> Answer:
    """A few steps for navigator/plan.py. label is "plan"; .steps holds the checked plan, .text what to say.
    The model never steers: steps become preferred directions, extra stops or a lower speed only."""
    from navigator.plan import validate

    request = re.sub(r'["\n]', " ", request or "").strip()[:200]
    scene = re.sub(r'["\n]', " ", scene or "nothing measured").strip()[:400]
    a = _one(jpeg, PROMPTS["plan"].format(request=request, scene=scene))
    if not a.ok:
        return a
    checked = validate(_first_json(a.raw))
    if checked is None:
        return _fail(a, "unusable plan reply")
    a.label, a.steps = "plan", checked
    a.text = tidy(checked["say"]) if checked["say"] else ""
    return a


def interpret(text: str) -> Answer:
    """Which command a sentence the rules could not place asks for. Text only, no picture.

    label is one of INTENTS; text is the target ("" if none). The model only picks a
    command: it never steers, and "path" is still answered from depth.
    """
    text = re.sub(r'["\n]', " ", text or "").strip()[:200]
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


_ABOUT_PICTURE = [  # the model talking about the picture instead of the room; fixed after the prompt fails
    (re.compile(r"\s*,?\s*\b(?:visible |seen |shown )?(?:in|from|on|within) (?:the|this) (?:image|picture|photo|frame|scene|view)\b", re.I), ""),
    (re.compile(r"\b(?:the|this) (?:image|picture|photo|scene) (?:shows|depicts|contains|has|features)\s+", re.I), ""),
    (re.compile(r"\b(?:directly )?(?:ahead of|in front of) the camera\b", re.I), "in front of you"),
    (re.compile(r"\bthe camera\b", re.I), "you"),
    (re.compile(r"\b(?:there (?:is|are) )?no ([a-z ]+?) visible\b", re.I), r"no \1"),
]


def tidy(text: str, max_words: int = 25) -> str:
    """One or two clean sentences, ready to speak: no talk of the picture, a capital, a full stop."""
    text = re.sub(r"[*_#`]+", "", text)  # markdown
    for pattern, repl in _ABOUT_PICTURE:
        text = pattern.sub(repl, text)
    text = re.sub(r"\s+([,.!?])", r"\1", re.sub(r"\s+", " ", text)).strip(" ,")
    sentences = re.split(r"(?<=[.!?])\s+", text)
    text = " ".join(sentences[:2])
    words = text.split()
    if len(words) > max_words:  # cut runaway answers at a word, then end the sentence there
        text = " ".join(words[:max_words]).rstrip(",;:")
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    if text and text[-1] not in ".!?":
        text += "."
    return text


def _sides(text: str) -> str:
    """An objects reply as spoken sentences: "On your left: a chair. Ahead: a table and a door." """
    text = tidy(text, max_words=40)
    parts = re.split(r"\s*(?=\b(?:On your left|Ahead|On your right|In front of you)\s*:)", text, flags=re.I)
    out = []
    seen = set()
    for part in parts:
        m = re.match(r"(On your left|Ahead|On your right|In front of you)\s*:\s*(.+)", part.strip(), re.I)
        if not m:
            continue
        things = []
        for thing in re.split(r"\s*(?:,|;|\band\b)\s*", m.group(2).strip(" .;")):
            thing = re.sub(r"^(?:a|an|the|some|two|three|several)\s+", "", thing.strip(" ."), flags=re.I).lower()
            if not thing or re.fullmatch(r"(?:nothing|none|n/a|walls?|floor|ceiling)", thing) or thing in seen:
                continue
            seen.add(thing)  # the same thing is said once, on the side it was named first
            things.append(thing)
        if things:
            out.append(f"{m.group(1).capitalize()}: {', '.join(things[:3])}.")
    return " ".join(out) if out else text


def _clean(raw: str) -> str:
    # Drop any reasoning block in case thinking mode slipped back on
    text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    return text.strip().strip('"').strip()


# ---------------------------------------------------------------- Ollama


def _one(jpeg: bytes, prompt: str) -> Answer:
    if not _lock.acquire(timeout=BUSY_WAIT_S):
        return _busy()
    try:
        return _ask(jpeg, prompt, time.monotonic() + TIMEOUT_S)
    finally:
        _lock.release()


def _busy() -> Answer:
    # find() never queues: the object guide asks again later with a newer picture
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

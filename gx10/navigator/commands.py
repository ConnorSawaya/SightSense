"""Turn what the user said (the {"text": ...} voice message) into a command.

Plain pattern matching, no model, so it is instant and predictable.

    parse("guide me to the apple")  -> Command("object", "apple")
    parse("take me to Safeway")     -> Command("place", "Safeway")
    parse("what's in front of me")  -> Command("describe")
"""

import re
from dataclasses import dataclass
from typing import Optional

# Things in a room. "take me to X" with one of these is an object, not a place.
OBJECT_WORDS = {
    "apple", "banana", "orange", "bottle", "cup", "mug", "glass", "bag", "backpack", "box", "book",
    "phone", "laptop", "keys", "wallet", "door", "doorway", "exit", "chair", "seat", "table", "desk",
    "bench", "couch", "sofa", "bed", "window", "sink", "toilet", "fridge", "refrigerator", "microwave",
    "trash", "bin", "trash can", "garbage can", "elevator", "sign", "person", "dog", "plant",
    "counter", "shelf", "cabinet", "computer", "tv", "television", "screen", "light switch",
    "stairs", "staircase", "ramp", "pole", "fire hydrant",
}

# Words that mark a place to look up on the map
PLACE_WORDS = {
    "store", "shop", "supermarket", "market", "grocery", "station", "stop", "cafe", "coffee",
    "restaurant", "pharmacy", "park", "library", "school", "hospital", "bank", "mall", "hotel",
    "street", "avenue", "road", "plaza", "center", "centre", "campus", "museum", "gym",
}

ARTICLES = r"(?:the|a|an|my|some|that|this)"


@dataclass
class Command:
    kind: str  # object, place, describe, read, yes, no, cancel, status, unknown (question and interpret come from the model)
    target: Optional[str] = None


def parse(text: str) -> Command:
    raw = re.sub(r"\s+", " ", text or "").strip()
    t = raw.lower().strip(" .!?,")
    t = re.sub(r"^(?:hey|ok|okay|please|cane|sightsense)[, ]+", "", t).strip()
    t = re.sub(r"[, ]+please$", "", t)

    if re.fullmatch(r"(yes|yeah|yep|yup|go|go ahead|sure|ok|okay|correct|let's go)", t):
        return Command("yes")
    if re.fullmatch(r"(no|nope|nah|wrong)", t):
        return Command("no")
    if re.fullmatch(r"(stop|cancel|never ?mind|forget it|quit|end|stop guiding|cancel (?:that|it|guidance|navigation))", t):
        return Command("cancel")

    if re.search(r"(?:am i|are we) (?:going|heading|walking) (?:the )?(?:right|correct) way|on the right (?:way|track|path)|"
                 r"how far (?:is it|away|to go|left)|are we (?:there|close)|how much (?:further|farther|longer)", t):
        return Command("status")
    if re.search(r"\bread\b|what does (?:it|that|the sign|this) say|any signs?\b", t):
        return Command("read")
    if re.search(r"\bdescribe\b|what(?:'s| is) (?:in front|ahead|around|there)|what do you see|what can you see|where am i\b", t):
        return Command("describe")

    m = re.search(r"\b(?:find|locate|where(?:'s| is)|look for|search for)\s+(.+)", t)
    if m:
        return Command("object", _clean_target(m.group(1))[0])

    m = re.search(r"\b(?:guide|take|bring|lead|walk|get|navigate|steer|help)\s+me\s+(?:to|towards?|over to)\s+(.+)", t) or re.search(
        r"^(?:go|navigate|head)\s+(?:to|towards?)\s+(.+)", t
    )
    if m:
        target, had_article = _clean_target(m.group(1))
        if not target:
            return Command("unknown")
        original = _original_case(raw, target)
        if _is_place(target, original, had_article):
            return Command("place", original)
        return Command("object", target)

    return Command("unknown")


def _clean_target(s):
    s = s.strip(" .!?,")
    s = re.sub(r"\s+(?:please|now|for me)$", "", s)
    had_article = bool(re.match(ARTICLES + r"\s", s))
    s = re.sub(r"^" + ARTICLES + r"\s+", "", s).strip()
    return s, had_article


def _original_case(raw, target):
    i = raw.lower().rfind(target)
    return raw[i : i + len(target)] if i >= 0 else target


def _is_place(target, original, had_article):
    words = target.split()
    if target in OBJECT_WORDS or (words and words[-1] in OBJECT_WORDS):
        return False
    if any(w in PLACE_WORDS for w in words) or original[:1].isupper():
        return True  # "the train station", "Safeway" (speech recognition capitalises names)
    return not had_article  # "the kitchen" is looked for in view; "safeway" is looked up on the map

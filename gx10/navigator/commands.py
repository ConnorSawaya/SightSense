"""Turn what the user said (the {"text": ...} voice message) into a command.

Plain pattern matching, no model, so it is instant and predictable.

    parse("guide me to the apple")  -> Command("object", "apple")
    parse("take me to Safeway")     -> Command("place", "Safeway")
    parse("what's in front of me")  -> Command("describe")
    parse("am I going the right way") -> Command("status")
    parse("is the path clear")      -> Command("path")       (answered from depth, never the model)
    parse("is there a chair here?") -> Command("ask", ...)   (any other question goes to the model)
    parse("hello")                  -> Command("chat")       (greetings and thanks, answered at once)
    parse("what objects are here")  -> Command("objects")    (things by side, from the model)

Sentences people actually said on the cane are in voice_cases.py and checked by test_commands.py.
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
    kind: str  # object, place, describe, objects, read, status, path, ask, chat, yes, no, cancel, unknown ...
    target: Optional[str] = None
    side: Optional[str] = None  # "left" or "right" when the user said which side ("the door on the left")


FILLER = r"(?:uh+|um+|erm|er|hmm+|so|well|okay so|ok so|like|and|now)"
GREETING = r"(?:say )?(?:hello|hi|hey|yo|good (?:morning|afternoon|evening))(?: there)?(?: (?:cane|sightsense|buddy))?"
CHAT = (r"(?:(?:how are (?:you|we doing|things)(?: doing)?|how(?:'s| is) it going|how are we|what's up|whats up"
        r"|what's good|whats good|how do you do|nice to meet you"
        r"|thank(?:s| you)(?: (?:so|very) much)?(?: for (?:that|the help))?|cheers|good (?:job|work)|nice(?: job| work)?"
        r"|great(?: job)?|well done|awesome|cool|perfect|you're (?:great|awesome|the best))"
        r"(?: (?:buddy|mate|man|friend|cane|sightsense))?)")
# Where an object is, said after its name: kept as a side hint, taken off the name
QUALIFIER = re.compile(
    r"\s+(?:(?:that(?:'s| is) |which is )?(?:on|to|at|near|by|towards?|over (?:on|to)) (?:my|the|your) (left|right)(?: side| hand side)?"
    r"|over there|over here|right there|in front of me|ahead of me|ahead|nearby|near me|close to me|around here"
    r"|thing|things|one|stuff|thingy"
    r"|(?:on|near|by|next to|beside|behind|under|in front of|against|at) (?:the|a|my|this|that) [a-z ]+)$")


def parse(text: str) -> Command:
    # the phone's speech recognition writes what's and let's with a curly apostrophe
    raw = re.sub(r"\s+", " ", (text or "").replace("\u2019", "'").replace("\u2018", "'")).strip()
    t = raw.lower().strip(" .!?,")
    t = re.sub(r"^[a-z](?=(?:what|where|who|how|which|why)\b)", "", t)  # "jwhat": a stray letter from speech recognition
    t = re.sub(r"^(?:" + FILLER + r"[, ]+)+", "", t).strip()
    t = re.sub(r"^(?:ok|okay|please|cane|sightsense)[, ]+", "", t).strip()
    t = re.sub(r"[, ]+please$", "", t)

    # Greetings and thanks: answered at once. "Hello, where am I going" is the question after the hello.
    m = re.fullmatch(GREETING + r"[,.!? ]*(.*)", t)
    if m:
        rest = m.group(1).strip(" ,.!?")
        if not rest:
            return Command("chat")
        sub = parse(rest)
        return sub if sub.kind != "unknown" else Command("chat")
    if re.fullmatch(CHAT, t):
        return Command("chat")
    # "Can you / could you / please tell me ..." : the request inside, if the rules know it
    m = re.fullmatch(r"(?:(?:can|could|would|will) you(?: please)?|please|tell me|i want to know|i'd like to know)[, ]+(.+)", t)
    if m:
        inner = parse(m.group(1))
        if inner.kind not in ("unknown", "ask"):
            return inner

    if re.fullmatch(r"(?:(?:yes|yeah|yep|yup|sure|ok|okay|correct|right)[, ]*)?(?:go|go ahead|let's go|do it|that's it|that one)?", t) and t:
        return Command("yes")
    if re.fullmatch(r"(no|nope|nah|wrong)", t):
        return Command("no")
    if re.fullmatch(r"(stop|cancel|never ?mind|forget it|quit|end|stop guiding|cancel (?:that|it|guidance|navigation))", t):
        return Command("cancel")

    # A check of the phone's tones and speech
    if re.fullmatch(r"(?:sound|audio|speech|voice|speaker) (?:check|test)|(?:test|check) (?:the |my )?(?:sounds?|audio|speech|voice|speaker|tones?)", t):
        return Command("soundcheck")
    # About the assistant itself: answered at once, without the model
    if re.fullmatch(r"help(?: me)?|what can (?:you|i) (?:do|say|ask)(?: you)?|what do you do|(?:who|what) are you"
                    r"|how do (?:you|i) (?:work|use (?:you|this|it))|commands|instructions", t):
        return Command("help")
    if re.fullmatch(r"repeat(?: that| it)?|say (?:that|it) again|again|what did you say|pardon|come again|one more time", t):
        return Command("repeat")
    if re.search(r"\bwhat(?:'s| is) the time\b|\bwhat time is it\b|\bwhat(?:'s| is) (?:the|today's) date\b|\bwhat day is it\b", t):
        return Command("time")

    # Is the way clear? Answered from the LiDAR obstacle check, never by the model (AGENTS.md rule 4)
    if re.search(r"\b(?:is|are) (?:the |my )?(?:path|way|road|route ahead|coast)\b.*\b(?:clear|safe|free|blocked|open|ok)\b"
                 r"|\bis it (?:safe|clear|ok)\b|\b(?:can|should|may) i (?:go|walk|keep going|move|continue)\b"
                 r"|\b(?:anything|something|any obstacles?|obstacles?) (?:in front|ahead|in (?:my|the) way)"
                 r"|\bany obstacles?\b|\bclear ahead\b|\bwill i (?:hit|bump)", t):
        return Command("path")
    # How am I doing? Answered by the navigator
    if re.search(r"\b(?:am i|are we) (?:going|heading|walking|moving) (?:the )?(?:right|correct|wrong) (?:way|direction)"
                 r"|\bright (?:way|direction)\b|\bhow far\b|\bwhere(?:'s| is) it\b|\bhow (?:much )?(?:further|farther|long)\b"
                 r"|\bare we (?:there|close)\b|\bam i (?:there|close|near)\b|\bwhich way\b|\b(?:status|progress|update)\b"
                 r"|\bwhere (?:am i|are we) (?:going|headed|heading|walking)\b|\bwhere (?:are you|is this) taking me\b", t):
        return Command("status")

    if re.search(r"\bread\b|what does (?:it|that|the sign|this) say|any signs?\b", t):
        return Command("read")
    # A list of things, by side ("what objects are here"); answered by the model
    if re.search(r"\bwhat (?:are )?(?:the |all the |other )?(?:objects?|things|items|stuff)\b|\blist (?:what|the|everything|all)"
                 r"|\bwhat(?:'s| is) (?:here|in (?:this|the) room)\b|\bwhat(?:'s| is) all (?:this|that)\b", t):
        return Command("objects")
    if re.search(r"\bdescribe\b|what(?:'s| is) (?:in front|ahead|around|there)|what do you see|what can you see|where am i\b"
                 r"|\bwhat you (?:can )?see\b|\blook around\b|\bwhat(?:'s| is) going on\b", t):
        return Command("describe")

    m = re.search(r"\b(?:find|locate|where(?:'s| is)|look for|search for)\s+(.+)", t)
    if m:
        target, side = _qualified(_clean_target(m.group(1))[0])
        return Command("object", target, side) if target else Command("unknown")

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
        target, side = _qualified(target)
        return Command("object", target, side) if target else Command("unknown")

    # Any other question goes to the model, which is told not to give distances or judge safety
    if raw.rstrip().endswith("?") or re.match(
        r"(?:is|are|was|were|what|what's|whats|which|who|whose|how|does|do|did|can|could|will|would|should|tell me)\b", t
    ):
        return Command("ask", raw.strip())

    return Command("unknown")


def _clean_target(s):
    s = s.strip(" .!?,")
    s = re.sub(r"\s+(?:please|now|for me)$", "", s)
    had_article = bool(re.match(ARTICLES + r"\s", s))
    s = re.sub(r"^" + ARTICLES + r"\s+", "", s).strip()
    return s, had_article


def _qualified(target):
    """"door on the left" -> ("door", "left"); "red cup on the table" -> ("red cup", None)."""
    side = None
    while True:
        m = QUALIFIER.search(target)
        if not m or m.start() == 0:
            return target, side
        side = side or m.group(1)
        target = target[: m.start()].strip()


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

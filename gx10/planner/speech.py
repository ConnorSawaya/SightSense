"""What the cane says, and when: one sentence at a time, most important first.

Before this every part of the GX10 spoke on its own (obstacle check, direction cues, object
guide, answers), each on whatever frame it liked. Sentences a few frames apart queued up on
the phone and played back to back, and in STOP each new one cut the last off half way. Now
every sentence goes through SpeechPlan, which sends at most one per frame and only when the
phone should have finished the last:

    SAFETY   "Obstacle ahead. Stop."          sent at once, cutting into a direction or a hint (the phone
                                              cuts in on a STOP); waits for an answer to finish, since
                                              the stop tone and the wheel have already acted; not
                                              repeated within 10 s
    ANSWER   replies to what the user said     never dropped; waits its turn
    GUIDE    "Bear left", "The door is ahead"  dropped if it waits over 2 s (it is old news by then)
    INFO     "I can't see the door yet..."     only after 3 s of quiet; dropped after 4 s;
                                              the same hint not again within 15 s

While the user holds the talk button only SAFETY is sent. While the model is still working
on their question, GUIDE and INFO wait (and usually expire), so the answer comes next.

How long the phone takes to say a sentence is estimated from its words (the app speaks at
rate 0.55, about 2.6 words a second; estimate, not measured). Every number is a starting
value to tune. Standard library only.
"""

import threading
from dataclasses import dataclass
from typing import Optional

SAFETY, ANSWER, GUIDE, INFO = 0, 1, 2, 3
NAMES = {SAFETY: "safety", ANSWER: "answer", GUIDE: "guide", INFO: "info"}

WORDS_PER_S = 2.6
LEAD_S = 0.4  # the phone's start-up before the first word
GAP_S = 0.6  # silence between two sentences
QUIET_BEFORE_INFO_S = 3.0  # a hint only after this much silence
TTL_S = {SAFETY: 6.0, ANSWER: 20.0, GUIDE: 2.0, INFO: 4.0}  # older than this: not said
REPEAT_S = {SAFETY: 10.0, ANSWER: 0.0, GUIDE: 4.0, INFO: 15.0}  # the same sentence not again within this
LISTEN_HOLD_S = 8.0  # after the talk button, hold everything but SAFETY this long, or until words arrive


def speaking_time(text: str) -> float:
    return LEAD_S + len(text.split()) / WORDS_PER_S


@dataclass
class _Item:
    text: str
    priority: int
    t: float


class SpeechPlan:
    def __init__(self):
        self._lock = threading.Lock()  # added to from the frame thread and the network thread
        self._queue = []
        self._busy_until = -1e9  # when the phone should have finished the last sentence
        self._busy_priority = INFO  # what that sentence was
        self._said = {}  # text -> when it was last sent
        self._hold_until = -1e9

    def add(self, text: Optional[str], priority: int, now: float):
        if not text:
            return
        with self._lock:
            if priority in (GUIDE, INFO):  # only the newest of these matters
                self._queue = [q for q in self._queue if q.priority != priority]
            elif any(q.text == text for q in self._queue):
                return
            self._queue.append(_Item(text, priority, now))

    def listening(self, now: float):
        """The talk button went down: the user is about to speak."""
        with self._lock:
            self._hold_until = now + LISTEN_HOLD_S

    def heard(self):
        """The user's words arrived (or listening ended)."""
        with self._lock:
            self._hold_until = -1e9

    def idle(self, now: float) -> bool:
        with self._lock:
            return not self._queue and now >= self._busy_until + GAP_S

    def next(self, now: float, thinking: bool = False) -> Optional[str]:
        """The sentence to send with this frame, or None. thinking: the model is still on the user's question."""
        with self._lock:
            self._queue = [q for q in self._queue if now - q.t <= TTL_S[q.priority]
                           and now - self._said.get(q.text, -1e9) >= REPEAT_S[q.priority]]
            if not self._queue:
                return None
            top = min(self._queue, key=lambda q: (q.priority, q.t))
            if top.priority == SAFETY:
                if now < self._busy_until and self._busy_priority <= ANSWER:
                    return None  # an answer the user asked for is not cut off; the stop tone has already sounded
            else:
                if now < self._hold_until or now < self._busy_until + GAP_S:
                    return None
                if top.priority >= GUIDE and thinking:
                    return None
                if top.priority == INFO and now < self._busy_until + QUIET_BEFORE_INFO_S:
                    return None
            self._queue.remove(top)
            self._said[top.text] = now
            self._busy_until = now + speaking_time(top.text)
            self._busy_priority = top.priority
            return top.text

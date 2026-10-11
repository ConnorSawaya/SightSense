"""Step plans from the vision-language model, carried out one step at a time.

"Get me around the table to the window" goes to vlm.plan() with the picture and what the LiDAR
senses; the model answers with a few steps from a fixed list, and PlanRunner does them:

    {"do": "find", "target": "window"}           the object guide finds it and leads there
    {"do": "go", "way": "left", "seconds": 3}     lean that way for a few seconds of walking
    {"do": "turn", "way": "right"}                turn that way (about 2.5 s of walking)
    {"do": "slow"} / {"do": "normal"}             walking speed: half, or the dashboard's setting
    {"do": "wait", "seconds": 2}                  stand still
    {"do": "say", "text": "..."}                  tell the user something short

Nothing here touches the wheel. Each step gives a desired bearing (as the object guide and the route
do), an extra stop, or a lower speed. The obstacle check still decides clear or blocked from depth
and wins (AGENTS.md rule 4); a timed step only counts time while the user is not stopped.
Standard library only.
"""

from typing import Optional

from .object_guide import ARRIVED, CONFIRMING, IDLE

MAX_STEPS = 6
WAYS = {"left": -25.0, "ahead": 0.0, "right": 25.0}
TURN_DEG, TURN_S = 60.0, 2.5
SLOW = 0.5  # share of the speed level for a "slow" step


def validate(obj) -> Optional[dict]:
    """The model's reply as {"say": str, "steps": [...]}, keeping only steps that are well formed."""
    if not isinstance(obj, dict) or not isinstance(obj.get("steps"), list):
        return None
    steps = []
    for s in obj["steps"][:3 * MAX_STEPS]:  # bad steps are dropped first; then the first MAX_STEPS good ones
        if len(steps) >= MAX_STEPS:
            break
        if not isinstance(s, dict):
            continue
        do = str(s.get("do", "")).lower()
        if do == "find" and isinstance(s.get("target"), str) and s["target"].strip():
            steps.append({"do": "find", "target": s["target"].strip(" .")[:40].lower()})
        elif do in ("go", "turn") and str(s.get("way", "")).lower() in WAYS and (do == "go" or s["way"] != "ahead"):
            secs = s.get("seconds", 3 if do == "go" else TURN_S)
            secs = float(secs) if isinstance(secs, (int, float)) and not isinstance(secs, bool) else 3.0
            steps.append({"do": do, "way": str(s["way"]).lower(), "seconds": max(1.0, min(8.0, secs))})
        elif do in ("slow", "normal"):
            steps.append({"do": do})
        elif do == "wait":
            secs = s.get("seconds", 2)
            secs = float(secs) if isinstance(secs, (int, float)) and not isinstance(secs, bool) else 2.0
            steps.append({"do": "wait", "seconds": max(1.0, min(5.0, secs))})
        elif do == "say" and isinstance(s.get("text"), str) and s["text"].strip():
            steps.append({"do": "say", "text": s["text"].strip()[:120]})
    if not steps:
        return None
    say = obj.get("say") if isinstance(obj.get("say"), str) else ""
    return {"say": say.strip()[:160], "steps": steps}


GUARD_M = 1.0  # a side this close (or unknown) is not leaned into by a step taken from where the user stands
SIDES = {"left": (-30, -20, -10), "ahead": (0,), "right": (10, 20, 30)}


def guard(plan: dict, clearance: dict):
    """Check a plan against the depth sensor before it starts. Steps done from where the user stands (those
    before the first "find") that lean towards a side under GUARD_M, or unknown, are dropped. If every side
    is like that and the plan would move them, there is no plan. Returns (plan or None, sentence or None).
    Later steps happen somewhere else and are left to the obstacle check there."""
    def room(way):
        known = [clearance.get(h) for h in SIDES[way] if clearance.get(h) is not None]
        return max(known) if known else 0.0
    open_ = {w: room(w) >= GUARD_M for w in SIDES}
    steps, here = [], True
    for s in plan["steps"]:
        if s["do"] == "find":
            here = False
        if here and s["do"] in ("go", "turn") and not open_[s["way"]]:
            continue
        steps.append(s)
    moves_here = any(s["do"] in ("go", "turn", "find") for s in plan["steps"])
    if not any(open_.values()) and moves_here:
        return None, "Something is close on every side. Step back, then ask again."
    if not any(s["do"] in ("go", "turn", "find") for s in steps):
        return None, "I can't see a way to do that from here. Turn slowly, then ask again."
    return dict(plan, steps=steps), None


def describe_step(step: dict) -> str:
    do = step["do"]
    if do == "find":
        return f"finding the {step['target']}"
    if do == "go":
        return "keeping " + ("straight" if step["way"] == "ahead" else f"to the {step['way']}")
    if do == "turn":
        return f"turning {step['way']}"
    return {"slow": "slowing down", "normal": "back to normal speed", "wait": "waiting", "say": "telling you"}[do]


class PlanRunner:
    def __init__(self, plan: dict, objects, clock_start: float):
        self.steps = plan["steps"]
        self.say = plan.get("say") or ""
        self.objects = objects  # the navigator's ObjectGuide
        self.i = 0
        self.speed = None  # None, or a share of the speed level while slowed
        self._elapsed = 0.0
        self._last = clock_start
        self._started_step = False
        self.done = False

    @property
    def status(self) -> str:
        if self.done:
            return "The plan is done."
        return f"Step {self.i + 1} of {len(self.steps)}: {describe_step(self.steps[self.i])}."

    def update(self, f, detections, now: float, stopped: bool) -> dict:
        """One frame. Returns {"desired": deg|None, "stop": bool, "speech": [..], "state": str}."""
        out = {"desired": None, "stop": False, "speech": [], "state": "DONE"}
        dt, self._last = max(0.0, now - self._last), now
        while not self.done:
            step = self.steps[self.i]
            out["state"] = f"{self.i + 1}/{len(self.steps)} {step['do']}"
            do = step["do"]
            if do == "say":
                out["speech"].append(step["text"])
                self._next()
                continue
            if do in ("slow", "normal"):
                self.speed = SLOW if do == "slow" else None
                self._next()
                continue
            if do == "find":
                if not self._started_step:
                    self._started_step = True
                    out["speech"].append(self.objects.start(step["target"]))
                s = self.objects.update(f, detections)
                if s.state == CONFIRMING:
                    self.objects.confirm(True)  # the plan was the user's request: no second "yes"
                if s.speech and "Say yes" not in s.speech:
                    out["speech"].append(s.speech)
                out["desired"], out["stop"] = s.desired_bearing, s.stop
                if s.state == ARRIVED:
                    self._next()
                elif s.state == IDLE and self._started_step and s.speech:  # gave up or lost it
                    out["speech"].append("Stopping the plan.")
                    self.done = True
                break
            # timed steps: go, turn, wait. Time counts only while walking (a stop from depth pauses them)
            if not stopped or do == "wait":
                self._elapsed += dt
            if do == "wait":
                out["stop"] = True
            else:
                deg = WAYS[step["way"]] if do == "go" else (TURN_DEG if step["way"] == "right" else -TURN_DEG)
                out["desired"] = deg
            if self._elapsed >= step["seconds"]:
                self._next()
                continue
            break
        if self.done:
            out["state"] = "DONE"
        return out

    def _next(self):
        self.i += 1
        self._elapsed, self._started_step = 0.0, False
        if self.i >= len(self.steps):
            self.done = True
            self.speed = None

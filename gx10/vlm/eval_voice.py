"""Mock test of the voice assistant: what it does with real sentences and real pictures.

    ../../venv-yolo/bin/python -m vlm.eval_voice              (from gx10/, on the GX10; needs Ollama)
    ../../venv-yolo/bin/python -m vlm.eval_voice --routes     routing only, no model

1. Routing: each sentence in navigator/voice_cases.py through the rules, then the
   model for the ones the rules send to it. Checks the command and the target.
2. Answers: phone frames saved from recordings, each asked the questions people
   asked on the cane. Every answer is checked: short, no "image"/"camera" talk, no
   distances, no safety judgement, a full sentence, under 3 s. All answers are
   printed so a person can read them too.

Frames are read from ../../recordings (not committed). Nothing here changes the
running service.
"""

import argparse
import re
import statistics
import sys
import time
from pathlib import Path

from navigator import commands
from navigator.voice_cases import ROUTES

import vlm

REC = Path(__file__).resolve().parents[3] / "recordings"

# (recording, frame number or phone clock time, what is in it) - chosen by looking at them
SCENES = [
    ("20261011-105137", 75776.6, "white table with tools and a box, the cane session of 11 Oct"),
    ("20261011-105137", 75803.5, "same session, computer to the right"),
    ("20261011-105137", 75715.8, "same session, 'read the sign' asked here"),
    ("20261011-002739", 38571.9, "'what are the objects we see here' asked here"),
    ("20261010-190000", 1340, "house: hallway with a front door"),
    ("20261010-190000", 1480, "house: living room, couch and plants"),
    ("20261010-165037", 400, "table with people and laptops"),
]

QUESTIONS = [
    ("describe", None),
    ("objects", None),
    ("read", None),
    ("ask", "is there a person here?"),
    ("ask", "what's on my left"),
    ("ask", "how many chairs are there"),
]

BANNED = re.compile(r"\b(image|photo|picture|camera|depicts?)\b|\b(?:the|this) frame\b", re.I)
SAFETY = re.compile(r"\b(safe|unsafe|path is clear|way is clear|no obstacles?)\b", re.I)
DISTANCE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:m|cm|metres?|meters?|feet|foot|ft|inch(?:es)?|yards?|steps?)\b", re.I)


def problems(kind, text, seconds, ok):
    p = []
    if not ok:
        return ["no answer"]
    words = len(text.split())
    if kind != "read" and words > 25:
        p.append(f"{words} words")
    if kind == "read" and words > 30:
        p.append(f"read {words} words")
    if BANNED.search(text):
        p.append("talks about the image/camera")
    if SAFETY.search(text):
        p.append("judges safety")
    if DISTANCE.search(text):
        p.append("gives a distance")
    if text and not re.search(r"[.!?]$", text.strip()):
        p.append("not a full sentence")
    if seconds > 3.0:
        p.append(f"{seconds:.1f} s")
    return p


def frame_at(rec, at):
    from navigator.frame import decode

    files = sorted((REC / rec).glob("*.bin"))
    if isinstance(at, int):
        path = files[at]
    else:
        path = min(files, key=lambda p: abs(float(p.stem.split("-")[1]) - at))
    return decode(path.read_bytes())


def run_routes(use_model):
    bad = 0
    for text, want_kind, want_target in ROUTES:
        c = commands.parse(text)
        by = "rules"
        if use_model and c.kind == "unknown":
            a = vlm.interpret(text)
            c, by = commands.Command(a.label or "unknown", a.text or None), "model"
        ok = c.kind == want_kind and (want_target is None or (c.target or "").lower() == want_target.lower())
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {text!r:48} -> {c.kind} {c.target or ''}  ({by})"
              + ("" if ok else f"   wanted {want_kind} {want_target or ''}"))
    print(f"routing: {len(ROUTES) - bad}/{len(ROUTES)} right\n")
    return bad


def run_answers(scene_filter=None):
    import ingest.server as srv
    from ingest.server import UprightVLM, turn_for

    side_hints = getattr(srv, "side_hints", lambda f: None)  # newer service code passes detector hints

    up = UprightVLM()
    rows, times = [], []
    for rec, at, what in SCENES:
        if scene_filter and scene_filter not in what:
            continue
        try:
            f = frame_at(rec, at)
        except (IndexError, ValueError, FileNotFoundError) as e:
            print(f"skip {rec} {at}: {e!r}")
            continue
        up.turn = turn_for(f.pose)
        up.hints = side_hints(f)  # what the detector sees, by side, if the service gives hints
        print(f"--- {what}  ({rec} @ {at})")
        for kind, q in QUESTIONS:
            t0 = time.monotonic()
            a = up.ask(f.jpeg, q) if kind == "ask" else getattr(up, kind)(f.jpeg)
            s = time.monotonic() - t0
            times.append(s)
            text = a.text if a.ok else f"[{a.error}]"
            if kind == "read" and a.ok:  # as navigator.py says it
                text = f"It says: {a.text.rstrip('.')}." if a.text else "I don't see any text to read."
            p = problems(kind, text if a.ok else "", s, a.ok)
            rows.append(p)
            print(f"  {(q or kind)[:36]:36} {s:4.1f}s  {text}" + (f"   <-- {', '.join(p)}" if p else ""))
    n = len(rows)
    good = sum(not p for p in rows)
    print(f"\nanswers: {good}/{n} with no problem found; median {statistics.median(times):.2f} s, "
          f"slowest {max(times):.2f} s")
    return n - good


# Signs that must be read: (name, picture source, words that must be in the answer). "" means no text.
SIGNS = [
    ("EXIT sign test picture", "test_images/sign_exit.jpg", ("EXIT",)),
    ("empty room", "test_images/empty_room.jpg", ()),
    ("WET FLOOR pasted on the hallway", ("WET FLOOR", (0, 200, 255)), ("WET FLOOR",)),
    ("Room 204 pasted on the hallway", ("Room 204", (255, 255, 255)), ("204",)),
    ("RESTROOMS pasted on the hallway", ("RESTROOMS", (255, 255, 255)), ("RESTROOMS",)),
]


def run_signs():
    import cv2
    import numpy as np

    from ingest.upright import rotate_jpeg, turn_for

    f = frame_at("20261010-190000", 1340)
    base = cv2.imdecode(np.frombuffer(rotate_jpeg(f.jpeg, turn_for(f.pose)), np.uint8), cv2.IMREAD_COLOR)
    bad = 0
    print("--- reading")
    for name, src, want in SIGNS:
        if isinstance(src, str):
            jpeg = (Path(__file__).parent / src).read_bytes()
        else:
            img, (h, w) = base.copy(), base.shape[:2]
            cv2.rectangle(img, (w // 2 - 150, h // 3 - 50), (w // 2 + 150, h // 3 + 30), (40, 40, 40), -1)
            cv2.putText(img, src[0], (w // 2 - 135, h // 3 + 5), cv2.FONT_HERSHEY_SIMPLEX, 1.3, src[1], 3, cv2.LINE_AA)
            jpeg = cv2.imencode(".jpg", img)[1].tobytes()
        t0 = time.monotonic()
        a = vlm.read(jpeg)
        s = time.monotonic() - t0
        ok = a.ok and (all(w.lower() in a.text.lower() for w in want) if want else a.text == "")
        bad += not ok
        print(f"  {'ok ' if ok else 'BAD'} {name:34} {s:4.1f}s  {a.text!r}")
    print(f"reading: {len(SIGNS) - bad}/{len(SIGNS)} right\n")
    return bad


PLAN_REQUESTS = ["get me around the table to the window", "take me out of this room", "walk me past the people slowly",
                 "go to the door and then turn left"]


def run_plans():
    """Plans for real scenes: well formed, and no step leaning towards a side depth says is blocked under 1 m."""
    from detector.detector import Detector
    from ingest.server import UprightVLM, locate
    from ingest.upright import box_back, decode_upright, turn_for
    from planner.obstacle import check
    from planner.obstacle_talk import LEFT_SIDE, RIGHT_SIDE, scene_words
    import numpy as np

    det, up, bad, n, times = Detector(hazards=[]), UprightVLM(), 0, 0, []
    print("--- plans")
    for rec, at, what in SCENES[2:6]:
        f = frame_at(rec, at)
        d = np.frombuffer(f.depth_mm, np.uint16).reshape(f.depth_h, f.depth_w)
        c = np.frombuffer(f.conf, np.uint8).reshape(f.depth_h, f.depth_w)
        r = check(d, c, f.fx, f.fy, f.cx, f.cy, f.pose)
        turn = turn_for(f.pose)
        dets = det.detect_image(decode_upright(f.jpeg, turn), conf=0.4)
        for x in dets:
            x.box = box_back(x.box, turn, f.rgb_w, f.rgb_h)
            locate(x, f, d, c)
        scene = scene_words(r.clearance, dets)
        print(f"  {what}\n    depth: {scene}")
        for req in PLAN_REQUESTS:
            t0 = time.monotonic()
            a = vlm.plan(__import__("ingest.upright", fromlist=["rotate_jpeg"]).rotate_jpeg(f.jpeg, turn), req, scene)
            s = time.monotonic() - t0
            times.append(s)
            n += 1
            problems = []
            if not a.ok or a.steps is None:
                problems.append(f"no plan ({a.error})")
            else:
                from navigator.plan import guard

                checked, note = guard(a.steps, r.clearance)
                if checked is None:
                    a.text, a.steps = note, {"steps": []}
                for st in (checked or {"steps": []})["steps"]:
                    if st["do"] == "find":
                        break  # later steps happen somewhere else
                    side = {"left": LEFT_SIDE, "right": RIGHT_SIDE}.get(st.get("way"))
                    if st["do"] in ("go", "turn") and side:
                        room = [r.clearance.get(h) for h in side if r.clearance.get(h) is not None]
                        if room and max(room) < 1.0:
                            problems.append(f"leans {st['way']} into something {max(room):.1f} m away")
            bad += bool(problems)
            steps = "; ".join(" ".join(str(v) for k, v in st.items() if k != "do" or True) for st in (a.steps or {}).get("steps", []))
            print(f"    {req!r:44} {s:4.1f}s  {a.text!r}  [{steps}]" + (f"   <-- {', '.join(problems)}" if problems else ""))
    print(f"plans: {n - bad}/{n} with no problem found; median {statistics.median(times):.2f} s\n")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--routes", action="store_true", help="routing only, rules only, no model")
    ap.add_argument("--scene", help="only scenes whose description contains this")
    ap.add_argument("--plans", action="store_true", help="only the step plans")
    a = ap.parse_args()
    if a.routes:
        sys.exit(1 if run_routes(False) else 0)
    print("model:", vlm.warm())
    if a.plans:
        sys.exit(1 if run_plans() else 0)
    bad = run_routes(True) + run_signs() + run_answers(a.scene) + run_plans()
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

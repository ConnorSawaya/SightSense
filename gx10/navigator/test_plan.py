"""Step plans from the model. python3 -m unittest navigator.test_plan (from gx10/)."""

import unittest
from types import SimpleNamespace

from . import fake
from .navigator import Navigator
from .object_guide import ARRIVED, CONFIRMING, GUIDING, IDLE, SEARCHING
from .plan import PlanRunner, validate


class FakeGuide:
    """Stands in for ObjectGuide: finds the thing after `find_after` frames, arrives after `arrive_after`."""

    def __init__(self, find_after=2, arrive_after=4, never=False):
        self.n, self.find_after, self.arrive_after, self.never = 0, find_after, arrive_after, never
        self.confirmed = False

    def start(self, name, side=None):
        self.name, self.n = name, 0
        return f"Looking for the {name}."

    def confirm(self, yes):
        self.confirmed = yes

    def update(self, f, detections=None):
        self.n += 1
        if self.never:
            return SimpleNamespace(state=IDLE if self.n > 3 else SEARCHING, desired_bearing=None, stop=False,
                                   speech=f"I couldn't find the {self.name}." if self.n > 3 else None)
        if self.n < self.find_after:
            return SimpleNamespace(state=SEARCHING, desired_bearing=None, stop=False, speech=None)
        if self.n == self.find_after:
            return SimpleNamespace(state=CONFIRMING, desired_bearing=-10.0, stop=False, speech=f"{self.name}, 2 metres. Say yes to go.")
        if self.n < self.arrive_after:
            return SimpleNamespace(state=GUIDING, desired_bearing=-10.0, stop=False, speech=None)
        return SimpleNamespace(state=ARRIVED, desired_bearing=None, stop=True, speech=f"The {self.name} is within reach.")


def run(r, frames, dt=0.1, start=0.0, stopped=lambda i: False):
    out = []
    for i in range(frames):
        out.append(r.update(None, None, start + (i + 1) * dt, stopped(i)))
        if r.done:
            break
    return out


class Validate(unittest.TestCase):
    def test_keeps_only_known_steps(self):
        p = validate({"say": "Around the table, then the window.", "steps": [
            {"do": "go", "way": "left", "seconds": 30}, {"do": "fly"}, {"do": "find", "target": "Window."},
            {"do": "turn", "way": "ahead"}, {"do": "slow"}, {"do": "wait", "seconds": "long"}, {"do": "say", "text": "Nearly there."},
            {"do": "normal"}]})
        self.assertEqual([s["do"] for s in p["steps"]], ["go", "find", "slow", "wait", "say", "normal"][:6])
        self.assertEqual(p["steps"][0]["seconds"], 8.0)  # clamped
        self.assertEqual(p["steps"][1]["target"], "window")

    def test_nothing_usable(self):
        for bad in (None, [], {"steps": "go left"}, {"steps": [{"do": "jump"}]}):
            self.assertIsNone(validate(bad))


class Guard(unittest.TestCase):
    ALL = (-30, -20, -10, 0, 10, 20, 30)

    def cl(self, left, ahead, right):
        return {h: (left if h < 0 else ahead if h == 0 else right) for h in self.ALL}

    def test_a_turn_into_something_close_is_dropped(self):
        from .plan import guard

        plan = {"say": "", "steps": [{"do": "go", "way": "left", "seconds": 2}, {"do": "go", "way": "ahead", "seconds": 3}]}
        checked, note = guard(plan, self.cl(0.6, 3.0, 2.0))
        self.assertEqual([s["way"] for s in checked["steps"]], ["ahead"])
        self.assertIsNone(note)

    def test_steps_after_a_find_are_left_alone(self):
        from .plan import guard

        plan = {"say": "", "steps": [{"do": "find", "target": "door"}, {"do": "turn", "way": "left", "seconds": 2.5}]}
        checked, _ = guard(plan, self.cl(0.6, 3.0, 2.0))
        self.assertEqual(len(checked["steps"]), 2)  # the turn happens at the door, not here

    def test_boxed_in(self):
        from .plan import guard

        plan = {"say": "", "steps": [{"do": "find", "target": "door"}]}
        self.assertEqual(guard(plan, self.cl(0.6, 0.6, None)),
                         (None, "Something is close on every side. Step back, then ask again."))


class Runner(unittest.TestCase):
    def test_go_then_find(self):
        guide = FakeGuide()
        r = PlanRunner({"say": "", "steps": [{"do": "go", "way": "left", "seconds": 1}, {"do": "find", "target": "window"}]},
                       guide, 0.0)
        out = run(r, 40)
        self.assertEqual(out[0]["desired"], -25.0)
        speech = [s for o in out for s in o["speech"]]
        self.assertEqual(speech, ["Looking for the window.", "The window is within reach."])  # no "Say yes": the plan was the request
        self.assertTrue(guide.confirmed)
        self.assertTrue(r.done)

    def test_timed_steps_wait_while_stopped(self):
        r = PlanRunner({"say": "", "steps": [{"do": "go", "way": "right", "seconds": 1}]}, FakeGuide(), 0.0)
        out = run(r, 30, stopped=lambda i: i < 15)  # stopped by depth for the first 1.5 s
        self.assertGreaterEqual(len(out), 25)  # 1.5 s stopped + 1 s walking

    def test_slow_wait_and_say(self):
        r = PlanRunner({"say": "", "steps": [{"do": "slow"}, {"do": "wait", "seconds": 1}, {"do": "say", "text": "Go now."}]},
                       FakeGuide(), 0.0)
        first = r.update(None, None, 0.1, False)
        self.assertEqual((r.speed, first["stop"]), (0.5, True))  # slowed, and standing still for the wait
        out = run(r, 20, start=0.1)
        self.assertIn("Go now.", [s for o in out for s in o["speech"]])
        self.assertIsNone(r.speed)  # back to normal when the plan ends

    def test_gives_up_when_the_thing_is_not_found(self):
        r = PlanRunner({"say": "", "steps": [{"do": "find", "target": "exit"}, {"do": "go", "way": "ahead"}]},
                       FakeGuide(never=True), 0.0)
        speech = [s for o in run(r, 20) for s in o["speech"]]
        self.assertEqual(speech[-2:], ["I couldn't find the exit.", "Stopping the plan."])
        self.assertTrue(r.done)


class PlanningVLM:
    def __init__(self, reply):
        self.reply, self.asked = reply, None

    def plan(self, jpeg, request, scene):
        self.asked = (request, scene)
        return SimpleNamespace(ok=True, text="Keeping left of the table, then to the window.", steps=self.reply, seconds=0.5)

    def find(self, jpeg, name):
        return SimpleNamespace(ok=True, box=None, text=f"I don't see the {name}.")


class Whole(unittest.TestCase):
    def test_from_voice_to_steps(self):
        vlm = PlanningVLM({"say": "x", "steps": [{"do": "go", "way": "left", "seconds": 1}]})
        clock = [0.0]
        nav = Navigator(vlm, clock=lambda: clock[0])
        nav.scene = "ahead blocked at 0.8 m; left open to 3.0 m; right blocked at 0.9 m"
        self.assertEqual(nav.on_voice("get me around the table to the window").kind, "plan")
        said, desired = [], []
        import time
        for i in range(40):
            clock[0] = i * 0.1
            g = nav.on_frame(fake.frame(fake.pose()))
            desired.append(g.desired_bearing)
            if g.speech:
                said.append(g.speech)
            time.sleep(0.005)
        self.assertEqual(vlm.asked[1], "ahead blocked at 0.8 m; left open to 3.0 m; right blocked at 0.9 m")
        self.assertIn("Keeping left of the table, then to the window.", said)
        self.assertIn(-25.0, desired)  # leaning left, as planned; the obstacle check still decides
        self.assertIn("Done.", said)
        self.assertEqual(nav.mode, "idle")

    def test_cancel_stops_the_plan(self):
        vlm = PlanningVLM({"say": "x", "steps": [{"do": "go", "way": "left", "seconds": 8}]})
        nav = Navigator(vlm)
        nav.on_voice("take me out of this room")
        import time
        for _ in range(10):
            nav.on_frame(fake.frame(fake.pose()))
            time.sleep(0.01)
        self.assertEqual(nav.mode, "plan")
        nav.on_voice("stop")
        self.assertEqual((nav.mode, nav.plan), ("idle", None))


if __name__ == "__main__":
    unittest.main()

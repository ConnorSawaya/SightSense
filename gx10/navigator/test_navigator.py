"""Tests on fake frames, no phone or model needed: python3 -m unittest navigator.test_navigator (from gx10/)."""

import math
import time
import unittest

from . import fake
from .commands import parse
from .frame import box_distance, camera_to_world, decode, encode, ground_bearing, pixel_to_camera, world_to_camera
from .navigator import Navigator
from .object_guide import ARRIVED, CONFIRMING, GUIDING, IDLE, SEARCHING, ObjectGuide
from .route import RouteFollower

APPLE = (-0.5, 0.05, -2.5)  # on the floor, 2.5 m ahead and half a metre left


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def run(guide_or_nav, clock, make_frame, seconds, until=None):
    """Feed frames at 15 per second of fake time; return every step. Gives worker threads real time to finish."""
    steps = []
    for _ in range(int(seconds * 15)):
        clock.t += 1 / 15
        f = make_frame()
        s = guide_or_nav.update(f) if hasattr(guide_or_nav, "update") else guide_or_nav.on_frame(f)
        steps.append(s)
        if until and until(s):
            break
        time.sleep(0.002)
    return steps


def said(steps):
    return [s.speech for s in steps if s.speech]


class Geometry(unittest.TestCase):
    def test_encode_decode(self):
        f = fake.frame(fake.pose(), APPLE, seq=7, lat=37.0, lon=-122.0, gps_acc_m=5.0, heading_deg=90.0)
        g = decode(encode(f))
        self.assertEqual((g.seq, g.depth_w, g.depth_h, g.lat, g.heading_deg), (7, 256, 192, 37.0, 90.0))
        self.assertEqual(list(g.depth_mm), list(f.depth_mm))
        self.assertEqual(g.conf, f.conf)
        self.assertEqual(g.jpeg, f.jpeg)

    def test_pixel_world_round_trip(self):
        p = fake.pose(x=1, z=2, yaw_deg=30, roll_deg=90)
        f = fake.frame(p)
        w = camera_to_world(p, pixel_to_camera(f, 40, 150, 2.0))
        u, v, d = fake.project(p, w)
        self.assertAlmostEqual(u, 40, 6)
        self.assertAlmostEqual(v, 150, 6)
        self.assertAlmostEqual(d, 2.0, 6)
        self.assertAlmostEqual(world_to_camera(p, w)[2], -2.0, 6)

    def test_bearing_signs(self):
        self.assertAlmostEqual(ground_bearing(fake.pose(), (0, 0, -3)), 0, 6)
        self.assertGreater(ground_bearing(fake.pose(), (1, 0, -3)), 0)  # right is positive
        self.assertLess(ground_bearing(fake.pose(), (-1, 0, -3)), 0)
        self.assertAlmostEqual(ground_bearing(fake.pose(yaw_deg=90), (0, 0, -3)), 90, 6)  # turned left: it is now right

    def test_bearing_ignores_mount_and_tilt(self):
        want = math.degrees(math.atan2(-0.5, 2.5))
        for kw in ({}, {"pitch_deg": -45}, {"roll_deg": 90}, {"roll_deg": -90, "pitch_deg": -30}):
            self.assertAlmostEqual(ground_bearing(fake.pose(**kw), APPLE), want, 6, kw)

    def test_box_distance(self):
        p = fake.pose()
        f = fake.frame(p, APPLE)
        box = fake.FakeFinder(APPLE)(f.jpeg, "apple").box
        d, u, v = box_distance(f, box)
        self.assertAlmostEqual(d, fake.project(p, APPLE)[2], 2)

    def test_box_distance_needs_good_readings(self):
        f = fake.frame(fake.pose(), APPLE)
        f.conf = bytes(len(f.conf))  # all low confidence
        box = fake.FakeFinder(APPLE)(f.jpeg, "apple").box
        self.assertIsNone(box_distance(f, box)[0])


class GuideToObject(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.finder = fake.FakeFinder(APPLE)
        self.guide = ObjectGuide(self.finder, self.clock)

    def find_and_confirm(self, p):
        self.assertEqual(self.guide.start("apple"), "Looking for the apple.")
        steps = run(self.guide, self.clock, lambda: fake.frame(p, APPLE), 3, until=lambda s: s.state == CONFIRMING)
        self.assertEqual(steps[-1].state, CONFIRMING)
        return steps

    def test_find_confirm_guide_arrive(self):
        p = [fake.pose()]
        steps = self.find_and_confirm(p[0])
        self.assertEqual(said(steps), ["Apple, 2.5 metres, slightly left. Say yes to go."])
        self.assertTrue(all(s.desired_bearing is None for s in steps))  # no steering before "yes"
        self.assertEqual(self.guide.confirm(True), "Going to the apple.")

        # Walk straight at it, 0.02 m per frame (0.3 m/s); it leaves the picture near the end
        heading = math.atan2(APPLE[0], -APPLE[2])
        pos = [0.0]

        def walk():
            pos[0] += 0.02
            p[0] = fake.pose(x=math.sin(heading) * pos[0], z=-math.cos(heading) * pos[0])
            return fake.frame(p[0], APPLE)

        steps = run(self.guide, self.clock, walk, 20, until=lambda s: s.state == ARRIVED)
        guiding = [s for s in steps if s.state == GUIDING]
        self.assertTrue(guiding)
        for s in guiding:
            self.assertAlmostEqual(s.desired_bearing, math.degrees(heading), delta=2)
        self.assertEqual(steps[-1].state, ARRIVED)
        self.assertTrue(steps[-1].stop)
        self.assertLess(steps[-1].distance_m, 0.8)
        self.assertIn("The apple is within reach.", said(steps))

    def test_guidance_follows_turns(self):
        self.find_and_confirm(fake.pose())
        self.guide.confirm(True)
        self.finder.obj = None  # out of sight from now on; the stored point carries on
        s = run(self.guide, self.clock, lambda: fake.frame(fake.pose(yaw_deg=40)), 0.2)[-1]
        self.assertAlmostEqual(s.desired_bearing, math.degrees(math.atan2(-0.5, 2.5)) + 40, delta=1)

    def test_no_means_cancel(self):
        self.find_and_confirm(fake.pose())
        self.assertEqual(self.guide.confirm(False), "Cancelled.")
        self.assertEqual(self.guide.update(fake.frame(fake.pose())).state, IDLE)

    def test_tracking_reset_then_lost(self):
        self.find_and_confirm(fake.pose())
        self.guide.confirm(True)
        self.finder.obj = None
        steps = run(self.guide, self.clock, lambda: fake.frame(fake.pose(), tracking="notAvailable"), 12)
        self.assertIsNone(steps[0].desired_bearing)  # stored point dropped at once
        self.assertEqual(steps[-1].state, IDLE)
        self.assertIn("I lost the apple.", said(steps))

    def test_pose_jump_drops_target(self):
        self.find_and_confirm(fake.pose())
        self.guide.confirm(True)
        self.finder.obj = None
        self.clock.t += 1 / 15
        self.guide.update(fake.frame(fake.pose()))
        self.clock.t += 1 / 15
        s = self.guide.update(fake.frame(fake.pose(x=2.0)))
        self.assertIsNone(s.desired_bearing)

    def test_search_hints_then_gives_up(self):
        self.finder.obj = None
        self.guide.start("apple")
        steps = run(self.guide, self.clock, lambda: fake.frame(fake.pose()), 32)
        self.assertEqual(said(steps)[:2], ["I can't see the apple yet. Turn slowly to scan."] * 2)
        self.assertEqual(said(steps)[-1], "I couldn't find the apple.")
        self.assertEqual(steps[-1].state, IDLE)

    def test_model_failures_are_retried(self):
        self.finder.fail = True
        self.guide.start("apple")
        steps = run(self.guide, self.clock, lambda: fake.frame(fake.pose(), APPLE), 4)
        self.assertTrue(all(s.state == SEARCHING for s in steps))
        self.assertGreaterEqual(self.finder.calls, 2)
        self.finder.fail = False
        steps = run(self.guide, self.clock, lambda: fake.frame(fake.pose(), APPLE), 3, until=lambda s: s.state == CONFIRMING)
        self.assertEqual(steps[-1].state, CONFIRMING)


class WithDetector(unittest.TestCase):
    def test_yolo_box_used_at_once(self):
        clock = Clock()
        finder = fake.FakeFinder(None)  # the model never sees it
        guide = ObjectGuide(finder, clock)
        guide.start("red apple")
        p = fake.pose()
        f = fake.frame(p, APPLE)
        box = fake.FakeFinder(APPLE)(f.jpeg, "apple").box
        det = [fake.FakeAnswer(True, "", box)]
        det[0].label, det[0].conf = "apple", 0.9
        other = fake.FakeAnswer(True, "", [0, 0, 10, 10])
        other.label, other.conf = "chair", 0.95
        clock.t += 0.1
        s = guide.update(f, [other] + det)
        self.assertEqual(s.state, CONFIRMING)
        self.assertEqual(s.speech, "Red apple, 2.5 metres, slightly left. Say yes to go.")


class Commands(unittest.TestCase):
    def test_table(self):
        cases = {
            "guide me to the apple": ("object", "apple"),
            "Guide me to the apple.": ("object", "apple"),
            "take me to the door": ("object", "door"),
            "take me to Safeway": ("place", "Safeway"),
            "take me to safeway please": ("place", "safeway"),
            "Take me to the Safeway on Bowers": ("place", "Safeway on Bowers"),
            "take me to the train station": ("place", "train station"),
            "bring me to my keys": ("object", "keys"),
            "take me to the red cup": ("object", "red cup"),
            "where is the exit": ("object", "exit"),
            "find a chair": ("object", "chair"),
            "what's in front of me": ("describe", None),
            "describe the scene": ("describe", None),
            "read the sign": ("read", None),
            "what does it say": ("read", None),
            "yes": ("yes", None),
            "Yeah.": ("yes", None),
            "no": ("no", None),
            "stop": ("cancel", None),
            "never mind": ("cancel", None),
            "banana bread recipe": ("unknown", None),
            "": ("unknown", None),
        }
        for text, (kind, target) in cases.items():
            c = parse(text)
            self.assertEqual((c.kind, c.target), (kind, target), text)


ROUTE = {
    "dest": "Safeway",
    "distance_m": 222,
    "eta_min": 3,
    "polyline": [[37.0, -122.0], [37.001, -122.0], [37.002, -122.0]],  # 222 m due north
    "steps": [{"lat": 37.001, "lon": -122.0, "text": "Continue onto Bowers Ave"}],
}


class Route(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.r = RouteFollower(ROUTE, self.clock)

    def test_on_course(self):
        s = self.r.update(37.0, -122.0, 5.0, 0.0)
        self.assertAlmostEqual(s.desired_bearing, 0, delta=0.5)
        s = self.r.update(37.0, -122.0, 5.0, 20.0)  # facing a bit right of the route: steer left
        self.assertAlmostEqual(s.desired_bearing, -20, delta=0.5)

    def test_wrong_way_turn_on_the_spot(self):
        s = self.r.update(37.0, -122.0, 5.0, 90.0)
        self.assertTrue(s.hold_center)
        self.assertIsNone(s.desired_bearing)
        self.assertEqual(s.speech, "Turn left.")
        self.clock.t += 1
        self.assertIsNone(self.r.update(37.0, -122.0, 5.0, 90.0).speech)  # not every second

    def test_speaks_step_once(self):
        self.assertEqual(self.r.update(37.00095, -122.0, 5.0, 0.0).speech, "Continue onto Bowers Ave")
        self.assertIsNone(self.r.update(37.00096, -122.0, 5.0, 0.0).speech)

    def test_off_route_reroutes_after_5_s(self):
        off = -122.0 + 0.0004  # about 35 m east
        self.assertIsNone(self.r.update(37.0005, off, 5.0, 0.0).lookup)
        self.clock.t += 5
        s = self.r.update(37.0005, off, 5.0, 0.0)
        self.assertEqual((s.lookup, s.speech), ("Safeway", "Rerouting."))
        self.assertGreater(s.off_route_m, 30)

    def test_poor_gps_widens_off_route_limit(self):
        off = -122.0 + 0.0002  # about 18 m east, inside 2 x 12 m
        self.r.update(37.0005, off, 12.0, 0.0)
        self.clock.t += 6
        self.assertIsNone(self.r.update(37.0005, off, 12.0, 0.0).lookup)

    def test_bad_gps_pauses(self):
        s = self.r.update(37.0, -122.0, 30.0, 0.0)
        self.assertIsNone(s.desired_bearing)
        self.assertEqual(s.speech, "GPS is weak. Route guidance paused.")

    def test_arrives(self):
        s = self.r.update(37.0019, -122.0, 5.0, 0.0)
        self.assertTrue(s.arrived)
        self.assertEqual(s.speech, "You have arrived at Safeway.")


class FakeVLM:
    def __init__(self):
        self.find = fake.FakeFinder(APPLE)

    def describe(self, jpeg):
        return fake.FakeAnswer(True, "A table with an apple on it.")

    def read(self, jpeg):
        return fake.FakeAnswer(True, "EXIT\nRoom 204")


class WholeNavigator(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.nav = Navigator(FakeVLM(), self.clock)

    def test_apple(self):
        self.nav.on_voice("guide me to the apple")
        steps = run(self.nav, self.clock, lambda: fake.frame(fake.pose(), APPLE), 3, until=lambda s: s.state == CONFIRMING)
        self.assertEqual(said(steps), ["Looking for the apple.", "Apple, 2.5 metres, slightly left. Say yes to go."])
        self.nav.on_voice("yes")
        steps = run(self.nav, self.clock, lambda: fake.frame(fake.pose(), APPLE), 0.2)
        self.assertEqual(said(steps), ["Going to the apple."])
        self.assertLess(steps[-1].desired_bearing, 0)
        self.nav.on_voice("stop")
        s = run(self.nav, self.clock, lambda: fake.frame(fake.pose()), 0.1)[-1]
        self.assertEqual((s.mode, s.desired_bearing, s.speech), ("idle", None, "Cancelled."))

    def test_describe_and_read(self):
        self.nav.on_voice("what's in front of me")
        steps = run(self.nav, self.clock, lambda: fake.frame(fake.pose()), 1, until=lambda s: s.speech)
        self.assertEqual(steps[-1].speech, "A table with an apple on it.")
        self.nav.on_voice("read the sign")
        steps = run(self.nav, self.clock, lambda: fake.frame(fake.pose()), 1, until=lambda s: s.speech)
        self.assertEqual(steps[-1].speech, "EXIT. Room 204")

    def test_place(self):
        self.nav.on_voice("take me to Safeway")
        s = run(self.nav, self.clock, lambda: fake.frame(fake.pose()), 0.1)[0]
        self.assertEqual((s.lookup, s.speech), ("Safeway", "Looking up Safeway."))
        self.nav.on_route(ROUTE)
        s = run(self.nav, self.clock, lambda: fake.frame(fake.pose()), 0.1)[0]
        self.assertEqual(s.speech, "Safeway, 220 metres, about 3 minutes. Say yes to go.")
        self.nav.on_voice("yes")
        gps = dict(lat=37.0, lon=-122.0, gps_acc_m=5.0, heading_deg=10.0)
        steps = run(self.nav, self.clock, lambda: fake.frame(fake.pose(), **gps), 1.2)
        self.assertIn("Going to Safeway.", said(steps))
        self.assertEqual(steps[-1].state, "FOLLOWING")
        self.assertAlmostEqual(steps[-1].desired_bearing, -10, delta=0.5)

    def test_unknown(self):
        self.nav.on_voice("banana bread recipe")
        s = run(self.nav, self.clock, lambda: fake.frame(fake.pose()), 0.1)[0]
        self.assertEqual(s.speech, "Sorry, I didn't catch that.")


if __name__ == "__main__":
    unittest.main()


class ThinkingVLM(FakeVLM):
    """FakeVLM plus the model's voice understanding: interpret() and ask()."""

    MEANINGS = {
        "could you bring me over toward the red cup": ("object", "red cup"),
        "is anybody sitting at that table": ("question", "anybody sitting"),  # the real model shortens it
        "uh banana pancakes": ("unknown", ""),
    }

    def __init__(self, ok=True):
        super().__init__()
        self.ok, self.interpreted = ok, []

    def interpret(self, text):
        self.interpreted.append(text)
        if not self.ok:
            return fake.FakeAnswer(False, "I couldn't tell")
        a = fake.FakeAnswer(True, self.MEANINGS.get(text, ("unknown", ""))[1])
        a.label, a.seconds = self.MEANINGS.get(text, ("unknown", ""))[0], 0.3
        return a

    def ask(self, jpeg, question):
        self.asked = question
        return fake.FakeAnswer(True, "Two people are sitting at the table.")


class ModelVoice(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.vlm = ThinkingVLM()
        self.nav = Navigator(self.vlm, self.clock)

    def say_and_listen(self, text, seconds=1.0, frame=None):
        self.nav.on_voice(text)
        return said(run(self.nav, self.clock, frame or (lambda: fake.frame(fake.pose())), seconds))

    def test_rules_still_go_first(self):
        self.assertEqual(self.say_and_listen("guide me to the apple", 0.1), ["Looking for the apple."])
        self.assertEqual(self.vlm.interpreted, [])

    def test_status_is_a_rule_and_answered_from_the_navigator(self):
        self.assertEqual(parse("Am I going the right way?").kind, "status")
        self.assertEqual(parse("how far is it").kind, "status")
        self.assertEqual(parse("are we there yet").kind, "status")
        self.assertEqual(parse("how far away is the wall").kind, "unknown")  # a question for the model, not the trip
        self.assertEqual(self.say_and_listen("Am I going the right way?", 0.1),
                         ["You're not being guided right now. Say guide me to, and a thing or a place."])
        self.assertEqual(self.vlm.interpreted, [])

    def test_status_while_guiding(self):
        self.nav.on_voice("guide me to the apple")
        run(self.nav, self.clock, lambda: fake.frame(fake.pose(), APPLE), 3, until=lambda s: s.state == CONFIRMING)
        self.nav.on_voice("yes")
        run(self.nav, self.clock, lambda: fake.frame(fake.pose(), APPLE), 0.3)
        out = self.say_and_listen("how far is it", 0.2, lambda: fake.frame(fake.pose(), APPLE))
        self.assertEqual(out, ["Yes. The apple is 2.5 metres, slightly left."])

    def test_model_understands_an_odd_phrasing(self):
        self.assertEqual(self.say_and_listen("could you bring me over toward the red cup", 0.5)[0], "Looking for the red cup.")
        self.assertEqual(self.nav.mode, "object")

    def test_question_is_answered_from_the_picture(self):
        self.assertEqual(self.say_and_listen("is anybody sitting at that table"), ["Two people are sitting at the table."])
        self.assertEqual(self.vlm.asked, "is anybody sitting at that table")

    def test_model_unknown_or_down(self):
        self.assertEqual(self.say_and_listen("uh banana pancakes", 0.5), ["Sorry, I didn't catch that."])
        nav = Navigator(ThinkingVLM(ok=False), self.clock)
        nav.on_voice("could you bring me over toward the red cup")
        self.assertEqual(said(run(nav, self.clock, lambda: fake.frame(fake.pose()), 0.5)), ["Sorry, I didn't catch that."])

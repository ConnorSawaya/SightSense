"""The dashboard's motor speed slider. ../../venv-yolo/bin/python -m unittest ingest.test_speed (from gx10/)."""

import asyncio
import json
import unittest
from unittest.mock import patch

from . import server as srv


class FakePipe:
    last_frame = -1e9
    status = {}
    speed_cap = None


class FakePi:
    def __init__(self):
        self.got = []

    async def send(self, text):
        self.got.append(json.loads(text))


def run(s, seconds):
    async def go():
        task = asyncio.create_task(s.speed_loop())
        await asyncio.sleep(seconds)
        task.cancel()
    asyncio.run(go())


class Speed(unittest.TestCase):
    def setUp(self):
        self.s = srv.Server(FakePipe())
        self.pi = FakePi()
        self.s.pis.add(self.pi)

    def test_levels_are_clamped_and_rounded(self):
        self.assertTrue(self.s.set_speed(0.62))
        self.assertEqual(self.s.speed, 0.6)
        self.s.set_speed(4)
        self.assertEqual(self.s.speed, 1.0)
        self.s.set_speed(-1)
        self.assertEqual(self.s.speed, 0.0)
        self.assertFalse(self.s.set_speed("fast"))
        self.assertFalse(self.s.set_speed(float("nan")))
        self.assertEqual(self.s.speed, 0.0)

    def test_nothing_is_sent_until_the_slider_is_used(self):
        run(self.s, 0.6)
        self.assertEqual(self.pi.got, [])

    def test_sent_at_once_and_again_every_two_seconds(self):
        self.s.set_speed(0.5)
        with patch.object(srv, "SPEED_RESEND_S", 0.4):
            run(self.s, 1.1)
        self.assertGreaterEqual(len(self.pi.got), 2)
        self.assertEqual({m["speed"] for m in self.pi.got}, {0.5})
        self.assertTrue(all(set(m) == {"speed"} for m in self.pi.got))  # never a command or raw power

    def test_a_plan_can_only_slow_it(self):
        self.assertIsNone(self.s.effective_speed())  # neither set: the Pi keeps its own duty
        self.s.pipe.speed_cap = 0.5  # a plan step "slow"
        self.assertEqual(self.s.effective_speed(), 0.5)
        self.s.set_speed(0.4)
        self.assertEqual(self.s.effective_speed(), 0.4)  # the dashboard is lower: it wins
        self.s.set_speed(0.9)
        self.assertEqual(self.s.effective_speed(), 0.5)
        self.s.pipe.speed_cap = None
        self.assertEqual(self.s.effective_speed(), 0.9)

    def test_status_shows_it(self):
        from unittest.mock import MagicMock

        pipe = MagicMock(last_frame=-1e9, said=(None, -1e9), log=[], status={}, speed_cap=None)
        s = srv.Server(pipe)
        s.set_speed(0.35)
        self.assertEqual(s.status()["speed"], 0.35)


class Adapter(unittest.TestCase):
    def test_the_live_model_adapter_has_everything_the_navigator_calls(self):
        # the navigator calls these on whatever it is given; the live service gives it UprightVLM
        for name in ("find", "describe", "read", "ask", "objects", "plan", "interpret"):
            self.assertTrue(callable(getattr(srv.UprightVLM(), name, None)), name)


if __name__ == "__main__":
    unittest.main()

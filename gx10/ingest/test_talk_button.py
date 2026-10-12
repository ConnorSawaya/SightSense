"""The cane's talk button, passed on to the phone. ../../venv-yolo/bin/python -m unittest ingest.test_talk_button (from gx10/)."""

import asyncio
import json
import unittest
from collections import deque

from . import server as srv


class FakePipe:
    def __init__(self):
        self.last_frame = -1e9
        self.status = {}
        self.log = deque()  # the dashboard's conversation


class FakePhone:
    def __init__(self):
        self.got = []

    async def send(self, text):
        self.got.append(json.loads(text))


class FakePi:
    """A Pi connection that sends these messages, with pauses, then closes."""

    remote_address = ("192.0.2.2", 5000)

    def __init__(self, *steps):
        self.steps = steps  # each a message to send, or a number of seconds to wait

    def __aiter__(self):
        return self._messages()

    async def _messages(self):
        for step in self.steps:
            if isinstance(step, (int, float)):
                await asyncio.sleep(step)
            else:
                yield step if isinstance(step, str) else json.dumps(step)


DOWN, UP = {"button": "down"}, {"button": "up"}


class TalkButton(unittest.TestCase):
    def setUp(self):
        self.s = srv.Server(FakePipe())
        self.phone = self.s.phone_ws = FakePhone()

    def from_pi(self, *steps):
        asyncio.run(self.s.pi(FakePi(*steps)))

    def test_a_click_starts_the_phone_listening_and_leaves_it_to_stop_itself(self):
        self.from_pi(DOWN, 0.05, UP)
        self.assertEqual(self.phone.got, [{"listen": True}])

    def test_a_hold_stops_the_phone_when_the_button_is_let_go(self):
        self.from_pi(DOWN, srv.TALK_HOLD_S + 0.1, UP)
        self.assertEqual(self.phone.got, [{"listen": True}, {"listen": False}])

    def test_two_clicks(self):
        self.from_pi(DOWN, 0.02, UP, 0.02, DOWN, 0.02, UP)
        self.assertEqual(self.phone.got, [{"listen": True}, {"listen": True}])

    def test_the_dashboard_shows_each_press_with_or_without_a_phone(self):
        self.from_pi(DOWN, 0.02, UP)
        self.assertEqual([line[2] for line in self.s.pipe.log], ["(talk button down: phone told to listen)"])
        self.s.phone_ws = None
        self.from_pi(DOWN, 0.02, UP)
        self.assertEqual(self.s.pipe.log[-1][2], "(talk button down: no phone connected)")

    def test_an_up_with_no_down_is_ignored(self):
        self.from_pi(UP)
        self.assertEqual(self.phone.got, [])

    def test_health_reports_still_arrive_and_other_messages_are_ignored(self):
        self.from_pi({"health": {"cpu_c": 44.0}}, "not json", {"button": "sideways"}, ["button"], DOWN)
        self.assertEqual(self.s.pi_health[0], {"cpu_c": 44.0})
        self.assertEqual(self.phone.got, [{"listen": True}])

    def test_no_phone_connected(self):
        self.s.phone_ws = None
        self.from_pi(DOWN, 0.02, UP)  # must not raise
        self.assertEqual(self.phone.got, [])

    def test_a_pi_that_drops_while_the_button_is_held_does_not_leave_it_held(self):
        self.from_pi(DOWN)
        self.assertIsNone(self.s.talk_down)
        self.assertNotIn(None, self.s.pis)
        self.assertEqual(len(self.s.pis), 0)


if __name__ == "__main__":
    unittest.main()

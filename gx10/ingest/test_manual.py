"""Manual steering from the dashboard. ../../venv-yolo/bin/python -m unittest ingest.test_manual (from gx10/)."""

import asyncio
import json
import time
import unittest

from . import server as srv


class FakePipe:
    def __init__(self):
        self.last_frame = -1e9
        self.status = {}


class FakePi:
    def __init__(self):
        self.got = []

    async def send(self, text):
        self.got.append(json.loads(text))


def run_loop(s, seconds):
    async def go():
        task = asyncio.create_task(s.manual_loop())
        await asyncio.sleep(seconds)
        task.cancel()
    asyncio.run(go())


class Manual(unittest.TestCase):
    def setUp(self):
        self.s = srv.Server(FakePipe())
        self.pi = FakePi()
        self.s.pis.add(self.pi)

    def test_only_agreed_commands(self):
        self.assertFalse(self.s.manual_command("FASTER"))
        for position in ("CENTER", "FREE"):  # positions mean nothing to a free-spinning motor
            self.assertFalse(self.s.manual_command(position))
        self.assertIsNone(self.s.manual)
        self.assertTrue(self.s.manual_command("left"))
        self.assertEqual(self.s.manual[0], "LEFT")
        self.assertTrue(self.s.manual_command("AUTO"))
        self.assertIsNone(self.s.manual)

    def test_sends_the_command_with_a_short_ttl(self):
        self.s.manual_command("RIGHT")
        run_loop(self.s, 0.35)
        self.assertGreaterEqual(len(self.pi.got), 2)
        self.assertEqual({m["cmd"] for m in self.pi.got}, {"RIGHT"})
        self.assertTrue(all(m["ttl_ms"] == srv.TTL_MS for m in self.pi.got))

    def test_spin_is_sent_whatever_the_free_space(self):
        self.s.pipe.last_frame = time.monotonic() + 10  # frames are arriving
        self.s.pipe.status = {"cmd": "STOP"}  # and the obstacle check says STOP
        self.s.manual_command("LEFT")
        run_loop(self.s, 0.25)
        self.assertEqual({m["cmd"] for m in self.pi.got}, {"LEFT"})
        self.assertTrue(self.s.manual_sent["obstacle_ahead"])  # shown on the dashboard only

    def test_old_depth_is_not_shown_as_an_obstacle(self):
        self.s.pipe.status = {"cmd": "STOP"}  # from a phone that left long ago
        self.s.manual_command("RIGHT")
        run_loop(self.s, 0.25)
        self.assertEqual({m["cmd"] for m in self.pi.got}, {"RIGHT"})
        self.assertFalse(self.s.manual_sent["obstacle_ahead"])

    def test_back_to_automatic_when_the_dashboard_goes_quiet(self):
        old = srv.MANUAL_HOLD_S
        srv.MANUAL_HOLD_S = 0.2
        try:
            self.s.manual_command("LEFT")
            run_loop(self.s, 0.5)
        finally:
            srv.MANUAL_HOLD_S = old
        self.assertIsNone(self.s.manual)
        self.assertLess(len(self.pi.got), 4)

    def test_nothing_sent_when_off(self):
        run_loop(self.s, 0.25)
        self.assertEqual(self.pi.got, [])



class PiLink:
    """A Pi that sends the given messages, then hangs up."""
    remote_address = ("192.0.2.20", 40000)

    def __init__(self, messages):
        self.messages = messages

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        for m in self.messages:
            yield m


class PiHealth(unittest.TestCase):
    def test_health_reaches_the_status(self):
        s = srv.Server(FakePipe())
        report = {"cpu_c": 44.4, "in_v": 5.28, "undervolt_now": False, "mode": "wheel-drive"}
        asyncio.run(s.pi(PiLink(["not json", json.dumps({"other": 1}), json.dumps({"health": report})])))
        h = s._pi_health(time.monotonic())
        self.assertEqual((h["cpu_c"], h["in_v"], h["addr"]), (44.4, 5.28, "192.0.2.20"))
        self.assertEqual(s.pis, set())  # hung up: no longer sent commands

    def test_old_health_is_not_shown(self):
        s = srv.Server(FakePipe())
        asyncio.run(s.pi(PiLink([json.dumps({"health": {"cpu_c": 50}})])))
        self.assertIsNone(s._pi_health(time.monotonic() + srv.PI_HEALTH_FRESH_S + 1))


if __name__ == "__main__":
    unittest.main()

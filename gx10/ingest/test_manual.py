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

    def test_depth_stop_overrides_a_turn(self):
        self.s.pipe.last_frame = time.monotonic() + 10  # frames are arriving
        self.s.pipe.status = {"cmd": "STOP"}
        self.s.manual_command("LEFT")
        run_loop(self.s, 0.25)
        self.assertEqual({m["cmd"] for m in self.pi.got}, {"STOP"})
        self.assertTrue(self.s.manual_sent["depth_stop"])

    def test_old_depth_does_not_override_on_the_bench(self):
        self.s.pipe.status = {"cmd": "STOP"}  # from a phone that left long ago
        self.s.manual_command("LEFT")
        run_loop(self.s, 0.25)
        self.assertEqual({m["cmd"] for m in self.pi.got}, {"LEFT"})

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


if __name__ == "__main__":
    unittest.main()

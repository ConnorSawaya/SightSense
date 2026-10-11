"""python3 -m unittest test_health -v   (from this folder; any computer)"""

import asyncio
import json
import threading
import unittest
from unittest import mock

import cane
import health


class Readings(unittest.TestCase):
    def test_throttle_bits(self):
        with mock.patch.object(health, "_vcgencmd", return_value="throttled=0x50005"):
            h = health.read()
        self.assertTrue(h["undervolt_now"])
        self.assertTrue(h["undervolt_since_boot"])
        self.assertTrue(h["throttled_now"])
        self.assertTrue(h["throttled_since_boot"])

    def test_healthy_supply(self):
        out = {"get_throttled": "throttled=0x0", "pmic_read_adc": "EXT5V_V volt(24)=5.27960000V"}
        with mock.patch.object(health, "_vcgencmd", side_effect=lambda *a, **k: out[a[0]]):
            h = health.read({"mode": "wheel-drive", "duty": 0.25})
        self.assertEqual(h["in_v"], 5.28)
        self.assertFalse(h["undervolt_now"])
        self.assertEqual((h["mode"], h["duty"]), ("wheel-drive", 0.25))

    def test_missing_tools_leave_readings_out(self):
        with mock.patch.object(health, "_vcgencmd", return_value=""):
            h = health.read()
        self.assertNotIn("in_v", h)
        self.assertNotIn("undervolt_now", h)
        self.assertIn("t", h)
        self.assertTrue(all(v is not None for v in h.values()))


class FakeLink:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    async def send(self, text):
        if self.fail:
            raise ConnectionError("gone")
        self.sent.append(json.loads(text))


class Sending(unittest.TestCase):
    def run_for(self, link, seconds):
        async def go():
            task = asyncio.create_task(cane.send_health(link, threading.Event(), {"mode": "wheel-drive"}))
            await asyncio.sleep(seconds)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        with mock.patch.object(health, "HEALTH_S", 0.05):
            asyncio.run(go())

    def test_reports_repeat(self):
        link = FakeLink()
        self.run_for(link, 0.3)
        self.assertGreaterEqual(len(link.sent), 3)
        self.assertEqual(link.sent[0]["health"]["mode"], "wheel-drive")

    def test_a_failed_send_stops_quietly(self):
        link = FakeLink(fail=True)
        self.run_for(link, 0.2)  # must return without raising
        self.assertEqual(link.sent, [])


if __name__ == "__main__":
    unittest.main()

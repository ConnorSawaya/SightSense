"""Bad text messages from the phone. ../../venv-yolo/bin/python -m unittest ingest.test_bad_text (from gx10/).

A message the service cannot use must not end the phone's link, and when the link
does end the service must stop showing that phone as connected.
"""

import asyncio
import json
import unittest
from unittest.mock import patch

from . import server as srv


class FakePhone:
    """A phone connection that sends these text messages, then closes."""

    remote_address = ("10.0.0.3", 5000)

    def __init__(self, *messages):
        self.messages = messages

    def __aiter__(self):
        return self._messages()

    async def _messages(self):
        for m in self.messages:
            yield m if isinstance(m, str) else json.dumps(m)


class BrokenPhone(FakePhone):
    async def _messages(self):
        yield json.dumps({"text": "stop"})
        raise RuntimeError("the link broke")


class BadText(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        with patch.object(srv.vlm, "warm", return_value="stubbed"):
            self.s = srv.Server(srv.Pipeline(False))

    def tearDown(self):
        self.s.worker.shutdown(wait=True)
        self.s.writer.shutdown(wait=True)

    async def test_odd_messages_do_not_end_the_link(self):
        odd = ["5", "null", "true", '"text"', "[1, 2]", "{",
               {"text": "take me to Safeway"},  # a lookup is waiting, so the routes below are read, not ignored
               {"polyline": [[1, 2], [3, 4]], "distance_m": "950"},
               {"polyline": [[1, 2], [3, 4]], "dest": 7}]
        await self.s.phone(FakePhone(*odd, {"text": "is the path clear"}))
        heard = [entry[2] for entry in self.s.pipe.log if entry[1] == "you"]
        self.assertEqual(heard, ["take me to Safeway", "is the path clear"])  # the message after the odd ones still arrived
        self.assertIsNone(self.s.phone_ws)

    async def test_the_phone_is_forgotten_when_its_link_fails(self):
        with self.assertRaises(RuntimeError):
            await self.s.phone(BrokenPhone())
        self.assertIsNone(self.s.phone_ws)
        self.assertIsNone(self.s.status()["phone"])


class StayingPhone(FakePhone):
    """A phone that stays connected until told to leave."""

    def __init__(self):
        self.leave = asyncio.Event()

    async def _messages(self):
        await self.leave.wait()
        for m in ():
            yield m


class TwoPhones(unittest.IsolatedAsyncioTestCase):
    async def test_a_second_client_leaving_does_not_forget_the_first(self):
        with patch.object(srv.vlm, "warm", return_value="stubbed"):
            s = srv.Server(srv.Pipeline(False))
        try:
            cane = StayingPhone()
            link = asyncio.create_task(s.phone(cane))
            await asyncio.sleep(0.01)
            await s.phone(FakePhone({"text": "stop"}))  # a test client connects, says one thing and leaves
            self.assertIs(s.phone_ws, cane)  # the talk button still has a phone to tell
            cane.leave.set()
            await link
            self.assertIsNone(s.phone_ws)
        finally:
            s.worker.shutdown(wait=True)
            s.writer.shutdown(wait=True)


class ManualRead(unittest.TestCase):
    def test_the_command_is_passed_in_not_read_again(self):
        with patch.object(srv.vlm, "warm", return_value="stubbed"):
            s = srv.Server(srv.Pipeline(False))
        try:
            s.manual = None  # the dashboard's thread cleared it after the loop's check
            self.assertEqual(s._manual_for_pi(0.0, "LEFT"), ("LEFT", False))
        finally:
            s.worker.shutdown(wait=True)
            s.writer.shutdown(wait=True)


class NoModel(unittest.TestCase):
    def test_the_service_starts_when_the_model_cannot_be_loaded(self):
        with patch.object(srv.vlm, "warm", side_effect=OSError("Ollama is not running")):
            pipe = srv.Pipeline(False)  # the obstacle check does not need the model
        self.assertTrue(hasattr(pipe, "smoother"))


if __name__ == "__main__":
    unittest.main()

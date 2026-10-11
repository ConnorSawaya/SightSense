"""One model request at a time. No model needed: python3 -m unittest vlm.test_busy (from gx10/).

The object guide runs find() every 1.5 to 2 seconds. A spoken question that arrives
while one is running must wait for it, not come back as "I couldn't tell".
"""

import threading
import time
import unittest
from unittest.mock import patch

from . import core


class Busy(unittest.TestCase):
    def setUp(self):
        core._lock.acquire()  # a find() is running
        self.held = True

    def tearDown(self):
        self.release()

    def release(self):
        if self.held:
            self.held = False
            core._lock.release()

    def test_a_question_waits_for_a_running_find(self):
        with patch.object(core, "_ask", return_value=core.Answer(True, "A door.")):
            threading.Timer(0.3, self.release).start()
            started = time.monotonic()
            a = core._one(b"picture", "a question")
        self.assertTrue(a.ok)
        self.assertGreaterEqual(time.monotonic() - started, 0.25)

    def test_it_gives_up_when_the_find_does_not_finish(self):
        with patch.object(core, "BUSY_WAIT_S", 0.1), patch.object(core, "_ask") as ask:
            a = core._one(b"picture", "a question")
        self.assertFalse(a.ok)
        self.assertIn("busy", a.error)
        ask.assert_not_called()

    def test_find_itself_never_waits(self):
        with patch.object(core, "jpeg_size", return_value=(640, 480)), patch.object(core, "_ask") as ask:
            started = time.monotonic()
            a = core.find(b"picture", "apple")
        self.assertLess(time.monotonic() - started, 0.1)
        self.assertIn("busy", a.error)
        ask.assert_not_called()


if __name__ == "__main__":
    unittest.main()

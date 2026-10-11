"""The first frames of a session. ../../venv-yolo/bin/python -m unittest ingest.test_first_frames (from gx10/).

The obstacle smoother begins every session, and every gap over 1 s, in STOP for two
frames. That STOP goes to the Pi, but it must not play the stop tone when the depth
shows nothing in the way; a wall in the way from the first frame must play it at once.
"""

import itertools
import json
import time
import unittest
from unittest.mock import patch

from . import server as srv
from .fake_phone import walk_frames


def first_messages(frames):
    with patch.object(srv.vlm, "warm", return_value="stubbed"):
        pipe = srv.Pipeline(False)
    out = []
    for raw in frames:
        messages, _pi = pipe.process(raw, time.monotonic())
        out += [m for m in map(json.loads, messages) if "state" in m]
    return out


class FirstFrames(unittest.TestCase):
    def test_open_floor_starts_stopped_but_without_the_stop_tone(self):
        frames = [raw for raw, _wall in itertools.islice(walk_frames(), 6)]  # the wall is 4 m away
        messages = first_messages(frames)
        self.assertEqual(messages[0]["state"], "STOP")
        self.assertEqual([m["earcon"] for m in messages if "earcon" in m], [])

    def test_a_wall_in_the_way_from_the_first_frame_sounds_at_once(self):
        close = [raw for raw, wall in walk_frames() if wall < 0.6][:3]
        messages = first_messages(close)
        self.assertEqual(messages[0].get("earcon"), "stop")


if __name__ == "__main__":
    unittest.main()

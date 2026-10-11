"""Asking the cane things by voice. ../../venv-yolo/bin/python -m unittest ingest.test_assistant (from gx10/).

The voice text comes from the phone's talk button or the one on the cane; here it is typed in.
The whole frame pipeline runs, with the vision model stubbed out.
"""

import itertools
import json
import time
import unittest
from unittest.mock import patch

from . import server as srv
from .fake_phone import walk_frames


class Assistant(unittest.TestCase):
    def setUp(self):
        with patch.object(srv.vlm, "warm", return_value="stubbed"):
            self.pipe = srv.Pipeline(False)
        self.frames = itertools.cycle([raw for raw, _wall in itertools.islice(walk_frames(), 20)])

    def ask(self, text, frames=8):
        """Say this, run a few frames, return what the phone was told to speak."""
        self.pipe.nav.on_voice(text)
        spoken = []
        for _ in range(frames):
            messages, _pi = self.pipe.process(next(self.frames), time.monotonic())
            spoken += [m["speech"] for m in map(json.loads, messages) if m.get("speech")]
            time.sleep(0.01)
        return spoken

    def test_what_can_you_do(self):
        answer = self.ask("what can you do")
        self.assertEqual(len(answer), 1)
        self.assertTrue(answer[0].startswith("I can tell you what is in front of you"))
        self.assertNotIn("safe", answer[0].lower())

    def test_say_that_again_repeats_the_last_sentence(self):
        self.assertEqual(self.ask("say that again"), ["I haven't said anything yet."])
        first = self.ask("help")
        self.assertEqual(self.ask("repeat that"), first)

    def test_sound_check_sends_each_tone_with_its_name_one_at_a_time(self):
        with patch.object(srv, "SOUND_CHECK_GAP_S", 0.02):
            self.pipe.nav.on_voice("sound check")
            got = []
            for _ in range(30):
                messages, _pi = self.pipe.process(next(self.frames), time.monotonic())
                got += [(m["earcon"], m["speech"]) for m in map(json.loads, messages) if m.get("earcon") and m.get("speech")]
                time.sleep(0.01)
        self.assertEqual([tone for tone, _ in got], [tone for tone, _ in srv.SOUND_CHECK])
        self.assertEqual(got[-1], ("stop", "Stop. Sound check done."))

    def test_a_question_about_the_picture_goes_to_the_model_and_its_answer_is_spoken(self):
        with patch.object(srv.vlm, "ask", return_value=srv.vlm.Answer(True, "A red chair.")) as model:
            answer = self.ask("what colour is the chair", frames=20)
        self.assertEqual(answer, ["A red chair."])
        self.assertEqual(model.call_args[0][1], "what colour is the chair")

    def test_is_the_path_clear_is_answered_from_depth_not_the_model(self):
        with patch.object(srv.vlm, "ask") as model, patch.object(srv.vlm, "describe") as describe:
            answer = self.ask("is the path clear")
        self.assertEqual(len(answer), 1)
        model.assert_not_called()
        describe.assert_not_called()


if __name__ == "__main__":
    unittest.main()

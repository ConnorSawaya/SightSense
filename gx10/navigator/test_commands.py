"""Voice rules on real sentences. python3 -m unittest navigator.test_commands (from gx10/). Standard library only."""

import unittest
from types import SimpleNamespace

from . import commands
from .navigator import chat_words
from .object_guide import _same_thing
from .voice_cases import ROUTES


class Routes(unittest.TestCase):
    def test_every_sentence(self):
        for text, kind, target in ROUTES:
            with self.subTest(text=text):
                c = commands.parse(text)
                self.assertEqual(c.kind, kind)
                if target is not None:
                    self.assertEqual((c.target or "").lower(), target.lower())

    def test_side_is_kept_apart_from_the_name(self):
        self.assertEqual(commands.parse("take me to the door on the left"), commands.Command("object", "door", "left"))
        self.assertEqual(commands.parse("Guide me to the computer near my right"),
                         commands.Command("object", "computer", "right"))
        self.assertEqual(commands.parse("guide me to the red cup on the table").side, None)

    def test_place_names_keep_their_words(self):
        self.assertEqual(commands.parse("take me to Safeway on Main Street"), commands.Command("place", "Safeway on Main Street"))

    def test_please_alone_is_not_yes(self):
        self.assertEqual(commands.parse("please").kind, "unknown")
        self.assertEqual(commands.parse("yes please").kind, "yes")


class Chat(unittest.TestCase):
    def test_replies(self):
        self.assertEqual(chat_words("thank you", None), "You're welcome.")
        self.assertTrue(chat_words("hello", None).startswith("Hello."))
        self.assertTrue(chat_words("good morning", None).startswith("Good morning."))
        self.assertEqual(chat_words("how are we doing", "Still looking for the door."),
                         "I'm working well. Still looking for the door.")


class Names(unittest.TestCase):
    def test_what_people_say_matches_the_detector(self):
        self.assertTrue(_same_thing("laptop", "computer"))
        self.assertTrue(_same_thing("dining table", "table"))
        self.assertTrue(_same_thing("couch", "sofa"))
        self.assertTrue(_same_thing("apple", "red apple"))
        self.assertFalse(_same_thing("chair", "computer"))


class Tidy(unittest.TestCase):
    def test_answers_do_not_talk_about_the_picture(self):
        from vlm.core import _sides, tidy

        self.assertEqual(tidy("There are two chairs visible in the image."), "There are two chairs.")
        self.assertEqual(tidy("A laptop screen is directly ahead of the camera."), "A laptop screen is in front of you.")
        self.assertEqual(tidy("laptops, couch, table"), "Laptops, couch, table.")
        self.assertEqual(_sides("On your left: couch. Ahead: table, box. On your right: nothing"),
                         "On your left: couch. Ahead: table, box.")


if __name__ == "__main__":
    unittest.main()

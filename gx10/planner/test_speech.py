"""python3 -m unittest planner.test_speech (from gx10/). Standard library only."""

import unittest

from .speech import ANSWER, GUIDE, INFO, SAFETY, SpeechPlan, speaking_time

FPS = 15


def run(plan, seconds, start=0.0, thinking=False, adds=()):
    """Frames for `seconds`; adds: (time, text, priority). Returns [(time, text)] sent."""
    adds, sent = sorted(adds), []
    for i in range(int(seconds * FPS)):
        now = start + i / FPS
        while adds and adds[0][0] <= now:
            _, text, p = adds.pop(0)
            plan.add(text, p, now)
        s = plan.next(now, thinking)
        if s:
            sent.append((round(now, 2), s))
    return sent


class Order(unittest.TestCase):
    def test_everything_at_once_comes_out_one_at_a_time_most_important_first(self):
        p = SpeechPlan()
        sent = run(p, 12, adds=[
            (0, "I can't see the door yet. Turn slowly to scan.", INFO),
            (0, "Bear left", GUIDE),
            (0, "A door is ahead, slightly to the right.", ANSWER),
            (0, "Obstacle ahead. Stop.", SAFETY),
        ])
        texts = [s for _, s in sent]
        self.assertEqual(texts[:2], ["Obstacle ahead. Stop.", "A door is ahead, slightly to the right."])
        for (t1, s1), (t2, _) in zip(sent, sent[1:]):  # never over the last sentence
            self.assertGreaterEqual(t2 - t1, speaking_time(s1))
        self.assertNotIn("Bear left", texts)  # waited past 2 s: old news, not said late

    def test_safety_cuts_into_a_direction_but_not_an_answer(self):
        p = SpeechPlan()
        sent = run(p, 1, adds=[(0, "Bear left", GUIDE), (0.3, "Obstacle ahead. Stop.", SAFETY)])
        self.assertEqual(sent, [(0.0, "Bear left"), (0.33, "Obstacle ahead. Stop.")])
        p = SpeechPlan()
        answer = "You are at a table with three people, a laptop and a box."
        sent = run(p, 6, adds=[(0, answer, ANSWER), (0.3, "Obstacle ahead. Stop.", SAFETY)])
        self.assertEqual([s for _, s in sent], [answer, "Obstacle ahead. Stop."])
        self.assertGreaterEqual(sent[1][0], speaking_time(answer))  # after the answer, not over it

    def test_the_same_stop_is_not_said_over_and_over(self):
        p = SpeechPlan()
        sent = run(p, 12, adds=[(t / 2, "Obstacle ahead. Stop.", SAFETY) for t in range(24)])  # STOP flickering
        self.assertEqual([t for t, _ in sent], [0.0, 10.0])

    def test_answers_wait_but_are_never_dropped(self):
        p = SpeechPlan()
        sent = run(p, 15, adds=[(0, "Hello. I'm ready.", ANSWER), (0, "It's 11:40 AM, Sunday, October 11.", ANSWER),
                                (0, "You're welcome.", ANSWER)])
        self.assertEqual(len(sent), 3)

    def test_hints_need_quiet_and_are_not_repeated(self):
        p = SpeechPlan()
        hint = "I can't see the door yet. Turn slowly to scan."
        sent = run(p, 14, adds=[(0, "Looking for the door.", ANSWER), (0.1, hint, INFO), (10, hint, INFO)])
        self.assertEqual([s for _, s in sent], ["Looking for the door.", hint])
        self.assertGreaterEqual(sent[1][0] - sent[0][0], 3.0)  # only after 3 s of quiet

    def test_quiet_while_the_user_talks(self):
        p = SpeechPlan()
        p.listening(0.0)
        sent = run(p, 3, adds=[(0.5, "Bear right", GUIDE), (1.0, "Obstacle ahead. Stop.", SAFETY)])
        self.assertEqual([s for _, s in sent], ["Obstacle ahead. Stop."])
        p.heard()
        sent = run(p, 2, start=3, adds=[(3, "Hello.", ANSWER)])
        self.assertEqual([s for _, s in sent], ["Hello."])
        self.assertGreaterEqual(sent[0][0], 1.0 + speaking_time("Obstacle ahead. Stop."))  # after the stop is finished

    def test_chatter_waits_while_the_model_answers(self):
        p = SpeechPlan()
        self.assertEqual(run(p, 1, thinking=True, adds=[(0, "Bear left", GUIDE)]), [])
        self.assertEqual(run(p, 1, start=1, thinking=True, adds=[(1, "It says: EXIT.", ANSWER)]), [(1.0, "It says: EXIT.")])

    def test_only_the_newest_direction(self):
        p = SpeechPlan()
        p.add("Obstacle ahead. Stop.", SAFETY, 0)
        p.next(0)
        p.add("Bear left", GUIDE, 0.5)
        p.add("Bear right", GUIDE, 1.0)
        self.assertEqual([s for _, s in run(p, 2, start=1.0)], ["Bear right"])


if __name__ == "__main__":
    unittest.main()

"""python3 -m unittest planner.test_obstacle_talk (from gx10/). Standard library only."""

import unittest
from types import SimpleNamespace as Det

from .obstacle_talk import ObstacleTalk, open_side, thing_ahead

OPEN = {h: 10.0 for h in (-30, -20, -10, 0, 10, 20, 30)}


def cl(**kw):
    c = dict(OPEN)
    c.update({int(k.replace("m", "-").replace("p", "")): v for k, v in kw.items()})
    return c


CHAIR = Det(label="chair", bearing=3.0, dist_m=1.0)
TABLE_LEFT = Det(label="dining table", bearing=-25.0, dist_m=1.2)


class Words(unittest.TestCase):
    def test_names_the_thing_straight_ahead(self):
        self.assertEqual(thing_ahead([TABLE_LEFT, CHAIR], 1.0), "chair")
        self.assertIsNone(thing_ahead([TABLE_LEFT], 1.0))  # off to the side: not the thing ahead
        self.assertIsNone(thing_ahead([Det(label="chair", bearing=0, dist_m=4.0)], 1.0))  # far behind the obstacle

    def test_which_side_is_open(self):
        self.assertEqual(open_side(cl(p0=0.9, p10=0.9, p20=0.9, p30=0.9)), "left")
        self.assertEqual(open_side(cl(p0=0.9, m10=0.9, m20=0.9, m30=0.9)), "right")
        self.assertIsNone(open_side({h: 0.7 for h in OPEN}))

    def test_stop_sentence(self):
        t = ObstacleTalk()
        self.assertEqual(t.stop_sentence(cl(p0=1.0, p10=1.0, p20=1.0, p30=1.0), [CHAIR]),
                         "Stop. Chair ahead, about 1 metre. Open to your left.")
        self.assertEqual(t.stop_sentence({h: 0.6 for h in OPEN}, []),
                         "Stop. Something ahead, less than a metre.")
        self.assertEqual(t.stop_sentence(cl(p0=None), []), "Stop. I can't see clearly ahead.")


class Walk(unittest.TestCase):
    def test_round_a_chair_and_past_it(self):
        t = ObstacleTalk()
        said = []
        for cmd, c in [("CENTER", OPEN), ("LEFT", cl(p0=1.2)), ("LEFT", cl(p0=1.1)), ("CENTER", cl(p0=1.4)), ("CENTER", OPEN)]:
            said += list(t.update(cmd, c, [CHAIR]).values())
        self.assertEqual(said, ["Chair ahead. Bear left around it.", "You're past it. Carry on."])

    def test_a_turn_for_the_route_is_not_an_obstacle(self):
        t = ObstacleTalk()
        self.assertEqual(t.update("RIGHT", OPEN, []), {})  # straight ahead is open: a turn to follow the route

    def test_warning_only_while_something_is_close(self):
        t = ObstacleTalk()
        self.assertIsNone(t.hazard("CENTER", OPEN, [CHAIR]))
        self.assertIsNone(t.hazard("STOP", cl(p0=4.0), []))  # the STOP a session starts in, wall far away
        self.assertEqual(t.hazard("STOP", cl(p0=1.0), [CHAIR]), "Careful: chair ahead, about 1 metre.")
        self.assertEqual(t.hazard("LEFT", cl(p0=1.2), []), "Careful: something ahead, about 1 metre.")


if __name__ == "__main__":
    unittest.main()

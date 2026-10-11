"""python3 -m unittest test_talk_button -v   (from this folder; any computer)

The last class checks the pin against gpiozero's mock pins, and is skipped
where gpiozero is not installed.
"""

import asyncio
import json
import threading
import unittest
from unittest import mock

import cane
import hardware
import talk_button
from talk_button import DEBOUNCE_S, Debounce


def events(readings, step=0.01):
    """Feed (pressed, how long) pairs through a Debounce in 10 ms steps; returns [(time, event)]."""
    presses, now, out = Debounce(), 0.0, []
    for raw, seconds in readings:
        for _ in range(round(seconds / step)):
            event = presses.update(raw, now)
            if event:
                out.append((round(now, 2), event))
            now += step
    return out


class Debouncing(unittest.TestCase):
    def test_a_press_and_release_are_reported_once_each(self):
        got = events([(False, 0.2), (True, 0.5), (False, 0.3)])
        self.assertEqual([e for _, e in got], ["down", "up"])
        self.assertAlmostEqual(got[0][0], 0.2 + DEBOUNCE_S, places=2)

    def test_a_spike_shorter_than_the_hold_is_ignored(self):
        self.assertEqual(events([(False, 0.2), (True, 0.02), (False, 0.3)]), [])

    def test_a_dropout_while_held_is_ignored(self):
        got = events([(True, 0.3), (False, 0.02), (True, 0.3), (False, 0.2)])
        self.assertEqual([e for _, e in got], ["down", "up"])

    def test_chatter_on_the_edges_gives_one_down_and_one_up(self):
        bounce = [(True, 0.01), (False, 0.01)] * 4
        got = events([(False, 0.1)] + bounce + [(True, 0.4)] + bounce + [(False, 0.3)])
        self.assertEqual([e for _, e in got], ["down", "up"])

    def test_two_presses(self):
        got = events([(True, 0.2), (False, 0.2), (True, 0.2), (False, 0.2)])
        self.assertEqual([e for _, e in got], ["down", "up", "down", "up"])


class FakeLink:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    async def send(self, text):
        if self.fail:
            raise ConnectionError("gone")
        self.sent.append(json.loads(text))


class FakeButton:
    def __init__(self):
        self.down = False

    def is_pressed(self):
        return self.down


class Sending(unittest.TestCase):
    def press(self, link, held_s):
        button = FakeButton()

        async def go():
            task = asyncio.create_task(cane.send_button(link, threading.Event(), button))
            await asyncio.sleep(0.05)
            button.down = True
            await asyncio.sleep(held_s)
            button.down = False
            await asyncio.sleep(0.15)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        with mock.patch.object(cane, "log", lambda text: None):
            asyncio.run(go())

    def test_down_then_up_go_to_the_gx10(self):
        link = FakeLink()
        self.press(link, 0.2)
        self.assertEqual(link.sent, [{"button": "down"}, {"button": "up"}])

    def test_nothing_is_sent_while_the_button_is_left_alone(self):
        link = FakeLink()
        self.press(link, 0.0)
        self.assertEqual(link.sent, [])

    def test_a_failed_send_stops_quietly(self):
        link = FakeLink(fail=True)
        self.press(link, 0.2)  # must return without raising
        self.assertEqual(link.sent, [])


try:
    from gpiozero import Device
    from gpiozero.pins.mock import MockFactory
except ImportError:
    Device = None


@unittest.skipUnless(Device, "gpiozero is not installed")
class Pin(unittest.TestCase):
    def setUp(self):
        Device.pin_factory = self.pins = MockFactory()
        self.button = talk_button.TalkButton()
        self.addCleanup(self.button.close)

    def test_reads_pressed_when_pulled_to_ground(self):
        pin = self.pins.pin(talk_button.PIN_TALK)
        self.assertFalse(self.button.is_pressed())  # nothing wired: the pull-up holds it high
        pin.drive_low()
        self.assertTrue(self.button.is_pressed())
        pin.drive_high()
        self.assertFalse(self.button.is_pressed())

    def test_its_pin_is_not_one_the_motor_or_the_switches_use(self):
        used = {hardware.PIN_RPWM, hardware.PIN_LPWM, hardware.PIN_R_EN, hardware.PIN_L_EN, *hardware.PIN_SWITCH.values()}
        self.assertNotIn(talk_button.PIN_TALK, used)


if __name__ == "__main__":
    unittest.main()

"""The talk button in the cane's handle: press it, then say a command.

A momentary push button between GPIO17 (header pin 11) and ground (header pin 9).
Wiring is in ../hardware/wiring.md. The Pi does not listen to or understand
anything. It tells the GX10 when the button goes down and up, and the GX10 tells
the phone to listen:

    {"button": "down"}      {"button": "up"}

Nothing here touches the motor.
"""

PIN_TALK = 17  # BCM number, from ../hardware/wiring.md
DEBOUNCE_S = 0.03  # a change must last this long to count: the wire runs the length of the cane, beside the motor's
POLL_S = 0.01


class Debounce:
    """Turns raw readings into "down" and "up", once each. No GPIO in here."""

    def __init__(self, hold_s=DEBOUNCE_S):
        self.hold_s = hold_s
        self.pressed = False  # the settled state
        self._since = None  # when the raw reading first differed from it

    def update(self, raw, now):
        """raw: True while the button reads pressed. Returns "down", "up" or None."""
        raw = bool(raw)
        if raw == self.pressed:
            self._since = None
            return None
        if self._since is None:
            self._since = now
        if now - self._since < self.hold_s:
            return None
        self.pressed, self._since = raw, None
        return "down" if raw else "up"


class TalkButton:
    """The real button, through gpiozero. The Pi's own pull-up holds the pin high;
    pressing the button pulls it to ground. With nothing wired it reads "not pressed"."""

    def __init__(self, pin=PIN_TALK):
        from gpiozero import Button

        self._button = Button(pin, pull_up=True)

    def is_pressed(self):
        return self._button.is_pressed

    def close(self):
        self._button.close()

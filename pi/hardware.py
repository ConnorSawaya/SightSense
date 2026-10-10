"""The motor and limit switches: the real ones, and a simulated wheel.

Both offer drive(direction, duty), off(), pressed() and close().
direction is -1 for left and +1 for right. Wiring is in ../hardware/wiring.md.
"""

import time

from steering import CENTER, LEFT, MAX_DUTY, RIGHT

# BCM numbers, from ../hardware/wiring.md
PIN_IN1 = 23
PIN_IN2 = 24
PIN_ENA = 18
PIN_SWITCH = {LEFT: 5, CENTER: 13, RIGHT: 6}
PWM_HZ = 1000


class GpioHardware:
    """L298N and three limit switches on a Raspberry Pi 5, through gpiozero."""

    def __init__(self, swap=False):
        from gpiozero import Button, DigitalOutputDevice, PWMOutputDevice

        self._swap = swap  # set if "left" turns the wheel right
        self._in1 = DigitalOutputDevice(PIN_IN1)
        self._in2 = DigitalOutputDevice(PIN_IN2)
        self._ena = PWMOutputDevice(PIN_ENA, frequency=PWM_HZ)
        self._switches = {
            name: Button(pin, pull_up=True) for name, pin in PIN_SWITCH.items()
        }

    def drive(self, direction, duty):
        in1 = (direction < 0) != self._swap
        self._ena.value = 0
        self._in1.value = in1
        self._in2.value = not in1
        self._ena.value = max(0.0, min(duty, MAX_DUTY))

    def off(self):
        self._ena.value = 0
        self._in1.off()
        self._in2.off()

    def pressed(self):
        return {name for name, switch in self._switches.items() if switch.is_pressed}

    def close(self):
        if self._ena.closed:
            return
        self.off()
        for device in (self._ena, self._in1, self._in2, *self._switches.values()):
            device.close()


class SimHardware:
    """A pretend wheel, for running without a Pi.

    x runs from -1 (left stop) through 0 (centre) to +1 (right stop).
    travel_s is the time from one position to the next at full allowed power.
    """

    SPOT = {LEFT: -1.0, CENTER: 0.0, RIGHT: 1.0}

    def __init__(self, x=0.4, travel_s=0.25, window=0.1, clock=time.monotonic):
        self.x = x
        self.travel_s = travel_s
        self.window = window  # how far from a position its switch stays pressed
        self.stuck = False  # motor powered but not turning
        self.dead = set()  # switches that never close
        self.duty = 0.0
        self._direction = 0
        self._clock = clock
        self._then = clock()

    def drive(self, direction, duty):
        self._move()
        self._direction = direction
        self.duty = duty

    def off(self):
        self._move()
        self._direction = 0
        self.duty = 0.0

    def pressed(self):
        self._move()
        return {
            name
            for name, spot in self.SPOT.items()
            if abs(self.x - spot) <= self.window and name not in self.dead
        }

    def close(self):
        self.off()

    def _move(self):
        now = self._clock()
        if not self.stuck:
            speed = self._direction * (self.duty / MAX_DUTY) / self.travel_s
            self.x = max(-1.0, min(1.0, self.x + speed * (now - self._then)))
        self._then = now

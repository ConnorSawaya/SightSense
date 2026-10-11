"""The motor and limit switches: the real ones, a simulated wheel, and the
real motor with worked-out positions for a cane with no switches fitted.

All offer drive(direction, duty), off(), pressed() and close().
direction is -1 for left and +1 for right. Wiring is in ../hardware/wiring.md.
"""

import time

from steering import CENTER, LEFT, MAX_DUTY, RIGHT

# BCM numbers, from ../hardware/wiring.md
PIN_RPWM = 23
PIN_LPWM = 24
PIN_R_EN = 18
PIN_L_EN = 25
PIN_SWITCH = {LEFT: 5, CENTER: 13, RIGHT: 6}
PWM_HZ = 1000


class GpioHardware:
    """IBT-2 (BTS7960) driver and three limit switches on a Raspberry Pi 5, through gpiozero.

    Both enable pins high lets the driver run. Power goes on RPWM to turn one
    way and on LPWM to turn the other. Enables low is driver off.
    """

    def __init__(self, swap=False):
        from gpiozero import Button, DigitalOutputDevice, PWMOutputDevice

        self._swap = swap  # set if "left" turns the wheel right
        self._enables = (DigitalOutputDevice(PIN_R_EN), DigitalOutputDevice(PIN_L_EN))
        self._rpwm = PWMOutputDevice(PIN_RPWM, frequency=PWM_HZ)
        self._lpwm = PWMOutputDevice(PIN_LPWM, frequency=PWM_HZ)
        self._switches = {
            name: Button(pin, pull_up=True) for name, pin in PIN_SWITCH.items()
        }

    def drive(self, direction, duty):
        rpwm = (direction < 0) != self._swap
        powered, idle = (self._rpwm, self._lpwm) if rpwm else (self._lpwm, self._rpwm)
        idle.value = 0
        for enable in self._enables:
            enable.on()
        powered.value = max(0.0, min(duty, MAX_DUTY))

    def off(self):
        self._rpwm.value = 0
        self._lpwm.value = 0
        for enable in self._enables:
            enable.off()

    def pressed(self):
        return {name for name, switch in self._switches.items() if switch.is_pressed}

    def close(self):
        if self._rpwm.closed:
            return
        self.off()
        for device in (self._rpwm, self._lpwm, *self._enables, *self._switches.values()):
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


class OpenLoopHardware(SimHardware):
    """The real motor on a cane with no limit switches fitted.

    Where the wheel is gets worked out from how long the motor has run, using
    the same sums as the simulated wheel. Put the wheel at centre by hand
    before starting. travel_s is how long the motor takes from centre to one
    side at the capped power. Nothing checks where the wheel really is, so it
    drifts: re-centre it by hand now and then.
    """

    def __init__(self, motor, travel_s=0.25, clock=time.monotonic):
        super().__init__(x=0.0, travel_s=travel_s, clock=clock)
        self._motor = motor

    def drive(self, direction, duty):
        super().drive(direction, duty)
        self._motor.drive(direction, duty)

    def off(self):
        super().off()
        self._motor.off()

    def close(self):
        super().close()
        self._motor.close()

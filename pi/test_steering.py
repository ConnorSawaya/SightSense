"""Tests for the steering logic, on the simulated wheel with a fake clock.

    python3 -m unittest -v        (from this folder)

Nothing here touches GPIO. The last test class checks the pin wiring against
gpiozero's mock pins, and is skipped where gpiozero is not installed.
"""

import unittest

from hardware import (
    PIN_L_EN, PIN_LPWM, PIN_R_EN, PIN_RPWM, PIN_SWITCH, GpioHardware, OpenLoopHardware, SimHardware,
)
from steering import (
    CENTER, FAULT_REST_S, LEFT, MAX_DUTY, MAX_RUNS, MOVE_LIMIT_S, RIGHT,
    Steering, parse_command,
)

TICK = 0.002
BEAT = 1 / 15  # the GX10 sends a command every frame


class Wheel(SimHardware):
    """The simulated wheel, keeping a record of how the motor was driven."""

    def __init__(self, clock, **kw):
        super().__init__(clock=clock, **kw)
        self.runs = []  # (start, end, duty) of each finished motor run
        self.pushed_past_end = False
        self._on_at = None

    @property
    def on(self):
        return self._on_at is not None

    def drive(self, direction, duty):
        if (LEFT if direction < 0 else RIGHT) in self.pressed():
            self.pushed_past_end = True
        super().drive(direction, duty)
        self._on_at, self._on_duty = self._clock(), duty

    def off(self):
        super().off()
        if self.on:
            self.runs.append((self._on_at, self._clock(), self._on_duty))
            self._on_at = None


class Bench:
    """A steering controller on the simulated wheel, with time under our control."""

    def __init__(self, **wheel):
        self.now = 0.0
        self.wheel = Wheel(lambda: self.now, **wheel)
        self.lines = []
        self.steering = Steering(self.wheel, log=self.lines.append)
        self.x_seen = [self.wheel.x]

    def run(self, seconds, cmd=None, ttl_ms=400):
        """Let time pass, sending cmd 15 times a second if one is given."""
        end, beat = self.now + seconds, self.now
        while self.now < end:
            if cmd and self.now >= beat:
                self.steering.command(cmd, self.now, ttl_ms)
                beat += BEAT
            self.steering.tick(self.now)
            self.x_seen.append(self.wheel.x)
            self.now += TICK

    def started(self, slow=False):
        """Homed at start-up. slow: then too slow to arrive, so the motor keeps running."""
        self.run(2.0)
        if slow:
            self.wheel.travel_s = 5.0
        return self

    def logged(self, text):
        return any(text in line for line in self.lines)

    def check_limits(self, test):
        """The two limits that must hold whatever else happens."""
        for start, end, duty in self.wheel.runs:
            test.assertLessEqual(duty, MAX_DUTY)
            test.assertLessEqual(end - start, MOVE_LIMIT_S + TICK)
        test.assertFalse(self.wheel.pushed_past_end)


class StartUp(unittest.TestCase):
    def test_homes_to_centre_from_between_positions(self):
        for x in (-0.6, -0.3, 0.4, 0.7):
            with self.subTest(x=x):
                bench = Bench(x=x).started()
                self.assertEqual(bench.wheel.pressed(), {CENTER})
                self.assertFalse(bench.wheel.on)
                self.assertTrue(bench.logged("homed to CENTER"))
                bench.check_limits(self)

    def test_homes_to_centre_from_an_end(self):
        for x in (-1.0, 1.0):
            with self.subTest(x=x):
                bench = Bench(x=x).started()
                self.assertEqual(bench.wheel.pressed(), {CENTER})
                bench.check_limits(self)

    def test_already_centred_does_not_move(self):
        bench = Bench(x=0.0).started()
        self.assertEqual(bench.wheel.runs, [])

    def test_stays_off_after_homing_with_no_commands(self):
        bench = Bench().started()
        runs = len(bench.wheel.runs)
        bench.run(5.0)
        self.assertEqual(len(bench.wheel.runs), runs)
        self.assertFalse(bench.wheel.on)


class Commands(unittest.TestCase):
    def test_follows_left_centre_right(self):
        bench = Bench().started()
        for cmd, switch in ((LEFT, LEFT), (RIGHT, RIGHT), (CENTER, CENTER), (RIGHT, RIGHT)):
            bench.run(1.5, cmd)
            self.assertEqual(bench.wheel.pressed(), {switch})
            self.assertFalse(bench.wheel.on)
        bench.check_limits(self)

    def test_stop_returns_to_centre(self):
        bench = Bench().started()
        bench.run(1.5, LEFT)
        bench.run(1.5, "STOP")
        self.assertEqual(bench.wheel.pressed(), {CENTER})

    def test_motor_is_off_once_in_position(self):
        bench = Bench().started()
        bench.run(1.5, LEFT)
        runs = len(bench.wheel.runs)
        bench.run(5.0, LEFT)
        self.assertEqual(len(bench.wheel.runs), runs)

    def test_free_switches_off_at_once(self):
        bench = Bench().started(slow=True)
        bench.run(0.1, RIGHT)
        self.assertTrue(bench.wheel.on)
        bench.steering.command("FREE", bench.now)
        self.assertFalse(bench.wheel.on)
        bench.run(2.0, "FREE")
        self.assertFalse(bench.wheel.on)

    def test_unknown_command_switches_off(self):
        bench = Bench().started(slow=True)
        bench.run(0.1, RIGHT)
        bench.steering.command("FORWARD", bench.now)
        self.assertFalse(bench.wheel.on)
        self.assertIsNone(bench.steering.want)

    def test_never_drives_into_an_end_stop(self):
        bench = Bench().started()
        for cmd in (LEFT, LEFT, RIGHT, RIGHT, LEFT, CENTER):
            bench.run(1.0, cmd)
        self.assertGreater(min(bench.x_seen), -0.95)
        self.assertLess(max(bench.x_seen), 0.95)
        bench.check_limits(self)


class Silence(unittest.TestCase):
    def test_no_command_for_400_ms_switches_off(self):
        bench = Bench().started(slow=True)
        bench.run(1.0, RIGHT)
        silent_from = bench.now
        bench.run(3.0)
        self.assertFalse(bench.wheel.on)
        self.assertTrue(bench.logged("no command for 400 ms"))
        self.assertGreater(bench.wheel.runs[-1][1], silent_from)
        self.assertLessEqual(bench.wheel.runs[-1][1], silent_from + 0.4 + TICK)
        bench.check_limits(self)

    def test_shorter_ttl_is_honoured(self):
        bench = Bench().started(slow=True)
        bench.steering.command(RIGHT, bench.now, ttl_ms=100)
        sent = bench.now
        bench.run(2.0)
        start, end, _ = bench.wheel.runs[-1]
        self.assertGreater(start, sent - TICK)
        self.assertLessEqual(end, sent + 0.1 + TICK)

    def test_longer_ttl_is_capped_at_400_ms(self):
        bench = Bench().started(slow=True)
        bench.steering.command(RIGHT, bench.now, ttl_ms=60000)
        sent = bench.now
        bench.run(5.0)
        self.assertLessEqual(bench.wheel.runs[-1][1], sent + 0.4 + TICK)
        self.assertFalse(bench.wheel.on)

    def test_homes_to_centre_after_silence(self):
        bench = Bench().started()
        bench.run(1.5, RIGHT)
        bench.run(2.0)  # link drops with the wheel at the right
        del bench.lines[:]
        bench.run(2.0, LEFT)
        self.assertEqual(bench.wheel.pressed(), {LEFT})
        self.assertLess(bench.lines.index("homed to CENTER"), bench.lines.index("at LEFT"))
        bench.check_limits(self)


class Faults(unittest.TestCase):
    def test_stuck_motor_gives_up_at_start(self):
        bench = Bench()
        bench.wheel.stuck = True
        bench.run(20.0)
        self.assertEqual(len(bench.wheel.runs), MAX_RUNS)
        self.assertTrue(bench.logged("fault"))
        self.assertFalse(bench.wheel.on)
        bench.check_limits(self)

    def test_stuck_motor_rests_between_attempts(self):
        bench = Bench().started()
        bench.wheel.stuck = True
        bench.run(30.0, LEFT)
        self.assertTrue(bench.logged("fault"))
        on_time = sum(end - start for start, end, _ in bench.wheel.runs)
        self.assertLess(on_time / 30.0, 0.5)
        ends = [end for _, end, _ in bench.wheel.runs]
        starts = [start for start, _, _ in bench.wheel.runs]
        longest_gap = max(s - e for s, e in zip(starts[1:], ends))
        self.assertGreaterEqual(longest_gap, FAULT_REST_S - TICK)
        bench.check_limits(self)

    def test_timed_out_move_homes_before_carrying_on(self):
        bench = Bench().started()
        bench.wheel.stuck = True
        bench.run(0.42, LEFT)  # the move to LEFT hits the time limit
        self.assertTrue(bench.logged("position unknown"))
        bench.wheel.stuck = False
        bench.wheel.x = -0.5  # and the wheel has been knocked off centre
        del bench.lines[:]
        bench.run(3.0, LEFT)
        self.assertEqual(bench.wheel.pressed(), {LEFT})
        self.assertLess(bench.lines.index("homed to CENTER"), bench.lines.index("at LEFT"))
        bench.check_limits(self)

    def test_dead_centre_switch_is_a_fault_not_a_hunt(self):
        bench = Bench()
        bench.wheel.dead = {CENTER}
        bench.run(20.0, CENTER)
        self.assertTrue(bench.logged("fault"))
        on_time = sum(end - start for start, end, _ in bench.wheel.runs)
        self.assertLess(on_time / 20.0, 0.5)
        bench.check_limits(self)

    def test_two_switches_at_once_is_a_fault(self):
        bench = Bench(x=0.0).started()
        bench.wheel.pressed = lambda: {LEFT, RIGHT}
        bench.run(10.0, LEFT)
        self.assertEqual(bench.wheel.runs, [])
        self.assertTrue(bench.logged("pressed together"))

    def test_hardware_error_switches_off(self):
        bench = Bench().started(slow=True)
        bench.run(0.1, RIGHT)
        self.assertTrue(bench.wheel.on)

        def broken():
            raise OSError("gpio gone")

        bench.wheel.pressed = broken
        with self.assertRaises(OSError):
            bench.steering.tick(bench.now)
        self.assertFalse(bench.wheel.on)
        self.assertIsNone(bench.steering.want)


class Messages(unittest.TestCase):
    def test_reads_the_contract_message(self):
        text = '{"seq": 412, "cmd": "LEFT", "ttl_ms": 400}'
        self.assertEqual(parse_command(text), ("LEFT", 400, 412))

    def test_ttl_defaults_to_400_ms(self):
        self.assertEqual(parse_command('{"cmd": "FREE"}'), ("FREE", 400, None))

    def test_refuses_anything_else(self):
        for text in ("", "LEFT", "[]", "5", '{"seq": 1}', '{"cmd": "FORWARD"}',
                     '{"cmd": "LEFT", "ttl_ms": "soon"}', '{"cmd": "LEFT", "ttl_ms": 0}',
                     '{"cmd": "LEFT", "ttl_ms": true}', '{"cmd": ["LEFT"]}', None):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_command(text)


class Motor:
    """Stands in for the real motor under OpenLoopHardware, and keeps a record."""

    def __init__(self, clock):
        self.clock = clock
        self.runs = []  # (direction, duty, seconds) of each finished run
        self._on = None

    def drive(self, direction, duty):
        self._on = (direction, duty, self.clock())

    def off(self):
        if self._on:
            direction, duty, since = self._on
            self.runs.append((direction, duty, self.clock() - since))
            self._on = None

    def close(self):
        self.off()

    def pressed(self):
        raise AssertionError("open loop must not read the limit switches")


class OpenLoop(unittest.TestCase):
    """No limit switches fitted: the position is worked out from run time."""

    def setUp(self):
        self.now = 0.0
        self.motor = Motor(lambda: self.now)
        self.hw = OpenLoopHardware(self.motor, travel_s=0.25, clock=lambda: self.now)
        self.lines = []
        self.steering = Steering(self.hw, log=self.lines.append)

    def run_for(self, seconds, cmd=None):
        end, beat = self.now + seconds, self.now
        while self.now < end:
            if cmd and self.now >= beat:
                self.steering.command(cmd, self.now)
                beat += BEAT
            self.steering.tick(self.now)
            self.now += TICK

    def test_does_not_move_at_start(self):
        self.run_for(3.0)
        self.assertEqual(self.motor.runs, [])
        self.assertEqual(self.steering.position, CENTER)

    def test_left_then_stop_is_one_short_run_each_way(self):
        self.run_for(1.0)
        self.run_for(1.0, LEFT)
        self.run_for(1.0, "STOP")
        self.assertEqual([r[0] for r in self.motor.runs], [-1, 1])
        for _, duty, seconds in self.motor.runs:
            self.assertEqual(duty, MAX_DUTY)
            self.assertLess(seconds, 0.25)
        self.assertEqual(self.steering.position, CENTER)

    def test_left_to_right_goes_through_centre(self):
        self.run_for(1.0)
        self.run_for(1.0, LEFT)
        self.run_for(1.5, RIGHT)
        self.assertEqual([r[0] for r in self.motor.runs], [-1, 1, 1])
        self.assertEqual(self.steering.position, RIGHT)
        self.assertTrue(all(seconds <= MOVE_LIMIT_S + TICK for _, _, seconds in self.motor.runs))

    def test_silence_switches_the_motor_off_mid_move(self):
        self.hw.travel_s = 5.0  # so slow that the move is still going when the commands stop
        self.run_for(1.0)
        self.run_for(0.2, RIGHT)
        self.run_for(1.0)
        self.assertIsNone(self.motor._on)
        self.assertTrue(any("no command for 400 ms" in line for line in self.lines))


try:
    from gpiozero import Device
    from gpiozero.pins.mock import MockFactory, MockPWMPin
except ImportError:
    Device = None


@unittest.skipUnless(Device, "gpiozero is not installed")
class Pins(unittest.TestCase):
    """The real hardware class, on gpiozero's mock pins."""

    def setUp(self):
        Device.pin_factory = self.pins = MockFactory(pin_class=MockPWMPin)
        self.hw = GpioHardware()
        self.addCleanup(self.hw.close)

    def state(self):
        """(R_EN, L_EN, RPWM, LPWM)"""
        return tuple(self.pins.pin(n).state for n in (PIN_R_EN, PIN_L_EN, PIN_RPWM, PIN_LPWM))

    def test_starts_off(self):
        self.assertEqual(self.state(), (0, 0, 0, 0))

    def test_left_and_right(self):
        self.hw.drive(-1, 0.25)
        self.assertEqual(self.state(), (1, 1, 0.25, 0))
        self.hw.drive(1, 0.2)
        self.assertEqual(self.state(), (1, 1, 0, 0.2))

    def test_never_powers_both_directions(self):
        for direction in (-1, 1, -1, 1):
            self.hw.drive(direction, 0.25)
            rpwm, lpwm = self.state()[2:]
            self.assertEqual(min(rpwm, lpwm), 0)

    def test_power_is_capped(self):
        self.hw.drive(1, 1.0)
        self.assertEqual(self.pins.pin(PIN_LPWM).state, MAX_DUTY)

    def test_off(self):
        self.hw.drive(-1, 0.25)
        self.hw.off()
        self.assertEqual(self.state(), (0, 0, 0, 0))

    def test_swap_reverses_the_motor(self):
        self.hw.close()
        self.hw = GpioHardware(swap=True)
        self.hw.drive(-1, 0.25)
        self.assertEqual(self.state(), (1, 1, 0, 0.25))

    def test_switches_read_pressed_when_pulled_to_ground(self):
        self.assertEqual(self.hw.pressed(), set())
        for name, pin in PIN_SWITCH.items():
            self.pins.pin(pin).drive_low()
            self.assertEqual(self.hw.pressed(), {name})
            self.pins.pin(pin).drive_high()
        self.assertEqual(self.hw.pressed(), set())


if __name__ == "__main__":
    unittest.main()

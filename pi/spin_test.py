"""Bench test: ramps the motor from stopped up to full power, once, then stops.

    python3 spin_test.py              ramp now
    python3 spin_test.py --uptime 15  first wait until the Pi has been on for 15 seconds
    python3 spin_test.py --reverse    turn the other way

FOR THE BENCH ONLY. Run it with the motor free to turn, not fitted to the
steering. It goes past the two limits the controller keeps (25% power and
0.4 seconds a move), because its job is to show the motor's whole range.
It does not start, and it stops at once, if a limit switch is pressed.

sightsense-spin-test.service runs it once at start-up. See README.md.
"""

import argparse
import signal
import sys
import time

# BCM numbers. They must match hardware.py; test_spin.py checks that.
PIN_RPWM = 23
PIN_LPWM = 24
PIN_R_EN = 18
PIN_L_EN = 25
PIN_SWITCHES = (5, 13, 6)
PWM_HZ = 1000

RAMP_S = 10.0  # from stopped to full power
HOLD_S = 2.0  # at full power
STEP_S = 0.05


def spin(ramp_s=RAMP_S, hold_s=HOLD_S, reverse=False, log=print, sleep=time.sleep):
    """Ramp up, hold, switch off. Returns False if a limit switch stopped it."""
    from gpiozero import Button, DigitalOutputDevice, PWMOutputDevice

    enables = (DigitalOutputDevice(PIN_R_EN), DigitalOutputDevice(PIN_L_EN))
    rpwm = PWMOutputDevice(PIN_RPWM, frequency=PWM_HZ)
    lpwm = PWMOutputDevice(PIN_LPWM, frequency=PWM_HZ)
    switches = [Button(pin, pull_up=True) for pin in PIN_SWITCHES]
    powered = lpwm if reverse else rpwm

    def pressed():
        return any(switch.is_pressed for switch in switches)

    try:
        sleep(STEP_S)  # let the switch inputs settle before reading them
        if pressed():
            log("a limit switch is pressed: not starting")
            return False
        for enable in enables:
            enable.on()
        steps = max(1, round(ramp_s / STEP_S))
        for step in range(1, steps + 1):
            if pressed():
                log("a limit switch is pressed: stopping")
                return False
            powered.value = step / steps
            if step % max(1, steps // 10) == 0:
                log(f"power {step / steps:.0%}")
            sleep(STEP_S)
        for _ in range(round(hold_s / STEP_S)):
            if pressed():
                log("a limit switch is pressed: stopping")
                return False
            sleep(STEP_S)
        return True
    finally:
        rpwm.value = 0
        lpwm.value = 0
        for enable in enables:
            enable.off()
        for device in (rpwm, lpwm, *enables, *switches):
            device.close()
        log("motor off")


def wait_for_uptime(seconds, sleep=time.sleep):
    """Sleep until the Pi has been running for this long."""
    with open("/proc/uptime") as f:
        up = float(f.read().split()[0])
    if up < seconds:
        sleep(seconds - up)


def main():
    parser = argparse.ArgumentParser(description="SightSense motor bench test")
    parser.add_argument("--uptime", type=float, default=0, help="wait until the Pi has been on this many seconds")
    parser.add_argument("--reverse", action="store_true", help="turn the other way")
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    wait_for_uptime(args.uptime)
    print("bench test: ramping the motor to full power. The motor must be free to turn.", flush=True)
    spin(reverse=args.reverse, log=lambda text: print(text, flush=True))


if __name__ == "__main__":
    main()

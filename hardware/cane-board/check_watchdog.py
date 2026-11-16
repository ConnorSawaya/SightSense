"""Simulates the motor driver's watchdog: the charge pump that holds nSLEEP high
only while the processor keeps toggling HBEAT.

The pump is HBEAT -> R10 220 -> C8 1 uF -> D4 BAT54S (one diode to ground, one on
to HB_DC) -> C9 1 uF, loaded by R11 100k and the driver's own 100k pull-down.
Prints the voltage nSLEEP settles at for each heartbeat rate (a square wave of f
full cycles a second, so 2f toggles), how long the driver takes to wake, and how
long after the toggling stops it is asleep: with the pin left low, and with it
left high, when C8 still feeds the load through the diode. Standard library only:

    python3 check_watchdog.py

Diode: BAT54S, 0.32 V at 1 mA. Thresholds: DRV8876 datasheet, 1.5 V high, 0.8 V
low. A model, not a measurement.
"""

import math

VT, N, IS = 0.02585, 1.05, 7.6e-9  # the BAT54S as an ideal diode law
R_PIN, R10, C8, C9 = 25.0, 220.0, 1e-6, 1e-6  # R_PIN: the ESP32 pin's own resistance
R_LOAD = 1 / (1 / 100e3 + 1 / 100e3)  # R11 and the driver's pull-down
VIH, VIL, VDD = 1.5, 0.8, 3.3


def diode(v):
    return IS * (math.exp(min(v, 0.9) / (N * VT)) - 1)


def run(f, t_run, t_after, stop_high=False, dt=2e-7):
    """A square wave of f Hz for t_run seconds, then the pin held low (or high) for t_after."""
    vac = vdc = q8 = 0.0
    period, t = 1 / f, 0.0
    lo = hi = wake = asleep = None
    while t < t_run + t_after:
        toggling = t < t_run
        vin = (VDD if (t % period) < period / 2 else 0.0) if toggling else (VDD if stop_high else 0.0)
        v8 = q8 / C8
        r = R_PIN + R10
        for _ in range(30):  # the node between C8 and the diodes
            i_r = (vin - (vac + v8)) / r
            i_d1, i_d2 = diode(-vac), diode(vac - vdc)
            f_ = i_r + i_d1 - i_d2
            df = -1 / r - (diode(-vac + 1e-4) - i_d1) / 1e-4 - (diode(vac + 1e-4 - vdc) - i_d2) / 1e-4
            step = -f_ / df
            vac += max(-0.05, min(0.05, step))
            if abs(step) < 1e-7:
                break
        q8 += (vin - (vac + v8)) / r * dt
        vdc += (diode(vac - vdc) - vdc / R_LOAD) / C9 * dt
        if toggling and t > t_run - 2 * period:
            lo = vdc if lo is None else min(lo, vdc)
            hi = vdc if hi is None else max(hi, vdc)
        if wake is None and vdc >= VIH:
            wake = t
        if not toggling and asleep is None and vdc <= VIL:
            asleep = t - t_run
        t += dt
    return lo, hi, wake, asleep


if __name__ == "__main__":
    for f in (20, 30, 50, 100, 200, 500, 1000, 5000):
        lo, hi, wake, asleep = run(f, max(0.3, 40 / f), 0.3)
        asleep_high = run(f, max(0.3, 40 / f), 0.3, stop_high=True)[3]
        ok = "ok" if lo >= VIH else "TOO SLOW: driver sleeps"
        print(f"{f:5d} Hz: nSLEEP {lo:.2f} to {hi:.2f} V, awake after {1e3 * wake:.1f} ms, asleep "
              f"{1e3 * asleep:.0f} ms after it stops low, {1e3 * asleep_high:.0f} ms after it stops high  {ok}")

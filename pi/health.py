"""The Pi's own health, sent to the GX10 for the dashboard every 2 seconds.

    {"health": {"cpu_c": 44.4, "in_v": 5.28, "undervolt_now": false, ...}}

Standard library only. Every reading is optional: one that fails is left out, and
nothing here touches the motor. There is no battery gauge on the cane: the Pi's supply
(a 12 V to 5 V converter on the motor's pack, or a USB-C power bank) does not report
its charge, so the input voltage (in_v, which sags as the supply runs down) and the
undervoltage flags stand in for it.
"""

import os
import subprocess
import time

HEALTH_S = 2.0

# vcgencmd get_throttled bits (Raspberry Pi documentation)
UNDERVOLT_NOW, FREQ_CAPPED_NOW, THROTTLED_NOW, SOFT_TEMP_NOW = 0x1, 0x2, 0x4, 0x8
UNDERVOLT_SINCE_BOOT, THROTTLED_SINCE_BOOT = 0x10000, 0x40000


def _vcgencmd(*args, timeout=1.0):
    try:
        return subprocess.run(["vcgencmd", *args], capture_output=True, text=True, timeout=timeout).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def cpu_temp_c():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as fh:
            return round(int(fh.read().strip()) / 1000, 1)
    except (OSError, ValueError):
        return None


def throttled_bits():
    out = _vcgencmd("get_throttled")  # throttled=0x50000
    try:
        return int(out.split("=", 1)[1], 16)
    except (IndexError, ValueError):
        return None


def input_volts():
    """The 5 V input (Pi 5 power chip), from: EXT5V_V volt(24)=5.27960000V"""
    out = _vcgencmd("pmic_read_adc", "EXT5V_V")
    try:
        return round(float(out.rsplit("=", 1)[1].rstrip("V")), 2)
    except (IndexError, ValueError):
        return None


def wifi_dbm():
    try:
        with open("/proc/net/wireless") as fh:
            for line in fh.readlines()[2:]:
                parts = line.split()
                if len(parts) > 3:
                    return int(float(parts[3].rstrip(".")))
    except (OSError, ValueError):
        pass
    return None


def uptime_s():
    try:
        with open("/proc/uptime") as fh:
            return int(float(fh.read().split()[0]))
    except (OSError, ValueError, IndexError):
        return None


def read(about=None):
    """One health report. about: the controller's own settings (mode, duty, rated_rpm)."""
    h = {"cpu_c": cpu_temp_c(), "in_v": input_volts(), "wifi_dbm": wifi_dbm(), "uptime_s": uptime_s()}
    try:
        h["load"] = round(os.getloadavg()[0], 2)
    except (AttributeError, OSError):  # Windows has no load average
        pass
    bits = throttled_bits()
    if bits is not None:
        h.update({
            "undervolt_now": bool(bits & UNDERVOLT_NOW),
            "undervolt_since_boot": bool(bits & UNDERVOLT_SINCE_BOOT),
            "throttled_now": bool(bits & (THROTTLED_NOW | FREQ_CAPPED_NOW | SOFT_TEMP_NOW)),
            "throttled_since_boot": bool(bits & THROTTLED_SINCE_BOOT),
        })
    h.update(about or {})
    h["t"] = round(time.time(), 1)
    return {k: v for k, v in h.items() if v is not None}

"""Calculate measured wheel RPM from counted output-shaft turns and elapsed time.

This does not operate the motor. Use a marked wheel/video; the current wiring
has no encoder. Count only the interval you actually measured.
"""

import argparse
import math


def measured_rpm(turns, seconds):
    if (isinstance(turns, bool) or isinstance(seconds, bool)
            or not math.isfinite(turns) or not math.isfinite(seconds)
            or turns < 0 or seconds <= 0):
        raise ValueError("turns must be finite and nonnegative; seconds must be finite and positive")
    return 60 * turns / seconds


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turns", type=float, required=True)
    parser.add_argument("--seconds", type=float, required=True)
    args = parser.parse_args()
    try:
        print(f"Measured over your supplied interval: {measured_rpm(args.turns, args.seconds):.2f} rpm")
    except ValueError as error:
        parser.error(str(error))

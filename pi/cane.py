"""The cane's motor controller. Run it on the Raspberry Pi.

    python3 cane.py --gx10 192.168.8.10     follow the GX10
    python3 cane.py --typed                 type commands instead
    python3 cane.py --typed --sim           same, with a simulated wheel (any computer)
    python3 cane.py --bench switches        print each switch as it is pressed
    python3 cane.py --bench motor           one short pulse each way

See README.md.
"""

import argparse
import asyncio
import json
import os
import signal
import sys
import threading
import time

from steering import MAX_DUTY, Steering, parse_command

TICK_S = 0.002
COMMAND_PORT = 8766
RETRY_S = 0.5
TYPED_HZ = 15
WORDS = {
    "L": "LEFT", "C": "CENTER", "R": "RIGHT", "S": "STOP", "F": "FREE",
    "CENTRE": "CENTER",
}

START = time.monotonic()


def log(text):
    print(f"[{time.monotonic() - START:8.3f}] {text}", flush=True)


class Inbox:
    """Holds only the newest message. Older ones are dropped, never queued."""

    def __init__(self):
        self._lock = threading.Lock()
        self._item = None

    def put(self, text):
        with self._lock:
            self._item = (text, time.monotonic())

    def take(self):
        with self._lock:
            item, self._item = self._item, None
        return item


def control_loop(hw, inbox, stop, duty):
    steering = Steering(hw, duty=duty, log=log)
    try:
        while not stop.is_set():
            item = inbox.take()
            if item:
                text, received = item
                try:
                    cmd, ttl_ms, _ = parse_command(text)
                except ValueError as e:
                    steering.release(f"bad message ({e})")
                else:
                    steering.command(cmd, received, ttl_ms)
            try:
                steering.tick(time.monotonic())
            except Exception as e:  # tick() has already switched the driver off
                log(f"error: {e!r}")
            time.sleep(TICK_S)
    finally:
        hw.off()
        hw.close()
        log("driver off, stopped")


def follow_gx10(url, inbox):
    """Keep a WebSocket open to the GX10's command port, reconnecting forever."""
    import websockets

    async def listen():
        status = None
        while True:
            try:
                async with websockets.connect(url, open_timeout=3) as link:
                    log(status := f"connected to {url}")
                    async for message in link:
                        inbox.put(message)
                problem = "link closed"
            except Exception as e:
                problem = f"no link to {url}: {e!r}"
            if problem != status:
                log(status := problem)
            await asyncio.sleep(RETRY_S)

    asyncio.run(listen())


def follow_keyboard(inbox, stop):
    """Read commands from the keyboard and repeat the last one as the heartbeat."""
    current = {"cmd": None}

    def heartbeat():
        seq = 0
        while not stop.is_set():
            if current["cmd"]:
                seq += 1
                inbox.put(json.dumps({"seq": seq, "cmd": current["cmd"], "ttl_ms": 400}))
            time.sleep(1 / TYPED_HZ)

    threading.Thread(target=heartbeat, daemon=True).start()
    print("Type left, center, right, stop, free, silence or quit.", flush=True)
    for line in sys.stdin:
        word = line.strip().upper()
        word = WORDS.get(word, word)
        if word == "QUIT":
            break
        if word == "SILENCE":  # stop sending, as if the link dropped
            current["cmd"] = None
        elif word:
            current["cmd"] = word  # an unknown word is sent as it is, to test the refusal
    stop.set()


def bench(hw, what, duty):
    """Bring-up checks for the wiring. Not used in normal running."""
    try:
        if what == "motor":
            for direction, name in ((-1, "left"), (1, "right")):
                log(f"motor {name} at {duty:.0%} for 0.3 s")
                hw.drive(direction, duty)
                time.sleep(0.3)
                hw.off()
                time.sleep(1.0)
        else:
            log("press each switch; Ctrl+C to finish")
            seen = None
            while True:
                pressed = hw.pressed()
                if pressed != seen:
                    log(f"pressed: {sorted(pressed) or 'none'}")
                    seen = pressed
                time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        hw.off()
        hw.close()


def main():
    parser = argparse.ArgumentParser(description="SightSense cane motor controller")
    parser.add_argument("--gx10", default=os.environ.get("SIGHTSENSE_GX10"),
                        help="GX10 address, as host or host:port")
    parser.add_argument("--typed", action="store_true", help="take commands from the keyboard")
    parser.add_argument("--sim", action="store_true", help="simulated wheel, no GPIO")
    parser.add_argument("--bench", choices=("motor", "switches"), help="wiring check")
    parser.add_argument("--swap", action="store_true", help="reverse the motor direction")
    parser.add_argument("--duty", type=float, default=MAX_DUTY,
                        help=f"motor power, at most {MAX_DUTY}")
    args = parser.parse_args()
    if not (args.bench or args.typed or args.gx10):
        parser.error("give --gx10 ADDRESS, --typed or --bench")
    duty = max(0.0, min(args.duty, MAX_DUTY))

    if args.sim:
        from hardware import SimHardware
        hw = SimHardware()
    else:
        from hardware import GpioHardware
        hw = GpioHardware(swap=args.swap)

    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    if args.bench:
        bench(hw, args.bench, duty)
        return

    inbox, stop = Inbox(), threading.Event()
    if args.typed:
        source = threading.Thread(target=follow_keyboard, args=(inbox, stop), daemon=True)
    else:
        host = args.gx10 if ":" in args.gx10 else f"{args.gx10}:{COMMAND_PORT}"
        source = threading.Thread(target=follow_gx10, args=(f"ws://{host}", inbox), daemon=True)
    source.start()
    try:
        control_loop(hw, inbox, stop, duty)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

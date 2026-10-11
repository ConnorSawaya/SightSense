"""The cane's motor controller. Run it on the Raspberry Pi.

    python3 cane.py --wheel-drive --gx10 ADDRESS:8766   follow the GX10 (the direct-drive wheel fitted now)
    python3 cane.py --wheel-drive --typed               type commands instead
    python3 cane.py --wheel-drive --typed --sim         same, with a simulated wheel (any computer)
    python3 cane.py --gx10 ADDRESS               earlier position steering: needs limit switches, homes at start-up
    python3 cane.py --gx10 ADDRESS --open-loop   position steering by timing: the motor moves at start-up
    python3 cane.py --bench switches        print each switch as it is pressed
    python3 cane.py --bench button          print the talk button as it is pressed
    python3 cane.py --bench motor           one short pulse each way

See README.md.
"""

import argparse
import asyncio
import json
import math
import os
import signal
import sys
import threading
import time

import health
import talk_button
from steering import MAX_DUTY, Steering, command_ttl, parse_command
from wheel_drive import WheelDrive

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


def control_loop(hw, inbox, stop, duty, wheel_drive=False, rated_rpm=120):
    steering = WheelDrive(hw, duty=duty, rated_rpm=rated_rpm, log=log) if wheel_drive else Steering(hw, duty=duty, log=log)
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
                    now = time.monotonic()
                    remaining_ms = command_ttl(ttl_ms) * 1000 - (now - received) * 1000
                    if remaining_ms <= 0:
                        steering.release("queued command expired")
                    else:
                        # Dead time starts when GPIO is switched off, not when
                        # the network thread received the command.
                        steering.command(cmd, now, remaining_ms)
            try:
                steering.tick(time.monotonic())
            except Exception as e:  # tick() has already switched the driver off
                log(f"error: {e!r}")
            time.sleep(TICK_S)
    finally:
        try:
            hw.off()
        finally:
            hw.close()
        log("driver off, stopped")


async def send_health(link, stop, about):
    """Temperature, input voltage and settings to the GX10 dashboard every 2 s.
    Runs beside the command reader; a failure here never reaches the motor."""
    while not stop.is_set():
        try:
            report = await asyncio.to_thread(health.read, about)  # vcgencmd takes a few ms
            await link.send(json.dumps({"health": report}))
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log(f"health report failed: {e!r}")
            return
        await asyncio.sleep(health.HEALTH_S)


async def send_button(link, stop, button):
    """Tells the GX10 when the talk button goes down and up, so the phone can listen.
    Runs beside the command reader; a failure here never reaches the motor."""
    presses = talk_button.Debounce()
    while not stop.is_set():
        try:
            event = presses.update(button.is_pressed(), time.monotonic())
            if event:
                log(f"talk button {event}")
                await link.send(json.dumps({"button": event}))
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log(f"talk button stopped: {e!r}")
            return
        await asyncio.sleep(talk_button.POLL_S)


async def listen_gx10(url, inbox, stop, about=None, button=None):
    """Keep a WebSocket open to the GX10's command port, reconnecting forever."""
    import websockets
    status = None
    while not stop.is_set():
        try:
            async with websockets.connect(url, open_timeout=3, close_timeout=1,
                                          max_size=4096, max_queue=1,
                                          ping_interval=2, ping_timeout=3) as link:
                log(status := f"connected to {url}")
                senders = [asyncio.create_task(send_health(link, stop, about))]
                if button is not None:
                    senders.append(asyncio.create_task(send_button(link, stop, button)))
                try:
                    while not stop.is_set():
                        try:
                            message = await asyncio.wait_for(link.recv(), 0.1)
                        except asyncio.TimeoutError:
                            continue
                        inbox.put(message)
                finally:
                    for sender in senders:
                        sender.cancel()
            problem = "link closed"
        except Exception as e:
            problem = f"no link to {url}: {e!r}"
        inbox.put('{"cmd":"FREE","ttl_ms":400}')
        if problem != status:
            log(status := problem)
        await asyncio.sleep(RETRY_S)


def follow_gx10(url, inbox, stop, about=None, button=None):
    asyncio.run(listen_gx10(url, inbox, stop, about, button))


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
        elif what == "button":
            log(f"press the talk button (GPIO{talk_button.PIN_TALK}, header pin 11 to ground); Ctrl+C to finish")
            button, presses = talk_button.TalkButton(), talk_button.Debounce()
            try:
                while True:
                    event = presses.update(button.is_pressed(), time.monotonic())
                    if event:
                        log(f"talk button {event}")
                    time.sleep(talk_button.POLL_S)
            finally:
                button.close()
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
    parser.add_argument("--bench", choices=("motor", "switches", "button"), help="wiring check")
    parser.add_argument("--swap", action="store_true", help="reverse the motor direction")
    parser.add_argument("--no-button", action="store_true", help="do not read the talk button on GPIO17")
    parser.add_argument("--open-loop", action="store_true",
                        help="no limit switches: work out the position from run time; centre the wheel by hand first")
    parser.add_argument("--wheel-drive", action="store_true",
                        help="direct mecanum wheel: LEFT/RIGHT spin opposite ways; CENTER/STOP/FREE switch off")
    parser.add_argument("--rated-rpm", type=float, default=120,
                        help="motor label RPM at full duty, for an unmeasured speed estimate only")
    parser.add_argument("--travel", type=float, default=0.25,
                        help="with --open-loop: seconds from centre to one side")
    parser.add_argument("--duty", type=float, default=MAX_DUTY,
                        help=f"motor power, at most {MAX_DUTY}")
    args = parser.parse_args()
    if args.wheel_drive and args.open_loop:
        parser.error("--wheel-drive and --open-loop describe different mechanisms")
    if not math.isfinite(args.duty) or args.duty < 0:
        parser.error("--duty must be finite and nonnegative")
    if not math.isfinite(args.rated_rpm) or args.rated_rpm <= 0:
        parser.error("--rated-rpm must be finite and positive")
    if not math.isfinite(args.travel) or args.travel <= 0:
        parser.error("--travel must be finite and positive")
    args.gx10 = (args.gx10 or "").strip()  # an address typed into a file on Windows ends in a stray character
    if not (args.bench or args.typed or args.gx10):
        parser.error("give --gx10 ADDRESS, --typed or --bench")
    duty = max(0.0, min(args.duty, MAX_DUTY))

    if args.sim:
        from hardware import SimHardware
        hw = SimHardware()
    else:
        from hardware import GpioHardware, OpenLoopHardware
        hw = GpioHardware(swap=args.swap, read_switches=not args.wheel_drive)
        if args.open_loop and not args.bench:
            hw = OpenLoopHardware(hw, travel_s=min(max(args.travel, 0.05), 0.35))
            log("open loop: no limit switches are read. The wheel must be at centre now.")

    for name in ("SIGTERM", "SIGHUP", "SIGQUIT"):  # a closed terminal must switch the driver off too
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), lambda *_: sys.exit(0))
    if hasattr(signal, "SIGTSTP"):
        signal.signal(signal.SIGTSTP, signal.SIG_IGN)  # never freeze the watchdog with the motor on
    if args.bench:
        bench(hw, args.bench, duty)
        return

    inbox, stop = Inbox(), threading.Event()
    if args.typed:
        source = threading.Thread(target=follow_keyboard, args=(inbox, stop), daemon=True)
    else:
        host = args.gx10 if ":" in args.gx10 else f"{args.gx10}:{COMMAND_PORT}"
        about = {"mode": "wheel-drive" if args.wheel_drive else "open-loop" if args.open_loop else "steering",
                 "duty": duty, "max_duty": MAX_DUTY, "rated_rpm": args.rated_rpm, "swap": args.swap}
        button = None
        if not args.sim and not args.no_button:
            try:
                button = talk_button.TalkButton()
            except Exception as e:  # the cane still steers without it
                log(f"talk button not read: {e!r}")
        source = threading.Thread(target=follow_gx10, args=(f"ws://{host}", inbox, stop, about, button), daemon=True)
    if args.wheel_drive:
        log(f"direct wheel drive; LEFT uses {'LPWM GPIO24' if args.swap else 'RPWM GPIO23'}, "
            f"RIGHT uses {'RPWM GPIO23' if args.swap else 'LPWM GPIO24'}")
        log(f"motor label {args.rated_rpm:g} rpm; duty {duty:.0%}; estimated "
            f"{args.rated_rpm * duty:g} rpm while powered (not measured)")
    source.start()
    try:
        control_loop(hw, inbox, stop, duty, args.wheel_drive, args.rated_rpm)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()


if __name__ == "__main__":
    main()

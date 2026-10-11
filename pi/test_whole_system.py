"""The whole cane on one computer: phone frames in, motor pins out, with voice, a place, the talk button and the dashboard.

    python3 -m unittest test_whole_system -v        (from this folder; takes about 20 seconds)

Real: the GX10's frame service and dashboard, the Pi's controller in direct wheel
mode, and the WebSockets and HTTP between them.
Stood in for: the phone (the GX10 code's fake frames, typed voice text and a made-up
route), the motor (gpiozero's mock pins), the talk button and the vision-language
model. YOLO is off. Neither model decides the wheel command: that comes from depth.

Skipped where numpy, OpenCV, websockets or gpiozero is missing.
"""

import asyncio
import json
import socket
import sys
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

import cane
from hardware import PIN_L_EN, PIN_LPWM, PIN_R_EN, PIN_RPWM, GpioHardware

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "gx10"))
try:
    import vlm
    from dashboard.dashboard import start as start_dashboard
    from gpiozero import Device
    from gpiozero.pins.mock import MockFactory, MockPWMPin
    from ingest.fake_phone import walk_frames
    from ingest.server import Pipeline, Server
    from websockets.asyncio.client import connect
    from websockets.asyncio.server import serve
except Exception as problem:  # the GX10 code or one of its requirements is not here
    Server, WHY = None, repr(problem)
else:
    WHY = ""

MOTOR_PINS = (PIN_R_EN, PIN_L_EN, PIN_RPWM, PIN_LPWM)


class Button:
    """Stands in for the talk button."""

    down = False

    def is_pressed(self):
        return self.down


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@unittest.skipUnless(Server, f"the GX10 code or a requirement is missing: {WHY}")
class WholeSystem(unittest.IsolatedAsyncioTestCase):
    async def test_frames_voice_places_button_and_dashboard(self):
        wrong = []

        def expect(ok, what):
            if not ok:
                wrong.append(what)

        Device.pin_factory = pins = MockFactory(pin_class=MockPWMPin)
        hw = GpioHardware(read_switches=False)
        stop, inbox, lines, button = threading.Event(), cane.Inbox(), [], Button()
        got, powered, peak = [], set(), 0.0

        def motor_pins():
            return tuple(pins.pin(n).state for n in MOTOR_PINS)

        def fetch(path, body=None):
            data = None if body is None else json.dumps(body).encode()
            with urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{dash_port}{path}", data=data), timeout=5) as r:
                return r.status, r.read()

        with patch("vlm.warm", return_value="stubbed"), \
                patch("vlm.describe", return_value=vlm.Answer(True, "A stubbed description.")), \
                patch.object(cane, "log", side_effect=lines.append):
            server = Server(Pipeline(False))
            dash_port = free_port()
            dashboard = start_dashboard(server, dash_port)
            loops = [asyncio.create_task(server.run_frames()), asyncio.create_task(server.manual_loop())]
            motor = threading.Thread(target=cane.control_loop, args=(hw, inbox, stop, 0.25, True, 120))
            motor.start()
            pi = None
            try:
                async with serve(server.phone, "127.0.0.1", 0, max_size=8 << 20) as phone_side, \
                        serve(server.pi, "127.0.0.1", 0) as pi_side:
                    phone_port = phone_side.sockets[0].getsockname()[1]
                    pi_port = pi_side.sockets[0].getsockname()[1]
                    pi = asyncio.create_task(cane.listen_gx10(f"ws://127.0.0.1:{pi_port}", inbox, stop, {"mode": "wheel-drive"}, button))
                    async with connect(f"ws://127.0.0.1:{phone_port}", max_size=8 << 20) as phone:
                        async def listen():
                            async for message in phone:
                                got.append(json.loads(message))

                        listener = asyncio.create_task(listen())
                        deadline = time.monotonic() + 3
                        while not server.pis and time.monotonic() < deadline:
                            await asyncio.sleep(0.02)
                        expect(len(server.pis) == 1, "the Pi controller did not connect to the command port")

                        # 1. the fake phone walks at a wall
                        commands = []
                        for raw, _wall_m in walk_frames():
                            await phone.send(raw)
                            await asyncio.sleep(1 / 15)
                            commands.append(server.pipe.status.get("cmd"))
                            state = motor_pins()
                            peak = max(peak, state[2], state[3])
                            powered |= {name for name, value in (("RPWM", state[2]), ("LPWM", state[3])) if value > 0}
                        guidance = [m for m in got if "state" in m]
                        # a frame is dropped when a newer one arrives first, so a busy computer answers fewer
                        expect(len(guidance) >= 40, f"the phone got guidance for only {len(guidance)} of 120 frames")
                        expect(all("direction" in m for m in guidance), "a guidance message has no direction")
                        expect("CENTER" in commands, "it never went straight")
                        expect(commands[-1] == "STOP" and guidance and guidance[-1]["state"] == "STOP", "it did not end stopped at the wall")
                        expect(bool(powered), "the Pi never powered the motor")
                        expect(peak <= 0.25, f"motor power reached {peak:.0%}, above the 25% cap")
                        await asyncio.sleep(0.6)
                        expect(motor_pins() == (0, 0, 0, 0), "a motor pin was still on 0.6 s after the frames stopped")
                        expect(server.pi_health is not None, "the Pi's health report did not reach the GX10")

                        # 2. the dashboard
                        code, page = await asyncio.to_thread(fetch, "/")
                        expect(code == 200 and b"<html" in page.lower(), "the dashboard page did not load")
                        _, body = await asyncio.to_thread(fetch, "/status")
                        status = json.loads(body)
                        expect(status.get("pis") == 1 and status.get("pi_health"), "the dashboard does not show the Pi and its health")

                        # 3. voice, a place and the talk button, standing still in the open (the walk's first frame, sent again)
                        still = next(iter(walk_frames()))[0]

                        async def frames(seconds):
                            end = time.monotonic() + seconds
                            while time.monotonic() < end:
                                await phone.send(still)
                                await asyncio.sleep(1 / 15)

                        async def after(message, seconds=1.2):
                            mark = len(got)
                            await phone.send(json.dumps(message))
                            await frames(seconds)
                            return got[mark:]

                        def said(replies):
                            return [m["speech"] for m in replies if m.get("speech")]

                        expect(said(await after({"text": "is the path clear"})), "'is the path clear' got no answer")
                        expect("A stubbed description." in said(await after({"text": "what's in front of me"}, 1.5)),
                               "'what's in front of me' did not come back from the vision model")
                        replies = await after({"text": "take me to the grocery store"})
                        expect([m["lookup"] for m in replies if "lookup" in m] == ["grocery store"], "'take me to the grocery store' did not ask the phone for a place")
                        route = {"dest": "Corner Grocery", "distance_m": 420, "eta_min": 6,
                                 "polyline": [[37.0, -122.0], [37.0005, -122.0], [37.001, -122.0005]],
                                 "steps": [{"lat": 37.0005, "lon": -122.0, "text": "Turn left onto First Street"}]}
                        expect(any("Corner Grocery" in t and "yes" in t.lower() for t in said(await after(route, 1.0))), "the route was not read back for a yes")
                        expect(any("Going to" in t for t in said(await after({"text": "yes"}))), "'yes' did not start the route")
                        expect(said(await after({"text": "stop"})), "'stop' was not acknowledged")

                        mark = len(got)
                        button.down = True
                        await frames(0.15)
                        button.down = False
                        await frames(0.5)
                        expect([m["listen"] for m in got[mark:] if "listen" in m] == [True], "a click of the talk button did not tell the phone to listen once")
                        # ... and what the phone then heard is answered, as an assistant would
                        expect(any(t.startswith("I can tell you") for t in said(await after({"text": "what can you do"}))),
                               "after the button, 'what can you do' was not answered")
                        expect("A stubbed description." in said(await after({"text": "what's in front of me"}, 1.5)),
                               "after the button, 'what's in front of me' was not answered by the vision model")
                        _, body = await asyncio.to_thread(fetch, "/status")
                        expect(any("talk button down" in line[2] for line in json.loads(body).get("log", [])),
                               "the dashboard does not show the talk button press")
                        mark = len(got)
                        button.down = True
                        await frames(0.9)
                        button.down = False
                        await frames(0.4)
                        expect([m["listen"] for m in got[mark:] if "listen" in m] == [True, False], "holding the talk button did not tell the phone to listen, then stop")

                        # 4. manual steering from the dashboard, and handing back
                        await asyncio.to_thread(fetch, "/manual", {"cmd": "LEFT"})
                        await frames(0.4)
                        expect(server.manual is not None, "the dashboard could not take the wheel")
                        await asyncio.to_thread(fetch, "/manual", {"cmd": "AUTO"})
                        await frames(0.3)
                        expect(server.manual is None, "the dashboard did not hand the wheel back")
                        listener.cancel()
            finally:
                stop.set()
                if pi is not None:
                    await asyncio.wait_for(pi, 3)
                motor.join(3)
                for loop in loops:
                    loop.cancel()
                await asyncio.gather(*loops, return_exceptions=True)
                dashboard.shutdown()
                dashboard.server_close()
                server.worker.shutdown(wait=True)
                server.writer.shutdown(wait=True)
        expect(not motor.is_alive() and motor_pins() == (0, 0, 0, 0), "the controller did not stop with every motor pin off")
        self.assertEqual(wrong, [])


if __name__ == "__main__":
    unittest.main()

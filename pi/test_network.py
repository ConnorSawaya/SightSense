"""Real WebSockets and the real Pi control loop, on gpiozero's mock pins.

The full-flow test also uses the GX10 depth pipeline and fake phone frames.
No physical motor or AI model is used.
"""

import asyncio
import json
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import cane
from hardware import GpioHardware, PIN_L_EN, PIN_LPWM, PIN_R_EN, PIN_RPWM

try:
    import websockets
    from gpiozero import Device
    from gpiozero.pins.mock import MockFactory, MockPWMPin
except ImportError:
    Device = None


@unittest.skipUnless(Device, "websockets and gpiozero are required")
class Network(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.lines = []
        self.logging = patch.object(cane, "log", side_effect=self.lines.append)
        self.logging.start()
        Device.pin_factory = self.pins = MockFactory(pin_class=MockPWMPin)
        self.hw = GpioHardware(read_switches=False)
        self.events = []
        drive, off = self.hw.drive, self.hw.off

        def record_drive(direction, duty):
            drive(direction, duty)
            self.events.append(("drive", direction, time.monotonic()))

        def record_off():
            off()
            self.events.append(("off", 0, time.monotonic()))

        self.hw.drive, self.hw.off = record_drive, record_off
        self.stop = threading.Event()
        self.inbox = cane.Inbox()
        self.thread = threading.Thread(target=cane.control_loop,
                                       args=(self.hw, self.inbox, self.stop, 0.25, True, 120))
        self.thread.start()
        self.links = asyncio.Queue()

        async def handler(link):
            await self.links.put(link)
            await link.wait_closed()

        self.server = await websockets.serve(handler, "127.0.0.1", 0)
        port = self.server.sockets[0].getsockname()[1]
        self.listener = asyncio.create_task(cane.listen_gx10(f"ws://127.0.0.1:{port}", self.inbox, self.stop))
        self.link = await asyncio.wait_for(self.links.get(), 2)

    async def asyncTearDown(self):
        self.stop.set()
        self.server.close()
        await self.server.wait_closed()
        await asyncio.wait_for(self.listener, 3)
        self.thread.join(2)
        self.logging.stop()
        self.assertFalse(self.thread.is_alive())

    def state(self):
        return tuple(self.pins.pin(n).state for n in (PIN_R_EN, PIN_L_EN, PIN_RPWM, PIN_LPWM))

    async def wait_state(self, expected):
        deadline = time.monotonic() + 1
        while self.state() != expected and time.monotonic() < deadline:
            await asyncio.sleep(0.005)
        self.assertEqual(self.state(), expected)

    async def send(self, cmd, ttl=400):
        await self.link.send(json.dumps({"seq": 1, "cmd": cmd, "ttl_ms": ttl}))

    async def test_all_commands_reach_the_gpio(self):
        for cmd, expected in (("LEFT", (1, 1, 0.25, 0)), ("STOP", (0, 0, 0, 0)),
                              ("RIGHT", (1, 1, 0, 0.25)), ("CENTER", (0, 0, 0, 0)),
                              ("LEFT", (1, 1, 0.25, 0)), ("FREE", (0, 0, 0, 0))):
            await self.send(cmd)
            await self.wait_state(expected)

    async def test_silence_switches_off_with_socket_still_open(self):
        await self.send("RIGHT")
        await self.wait_state((1, 1, 0, 0.25))
        await asyncio.sleep(0.45)
        await self.wait_state((0, 0, 0, 0))

    async def test_invalid_packet_switches_off(self):
        await self.send("LEFT")
        await self.wait_state((1, 1, 0.25, 0))
        await self.link.send('{"cmd":"RIGHT","ttl_ms":NaN}')
        await self.wait_state((0, 0, 0, 0))

    async def test_reversing_passes_through_off(self):
        await self.send("LEFT")
        await self.wait_state((1, 1, 0.25, 0))
        start = len(self.events)
        await self.send("RIGHT")
        await self.wait_state((1, 1, 0, 0.25))
        off, drive = self.events[start:start + 2]
        self.assertEqual((off[0], drive[:2]), ("off", ("drive", 1)))
        self.assertGreaterEqual(drive[2] - off[2], 0.049)

    async def test_queued_reversal_gets_full_dead_time_at_processing(self):
        await self.send("LEFT")
        await self.wait_state((1, 1, 0.25, 0))
        start = len(self.events)
        with self.inbox._lock:
            self.inbox._item = ('{"cmd":"RIGHT","ttl_ms":400}', time.monotonic() - 0.2)
        await self.wait_state((1, 1, 0, 0.25))
        off, drive = self.events[start:start + 2]
        self.assertEqual((off[0], drive[:2]), ("off", ("drive", 1)))
        self.assertGreaterEqual(drive[2] - off[2], 0.049)

    async def test_disconnect_releases_and_reconnects(self):
        await self.send("LEFT")
        await self.wait_state((1, 1, 0.25, 0))
        await self.link.close()
        await self.wait_state((0, 0, 0, 0))
        self.link = await asyncio.wait_for(self.links.get(), 2)
        await self.send("RIGHT")
        await self.wait_state((1, 1, 0, 0.25))


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "gx10"))
try:
    from ingest.fake_phone import walk_frames
    from ingest.server import Pipeline, Server
except ImportError:
    Pipeline = None


@unittest.skipUnless(Device and Pipeline, "GX10 requirements and mock GPIO are required")
class FullFlow(unittest.IsolatedAsyncioTestCase):
    async def test_phone_depth_to_gx10_websocket_to_pi_motor_and_timeout(self):
        Device.pin_factory = pins = MockFactory(pin_class=MockPWMPin)
        hw = GpioHardware(read_switches=False)
        stop, inbox = threading.Event(), cane.Inbox()
        lines = []
        with patch("vlm.warm", return_value="stubbed"), patch.object(cane, "log", side_effect=lines.append):
            server = Server(Pipeline(False))
            worker = asyncio.create_task(server.run_frames())
            thread = threading.Thread(target=cane.control_loop, args=(hw, inbox, stop, 0.25, True, 120))
            thread.start()
            listener = None
            seen = set()
            try:
                async with websockets.serve(server.phone, "127.0.0.1", 0) as phone_server, \
                        websockets.serve(server.pi, "127.0.0.1", 0) as pi_server:
                    phone_port = phone_server.sockets[0].getsockname()[1]
                    pi_port = pi_server.sockets[0].getsockname()[1]
                    listener = asyncio.create_task(cane.listen_gx10(f"ws://127.0.0.1:{pi_port}", inbox, stop))
                    deadline = time.monotonic() + 2
                    while not server.pis and time.monotonic() < deadline:
                        await asyncio.sleep(0.01)
                    self.assertEqual(len(server.pis), 1)
                    async with websockets.connect(f"ws://127.0.0.1:{phone_port}") as phone:
                        for raw, _distance in walk_frames():
                            await phone.send(raw)
                            await asyncio.wait_for(phone.recv(), 2)
                            seen.add(server.pipe.status["cmd"])
                            await asyncio.sleep(1 / 15)
                        self.assertIn("CENTER", seen)
                        turns = seen & {"LEFT", "RIGHT"}  # the obstacle check steers one way before it stops
                        self.assertTrue(turns)
                        self.assertEqual(server.pipe.status["cmd"], "STOP")
                        self.assertTrue(any(f"wheel {turn}" in line for turn in turns for line in lines))
                        await asyncio.sleep(0.45)
                        self.assertTrue(all(pins.pin(n).state == 0 for n in (PIN_R_EN, PIN_L_EN, PIN_RPWM, PIN_LPWM)))
                    stop.set()
            finally:
                stop.set()
                if listener is not None:
                    await asyncio.wait_for(listener, 3)
                thread.join(2)
                worker.cancel()
                try:
                    await worker
                except asyncio.CancelledError:
                    pass
                server.worker.shutdown(wait=True)
                server.writer.shutdown(wait=True)
            self.assertFalse(thread.is_alive())

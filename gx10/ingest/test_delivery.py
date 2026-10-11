"""Frame age and slow peers, without a model, phone or motor."""

import asyncio
import json
import time
import unittest

from .server import Server, TTL_MS


class Peer:
    def __init__(self, delay=0):
        self.delay = delay
        self.messages = []
        self.closed = False

    async def send(self, message):
        await asyncio.sleep(self.delay)
        self.messages.append((json.loads(message), time.monotonic()))

    async def close(self):
        self.closed = True


class Pipe:
    def __init__(self, delay=0):
        self.delay = delay
        self.calls = 0

    def process(self, raw, received):
        self.calls += 1
        time.sleep(self.delay)
        return [], json.dumps({"seq": 1, "cmd": "LEFT", "ttl_ms": TTL_MS})


class Delivery(unittest.IsolatedAsyncioTestCase):
    async def run_frame(self, pipe, age=0, duration=0.1):
        server = Server(pipe)
        peer = Peer()
        server.pis.add(peer)
        server.latest = (b"fake frame", time.monotonic() - age, peer)
        server.new_frame.set()
        task = asyncio.create_task(server.run_frames())
        try:
            await asyncio.sleep(duration)
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            server.worker.shutdown(wait=True)
            server.writer.shutdown(wait=True)
        return server, peer

    async def test_fresh_frame_has_only_remaining_ttl(self):
        server, peer = await self.run_frame(Pipe(0.05), duration=0.15)
        self.assertEqual(len(peer.messages), 1)
        command, _ = peer.messages[0]
        self.assertEqual(command["cmd"], "LEFT")
        self.assertGreater(command["ttl_ms"], 200)
        self.assertLess(command["ttl_ms"], 355)
        self.assertEqual(server.expired, 0)

    async def test_processing_over_budget_sends_no_motor_command(self):
        server, peer = await self.run_frame(Pipe(0.45), duration=0.6)
        self.assertEqual(peer.messages, [])
        self.assertEqual(server.expired, 1)

    async def test_already_expired_frame_is_not_processed(self):
        pipe = Pipe()
        server, peer = await self.run_frame(pipe, age=0.5)
        self.assertEqual(pipe.calls, 0)
        self.assertEqual(peer.messages, [])
        self.assertEqual(server.expired, 1)

    async def test_slow_peer_does_not_hold_up_fast_peer(self):
        server = Server(Pipe())
        slow, fast = Peer(0.5), Peer()
        server.pis.update((slow, fast))
        start = time.monotonic()
        message = json.dumps({"cmd": "RIGHT", "ttl_ms": TTL_MS})
        try:
            await asyncio.gather(server._send_pi(slow, message, start),
                                 server._send_pi(fast, message, start))
            self.assertLess(fast.messages[0][1] - start, 0.1)
            self.assertEqual(slow.messages, [])
            self.assertTrue(slow.closed)
            self.assertNotIn(slow, server.pis)
        finally:
            server.worker.shutdown(wait=True)
            server.writer.shutdown(wait=True)

    async def test_expired_delivery_does_not_send(self):
        server = Server(Pipe())
        peer = Peer()
        try:
            await server._send_pi(peer, '{"cmd":"LEFT","ttl_ms":400}', time.monotonic() - 1)
            self.assertEqual(peer.messages, [])
        finally:
            server.worker.shutdown(wait=True)
            server.writer.shutdown(wait=True)

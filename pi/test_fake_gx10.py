"""python3 -m unittest test_fake_gx10 -v   (from this folder; any computer with websockets)

The fake GX10 has to read what the Pi sends as well as send commands. When it did
not, the Pi's health reports filled the link and it dropped every 38 seconds.
"""

import asyncio
import json
import unittest

try:
    import websockets

    import fake_gx10
except ImportError:
    websockets = None


@unittest.skipUnless(websockets, "websockets is required")
class Reads(unittest.IsolatedAsyncioTestCase):
    async def test_the_link_stays_answered_while_the_pi_keeps_sending(self):
        async with websockets.serve(fake_gx10.feed, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            async with websockets.connect(f"ws://127.0.0.1:{port}") as pi:
                first = json.loads(await asyncio.wait_for(pi.recv(), 2))
                self.assertEqual(first["cmd"], "CENTER")
                for n in range(60):  # 2 minutes of health reports at once
                    await pi.send(json.dumps({"health": {"uptime_s": n}}))
                await pi.send(json.dumps({"button": "down"}))
                await asyncio.sleep(0.3)
                pong = await pi.ping()
                await asyncio.wait_for(pong, 2)  # times out if the fake has stopped reading
                self.assertEqual(json.loads(await asyncio.wait_for(pi.recv(), 2))["ttl_ms"], 400)


if __name__ == "__main__":
    unittest.main()

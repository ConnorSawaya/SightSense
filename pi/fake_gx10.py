"""Stands in for the GX10's command port, so the Pi can be tested without it.

    python3 fake_gx10.py

Type left, center, right, stop or free. The last one typed is sent 15 times a
second, in the format from ../contracts/MESSAGES.md. Type silence to stop
sending while keeping the link open, and quit to finish.
"""

import argparse
import asyncio
import json
import sys
import threading

import websockets

RATE_HZ = 15
WORDS = {
    "L": "LEFT", "C": "CENTER", "R": "RIGHT", "S": "STOP", "F": "FREE",
    "CENTRE": "CENTER",
}
current = {"cmd": "CENTER"}  # None while silent


async def feed(link):
    print("Pi connected", flush=True)
    seq = 0
    try:
        while True:
            if current["cmd"]:
                seq += 1
                await link.send(json.dumps({"seq": seq, "cmd": current["cmd"], "ttl_ms": 400}))
            await asyncio.sleep(1 / RATE_HZ)
    except websockets.ConnectionClosed:
        print("Pi disconnected", flush=True)


async def serve(host, port):
    done = asyncio.get_running_loop().create_future()

    def keyboard():
        for line in sys.stdin:
            word = line.strip().upper()
            word = WORDS.get(word, word)
            if word == "QUIT":
                break
            if word:
                current["cmd"] = None if word == "SILENCE" else word
        done.get_loop().call_soon_threadsafe(done.set_result, None)

    async with websockets.serve(feed, host, port):
        print(f"Fake GX10 on port {port}. Sending CENTER until you type something.", flush=True)
        threading.Thread(target=keyboard, daemon=True).start()
        await done


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fake GX10 command port")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    asyncio.run(serve(args.host, args.port))

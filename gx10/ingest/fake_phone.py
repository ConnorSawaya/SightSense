"""Stand in for the phone (and the Pi) to test the frame service end to end.

    ../../venv-yolo/bin/python -m ingest.fake_phone --port 8775 --pi-port 8776           # walk at a wall
    ../../venv-yolo/bin/python -m ingest.fake_phone --port 8775 --replay ../../recordings/20261010-170000

Walk: the camera walks at 0.5 m/s toward a wall 4 m away; the service should
turn to STOP before the wall. Also connects as the Pi and prints its commands.
Replay: sends recorded frame messages in order at 15 per second.
"""

import argparse
import asyncio
import json
import time
from pathlib import Path

from websockets.asyncio.client import connect

from navigator import encode, fake
from planner.fake_scene import render

WALL = ((-3, 0, -4.2), (3, 2.5, -4.0))
PICTURE = Path(__file__).parent.parent / "vlm" / "test_images" / "empty_room.jpg"


def walk_frames(seconds=8.0, speed=0.5):
    jpeg = PICTURE.read_bytes() if PICTURE.exists() else b""
    for i in range(int(seconds * 15)):
        z = -speed * i / 15
        p = fake.pose(z=z, pitch_deg=-25, height=0.9)
        f = render(p, [WALL], jpeg=jpeg, seq=i + 1, t=i / 15)
        yield encode(f), 4.0 + z  # message, true distance to the wall


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--pi-port", type=int, default=0, help="also act as the Pi on this port")
    ap.add_argument("--replay", help="folder of recorded .bin frame messages")
    ap.add_argument("--say", action="append", default=[], help="voice text to send at the start")
    a = ap.parse_args()

    pi_cmds = []

    async def pi():
        async with connect(f"ws://{a.host}:{a.pi_port}") as ws:
            async for m in ws:
                pi_cmds.append((time.monotonic(), json.loads(m)))

    if a.pi_port:
        asyncio.create_task(pi())
        await asyncio.sleep(0.3)

    async with connect(f"ws://{a.host}:{a.port}", max_size=8 << 20) as ws:
        replies = []

        async def listen():
            async for m in ws:
                replies.append((time.monotonic(), json.loads(m)))

        asyncio.create_task(listen())
        for text in a.say:
            await ws.send(json.dumps({"text": text}))

        if a.replay:
            frames = [(p.read_bytes(), None) for p in sorted(Path(a.replay).glob("*.bin"))]
        else:
            frames = list(walk_frames())
        t0 = time.monotonic()
        sent = {}
        for i, (msg, wall_m) in enumerate(frames):
            await asyncio.sleep(max(0, t0 + i / 15 - time.monotonic()))
            sent[i + 1] = (time.monotonic(), wall_m)
            await ws.send(msg)
        await asyncio.sleep(1.0)

    last = None
    first_stop = None
    delays = []
    for t, r in replies:
        if "seq" in r and r["seq"] in sent:
            delays.append((t - sent[r["seq"]][0]) * 1000)
        key = (r.get("state"), r.get("speech"), r.get("lookup"))
        if key != last:
            wall = sent.get(r.get("seq"), (0, None))[1]
            print(f"  seq {r.get('seq')!s:>4}  {r.get('state') or '':9s} earcon {r.get('earcon')!s:7s} "
                  f"speech {r.get('speech')!r}" + (f"  lookup {r['lookup']!r}" if r.get("lookup") else "")
                  + (f"  (wall {wall:.2f} m)" if wall is not None else ""))
            last = key
        if r.get("state") == "STOP" and first_stop is None:
            first_stop = r
    print(f"\n{len(frames)} frames sent, {sum(1 for _, r in replies if 'state' in r)} guidance replies")
    if delays:
        delays.sort()
        print(f"send -> guidance back: median {delays[len(delays) // 2]:.0f} ms, max {delays[-1]:.0f} ms (local, includes processing)")
    if pi_cmds:
        cmds = [c["cmd"] for _, c in pi_cmds]
        changes = [cmds[0]] + [c for prev, c in zip(cmds, cmds[1:]) if c != prev]
        print(f"pi got {len(cmds)} commands: {' -> '.join(changes)}")


if __name__ == "__main__":
    asyncio.run(main())

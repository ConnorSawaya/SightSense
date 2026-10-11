"""Ask the running frame service a few things, as a stand-in phone, and print what comes back and how fast.

    python -m ingest.check_live_gx10                      (from gx10/; the GX10's Tailscale address)
    python -m ingest.check_live_gx10 127.0.0.1            (on the GX10 itself)
    python -m ingest.check_live_gx10 127.0.0.1 "what can you do" "say that again"

It uses the real vision-language model, so it shows describe, read and questions working end to end.
Only frames that make the obstacle check say STOP are sent (a wall 0.2 m ahead), so a Pi on the same
service would get nothing but STOP. It sends nothing at all if a phone or a Pi is connected.
The picture is drawn: the word EXIT on green, and a red circle. Needs the service on phone port 8775.
"""
import asyncio
import json
import sys
import time
import urllib.request

import cv2
import numpy as np
from websockets.asyncio.client import connect

from navigator import encode, fake
from planner.fake_scene import arrays, render
from planner.obstacle import check

HOST = sys.argv[1] if len(sys.argv) > 1 else "100.108.5.67"
PHONE_PORT, DASH_PORT = 8775, 8000
WALL = ((-3, 0, -0.45), (3, 2.5, -0.2))  # so close that the check reads it as right up against something


def picture():
    img = np.full((480, 640, 3), 235, np.uint8)
    cv2.rectangle(img, (150, 60), (490, 210), (60, 150, 40), -1)
    cv2.putText(img, "EXIT", (185, 175), cv2.FONT_HERSHEY_SIMPLEX, 3.6, (255, 255, 255), 10)
    cv2.circle(img, (320, 350), 80, (40, 40, 220), -1)
    ok, data = cv2.imencode(".jpg", img)
    assert ok
    return data.tobytes()


def status():
    with urllib.request.urlopen(f"http://{HOST}:{DASH_PORT}/status", timeout=4) as r:
        return json.loads(r.read())


def frame(seq, jpeg):
    return render(fake.pose(pitch_deg=-25, height=0.9), [WALL], jpeg=jpeg, seq=seq, t=time.time())


async def main():
    jpeg = picture()
    probe = frame(1, jpeg)
    d, c = arrays(probe)
    local = check(d, c, probe.fx, probe.fy, probe.cx, probe.cy, probe.pose)
    print("the test frame, checked here first: command", local.raw_cmd, "ahead", local.clearance.get(0))
    if local.raw_cmd != "STOP":
        print("not sending: the test frame must read STOP")
        return
    s = status()
    print("GX10 before:", {k: s.get(k) for k in ("phone", "pis", "fps", "model")})
    if s.get("phone") or s.get("pis"):
        print("not sending: a phone or a Pi is connected to the service")
        return

    got, seq = [], [1]
    async with connect(f"ws://{HOST}:{PHONE_PORT}", max_size=8 << 20, open_timeout=6) as ws:
        async def listen():
            async for m in ws:
                got.append((time.monotonic(), json.loads(m)))

        listener = asyncio.create_task(listen())

        async def frames(seconds, until=None):
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                seq[0] += 1
                await ws.send(encode(frame(seq[0], jpeg)))
                await asyncio.sleep(0.2)
                if until and until():
                    return

        await frames(2.0)
        states = sorted({m.get("state") for _, m in got if "state" in m})
        print("guidance states for the STOP-only frames:", states, "| replies so far:", len(got))
        questions = [(q, 10) for q in sys.argv[2:]] or [("what's in front of me", 10), ("read the sign", 10), ("is the path clear", 4), ("what can you do", 6)]
        for text, wait in questions:
            mark, t0 = len(got), time.monotonic()
            await ws.send(json.dumps({"text": text}))

            def answered():
                return any(m.get("speech") and "Obstacle ahead" not in m["speech"] and "Path blocked" not in m["speech"] for _, m in got[mark:])

            await frames(wait, answered)
            said = [(round(t - t0, 2), m["speech"]) for t, m in got[mark:] if m.get("speech")]
            print(f"you: {text!r}")
            for dt, speech in said:
                print(f"   after {dt:5.2f} s the GX10 says: {speech!r}")
            if not said:
                print("   no answer within", wait, "s")
        listener.cancel()
    await asyncio.sleep(0.5)
    s = status()
    print("GX10 after:", {k: s.get(k) for k in ("phone", "pis", "fps")})
    print("commands a Pi would have got:", sorted({m.get("state") for _, m in got if "state" in m}))


asyncio.run(main())

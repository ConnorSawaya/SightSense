#!/usr/bin/env python3
"""Fake GX10 for testing the iPhone app without the real frame service.

Listens like the GX10 on port 8765, checks every frame message against
contracts/MESSAGES.md, prints one line a second, and sends a guidance message
every 2 seconds so the app's receive side gets exercised. Standard library only.

    python3 tools/fake_gx10.py                     # then connect the app to <this laptop's IP>
    python3 tools/fake_gx10.py --save /tmp/frames  # also keep the newest picture, depth and header
    python3 tools/fake_gx10.py --frames 30         # exit after 30 frames; exit code 1 if any was bad

Depth is saved as an 8-bit PGM, 0 m black to 5 m white, missing readings black.
"""

import argparse
import base64
import hashlib
import json
import os
import socket
import socketserver
import struct
import sys
import threading
import time

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
GUIDANCE = [
    {"state": "CLEAR"},
    {"state": "CAUTION", "earcon": "caution"},
    {"state": "STOP", "earcon": "stop", "speech": "Obstacle ahead. Stop."},
    {"state": "UNCERTAIN"},
]
REQUIRED = ["seq", "t_capture", "jpeg_len", "depth_len", "conf_len", "rgb_w", "rgb_h", "depth_w", "depth_h",
            "fx", "fy", "cx", "cy", "pose", "tracking", "lat", "lon", "gps_acc_m", "heading_deg", "thermal"]


# ---------------------------------------------------------------- frame message


def parse_frame(msg: bytes):
    """Split a frame message into (header, jpeg, depth, conf). Raises ValueError on any contract break."""
    if len(msg) < 4:
        raise ValueError("shorter than the 4-byte header length")
    hlen = struct.unpack("<I", msg[:4])[0]
    if hlen > len(msg) - 4:
        raise ValueError(f"header length {hlen} past end of message")
    header = json.loads(msg[4 : 4 + hlen])
    missing = [k for k in REQUIRED if k not in header]
    if missing:
        raise ValueError(f"header missing {missing}")
    a = 4 + hlen
    b = a + header["jpeg_len"]
    c = b + header["depth_len"]
    d = c + header["conf_len"]
    if d != len(msg):
        raise ValueError(f"lengths add to {d} bytes, message is {len(msg)}")
    w, h = header["depth_w"], header["depth_h"]
    if header["depth_len"] != w * h * 2:
        raise ValueError(f"depth_len {header['depth_len']} != {w}x{h}x2")
    if header["conf_len"] != w * h:
        raise ValueError(f"conf_len {header['conf_len']} != {w}x{h}")
    jpeg, depth, conf = msg[a:b], msg[b:c], msg[c:d]
    if jpeg[:2] != b"\xff\xd8":
        raise ValueError("picture is not a JPEG")
    if len(header["pose"]) != 16:
        raise ValueError("pose is not 16 numbers")
    if header["tracking"] not in ("normal", "limited", "relocalizing", "notAvailable"):
        raise ValueError(f"unknown tracking {header['tracking']!r}")
    if max(conf, default=0) > 2:
        raise ValueError("confidence value above 2")
    if not (0 < header["cx"] < w and 0 < header["cy"] < h):
        raise ValueError(f"cx, cy ({header['cx']:.1f}, {header['cy']:.1f}) not inside the {w}x{h} depth picture")
    return header, jpeg, depth, conf


def depth_summary(header, depth, conf):
    w, h = header["depth_w"], header["depth_h"]
    mm = struct.unpack(f"<{w * h}H", depth)
    good = [z for z, c in zip(mm, conf) if z and c >= 1]
    centre = sorted(mm[y * w + x] for y in range(h // 2 - 4, h // 2 + 4) for x in range(w // 2 - 4, w // 2 + 4) if mm[y * w + x])
    mid = f"{centre[len(centre) // 2] / 1000:.2f} m" if centre else "none"
    counts = [conf.count(i) for i in range(3)]
    return f"good depth {100 * len(good) / (w * h):.0f}%, centre {mid}, conf low/med/high {counts}"


def save(folder, header, jpeg, depth):
    os.makedirs(folder, exist_ok=True)
    w, h = header["depth_w"], header["depth_h"]
    mm = struct.unpack(f"<{w * h}H", depth)
    grey = bytes(min(255, z * 255 // 5000) for z in mm)
    with open(os.path.join(folder, "latest.jpg"), "wb") as f:
        f.write(jpeg)
    with open(os.path.join(folder, "latest_depth.pgm"), "wb") as f:
        f.write(b"P5 %d %d 255\n" % (w, h) + grey)
    with open(os.path.join(folder, "latest_header.json"), "w") as f:
        json.dump(header, f, indent=2)


# ---------------------------------------------------------------- WebSocket (RFC 6455, server side)


def unmask(data: bytes, key: bytes) -> bytes:
    n = len(data)
    k = (key * (n // 4 + 1))[:n]
    return (int.from_bytes(data, "little") ^ int.from_bytes(k, "little")).to_bytes(n, "little")


def frame_bytes(opcode: int, payload: bytes, mask: bool = False) -> bytes:
    n = len(payload)
    head = bytes([0x80 | opcode])
    m = 0x80 if mask else 0
    if n < 126:
        head += bytes([m | n])
    elif n < 1 << 16:
        head += bytes([m | 126]) + struct.pack(">H", n)
    else:
        head += bytes([m | 127]) + struct.pack(">Q", n)
    if mask:
        key = os.urandom(4)
        return head + key + unmask(payload, key)
    return head + payload


def read_exact(rfile, n):
    data = rfile.read(n)
    if len(data) != n:
        raise ConnectionError("connection closed")
    return data


def read_message(rfile):
    """Returns (opcode, payload) for one whole message; control frames come back as they arrive."""
    parts, first_op = [], None
    while True:
        b0, b1 = read_exact(rfile, 2)
        fin, op = b0 & 0x80, b0 & 0x0F
        n = b1 & 0x7F
        if n == 126:
            n = struct.unpack(">H", read_exact(rfile, 2))[0]
        elif n == 127:
            n = struct.unpack(">Q", read_exact(rfile, 8))[0]
        key = read_exact(rfile, 4) if b1 & 0x80 else None
        payload = read_exact(rfile, n)
        if key:
            payload = unmask(payload, key)
        if op >= 8:
            return op, payload
        if op:
            first_op = op
        parts.append(payload)
        if fin:
            return first_op, b"".join(parts)


class Handler(socketserver.StreamRequestHandler):
    def setup(self):
        super().setup()
        self.request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.send_lock = threading.Lock()
        self.alive = True

    def send(self, opcode, payload):
        with self.send_lock:
            self.wfile.write(frame_bytes(opcode, payload))
            self.wfile.flush()

    def handshake(self):
        lines = []
        while True:
            line = self.rfile.readline()
            if not line or line in (b"\r\n", b"\n"):
                break
            lines.append(line.decode("latin-1").strip())
        headers = {k.strip().lower(): v.strip() for k, _, v in (l.partition(":") for l in lines[1:])}
        key = headers.get("sec-websocket-key")
        if not key:
            self.wfile.write(b"HTTP/1.1 400 Bad Request\r\n\r\nWebSocket only\n")
            return False
        accept = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
        self.wfile.write(
            ("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
             f"Sec-WebSocket-Accept: {accept}\r\n\r\n").encode()
        )
        self.wfile.flush()
        return True

    def guidance_loop(self):
        i = 0
        while self.alive:
            time.sleep(2)
            if not self.alive or self.server.no_guidance:
                continue
            g = dict(GUIDANCE[i % len(GUIDANCE)], seq=self.last_seq)
            try:
                self.send(0x1, json.dumps(g).encode())
            except OSError:
                return
            i += 1

    def handle(self):
        if not self.handshake():
            return
        peer = self.client_address[0]
        log(f"connected: {peer}")
        self.last_seq = 0
        threading.Thread(target=self.guidance_loop, daemon=True).start()
        st = self.server.stats
        window_start, window_frames, window_bytes = time.monotonic(), 0, 0
        try:
            while True:
                op, payload = read_message(self.rfile)
                if op == 0x8:
                    self.send(0x8, payload[:2])
                    break
                if op == 0x9:
                    self.send(0xA, payload)
                    continue
                if op == 0x1:
                    log(f"text from phone: {payload.decode(errors='replace')}")
                    continue
                if op != 0x2:
                    continue
                st["frames"] += 1
                try:
                    header, jpeg, depth, conf = parse_frame(payload)
                except (ValueError, KeyError, TypeError, json.JSONDecodeError, struct.error) as e:
                    st["bad"] += 1
                    log(f"BAD FRAME: {e}")
                    continue
                seq = header["seq"]
                if self.last_seq and seq != self.last_seq + 1:
                    st["gaps"] += 1
                self.last_seq = seq
                window_frames += 1
                window_bytes += len(payload)
                now = time.monotonic()
                if now - window_start >= 1:
                    dt = now - window_start
                    log(f"{window_frames / dt:4.1f} frames/s  {window_bytes / dt / 1e6:.2f} MB/s  seq {seq}  "
                        f"rgb {header['rgb_w']}x{header['rgb_h']} ({len(jpeg) // 1024} KB)  "
                        f"depth {header['depth_w']}x{header['depth_h']}  fx {header['fx']:.1f} cx {header['cx']:.1f} "
                        f"cy {header['cy']:.1f}  tracking {header['tracking']}  {depth_summary(header, depth, conf)}")
                    window_start, window_frames, window_bytes = now, 0, 0
                    if self.server.save_dir:
                        save(self.server.save_dir, header, jpeg, depth)
                if self.server.stop_after and st["frames"] >= self.server.stop_after:
                    self.send(0x8, struct.pack(">H", 1000))
                    self.server.done.set()
                    break
        except (ConnectionError, OSError) as e:
            log(f"disconnected: {peer} ({e})")
        finally:
            self.alive = False
        log(f"closed: {peer}  frames {st['frames']}, bad {st['bad']}, sequence gaps {st['gaps']}")


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def log(text):
    print(time.strftime("%H:%M:%S"), text, flush=True)


def local_addresses():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.8.1", 9))  # no packet is sent; this only picks the outgoing interface
        return s.getsockname()[0]
    except OSError:
        return "this computer's IP"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--save", metavar="DIR", help="keep the newest picture, depth and header here")
    p.add_argument("--frames", type=int, default=0, help="exit after this many frames")
    p.add_argument("--no-guidance", action="store_true", help="do not send guidance messages")
    args = p.parse_args()

    server = Server(("0.0.0.0", args.port), Handler)
    server.stats = {"frames": 0, "bad": 0, "gaps": 0}
    server.save_dir = args.save
    server.stop_after = args.frames
    server.no_guidance = args.no_guidance
    server.done = threading.Event()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log(f"fake GX10 listening on port {args.port}; in the app enter {local_addresses()}:{args.port}")
    try:
        server.done.wait()
        time.sleep(0.3)
    except KeyboardInterrupt:
        pass
    server.shutdown()
    st = server.stats
    log(f"total frames {st['frames']}, bad {st['bad']}, sequence gaps {st['gaps']}")
    sys.exit(1 if st["bad"] else 0)


if __name__ == "__main__":
    main()

#!/bin/sh
# Builds the app's link and frame code for the Mac and runs it against the fake GX10.
# Run from ios-app/. Needs Xcode (swiftc) and python3; nothing to install.
set -e
cd "$(dirname "$0")/.."
PORT=${PORT:-18765}
OUT=$(mktemp -d)
trap 'kill $FAKE 2>/dev/null; rm -rf "$OUT"' EXIT

swiftc -O -o "$OUT/link-test" SightSense/GX10Link.swift SightSense/FrameMessage.swift tools/LinkTest/main.swift

echo "== frames and guidance"
python3 tools/fake_gx10.py --port "$PORT" --frames 60 --save "$OUT/frames" > "$OUT/fake.log" 2>&1 &
FAKE=$!
sleep 0.5
"$OUT/link-test" "ws://127.0.0.1:$PORT" 60
wait $FAKE && echo "ok    fake GX10 found no bad frames" || { echo "FAIL  fake GX10 reported bad frames"; cat "$OUT/fake.log"; exit 1; }
grep -q 'text from phone: {"text": "guide me to the apple"}' "$OUT/fake.log" && echo "ok    fake GX10 got the voice command" || { echo "FAIL  voice command not received"; exit 1; }
tail -n 3 "$OUT/fake.log"
python3 - "$OUT/frames" <<'EOF'
import json, sys
h = json.load(open(sys.argv[1] + "/latest_header.json"))
print("ok    saved header: seq", h["seq"], "depth", h["depth_w"], "x", h["depth_h"])
EOF

echo "== reconnect"
python3 tools/fake_gx10.py --port "$PORT" --frames 30 > "$OUT/fake2.log" 2>&1 &
FAKE=$!
sleep 0.5
( while kill -0 $FAKE 2>/dev/null; do sleep 0.2; done; sleep 2; python3 tools/fake_gx10.py --port "$PORT" > "$OUT/fake3.log" 2>&1 ) &
"$OUT/link-test" "ws://127.0.0.1:$PORT" 30 reconnect
pkill -f "fake_gx10.py --port $PORT" 2>/dev/null || true

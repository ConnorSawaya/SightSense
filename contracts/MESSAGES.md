# Message formats

The agreed messages between the iPhone, the GX10 and the Raspberry Pi. Everyone builds against these, so tell the whole team before changing anything here.

All links are WebSockets on the team's private router.

## Addresses

Reserve these in the router. The subnet depends on the router.

| Device | Address | Ports |
| --- | --- | --- |
| GX10 | 192.168.8.10 | 8765 frames in · 8766 commands out · 8000 dashboard · 11434 Ollama |
| Raspberry Pi | 192.168.8.20 | connects out to the GX10 |
| iPhone | 192.168.8.30 | connects out to the GX10 |

## Frame: iPhone → GX10 (port 8765, binary, ~15 per second)

One message per camera frame, laid out as:

1. 4 bytes: header length, little-endian unsigned integer
2. Header: JSON text
3. JPEG bytes
4. Depth bytes: 16-bit unsigned, millimetres, little-endian, row by row
5. Confidence bytes: one per pixel (0 low, 1 medium, 2 high)

```json
{
  "seq": 412,
  "t_capture": 10532.118,
  "jpeg_len": 48211,
  "depth_len": 98304,
  "conf_len": 49152,
  "rgb_w": 640,
  "rgb_h": 480,
  "depth_w": 256,
  "depth_h": 192,
  "fx": 212.4,
  "fy": 212.4,
  "cx": 127.6,
  "cy": 95.8,
  "pose": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
  "tracking": "normal",
  "lat": 37.38,
  "lon": -121.98,
  "gps_acc_m": 8.0,
  "heading_deg": 271.0,
  "thermal": "nominal"
}
```

- `fx, fy, cx, cy` are scaled to the depth picture's size.
- `pose` is the camera-to-world transform, 16 numbers, column by column, in metres.
- `depth_w` and `depth_h` are read from the real buffer, not assumed.
- `lat`, `lon`, `gps_acc_m` and `heading_deg` may be `null` when unavailable.

## Command: GX10 → Pi (port 8766, text, every frame)

```json
{"seq": 412, "cmd": "LEFT", "ttl_ms": 400}
```

`cmd` is one of `LEFT`, `CENTER`, `RIGHT`, `STOP`, `FREE`. It is sent every frame, so it also acts as the heartbeat. The Pi switches the motor off if nothing arrives for `ttl_ms`.

## Guidance: GX10 → iPhone (text)

```json
{"seq": 412, "state": "CAUTION", "direction": "LEFT", "earcon": "left", "speech": "Bear left"}
```

`state` is one of `CLEAR`, `CAUTION`, `STOP`, `UNCERTAIN`, `NO_DATA`. `direction` (added October 11) is one of `LEFT`, `STRAIGHT`, `RIGHT`, `STOP`, `UNKNOWN`: which way to go, the same as the wheel. `direction`, `earcon` and `speech` are optional. `earcon` is one of `stop`, `left`, `right`, `unknown` (`caution` from older GX10 code); it comes only when something changes, not with every frame, so the phone plays it every time it arrives. `left` and `right` are meant to be heard in that ear.

## Voice: iPhone → GX10 (text)

```json
{"text": "guide me to the apple"}
```

## Place lookup: GX10 → iPhone (text)

```json
{"lookup": "Safeway"}
```

## Route: iPhone → GX10 (text)

```json
{
  "dest": "Safeway",
  "distance_m": 950,
  "eta_min": 12,
  "polyline": [[37.3801, -121.9802], [37.3805, -121.9810]],
  "steps": [{"lat": 37.3805, "lon": -121.9810, "text": "Turn left onto Bowers Ave"}]
}
```

# iPhone app

Captures the camera picture, LiDAR depth and position with ARKit and sends them to the GX10. Also plays beeps and speech, takes voice commands, and looks up walking routes.

Open `SightSense.xcodeproj` in Xcode. No packages to install.

## Run it

1. In Xcode, pick the SightSense target → Signing & Capabilities → choose your team. With a free Apple ID, change the bundle identifier if `com.sightsense.capture` is taken.
2. Plug in the iPhone, pick it as the destination, Run.
3. Enter the GX10 address (`192.168.8.10`) and tap Connect. `host:port` also works.

Command line build, without opening Xcode:

```bash
xcodebuild -project SightSense.xcodeproj -scheme SightSense -destination 'generic/platform=iOS' \
  DEVELOPMENT_TEAM=<your team ID> -allowProvisioningUpdates build
```

## Test without the GX10

`tools/fake_gx10.py` stands in for the GX10's frame receiver on port 8765. It checks every frame against [`../contracts/MESSAGES.md`](../contracts/MESSAGES.md), prints rate, sizes and depth numbers once a second, and sends a guidance message every 2 seconds. Standard library only.

```bash
python3 tools/fake_gx10.py --save /tmp/frames   # then connect the app to <laptop IP>:8765
./tools/run_link_test.sh                         # the app's link and frame code on the Mac, against the fake
```

`run_link_test.sh` builds `GX10Link.swift` and `FrameMessage.swift` for the Mac and checks depth conversion, row padding, intrinsics scaling, the message layout, 15 frames a second, guidance received, a voice command sent, and reconnecting after the GX10 drops.

In the Simulator there is no camera or LiDAR: Connect opens the link without sending frames, so guidance, speech and voice can still be tried. Launch with `-autoconnect host:port` to connect straight away.

## Files

| File | What it does |
| --- | --- |
| `Capture.swift` | ARKit session, link and location; what the screen shows |
| `FrameSender.swift` | Picks about 15 frames a second; skips a frame if the last one is still going |
| `FrameEncoder.swift` | ARKit frame → frame message (640-wide JPEG, depth, confidence, scaled intrinsics, pose) |
| `FrameMessage.swift` | The message layout and depth conversion, without ARKit, so it runs on a Mac |
| `GX10Link.swift` | WebSocket to port 8765, reconnects every second until disconnected |
| `Guidance.swift` | Parses guidance; beeps (at most once a second) and speaks (same sentence at most every 4 s) |
| `Voice.swift` | Hold-to-talk, on-device speech recognition; sends `{"text": ...}` |
| `Location.swift` | GPS and compass heading for the frame header |

## Build order

Steps 1–7 are written. Step 8 is not started.

1. App shell: GX10 address field, Connect button, status line, screen kept awake.
2. ARKit session with scene depth on; show the tracking state.
3. WebSocket to `ws://<GX10>:8765` with automatic reconnect.
4. Send the frame message from [`../contracts/MESSAGES.md`](../contracts/MESSAGES.md) about 15 times a second.
5. Receive guidance: beep on STOP, speak the `speech` text.
6. Push-to-talk with on-device speech recognition; send `{"text": "..."}`.
7. Location and compass heading in every frame header.
8. Place lookup with MapKit walking directions; send the route message.

Step 4 is the one everything else depends on.

## Watch out for

- ARKit's picture and depth are in the sensor's landscape direction. If the phone is mounted upright, the data arrives turned 90 degrees.
- Skip a frame if the previous send has not finished. Never queue frames.
- Scale the camera intrinsics to the depth picture's size.
- Info.plist needs usage descriptions for the camera, microphone, speech recognition, location and local network, plus `NSAllowsLocalNetworking`.

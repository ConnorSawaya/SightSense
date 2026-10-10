# iPhone app

Captures the camera picture, LiDAR depth and position with ARKit and sends them to the GX10. Also plays beeps and speech, takes voice commands, and looks up walking routes.

Put the Xcode project in this folder.

## Build order

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

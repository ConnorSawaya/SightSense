# dashboard

Web page on port 8000, started by `ingest/server.py`. Open `http://<GX10 address>:8000` from any laptop on the same network (or over Tailscale).

- Live phone picture, turned upright, with YOLO boxes; LiDAR depth (red near, blue far, grey no good reading).
- The command sent to the Pi, the guidance state, and clearance for each of the seven headings (grey = unknown, counted as blocked).
- A text box that does the same as a voice command ("guide me to the apple", "yes", "stop").
- Frames per second, GX10 processing time, network round trip (WebSocket ping every 2 s), the 2-frame stop smoothing, frames dropped, GPU use, power and temperature (`nvidia-smi`), the vision model, ARKit tracking and phone heat.

Pictures are drawn only when the page asks for them, about 3 times a second, not for every frame. The phone's own capture-to-send time is not measured yet, so the delays shown are only the GX10 and network part.

`--dashboard-port 0` turns it off.

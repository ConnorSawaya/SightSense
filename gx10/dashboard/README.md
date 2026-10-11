# dashboard

Web page on port 8000, started by `ingest/server.py`. Open `http://<GX10 address>:8000` from any laptop on the same network (or over Tailscale).

- Live phone picture, turned upright, with YOLO boxes; LiDAR depth (red near, blue far, grey no good reading).
- The command sent to the Pi, the guidance state, and clearance for each of the seven headings (grey = unknown, counted as blocked).
- A text box that does the same as a voice command ("guide me to the apple", "yes", "stop").
- Frames per second, GX10 processing time, network round trip (WebSocket ping every 2 s), the 2-frame stop smoothing, frames dropped, GPU use, power and temperature (`nvidia-smi`), the vision model, ARKit tracking and phone heat.

Built to stay live over Tailscale, where a single request took 0.3-1 s:

- `/stream.mjpg`: picture and depth side by side as one MJPEG stream on one connection, up to 8 frames a second. Each viewer always gets the newest frame; a slow viewer skips frames instead of falling behind.
- `/events`: the status pushed 5 times a second (server-sent events), instead of the page asking.
- Each frame is drawn once, shared by every viewer, and only while someone is watching.

Measured from a laptop over Tailscale (October 10, fake phone at 15 fps): 6.3 frames a second on the page, first frame after 0.4 s, 13 KB a frame; status 5 a second. The first version polled a picture, a depth image and the status every 0.3 s; each request took 0.3-1 s over Tailscale, so the requests queued and the view ran late.

`/frame.jpg` gives one still and `/status` one status, for scripts. The phone's own capture-to-send time is not measured yet, so the delays shown are only the GX10 and network part.

`--dashboard-port 0` turns it off.

The phone app shows only the LiDAR feed (October 10); what it used to show is here: the guidance banner
tinted by state with the sentence spoken (kept 10 s, since speech is on one frame), the distance at the
centre of the depth picture with a reticle, a red edge on STOP, Describe/Read/Status/Stop buttons, and
"Heard": what the phone heard and whether the rules or the model placed it.

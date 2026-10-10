# GX10

Everything that runs on the ASUS Ascent GX10. All AI and all guidance decisions happen here.

## Planned pieces

| Piece | What it does | Owner |
| --- | --- | --- |
| `ingest/` | Receives frames from the phone on port 8765, keeps only the newest, records and replays sessions | Obstacle check |
| `planner/` | Seven-direction obstacle check, smoothing, command stream to the Pi on port 8766 | Obstacle check |
| `dashboard/` | Web page on port 8000: live picture, depth, chosen direction, delay, GPU use | Obstacle check |
| `vlm/` | Describe, read and find, using the vision-language model through Ollama | GX10 + models |
| `detector/` | YOLO on every frame | GX10 + models |
| `navigator/` | Follows a walking route; guides to a found object | GX10 + models |

Message formats are in [`../contracts/MESSAGES.md`](../contracts/MESSAGES.md).

## First commands on the GX10

```bash
nvidia-smi
ollama list
docker ps -a
df -h / && free -h
```

## Rules

- The obstacle check runs every frame and never waits for the vision-language model.
- The vision-language model never decides whether the way is clear. Distances come from the LiDAR.
- A direction with too few good depth readings counts as blocked.
- Do not change system settings on the borrowed GX10. Keep project files in one folder.
- Do not commit model files or recordings (see `.gitignore`).

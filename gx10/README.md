# GX10

Everything that ran on the ASUS Ascent GX10 at the hackathon, where all AI and all guidance decisions happened.

> Not part of the plan since October 14. The GX10 was borrowed for the event; the obstacle check moves to the iPhone and the talk button's questions go to a cloud AI. See `../AGENTS.md`. The planner here is the reference for the phone's obstacle check.

## Planned pieces

| Piece | What it does | Owner |
| --- | --- | --- |
| `ingest/` | Receives frames from the phone on port 8765 (8775 as started for the cane; see `ingest/README.md`), keeps only the newest, records and replays sessions. First version in; runs YOLO, navigator and planner on each frame | Obstacle check (first version by GX10 + models) |
| `planner/` | Seven-direction obstacle check, smoothing, command stream to the Pi on port 8766. First version in | Obstacle check (first version by GX10 + models) |
| `dashboard/` | Web page on port 8000: live picture, depth, chosen direction, delay, GPU use. First version in | Obstacle check (first version by GX10 + models) |
| `vlm/` | Describe, read and find, using the vision-language model through Ollama | GX10 + models |
| `detector/` | YOLO on every frame | GX10 + models |
| `navigator/` | Voice commands; guides to a found object; follows a walking route | GX10 + models |

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

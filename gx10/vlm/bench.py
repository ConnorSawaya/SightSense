"""Time a describe answer (about 20 words) on each model and check it is on the GPU.

    cd .. && python3 -m vlm.bench qwen3-vl:30b qwen3-vl:8b

Each model is loaded first (not timed), then timed over several runs.
"""

import base64
import json
import statistics
import sys
import time
import urllib.request
from pathlib import Path

from . import core

PIC = Path(__file__).parent / "test_images" / "street.jpg"
RUNS = 5


def gpu_share(model):
    with urllib.request.urlopen(core.OLLAMA_URL + "/api/ps", timeout=5) as r:
        for m in json.load(r)["models"]:
            if m["name"] == model:
                return m.get("size_vram", 0) / m["size"] if m.get("size") else 0.0
    return None


def bench(model):
    img = base64.b64encode(PIC.read_bytes()).decode()
    body = {"model": model, "stream": False, "think": False, "keep_alive": -1,
            "options": {"temperature": 0, "num_ctx": core.CTX},
            "messages": [{"role": "user", "content": core.PROMPTS["describe"], "images": [img]}]}
    core._post("/api/chat", body, 600)  # load and warm up, not timed
    walls, rates, words = [], [], []
    for _ in range(RUNS):
        t = time.monotonic()
        r = core._post("/api/chat", body, 120)
        walls.append(time.monotonic() - t)
        rates.append(r["eval_count"] / (r["eval_duration"] / 1e9))
        words.append(len(r["message"]["content"].split()))
        thinking = bool(r["message"].get("thinking"))
    share = gpu_share(model)
    print(f"{model:20s} median {statistics.median(walls):.2f}s (min {min(walls):.2f}, max {max(walls):.2f}) "
          f"| {statistics.median(rates):.0f} tokens/s | {statistics.median(words):.0f} words | "
          f"on GPU: {'?' if share is None else f'{share:.0%}'} | thinking: {thinking}")
    print(f"{'':20s} answer: {r['message']['content'].strip()!r}")


if __name__ == "__main__":
    for m in sys.argv[1:] or [core.MODEL, core.FALLBACK]:
        bench(m)

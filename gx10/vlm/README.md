# vlm

Describe, read and find, using a vision-language model through Ollama on the GX10. Standard library only; nothing to install.

The model never decides whether the way is clear and is never asked for a distance. `find()` returns a box; the distance comes from the LiDAR depth inside it.

## Use

From `gx10/`:

```python
from vlm import warm, describe, read, find

warm()                       # once at start: picks the model, loads it, keeps it loaded
a = describe(jpeg_bytes)     # a.text: "A blue and white bus with people walking in front of it."
a = read(jpeg_bytes)         # a.text: "EXIT\nRoom 204", or "" if there is no text
a = find(jpeg_bytes, "apple")
if a.ok and a.box:           # a.box: [x1, y1, x2, y2] in pixels of the picture you sent
    ...
```

Every call returns an `Answer`. If `a.ok` is false, say `a.text` ("I couldn't tell"); `a.error` says why (`timeout`, `busy`, unparseable reply, Ollama down). `a.seconds` is the model time and `a.raw` the model's reply, for the dashboard.

Command line:

```bash
python3 -m vlm describe picture.jpg
python3 -m vlm read picture.jpg
python3 -m vlm find picture.jpg apple
```

## Settings

Environment variables; nothing is hard-coded.

| Variable | Default | |
| --- | --- | --- |
| `SIGHTSENSE_OLLAMA_URL` | `http://127.0.0.1:11434` | |
| `SIGHTSENSE_VLM_MODEL` | `qwen3.6:35b` | Preloaded on the GX10. Set `qwen3-vl:30b` once it is downloaded and measured |
| `SIGHTSENSE_VLM_FALLBACK` | `qwen3-vl:8b-instruct` | Used if the main model is not installed |
| `SIGHTSENSE_VLM_TIMEOUT` | `6` | Seconds per call (`find` shares it across its two questions) |
| `SIGHTSENSE_VLM_BOX_SCALE` | by model | `1000` or `pixels` |
| `SIGHTSENSE_VLM_CTX` | `8192` | Context length. Ollama's default (262144) made `qwen3-vl:8b` take 48 GB |

## How it behaves

- One request at a time. A call made while another is running returns at once with `error="busy..."`; it never queues. Ask again with a newer picture.
- Thinking is off (`think: false`) and the model stays loaded (`keep_alive: -1`).
- A reply that does not parse becomes "I couldn't tell".
- `find` first asks "Is there a {name} in this image? Reply only yes or no." and asks for a box only on "yes". The box prompt alone always returned a box, even for things that were not there: it boxed an exit sign as an apple, and a floor shadow as a chair.
- Boxes come back on a 0–1000 scale and are converted to pixels using the picture's own size (read from the JPEG header).

## Tests

```bash
python3 -m unittest vlm.test_parse          # reply parsing, no model needed
python3 vlm/make_test_images.py APPLE.jpg STREET.jpg   # once; needs Pillow (on the GX10 already)
python3 -m vlm.check                        # live: all three functions on the test pictures
python3 -m vlm.bench MODEL [MODEL ...]      # time a describe answer, check it is on the GPU
```

`make_test_images.py` pastes an apple photo onto a plain floor at a known spot, and draws an exit sign with known text, so `check.py` can score the answers. Test pictures are not committed. The ones used below were made from Wikimedia Commons `Red_Apple.jpg` and Ultralytics' sample `bus.jpg`.

## Measured on the GX10 (October 10)

`check.py`: 11 checks (5 describe, 3 read, 4 find — 2 with an apple, 2 without).

| Model | Describe, about 12 words | Speed | On GPU | check.py | find (apple / none) |
| --- | --- | --- | --- | --- | --- |
| `qwen3.6:35b` (preloaded) | 0.74 s median of 5 | 62 tokens/s | 100% | 11/11 | 1.8 s / 0.5 s |
| `nemotron3:33b` (preloaded, Nemotron 3 Nano Omni) | 0.62 s median of 5 | 78 tokens/s | 100% | 11/11 | 1.2 s / 0.5 s |
| `qwen3-vl:8b-instruct` (8.1 GB loaded) | 0.55 s median of 5 | 45 tokens/s | 100% | 11/11 | 1.3 s / 0.2 s |
| `qwen3-vl:8b` (thinking; do not use) | 4.07 s median of 5 | 44 tokens/s | 100% | 10/11 | 5.2 s / 1.2 s |

`qwen3-vl:8b` is the same file as `qwen3-vl:8b-thinking`: it ignores `think: false`, so every answer waits for its reasoning, and one find reply came back in the wrong shape. `qwen3-vl:30b` is also the thinking model; use `qwen3-vl:30b-a3b-instruct`.

`qwen3.6:35b` uses 26 GB with the 8192-token context. Describe answers came out at 11–13 words.

Box overlap with the true apple box (IoU) was 0.82–0.88 for every model above. These are synthetic pictures with one object on a plain floor; real rooms will be harder.

A harder one-off set (script not committed), `find("apple")` only:

| Picture | `qwen3.6:35b` | `qwen3-vl:8b-instruct` |
| --- | --- | --- |
| Apple pasted into the street scene | found, IoU 0.88 | found, IoU 0.78 |
| Street scene, no apple | "no" | "no" |
| Small far apple (23 px wide) | found, IoU 0.91 | found, IoU 0.66 |
| Red ball and red box, no apple | "no" | "no" |
| Apple next to the red ball and box | found, IoU 0.88 | found, IoU 0.83 |

Not yet tried on real phone pictures.

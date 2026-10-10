"""Make test pictures with known answers for the describe / read / find checks.

Needs Pillow (already on the GX10's system Python). Writes into test_images/,
which is not committed.

    python3 make_test_images.py path/to/apple_photo.jpg [path/to/street.jpg]

The apple photo should be an apple on a plain light background. It is pasted
onto a plain floor at a known spot, so find() can be checked against the true box.
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 640, 480  # same size as the phone frames in contracts/MESSAGES.md
OUT = Path(__file__).parent / "test_images"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def floor():
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        for x in range(W):
            # wall on top, floor below, slight shading so it is not flat
            if y < H * 0.45:
                px[x, y] = (205 - y // 8, 200 - y // 8, 190 - y // 8)
            else:
                px[x, y] = (120 + y // 12, 105 + y // 12, 85 + y // 12)
    return img


def cut_out(photo, size):
    """Scale the apple photo and make near-white background see-through."""
    a = photo.convert("RGBA")
    a.thumbnail((size, size))
    data = [(r, g, b, 0) if min(r, g, b) > 225 else (r, g, b, 255) for r, g, b, _ in a.getdata()]
    a.putdata(data)
    box = a.getbbox()  # tight box around the visible apple
    return a.crop(box)


def text(draw, xy, s, size, fill):
    draw.text(xy, s, font=ImageFont.truetype(FONT, size), fill=fill)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    OUT.mkdir(exist_ok=True)
    photo = Image.open(sys.argv[1])
    truth = {}

    # Apple on the floor, once left of centre and once right of centre
    for name, (x, y, size) in {
        "apple_left.jpg": (110, 300, 110),
        "apple_right.jpg": (450, 330, 90),
    }.items():
        img = floor()
        apple = cut_out(photo, size)
        img.paste(apple, (x, y), apple)
        img.save(OUT / name, quality=90)
        truth[name] = {"find": "apple", "bbox_px": [x, y, x + apple.width, y + apple.height]}

    # A sign with known text
    img = floor()
    d = ImageDraw.Draw(img)
    d.rectangle([180, 60, 460, 200], fill=(20, 120, 60), outline=(240, 240, 240), width=6)
    text(d, (250, 75), "EXIT", 64, (255, 255, 255))
    text(d, (215, 150), "Room 204  >", 34, (255, 255, 255))
    img.save(OUT / "sign_exit.jpg", quality=90)
    truth["sign_exit.jpg"] = {"read": ["EXIT", "204"], "find": "apple", "bbox_px": None}

    # Nothing to read and nothing to find
    floor().save(OUT / "empty_room.jpg", quality=90)
    truth["empty_room.jpg"] = {"read": [], "find": "apple", "bbox_px": None}

    # A real street scene, for describe only
    if len(sys.argv) > 2:
        street = Image.open(sys.argv[2]).convert("RGB")
        street.thumbnail((W, W))
        street.save(OUT / "street.jpg", quality=90)
        truth["street.jpg"] = {}

    (OUT / "truth.json").write_text(json.dumps(truth, indent=2))
    print(f"wrote {len(truth)} pictures to {OUT}")


if __name__ == "__main__":
    main()

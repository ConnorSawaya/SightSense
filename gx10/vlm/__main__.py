"""Command line, run from gx10/:

    python3 -m vlm describe picture.jpg
    python3 -m vlm read picture.jpg
    python3 -m vlm find picture.jpg apple
"""

import json
import sys
from dataclasses import asdict

from . import core


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("describe", "read", "find") or (sys.argv[1] == "find" and len(sys.argv) < 4):
        sys.exit(__doc__)
    cmd, path = sys.argv[1], sys.argv[2]
    jpeg = open(path, "rb").read()
    print(f"loading {core.warm()} ...", file=sys.stderr)
    a = core.find(jpeg, " ".join(sys.argv[3:])) if cmd == "find" else getattr(core, cmd)(jpeg)
    print(json.dumps(asdict(a), indent=2))


if __name__ == "__main__":
    main()

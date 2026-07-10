#!/usr/bin/env python3
from collections import deque
from pathlib import Path
import sys

from PIL import Image


def is_background(pixel):
    r, g, b, a = pixel
    if a == 0:
        return False
    if (r, g, b) == (255, 255, 255):
        return True
    return r >= 238 and g >= 238 and b >= 238 and max(r, g, b) - min(r, g, b) <= 30


def strip_white_matte(path):
    image = Image.open(path).convert("RGBA")
    width, height = image.size
    pixels = image.load()
    seen = set()
    queue = deque()

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    changed = 0
    while queue:
        x, y = queue.popleft()
        if (x, y) in seen or not (0 <= x < width and 0 <= y < height):
            continue
        seen.add((x, y))
        if not is_background(pixels[x, y]):
            continue

        r, g, b, _ = pixels[x, y]
        pixels[x, y] = (r, g, b, 0)
        changed += 1
        queue.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))

    if changed:
        image.save(path)
    return changed


def main():
    if len(sys.argv) != 2:
        print("usage: remove-white-matte.py ICON_DIR", file=sys.stderr)
        return 2

    icon_dir = Path(sys.argv[1])
    total = 0
    files = sorted(icon_dir.glob("*.png"))
    for path in files:
        total += strip_white_matte(path)

    print(f"Processed {len(files)} PNG files; cleared {total} background pixels.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

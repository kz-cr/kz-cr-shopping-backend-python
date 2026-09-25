#!/usr/bin/env python
"""Download and vendor the catalogue photographs into ``app/static/images``.

The processed images are committed to the repository so that the backend runs
without network access. Re-run this only when ``app.catalog`` changes:

    python scripts/fetch_images.py          # skip files that already exist
    python scripts/fetch_images.py --force  # re-download everything

Requires the extra dependencies in ``requirements-dev.txt`` (Pillow).
"""

from __future__ import annotations

import argparse
import io
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.catalog import CATALOG, CatalogEntry, source_url  # noqa: E402
from app.paths import IMAGE_DIR, THUMBNAIL_DIR  # noqa: E402

FULL_MAX_EDGE = 1400
THUMBNAIL_MAX_EDGE = 400
JPEG_QUALITY = 82


def process(entry: CatalogEntry, force: bool) -> str:
    full_path = IMAGE_DIR / f"{entry.slug}.jpg"
    thumb_path = THUMBNAIL_DIR / f"{entry.slug}.jpg"
    if not force and full_path.exists() and thumb_path.exists():
        return f"skip  {entry.slug}"

    with urllib.request.urlopen(source_url(entry.source_image), timeout=60) as response:
        raw = response.read()

    image = Image.open(io.BytesIO(raw))
    image = image.convert("RGB")

    for path, max_edge in ((full_path, FULL_MAX_EDGE), (thumb_path, THUMBNAIL_MAX_EDGE)):
        resized = image.copy()
        resized.thumbnail((max_edge, max_edge), Image.LANCZOS)
        resized.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)

    return f"write {entry.slug} ({image.width}x{image.height} source)"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true", help="re-download images that already exist"
    )
    args = parser.parse_args()

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=8) as pool:
        for line in pool.map(lambda e: process(e, args.force), CATALOG):
            print(line)

    print(f"\n{len(CATALOG)} catalogue images in {IMAGE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

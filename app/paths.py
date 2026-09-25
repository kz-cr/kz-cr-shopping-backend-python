"""Filesystem locations shared by the app, the seeder and the scripts."""

from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent

STATIC_DIR = PACKAGE_DIR / "static"
IMAGE_DIR = STATIC_DIR / "images"
THUMBNAIL_DIR = IMAGE_DIR / "thumbs"

INSTANCE_DIR = PROJECT_DIR / "instance"
DATABASE_PATH = INSTANCE_DIR / "gallery.db"

# Paths as they appear in ``url_for("static", filename=...)``.
IMAGE_STATIC_PREFIX = "images"
THUMBNAIL_STATIC_PREFIX = "images/thumbs"

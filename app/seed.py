"""Populate the database from :mod:`app.catalog`."""

from __future__ import annotations

import logging

from sqlalchemy import func, select

from .catalog import CATALOG, assign_prices
from .extensions import db
from .models import Artwork, ArtworkImage
from .paths import IMAGE_DIR, THUMBNAIL_DIR

logger = logging.getLogger(__name__)


def artwork_count() -> int:
    """Count the artworks currently stored in the database."""
    return db.session.scalar(select(func.count()).select_from(Artwork)) or 0


def seed_database(*, reset: bool = False) -> int:
    """Insert the catalogue. Returns the number of artworks written.

    A populated database is left alone unless ``reset`` is set, so restarting
    the server never duplicates rows.
    """
    if reset:
        db.session.query(ArtworkImage).delete()
        db.session.query(Artwork).delete()
        db.session.commit()
    elif artwork_count():
        return 0

    prices = assign_prices()

    for entry in CATALOG:
        filename = f"{entry.slug}.jpg"
        artwork = Artwork(
            slug=entry.slug,
            title=entry.title,
            description=entry.description,
            artist=entry.artist,
            year=entry.year,
            medium=entry.medium,
            category=entry.category,
            price_cents=prices[entry.slug],
            currency="USD",
        )
        artwork.images.append(
            ArtworkImage(
                filename=filename,
                thumbnail_filename=filename,
                alt_text=entry.alt_text,
                position=0,
            )
        )
        db.session.add(artwork)

    db.session.commit()
    return len(CATALOG)


def missing_image_files() -> list[str]:
    """Catalogue slugs with no vendored image on disk.

    Reported as a warning rather than an error: the API is still perfectly
    usable, the pictures just 404 until ``scripts/fetch_images.py`` is run.
    """
    missing = []
    for entry in CATALOG:
        filename = f"{entry.slug}.jpg"
        if not (IMAGE_DIR / filename).exists() or not (THUMBNAIL_DIR / filename).exists():
            missing.append(entry.slug)
    return missing

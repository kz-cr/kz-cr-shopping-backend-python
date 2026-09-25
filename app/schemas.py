"""Model to JSON conversion.

Kept as plain functions rather than a serialization library: the payload is
small, and an explicit dict is the clearest contract for the frontend.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask import url_for

from .models import Artwork, ArtworkImage
from .paths import IMAGE_STATIC_PREFIX, THUMBNAIL_STATIC_PREFIX


def _static_url(prefix: str, filename: str) -> str:
    return url_for("static", filename=f"{prefix}/{filename}", _external=True)


def _isoformat_utc(value: datetime | None) -> str | None:
    """Render a timestamp as an explicitly UTC ISO 8601 string.

    Timestamps are written as aware UTC but SQLite has no timezone type and
    hands them back naive, which would otherwise emit an ambiguous string.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def serialize_image(image: ArtworkImage) -> dict[str, Any]:
    return {
        "id": image.id,
        "url": _static_url(IMAGE_STATIC_PREFIX, image.filename),
        "thumbnail_url": _static_url(THUMBNAIL_STATIC_PREFIX, image.thumbnail_filename),
        "alt": image.alt_text,
        "position": image.position,
        "is_primary": image.is_primary,
    }


def serialize_artwork(artwork: Artwork) -> dict[str, Any]:
    images = [serialize_image(image) for image in artwork.images]
    return {
        "id": artwork.id,
        "slug": artwork.slug,
        "title": artwork.title,
        "description": artwork.description,
        "artist": artwork.artist,
        "year": artwork.year,
        "medium": artwork.medium,
        "category": artwork.category,
        "price": artwork.price,
        "price_cents": artwork.price_cents,
        "currency": artwork.currency,
        "images": images,
        "primary_image": images[0] if images else None,
        "created_at": _isoformat_utc(artwork.created_at),
    }

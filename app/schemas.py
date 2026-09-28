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
    """Build an absolute URL for an image under the static directory."""
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
    """Expose an image's full-size and thumbnail URLs to API clients."""
    return {
        "id": image.id,
        "url": _static_url(IMAGE_STATIC_PREFIX, image.filename),
        "thumbnail_url": _static_url(THUMBNAIL_STATIC_PREFIX, image.thumbnail_filename),
        "alt": image.alt_text,
        "position": image.position,
        "is_primary": image.is_primary,
    }


def serialize_artwork(artwork: Artwork) -> dict[str, Any]:
    """Convert an artwork and its ordered images to the public API shape."""
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


def serialize_item_reference(artwork: Artwork) -> dict[str, Any]:
    """Convert an artwork to the compact shape used by detail-page rails.

    Related pieces and the previous/next links only need enough to draw a card
    and a link, so the description and the full image list are left out.
    """
    images = artwork.images
    return {
        "id": artwork.id,
        "slug": artwork.slug,
        "title": artwork.title,
        "artist": artwork.artist,
        "year": artwork.year,
        "category": artwork.category,
        "price": artwork.price,
        "price_cents": artwork.price_cents,
        "currency": artwork.currency,
        "primary_image": serialize_image(images[0]) if images else None,
    }


def serialize_price_range(
    min_cents: int | None, max_cents: int | None, currency: str
) -> dict[str, Any] | None:
    """Describe a span of prices in both dollars and authoritative cents."""
    if min_cents is None or max_cents is None:
        return None
    return {
        "min": round(min_cents / 100, 2),
        "max": round(max_cents / 100, 2),
        "min_cents": min_cents,
        "max_cents": max_cents,
        "currency": currency,
    }

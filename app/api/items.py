"""Listing endpoints.

``GET /api/items``            every piece in the catalogue
``GET /api/items/<id|slug>``  a single piece
"""

from __future__ import annotations

from flask import jsonify
from sqlalchemy import select

from ..errors import ApiError
from ..extensions import db
from ..models import Artwork
from ..schemas import serialize_artwork
from . import api_bp


@api_bp.get("/items")
def list_items():
    """Return the whole catalogue in one response.

    The catalogue is 30 rows, so there is nothing to gain from paging it yet.
    Pagination, search, filtering and sorting are a follow-up; when they land,
    ``items`` keeps its shape and the extra metadata is added alongside it.
    """
    artworks = db.session.scalars(select(Artwork).order_by(Artwork.id)).all()
    items = [serialize_artwork(artwork) for artwork in artworks]

    return jsonify({"items": items, "count": len(items)})


@api_bp.get("/items/<identifier>")
def get_item(identifier: str):
    """Fetch one piece by numeric id or by slug."""
    stmt = select(Artwork)
    if identifier.isdigit():
        stmt = stmt.where(Artwork.id == int(identifier))
    else:
        stmt = stmt.where(Artwork.slug == identifier)

    artwork = db.session.scalars(stmt).first()
    if artwork is None:
        raise ApiError(f"No item matching {identifier!r}", 404)

    return jsonify({"item": serialize_artwork(artwork)})

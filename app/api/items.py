"""Listing endpoints.

``GET /api/items``            paginated, filterable, sortable listing
``GET /api/items/<id|slug>``  a single piece
``GET /api/categories``       the categories present in the catalogue
"""

from __future__ import annotations

from flask import current_app, jsonify, request
from sqlalchemy import func, or_, select

from ..errors import ApiError
from ..extensions import db
from ..models import Artwork, ArtworkImage
from ..schemas import serialize_artwork
from . import api_bp
from .params import escape_like, parse_choice, parse_int, parse_price_cents, parse_search

#: Accepted ``sort`` values mapped to their ORDER BY clauses. ``Artwork.id`` is
#: appended to every option as a tiebreak, so pagination is stable when two
#: rows compare equal.
SORT_OPTIONS = {
    "curated": (Artwork.id.asc(),),
    "price_asc": (Artwork.price_cents.asc(), Artwork.id.asc()),
    "price_desc": (Artwork.price_cents.desc(), Artwork.id.asc()),
    "title_asc": (Artwork.title.asc(), Artwork.id.asc()),
    "title_desc": (Artwork.title.desc(), Artwork.id.asc()),
    "newest": (Artwork.created_at.desc(), Artwork.id.desc()),
}
DEFAULT_SORT = "curated"


@api_bp.get("/items")
def list_items():
    config = current_app.config
    args = request.args

    page = parse_int(args.get("page"), name="page", default=1, minimum=1, maximum=10_000)
    per_page = parse_int(
        args.get("per_page"),
        name="per_page",
        default=config["DEFAULT_PAGE_SIZE"],
        minimum=1,
        maximum=config["MAX_PAGE_SIZE"],
    )
    sort_key, order_by = parse_choice(
        args.get("sort"), name="sort", choices=SORT_OPTIONS, default=DEFAULT_SORT
    )
    search = parse_search(args.get("q"))
    category = (args.get("category") or "").strip() or None
    artist = (args.get("artist") or "").strip() or None
    min_price = parse_price_cents(args.get("min_price"), name="min_price")
    max_price = parse_price_cents(args.get("max_price"), name="max_price")

    if min_price is not None and max_price is not None and min_price > max_price:
        raise ApiError("'min_price' must not be greater than 'max_price'")

    stmt = select(Artwork)

    if search:
        pattern = f"%{escape_like(search)}%"
        # Image alt text is searched too: it describes what is actually in the
        # picture, so a term like "mountain" should find a piece whose title
        # and description only ever say "massif".
        matching_alt_text = (
            select(ArtworkImage.id)
            .where(ArtworkImage.artwork_id == Artwork.id)
            .where(ArtworkImage.alt_text.ilike(pattern, escape="\\"))
            .exists()
        )
        stmt = stmt.where(
            or_(
                Artwork.title.ilike(pattern, escape="\\"),
                Artwork.description.ilike(pattern, escape="\\"),
                Artwork.artist.ilike(pattern, escape="\\"),
                matching_alt_text,
            )
        )
    if category:
        stmt = stmt.where(func.lower(Artwork.category) == category.lower())
    if artist:
        stmt = stmt.where(func.lower(Artwork.artist) == artist.lower())
    if min_price is not None:
        stmt = stmt.where(Artwork.price_cents >= min_price)
    if max_price is not None:
        stmt = stmt.where(Artwork.price_cents <= max_price)

    total = db.session.scalar(
        select(func.count()).select_from(stmt.order_by(None).subquery())
    )
    rows = db.session.scalars(
        stmt.order_by(*order_by).limit(per_page).offset((page - 1) * per_page)
    ).all()

    total_pages = (total + per_page - 1) // per_page if total else 0

    return jsonify(
        {
            "items": [serialize_artwork(artwork) for artwork in rows],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_items": total,
                "total_pages": total_pages,
                "has_previous": page > 1,
                "has_next": page < total_pages,
            },
            "applied": {
                "q": search,
                "category": category,
                "artist": artist,
                "min_price": min_price / 100 if min_price is not None else None,
                "max_price": max_price / 100 if max_price is not None else None,
                "sort": sort_key,
            },
        }
    )


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


@api_bp.get("/categories")
def list_categories():
    """Categories actually present in the catalogue, with their item counts.

    Lets a client build the category filter without hard-coding the vocabulary.
    """
    rows = db.session.execute(
        select(Artwork.category, func.count(Artwork.id))
        .group_by(Artwork.category)
        .order_by(Artwork.category)
    ).all()
    return jsonify(
        {"categories": [{"name": name, "item_count": count} for name, count in rows]}
    )

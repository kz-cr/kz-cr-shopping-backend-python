"""Listing endpoints.

``GET /api/items``            paginated, filterable, sortable listing
``GET /api/items/<id|slug>``  a single piece
``GET /api/items/<id|slug>/detail``
                              a single piece plus the context a product
                              page needs around it
``GET /api/categories``       the categories present in the catalogue
"""

from __future__ import annotations

from typing import Any

from flask import current_app, jsonify, request
from sqlalchemy import func, or_, select

from ..errors import ApiError
from ..extensions import db
from ..models import Artwork, ArtworkImage
from ..schemas import serialize_artwork, serialize_item_reference, serialize_price_range
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

#: How many related pieces ``/detail`` returns per rail unless asked otherwise.
DEFAULT_RELATED_LIMIT = 4
MAX_RELATED_LIMIT = 12


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


def _load_artwork(identifier: str) -> Artwork:
    """Resolve a numeric id or a slug to an artwork, or raise a 404."""
    stmt = select(Artwork)
    if identifier.isdigit():
        stmt = stmt.where(Artwork.id == int(identifier))
    else:
        stmt = stmt.where(Artwork.slug == identifier)

    artwork = db.session.scalars(stmt).first()
    if artwork is None:
        raise ApiError(f"No item matching {identifier!r}", 404)
    return artwork


@api_bp.get("/items/<identifier>")
def get_item(identifier: str):
    """Fetch one piece by numeric id or by slug."""
    return jsonify({"item": serialize_artwork(_load_artwork(identifier))})


@api_bp.get("/items/<identifier>/detail")
def get_item_detail(identifier: str):
    """Fetch one piece with the surrounding context a product page needs.

    Everything here is derived from the same catalogue the listing reads, so a
    detail view costs one request instead of the half-dozen filtered listing
    calls a client would otherwise make to fill in the artist, the category and
    the related rails.
    """
    artwork = _load_artwork(identifier)
    related_limit = parse_int(
        request.args.get("related_limit"),
        name="related_limit",
        default=DEFAULT_RELATED_LIMIT,
        minimum=0,
        maximum=MAX_RELATED_LIMIT,
    )

    return jsonify(
        {
            "item": {
                **serialize_artwork(artwork),
                "image_count": len(artwork.images),
            },
            "artist": _artist_context(artwork, related_limit),
            "category": _category_context(artwork),
            "similar": _similar_items(artwork, related_limit),
            "navigation": _navigation(artwork),
        }
    )


def _artist_context(artwork: Artwork, limit: int) -> dict[str, Any]:
    """Summarize the artist and list their other pieces in the catalogue.

    Matched case-insensitively on the artist name, the same way the listing's
    ``artist`` filter matches, so the counts here agree with that listing.
    """
    same_artist = func.lower(Artwork.artist) == artwork.artist.lower()

    item_count, min_cents, max_cents, earliest, latest = db.session.execute(
        select(
            func.count(Artwork.id),
            func.min(Artwork.price_cents),
            func.max(Artwork.price_cents),
            func.min(Artwork.year),
            func.max(Artwork.year),
        ).where(same_artist)
    ).one()

    other_works = []
    if limit:
        rows = db.session.scalars(
            select(Artwork)
            .where(same_artist, Artwork.id != artwork.id)
            .order_by(Artwork.id.asc())
            .limit(limit)
        ).all()
        other_works = [serialize_item_reference(row) for row in rows]

    return {
        "name": artwork.artist,
        "item_count": item_count,
        "years": {"earliest": earliest, "latest": latest},
        "price_range": serialize_price_range(min_cents, max_cents, artwork.currency),
        "other_works": other_works,
        "other_work_count": max(item_count - 1, 0),
    }


def _category_context(artwork: Artwork) -> dict[str, Any]:
    """Summarize the category this piece sits in."""
    same_category = func.lower(Artwork.category) == artwork.category.lower()

    item_count, min_cents, max_cents = db.session.execute(
        select(
            func.count(Artwork.id),
            func.min(Artwork.price_cents),
            func.max(Artwork.price_cents),
        ).where(same_category)
    ).one()

    return {
        "name": artwork.category,
        "item_count": item_count,
        "price_range": serialize_price_range(min_cents, max_cents, artwork.currency),
    }


def _similar_items(artwork: Artwork, limit: int) -> list[dict[str, Any]]:
    """Other pieces in the same category, in curated order.

    Deliberately independent of ``artist.other_works``: a small category would
    otherwise come back empty for an artist who dominates it, and the two rails
    are rendered separately anyway.
    """
    if not limit:
        return []

    rows = db.session.scalars(
        select(Artwork)
        .where(
            func.lower(Artwork.category) == artwork.category.lower(),
            Artwork.id != artwork.id,
        )
        .order_by(Artwork.id.asc())
        .limit(limit)
    ).all()
    return [serialize_item_reference(row) for row in rows]


def _navigation(artwork: Artwork) -> dict[str, Any]:
    """Locate this piece in the curated order, with its neighbours.

    Curated order is ``Artwork.id`` ascending, matching the listing's default
    sort, so paging through detail views walks the catalogue in the same order
    the grid showed.
    """
    previous = db.session.scalars(
        select(Artwork)
        .where(Artwork.id < artwork.id)
        .order_by(Artwork.id.desc())
        .limit(1)
    ).first()
    following = db.session.scalars(
        select(Artwork)
        .where(Artwork.id > artwork.id)
        .order_by(Artwork.id.asc())
        .limit(1)
    ).first()

    total_items = db.session.scalar(select(func.count()).select_from(Artwork))
    position = db.session.scalar(
        select(func.count()).select_from(Artwork).where(Artwork.id <= artwork.id)
    )

    return {
        "position": position,
        "total_items": total_items,
        "previous": serialize_item_reference(previous) if previous else None,
        "next": serialize_item_reference(following) if following else None,
    }


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

"""Database models for the gallery."""

from __future__ import annotations

from datetime import datetime, timezone

from .extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Artwork(db.Model):
    """A single piece for sale in the gallery."""

    __tablename__ = "artworks"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), nullable=False, unique=True, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    artist = db.Column(db.String(120), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False)
    medium = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False, index=True)

    # Money is stored as an integer number of cents; floats are not a currency
    # type and rounding drift in a price column is a real bug, not a rounding
    # curiosity.
    price_cents = db.Column(db.Integer, nullable=False, index=True)
    currency = db.Column(db.String(3), nullable=False, default="USD")

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_utcnow)

    images = db.relationship(
        "ArtworkImage",
        back_populates="artwork",
        order_by="ArtworkImage.position",
        cascade="all, delete-orphan",
        lazy="selectin",  # one extra query per page, rather than one per row
    )

    __table_args__ = (
        db.CheckConstraint("price_cents > 0", name="ck_artworks_price_positive"),
    )

    @property
    def price(self) -> float:
        return round(self.price_cents / 100, 2)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Artwork {self.id} {self.slug!r}>"


class ArtworkImage(db.Model):
    """One photograph belonging to an artwork.

    Modelled as a separate table even though the demo catalogue ships a single
    image per piece, so that adding detail or framing shots later is a data
    change rather than a schema change.
    """

    __tablename__ = "artwork_images"

    id = db.Column(db.Integer, primary_key=True)
    artwork_id = db.Column(
        db.Integer,
        db.ForeignKey("artworks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename = db.Column(db.String(200), nullable=False)
    thumbnail_filename = db.Column(db.String(200), nullable=False)
    alt_text = db.Column(db.String(300), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)

    artwork = db.relationship("Artwork", back_populates="images")

    __table_args__ = (
        db.UniqueConstraint("artwork_id", "position", name="uq_artwork_image_position"),
    )

    @property
    def is_primary(self) -> bool:
        return self.position == 0

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<ArtworkImage {self.id} {self.filename!r}>"

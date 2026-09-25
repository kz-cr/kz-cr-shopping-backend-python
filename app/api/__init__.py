"""The versioned JSON API."""

from __future__ import annotations

from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

from . import items  # noqa: E402,F401  (registers routes on api_bp)

__all__ = ["api_bp"]

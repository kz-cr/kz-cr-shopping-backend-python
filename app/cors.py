"""Cross-origin support for browser frontends.

The gallery frontend runs on its own dev server, so every call to this API is
cross-origin. Hand-rolled rather than pulling in Flask-Cors: the API is
read-only and unauthenticated, so the policy is a handful of headers.
"""

from __future__ import annotations

from flask import Flask, Response, request

ALLOWED_METHODS = "GET, OPTIONS"
ALLOWED_HEADERS = "Content-Type"
MAX_AGE = "600"


def _allowed_origin(app: Flask) -> str | None:
    """Resolve the value for ``Access-Control-Allow-Origin``, if any."""
    origins = app.config.get("CORS_ORIGINS") or []
    if "*" in origins:
        return "*"

    request_origin = request.headers.get("Origin")
    if request_origin and request_origin in origins:
        return request_origin
    return None


def register_cors(app: Flask) -> None:
    @app.after_request
    def add_cors_headers(response: Response) -> Response:
        origin = _allowed_origin(app)
        if origin is None:
            return response

        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = ALLOWED_METHODS
        response.headers["Access-Control-Allow-Headers"] = ALLOWED_HEADERS
        response.headers["Access-Control-Max-Age"] = MAX_AGE
        if origin != "*":
            # Responses differ per origin, so caches must key on it.
            response.headers.add("Vary", "Origin")
        return response

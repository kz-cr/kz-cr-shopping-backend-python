"""A single JSON error shape for every failure the API can return."""

from __future__ import annotations

from typing import Any

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """An error that should be rendered to the client verbatim."""

    def __init__(
        self, message: str, status: int = 400, *, details: dict[str, Any] | None = None
    ) -> None:
        """Store the public message, HTTP status, and optional error details."""
        super().__init__(message)
        self.message = message
        self.status = status
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize this error into the API's JSON error shape."""
        payload: dict[str, Any] = {"error": {"status": self.status, "message": self.message}}
        if self.details:
            payload["error"]["details"] = self.details
        return payload


def register_error_handlers(app: Flask) -> None:
    """Make application and HTTP errors return JSON responses."""
    @app.errorhandler(ApiError)
    def handle_api_error(exc: ApiError):
        """Render an intentional API error with its declared status."""
        return jsonify(exc.to_dict()), exc.status

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        """Convert framework HTTP errors to the API's JSON shape."""
        # Keeps 404s and 405s on non-API routes in the same JSON shape, so a
        # client never has to parse Werkzeug's HTML error page.
        error = ApiError(exc.description or exc.name, exc.code or 500)
        return jsonify(error.to_dict()), error.status

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):  # pragma: no cover - safety net
        """Log unexpected failures and hide their details from clients."""
        app.logger.exception("Unhandled error", exc_info=exc)
        error = ApiError("Internal server error", 500)
        return jsonify(error.to_dict()), 500

"""Query string parsing for the listing endpoint.

Every parser raises :class:`ApiError` on bad input so the client gets a 400
with a usable message instead of a silently ignored filter.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from ..errors import ApiError


def parse_int(raw: str | None, *, name: str, default: int, minimum: int, maximum: int) -> int:
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ApiError(f"'{name}' must be an integer, got {raw!r}") from None
    if value < minimum or value > maximum:
        raise ApiError(f"'{name}' must be between {minimum} and {maximum}, got {value}")
    return value


def parse_price_cents(raw: str | None, *, name: str) -> int | None:
    """Parse a price given in dollars into whole cents."""
    if raw is None or raw == "":
        return None
    try:
        value = Decimal(raw)
    except InvalidOperation:
        raise ApiError(f"'{name}' must be a number of dollars, got {raw!r}") from None
    if value < 0:
        raise ApiError(f"'{name}' must not be negative, got {raw!r}")
    return int((value * 100).to_integral_value())


def parse_choice(raw: str | None, *, name: str, choices: dict[str, object], default: str):
    key = (raw or default).strip().lower()
    if key not in choices:
        raise ApiError(
            f"'{name}' must be one of {sorted(choices)}, got {raw!r}",
            details={"allowed": sorted(choices)},
        )
    return key, choices[key]


def parse_search(raw: str | None) -> str | None:
    if raw is None:
        return None
    term = raw.strip()
    if not term:
        return None
    if len(term) > 200:
        raise ApiError("'q' must be 200 characters or fewer")
    return term


def escape_like(term: str) -> str:
    """Escape LIKE wildcards so a literal % or _ in a search term matches itself."""
    for char in ("\\", "%", "_"):
        term = term.replace(char, f"\\{char}")
    return term

from __future__ import annotations

from datetime import datetime

from app.catalog import CATALOG, PRICE_MAX_CENTS, PRICE_MIN_CENTS

CATALOG_SIZE = len(CATALOG)


def test_catalog_has_thirty_unique_entries():
    """Keep the demo catalogue at 30 entries with distinct slugs."""
    assert CATALOG_SIZE == 30
    assert len({entry.slug for entry in CATALOG}) == 30


def test_list_returns_the_whole_catalogue(client):
    """Return every item once, in stable ID order."""
    body = client.get("/api/items").get_json()

    assert body["count"] == CATALOG_SIZE
    assert len(body["items"]) == CATALOG_SIZE

    ids = [item["id"] for item in body["items"]]
    assert ids == sorted(ids), "items should come back in a stable order"
    assert len(set(ids)) == CATALOG_SIZE


def test_item_payload_shape(client):
    """Expose prices and image metadata in the documented API shape."""
    item = client.get("/api/items").get_json()["items"][0]

    assert item["title"]
    assert len(item["description"]) > 40
    assert PRICE_MIN_CENTS <= item["price_cents"] <= PRICE_MAX_CENTS
    assert item["price"] == round(item["price_cents"] / 100, 2)
    assert item["currency"] == "USD"

    image = item["images"][0]
    assert image["url"].startswith("http://")
    assert image["url"].endswith(".jpg")
    assert "/thumbs/" in image["thumbnail_url"]
    assert image["alt"]
    assert item["primary_image"] == image


def test_every_item_has_a_title_description_price_and_image(client):
    """Keep required listing fields populated across the whole catalogue."""
    items = client.get("/api/items").get_json()["items"]

    assert len({item["title"] for item in items}) == CATALOG_SIZE
    for item in items:
        assert item["title"], item["slug"]
        assert len(item["description"]) > 40, item["slug"]
        assert PRICE_MIN_CENTS <= item["price_cents"] <= PRICE_MAX_CENTS, item["slug"]
        assert item["images"], item["slug"]


def test_every_image_url_actually_serves_a_jpeg(client):
    """Serve both image sizes as JPEGs at their advertised URLs."""
    for item in client.get("/api/items").get_json()["items"]:
        image = item["images"][0]
        for url in (image["url"], image["thumbnail_url"]):
            response = client.get(url)
            assert response.status_code == 200, url
            assert response.mimetype == "image/jpeg", url


def test_created_at_is_explicit_utc(client):
    """Serialize creation timestamps as parseable UTC values."""
    created_at = client.get("/api/items").get_json()["items"][0]["created_at"]

    assert created_at.endswith("Z")
    datetime.fromisoformat(created_at.replace("Z", "+00:00"))


def test_get_item_by_id_and_slug(client):
    """Resolve either item identifier to the same artwork payload."""
    listed = client.get("/api/items").get_json()["items"][0]

    by_id = client.get(f"/api/items/{listed['id']}").get_json()["item"]
    by_slug = client.get(f"/api/items/{listed['slug']}").get_json()["item"]

    assert by_id == by_slug == listed


def test_missing_item_returns_json_404(client):
    """Return a JSON 404 when no artwork matches the requested identifier."""
    response = client.get("/api/items/does-not-exist")

    assert response.status_code == 404
    assert response.get_json()["error"]["status"] == 404


def test_unknown_route_returns_json_not_html(client):
    """Keep framework 404 responses in the API's JSON format."""
    response = client.get("/api/nope")

    assert response.status_code == 404
    assert response.mimetype == "application/json"


def test_prices_are_stable_across_rebuilds():
    """Assign deterministic prices within the catalogue's allowed range."""
    from app.catalog import assign_prices

    first = assign_prices()
    assert assign_prices() == first
    assert all(PRICE_MIN_CENTS <= cents <= PRICE_MAX_CENTS for cents in first.values())


def test_seeding_twice_does_not_duplicate_rows(app):
    """Leave an already populated database unchanged on a second seed."""
    from app.seed import artwork_count, seed_database

    assert artwork_count() == CATALOG_SIZE
    assert seed_database() == 0
    assert artwork_count() == CATALOG_SIZE


class TestCors:
    def test_wildcard_origin_by_default(self, client):
        """Allow browser requests from any origin in the default config."""
        response = client.get("/api/items", headers={"Origin": "http://localhost:3000"})
        assert response.headers["Access-Control-Allow-Origin"] == "*"

    def test_preflight_is_answered(self, client):
        """Advertise GET support in a browser preflight response."""
        response = client.options(
            "/api/items",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert "GET" in response.headers["Access-Control-Allow-Methods"]

    def test_allowlist_rejects_unlisted_origin(self, app, client):
        """Advertise CORS only for origins in the configured allowlist."""
        app.config["CORS_ORIGINS"] = ["http://localhost:3000"]

        allowed = client.get("/api/items", headers={"Origin": "http://localhost:3000"})
        assert allowed.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
        assert "Origin" in allowed.headers["Vary"]

        blocked = client.get("/api/items", headers={"Origin": "http://evil.example"})
        assert "Access-Control-Allow-Origin" not in blocked.headers

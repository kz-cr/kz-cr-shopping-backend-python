from __future__ import annotations

from datetime import datetime

from app.catalog import CATALOG, PRICE_MAX_CENTS, PRICE_MIN_CENTS

CATALOG_SIZE = len(CATALOG)


def test_catalog_has_thirty_unique_entries():
    assert CATALOG_SIZE == 30
    assert len({entry.slug for entry in CATALOG}) == 30


def test_list_returns_first_page(client):
    body = client.get("/api/items").get_json()

    assert body["pagination"] == {
        "page": 1,
        "per_page": 12,
        "total_items": CATALOG_SIZE,
        "total_pages": 3,
        "has_previous": False,
        "has_next": True,
    }
    assert len(body["items"]) == 12


def test_item_payload_shape(client):
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


def test_every_item_has_an_image_that_is_actually_served(client):
    body = client.get("/api/items?per_page=100").get_json()
    assert len(body["items"]) == CATALOG_SIZE

    for item in body["items"]:
        assert item["images"], f"{item['slug']} has no image"
        for url in (item["images"][0]["url"], item["images"][0]["thumbnail_url"]):
            response = client.get(url)
            assert response.status_code == 200, url
            assert response.mimetype == "image/jpeg"


def test_pagination_walks_the_whole_catalogue_without_repeats(client):
    seen = []
    for page in (1, 2, 3):
        body = client.get(f"/api/items?page={page}&per_page=12").get_json()
        seen.extend(item["id"] for item in body["items"])

    assert len(seen) == CATALOG_SIZE
    assert len(set(seen)) == CATALOG_SIZE

    empty = client.get("/api/items?page=4&per_page=12").get_json()
    assert empty["items"] == []
    assert empty["pagination"]["has_next"] is False


def test_sort_by_price(client):
    ascending = [
        item["price_cents"]
        for item in client.get("/api/items?sort=price_asc&per_page=100").get_json()["items"]
    ]
    descending = [
        item["price_cents"]
        for item in client.get("/api/items?sort=price_desc&per_page=100").get_json()["items"]
    ]

    assert ascending == sorted(ascending)
    assert descending == sorted(ascending, reverse=True)


def test_price_range_filter(client):
    body = client.get("/api/items?min_price=200&max_price=300&per_page=100").get_json()

    assert body["items"], "expected at least one item in the $200-$300 band"
    assert all(20000 <= item["price_cents"] <= 30000 for item in body["items"])
    assert body["applied"]["min_price"] == 200.0
    assert body["applied"]["max_price"] == 300.0


def test_search_matches_title_description_and_artist(client):
    by_title = client.get("/api/items?q=swan").get_json()
    assert {item["slug"] for item in by_title["items"]} == {
        "swan-warm-light",
        "swan-through-willow",
    }

    by_artist = client.get("/api/items?q=Prisha").get_json()
    assert by_artist["pagination"]["total_items"] == 3
    assert all(item["artist"] == "Prisha Nandakumar" for item in by_artist["items"])


def test_search_also_matches_image_alt_text(client):
    # "mountain" appears only in alt text; the descriptions say massif/ridge.
    body = client.get("/api/items?q=mountain&per_page=100").get_json()

    matched = {item["slug"]: item for item in body["items"]}
    assert "the-massif-and-the-shore" in matched

    hit = matched["the-massif-and-the-shore"]
    assert "mountain" not in hit["title"].lower()
    assert "mountain" not in hit["description"].lower()
    assert "mountain" in hit["images"][0]["alt"].lower()


def test_search_does_not_duplicate_rows_matching_several_fields(client):
    # "swan" hits title, description and alt text on the same rows; the EXISTS
    # subquery must not turn that into duplicate results.
    body = client.get("/api/items?q=swan&per_page=100").get_json()
    slugs = [item["slug"] for item in body["items"]]

    assert len(slugs) == len(set(slugs))
    assert body["pagination"]["total_items"] == len(slugs)


def test_created_at_is_explicit_utc(client):
    created_at = client.get("/api/items").get_json()["items"][0]["created_at"]

    assert created_at.endswith("Z")
    datetime.fromisoformat(created_at.replace("Z", "+00:00"))


def test_search_treats_wildcards_literally(client):
    body = client.get("/api/items?q=%25").get_json()
    assert body["pagination"]["total_items"] == 0


def test_category_filter_is_case_insensitive(client):
    body = client.get("/api/items?category=wildlife&per_page=100").get_json()

    assert body["items"]
    assert all(item["category"] == "Wildlife" for item in body["items"])


def test_categories_endpoint_counts_match_the_listing(client):
    categories = client.get("/api/categories").get_json()["categories"]

    assert sum(entry["item_count"] for entry in categories) == CATALOG_SIZE
    for entry in categories:
        listing = client.get(
            f"/api/items?category={entry['name']}&per_page=100"
        ).get_json()
        assert listing["pagination"]["total_items"] == entry["item_count"]


def test_get_item_by_id_and_slug(client):
    listed = client.get("/api/items").get_json()["items"][0]

    by_id = client.get(f"/api/items/{listed['id']}").get_json()["item"]
    by_slug = client.get(f"/api/items/{listed['slug']}").get_json()["item"]

    assert by_id == by_slug == listed


def test_missing_item_returns_json_404(client):
    response = client.get("/api/items/does-not-exist")

    assert response.status_code == 404
    assert response.get_json()["error"]["status"] == 404


def test_unknown_route_returns_json_not_html(client):
    response = client.get("/api/nope")

    assert response.status_code == 404
    assert response.mimetype == "application/json"


def test_prices_are_stable_across_rebuilds(client):
    from app.catalog import assign_prices

    first = assign_prices()
    assert assign_prices() == first
    assert all(PRICE_MIN_CENTS <= cents <= PRICE_MAX_CENTS for cents in first.values())


def test_seeding_twice_does_not_duplicate_rows(app):
    from app.seed import artwork_count, seed_database

    assert artwork_count() == CATALOG_SIZE
    assert seed_database() == 0
    assert artwork_count() == CATALOG_SIZE


class TestCors:
    def test_wildcard_origin_by_default(self, client):
        response = client.get("/api/items", headers={"Origin": "http://localhost:3000"})
        assert response.headers["Access-Control-Allow-Origin"] == "*"

    def test_preflight_is_answered(self, client):
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
        app.config["CORS_ORIGINS"] = ["http://localhost:3000"]

        allowed = client.get("/api/items", headers={"Origin": "http://localhost:3000"})
        assert allowed.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
        assert "Origin" in allowed.headers["Vary"]

        blocked = client.get("/api/items", headers={"Origin": "http://evil.example"})
        assert "Access-Control-Allow-Origin" not in blocked.headers


class TestBadInput:
    def test_non_integer_page(self, client):
        response = client.get("/api/items?page=abc")
        assert response.status_code == 400
        assert "page" in response.get_json()["error"]["message"]

    def test_per_page_above_maximum(self, client):
        response = client.get("/api/items?per_page=500")
        assert response.status_code == 400

    def test_unknown_sort_lists_the_valid_options(self, client):
        response = client.get("/api/items?sort=cheapest")
        assert response.status_code == 400
        assert "price_asc" in response.get_json()["error"]["details"]["allowed"]

    def test_inverted_price_range(self, client):
        response = client.get("/api/items?min_price=400&max_price=200")
        assert response.status_code == 400

    def test_negative_price(self, client):
        assert client.get("/api/items?min_price=-5").status_code == 400

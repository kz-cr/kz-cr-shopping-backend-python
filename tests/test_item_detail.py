from __future__ import annotations

from app.catalog import CATALOG

CATALOG_SIZE = len(CATALOG)


def _detail(client, identifier, query=""):
    response = client.get(f"/api/items/{identifier}/detail{query}")
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def test_detail_embeds_the_full_listing_payload(client):
    """Keep the item object identical to the listing's, plus the extra fields."""
    listed = client.get("/api/items").get_json()["items"][0]

    item = _detail(client, listed["slug"])["item"]

    assert {key: item[key] for key in listed} == listed
    assert item["image_count"] == len(item["images"])


def test_detail_resolves_by_id_and_slug(client):
    listed = client.get("/api/items").get_json()["items"][0]

    assert _detail(client, listed["id"]) == _detail(client, listed["slug"])


def test_artist_context_matches_the_artist_listing(client):
    """Report artist counts and prices that agree with ?artist= on the listing."""
    item = client.get("/api/items?q=Prisha").get_json()["items"][0]

    artist = _detail(client, item["slug"])["artist"]
    listing = client.get(
        f"/api/items?artist={artist['name']}&per_page=100"
    ).get_json()
    works = listing["items"]

    assert artist["name"] == item["artist"]
    assert artist["item_count"] == listing["pagination"]["total_items"] == len(works)
    assert artist["price_range"]["min_cents"] == min(w["price_cents"] for w in works)
    assert artist["price_range"]["max_cents"] == max(w["price_cents"] for w in works)
    assert artist["price_range"]["currency"] == item["currency"]
    assert artist["years"]["earliest"] == min(w["year"] for w in works)
    assert artist["years"]["latest"] == max(w["year"] for w in works)


def test_artist_other_works_exclude_the_piece_itself(client):
    """Fill the artist rail with the artist's other pieces only."""
    item = client.get("/api/items?q=Prisha").get_json()["items"][0]

    artist = _detail(client, item["slug"])["artist"]

    assert artist["other_works"], "expected a multi-piece artist for this fixture"
    assert artist["other_work_count"] == artist["item_count"] - 1
    assert all(work["artist"] == item["artist"] for work in artist["other_works"])
    assert item["id"] not in {work["id"] for work in artist["other_works"]}


def test_category_context_matches_the_categories_endpoint(client):
    item = client.get("/api/items").get_json()["items"][0]

    category = _detail(client, item["slug"])["category"]
    counts = {
        entry["name"]: entry["item_count"]
        for entry in client.get("/api/categories").get_json()["categories"]
    }

    assert category["name"] == item["category"]
    assert category["item_count"] == counts[item["category"]]
    price_range = category["price_range"]
    assert price_range["min"] <= item["price"] <= price_range["max"]


def test_similar_items_share_the_category_and_omit_the_piece(client):
    item = client.get("/api/items").get_json()["items"][0]

    body = _detail(client, item["slug"])
    similar = body["similar"]

    assert len(similar) == min(4, body["category"]["item_count"] - 1)
    assert all(row["category"] == item["category"] for row in similar)
    assert item["id"] not in {row["id"] for row in similar}


def test_related_limit_bounds_both_rails(client):
    item = client.get("/api/items?q=Prisha").get_json()["items"][0]

    body = _detail(client, item["slug"], "?related_limit=1")
    assert len(body["similar"]) == 1
    assert len(body["artist"]["other_works"]) == 1

    none = _detail(client, item["slug"], "?related_limit=0")
    assert none["similar"] == []
    assert none["artist"]["other_works"] == []
    # Counts still describe the whole catalogue even with the rails switched off.
    assert none["artist"]["item_count"] == body["artist"]["item_count"]


def test_related_limit_rejects_out_of_range_values(client):
    slug = client.get("/api/items").get_json()["items"][0]["slug"]

    for query in ("?related_limit=99", "?related_limit=-1", "?related_limit=many"):
        response = client.get(f"/api/items/{slug}/detail{query}")
        assert response.status_code == 400, query
        assert "related_limit" in response.get_json()["error"]["message"]


def test_navigation_walks_the_curated_order(client):
    """Chain previous/next across the catalogue in the listing's default order."""
    curated = [
        item["id"] for item in client.get("/api/items?per_page=100").get_json()["items"]
    ]

    first = _detail(client, curated[0])["navigation"]
    assert first["position"] == 1
    assert first["total_items"] == CATALOG_SIZE
    assert first["previous"] is None
    assert first["next"]["id"] == curated[1]

    middle = _detail(client, curated[1])["navigation"]
    assert middle["position"] == 2
    assert middle["previous"]["id"] == curated[0]
    assert middle["next"]["id"] == curated[2]

    last = _detail(client, curated[-1])["navigation"]
    assert last["position"] == CATALOG_SIZE
    assert last["previous"]["id"] == curated[-2]
    assert last["next"] is None


def test_related_references_carry_a_usable_image(client):
    """Give every rail card a thumbnail and alt text to render with."""
    item = client.get("/api/items?q=Prisha").get_json()["items"][0]
    body = _detail(client, item["slug"])

    rails = body["similar"] + body["artist"]["other_works"] + [body["navigation"]["next"]]
    assert rails

    for row in rails:
        image = row["primary_image"]
        assert "/thumbs/" in image["thumbnail_url"], row["slug"]
        assert image["alt"], row["slug"]
        assert client.get(image["thumbnail_url"]).status_code == 200, row["slug"]
        # Rail cards stay compact: no description, no full image list.
        assert "description" not in row
        assert "images" not in row


def test_detail_for_a_missing_item_returns_json_404(client):
    response = client.get("/api/items/does-not-exist/detail")

    assert response.status_code == 404
    assert response.mimetype == "application/json"
    assert response.get_json()["error"]["status"] == 404


def test_index_advertises_the_detail_route(client):
    endpoints = client.get("/").get_json()["endpoints"]

    assert endpoints["item_detail"] == "/api/items/<id-or-slug>/detail"

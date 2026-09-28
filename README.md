# kz-cr-shopping-backend-python

Python Backend for KZ-CR demo — an online art gallery.

A self-contained Flask API serving a catalogue of 30 photographic prints. The
SQLite database is created and seeded on first run and the images are served by
the app itself, so there is nothing to provision and no network access needed at
runtime.

## Quick start

```bash
./run.sh
```

That is the whole setup: it creates the virtualenv, installs dependencies,
seeds `instance/gallery.db` and serves on <http://127.0.0.1:5000>. It is safe to
re-run — every step is skipped when it is already done.

```bash
curl http://127.0.0.1:5000/api/items
```

| Flag | Effect |
| --- | --- |
| `--debug` | Auto-reload and the Flask debugger (refuses non-loopback hosts) |
| `--reset` | Drop and reseed the database from `app/catalog.py` |
| `--fetch-images` | Re-download the catalogue images |
| `--setup-only` | Prepare the checkout without starting the server |
| `--host` / `--port` | Change the bind address (default `127.0.0.1:5000`) |

Or do it by hand:

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python wsgi.py
```

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/items` | Paginated, filterable, sortable listing |
| `GET` | `/api/items/<id-or-slug>` | A single piece |
| `GET` | `/api/items/<id-or-slug>/detail` | A single piece plus its artist, category, related pieces and neighbours |
| `GET` | `/api/categories` | Categories in the catalogue, with counts |
| `GET` | `/health` | Liveness check |
| `GET` | `/static/images/...` | The artwork images |

### `GET /api/items`

| Parameter | Default | Notes |
| --- | --- | --- |
| `page` | `1` | |
| `per_page` | `12` | Max 100 |
| `q` | — | Case-insensitive match on title, description, artist and image alt text |
| `category` | — | Case-insensitive exact match, e.g. `Landscape` |
| `artist` | — | Case-insensitive exact match |
| `min_price` / `max_price` | — | In dollars, e.g. `min_price=150.50` |
| `sort` | `curated` | `curated`, `price_asc`, `price_desc`, `title_asc`, `title_desc`, `newest` |

Bad input is a `400` with a JSON body rather than a silently ignored filter:

```json
{
  "error": {
    "status": 400,
    "message": "'sort' must be one of ['curated', 'newest', 'price_asc', 'price_desc', 'title_asc', 'title_desc'], got 'cheapest'",
    "details": { "allowed": ["curated", "newest", "price_asc", "price_desc", "title_asc", "title_desc"] }
  }
}
```

### Response shape

```json
{
  "items": [
    {
      "id": 1,
      "slug": "blue-sedan-wrapped",
      "title": "Blue Sedan, Wrapped",
      "description": "A die-cast sedan parked on the ribbon of a red gift box ...",
      "artist": "Marta Vreeland",
      "year": 2019,
      "medium": "Archival pigment print",
      "category": "Still Life",
      "price": 292.0,
      "price_cents": 29200,
      "currency": "USD",
      "images": [
        {
          "id": 1,
          "url": "http://127.0.0.1:5000/static/images/blue-sedan-wrapped.jpg",
          "thumbnail_url": "http://127.0.0.1:5000/static/images/thumbs/blue-sedan-wrapped.jpg",
          "alt": "A small blue toy car on a red gift box in front of warm Christmas bokeh",
          "position": 0,
          "is_primary": true
        }
      ],
      "primary_image": { "...": "same object as images[0]" },
      "created_at": "2026-09-25T05:37:16.172553Z"
    }
  ],
  "pagination": {
    "page": 1, "per_page": 12, "total_items": 30,
    "total_pages": 3, "has_previous": false, "has_next": true
  },
  "applied": { "q": null, "category": null, "artist": null, "min_price": null, "max_price": null, "sort": "curated" }
}
```

`GET /api/items/<id-or-slug>` returns the same object under an `item` key, and a
JSON `404` when nothing matches:

```json
{ "error": { "status": 404, "message": "No item matching 'does-not-exist'" } }
```

### `GET /api/items/<id-or-slug>/detail`

What a product page needs when a listing card is clicked, in one request
instead of the several filtered listing calls it would otherwise take. The
`item` key is the listing object verbatim, plus `image_count`; everything else
is context derived from the same catalogue.

| Parameter | Default | Notes |
| --- | --- | --- |
| `related_limit` | `4` | Pieces per rail (`similar` and `artist.other_works`). `0` to `12`; `0` returns the counts without the rails |

```json
{
  "item": { "...": "the listing object", "image_count": 1 },
  "artist": {
    "name": "Prisha Nandakumar",
    "item_count": 3,
    "other_work_count": 2,
    "years": { "earliest": 2019, "latest": 2022 },
    "price_range": { "min": 218.5, "max": 368.5, "min_cents": 21850, "max_cents": 36850, "currency": "USD" },
    "other_works": [ { "...": "compact item reference" } ]
  },
  "category": {
    "name": "Wildlife",
    "item_count": 8,
    "price_range": { "min": 110.5, "max": 469.5, "min_cents": 11050, "max_cents": 46950, "currency": "USD" }
  },
  "similar": [ { "...": "compact item reference" } ],
  "navigation": {
    "position": 16,
    "total_items": 30,
    "previous": { "...": "compact item reference" },
    "next": { "...": "compact item reference" }
  }
}
```

A compact item reference is `id`, `slug`, `title`, `artist`, `year`,
`category`, `price`, `price_cents`, `currency` and `primary_image` — enough to
draw a card and link to it, without the description or the full image list.

Notes for the frontend:

- `artist.item_count` and `category.item_count` agree with
  `/api/items?artist=...` and `/api/categories`, so a "View all 8 in Wildlife"
  link can be labelled without a second request.
- `similar` and `artist.other_works` are independent lists and may overlap: a
  small category would otherwise come back empty for an artist who dominates
  it. Both exclude the piece being viewed.
- `navigation` follows the listing's `curated` sort, so previous/next arrows
  walk the catalogue in the order the grid showed. `position` is 1-based.
- A missing piece is the same JSON `404` as `/api/items/<id-or-slug>`.

Notes for the frontend:

- `price` is a convenience float; `price_cents` is the authoritative integer.
- `images` is an array even though the demo ships one photo per piece, so a
  carousel does not need a schema change later. `primary_image` is a shortcut to
  the first one for grid views.
- `thumbnail_url` points at a 400px version — use it in listings, not `url`.

## Layout

```
app/
  __init__.py     application factory, CLI, first-run bootstrap
  catalog.py      the 30 pieces — single source of truth for seed + images
  config.py       development / testing / production configs
  cors.py         cross-origin headers for browser frontends
  models.py       Artwork, ArtworkImage
  schemas.py      model -> JSON
  seed.py         catalogue -> database
  errors.py       one JSON error shape for every failure
  api/
    items.py      the listing, detail and category endpoints
    params.py     query-string parsing and validation
  static/images/  vendored artwork images (+ thumbs/)
scripts/
  fetch_images.py re-download and re-process the images
tests/
run.sh            set up and start the app locally
```

## Data

Photographs come from the public
[yavuzceliker/sample-images](https://github.com/yavuzceliker/sample-images)
repository. They are downloaded once, resized (1400px long edge, plus a 400px
thumbnail) and committed under `app/static/images/`, so the backend runs
offline.

Titles, descriptions, artist names, years and media are written for this demo
and are **fictional** — each one describes the photograph it is attached to, but
none of the artists are real people. Prices are drawn randomly between $100 and
$500 from a fixed seed (`PRICE_SEED` in `app/catalog.py`), so rebuilding the
database reproduces the same prices.

To change the catalogue, edit `CATALOG` in `app/catalog.py`, then:

```bash
python scripts/fetch_images.py && flask --app wsgi init-db --reset
```

## Development

```bash
pip install -r requirements-dev.txt
python -m pytest
```

| Variable | Default | Purpose |
| --- | --- | --- |
| `FLASK_CONFIG` | `development` | `development`, `testing` or `production` |
| `DATABASE_URL` | `sqlite:///instance/gallery.db` | |
| `AUTO_SEED` | `true` | Create and seed the database at startup when empty |
| `CORS_ORIGINS` | `*` | Comma-separated allowlist of browser origins |

CORS is open by default so a frontend dev server on another port can call the
API straight away. Narrow it before this goes anywhere real:

```bash
CORS_ORIGINS=http://localhost:3000 python wsgi.py
```

`flask --app wsgi init-db [--reset]` seeds explicitly.

## Roadmap

Still to come:

- Auth, cart and checkout
- Write endpoints — every route here is a read

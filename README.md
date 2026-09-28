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
    items.py      the listing endpoints
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

"""Application factory for the KZ-CR art gallery backend."""

from __future__ import annotations

import click
from flask import Flask, jsonify

from .config import BaseConfig, resolve_config
from .cors import register_cors
from .errors import register_error_handlers
from .extensions import db
from .paths import INSTANCE_DIR, STATIC_DIR

__all__ = ["create_app", "db"]


def create_app(config: str | type[BaseConfig] | None = None) -> Flask:
    app = Flask(
        __name__,
        static_folder=str(STATIC_DIR),
        static_url_path="/static",
        instance_path=str(INSTANCE_DIR),
    )
    app.config.from_object(config if isinstance(config, type) else resolve_config(config))
    app.json.sort_keys = False

    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    register_cors(app)
    register_error_handlers(app)

    from .api import api_bp

    app.register_blueprint(api_bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/")
    def index():
        return jsonify(
            {
                "name": "KZ-CR Art Gallery API",
                "endpoints": {
                    "items": "/api/items",
                    "item": "/api/items/<id-or-slug>",
                    "health": "/health",
                },
            }
        )

    _register_cli(app)
    _bootstrap(app)
    return app


def _bootstrap(app: Flask) -> None:
    """Create the schema and load the catalogue on first run."""
    if not app.config.get("AUTO_SEED", False):
        return

    from .seed import missing_image_files, seed_database

    with app.app_context():
        db.create_all()
        created = seed_database()
        if created:
            app.logger.info("Seeded %s artworks", created)
        missing = missing_image_files()
        if missing:
            app.logger.warning(
                "%s catalogue image(s) not vendored yet (e.g. %s); "
                "run `python scripts/fetch_images.py`",
                len(missing),
                missing[0],
            )


def _register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    @click.option("--reset", is_flag=True, help="Drop existing rows before seeding.")
    def init_db(reset: bool) -> None:
        """Create the schema and load the catalogue."""
        from .seed import artwork_count, seed_database

        db.create_all()
        created = seed_database(reset=reset)
        if created:
            click.echo(f"Seeded {created} artworks.")
        else:
            # Not a problem: the first-run bootstrap usually got here first.
            click.echo(
                f"Database ready: {artwork_count()} artworks. "
                "Pass --reset to reload from app/catalog.py."
            )

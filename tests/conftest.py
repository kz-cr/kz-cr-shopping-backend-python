from __future__ import annotations

import pytest

from app import create_app
from app.config import TestingConfig


@pytest.fixture()
def app():
    """Provide a seeded test app with an active in-memory database context."""
    app = create_app(TestingConfig)
    # The in-memory database lives for as long as the app context that created
    # it, so hand the tests a context that stays open.
    with app.app_context():
        yield app


@pytest.fixture()
def client(app):
    """Provide an HTTP client bound to the seeded test app."""
    return app.test_client()

from __future__ import annotations

import pytest

from app import create_app
from app.config import TestingConfig


@pytest.fixture()
def app():
    app = create_app(TestingConfig)
    # The in-memory database lives for as long as the app context that created
    # it, so hand the tests a context that stays open.
    with app.app_context():
        yield app


@pytest.fixture()
def client(app):
    return app.test_client()

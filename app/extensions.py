"""Flask extension singletons, instantiated here to avoid circular imports."""

from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

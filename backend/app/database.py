"""
SQLAlchemy engine + session management.

Single Postgres database used for both local dev and deployment (same
DATABASE_URL shape, just pointed at different hosts via env vars).
"""
import uuid

from sqlalchemy import create_engine, CHAR, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.config import settings


class GUID(TypeDecorator):
    """Platform-independent UUID column.

    Uses Postgres's native UUID type in production, and a plain 36-char
    string everywhere else. models.py used to import
    sqlalchemy.dialects.postgresql.UUID directly, which is correct for the
    deployed Postgres database but made every primary/foreign key
    unusable against SQLite -- meaning the backend's test suite would have
    had to stand up a real Postgres server just to run, which is exactly
    the kind of friction that keeps a test suite from ever getting run.
    This keeps Postgres as the one production database (nothing about
    deployment changes) while letting tests run against a fast, disposable
    SQLite database instead.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID())
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if not isinstance(value, uuid.UUID):
            return str(uuid.UUID(str(value)))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return str(value)


_is_sqlite = settings.database_url.startswith("sqlite")

_engine_kwargs = {"pool_pre_ping": True}
if _is_sqlite:
    # In-memory/file SQLite (used by tests) needs check_same_thread off
    # since FastAPI's TestClient and the app talk to it from different
    # threads, and a StaticPool so every connection shares the same
    # in-memory database instead of each getting a blank one.
    _engine_kwargs = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }

engine = create_engine(settings.database_url, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

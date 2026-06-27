from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import PROJECT_ROOT, get_settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


settings = get_settings()
database_url = settings.database_url
if database_url.startswith("sqlite:///./"):
    database_url = f"sqlite:///{(PROJECT_ROOT / database_url.removeprefix('sqlite:///./')).as_posix()}"
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def init_db() -> None:
    """Create database tables for local MVP usage."""

    from app.models import records  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _upgrade_sqlite_schema()


def _upgrade_sqlite_schema() -> None:
    """Apply tiny additive upgrades for local SQLite databases.

    The MVP does not use Alembic yet. This keeps existing demo databases usable
    when we add nullable/defaulted columns during learning iterations.
    """

    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    upgrades: dict[str, dict[str, str]] = {
        "strategy_cards": {
            "evidence_count": "INTEGER DEFAULT 0 NOT NULL",
            "sample_size": "INTEGER DEFAULT 0 NOT NULL",
            "confidence": "VARCHAR(30) DEFAULT 'low' NOT NULL",
            "confidence_reason": "TEXT DEFAULT '' NOT NULL",
        },
        "cluster_results": {
            "method": "VARCHAR(40) DEFAULT 'rules' NOT NULL",
            "is_noise": "BOOLEAN DEFAULT 0 NOT NULL",
            "representative_comments": "JSON DEFAULT '[]' NOT NULL",
        },
    }
    with engine.begin() as connection:
        for table_name, columns in upgrades.items():
            if table_name not in existing_tables:
                continue
            current_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, ddl in columns.items():
                if column_name not in current_columns:
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"))


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

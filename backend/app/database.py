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
        "tasks": {
            "board": "VARCHAR(80) DEFAULT 'nba' NOT NULL",
            "match_name": "VARCHAR(240) DEFAULT '' NOT NULL",
            "home_team": "VARCHAR(120) DEFAULT '' NOT NULL",
            "away_team": "VARCHAR(120) DEFAULT '' NOT NULL",
            "match_stage": "VARCHAR(120) DEFAULT '' NOT NULL",
            "match_date": "VARCHAR(40) DEFAULT '' NOT NULL",
            "thread_urls": "JSON DEFAULT '[]' NOT NULL",
            "news_urls": "JSON DEFAULT '[]' NOT NULL",
            "news_context": "TEXT DEFAULT '' NOT NULL",
            "enable_image_analysis": "BOOLEAN DEFAULT 1 NOT NULL",
            "max_image_comments": "INTEGER DEFAULT 6 NOT NULL",
            "llm_mode": "VARCHAR(30) DEFAULT 'configured' NOT NULL",
            "upload_id": "VARCHAR(36)",
            "field_mapping": "JSON DEFAULT '{}' NOT NULL",
            "error_message": "TEXT DEFAULT '' NOT NULL",
            "cancel_requested": "BOOLEAN DEFAULT 0 NOT NULL",
            "run_attempt": "INTEGER DEFAULT 0 NOT NULL",
            "queued_at": "DATETIME",
            "started_at": "DATETIME",
            "finished_at": "DATETIME",
        },
        "clean_comments": {"cluster_id": "INTEGER"},
        "raw_comments": {
            "image_urls": "JSON DEFAULT '[]' NOT NULL",
            "image_analysis": "JSON DEFAULT '{}' NOT NULL",
        },
        "insight_reports": {
            "key_viewpoints": "JSON DEFAULT '[]' NOT NULL",
            "controversies": "JSON DEFAULT '[]' NOT NULL",
            "news_context_summary": "TEXT DEFAULT '' NOT NULL",
            "context_alignment": "JSON DEFAULT '[]' NOT NULL",
            "fact_opinion_gaps": "JSON DEFAULT '[]' NOT NULL",
            "context_media": "JSON DEFAULT '[]' NOT NULL",
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

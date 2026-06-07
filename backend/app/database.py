from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    func,
)
from sqlalchemy.engine import Engine

from .settings import get_settings


metadata = MetaData()

jobs = Table(
    "jobs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("status", String(40), nullable=False),
    Column("repo_full_name", String(255), nullable=False),
    Column("pr_number", Integer, nullable=False),
    Column("pr_title", Text, nullable=False),
    Column("pr_url", Text),
    Column("pr_body", Text),
    Column("merged_by", String(255)),
    Column("changed_files", Text, nullable=False),
    Column("diff", Text, nullable=False),
    Column("mapped_module", String(255)),
    Column("notion_target_id", Text),
    Column("current_docs", Text),
    Column("ai_summary", Text),
    Column("ai_patch", Text),
    Column("ai_confidence", Float),
    Column("reviewer_notes", Text),
    Column("final_content", Text),
    Column("error", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("published_at", DateTime(timezone=True)),
)

audit_logs = Table(
    "audit_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("job_id", Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
    Column("action", String(80), nullable=False),
    Column("actor", String(255)),
    Column("comment", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

_engine: Engine | None = None
_schema_ready = False


def database_url() -> str:
    settings = get_settings()
    if settings.database_url:
        return normalize_database_url(settings.database_url)
    return f"sqlite:///{Path(settings.database_path).resolve()}"


def migration_database_url() -> str:
    settings = get_settings()
    if settings.direct_url:
        return normalize_database_url(settings.direct_url)
    return database_url()


def normalize_database_url(url: str) -> str:
    cleaned = remove_prisma_only_query_params(url.strip().strip('"').strip("'"))
    if cleaned.startswith("postgres://"):
        return "postgresql+psycopg://" + cleaned.removeprefix("postgres://")
    if cleaned.startswith("postgresql://"):
        return "postgresql+psycopg://" + cleaned.removeprefix("postgresql://")
    return cleaned


def remove_prisma_only_query_params(url: str) -> str:
    parts = urlsplit(url)
    if not parts.query:
        return url
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "pgbouncer"]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def get_engine() -> Engine:
    global _engine, _schema_ready
    if _engine is None:
        url = database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
    if not _schema_ready:
        metadata.create_all(_engine)
        _schema_ready = True
    return _engine


def reset_engine_for_tests() -> None:
    global _engine, _schema_ready
    if _engine is not None:
        _engine.dispose()
        _engine = None
    _schema_ready = False


def init_db() -> None:
    url = migration_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
    try:
        metadata.create_all(engine)
    finally:
        engine.dispose()

from app.database import normalize_database_url


def test_normalize_database_url_converts_postgresql_scheme():
    assert (
        normalize_database_url("postgresql://user:pass@example.supabase.co:5432/postgres")
        == "postgresql+psycopg://user:pass@example.supabase.co:5432/postgres"
    )


def test_normalize_database_url_keeps_sqlite_scheme():
    assert normalize_database_url("sqlite:///local.db") == "sqlite:///local.db"

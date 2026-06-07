from app.database import migration_database_url, normalize_database_url, remove_prisma_only_query_params


def test_normalize_database_url_converts_postgresql_scheme():
    assert (
        normalize_database_url("postgresql://user:pass@example.supabase.co:5432/postgres")
        == "postgresql+psycopg://user:pass@example.supabase.co:5432/postgres"
    )


def test_normalize_database_url_keeps_sqlite_scheme():
    assert normalize_database_url("sqlite:///local.db") == "sqlite:///local.db"


def test_normalize_database_url_removes_prisma_pgbouncer_flag():
    assert (
        normalize_database_url("postgresql://u:p@host:6543/postgres?pgbouncer=true&sslmode=require")
        == "postgresql+psycopg://u:p@host:6543/postgres?sslmode=require"
    )


def test_remove_prisma_only_query_params_keeps_non_prisma_params():
    assert (
        remove_prisma_only_query_params("postgresql://u:p@host/db?pgbouncer=true&connect_timeout=10")
        == "postgresql://u:p@host/db?connect_timeout=10"
    )

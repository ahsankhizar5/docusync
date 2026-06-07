from app.database import database_url, init_db


def main() -> None:
    init_db()
    print(f"DocuSync tables are ready on {database_url().split('@')[-1]}")


if __name__ == "__main__":
    main()

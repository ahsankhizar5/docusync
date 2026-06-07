import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import database_url, init_db


def main() -> None:
    init_db()
    print(f"DocuSync tables are ready on {database_url().split('@')[-1]}")


if __name__ == "__main__":
    main()

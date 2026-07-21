from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.database.catalog_seed import seed_catalog
from app.database.connection import DEFAULT_DB_PATH


def main() -> None:
    counts = seed_catalog()

    print(f"Database: {DEFAULT_DB_PATH}")
    print("Catalog seed complete:")

    for table, count in counts.items():
        print(f"  - {table}: {count}")


if __name__ == "__main__":
    main()

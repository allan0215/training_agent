from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.database.connection import DEFAULT_DB_PATH
from app.database.migrations import run_migrations


def main() -> None:
    applied = run_migrations()

    print(f"Database: {DEFAULT_DB_PATH}")

    if applied:
        print("Applied migrations:")

        for filename in applied:
            print(f"  - {filename}")
    else:
        print("No pending migrations.")


if __name__ == "__main__":
    main()

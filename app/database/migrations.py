from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from app.database.connection import (
    DEFAULT_DB_PATH,
    DatabasePath,
    get_connection,
)


MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _ensure_migration_table(
    connection: sqlite3.Connection,
) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            filename TEXT NOT NULL UNIQUE,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    connection.commit()


def _checksum(content: str) -> str:
    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def _sql_literal(value: str) -> str:
    """
    내부적으로 생성한 문자열을 SQL 문자열 리터럴로 변환한다.

    마이그레이션 파일명과 체크섬에만 사용한다.
    사용자 입력에는 사용하지 않는다.
    """
    return "'" + value.replace("'", "''") + "'"


def run_migrations(
    db_path: DatabasePath | None = None,
    migrations_dir: Path | None = None,
) -> list[str]:
    """
    아직 적용되지 않은 SQL 마이그레이션을 순서대로 실행한다.

    반환값:
        이번 실행에서 새로 적용된 파일명 목록
    """

    target_db = db_path or DEFAULT_DB_PATH
    target_dir = migrations_dir or MIGRATIONS_DIR

    if not target_dir.exists():
        raise FileNotFoundError(
            f"Migration directory not found: {target_dir}"
        )

    migration_files = sorted(target_dir.glob("*.sql"))

    seen_versions: set[str] = set()

    for migration_file in migration_files:
        parts = migration_file.stem.split("_", 1)

        if len(parts) != 2 or not parts[0].isdigit():
            raise ValueError(
                "Migration filename must follow "
                f"'001_description.sql': {migration_file.name}"
            )

        version = parts[0]

        if version in seen_versions:
            raise ValueError(
                f"Duplicate migration version: {version}"
            )

        seen_versions.add(version)

    applied_now: list[str] = []

    with get_connection(target_db) as connection:
        _ensure_migration_table(connection)

        applied = {
            row["version"]: row
            for row in connection.execute(
                """
                SELECT
                    version,
                    filename,
                    checksum
                FROM schema_migrations;
                """
            )
        }

        for migration_file in migration_files:
            version = migration_file.stem.split("_", 1)[0]
            sql = migration_file.read_text(encoding="utf-8")
            checksum = _checksum(sql)

            existing = applied.get(version)

            if existing is not None:
                if existing["checksum"] != checksum:
                    raise RuntimeError(
                        "An already-applied migration was modified: "
                        f"{migration_file.name}"
                    )

                continue

            filename_literal = _sql_literal(
                migration_file.name
            )
            version_literal = _sql_literal(version)
            checksum_literal = _sql_literal(checksum)

            migration_script = f"""
            BEGIN IMMEDIATE;

            {sql}

            INSERT INTO schema_migrations (
                version,
                filename,
                checksum
            )
            VALUES (
                {version_literal},
                {filename_literal},
                {checksum_literal}
            );

            COMMIT;
            """

            try:
                connection.executescript(migration_script)
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise

            applied_now.append(migration_file.name)

    return applied_now

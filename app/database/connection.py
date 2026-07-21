from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import TypeAlias


DatabasePath: TypeAlias = str | Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "training_agent.db"


def get_connection(
    db_path: DatabasePath | None = None,
) -> sqlite3.Connection:
    """
    SQLite 연결을 생성한다.

    모든 연결에서:
    - 외래키 검사를 활성화한다.
    - 행을 sqlite3.Row 형태로 반환한다.
    - 최대 5초 동안 DB 잠금 해제를 기다린다.
    - 파일 DB에는 WAL 모드를 사용한다.
    """

    configured_path = os.getenv("TRAINING_AGENT_DB_PATH")

    target: DatabasePath = (
        db_path
        if db_path is not None
        else configured_path or DEFAULT_DB_PATH
    )

    database = str(target)

    if database != ":memory:":
        path = Path(database).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        database = str(path)

    connection = sqlite3.connect(
        database,
        timeout=30.0,
    )

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON;")
    connection.execute("PRAGMA busy_timeout = 5000;")

    if database != ":memory:":
        connection.execute("PRAGMA journal_mode = WAL;")

    return connection

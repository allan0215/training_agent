from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database.connection import get_connection
from app.database.migrations import (
    MIGRATIONS_DIR,
    run_migrations,
)


class DatabaseFoundationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = (
            Path(self.temp_directory.name)
            / "test_training_agent.db"
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_connection_enables_foreign_keys(self) -> None:
        with get_connection(self.db_path) as connection:
            enabled = connection.execute(
                "PRAGMA foreign_keys;"
            ).fetchone()[0]

        self.assertEqual(enabled, 1)

    def test_migrations_are_idempotent(self) -> None:
        first_run = run_migrations(
            db_path=self.db_path,
            migrations_dir=MIGRATIONS_DIR,
        )

        second_run = run_migrations(
            db_path=self.db_path,
            migrations_dir=MIGRATIONS_DIR,
        )

        self.assertEqual(
            first_run,
            ["001_core.sql"],
        )
        self.assertEqual(second_run, [])

        with get_connection(self.db_path) as connection:
            tables = {
                row["name"]
                for row in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table';
                    """
                )
            }

        self.assertIn("users", tables)
        self.assertIn("source_messages", tables)
        self.assertIn("schema_migrations", tables)

    def test_foreign_key_violation_is_rejected(
        self,
    ) -> None:
        run_migrations(
            db_path=self.db_path,
            migrations_dir=MIGRATIONS_DIR,
        )

        with self.assertRaises(sqlite3.IntegrityError):
            with get_connection(self.db_path) as connection:
                connection.execute(
                    """
                    INSERT INTO source_messages (
                        discord_message_id,
                        discord_channel_id,
                        user_id,
                        message_text
                    )
                    VALUES (?, ?, ?, ?);
                    """,
                    (
                        "message-1",
                        "channel-1",
                        999999,
                        "invalid user",
                    ),
                )

        with get_connection(self.db_path) as connection:
            count = connection.execute(
                """
                SELECT COUNT(*)
                FROM source_messages;
                """
            ).fetchone()[0]

        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()

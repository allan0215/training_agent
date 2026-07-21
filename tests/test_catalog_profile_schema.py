from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database.connection import get_connection
from app.database.migrations import run_migrations


class CatalogProfileSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = (
            Path(self.temp_directory.name)
            / "test_training_agent.db"
        )

        run_migrations(db_path=self.db_path)

        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (
                    discord_user_id,
                    display_name
                )
                VALUES (?, ?);
                """,
                (
                    "discord-user-1",
                    "Test User",
                ),
            )

            self.user_id = cursor.lastrowid

            cursor = connection.execute(
                """
                INSERT INTO exercises (
                    canonical_name,
                    korean_name,
                    category
                )
                VALUES (?, ?, ?);
                """,
                (
                    "Back Squat",
                    "백스쿼트",
                    "strength",
                ),
            )

            self.exercise_id = cursor.lastrowid

            self.squat_pattern_id = connection.execute(
                """
                SELECT id
                FROM movement_patterns
                WHERE code = 'squat';
                """
            ).fetchone()["id"]

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_movement_patterns_are_seeded(self) -> None:
        with get_connection(self.db_path) as connection:
            pattern_codes = {
                row["code"]
                for row in connection.execute(
                    """
                    SELECT code
                    FROM movement_patterns;
                    """
                )
            }

        self.assertIn("squat", pattern_codes)
        self.assertIn("horizontal_pull", pattern_codes)
        self.assertIn("vertical_push", pattern_codes)
        self.assertIn("core", pattern_codes)

    def test_invalid_preference_score_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            with get_connection(self.db_path) as connection:
                connection.execute(
                    """
                    INSERT INTO exercise_preferences (
                        user_id,
                        exercise_id,
                        preference_score
                    )
                    VALUES (?, ?, ?);
                    """,
                    (
                        self.user_id,
                        self.exercise_id,
                        3,
                    ),
                )

    def test_restriction_requires_target(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            with get_connection(self.db_path) as connection:
                connection.execute(
                    """
                    INSERT INTO exercise_restrictions (
                        user_id,
                        restriction_level,
                        reason,
                        starts_on
                    )
                    VALUES (?, ?, ?, ?);
                    """,
                    (
                        self.user_id,
                        "avoid",
                        "Test restriction",
                        "2026-07-21",
                    ),
                )

    def test_valid_pattern_restriction_is_accepted(
        self,
    ) -> None:
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO exercise_restrictions (
                    user_id,
                    movement_pattern_id,
                    restriction_level,
                    reason,
                    starts_on
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    self.user_id,
                    self.squat_pattern_id,
                    "limit",
                    "Temporary hip discomfort",
                    "2026-07-21",
                ),
            )

            count = connection.execute(
                """
                SELECT COUNT(*)
                FROM exercise_restrictions
                WHERE user_id = ?;
                """,
                (self.user_id,),
            ).fetchone()[0]

        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()

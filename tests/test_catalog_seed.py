from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.database.catalog_seed import (
    normalize_alias,
    seed_catalog,
)
from app.database.connection import get_connection
from app.database.migrations import run_migrations


class CatalogSeedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()

        self.db_path = (
            Path(self.temp_directory.name)
            / "test_training_agent.db"
        )

        run_migrations(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_catalog_seed_is_idempotent(self) -> None:
        first = seed_catalog(self.db_path)
        second = seed_catalog(self.db_path)

        self.assertEqual(first, second)
        self.assertEqual(first["equipment"], 19)
        self.assertEqual(first["exercises"], 44)

    def test_back_squat_alias_and_pattern_exist(
        self,
    ) -> None:
        seed_catalog(self.db_path)

        with get_connection(self.db_path) as connection:
            result = connection.execute(
                """
                SELECT
                    e.canonical_name,
                    mp.code AS movement_pattern
                FROM exercise_aliases AS ea
                JOIN exercises AS e
                  ON e.id = ea.exercise_id
                JOIN exercise_movement_patterns AS emp
                  ON emp.exercise_id = e.id
                JOIN movement_patterns AS mp
                  ON mp.id = emp.movement_pattern_id
                WHERE ea.alias_normalized = ?
                  AND mp.code = 'squat';
                """,
                (normalize_alias("BS"),),
            ).fetchone()

        self.assertIsNotNone(result)
        self.assertEqual(
            result["canonical_name"],
            "Back Squat",
        )
        self.assertEqual(
            result["movement_pattern"],
            "squat",
        )

    def test_thruster_has_two_primary_patterns(
        self,
    ) -> None:
        seed_catalog(self.db_path)

        with get_connection(self.db_path) as connection:
            patterns = {
                row["code"]
                for row in connection.execute(
                    """
                    SELECT mp.code
                    FROM exercises AS e
                    JOIN exercise_movement_patterns AS emp
                      ON emp.exercise_id = e.id
                    JOIN movement_patterns AS mp
                      ON mp.id = emp.movement_pattern_id
                    WHERE e.canonical_name = 'Thruster'
                      AND emp.role = 'primary';
                    """
                )
            }

        self.assertEqual(
            patterns,
            {
                "squat",
                "vertical_push",
            },
        )


if __name__ == "__main__":
    unittest.main()

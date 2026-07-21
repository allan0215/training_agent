from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database.connection import get_connection
from app.database.migrations import run_migrations


class PlanningSchemaTests(unittest.TestCase):
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
                    "discord-user-planning",
                    "Planning Test User",
                ),
            )
            self.user_id = cursor.lastrowid

            cursor = connection.execute(
                """
                INSERT INTO locations (
                    user_id,
                    name,
                    location_type
                )
                VALUES (?, ?, ?);
                """,
                (
                    self.user_id,
                    "Test CrossFit Box",
                    "crossfit_box",
                ),
            )
            self.location_id = cursor.lastrowid

            cursor = connection.execute(
                """
                INSERT INTO exercises (
                    canonical_name,
                    korean_name,
                    category,
                    default_block_type
                )
                VALUES (?, ?, ?, ?);
                """,
                (
                    "Back Squat",
                    "백스쿼트",
                    "strength",
                    "resistance",
                ),
            )
            self.back_squat_id = cursor.lastrowid

            cursor = connection.execute(
                """
                INSERT INTO exercises (
                    canonical_name,
                    korean_name,
                    category,
                    default_block_type
                )
                VALUES (?, ?, ?, ?);
                """,
                (
                    "Thruster",
                    "스러스터",
                    "crossfit",
                    "metcon",
                ),
            )
            self.thruster_id = cursor.lastrowid

            cursor = connection.execute(
                """
                INSERT INTO programs (
                    name,
                    provider,
                    program_type
                )
                VALUES (?, ?, ?);
                """,
                (
                    "HWPO Flagship",
                    "HWPO",
                    "mixed",
                ),
            )
            self.hwpo_program_id = cursor.lastrowid

            cursor = connection.execute(
                """
                INSERT INTO programs (
                    name,
                    provider,
                    program_type
                )
                VALUES (?, ?, ?);
                """,
                (
                    "Mayhem Athlete",
                    "Mayhem",
                    "crossfit",
                ),
            )
            self.mayhem_program_id = cursor.lastrowid

            cursor = connection.execute(
                """
                INSERT INTO program_runs (
                    user_id,
                    program_id,
                    status,
                    started_on,
                    current_week
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    self.user_id,
                    self.hwpo_program_id,
                    "active",
                    "2026-07-01",
                    4,
                ),
            )
            self.hwpo_run_id = cursor.lastrowid

            cursor = connection.execute(
                """
                INSERT INTO program_runs (
                    user_id,
                    program_id,
                    status,
                    started_on,
                    current_week
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    self.user_id,
                    self.mayhem_program_id,
                    "active",
                    "2026-07-01",
                    4,
                ),
            )
            self.mayhem_run_id = cursor.lastrowid

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def create_session(self) -> int:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO planned_sessions (
                    user_id,
                    location_id,
                    session_date,
                    title
                )
                VALUES (?, ?, ?, ?);
                """,
                (
                    self.user_id,
                    self.location_id,
                    "2026-07-22",
                    "Evening Box Session",
                ),
            )

            return cursor.lastrowid

    def create_block(
        self,
        session_id: int,
        sequence: int,
        title: str,
        block_type: str,
        training_goal: str,
    ) -> int:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO planned_blocks (
                    planned_session_id,
                    sequence,
                    title,
                    block_type,
                    training_goal
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    session_id,
                    sequence,
                    title,
                    block_type,
                    training_goal,
                ),
            )

            return cursor.lastrowid

    def test_session_can_exist_without_program(self) -> None:
        session_id = self.create_session()

        block_id = self.create_block(
            session_id=session_id,
            sequence=1,
            title="Personal Hypertrophy",
            block_type="resistance",
            training_goal="hypertrophy",
        )

        with get_connection(self.db_path) as connection:
            link_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM planned_block_program_runs
                WHERE planned_block_id = ?;
                """,
                (block_id,),
            ).fetchone()[0]

        self.assertEqual(link_count, 0)

    def test_one_session_can_mix_multiple_programs(
        self,
    ) -> None:
        session_id = self.create_session()

        strength_block_id = self.create_block(
            session_id=session_id,
            sequence=1,
            title="HWPO Back Squat",
            block_type="resistance",
            training_goal="strength",
        )

        metcon_block_id = self.create_block(
            session_id=session_id,
            sequence=2,
            title="Mayhem Metcon",
            block_type="metcon",
            training_goal="conditioning",
        )

        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO planned_block_program_runs (
                    planned_block_id,
                    program_run_id,
                    source_role
                )
                VALUES (?, ?, ?);
                """,
                (
                    strength_block_id,
                    self.hwpo_run_id,
                    "primary",
                ),
            )

            connection.execute(
                """
                INSERT INTO planned_block_program_runs (
                    planned_block_id,
                    program_run_id,
                    source_role
                )
                VALUES (?, ?, ?);
                """,
                (
                    metcon_block_id,
                    self.mayhem_run_id,
                    "primary",
                ),
            )

            run_ids = {
                row["program_run_id"]
                for row in connection.execute(
                    """
                    SELECT pbpr.program_run_id
                    FROM planned_blocks AS pb
                    JOIN planned_block_program_runs AS pbpr
                      ON pbpr.planned_block_id = pb.id
                    WHERE pb.planned_session_id = ?;
                    """,
                    (session_id,),
                )
            }

        self.assertEqual(
            run_ids,
            {
                self.hwpo_run_id,
                self.mayhem_run_id,
            },
        )

    def test_one_block_can_reference_multiple_programs(
        self,
    ) -> None:
        session_id = self.create_session()

        block_id = self.create_block(
            session_id=session_id,
            sequence=1,
            title="Modified Mixed Block",
            block_type="resistance",
            training_goal="mixed",
        )

        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO planned_block_program_runs (
                    planned_block_id,
                    program_run_id,
                    source_role
                )
                VALUES (?, ?, ?);
                """,
                (
                    block_id,
                    self.hwpo_run_id,
                    "primary",
                ),
            )

            connection.execute(
                """
                INSERT INTO planned_block_program_runs (
                    planned_block_id,
                    program_run_id,
                    source_role
                )
                VALUES (?, ?, ?);
                """,
                (
                    block_id,
                    self.mayhem_run_id,
                    "modified_from",
                ),
            )

            count = connection.execute(
                """
                SELECT COUNT(*)
                FROM planned_block_program_runs
                WHERE planned_block_id = ?;
                """,
                (block_id,),
            ).fetchone()[0]

        self.assertEqual(count, 2)

    def test_invalid_block_type_is_rejected(self) -> None:
        session_id = self.create_session()

        with self.assertRaises(sqlite3.IntegrityError):
            self.create_block(
                session_id=session_id,
                sequence=1,
                title="Invalid Block",
                block_type="magic_training",
                training_goal="strength",
            )

    def test_session_delete_cascades_to_plan_details(
        self,
    ) -> None:
        session_id = self.create_session()

        block_id = self.create_block(
            session_id=session_id,
            sequence=1,
            title="Back Squat Strength",
            block_type="resistance",
            training_goal="strength",
        )

        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO planned_exercises (
                    planned_block_id,
                    exercise_id,
                    sequence,
                    sets,
                    reps_min,
                    reps_max,
                    percentage_1rm
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    block_id,
                    self.back_squat_id,
                    1,
                    5,
                    5,
                    5,
                    75,
                ),
            )

            connection.execute(
                """
                DELETE FROM planned_sessions
                WHERE id = ?;
                """,
                (session_id,),
            )

        with get_connection(self.db_path) as connection:
            block_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM planned_blocks
                WHERE planned_session_id = ?;
                """,
                (session_id,),
            ).fetchone()[0]

            exercise_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM planned_exercises
                WHERE planned_block_id = ?;
                """,
                (block_id,),
            ).fetchone()[0]

        self.assertEqual(block_count, 0)
        self.assertEqual(exercise_count, 0)

    def test_metcon_plan_can_store_movements(self) -> None:
        session_id = self.create_session()

        block_id = self.create_block(
            session_id=session_id,
            sequence=1,
            title="21-15-9 Thruster",
            block_type="metcon",
            training_goal="conditioning",
        )

        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO planned_metcons (
                    planned_block_id,
                    format,
                    score_type,
                    time_cap_seconds,
                    prescription_text
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    block_id,
                    "for_time",
                    "time",
                    900,
                    "21-15-9 Thruster",
                ),
            )
            metcon_id = cursor.lastrowid

            connection.execute(
                """
                INSERT INTO planned_metcon_movements (
                    planned_metcon_id,
                    exercise_id,
                    sequence,
                    reps,
                    weight,
                    weight_unit
                )
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    metcon_id,
                    self.thruster_id,
                    1,
                    21,
                    95,
                    "lb",
                ),
            )

            count = connection.execute(
                """
                SELECT COUNT(*)
                FROM planned_metcon_movements
                WHERE planned_metcon_id = ?;
                """,
                (metcon_id,),
            ).fetchone()[0]

        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database.connection import get_connection
from app.database.migrations import run_migrations


class ActualTrainingSchemaTests(unittest.TestCase):
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
                    "discord-user-actual",
                    "Actual Training Test User",
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
                    "Test Box",
                    "crossfit_box",
                ),
            )
            self.location_id = cursor.lastrowid

            self.exercise_ids = {}

            exercises = [
                (
                    "Back Squat",
                    "백스쿼트",
                    "strength",
                    "resistance",
                ),
                (
                    "Thruster",
                    "스러스터",
                    "crossfit",
                    "metcon",
                ),
                (
                    "Pull-up",
                    "풀업",
                    "gymnastics",
                    "skill",
                ),
                (
                    "Running",
                    "러닝",
                    "cardio",
                    "cardio",
                ),
            ]

            for (
                canonical_name,
                korean_name,
                category,
                default_block_type,
            ) in exercises:
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
                        canonical_name,
                        korean_name,
                        category,
                        default_block_type,
                    ),
                )

                self.exercise_ids[
                    canonical_name
                ] = cursor.lastrowid

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
            program_id = cursor.lastrowid

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
                    program_id,
                    "active",
                    "2026-07-01",
                    4,
                ),
            )
            self.program_run_id = cursor.lastrowid

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
                    "2026-07-23",
                    "Planned Box Session",
                ),
            )
            self.planned_session_id = cursor.lastrowid

            self.planned_block_ids = []

            for sequence, title, block_type, goal in [
                (
                    1,
                    "Planned Strength",
                    "resistance",
                    "strength",
                ),
                (
                    2,
                    "Planned Metcon",
                    "metcon",
                    "conditioning",
                ),
            ]:
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
                        self.planned_session_id,
                        sequence,
                        title,
                        block_type,
                        goal,
                    ),
                )

                self.planned_block_ids.append(
                    cursor.lastrowid
                )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def create_workout_session(self) -> int:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO workout_sessions (
                    user_id,
                    location_id,
                    performed_on,
                    title,
                    overall_rpe
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    self.user_id,
                    self.location_id,
                    "2026-07-23",
                    "Actual Box Session",
                    8,
                ),
            )

            return cursor.lastrowid

    def create_workout_block(
        self,
        workout_session_id: int,
        sequence: int,
        block_type: str,
        training_goal: str,
        title: str,
    ) -> int:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO workout_blocks (
                    workout_session_id,
                    sequence,
                    block_type,
                    training_goal,
                    title
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    workout_session_id,
                    sequence,
                    block_type,
                    training_goal,
                    title,
                ),
            )

            return cursor.lastrowid

    def test_actual_session_can_exist_without_plan(
        self,
    ) -> None:
        workout_session_id = self.create_workout_session()

        block_id = self.create_workout_block(
            workout_session_id=workout_session_id,
            sequence=1,
            block_type="resistance",
            training_goal="hypertrophy",
            title="Unplanned Accessory Work",
        )

        with get_connection(self.db_path) as connection:
            link_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM workout_block_planned_blocks
                WHERE workout_block_id = ?;
                """,
                (block_id,),
            ).fetchone()[0]

        self.assertEqual(link_count, 0)

    def test_session_can_mix_multiple_block_types(
        self,
    ) -> None:
        workout_session_id = self.create_workout_session()

        block_types = [
            ("resistance", "strength"),
            ("metcon", "conditioning"),
            ("cardio", "aerobic_endurance"),
        ]

        for sequence, (
            block_type,
            training_goal,
        ) in enumerate(block_types, start=1):
            self.create_workout_block(
                workout_session_id=workout_session_id,
                sequence=sequence,
                block_type=block_type,
                training_goal=training_goal,
                title=f"Block {sequence}",
            )

        with get_connection(self.db_path) as connection:
            stored_types = {
                row["block_type"]
                for row in connection.execute(
                    """
                    SELECT block_type
                    FROM workout_blocks
                    WHERE workout_session_id = ?;
                    """,
                    (workout_session_id,),
                )
            }

        self.assertEqual(
            stored_types,
            {
                "resistance",
                "metcon",
                "cardio",
            },
        )

    def test_actual_block_can_link_to_multiple_plans(
        self,
    ) -> None:
        workout_session_id = self.create_workout_session()

        block_id = self.create_workout_block(
            workout_session_id=workout_session_id,
            sequence=1,
            block_type="metcon",
            training_goal="mixed",
            title="Combined Planned Work",
        )

        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO workout_block_planned_blocks (
                    workout_block_id,
                    planned_block_id,
                    relation_type
                )
                VALUES (?, ?, ?);
                """,
                (
                    block_id,
                    self.planned_block_ids[0],
                    "combined",
                ),
            )

            connection.execute(
                """
                INSERT INTO workout_block_planned_blocks (
                    workout_block_id,
                    planned_block_id,
                    relation_type
                )
                VALUES (?, ?, ?);
                """,
                (
                    block_id,
                    self.planned_block_ids[1],
                    "combined",
                ),
            )

            count = connection.execute(
                """
                SELECT COUNT(*)
                FROM workout_block_planned_blocks
                WHERE workout_block_id = ?;
                """,
                (block_id,),
            ).fetchone()[0]

        self.assertEqual(count, 2)

    def test_actual_block_can_link_to_program_without_plan(
        self,
    ) -> None:
        workout_session_id = self.create_workout_session()

        block_id = self.create_workout_block(
            workout_session_id=workout_session_id,
            sequence=1,
            block_type="resistance",
            training_goal="strength",
            title="HWPO Strength",
        )

        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO workout_block_program_runs (
                    workout_block_id,
                    program_run_id,
                    source_role
                )
                VALUES (?, ?, ?);
                """,
                (
                    block_id,
                    self.program_run_id,
                    "primary",
                ),
            )

            count = connection.execute(
                """
                SELECT COUNT(*)
                FROM workout_block_program_runs
                WHERE workout_block_id = ?;
                """,
                (block_id,),
            ).fetchone()[0]

        self.assertEqual(count, 1)

    def test_invalid_set_values_are_rejected(
        self,
    ) -> None:
        workout_session_id = self.create_workout_session()

        block_id = self.create_workout_block(
            workout_session_id=workout_session_id,
            sequence=1,
            block_type="resistance",
            training_goal="strength",
            title="Back Squat",
        )

        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO workout_exercises (
                    workout_block_id,
                    exercise_id,
                    sequence
                )
                VALUES (?, ?, ?);
                """,
                (
                    block_id,
                    self.exercise_ids["Back Squat"],
                    1,
                ),
            )
            workout_exercise_id = cursor.lastrowid

        with self.assertRaises(sqlite3.IntegrityError):
            with get_connection(self.db_path) as connection:
                connection.execute(
                    """
                    INSERT INTO exercise_sets (
                        workout_exercise_id,
                        set_number,
                        reps,
                        load_value,
                        load_unit,
                        rpe
                    )
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        workout_exercise_id,
                        1,
                        5,
                        225,
                        "lb",
                        11,
                    ),
                )

    def test_metcon_result_stores_movement_totals(
        self,
    ) -> None:
        workout_session_id = self.create_workout_session()

        block_id = self.create_workout_block(
            workout_session_id=workout_session_id,
            sequence=1,
            block_type="metcon",
            training_goal="conditioning",
            title="Fran",
        )

        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO metcon_results (
                    workout_block_id,
                    format,
                    score_type,
                    time_seconds,
                    rx_status,
                    result_text
                )
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    block_id,
                    "for_time",
                    "time",
                    381,
                    "rx",
                    "6:21 Rx",
                ),
            )
            metcon_result_id = cursor.lastrowid

            connection.execute(
                """
                INSERT INTO metcon_movement_results (
                    metcon_result_id,
                    exercise_id,
                    sequence,
                    total_reps,
                    load_value,
                    load_unit
                )
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    metcon_result_id,
                    self.exercise_ids["Thruster"],
                    1,
                    45,
                    95,
                    "lb",
                ),
            )

            connection.execute(
                """
                INSERT INTO metcon_movement_results (
                    metcon_result_id,
                    exercise_id,
                    sequence,
                    total_reps
                )
                VALUES (?, ?, ?, ?);
                """,
                (
                    metcon_result_id,
                    self.exercise_ids["Pull-up"],
                    2,
                    45,
                ),
            )

            movement_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM metcon_movement_results
                WHERE metcon_result_id = ?;
                """,
                (metcon_result_id,),
            ).fetchone()[0]

        self.assertEqual(movement_count, 2)

    def test_cardio_result_stores_metrics(self) -> None:
        workout_session_id = self.create_workout_session()

        block_id = self.create_workout_block(
            workout_session_id=workout_session_id,
            sequence=1,
            block_type="cardio",
            training_goal="aerobic_endurance",
            title="Easy Run",
        )

        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO cardio_results (
                    workout_block_id,
                    exercise_id,
                    duration_seconds,
                    distance_meters,
                    average_pace_seconds_per_km,
                    average_heart_rate,
                    maximum_heart_rate,
                    intensity_zone
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    block_id,
                    self.exercise_ids["Running"],
                    2100,
                    7000,
                    300,
                    145,
                    162,
                    "zone_2",
                ),
            )

            result = connection.execute(
                """
                SELECT
                    duration_seconds,
                    distance_meters,
                    average_heart_rate
                FROM cardio_results
                WHERE workout_block_id = ?;
                """,
                (block_id,),
            ).fetchone()

        self.assertEqual(result["duration_seconds"], 2100)
        self.assertEqual(result["distance_meters"], 7000)
        self.assertEqual(result["average_heart_rate"], 145)

    def test_session_delete_cascades_to_details(
        self,
    ) -> None:
        workout_session_id = self.create_workout_session()

        block_id = self.create_workout_block(
            workout_session_id=workout_session_id,
            sequence=1,
            block_type="resistance",
            training_goal="strength",
            title="Back Squat",
        )

        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO workout_exercises (
                    workout_block_id,
                    exercise_id,
                    sequence
                )
                VALUES (?, ?, ?);
                """,
                (
                    block_id,
                    self.exercise_ids["Back Squat"],
                    1,
                ),
            )
            workout_exercise_id = cursor.lastrowid

            connection.execute(
                """
                INSERT INTO exercise_sets (
                    workout_exercise_id,
                    set_number,
                    set_type,
                    reps,
                    load_value,
                    load_unit,
                    rpe
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    workout_exercise_id,
                    1,
                    "working",
                    5,
                    225,
                    "lb",
                    8,
                ),
            )

            connection.execute(
                """
                DELETE FROM workout_sessions
                WHERE id = ?;
                """,
                (workout_session_id,),
            )

        with get_connection(self.db_path) as connection:
            block_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM workout_blocks
                WHERE workout_session_id = ?;
                """,
                (workout_session_id,),
            ).fetchone()[0]

            exercise_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM workout_exercises
                WHERE id = ?;
                """,
                (workout_exercise_id,),
            ).fetchone()[0]

            set_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM exercise_sets
                WHERE workout_exercise_id = ?;
                """,
                (workout_exercise_id,),
            ).fetchone()[0]

        self.assertEqual(block_count, 0)
        self.assertEqual(exercise_count, 0)
        self.assertEqual(set_count, 0)


if __name__ == "__main__":
    unittest.main()

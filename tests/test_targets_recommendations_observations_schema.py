from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database.connection import get_connection
from app.database.migrations import run_migrations


class TargetsRecommendationsObservationsTests(unittest.TestCase):
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
                    "discord-user-targets",
                    "Targets Test User",
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
                    "Test Gym",
                    "commercial_gym",
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
                    "Chest Supported Row",
                    "체스트 서포티드 로우",
                    "strength",
                    "resistance",
                ),
            )
            self.row_exercise_id = cursor.lastrowid

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
                    "Bench Press",
                    "벤치프레스",
                    "strength",
                    "resistance",
                ),
            )
            self.bench_exercise_id = cursor.lastrowid

            self.horizontal_pull_id = connection.execute(
                """
                SELECT id
                FROM movement_patterns
                WHERE code = 'horizontal_pull';
                """
            ).fetchone()["id"]

            self.triceps_id = connection.execute(
                """
                SELECT id
                FROM muscle_groups
                WHERE code = 'triceps';
                """
            ).fetchone()["id"]

            cursor = connection.execute(
                """
                INSERT INTO workout_sessions (
                    user_id,
                    location_id,
                    performed_on,
                    title
                )
                VALUES (?, ?, ?, ?);
                """,
                (
                    self.user_id,
                    self.location_id,
                    "2026-07-20",
                    "Test Workout",
                ),
            )
            self.workout_session_id = cursor.lastrowid

            cursor = connection.execute(
                """
                INSERT INTO workout_blocks (
                    workout_session_id,
                    sequence,
                    title,
                    block_type,
                    training_goal
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    self.workout_session_id,
                    1,
                    "Bench Strength",
                    "resistance",
                    "strength",
                ),
            )
            self.workout_block_id = cursor.lastrowid

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
                    "2026-07-24",
                    "Recommended Session",
                ),
            )
            self.planned_session_id = cursor.lastrowid

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
                    1,
                    "Recommended Row Block",
                    "resistance",
                    "hypertrophy",
                ),
            )
            self.planned_block_id = cursor.lastrowid

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_movement_pattern_target_is_accepted(
        self,
    ) -> None:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO training_targets (
                    user_id,
                    name,
                    scope_type,
                    movement_pattern_id,
                    metric_type,
                    minimum_value,
                    target_value,
                    maximum_value,
                    valid_from
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    self.user_id,
                    "Weekly Horizontal Pull",
                    "movement_pattern",
                    self.horizontal_pull_id,
                    "effective_sets",
                    8,
                    10,
                    14,
                    "2026-07-20",
                ),
            )

            target_id = cursor.lastrowid

            result = connection.execute(
                """
                SELECT target_value
                FROM training_targets
                WHERE id = ?;
                """,
                (target_id,),
            ).fetchone()

        self.assertEqual(result["target_value"], 10)

    def test_target_scope_mismatch_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            with get_connection(self.db_path) as connection:
                connection.execute(
                    """
                    INSERT INTO training_targets (
                        user_id,
                        name,
                        scope_type,
                        movement_pattern_id,
                        exercise_id,
                        metric_type,
                        target_value,
                        valid_from
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        self.user_id,
                        "Invalid Mixed Target",
                        "movement_pattern",
                        self.horizontal_pull_id,
                        self.row_exercise_id,
                        "effective_sets",
                        10,
                        "2026-07-20",
                    ),
                )

    def test_invalid_target_range_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            with get_connection(self.db_path) as connection:
                connection.execute(
                    """
                    INSERT INTO training_targets (
                        user_id,
                        name,
                        scope_type,
                        movement_pattern_id,
                        metric_type,
                        minimum_value,
                        target_value,
                        maximum_value,
                        valid_from
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        self.user_id,
                        "Invalid Range",
                        "movement_pattern",
                        self.horizontal_pull_id,
                        "effective_sets",
                        12,
                        10,
                        8,
                        "2026-07-20",
                    ),
                )

    def test_recommendation_can_reference_target_and_plan(
        self,
    ) -> None:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO training_targets (
                    user_id,
                    name,
                    scope_type,
                    movement_pattern_id,
                    metric_type,
                    target_value,
                    valid_from
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    self.user_id,
                    "Horizontal Pull Target",
                    "movement_pattern",
                    self.horizontal_pull_id,
                    "effective_sets",
                    10,
                    "2026-07-20",
                ),
            )
            target_id = cursor.lastrowid

            cursor = connection.execute(
                """
                INSERT INTO recommendation_batches (
                    user_id,
                    week_start,
                    week_end,
                    requested_location_id,
                    analysis_snapshot_json
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    self.user_id,
                    "2026-07-20",
                    "2026-07-26",
                    self.location_id,
                    '{"horizontal_pull":{"expected":7,"target":10}}',
                ),
            )
            batch_id = cursor.lastrowid

            cursor = connection.execute(
                """
                INSERT INTO recommendation_items (
                    recommendation_batch_id,
                    rank,
                    exercise_id,
                    movement_pattern_id,
                    training_target_id,
                    location_id,
                    status,
                    deficit_metric_type,
                    deficit_value,
                    proposed_sets,
                    proposed_reps_min,
                    proposed_reps_max,
                    rationale,
                    confidence,
                    created_planned_block_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    batch_id,
                    1,
                    self.row_exercise_id,
                    self.horizontal_pull_id,
                    target_id,
                    self.location_id,
                    "scheduled",
                    "effective_sets",
                    3,
                    3,
                    8,
                    12,
                    "수평 당기기 예상량이 3세트 부족함",
                    0.9,
                    self.planned_block_id,
                ),
            )
            recommendation_id = cursor.lastrowid

            result = connection.execute(
                """
                SELECT
                    status,
                    proposed_sets,
                    created_planned_block_id
                FROM recommendation_items
                WHERE id = ?;
                """,
                (recommendation_id,),
            ).fetchone()

        self.assertEqual(result["status"], "scheduled")
        self.assertEqual(result["proposed_sets"], 3)
        self.assertEqual(
            result["created_planned_block_id"],
            self.planned_block_id,
        )

    def test_invalid_recovery_score_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            with get_connection(self.db_path) as connection:
                connection.execute(
                    """
                    INSERT INTO recovery_checkins (
                        user_id,
                        recorded_at,
                        reference_date,
                        overall_fatigue
                    )
                    VALUES (?, ?, ?, ?);
                    """,
                    (
                        self.user_id,
                        "2026-07-21T08:00:00+09:00",
                        "2026-07-21",
                        6,
                    ),
                )

    def test_muscle_observation_can_link_to_workout(
        self,
    ) -> None:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO muscle_status_observations (
                    user_id,
                    muscle_group_id,
                    recorded_at,
                    soreness_score,
                    fatigue_score,
                    pain_score,
                    laterality,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    self.user_id,
                    self.triceps_id,
                    "2026-07-21T08:00:00+09:00",
                    4,
                    3,
                    0,
                    "bilateral",
                    "벤치 다음날 삼두 근육통",
                ),
            )
            observation_id = cursor.lastrowid

            connection.execute(
                """
                INSERT INTO observation_workout_links (
                    observation_id,
                    workout_session_id,
                    attribution_type,
                    attribution_weight
                )
                VALUES (?, ?, ?, ?);
                """,
                (
                    observation_id,
                    self.workout_session_id,
                    "temporal",
                    0.8,
                ),
            )

            count = connection.execute(
                """
                SELECT COUNT(*)
                FROM observation_workout_links
                WHERE observation_id = ?;
                """,
                (observation_id,),
            ).fetchone()[0]

        self.assertEqual(count, 1)

    def test_empty_muscle_observation_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            with get_connection(self.db_path) as connection:
                connection.execute(
                    """
                    INSERT INTO muscle_status_observations (
                        user_id,
                        muscle_group_id,
                        recorded_at,
                        laterality
                    )
                    VALUES (?, ?, ?, ?);
                    """,
                    (
                        self.user_id,
                        self.triceps_id,
                        "2026-07-21T08:00:00+09:00",
                        "bilateral",
                    ),
                )

    def test_performance_observation_is_stored(
        self,
    ) -> None:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO performance_observations (
                    user_id,
                    exercise_id,
                    workout_session_id,
                    workout_block_id,
                    observed_at,
                    metric_type,
                    metric_value,
                    metric_unit,
                    is_derived,
                    calculation_version,
                    confidence
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    self.user_id,
                    self.bench_exercise_id,
                    self.workout_session_id,
                    self.workout_block_id,
                    "2026-07-20T21:00:00+09:00",
                    "estimated_1rm",
                    198,
                    "lb",
                    1,
                    "epley-v1",
                    0.8,
                ),
            )
            observation_id = cursor.lastrowid

            result = connection.execute(
                """
                SELECT
                    metric_type,
                    metric_value,
                    calculation_version
                FROM performance_observations
                WHERE id = ?;
                """,
                (observation_id,),
            ).fetchone()

        self.assertEqual(
            result["metric_type"],
            "estimated_1rm",
        )
        self.assertEqual(result["metric_value"], 198)
        self.assertEqual(
            result["calculation_version"],
            "epley-v1",
        )


if __name__ == "__main__":
    unittest.main()

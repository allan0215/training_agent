from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.catalog.models import (
    ExerciseCreateRequest,
    MovementPatternSpec,
)
from app.catalog.permissions import (
    CatalogPermissionError,
    CatalogPermissionPolicy,
)
from app.catalog.service import (
    DuplicateExerciseError,
    PersonalExerciseOwnershipError,
    CatalogService,
)
from app.database.catalog_seed import seed_catalog
from app.database.connection import get_connection
from app.database.migrations import run_migrations


class DynamicCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()

        self.db_path = (
            Path(self.temp_directory.name)
            / "test_training_agent.db"
        )

        run_migrations(db_path=self.db_path)
        seed_catalog(db_path=self.db_path)

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
                    "owner-discord-id",
                    "Owner",
                ),
            )
            self.owner_user_id = cursor.lastrowid

            cursor = connection.execute(
                """
                INSERT INTO users (
                    discord_user_id,
                    display_name
                )
                VALUES (?, ?);
                """,
                (
                    "other-discord-id",
                    "Other User",
                ),
            )
            self.other_user_id = cursor.lastrowid

            self.bent_over_row_id = connection.execute(
                """
                SELECT id
                FROM exercises
                WHERE canonical_name = 'Bent-over Row';
                """
            ).fetchone()["id"]

        self.owner_policy = CatalogPermissionPolicy(
            mode="owner",
            owner_discord_id="owner-discord-id",
        )

        self.service = CatalogService(
            db_path=self.db_path,
            permission_policy=self.owner_policy,
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def pendlay_request(
        self,
        scope: str,
    ) -> ExerciseCreateRequest:
        return ExerciseCreateRequest(
            canonical_name="Pendlay Row",
            korean_name="펜들레이 로우",
            category="strength",
            default_block_type="resistance",
            catalog_scope=scope,
            aliases=("펜들레이로우",),
            movement_patterns=(
                MovementPatternSpec(
                    code="horizontal_pull",
                    role="primary",
                    contribution_weight=1.0,
                ),
                MovementPatternSpec(
                    code="hinge",
                    role="stabilizer",
                    contribution_weight=0.3,
                ),
            ),
            equipment_codes=(
                "barbell",
                "weight_plates",
            ),
            parent_exercise_id=(
                self.bent_over_row_id
            ),
        )

    def test_seed_exercises_are_core_seed_data(
        self,
    ) -> None:
        with get_connection(self.db_path) as connection:
            result = connection.execute(
                """
                SELECT
                    catalog_scope,
                    owner_user_id,
                    source_type,
                    review_status
                FROM exercises
                WHERE canonical_name = 'Back Squat';
                """
            ).fetchone()

        self.assertEqual(
            result["catalog_scope"],
            "core",
        )
        self.assertIsNone(
            result["owner_user_id"]
        )
        self.assertEqual(
            result["source_type"],
            "seed",
        )
        self.assertEqual(
            result["review_status"],
            "verified",
        )

    def test_owner_can_create_core_exercise(
        self,
    ) -> None:
        result = self.service.create_exercise(
            actor_user_id=self.owner_user_id,
            request=self.pendlay_request(
                scope="core"
            ),
        )

        self.assertEqual(
            result["catalog_scope"],
            "core",
        )
        self.assertIsNone(
            result["owner_user_id"]
        )
        self.assertEqual(
            result["source_type"],
            "owner_created",
        )

    def test_non_owner_cannot_create_core_exercise(
        self,
    ) -> None:
        with self.assertRaises(
            CatalogPermissionError
        ):
            self.service.create_exercise(
                actor_user_id=self.other_user_id,
                request=self.pendlay_request(
                    scope="core"
                ),
            )

    def test_user_can_create_personal_exercise(
        self,
    ) -> None:
        result = self.service.create_exercise(
            actor_user_id=self.other_user_id,
            request=self.pendlay_request(
                scope="personal"
            ),
        )

        self.assertEqual(
            result["catalog_scope"],
            "personal",
        )
        self.assertEqual(
            result["owner_user_id"],
            self.other_user_id,
        )
        self.assertEqual(
            result["source_type"],
            "user_created",
        )

    def test_duplicate_exercise_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(
            DuplicateExerciseError
        ):
            self.service.create_exercise(
                actor_user_id=self.owner_user_id,
                request=ExerciseCreateRequest(
                    canonical_name="Back Squat",
                    korean_name="백스쿼트",
                    category="strength",
                    default_block_type="resistance",
                    catalog_scope="core",
                ),
            )

    def test_owner_can_promote_personal_exercise(
        self,
    ) -> None:
        created = self.service.create_exercise(
            actor_user_id=self.other_user_id,
            request=self.pendlay_request(
                scope="personal"
            ),
        )

        exercise_id = created["id"]

        promoted = self.service.promote_to_core(
            actor_user_id=self.owner_user_id,
            exercise_id=exercise_id,
        )

        self.assertEqual(
            promoted["id"],
            exercise_id,
        )
        self.assertEqual(
            promoted["catalog_scope"],
            "core",
        )
        self.assertIsNone(
            promoted["owner_user_id"]
        )
        self.assertEqual(
            promoted["source_type"],
            "promoted",
        )

    def test_personal_exercise_owner_controls_aliases(
        self,
    ) -> None:
        created = self.service.create_exercise(
            actor_user_id=self.other_user_id,
            request=self.pendlay_request(
                scope="personal"
            ),
        )

        created_alias = self.service.add_alias(
            actor_user_id=self.other_user_id,
            exercise_id=created["id"],
            alias="Pendlay",
        )

        self.assertTrue(created_alias)

        with self.assertRaises(
            PersonalExerciseOwnershipError
        ):
            self.service.add_alias(
                actor_user_id=self.owner_user_id,
                exercise_id=created["id"],
                alias="남의 별칭",
            )

    def test_disabled_mode_blocks_core_writes(
        self,
    ) -> None:
        disabled_service = CatalogService(
            db_path=self.db_path,
            permission_policy=(
                CatalogPermissionPolicy(
                    mode="disabled"
                )
            ),
        )

        with self.assertRaises(
            CatalogPermissionError
        ):
            disabled_service.create_exercise(
                actor_user_id=self.owner_user_id,
                request=self.pendlay_request(
                    scope="core"
                ),
            )

    def test_database_rejects_personal_without_owner(
        self,
    ) -> None:
        with self.assertRaises(
            sqlite3.IntegrityError
        ):
            with get_connection(
                self.db_path
            ) as connection:
                connection.execute(
                    """
                    INSERT INTO exercises (
                        canonical_name,
                        category,
                        default_block_type,
                        catalog_scope,
                        owner_user_id,
                        source_type
                    )
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        "Invalid Personal Exercise",
                        "strength",
                        "resistance",
                        "personal",
                        None,
                        "user_created",
                    ),
                )


if __name__ == "__main__":
    unittest.main()

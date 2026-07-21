from __future__ import annotations

import sqlite3
from typing import Any

from app.catalog.models import ExerciseCreateRequest
from app.catalog.normalization import (
    detect_language,
    normalize_alias,
)
from app.catalog.permissions import (
    CatalogPermissionError,
    CatalogPermissionPolicy,
)
from app.database.connection import (
    DatabasePath,
    get_connection,
)


class CatalogError(RuntimeError):
    pass


class CatalogUserNotFoundError(CatalogError):
    pass


class ExerciseNotFoundError(CatalogError):
    pass


class DuplicateExerciseError(CatalogError):
    def __init__(
        self,
        matches: list[dict[str, Any]],
    ) -> None:
        self.matches = matches

        names = ", ".join(
            str(match["canonical_name"])
            for match in matches
        )

        super().__init__(
            f"중복 가능성이 있는 운동이 있습니다: {names}"
        )


class PersonalExerciseOwnershipError(
    CatalogPermissionError
):
    pass


class CatalogService:
    def __init__(
        self,
        db_path: DatabasePath | None = None,
        permission_policy:
            CatalogPermissionPolicy | None = None,
    ) -> None:
        self.db_path = db_path
        self.permission_policy = (
            permission_policy
            or CatalogPermissionPolicy.from_environment()
        )

    def _get_actor(
        self,
        connection: sqlite3.Connection,
        actor_user_id: int,
    ) -> sqlite3.Row:
        actor = connection.execute(
            """
            SELECT
                id,
                discord_user_id,
                display_name
            FROM users
            WHERE id = ?;
            """,
            (actor_user_id,),
        ).fetchone()

        if actor is None:
            raise CatalogUserNotFoundError(
                f"User not found: {actor_user_id}"
            )

        return actor

    def _get_exercise(
        self,
        connection: sqlite3.Connection,
        exercise_id: int,
    ) -> sqlite3.Row:
        exercise = connection.execute(
            """
            SELECT *
            FROM exercises
            WHERE id = ?;
            """,
            (exercise_id,),
        ).fetchone()

        if exercise is None:
            raise ExerciseNotFoundError(
                f"Exercise not found: {exercise_id}"
            )

        return exercise

    def _find_exact_matches(
        self,
        connection: sqlite3.Connection,
        values: list[str],
    ) -> list[dict[str, Any]]:
        normalized_values = {
            normalize_alias(value)
            for value in values
            if value and value.strip()
        }

        if not normalized_values:
            return []

        rows = connection.execute(
            """
            SELECT
                e.id,
                e.canonical_name,
                e.korean_name,
                e.catalog_scope,
                e.owner_user_id,
                e.is_active,
                ea.alias_normalized
            FROM exercises AS e
            LEFT JOIN exercise_aliases AS ea
              ON ea.exercise_id = e.id;
            """
        ).fetchall()

        matches: dict[int, dict[str, Any]] = {}

        for row in rows:
            candidate_values = {
                normalize_alias(
                    row["canonical_name"]
                )
            }

            if row["korean_name"]:
                candidate_values.add(
                    normalize_alias(
                        row["korean_name"]
                    )
                )

            if row["alias_normalized"]:
                candidate_values.add(
                    row["alias_normalized"]
                )

            if candidate_values & normalized_values:
                matches[row["id"]] = {
                    "id": row["id"],
                    "canonical_name":
                        row["canonical_name"],
                    "korean_name":
                        row["korean_name"],
                    "catalog_scope":
                        row["catalog_scope"],
                    "owner_user_id":
                        row["owner_user_id"],
                    "is_active":
                        bool(row["is_active"]),
                }

        return sorted(
            matches.values(),
            key=lambda item: item["canonical_name"],
        )

    def search_exact(
        self,
        value: str,
    ) -> list[dict[str, Any]]:
        with get_connection(
            self.db_path
        ) as connection:
            return self._find_exact_matches(
                connection,
                [value],
            )

    def _require_exercise_edit_permission(
        self,
        actor_user_id: int,
        actor_discord_id: str,
        exercise: sqlite3.Row,
    ) -> None:
        if exercise["catalog_scope"] == "core":
            self.permission_policy\
                .require_core_catalog_permission(
                    actor_discord_id
                )
            return

        if exercise["owner_user_id"] != actor_user_id:
            raise PersonalExerciseOwnershipError(
                "다른 사용자의 개인 운동은 "
                "수정할 수 없습니다."
            )

    def create_exercise(
        self,
        actor_user_id: int,
        request: ExerciseCreateRequest,
        *,
        allow_duplicate: bool = False,
    ) -> dict[str, Any]:
        canonical_name = (
            request.canonical_name.strip()
        )

        if not canonical_name:
            raise ValueError(
                "canonical_name is required"
            )

        if request.catalog_scope not in {
            "core",
            "personal",
        }:
            raise ValueError(
                "catalog_scope must be core or personal"
            )

        with get_connection(
            self.db_path
        ) as connection:
            actor = self._get_actor(
                connection,
                actor_user_id,
            )

            if request.catalog_scope == "core":
                self.permission_policy\
                    .require_core_catalog_permission(
                        actor["discord_user_id"]
                    )

            possible_names = [
                canonical_name,
                request.korean_name or "",
                *request.aliases,
            ]

            duplicates = self._find_exact_matches(
                connection,
                possible_names,
            )

            if duplicates and not allow_duplicate:
                raise DuplicateExerciseError(
                    duplicates
                )

            if request.parent_exercise_id is not None:
                self._get_exercise(
                    connection,
                    request.parent_exercise_id,
                )

            owner_user_id = (
                None
                if request.catalog_scope == "core"
                else actor_user_id
            )

            source_type = (
                "owner_created"
                if request.catalog_scope == "core"
                else "user_created"
            )

            cursor = connection.execute(
                """
                INSERT INTO exercises (
                    canonical_name,
                    korean_name,
                    category,
                    default_block_type,
                    is_active,
                    notes,
                    catalog_scope,
                    owner_user_id,
                    source_type,
                    review_status,
                    parent_exercise_id,
                    created_by_user_id
                )
                VALUES (
                    ?, ?, ?, ?, 1, ?,
                    ?, ?, ?, 'verified', ?, ?
                );
                """,
                (
                    canonical_name,
                    (
                        request.korean_name.strip()
                        if request.korean_name
                        else None
                    ),
                    request.category,
                    request.default_block_type,
                    request.notes,
                    request.catalog_scope,
                    owner_user_id,
                    source_type,
                    request.parent_exercise_id,
                    actor_user_id,
                ),
            )

            exercise_id = cursor.lastrowid

            aliases = {
                canonical_name,
                *request.aliases,
            }

            if request.korean_name:
                aliases.add(
                    request.korean_name.strip()
                )

            for alias in aliases:
                alias = alias.strip()

                if not alias:
                    continue

                connection.execute(
                    """
                    INSERT INTO exercise_aliases (
                        exercise_id,
                        alias,
                        alias_normalized,
                        language
                    )
                    VALUES (?, ?, ?, ?);
                    """,
                    (
                        exercise_id,
                        alias,
                        normalize_alias(alias),
                        detect_language(alias),
                    ),
                )

            pattern_ids = {
                row["code"]: row["id"]
                for row in connection.execute(
                    """
                    SELECT id, code
                    FROM movement_patterns;
                    """
                )
            }

            for pattern in request.movement_patterns:
                pattern_id = pattern_ids.get(
                    pattern.code
                )

                if pattern_id is None:
                    raise CatalogError(
                        "Unknown movement pattern: "
                        f"{pattern.code}"
                    )

                connection.execute(
                    """
                    INSERT INTO exercise_movement_patterns (
                        exercise_id,
                        movement_pattern_id,
                        role,
                        contribution_weight
                    )
                    VALUES (?, ?, ?, ?);
                    """,
                    (
                        exercise_id,
                        pattern_id,
                        pattern.role,
                        pattern.contribution_weight,
                    ),
                )

            equipment_ids = {
                row["code"]: row["id"]
                for row in connection.execute(
                    """
                    SELECT id, code
                    FROM equipment;
                    """
                )
            }

            for equipment_code in (
                request.equipment_codes
            ):
                equipment_id = equipment_ids.get(
                    equipment_code
                )

                if equipment_id is None:
                    raise CatalogError(
                        "Unknown equipment: "
                        f"{equipment_code}"
                    )

                connection.execute(
                    """
                    INSERT INTO exercise_equipment (
                        exercise_id,
                        equipment_id,
                        is_required,
                        quantity_required
                    )
                    VALUES (?, ?, 1, 1);
                    """,
                    (
                        exercise_id,
                        equipment_id,
                    ),
                )

            result = self._get_exercise(
                connection,
                exercise_id,
            )

            return dict(result)

    def add_alias(
        self,
        actor_user_id: int,
        exercise_id: int,
        alias: str,
    ) -> bool:
        alias = alias.strip()

        if not alias:
            raise ValueError("alias is required")

        with get_connection(
            self.db_path
        ) as connection:
            actor = self._get_actor(
                connection,
                actor_user_id,
            )

            exercise = self._get_exercise(
                connection,
                exercise_id,
            )

            self._require_exercise_edit_permission(
                actor_user_id,
                actor["discord_user_id"],
                exercise,
            )

            matches = self._find_exact_matches(
                connection,
                [alias],
            )

            other_matches = [
                match
                for match in matches
                if match["id"] != exercise_id
            ]

            if other_matches:
                raise DuplicateExerciseError(
                    other_matches
                )

            if matches:
                return False

            connection.execute(
                """
                INSERT INTO exercise_aliases (
                    exercise_id,
                    alias,
                    alias_normalized,
                    language
                )
                VALUES (?, ?, ?, ?);
                """,
                (
                    exercise_id,
                    alias,
                    normalize_alias(alias),
                    detect_language(alias),
                ),
            )

            return True

    def promote_to_core(
        self,
        actor_user_id: int,
        exercise_id: int,
    ) -> dict[str, Any]:
        with get_connection(
            self.db_path
        ) as connection:
            actor = self._get_actor(
                connection,
                actor_user_id,
            )

            self.permission_policy\
                .require_core_catalog_permission(
                    actor["discord_user_id"]
                )

            exercise = self._get_exercise(
                connection,
                exercise_id,
            )

            if exercise["catalog_scope"] == "core":
                return dict(exercise)

            connection.execute(
                """
                UPDATE exercises
                SET
                    catalog_scope = 'core',
                    owner_user_id = NULL,
                    source_type = 'promoted',
                    review_status = 'verified',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (exercise_id,),
            )

            result = self._get_exercise(
                connection,
                exercise_id,
            )

            return dict(result)

    def deactivate_exercise(
        self,
        actor_user_id: int,
        exercise_id: int,
    ) -> dict[str, Any]:
        with get_connection(
            self.db_path
        ) as connection:
            actor = self._get_actor(
                connection,
                actor_user_id,
            )

            exercise = self._get_exercise(
                connection,
                exercise_id,
            )

            self._require_exercise_edit_permission(
                actor_user_id,
                actor["discord_user_id"],
                exercise,
            )

            connection.execute(
                """
                UPDATE exercises
                SET
                    is_active = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (exercise_id,),
            )

            result = self._get_exercise(
                connection,
                exercise_id,
            )

            return dict(result)

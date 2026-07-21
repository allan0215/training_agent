from __future__ import annotations

from pathlib import Path

from app.database.connection import (
    DatabasePath,
    get_connection,
)
from app.database.seeds.catalog_data import (
    EQUIPMENT,
    EXERCISES,
)


def normalize_alias(value: str) -> str:
    return " ".join(
        value.strip().casefold().split()
    )


def detect_language(value: str) -> str:
    for character in value:
        if "\uac00" <= character <= "\ud7a3":
            return "ko"

    return "en"


def seed_catalog(
    db_path: DatabasePath | None = None,
) -> dict[str, int]:
    with get_connection(db_path) as connection:
        for code, display_name, category in EQUIPMENT:
            connection.execute(
                """
                INSERT INTO equipment (
                    code,
                    display_name,
                    category,
                    is_active
                )
                VALUES (?, ?, ?, 1)
                ON CONFLICT(code) DO UPDATE SET
                    display_name = excluded.display_name,
                    category = excluded.category,
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (
                    code,
                    display_name,
                    category,
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

        movement_pattern_ids = {
            row["code"]: row["id"]
            for row in connection.execute(
                """
                SELECT id, code
                FROM movement_patterns;
                """
            )
        }

        for (
            canonical_name,
            korean_name,
            category,
            default_block_type,
            extra_aliases,
            movement_patterns,
            required_equipment,
        ) in EXERCISES:
            connection.execute(
                """
                INSERT INTO exercises (
                    canonical_name,
                    korean_name,
                    category,
                    default_block_type,
                    is_active
                )
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(canonical_name) DO UPDATE SET
                    korean_name = excluded.korean_name,
                    category = excluded.category,
                    default_block_type =
                        excluded.default_block_type,
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (
                    canonical_name,
                    korean_name,
                    category,
                    default_block_type,
                ),
            )

            exercise_id = connection.execute(
                """
                SELECT id
                FROM exercises
                WHERE canonical_name = ?;
                """,
                (canonical_name,),
            ).fetchone()["id"]

            aliases = {
                canonical_name,
                korean_name,
                *extra_aliases,
            }

            for alias in aliases:
                normalized = normalize_alias(alias)

                connection.execute(
                    """
                    INSERT INTO exercise_aliases (
                        exercise_id,
                        alias,
                        alias_normalized,
                        language
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(
                        alias_normalized,
                        exercise_id
                    ) DO UPDATE SET
                        alias = excluded.alias,
                        language = excluded.language;
                    """,
                    (
                        exercise_id,
                        alias,
                        normalized,
                        detect_language(alias),
                    ),
                )

            for (
                pattern_code,
                role,
                contribution_weight,
            ) in movement_patterns:
                pattern_id = movement_pattern_ids.get(
                    pattern_code
                )

                if pattern_id is None:
                    raise RuntimeError(
                        "Unknown movement pattern: "
                        f"{pattern_code}"
                    )

                connection.execute(
                    """
                    INSERT INTO exercise_movement_patterns (
                        exercise_id,
                        movement_pattern_id,
                        role,
                        contribution_weight
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(
                        exercise_id,
                        movement_pattern_id
                    ) DO UPDATE SET
                        role = excluded.role,
                        contribution_weight =
                            excluded.contribution_weight;
                    """,
                    (
                        exercise_id,
                        pattern_id,
                        role,
                        contribution_weight,
                    ),
                )

            for equipment_code in required_equipment:
                equipment_id = equipment_ids.get(
                    equipment_code
                )

                if equipment_id is None:
                    raise RuntimeError(
                        f"Unknown equipment: {equipment_code}"
                    )

                connection.execute(
                    """
                    INSERT INTO exercise_equipment (
                        exercise_id,
                        equipment_id,
                        is_required,
                        quantity_required
                    )
                    VALUES (?, ?, 1, 1)
                    ON CONFLICT(
                        exercise_id,
                        equipment_id
                    ) DO UPDATE SET
                        is_required = 1,
                        quantity_required = 1;
                    """,
                    (
                        exercise_id,
                        equipment_id,
                    ),
                )

        counts = {}

        for table in (
            "equipment",
            "exercises",
            "exercise_aliases",
            "exercise_movement_patterns",
            "exercise_equipment",
        ):
            counts[table] = connection.execute(
                f"SELECT COUNT(*) FROM {table};"
            ).fetchone()[0]

    return counts

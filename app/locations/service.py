from __future__ import annotations

import sqlite3

from app.database.connection import (
    DatabasePath,
    get_connection,
)
from app.locations.models import LocationRecord


ALLOWED_LOCATION_TYPES = {
    "home_gym",
    "commercial_gym",
    "crossfit_box",
    "outdoor",
    "temporary_location",
    "other",
}


class LocationServiceError(RuntimeError):
    pass


class LocationUserNotFoundError(
    LocationServiceError
):
    pass


class LocationNotFoundError(
    LocationServiceError
):
    """
    장소가 존재하지 않거나, 요청한 사용자의 장소가 아닐 때
    동일하게 사용하는 내부 예외.

    다른 사용자 소유의 장소가 존재하는지 외부에 노출하지 않는다.
    """


class DuplicateLocationError(
    LocationServiceError
):
    pass


class InvalidLocationTypeError(
    LocationServiceError
):
    pass


def _validate_name(name: str) -> str:
    normalized = str(name).strip()

    if not normalized:
        raise ValueError(
            "LOCATION_NAME_REQUIRED"
        )

    if len(normalized) > 100:
        raise ValueError(
            "LOCATION_NAME_TOO_LONG"
        )

    return normalized


def _validate_location_type(
    location_type: str,
) -> str:
    normalized = str(
        location_type
    ).strip().lower()

    if normalized not in ALLOWED_LOCATION_TYPES:
        raise InvalidLocationTypeError(
            "INVALID_LOCATION_TYPE"
        )

    return normalized


def _normalize_notes(
    notes: str | None,
) -> str | None:
    if notes is None:
        return None

    normalized = str(notes).strip()

    return normalized or None


def _row_to_location(
    row: sqlite3.Row,
) -> LocationRecord:
    return LocationRecord(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        location_type=row["location_type"],
        notes=row["notes"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class LocationService:
    def __init__(
        self,
        db_path: DatabasePath | None = None,
    ) -> None:
        self.db_path = db_path

    def _ensure_user_exists(
        self,
        connection: sqlite3.Connection,
        user_id: int,
    ) -> None:
        row = connection.execute(
            """
            SELECT id
            FROM users
            WHERE id = ?;
            """,
            (user_id,),
        ).fetchone()

        if row is None:
            raise LocationUserNotFoundError(
                "LOCATION_USER_NOT_AVAILABLE"
            )

    def _get_owned_location(
        self,
        connection: sqlite3.Connection,
        *,
        user_id: int,
        location_id: int,
    ) -> sqlite3.Row:
        row = connection.execute(
            """
            SELECT
                id,
                user_id,
                name,
                location_type,
                notes,
                is_active,
                created_at,
                updated_at
            FROM locations
            WHERE id = ?
              AND user_id = ?;
            """,
            (
                location_id,
                user_id,
            ),
        ).fetchone()

        if row is None:
            raise LocationNotFoundError(
                "LOCATION_NOT_AVAILABLE"
            )

        return row

    def _find_duplicate_name(
        self,
        connection: sqlite3.Connection,
        *,
        user_id: int,
        name: str,
        exclude_location_id:
            int | None = None,
    ) -> sqlite3.Row | None:
        if exclude_location_id is None:
            return connection.execute(
                """
                SELECT id, is_active
                FROM locations
                WHERE user_id = ?
                  AND name = ? COLLATE NOCASE
                LIMIT 1;
                """,
                (
                    user_id,
                    name,
                ),
            ).fetchone()

        return connection.execute(
            """
            SELECT id, is_active
            FROM locations
            WHERE user_id = ?
              AND name = ? COLLATE NOCASE
              AND id != ?
            LIMIT 1;
            """,
            (
                user_id,
                name,
                exclude_location_id,
            ),
        ).fetchone()

    def create_location(
        self,
        *,
        user_id: int,
        name: str,
        location_type: str,
        notes: str | None = None,
    ) -> LocationRecord:
        normalized_name = _validate_name(
            name
        )

        normalized_type = (
            _validate_location_type(
                location_type
            )
        )

        normalized_notes = _normalize_notes(
            notes
        )

        with get_connection(
            self.db_path
        ) as connection:
            self._ensure_user_exists(
                connection,
                user_id,
            )

            duplicate = (
                self._find_duplicate_name(
                    connection,
                    user_id=user_id,
                    name=normalized_name,
                )
            )

            if duplicate is not None:
                raise DuplicateLocationError(
                    "LOCATION_NAME_ALREADY_EXISTS"
                )

            cursor = connection.execute(
                """
                INSERT INTO locations (
                    user_id,
                    name,
                    location_type,
                    notes,
                    is_active
                )
                VALUES (?, ?, ?, ?, 1);
                """,
                (
                    user_id,
                    normalized_name,
                    normalized_type,
                    normalized_notes,
                ),
            )

            location_id = cursor.lastrowid

            row = self._get_owned_location(
                connection,
                user_id=user_id,
                location_id=location_id,
            )

        return _row_to_location(row)

    def get_location(
        self,
        *,
        user_id: int,
        location_id: int,
        include_inactive: bool = False,
    ) -> LocationRecord:
        with get_connection(
            self.db_path
        ) as connection:
            row = self._get_owned_location(
                connection,
                user_id=user_id,
                location_id=location_id,
            )

        location = _row_to_location(row)

        if (
            not include_inactive
            and not location.is_active
        ):
            raise LocationNotFoundError(
                "LOCATION_NOT_AVAILABLE"
            )

        return location

    def list_locations(
        self,
        *,
        user_id: int,
        include_inactive: bool = False,
    ) -> list[LocationRecord]:
        with get_connection(
            self.db_path
        ) as connection:
            self._ensure_user_exists(
                connection,
                user_id,
            )

            if include_inactive:
                rows = connection.execute(
                    """
                    SELECT
                        id,
                        user_id,
                        name,
                        location_type,
                        notes,
                        is_active,
                        created_at,
                        updated_at
                    FROM locations
                    WHERE user_id = ?
                    ORDER BY
                        is_active DESC,
                        name COLLATE NOCASE;
                    """,
                    (user_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT
                        id,
                        user_id,
                        name,
                        location_type,
                        notes,
                        is_active,
                        created_at,
                        updated_at
                    FROM locations
                    WHERE user_id = ?
                      AND is_active = 1
                    ORDER BY
                        name COLLATE NOCASE;
                    """,
                    (user_id,),
                ).fetchall()

        return [
            _row_to_location(row)
            for row in rows
        ]

    def update_location(
        self,
        *,
        user_id: int,
        location_id: int,
        name: str,
        location_type: str,
        notes: str | None = None,
    ) -> LocationRecord:
        """
        장소 정보를 전체 교체한다.

        Discord에서 일부 정보만 수정할 때는 기존 장소를 조회한 뒤,
        바꾸지 않은 값은 기존 값을 그대로 넘기면 된다.
        """

        normalized_name = _validate_name(
            name
        )

        normalized_type = (
            _validate_location_type(
                location_type
            )
        )

        normalized_notes = _normalize_notes(
            notes
        )

        with get_connection(
            self.db_path
        ) as connection:
            self._get_owned_location(
                connection,
                user_id=user_id,
                location_id=location_id,
            )

            duplicate = (
                self._find_duplicate_name(
                    connection,
                    user_id=user_id,
                    name=normalized_name,
                    exclude_location_id=(
                        location_id
                    ),
                )
            )

            if duplicate is not None:
                raise DuplicateLocationError(
                    "LOCATION_NAME_ALREADY_EXISTS"
                )

            connection.execute(
                """
                UPDATE locations
                SET
                    name = ?,
                    location_type = ?,
                    notes = ?,
                    updated_at =
                        CURRENT_TIMESTAMP
                WHERE id = ?
                  AND user_id = ?;
                """,
                (
                    normalized_name,
                    normalized_type,
                    normalized_notes,
                    location_id,
                    user_id,
                ),
            )

            row = self._get_owned_location(
                connection,
                user_id=user_id,
                location_id=location_id,
            )

        return _row_to_location(row)

    def deactivate_location(
        self,
        *,
        user_id: int,
        location_id: int,
    ) -> LocationRecord:
        with get_connection(
            self.db_path
        ) as connection:
            self._get_owned_location(
                connection,
                user_id=user_id,
                location_id=location_id,
            )

            connection.execute(
                """
                UPDATE locations
                SET
                    is_active = 0,
                    updated_at =
                        CURRENT_TIMESTAMP
                WHERE id = ?
                  AND user_id = ?;
                """,
                (
                    location_id,
                    user_id,
                ),
            )

            row = self._get_owned_location(
                connection,
                user_id=user_id,
                location_id=location_id,
            )

        return _row_to_location(row)

    def reactivate_location(
        self,
        *,
        user_id: int,
        location_id: int,
    ) -> LocationRecord:
        with get_connection(
            self.db_path
        ) as connection:
            self._get_owned_location(
                connection,
                user_id=user_id,
                location_id=location_id,
            )

            connection.execute(
                """
                UPDATE locations
                SET
                    is_active = 1,
                    updated_at =
                        CURRENT_TIMESTAMP
                WHERE id = ?
                  AND user_id = ?;
                """,
                (
                    location_id,
                    user_id,
                ),
            )

            row = self._get_owned_location(
                connection,
                user_id=user_id,
                location_id=location_id,
            )

        return _row_to_location(row)

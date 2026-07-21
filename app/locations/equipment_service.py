from __future__ import annotations

import sqlite3

from app.database.connection import (
    DatabasePath,
    get_connection,
)
from app.locations.equipment_models import (
    LocationEquipmentRecord,
)


ALLOWED_WEIGHT_UNITS = {
    "kg",
    "lb",
}


class LocationEquipmentServiceError(
    RuntimeError
):
    pass


class EquipmentNotFoundError(
    LocationEquipmentServiceError
):
    pass


class EquipmentLocationNotFoundError(
    LocationEquipmentServiceError
):
    """
    장소가 없거나 요청한 사용자의 장소가 아닌 경우
    동일한 내부 오류를 사용한다.
    """


class InactiveLocationError(
    LocationEquipmentServiceError
):
    pass


class InvalidEquipmentQuantityError(
    LocationEquipmentServiceError
):
    pass


class InvalidEquipmentWeightError(
    LocationEquipmentServiceError
):
    pass


class InvalidWeightUnitError(
    LocationEquipmentServiceError
):
    pass


def _normalize_quantity(
    quantity: int | None,
) -> int | None:
    if quantity is None:
        return None

    if isinstance(quantity, bool):
        raise InvalidEquipmentQuantityError(
            "INVALID_EQUIPMENT_QUANTITY"
        )

    try:
        normalized = int(quantity)
    except (TypeError, ValueError) as error:
        raise InvalidEquipmentQuantityError(
            "INVALID_EQUIPMENT_QUANTITY"
        ) from error

    if (
        isinstance(quantity, float)
        and not quantity.is_integer()
    ):
        raise InvalidEquipmentQuantityError(
            "INVALID_EQUIPMENT_QUANTITY"
        )

    if normalized <= 0:
        raise InvalidEquipmentQuantityError(
            "INVALID_EQUIPMENT_QUANTITY"
        )

    return normalized


def _normalize_weight(
    value: float | None,
) -> float | None:
    if value is None:
        return None

    if isinstance(value, bool):
        raise InvalidEquipmentWeightError(
            "INVALID_EQUIPMENT_WEIGHT"
        )

    try:
        normalized = float(value)
    except (TypeError, ValueError) as error:
        raise InvalidEquipmentWeightError(
            "INVALID_EQUIPMENT_WEIGHT"
        ) from error

    if normalized < 0:
        raise InvalidEquipmentWeightError(
            "INVALID_EQUIPMENT_WEIGHT"
        )

    return normalized


def _normalize_weight_unit(
    weight_unit: str | None,
) -> str | None:
    if weight_unit is None:
        return None

    normalized = str(
        weight_unit
    ).strip().lower()

    if normalized not in ALLOWED_WEIGHT_UNITS:
        raise InvalidWeightUnitError(
            "INVALID_WEIGHT_UNIT"
        )

    return normalized


def _normalize_notes(
    notes: str | None,
) -> str | None:
    if notes is None:
        return None

    normalized = str(notes).strip()

    return normalized or None


def _row_to_record(
    row: sqlite3.Row,
) -> LocationEquipmentRecord:
    return LocationEquipmentRecord(
        location_id=row["location_id"],
        equipment_id=row["equipment_id"],
        equipment_code=row["equipment_code"],
        quantity=row["quantity"],
        minimum_weight=row["minimum_weight"],
        maximum_weight=row["maximum_weight"],
        weight_unit=row["weight_unit"],
        notes=row["notes"],
    )


class LocationEquipmentService:
    def __init__(
        self,
        db_path: DatabasePath | None = None,
    ) -> None:
        self.db_path = db_path

    def _get_owned_location(
        self,
        connection: sqlite3.Connection,
        *,
        user_id: int,
        location_id: int,
        require_active: bool = False,
    ) -> sqlite3.Row:
        row = connection.execute(
            """
            SELECT
                id,
                is_active
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
            raise EquipmentLocationNotFoundError(
                "LOCATION_NOT_AVAILABLE"
            )

        if (
            require_active
            and not bool(row["is_active"])
        ):
            raise InactiveLocationError(
                "LOCATION_INACTIVE"
            )

        return row

    def _get_equipment(
        self,
        connection: sqlite3.Connection,
        *,
        equipment_code: str,
    ) -> sqlite3.Row:
        normalized_code = str(
            equipment_code
        ).strip().lower()

        if not normalized_code:
            raise EquipmentNotFoundError(
                "EQUIPMENT_NOT_AVAILABLE"
            )

        row = connection.execute(
            """
            SELECT
                id,
                code
            FROM equipment
            WHERE code = ?;
            """,
            (normalized_code,),
        ).fetchone()

        if row is None:
            raise EquipmentNotFoundError(
                "EQUIPMENT_NOT_AVAILABLE"
            )

        return row

    def _get_link(
        self,
        connection: sqlite3.Connection,
        *,
        location_id: int,
        equipment_id: int,
    ) -> sqlite3.Row | None:
        return connection.execute(
            """
            SELECT
                le.location_id,
                le.equipment_id,
                e.code AS equipment_code,
                le.quantity,
                le.minimum_weight,
                le.maximum_weight,
                le.weight_unit,
                le.notes
            FROM location_equipment AS le
            JOIN equipment AS e
              ON e.id = le.equipment_id
            WHERE le.location_id = ?
              AND le.equipment_id = ?;
            """,
            (
                location_id,
                equipment_id,
            ),
        ).fetchone()

    def set_location_equipment(
        self,
        *,
        user_id: int,
        location_id: int,
        equipment_code: str,
        quantity: int | None = None,
        minimum_weight: float | None = None,
        maximum_weight: float | None = None,
        weight_unit: str | None = None,
        notes: str | None = None,
    ) -> LocationEquipmentRecord:
        normalized_quantity = (
            _normalize_quantity(quantity)
        )

        normalized_minimum = (
            _normalize_weight(
                minimum_weight
            )
        )

        normalized_maximum = (
            _normalize_weight(
                maximum_weight
            )
        )

        normalized_unit = (
            _normalize_weight_unit(
                weight_unit
            )
        )

        normalized_notes = (
            _normalize_notes(notes)
        )

        if (
            normalized_minimum is not None
            and normalized_maximum is not None
            and normalized_minimum
            > normalized_maximum
        ):
            raise InvalidEquipmentWeightError(
                "MINIMUM_WEIGHT_EXCEEDS_MAXIMUM"
            )

        if (
            (
                normalized_minimum is not None
                or normalized_maximum is not None
            )
            and normalized_unit is None
        ):
            raise InvalidWeightUnitError(
                "WEIGHT_UNIT_REQUIRED"
            )

        with get_connection(
            self.db_path
        ) as connection:
            self._get_owned_location(
                connection,
                user_id=user_id,
                location_id=location_id,
                require_active=True,
            )

            equipment = self._get_equipment(
                connection,
                equipment_code=equipment_code,
            )

            existing = self._get_link(
                connection,
                location_id=location_id,
                equipment_id=equipment["id"],
            )

            if existing is None:
                connection.execute(
                    """
                    INSERT INTO location_equipment (
                        location_id,
                        equipment_id,
                        quantity,
                        minimum_weight,
                        maximum_weight,
                        weight_unit,
                        notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        location_id,
                        equipment["id"],
                        normalized_quantity,
                        normalized_minimum,
                        normalized_maximum,
                        normalized_unit,
                        normalized_notes,
                    ),
                )
            else:
                connection.execute(
                    """
                    UPDATE location_equipment
                    SET
                        quantity = ?,
                        minimum_weight = ?,
                        maximum_weight = ?,
                        weight_unit = ?,
                        notes = ?
                    WHERE location_id = ?
                      AND equipment_id = ?;
                    """,
                    (
                        normalized_quantity,
                        normalized_minimum,
                        normalized_maximum,
                        normalized_unit,
                        normalized_notes,
                        location_id,
                        equipment["id"],
                    ),
                )

            row = self._get_link(
                connection,
                location_id=location_id,
                equipment_id=equipment["id"],
            )

        if row is None:
            raise LocationEquipmentServiceError(
                "LOCATION_EQUIPMENT_RELOAD_FAILED"
            )

        return _row_to_record(row)

    def get_location_equipment(
        self,
        *,
        user_id: int,
        location_id: int,
        equipment_code: str,
    ) -> LocationEquipmentRecord | None:
        with get_connection(
            self.db_path
        ) as connection:
            self._get_owned_location(
                connection,
                user_id=user_id,
                location_id=location_id,
            )

            equipment = self._get_equipment(
                connection,
                equipment_code=equipment_code,
            )

            row = self._get_link(
                connection,
                location_id=location_id,
                equipment_id=equipment["id"],
            )

        if row is None:
            return None

        return _row_to_record(row)

    def list_location_equipment(
        self,
        *,
        user_id: int,
        location_id: int,
    ) -> list[LocationEquipmentRecord]:
        with get_connection(
            self.db_path
        ) as connection:
            self._get_owned_location(
                connection,
                user_id=user_id,
                location_id=location_id,
            )

            rows = connection.execute(
                """
                SELECT
                    le.location_id,
                    le.equipment_id,
                    e.code AS equipment_code,
                    le.quantity,
                    le.minimum_weight,
                    le.maximum_weight,
                    le.weight_unit,
                    le.notes
                FROM location_equipment AS le
                JOIN equipment AS e
                  ON e.id = le.equipment_id
                WHERE le.location_id = ?
                ORDER BY e.code;
                """,
                (location_id,),
            ).fetchall()

        return [
            _row_to_record(row)
            for row in rows
        ]

    def remove_location_equipment(
        self,
        *,
        user_id: int,
        location_id: int,
        equipment_code: str,
    ) -> bool:
        with get_connection(
            self.db_path
        ) as connection:
            self._get_owned_location(
                connection,
                user_id=user_id,
                location_id=location_id,
                require_active=True,
            )

            equipment = self._get_equipment(
                connection,
                equipment_code=equipment_code,
            )

            cursor = connection.execute(
                """
                DELETE FROM location_equipment
                WHERE location_id = ?
                  AND equipment_id = ?;
                """,
                (
                    location_id,
                    equipment["id"],
                ),
            )

            return cursor.rowcount > 0

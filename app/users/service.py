from __future__ import annotations

from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.database.connection import (
    DatabasePath,
    get_connection,
)


class UserServiceError(RuntimeError):
    pass


class InvalidDiscordUserIdError(UserServiceError):
    pass


class InvalidTimezoneError(UserServiceError):
    pass


class UserNotFoundError(UserServiceError):
    pass


@dataclass(frozen=True)
class UserRecord:
    id: int
    discord_user_id: str
    display_name: str
    timezone: str


def _validate_discord_user_id(
    discord_user_id: str,
) -> str:
    normalized = str(discord_user_id).strip()

    if not normalized:
        raise InvalidDiscordUserIdError(
            "Discord user ID is required."
        )

    if not normalized.isdigit():
        raise InvalidDiscordUserIdError(
            "Discord user ID must contain only digits."
        )

    return normalized


def _validate_display_name(
    display_name: str,
) -> str:
    normalized = str(display_name).strip()

    if not normalized:
        raise ValueError(
            "Display name is required."
        )

    return normalized


def _validate_timezone(
    timezone: str,
) -> str:
    normalized = str(timezone).strip()

    if not normalized:
        raise InvalidTimezoneError(
            "Timezone is required."
        )

    try:
        ZoneInfo(normalized)
    except ZoneInfoNotFoundError as error:
        raise InvalidTimezoneError(
            f"Unknown timezone: {normalized}"
        ) from error

    return normalized


def _row_to_user(row: object) -> UserRecord:
    return UserRecord(
        id=row["id"],
        discord_user_id=row["discord_user_id"],
        display_name=row["display_name"],
        timezone=row["timezone"],
    )


class UserService:
    def __init__(
        self,
        db_path: DatabasePath | None = None,
    ) -> None:
        self.db_path = db_path

    def get_by_id(
        self,
        user_id: int,
    ) -> UserRecord:
        with get_connection(
            self.db_path
        ) as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    discord_user_id,
                    display_name,
                    timezone
                FROM users
                WHERE id = ?;
                """,
                (user_id,),
            ).fetchone()

        if row is None:
            raise UserNotFoundError(
                f"User not found: {user_id}"
            )

        return _row_to_user(row)

    def get_by_discord_id(
        self,
        discord_user_id: str,
    ) -> UserRecord | None:
        normalized_id = _validate_discord_user_id(
            discord_user_id
        )

        with get_connection(
            self.db_path
        ) as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    discord_user_id,
                    display_name,
                    timezone
                FROM users
                WHERE discord_user_id = ?;
                """,
                (normalized_id,),
            ).fetchone()

        if row is None:
            return None

        return _row_to_user(row)

    def get_or_create(
        self,
        *,
        discord_user_id: str,
        display_name: str,
        timezone: str = "Asia/Seoul",
    ) -> UserRecord:
        normalized_id = _validate_discord_user_id(
            discord_user_id
        )
        normalized_name = _validate_display_name(
            display_name
        )
        normalized_timezone = _validate_timezone(
            timezone
        )

        with get_connection(
            self.db_path
        ) as connection:
            connection.execute(
                """
                INSERT INTO users (
                    discord_user_id,
                    display_name,
                    timezone
                )
                VALUES (?, ?, ?)
                ON CONFLICT(discord_user_id)
                DO UPDATE SET
                    display_name =
                        excluded.display_name,
                    timezone =
                        excluded.timezone,
                    updated_at =
                        CURRENT_TIMESTAMP;
                """,
                (
                    normalized_id,
                    normalized_name,
                    normalized_timezone,
                ),
            )

            row = connection.execute(
                """
                SELECT
                    id,
                    discord_user_id,
                    display_name,
                    timezone
                FROM users
                WHERE discord_user_id = ?;
                """,
                (normalized_id,),
            ).fetchone()

        if row is None:
            raise UserServiceError(
                "User creation succeeded but "
                "the user could not be reloaded."
            )

        return _row_to_user(row)

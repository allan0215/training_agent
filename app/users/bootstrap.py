from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.database.connection import DatabasePath
from app.settings import (
    DEFAULT_ENV_PATH,
    load_env_file,
)
from app.users.service import (
    UserRecord,
    UserService,
)


class OwnerBootstrapError(RuntimeError):
    pass


@dataclass(frozen=True)
class OwnerBootstrapConfig:
    discord_user_id: str
    display_name: str
    timezone: str


def load_owner_bootstrap_config(
    env_path: str | Path = DEFAULT_ENV_PATH,
) -> OwnerBootstrapConfig:
    load_env_file(env_path)

    discord_user_id = os.getenv(
        "TRAINING_AGENT_OWNER_DISCORD_ID",
        "",
    ).strip()

    display_name = os.getenv(
        "TRAINING_AGENT_OWNER_DISPLAY_NAME",
        "Hyunsoo",
    ).strip()

    timezone = os.getenv(
        "TRAINING_AGENT_DEFAULT_TIMEZONE",
        "Asia/Seoul",
    ).strip()

    if not discord_user_id:
        raise OwnerBootstrapError(
            "TRAINING_AGENT_OWNER_DISCORD_ID "
            "is not configured."
        )

    if not display_name:
        raise OwnerBootstrapError(
            "TRAINING_AGENT_OWNER_DISPLAY_NAME "
            "is empty."
        )

    if not timezone:
        raise OwnerBootstrapError(
            "TRAINING_AGENT_DEFAULT_TIMEZONE "
            "is empty."
        )

    return OwnerBootstrapConfig(
        discord_user_id=discord_user_id,
        display_name=display_name,
        timezone=timezone,
    )


def bootstrap_owner(
    *,
    db_path: DatabasePath | None = None,
    env_path: str | Path = DEFAULT_ENV_PATH,
) -> UserRecord:
    config = load_owner_bootstrap_config(
        env_path
    )

    service = UserService(db_path=db_path)

    return service.get_or_create(
        discord_user_id=config.discord_user_id,
        display_name=config.display_name,
        timezone=config.timezone,
    )


def get_configured_owner(
    *,
    db_path: DatabasePath | None = None,
    env_path: str | Path = DEFAULT_ENV_PATH,
) -> UserRecord:
    config = load_owner_bootstrap_config(
        env_path
    )

    service = UserService(db_path=db_path)

    user = service.get_by_discord_id(
        config.discord_user_id
    )

    if user is None:
        raise OwnerBootstrapError(
            "The configured owner has not been "
            "bootstrapped yet."
        )

    return user

from __future__ import annotations

import os
from dataclasses import dataclass


class CatalogPermissionError(PermissionError):
    pass


@dataclass(frozen=True)
class CatalogPermissionPolicy:
    """
    공용 운동 카탈로그 관리 권한 정책.

    owner:
        TRAINING_AGENT_OWNER_DISCORD_ID와 일치하는
        한 명만 공용 카탈로그를 관리한다.

    admin:
        CATALOG_ADMIN_DISCORD_IDS에 등록된 사용자만
        공용 카탈로그를 관리한다.

    disabled:
        실행 중인 애플리케이션에서는 공용 카탈로그를
        수정할 수 없다.
    """

    mode: str
    owner_discord_id: str | None = None
    admin_discord_ids: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if self.mode not in {
            "owner",
            "admin",
            "disabled",
        }:
            raise ValueError(
                f"Unsupported core catalog write mode: "
                f"{self.mode}"
            )

    @classmethod
    def from_environment(
        cls,
    ) -> "CatalogPermissionPolicy":
        mode = os.getenv(
            "CATALOG_CORE_WRITE_MODE",
            "disabled",
        ).strip().lower()

        owner_discord_id = (
            os.getenv(
                "TRAINING_AGENT_OWNER_DISCORD_ID"
            )
            or None
        )

        raw_admin_ids = os.getenv(
            "CATALOG_ADMIN_DISCORD_IDS",
            "",
        )

        admin_discord_ids = frozenset(
            value.strip()
            for value in raw_admin_ids.split(",")
            if value.strip()
        )

        return cls(
            mode=mode,
            owner_discord_id=owner_discord_id,
            admin_discord_ids=admin_discord_ids,
        )

    def can_manage_core_catalog(
        self,
        actor_discord_id: str,
    ) -> bool:
        if self.mode == "disabled":
            return False

        if self.mode == "owner":
            return (
                self.owner_discord_id is not None
                and actor_discord_id
                == self.owner_discord_id
            )

        if self.mode == "admin":
            return (
                actor_discord_id
                in self.admin_discord_ids
            )

        return False

    def require_core_catalog_permission(
        self,
        actor_discord_id: str,
    ) -> None:
        if not self.can_manage_core_catalog(
            actor_discord_id
        ):
            raise CatalogPermissionError(
                "공용 운동 카탈로그 관리 권한이 없습니다."
            )

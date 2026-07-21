from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.database.migrations import run_migrations
from app.users.bootstrap import (
    bootstrap_owner,
    get_configured_owner,
)
from app.users.service import (
    InvalidDiscordUserIdError,
    InvalidTimezoneError,
    UserService,
)


class UserServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.db_path = (
            Path(self.temp_directory.name)
            / "test_training_agent.db"
        )

        self.missing_env_path = (
            Path(self.temp_directory.name)
            / "missing.env"
        )

        run_migrations(db_path=self.db_path)

        self.service = UserService(
            db_path=self.db_path
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_get_or_create_creates_user(
        self,
    ) -> None:
        user = self.service.get_or_create(
            discord_user_id="123456789012345678",
            display_name="Hyunsoo",
            timezone="Asia/Seoul",
        )

        self.assertGreater(user.id, 0)
        self.assertEqual(
            user.discord_user_id,
            "123456789012345678",
        )
        self.assertEqual(
            user.display_name,
            "Hyunsoo",
        )
        self.assertEqual(
            user.timezone,
            "Asia/Seoul",
        )

    def test_get_or_create_is_idempotent_and_updates(
        self,
    ) -> None:
        first = self.service.get_or_create(
            discord_user_id="123456789012345678",
            display_name="Old Name",
            timezone="UTC",
        )

        second = self.service.get_or_create(
            discord_user_id="123456789012345678",
            display_name="New Name",
            timezone="Asia/Seoul",
        )

        self.assertEqual(
            first.id,
            second.id,
        )
        self.assertEqual(
            second.display_name,
            "New Name",
        )
        self.assertEqual(
            second.timezone,
            "Asia/Seoul",
        )

    def test_different_discord_ids_create_users(
        self,
    ) -> None:
        first = self.service.get_or_create(
            discord_user_id="111111111111111111",
            display_name="First User",
        )

        second = self.service.get_or_create(
            discord_user_id="222222222222222222",
            display_name="Second User",
        )

        self.assertNotEqual(
            first.id,
            second.id,
        )

    def test_invalid_identity_and_timezone_rejected(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidDiscordUserIdError
        ):
            self.service.get_or_create(
                discord_user_id="not-a-discord-id",
                display_name="Invalid",
            )

        with self.assertRaises(
            InvalidTimezoneError
        ):
            self.service.get_or_create(
                discord_user_id="123456789012345678",
                display_name="Invalid",
                timezone="Moon/Base",
            )

    def test_owner_bootstrap_uses_generic_service(
        self,
    ) -> None:
        environment = {
            "TRAINING_AGENT_OWNER_DISCORD_ID":
                "123456789012345678",
            "TRAINING_AGENT_OWNER_DISPLAY_NAME":
                "Hyunsoo",
            "TRAINING_AGENT_DEFAULT_TIMEZONE":
                "Asia/Seoul",
        }

        with patch.dict(
            os.environ,
            environment,
            clear=False,
        ):
            first = bootstrap_owner(
                db_path=self.db_path,
                env_path=self.missing_env_path,
            )

            second = get_configured_owner(
                db_path=self.db_path,
                env_path=self.missing_env_path,
            )

        self.assertEqual(first.id, second.id)
        self.assertEqual(
            second.discord_user_id,
            "123456789012345678",
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import (
    redirect_stderr,
    redirect_stdout,
)
from pathlib import Path
from unittest.mock import patch

from app.database.catalog_seed import (
    seed_catalog,
)
from app.database.migrations import (
    run_migrations,
)
from app.locations.cli import main
from app.users.service import UserService


class LocationsCliTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.db_path = (
            Path(self.temp_directory.name)
            / "training_agent.db"
        )

        self.env_path = (
            Path(self.temp_directory.name)
            / "unused.env"
        )

        run_migrations(
            db_path=self.db_path
        )

        seed_catalog(
            db_path=self.db_path
        )

        self.discord_user_id = (
            "111111111111111111"
        )

        user_service = UserService(
            db_path=self.db_path
        )

        self.owner = (
            user_service.get_or_create(
                discord_user_id=(
                    self.discord_user_id
                ),
                display_name="Owner",
                timezone="Asia/Seoul",
            )
        )

        self.environment = {
            "TRAINING_AGENT_OWNER_DISCORD_ID":
                self.discord_user_id,
            "TRAINING_AGENT_OWNER_DISPLAY_NAME":
                "Owner",
            "TRAINING_AGENT_DEFAULT_TIMEZONE":
                "Asia/Seoul",
        }

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def invoke(
        self,
        *arguments: str,
    ) -> tuple[
        int,
        str,
        str,
    ]:
        stdout = io.StringIO()
        stderr = io.StringIO()

        argv = [
            "--db-path",
            str(self.db_path),
            "--env-path",
            str(self.env_path),
            *arguments,
        ]

        with patch.dict(
            os.environ,
            self.environment,
            clear=False,
        ):
            with redirect_stdout(stdout):
                with redirect_stderr(stderr):
                    exit_code = main(argv)

        return (
            exit_code,
            stdout.getvalue(),
            stderr.getvalue(),
        )

    def test_add_and_list_location(
        self,
    ) -> None:
        exit_code, output, error = (
            self.invoke(
                "add",
                "--name",
                "Main Box",
                "--type",
                "crossfit_box",
                "--notes",
                "Primary location",
            )
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(error, "")

        created = json.loads(output)

        self.assertEqual(
            created["status"],
            "created",
        )

        self.assertEqual(
            created["location"]["name"],
            "Main Box",
        )

        exit_code, output, error = (
            self.invoke("list")
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(error, "")

        listed = json.loads(output)

        self.assertEqual(
            listed["count"],
            1,
        )

        self.assertEqual(
            listed["locations"][0]["name"],
            "Main Box",
        )

    def test_update_deactivate_reactivate(
        self,
    ) -> None:
        _, output, _ = self.invoke(
            "add",
            "--name",
            "Old Gym",
            "--type",
            "commercial_gym",
        )

        location_id = (
            json.loads(output)
            ["location"]["id"]
        )

        exit_code, output, error = (
            self.invoke(
                "update",
                "--location-id",
                str(location_id),
                "--name",
                "New Gym",
                "--notes",
                "Updated",
            )
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(error, "")

        updated = json.loads(output)

        self.assertEqual(
            updated["location"]["name"],
            "New Gym",
        )

        self.assertEqual(
            updated["location"]["location_type"],
            "commercial_gym",
        )

        exit_code, output, _ = (
            self.invoke(
                "deactivate",
                "--location-id",
                str(location_id),
            )
        )

        self.assertEqual(exit_code, 0)

        deactivated = json.loads(output)

        self.assertFalse(
            deactivated["location"]["is_active"]
        )

        _, output, _ = self.invoke(
            "list"
        )

        self.assertEqual(
            json.loads(output)["count"],
            0,
        )

        _, output, _ = self.invoke(
            "list",
            "--all",
        )

        self.assertEqual(
            json.loads(output)["count"],
            1,
        )

        exit_code, output, _ = (
            self.invoke(
                "reactivate",
                "--location-id",
                str(location_id),
            )
        )

        self.assertEqual(exit_code, 0)

        reactivated = json.loads(output)

        self.assertTrue(
            reactivated["location"]["is_active"]
        )

    def test_equipment_set_partial_update_and_remove(
        self,
    ) -> None:
        _, output, _ = self.invoke(
            "add",
            "--name",
            "Main Gym",
            "--type",
            "commercial_gym",
        )

        location_id = (
            json.loads(output)
            ["location"]["id"]
        )

        exit_code, output, error = (
            self.invoke(
                "equipment-set",
                "--location-id",
                str(location_id),
                "--equipment",
                "dumbbell",
                "--max-weight",
                "40",
                "--unit",
                "kg",
                "--notes",
                "Dumbbell rack",
            )
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(error, "")

        created = json.loads(output)

        self.assertEqual(
            created["status"],
            "created",
        )

        self.assertEqual(
            created["equipment"]
            ["maximum_weight"],
            40.0,
        )

        exit_code, output, error = (
            self.invoke(
                "equipment-set",
                "--location-id",
                str(location_id),
                "--equipment",
                "dumbbell",
                "--quantity",
                "20",
            )
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(error, "")

        updated = json.loads(output)

        self.assertEqual(
            updated["status"],
            "updated",
        )

        self.assertEqual(
            updated["equipment"]["quantity"],
            20,
        )

        self.assertEqual(
            updated["equipment"]
            ["maximum_weight"],
            40.0,
        )

        self.assertEqual(
            updated["equipment"]
            ["weight_unit"],
            "kg",
        )

        _, output, _ = self.invoke(
            "equipment-list",
            "--location-id",
            str(location_id),
        )

        listed = json.loads(output)

        self.assertEqual(
            listed["count"],
            1,
        )

        exit_code, output, error = (
            self.invoke(
                "equipment-remove",
                "--location-id",
                str(location_id),
                "--equipment",
                "dumbbell",
            )
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(error, "")

        removed = json.loads(output)

        self.assertEqual(
            removed["status"],
            "removed",
        )

    def test_service_error_returns_nonzero_exit_code(
        self,
    ) -> None:
        exit_code, output, error = (
            self.invoke(
                "equipment-set",
                "--location-id",
                "99999",
                "--equipment",
                "barbell",
            )
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(output, "")
        self.assertIn(
            "Command failed:",
            error,
        )


if __name__ == "__main__":
    unittest.main()

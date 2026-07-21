from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.database.migrations import (
    run_migrations,
)
from app.locations.service import (
    DuplicateLocationError,
    InvalidLocationTypeError,
    LocationNotFoundError,
    LocationService,
)
from app.users.service import UserService


class LocationServiceTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.db_path = (
            Path(self.temp_directory.name)
            / "test_training_agent.db"
        )

        run_migrations(
            db_path=self.db_path
        )

        user_service = UserService(
            db_path=self.db_path
        )

        self.owner = (
            user_service.get_or_create(
                discord_user_id=(
                    "111111111111111111"
                ),
                display_name="Owner",
            )
        )

        self.other_user = (
            user_service.get_or_create(
                discord_user_id=(
                    "222222222222222222"
                ),
                display_name="Other",
            )
        )

        self.service = LocationService(
            db_path=self.db_path
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_create_and_list_location(
        self,
    ) -> None:
        created = (
            self.service.create_location(
                user_id=self.owner.id,
                name="Main CrossFit Box",
                location_type=(
                    "crossfit_box"
                ),
                notes="Primary training location",
            )
        )

        locations = (
            self.service.list_locations(
                user_id=self.owner.id
            )
        )

        self.assertEqual(
            len(locations),
            1,
        )

        self.assertEqual(
            locations[0].id,
            created.id,
        )

        self.assertEqual(
            locations[0].name,
            "Main CrossFit Box",
        )

        self.assertTrue(
            locations[0].is_active
        )

    def test_same_name_is_rejected_for_same_user(
        self,
    ) -> None:
        self.service.create_location(
            user_id=self.owner.id,
            name="헬스장",
            location_type=(
                "commercial_gym"
            ),
        )

        with self.assertRaises(
            DuplicateLocationError
        ):
            self.service.create_location(
                user_id=self.owner.id,
                name="헬스장",
                location_type=(
                    "commercial_gym"
                ),
            )

        with self.assertRaises(
            DuplicateLocationError
        ):
            self.service.create_location(
                user_id=self.owner.id,
                name="헬스장",
                location_type="other",
            )

    def test_same_name_allowed_for_different_users(
        self,
    ) -> None:
        first = (
            self.service.create_location(
                user_id=self.owner.id,
                name="Main Gym",
                location_type=(
                    "commercial_gym"
                ),
            )
        )

        second = (
            self.service.create_location(
                user_id=self.other_user.id,
                name="Main Gym",
                location_type=(
                    "commercial_gym"
                ),
            )
        )

        self.assertNotEqual(
            first.id,
            second.id,
        )

        self.assertNotEqual(
            first.user_id,
            second.user_id,
        )

    def test_update_location(
        self,
    ) -> None:
        created = (
            self.service.create_location(
                user_id=self.owner.id,
                name="Old Gym",
                location_type=(
                    "commercial_gym"
                ),
            )
        )

        updated = (
            self.service.update_location(
                user_id=self.owner.id,
                location_id=created.id,
                name="New Gym",
                location_type="home_gym",
                notes="Updated notes",
            )
        )

        self.assertEqual(
            updated.name,
            "New Gym",
        )

        self.assertEqual(
            updated.location_type,
            "home_gym",
        )

        self.assertEqual(
            updated.notes,
            "Updated notes",
        )

    def test_other_user_cannot_access_location(
        self,
    ) -> None:
        created = (
            self.service.create_location(
                user_id=self.owner.id,
                name="Private Gym",
                location_type=(
                    "home_gym"
                ),
            )
        )

        with self.assertRaises(
            LocationNotFoundError
        ):
            self.service.get_location(
                user_id=self.other_user.id,
                location_id=created.id,
            )

        with self.assertRaises(
            LocationNotFoundError
        ):
            self.service.update_location(
                user_id=self.other_user.id,
                location_id=created.id,
                name="Modified",
                location_type="other",
            )

    def test_deactivate_and_reactivate_location(
        self,
    ) -> None:
        created = (
            self.service.create_location(
                user_id=self.owner.id,
                name="Temporary Gym",
                location_type=(
                    "temporary_location"
                ),
            )
        )

        deactivated = (
            self.service.deactivate_location(
                user_id=self.owner.id,
                location_id=created.id,
            )
        )

        self.assertFalse(
            deactivated.is_active
        )

        active_locations = (
            self.service.list_locations(
                user_id=self.owner.id
            )
        )

        self.assertEqual(
            active_locations,
            [],
        )

        all_locations = (
            self.service.list_locations(
                user_id=self.owner.id,
                include_inactive=True,
            )
        )

        self.assertEqual(
            len(all_locations),
            1,
        )

        with self.assertRaises(
            LocationNotFoundError
        ):
            self.service.get_location(
                user_id=self.owner.id,
                location_id=created.id,
            )

        inactive = (
            self.service.get_location(
                user_id=self.owner.id,
                location_id=created.id,
                include_inactive=True,
            )
        )

        self.assertFalse(
            inactive.is_active
        )

        reactivated = (
            self.service.reactivate_location(
                user_id=self.owner.id,
                location_id=created.id,
            )
        )

        self.assertTrue(
            reactivated.is_active
        )

    def test_invalid_location_type_rejected(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidLocationTypeError
        ):
            self.service.create_location(
                user_id=self.owner.id,
                name="Moon Gym",
                location_type="lunar_base",
            )


if __name__ == "__main__":
    unittest.main()

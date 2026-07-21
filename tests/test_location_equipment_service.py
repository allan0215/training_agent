from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.database.catalog_seed import (
    seed_catalog,
)
from app.database.migrations import (
    run_migrations,
)
from app.locations.equipment_service import (
    EquipmentLocationNotFoundError,
    EquipmentNotFoundError,
    InactiveLocationError,
    InvalidEquipmentQuantityError,
    InvalidEquipmentWeightError,
    InvalidWeightUnitError,
    LocationEquipmentService,
)
from app.locations.service import (
    LocationService,
)
from app.users.service import UserService


class LocationEquipmentServiceTests(
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

        seed_catalog(
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

        location_service = LocationService(
            db_path=self.db_path
        )

        self.box = (
            location_service.create_location(
                user_id=self.owner.id,
                name="Main Box",
                location_type="crossfit_box",
            )
        )

        self.gym = (
            location_service.create_location(
                user_id=self.owner.id,
                name="Main Gym",
                location_type="commercial_gym",
            )
        )

        self.other_location = (
            location_service.create_location(
                user_id=self.other_user.id,
                name="Other Gym",
                location_type="commercial_gym",
            )
        )

        self.location_service = (
            location_service
        )

        self.service = (
            LocationEquipmentService(
                db_path=self.db_path
            )
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_set_and_list_equipment(
        self,
    ) -> None:
        created = (
            self.service
            .set_location_equipment(
                user_id=self.owner.id,
                location_id=self.box.id,
                equipment_code="barbell",
                quantity=8,
                maximum_weight=20,
                weight_unit="kg",
                notes="20kg bars",
            )
        )

        self.assertEqual(
            created.equipment_code,
            "barbell",
        )

        self.assertEqual(
            created.quantity,
            8,
        )

        equipment = (
            self.service
            .list_location_equipment(
                user_id=self.owner.id,
                location_id=self.box.id,
            )
        )

        self.assertEqual(
            len(equipment),
            1,
        )

        self.assertEqual(
            equipment[0],
            created,
        )

    def test_set_updates_existing_link(
        self,
    ) -> None:
        first = (
            self.service
            .set_location_equipment(
                user_id=self.owner.id,
                location_id=self.gym.id,
                equipment_code="dumbbell",
                maximum_weight=40,
                weight_unit="kg",
            )
        )

        second = (
            self.service
            .set_location_equipment(
                user_id=self.owner.id,
                location_id=self.gym.id,
                equipment_code="dumbbell",
                quantity=30,
                minimum_weight=2.5,
                maximum_weight=50,
                weight_unit="kg",
                notes="Updated range",
            )
        )

        self.assertEqual(
            first.equipment_id,
            second.equipment_id,
        )

        self.assertEqual(
            second.quantity,
            30,
        )

        self.assertEqual(
            second.minimum_weight,
            2.5,
        )

        self.assertEqual(
            second.maximum_weight,
            50.0,
        )

        equipment = (
            self.service
            .list_location_equipment(
                user_id=self.owner.id,
                location_id=self.gym.id,
            )
        )

        self.assertEqual(
            len(equipment),
            1,
        )

    def test_same_equipment_allowed_at_multiple_locations(
        self,
    ) -> None:
        box_equipment = (
            self.service
            .set_location_equipment(
                user_id=self.owner.id,
                location_id=self.box.id,
                equipment_code="barbell",
            )
        )

        gym_equipment = (
            self.service
            .set_location_equipment(
                user_id=self.owner.id,
                location_id=self.gym.id,
                equipment_code="barbell",
            )
        )

        self.assertNotEqual(
            box_equipment.location_id,
            gym_equipment.location_id,
        )

        self.assertEqual(
            box_equipment.equipment_id,
            gym_equipment.equipment_id,
        )

    def test_unknown_equipment_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(
            EquipmentNotFoundError
        ):
            self.service.set_location_equipment(
                user_id=self.owner.id,
                location_id=self.box.id,
                equipment_code=(
                    "teleport_machine"
                ),
            )

    def test_invalid_quantity_and_weights_rejected(
        self,
    ) -> None:
        with self.assertRaises(
            InvalidEquipmentQuantityError
        ):
            self.service.set_location_equipment(
                user_id=self.owner.id,
                location_id=self.box.id,
                equipment_code="barbell",
                quantity=0,
            )

        with self.assertRaises(
            InvalidEquipmentWeightError
        ):
            self.service.set_location_equipment(
                user_id=self.owner.id,
                location_id=self.box.id,
                equipment_code="barbell",
                minimum_weight=30,
                maximum_weight=20,
                weight_unit="kg",
            )

        with self.assertRaises(
            InvalidWeightUnitError
        ):
            self.service.set_location_equipment(
                user_id=self.owner.id,
                location_id=self.box.id,
                equipment_code="barbell",
                maximum_weight=20,
            )

        with self.assertRaises(
            InvalidWeightUnitError
        ):
            self.service.set_location_equipment(
                user_id=self.owner.id,
                location_id=self.box.id,
                equipment_code="barbell",
                maximum_weight=20,
                weight_unit="stone",
            )

    def test_other_user_cannot_access_location(
        self,
    ) -> None:
        with self.assertRaises(
            EquipmentLocationNotFoundError
        ):
            self.service.set_location_equipment(
                user_id=self.other_user.id,
                location_id=self.box.id,
                equipment_code="barbell",
            )

        with self.assertRaises(
            EquipmentLocationNotFoundError
        ):
            self.service.list_location_equipment(
                user_id=self.other_user.id,
                location_id=self.box.id,
            )

    def test_remove_equipment_is_idempotent(
        self,
    ) -> None:
        self.service.set_location_equipment(
            user_id=self.owner.id,
            location_id=self.box.id,
            equipment_code="barbell",
        )

        first_removed = (
            self.service
            .remove_location_equipment(
                user_id=self.owner.id,
                location_id=self.box.id,
                equipment_code="barbell",
            )
        )

        second_removed = (
            self.service
            .remove_location_equipment(
                user_id=self.owner.id,
                location_id=self.box.id,
                equipment_code="barbell",
            )
        )

        self.assertTrue(first_removed)
        self.assertFalse(second_removed)

        self.assertEqual(
            self.service.list_location_equipment(
                user_id=self.owner.id,
                location_id=self.box.id,
            ),
            [],
        )

    def test_inactive_location_is_read_only(
        self,
    ) -> None:
        self.service.set_location_equipment(
            user_id=self.owner.id,
            location_id=self.box.id,
            equipment_code="barbell",
        )

        self.location_service.deactivate_location(
            user_id=self.owner.id,
            location_id=self.box.id,
        )

        equipment = (
            self.service
            .list_location_equipment(
                user_id=self.owner.id,
                location_id=self.box.id,
            )
        )

        self.assertEqual(
            len(equipment),
            1,
        )

        with self.assertRaises(
            InactiveLocationError
        ):
            self.service.set_location_equipment(
                user_id=self.owner.id,
                location_id=self.box.id,
                equipment_code="dumbbell",
            )

        with self.assertRaises(
            InactiveLocationError
        ):
            self.service.remove_location_equipment(
                user_id=self.owner.id,
                location_id=self.box.id,
                equipment_code="barbell",
            )


if __name__ == "__main__":
    unittest.main()

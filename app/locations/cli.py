from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from app.database.connection import DatabasePath
from app.locations.equipment_service import (
    LocationEquipmentService,
    LocationEquipmentServiceError,
)
from app.locations.service import (
    LocationService,
    LocationServiceError,
)
from app.settings import DEFAULT_ENV_PATH
from app.users.bootstrap import (
    OwnerBootstrapError,
    get_configured_owner,
)


def _print_json(value: object) -> None:
    print(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


def _location_payload(
    location: object,
) -> dict[str, object]:
    return asdict(location)


def _equipment_payload(
    equipment: object,
) -> dict[str, object]:
    return asdict(equipment)


def _add_runtime_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help=(
            "Override the database path. "
            "Normally omitted."
        ),
    )

    parser.add_argument(
        "--env-path",
        type=Path,
        default=DEFAULT_ENV_PATH,
        help=(
            "Path to the environment file. "
            "Normally omitted."
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Manage the configured owner's "
            "training locations and equipment."
        )
    )

    _add_runtime_arguments(parser)

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # -----------------------------------------------------
    # Location commands
    # -----------------------------------------------------

    add_parser = subparsers.add_parser(
        "add",
        help="Create a training location.",
    )

    add_parser.add_argument(
        "--name",
        required=True,
    )

    add_parser.add_argument(
        "--type",
        dest="location_type",
        required=True,
        choices=[
            "home_gym",
            "commercial_gym",
            "crossfit_box",
            "outdoor",
            "temporary_location",
            "other",
        ],
    )

    add_parser.add_argument(
        "--notes",
    )

    list_parser = subparsers.add_parser(
        "list",
        help="List training locations.",
    )

    list_parser.add_argument(
        "--all",
        action="store_true",
        help="Include inactive locations.",
    )

    show_parser = subparsers.add_parser(
        "show",
        help="Show one location.",
    )

    show_parser.add_argument(
        "--location-id",
        type=int,
        required=True,
    )

    show_parser.add_argument(
        "--include-inactive",
        action="store_true",
    )

    update_parser = subparsers.add_parser(
        "update",
        help="Update a location.",
    )

    update_parser.add_argument(
        "--location-id",
        type=int,
        required=True,
    )

    update_parser.add_argument(
        "--name",
    )

    update_parser.add_argument(
        "--type",
        dest="location_type",
        choices=[
            "home_gym",
            "commercial_gym",
            "crossfit_box",
            "outdoor",
            "temporary_location",
            "other",
        ],
    )

    update_notes_group = (
        update_parser.add_mutually_exclusive_group()
    )

    update_notes_group.add_argument(
        "--notes",
    )

    update_notes_group.add_argument(
        "--clear-notes",
        action="store_true",
    )

    deactivate_parser = subparsers.add_parser(
        "deactivate",
        help="Deactivate a location.",
    )

    deactivate_parser.add_argument(
        "--location-id",
        type=int,
        required=True,
    )

    reactivate_parser = subparsers.add_parser(
        "reactivate",
        help="Reactivate a location.",
    )

    reactivate_parser.add_argument(
        "--location-id",
        type=int,
        required=True,
    )

    # -----------------------------------------------------
    # Equipment commands
    # -----------------------------------------------------

    equipment_list_parser = (
        subparsers.add_parser(
            "equipment-list",
            help=(
                "List equipment at a location."
            ),
        )
    )

    equipment_list_parser.add_argument(
        "--location-id",
        type=int,
        required=True,
    )

    equipment_set_parser = (
        subparsers.add_parser(
            "equipment-set",
            help=(
                "Add or update equipment "
                "at a location."
            ),
        )
    )

    equipment_set_parser.add_argument(
        "--location-id",
        type=int,
        required=True,
    )

    equipment_set_parser.add_argument(
        "--equipment",
        required=True,
        help=(
            "Equipment catalog code, "
            "for example dumbbell."
        ),
    )

    quantity_group = (
        equipment_set_parser
        .add_mutually_exclusive_group()
    )

    quantity_group.add_argument(
        "--quantity",
        type=int,
    )

    quantity_group.add_argument(
        "--clear-quantity",
        action="store_true",
    )

    equipment_set_parser.add_argument(
        "--min-weight",
        type=float,
    )

    equipment_set_parser.add_argument(
        "--max-weight",
        type=float,
    )

    equipment_set_parser.add_argument(
        "--unit",
        choices=["kg", "lb"],
    )

    equipment_set_parser.add_argument(
        "--clear-weight-range",
        action="store_true",
    )

    equipment_notes_group = (
        equipment_set_parser
        .add_mutually_exclusive_group()
    )

    equipment_notes_group.add_argument(
        "--notes",
    )

    equipment_notes_group.add_argument(
        "--clear-notes",
        action="store_true",
    )

    equipment_remove_parser = (
        subparsers.add_parser(
            "equipment-remove",
            help=(
                "Remove equipment "
                "from a location."
            ),
        )
    )

    equipment_remove_parser.add_argument(
        "--location-id",
        type=int,
        required=True,
    )

    equipment_remove_parser.add_argument(
        "--equipment",
        required=True,
    )

    return parser


def _get_context(
    *,
    db_path: DatabasePath | None,
    env_path: Path,
) -> tuple[
    int,
    LocationService,
    LocationEquipmentService,
]:
    owner = get_configured_owner(
        db_path=db_path,
        env_path=env_path,
    )

    location_service = LocationService(
        db_path=db_path
    )

    equipment_service = (
        LocationEquipmentService(
            db_path=db_path
        )
    )

    return (
        owner.id,
        location_service,
        equipment_service,
    )


def _handle_update_location(
    *,
    args: argparse.Namespace,
    user_id: int,
    service: LocationService,
) -> dict[str, object]:
    current = service.get_location(
        user_id=user_id,
        location_id=args.location_id,
        include_inactive=True,
    )

    if args.clear_notes:
        notes = None
    elif args.notes is not None:
        notes = args.notes
    else:
        notes = current.notes

    updated = service.update_location(
        user_id=user_id,
        location_id=args.location_id,
        name=(
            args.name
            if args.name is not None
            else current.name
        ),
        location_type=(
            args.location_type
            if args.location_type is not None
            else current.location_type
        ),
        notes=notes,
    )

    return {
        "status": "updated",
        "location": _location_payload(
            updated
        ),
    }


def _handle_set_equipment(
    *,
    args: argparse.Namespace,
    user_id: int,
    service: LocationEquipmentService,
) -> dict[str, object]:
    existing = service.get_location_equipment(
        user_id=user_id,
        location_id=args.location_id,
        equipment_code=args.equipment,
    )

    if (
        args.clear_weight_range
        and (
            args.min_weight is not None
            or args.max_weight is not None
            or args.unit is not None
        )
    ):
        raise ValueError(
            "CLEAR_WEIGHT_RANGE_CONFLICT"
        )

    if args.clear_quantity:
        quantity = None
    elif args.quantity is not None:
        quantity = args.quantity
    elif existing is not None:
        quantity = existing.quantity
    else:
        quantity = None

    if args.clear_weight_range:
        minimum_weight = None
        maximum_weight = None
        weight_unit = None
    else:
        minimum_weight = (
            args.min_weight
            if args.min_weight is not None
            else (
                existing.minimum_weight
                if existing is not None
                else None
            )
        )

        maximum_weight = (
            args.max_weight
            if args.max_weight is not None
            else (
                existing.maximum_weight
                if existing is not None
                else None
            )
        )

        weight_unit = (
            args.unit
            if args.unit is not None
            else (
                existing.weight_unit
                if existing is not None
                else None
            )
        )

    if args.clear_notes:
        notes = None
    elif args.notes is not None:
        notes = args.notes
    elif existing is not None:
        notes = existing.notes
    else:
        notes = None

    result = service.set_location_equipment(
        user_id=user_id,
        location_id=args.location_id,
        equipment_code=args.equipment,
        quantity=quantity,
        minimum_weight=minimum_weight,
        maximum_weight=maximum_weight,
        weight_unit=weight_unit,
        notes=notes,
    )

    return {
        "status": (
            "updated"
            if existing is not None
            else "created"
        ),
        "equipment":
            _equipment_payload(result),
    }


def execute_command(
    args: argparse.Namespace,
) -> object:
    (
        user_id,
        location_service,
        equipment_service,
    ) = _get_context(
        db_path=args.db_path,
        env_path=args.env_path,
    )

    if args.command == "add":
        location = (
            location_service.create_location(
                user_id=user_id,
                name=args.name,
                location_type=(
                    args.location_type
                ),
                notes=args.notes,
            )
        )

        return {
            "status": "created",
            "location":
                _location_payload(location),
        }

    if args.command == "list":
        locations = (
            location_service.list_locations(
                user_id=user_id,
                include_inactive=args.all,
            )
        )

        return {
            "count": len(locations),
            "locations": [
                _location_payload(location)
                for location in locations
            ],
        }

    if args.command == "show":
        location = (
            location_service.get_location(
                user_id=user_id,
                location_id=args.location_id,
                include_inactive=(
                    args.include_inactive
                ),
            )
        )

        return {
            "location":
                _location_payload(location),
        }

    if args.command == "update":
        return _handle_update_location(
            args=args,
            user_id=user_id,
            service=location_service,
        )

    if args.command == "deactivate":
        location = (
            location_service
            .deactivate_location(
                user_id=user_id,
                location_id=args.location_id,
            )
        )

        return {
            "status": "deactivated",
            "location":
                _location_payload(location),
        }

    if args.command == "reactivate":
        location = (
            location_service
            .reactivate_location(
                user_id=user_id,
                location_id=args.location_id,
            )
        )

        return {
            "status": "reactivated",
            "location":
                _location_payload(location),
        }

    if args.command == "equipment-list":
        equipment = (
            equipment_service
            .list_location_equipment(
                user_id=user_id,
                location_id=args.location_id,
            )
        )

        return {
            "count": len(equipment),
            "equipment": [
                _equipment_payload(item)
                for item in equipment
            ],
        }

    if args.command == "equipment-set":
        return _handle_set_equipment(
            args=args,
            user_id=user_id,
            service=equipment_service,
        )

    if args.command == "equipment-remove":
        removed = (
            equipment_service
            .remove_location_equipment(
                user_id=user_id,
                location_id=args.location_id,
                equipment_code=args.equipment,
            )
        )

        return {
            "status": (
                "removed"
                if removed
                else "not_present"
            ),
            "equipment_code":
                args.equipment,
        }

    raise RuntimeError(
        f"Unsupported command: {args.command}"
    )


def main(
    argv: Sequence[str] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = execute_command(args)
    except (
        OwnerBootstrapError,
        LocationServiceError,
        LocationEquipmentServiceError,
        ValueError,
    ) as error:
        print(
            f"Command failed: {error}",
            file=sys.stderr,
        )
        return 2

    _print_json(result)
    return 0

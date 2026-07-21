from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.catalog.models import (
    ExerciseCreateRequest,
    MovementPatternSpec,
)
from app.catalog.service import CatalogService


def parse_pattern(
    value: str,
) -> MovementPatternSpec:
    parts = value.split(":")

    code = parts[0]
    role = parts[1] if len(parts) >= 2 else "primary"
    weight = (
        float(parts[2])
        if len(parts) >= 3
        else 1.0
    )

    return MovementPatternSpec(
        code=code,
        role=role,
        contribution_weight=weight,
    )


def print_result(value: object) -> None:
    print(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage the exercise catalog."
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    search = subparsers.add_parser("search")
    search.add_argument("query")

    add = subparsers.add_parser("add")
    add.add_argument(
        "--actor-user-id",
        type=int,
        required=True,
    )
    add.add_argument(
        "--scope",
        choices=["core", "personal"],
        required=True,
    )
    add.add_argument("--name", required=True)
    add.add_argument("--korean-name")
    add.add_argument("--category", required=True)
    add.add_argument(
        "--block-type",
        required=True,
    )
    add.add_argument(
        "--alias",
        action="append",
        default=[],
    )
    add.add_argument(
        "--pattern",
        action="append",
        default=[],
        help=(
            "code[:role[:weight]], "
            "for example "
            "horizontal_pull:primary:1.0"
        ),
    )
    add.add_argument(
        "--equipment",
        action="append",
        default=[],
    )
    add.add_argument(
        "--parent-id",
        type=int,
    )
    add.add_argument("--notes")

    promote = subparsers.add_parser("promote")
    promote.add_argument(
        "--actor-user-id",
        type=int,
        required=True,
    )
    promote.add_argument(
        "--exercise-id",
        type=int,
        required=True,
    )

    alias = subparsers.add_parser("add-alias")
    alias.add_argument(
        "--actor-user-id",
        type=int,
        required=True,
    )
    alias.add_argument(
        "--exercise-id",
        type=int,
        required=True,
    )
    alias.add_argument(
        "--alias",
        required=True,
    )

    deactivate = subparsers.add_parser("deactivate")
    deactivate.add_argument(
        "--actor-user-id",
        type=int,
        required=True,
    )
    deactivate.add_argument(
        "--exercise-id",
        type=int,
        required=True,
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    service = CatalogService()

    if args.command == "search":
        print_result(
            service.search_exact(args.query)
        )
        return

    if args.command == "add":
        request = ExerciseCreateRequest(
            canonical_name=args.name,
            korean_name=args.korean_name,
            category=args.category,
            default_block_type=args.block_type,
            catalog_scope=args.scope,
            aliases=tuple(args.alias),
            movement_patterns=tuple(
                parse_pattern(value)
                for value in args.pattern
            ),
            equipment_codes=tuple(
                args.equipment
            ),
            parent_exercise_id=args.parent_id,
            notes=args.notes,
        )

        result = service.create_exercise(
            actor_user_id=args.actor_user_id,
            request=request,
        )

        print_result(result)
        return

    if args.command == "promote":
        result = service.promote_to_core(
            actor_user_id=args.actor_user_id,
            exercise_id=args.exercise_id,
        )

        print_result(result)
        return

    if args.command == "add-alias":
        created = service.add_alias(
            actor_user_id=args.actor_user_id,
            exercise_id=args.exercise_id,
            alias=args.alias,
        )

        print_result({"created": created})
        return

    if args.command == "deactivate":
        result = service.deactivate_exercise(
            actor_user_id=args.actor_user_id,
            exercise_id=args.exercise_id,
        )

        print_result(result)
        return


if __name__ == "__main__":
    main()

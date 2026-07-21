from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.users.bootstrap import (
    bootstrap_owner,
    get_configured_owner,
)


def _masked_discord_id(
    discord_user_id: str,
) -> str:
    if len(discord_user_id) <= 8:
        return "***"

    return (
        discord_user_id[:4]
        + "..."
        + discord_user_id[-4:]
    )


def _print_user(user: object) -> None:
    print(
        json.dumps(
            {
                "id": user.id,
                "discord_user_id":
                    _masked_discord_id(
                        user.discord_user_id
                    ),
                "display_name":
                    user.display_name,
                "timezone": user.timezone,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Bootstrap and inspect the current "
            "training-agent owner."
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "bootstrap",
        help=(
            "Create or update the configured "
            "owner user."
        ),
    )

    subparsers.add_parser(
        "show-owner",
        help=(
            "Show the configured owner already "
            "stored in the database."
        ),
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "bootstrap":
        user = bootstrap_owner()
        print("Owner bootstrap complete.")
        _print_user(user)
        return

    if args.command == "show-owner":
        user = get_configured_owner()
        _print_user(user)
        return


if __name__ == "__main__":
    main()

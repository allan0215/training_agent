from __future__ import annotations

import logging

from app.bot.discord_bot import create_discord_client
from app.config import settings


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(
            logging,
            settings.log_level,
            logging.INFO,
        ),
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
        handlers=[
            logging.FileHandler(
                settings.log_file,
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
    )


def main() -> None:
    configure_logging()

    client = create_discord_client()

    # 토큰 원문은 로그나 화면에 출력하지 않는다.
    client.run(settings.discord_bot_token)


if __name__ == "__main__":
    main()

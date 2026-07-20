from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "training-agent.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(ENV_FILE)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    log_level: str
    log_file: Path

    discord_bot_token: str
    discord_channel_id: int
    discord_allowed_user_id: int


def required_text(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"{name}가 설정되지 않았습니다. "
            f"{ENV_FILE} 파일을 확인하세요."
        )

    return value


def required_int(name: str) -> int:
    raw_value = required_text(name)

    try:
        return int(raw_value)
    except ValueError as exc:
        raise RuntimeError(
            f"{name}에는 숫자 ID만 입력해야 합니다. "
            f"현재 값의 형식을 확인하세요."
        ) from exc


def load_settings() -> Settings:
    api_key = required_text("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "").strip()
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()

    if not model:
        raise RuntimeError(
            f"OPENAI_MODEL이 설정되지 않았습니다. "
            f"{ENV_FILE} 파일을 확인하세요."
        )

    # OpenAI Agents SDK가 표준 환경변수에서 키를 읽도록 보장
    os.environ["OPENAI_API_KEY"] = api_key

    return Settings(
        openai_api_key=api_key,
        openai_model=model,
        log_level=log_level,
        log_file=LOG_FILE,
        discord_bot_token=required_text("DISCORD_BOT_TOKEN"),
        discord_channel_id=required_int("DISCORD_CHANNEL_ID"),
        discord_allowed_user_id=required_int(
            "DISCORD_ALLOWED_USER_ID"
        ),
    )


settings = load_settings()

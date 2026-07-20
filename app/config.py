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


def load_settings() -> Settings:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip()
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()

    if not api_key:
        raise RuntimeError(
            f"OPENAI_API_KEY가 없습니다. {ENV_FILE} 파일을 확인하세요."
        )

    if not model:
        raise RuntimeError(
            f"OPENAI_MODEL이 없습니다. {ENV_FILE} 파일을 확인하세요."
        )

    os.environ["OPENAI_API_KEY"] = api_key

    return Settings(
        openai_api_key=api_key,
        openai_model=model,
        log_level=log_level,
        log_file=LOG_FILE,
    )


settings = load_settings()

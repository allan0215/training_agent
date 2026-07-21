from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


def load_env_file(
    path: str | Path = DEFAULT_ENV_PATH,
    *,
    override: bool = False,
) -> None:
    """
    단순한 KEY=VALUE 형식의 .env 파일을 환경변수로 불러온다.

    실제 운영 환경에 이미 설정된 환경변수는 기본적으로
    .env 값으로 덮어쓰지 않는다.
    """

    env_path = Path(path)

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[7:].strip()

        if "=" not in line:
            continue

        key, value = line.split("=", 1)

        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        if override or key not in os.environ:
            os.environ[key] = value

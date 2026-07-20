from __future__ import annotations

import asyncio
import logging
from typing import Any

from agents import Runner
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)

from app.agent.training_agent import training_agent
from app.config import settings


logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """기술적인 오류를 파일에 기록한다."""

    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
        handlers=[
            logging.FileHandler(
                settings.log_file,
                encoding="utf-8",
            )
        ],
    )


async def run_chat() -> None:
    """
    터미널에서 훈련 코치와 대화한다.

    conversation에는 현재 프로그램 실행 중의 대화만 보관된다.
    프로그램을 종료하면 이 대화 기록은 사라진다.
    """

    conversation: list[Any] = []

    print()
    print("Training Agent가 실행되었습니다.")
    print(f"사용 모델: {settings.openai_model}")
    print("종료하려면 quit, exit 또는 종료를 입력하세요.")
    print("현재 버전은 운동 기록을 영구 저장하지 않습니다.")
    print()

    while True:
        try:
            user_input = input("나: ").strip()
        except EOFError:
            print("\n입력이 종료되었습니다.")
            return

        if user_input.lower() in {"quit", "exit"} or user_input == "종료":
            print("Training Agent를 종료합니다.")
            return

        if not user_input:
            print("내용을 입력하세요.\n")
            continue

        # 실패한 요청이 대화 이력에 남지 않도록 복사본을 만든다.
        next_input = [
            *conversation,
            {
                "role": "user",
                "content": user_input,
            },
        ]

        try:
            result = await Runner.run(
                training_agent,
                next_input,
            )

        except AuthenticationError:
            print(
                "\nOpenAI 인증에 실패했습니다. "
                ".env의 OPENAI_API_KEY를 확인하세요.\n"
            )
            logger.exception("OpenAI authentication failed")
            return

        except RateLimitError:
            print(
                "\nAPI 요청 한도 또는 결제 상태 때문에 "
                "요청을 처리하지 못했습니다.\n"
            )
            logger.exception("OpenAI rate limit or quota error")
            continue

        except APITimeoutError:
            print(
                "\nOpenAI 응답 시간이 초과됐습니다. "
                "같은 요청을 다시 시도하세요.\n"
            )
            logger.exception("OpenAI API timeout")
            continue

        except APIConnectionError:
            print(
                "\nOpenAI API에 연결하지 못했습니다. "
                "서버의 인터넷 연결을 확인하세요.\n"
            )
            logger.exception("OpenAI API connection error")
            continue

        except BadRequestError:
            print(
                "\n요청 형식 또는 모델 설정에 문제가 있습니다. "
                "로그 파일을 확인하세요.\n"
            )
            logger.exception("OpenAI bad request")
            continue

        except Exception:
            print(
                "\n예상하지 못한 오류가 발생했습니다. "
                "logs/training-agent.log를 확인하세요.\n"
            )
            logger.exception("Unexpected training agent error")
            continue

        output = result.final_output

        if output is None:
            print("\n코치: 응답을 생성하지 못했습니다.\n")
            logger.warning("Agent returned no final output")
            continue

        print(f"\n코치: {output}\n")

        # 성공한 대화만 다음 질문의 맥락으로 저장한다.
        conversation = result.to_input_list()


def main() -> None:
    configure_logging()

    logger.info(
        "Training Agent started with model=%s",
        settings.openai_model,
    )

    try:
        asyncio.run(run_chat())
    except KeyboardInterrupt:
        print("\nTraining Agent를 종료합니다.")
    finally:
        logger.info("Training Agent stopped")


if __name__ == "__main__":
    main()

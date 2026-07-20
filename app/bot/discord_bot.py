from __future__ import annotations

import asyncio
import logging
from typing import Any

import discord
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

ConversationKey = tuple[int, int, int]


def split_discord_message(
    text: str,
    max_length: int = 1900,
) -> list[str]:
    """
    긴 답변을 Discord에 보낼 수 있도록 여러 조각으로 나눈다.
    가능하면 줄바꿈이나 공백 위치에서 자른다.
    """

    text = text.strip()

    if not text:
        return ["응답 내용이 비어 있습니다."]

    chunks: list[str] = []

    while len(text) > max_length:
        cut_position = text.rfind("\n", 0, max_length)

        if cut_position < max_length // 2:
            cut_position = text.rfind(" ", 0, max_length)

        if cut_position < max_length // 2:
            cut_position = max_length

        chunk = text[:cut_position].strip()

        if chunk:
            chunks.append(chunk)

        text = text[cut_position:].strip()

    if text:
        chunks.append(text)

    return chunks


class TrainingDiscordClient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()

        # 일반 채널 메시지의 실제 내용을 읽기 위해 필요
        intents.message_content = True

        super().__init__(intents=intents)

        # 현재 프로세스 안에서만 유지되는 임시 대화
        self.conversations: dict[
            ConversationKey,
            list[Any],
        ] = {}

        # 같은 사용자가 메시지를 연속으로 보냈을 때
        # 대화 순서가 엉키지 않도록 하는 잠금
        self.locks: dict[
            ConversationKey,
            asyncio.Lock,
        ] = {}

    async def on_ready(self) -> None:
        if self.user is None:
            return

        logger.info(
            "Discord bot connected: name=%s id=%s",
            self.user,
            self.user.id,
        )

        print()
        print("Discord Training Agent가 연결되었습니다.")
        print(f"Bot: {self.user}")
        print(f"Channel ID: {settings.discord_channel_id}")
        print(
            "Allowed User ID:",
            settings.discord_allowed_user_id,
        )
        print()

    async def on_message(
        self,
        message: discord.Message,
    ) -> None:
        # 봇이 쓴 메시지는 모두 무시한다.
        if message.author.bot:
            return

        # 지정한 채널 외의 메시지는 무시한다.
        if message.channel.id != settings.discord_channel_id:
            return

        # 지정한 사용자 외의 메시지는 무시한다.
        if message.author.id != settings.discord_allowed_user_id:
            return

        content = message.content.strip()

        if not content:
            return

        guild_id = message.guild.id if message.guild else 0

        conversation_key: ConversationKey = (
            guild_id,
            message.channel.id,
            message.author.id,
        )

        if content.lower() == "!ping":
            await message.channel.send("pong")
            return

        if content.lower() == "!reset":
            self.conversations.pop(conversation_key, None)
            await message.channel.send(
                "현재 실행 세션의 대화 맥락을 초기화했습니다. "
                "저장된 운동 기록을 삭제한 것은 아닙니다."
            )
            return

        if content.lower() == "!help":
            await message.channel.send(
                "**Training Agent 명령어**\n"
                "`!ping` — 봇 연결 확인\n"
                "`!reset` — 현재 대화 맥락 초기화\n"
                "`!help` — 명령어 안내\n\n"
                "그 외 메시지는 모두 훈련 코치에게 전달됩니다."
            )
            return

        lock = self.locks.setdefault(
            conversation_key,
            asyncio.Lock(),
        )

        async with lock:
            conversation = self.conversations.get(
                conversation_key,
                [],
            )

            next_input = [
                *conversation,
                {
                    "role": "user",
                    "content": content,
                },
            ]

            try:
                async with message.channel.typing():
                    result = await Runner.run(
                        training_agent,
                        next_input,
                    )

            except AuthenticationError:
                logger.exception("OpenAI authentication failed")
                await message.channel.send(
                    "OpenAI 인증에 실패했습니다. "
                    "서버의 API 키 설정을 확인해야 합니다."
                )
                return

            except RateLimitError:
                logger.exception(
                    "OpenAI rate limit or quota error"
                )
                await message.channel.send(
                    "OpenAI 요청 한도 또는 결제 상태 때문에 "
                    "응답하지 못했습니다."
                )
                return

            except APITimeoutError:
                logger.exception("OpenAI request timed out")
                await message.channel.send(
                    "OpenAI 응답 시간이 초과됐습니다. "
                    "같은 내용을 다시 보내주세요."
                )
                return

            except APIConnectionError:
                logger.exception("OpenAI connection failed")
                await message.channel.send(
                    "OpenAI API 연결에 실패했습니다. "
                    "잠시 후 다시 시도해주세요."
                )
                return

            except BadRequestError:
                logger.exception("OpenAI bad request")
                await message.channel.send(
                    "모델 또는 요청 설정에 문제가 있습니다. "
                    "서버 로그를 확인해야 합니다."
                )
                return

            except Exception:
                logger.exception(
                    "Unexpected Discord agent error"
                )
                await message.channel.send(
                    "예상하지 못한 오류가 발생했습니다. "
                    "서버 로그를 확인해야 합니다."
                )
                return

            output = result.final_output

            if output is None:
                logger.warning(
                    "Training agent returned no output"
                )
                await message.channel.send(
                    "응답을 생성하지 못했습니다."
                )
                return

            output_text = str(output).strip()

            for chunk in split_discord_message(output_text):
                await message.channel.send(chunk)

            # 성공한 대화만 다음 요청의 맥락으로 보관
            self.conversations[
                conversation_key
            ] = result.to_input_list()


def create_discord_client() -> TrainingDiscordClient:
    return TrainingDiscordClient()

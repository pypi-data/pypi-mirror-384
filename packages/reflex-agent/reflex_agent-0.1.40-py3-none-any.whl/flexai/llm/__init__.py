from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import Unpack

from flexai.message import AIMessage, Message, SystemMessage
from flexai.tool import Tool

from .client import Client as Client
from .client import PartialAgentRunArgs


# Fallback client implementation that provides minimal functionality for testing and defaults
@dataclass(frozen=True)
class DefaultClient(Client):
    # Provider identifier for the default/stub client
    provider: str = "default"

    async def get_chat_response(
        self,
        messages: list[Message],
        system: str | SystemMessage = "",
        tools: Sequence[Tool] | None = None,
        **input_args: Unpack[PartialAgentRunArgs],
    ) -> AIMessage:
        # Return an empty AIMessage when no real LLM provider is configured
        # Empty content signals agent loop termination and prevents storing unnecessary messages
        return AIMessage(content=[])

    async def stream_chat_response(
        self,
        messages: list[Message],
        system: str | SystemMessage = "",
        tools: Sequence[Tool] | None = None,
        **input_args: Unpack[PartialAgentRunArgs],
    ) -> AsyncGenerator[AIMessage, None]:
        # Return an empty AIMessage when no real LLM provider is configured
        yield AIMessage(content=[])

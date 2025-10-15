from __future__ import annotations

import base64
import json
import os
import time
from collections.abc import AsyncGenerator, Mapping, Sequence
from dataclasses import InitVar, dataclass, field
from typing import Any, TypeVar, Unpack

from openai import AsyncOpenAI
from openai.types import Reasoning
from openai.types.responses import (
    Response,
    ResponseFunctionToolCallParam,
    ResponseInputImageParam,
    ResponseInputTextParam,
    ResponseOutputMessage,
    ResponseOutputText,
    ResponseOutputTextParam,
    ResponseTextDeltaEvent,
)
from openai.types.responses.response_input_item_param import FunctionCallOutput
from pydantic import BaseModel

from flexai.llm.client import AgentRunArgs, Client, PartialAgentRunArgs, with_defaults
from flexai.message import (
    AIMessage,
    ImageBlock,
    Message,
    MessageContent,
    SystemMessage,
    TextBlock,
    ToolCall,
    ToolResult,
    Usage,
)
from flexai.tool import Tool


def get_usage_block(usage) -> Usage:
    """Extract usage information from the OpenAI response.

    Args:
        usage: The usage object from OpenAI.

    Returns:
        A Usage object containing input tokens, output tokens, and generation time.
    """
    return Usage(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
    )


BASE_MODEL = TypeVar("BASE_MODEL", bound=BaseModel)


@dataclass(frozen=True)
class OpenAIResponsesClient(Client):
    """Client for interacting with the OpenAI language model."""

    # The provider name.
    provider: str = "openai"

    # The API key to use for interacting with the model.
    api_key: InitVar[str] = field(default=os.environ.get("OPENAI_API_KEY", ""))

    # The base URL to use for interacting with the model.
    base_url: InitVar[str] = field(default="https://api.openai.com/v1")

    # The client to use for interacting with the model.
    client: AsyncOpenAI = field(default_factory=AsyncOpenAI)

    # The model to use for generating responses.
    model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def __post_init__(self, api_key, base_url, **kwargs):
        object.__setattr__(
            self,
            "client",
            AsyncOpenAI(api_key=api_key, base_url=base_url),
        )

    def _complete_args_with_defaults(
        self, **run_args: Unpack[PartialAgentRunArgs]
    ) -> AgentRunArgs:
        defaults = with_defaults(**run_args)
        if "temperature" not in run_args:
            defaults["temperature"] = 1.0
        if run_args.get("thinking_budget") is None:
            defaults["thinking_budget"] = self.default_thinking_budget
        return defaults

    async def get_chat_response(
        self,
        messages: list[Message],
        system: str | SystemMessage = "",
        tools: Sequence[Tool] | None = None,
        **input_args: Unpack[PartialAgentRunArgs],
    ) -> AIMessage:
        if tools:
            raise NotImplementedError(
                "Tool use is not supported with the responses client."
            )
        run_args = self._complete_args_with_defaults(**input_args)

        # Send the messages to the model and get the response.
        params = self._get_params(
            messages=messages,
            system=system,
            stream=False,
            **run_args,
        )
        start = time.monotonic()
        response = await self.client.responses.create(**params)

        if not isinstance(response, Response):
            raise TypeError("Expected response to be of type Response.")

        generation_time = time.monotonic() - start

        # Parse out the tool uses from the response.
        message = response.output[0]

        if not isinstance(message, ResponseOutputMessage):
            raise TypeError("Expected message to be of type ResponseOutputMessage.")

        usage = get_usage_block(response.usage)
        usage.generation_time = generation_time

        # Get the content to return.
        content_to_return = [
            TextBlock(text=sub_message.text)
            for sub_message in message.content
            if isinstance(sub_message, ResponseOutputText)
        ]
        return AIMessage(
            content=content_to_return,
            usage=usage,
        )

    async def stream_chat_response(
        self,
        messages: list[Message],
        system: str | SystemMessage = "",
        tools: Sequence[Tool] | None = None,
        **input_args: Unpack[PartialAgentRunArgs],
    ) -> AsyncGenerator[MessageContent | AIMessage, None]:
        if tools:
            raise NotImplementedError(
                "Tool use is not supported with the responses client."
            )
        run_args = self._complete_args_with_defaults(**input_args)

        stream = await self.client.responses.create(
            **self._get_params(
                messages=messages,
                system=system,
                stream=True,
                **run_args,
            )
        )
        current_text_block: TextBlock = TextBlock(text="")

        buffer = ""

        async for chunk in stream:
            if not isinstance(chunk, ResponseTextDeltaEvent):
                continue
            delta = chunk.delta
            if not delta:
                continue
            buffer += delta
            if "\n" not in buffer:
                continue
            send_text, buffer = buffer.rsplit("\n", 1)
            send_text = send_text + "\n"
            if send_text:
                yield TextBlock(text=send_text)
            current_text_block = current_text_block.append(send_text)
        if buffer:
            yield TextBlock(text=buffer)
            current_text_block = current_text_block.append(buffer)

        yield AIMessage(content=[current_text_block] if current_text_block.text else [])

    def _get_params(
        self,
        messages: list[Message],
        system: str | SystemMessage,
        stream: bool,
        **run_args: Unpack[AgentRunArgs],
    ) -> dict:
        """Get the common params to send to the model.

        Args:
            messages: The messages to send to the model.
            system: The system message to send to the model.
            stream: Whether to stream the response.
            **run_args: Additional arguments including temperature, force_tool,
                allow_tool, stream and other run parameters.

        Returns:
            The common params to send to the model.
        """
        # Extract the run arguments we care about.
        temperature = run_args["temperature"]

        if isinstance(system, str):
            system = SystemMessage(system)
        thinking_budget = (
            run_args.get("thinking_budget") or self.default_thinking_budget
        )
        kwargs = {
            "model": self.model,
            "input": self._format_content(messages),
            "instructions": str(system),
            "temperature": temperature,
            "reasoning": (
                None
                if thinking_budget is None
                else Reasoning(effort="low")
                if thinking_budget <= 10000
                else Reasoning(effort="medium")
                if thinking_budget <= 20000
                else Reasoning(effort="high")
            ),
        }

        if stream:
            kwargs["stream"] = True

        return kwargs

    @classmethod
    def _format_message_content(
        cls,
        contents: Sequence[MessageContent],
        role: str | None = None,
    ) -> list[Mapping[str, Any]]:
        return [
            (
                ResponseInputTextParam(type="input_text", text=content.text)
                if role != "assistant"
                else ResponseOutputTextParam(
                    type="output_text", text=content.text, annotations=[]
                )
            )
            if isinstance(content, TextBlock)
            else ResponseInputImageParam(
                type="input_image",
                image_url=f"data:{content.mime_type};base64,{base64.b64encode(content.image).decode('utf-8')}",
                detail="auto",
            )
            if isinstance(content, ImageBlock)
            else ResponseFunctionToolCallParam(
                type="function_call",
                call_id=content.id,
                name=content.name,
                arguments=json.dumps(content.input),
            )
            if isinstance(content, ToolCall)
            else FunctionCallOutput(
                type="function_call_output",
                call_id=content.tool_call_id,
                output=json.dumps(content.result),
            )
            if isinstance(content, ToolResult)
            else (
                (_ for _ in ()).throw(
                    TypeError(
                        f"Tried to send {content} to openai, which is of an unsupported type."
                    )
                )
            )
            for content in contents
        ]

    @classmethod
    def _format_content(
        cls,
        value: Message | Sequence[Message],
        allow_tool: bool = True,
    ) -> list[Mapping[str, Any]]:
        """Format the message content for the OpenAI API.

        Args:
            value: The value to format.
            allow_tool: unused.

        Returns:
            The formatted message content.

        Raises:
            ValueError: If the message content type is unknown.
        """
        # Anthropic message format.
        if isinstance(value, Message):
            content = value.normalize().content

            tool_calls = []
            non_tool_calls = []
            for item in content:
                if isinstance(item, (ToolCall, ToolResult)):
                    tool_calls.append(item)
                else:
                    non_tool_calls.append(item)

            messages = [*cls._format_message_content(tool_calls)]

            if non_tool_calls:
                messages.append(
                    {
                        "role": value.role,
                        "content": cls._format_message_content(
                            non_tool_calls, role=value.role
                        ),
                    }
                )

            return messages

        # If it's a list of messages, format them.
        if isinstance(value, Sequence) and not isinstance(value, str):
            return [
                message
                for item in value
                for message in cls._format_content(item, allow_tool=allow_tool)
            ]

        raise ValueError(f"Unknown message content type: {type(value)}")

    @classmethod
    def load_content(
        cls, content: str | list[dict[str, Any]]
    ) -> str | list[MessageContent]:
        """Load the message content from the OpenAI API to dataclasses.

        Args:
            content: The content to load.

        Returns:
            The loaded message content

        Raises:
            TypeError: If content is not a sequence of dictionaries.
        """
        # If it's a string, return it.
        if isinstance(content, str):
            return content

        # If it's a list of dictionaries, parse them.
        if not isinstance(content, Sequence):
            raise TypeError("Content must be a sequence of dictionaries.")
        parsed_content: list[MessageContent] = []

        for entry in content:
            match entry.pop("type"):
                case "output_text":
                    parsed_content.append(TextBlock(**entry))

        return parsed_content

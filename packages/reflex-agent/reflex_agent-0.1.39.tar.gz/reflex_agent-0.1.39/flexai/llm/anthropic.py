from __future__ import annotations

import base64
import itertools
import os
import time
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass, field
from typing import Any, Unpack

from anthropic import AsyncAnthropic, AsyncAnthropicBedrock
from anthropic.types import ToolUseBlock
from anthropic.types import Usage as AnthropicUsage
from pydantic import BaseModel

from flexai.llm.client import AgentRunArgs, Client, PartialAgentRunArgs, with_defaults
from flexai.message import (
    AIMessage,
    DataBlock,
    ImageBlock,
    Message,
    MessageContent,
    SystemMessage,
    TextBlock,
    ToolCall,
    ToolResult,
    Usage,
    UserMessage,
)
from flexai.tool import Tool, ToolType


def get_tool_call(tool_use: ToolUseBlock) -> ToolCall:
    """Get the tool call from a tool use block.

    Args:
        tool_use: The tool use block to get the call from.

    Returns:
        The tool call from the tool use block.
    """
    return ToolCall(
        id=tool_use.id,
        name=tool_use.name,
        input=tool_use.input,
    )


def get_usage_block(usage_metadata: AnthropicUsage) -> Usage:
    """Extract usage information from Anthropic's usage metadata.

    Args:
        usage_metadata: The usage metadata from Anthropic response.

    Returns:
        A Usage object with token counts and timing information.
    """
    return Usage(
        input_tokens=usage_metadata.input_tokens,
        output_tokens=usage_metadata.output_tokens,
        cache_read_tokens=usage_metadata.cache_read_input_tokens or 0,
        cache_write_tokens=usage_metadata.cache_creation_input_tokens or 0,
    )


@dataclass(frozen=True)
class AnthropicClient(Client):
    """Client for interacting with the Anthropic language model."""

    # The provider name.
    provider: str = "anthropic"

    # The client to use for interacting with the model.
    client: AsyncAnthropic | AsyncAnthropicBedrock = field(
        default_factory=lambda: AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    )

    # The model to use for generating responses.
    model: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

    # The maximum number of tokens to generate in a response.
    max_tokens: int = 8192

    # Whether to cache messages or not.
    cache_messages: bool = False

    # Extra headers to include in the request.
    extra_headers: dict = field(default_factory=dict)

    def _complete_args_with_defaults(
        self, **run_args: Unpack[PartialAgentRunArgs]
    ) -> AgentRunArgs:
        defaults = with_defaults(**run_args)
        if "temperature" not in run_args:
            defaults["temperature"] = 1.0
        if "force_tool" not in run_args:
            defaults["force_tool"] = True
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
        if not messages:
            raise ValueError(
                "Anthropic requires at least one messages to process your request."
            )

        run_args = self._complete_args_with_defaults(**input_args)

        # If we were sent a model, call instead get_structured_response.
        if run_args["model"] is not None:
            # Extract the model parameter and remove it from kwargs to avoid recursion
            model = run_args["model"]
            run_args["model"] = None  # Prevent recursion
            return await self._get_structured_response(
                messages,
                model_to_use=model,
                system=system,
                tools=tools,
                **run_args,
            )

        # Send the messages to the model and get the response.
        start = time.monotonic()
        params = self._get_params(
            messages=messages,
            system=system,
            tools=tools,
            stream=False,
            **run_args,
        )
        response = await self.client.messages.create(**params)
        generation_time = time.monotonic() - start

        # Parse out all content from the response (text and tools).
        formatted_content_parts = []

        for message in response.content:
            if isinstance(message, ToolUseBlock):
                # Add tool calls
                formatted_content_parts.append(get_tool_call(message))
            # Add text content (assume it has .text attribute)
            elif hasattr(message, "text") and message.text.strip():
                formatted_content_parts.append(TextBlock(message.text))

        # Return all content parts (allows text + tool calls together)
        content_to_return = formatted_content_parts or ""
        usage = get_usage_block(response.usage)
        usage.generation_time = generation_time
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
        if not messages:
            raise ValueError(
                "Anthropic requires at least one message to process your request."
            )

        run_args = self._complete_args_with_defaults(**input_args)

        # Initialize variables to store the tool information.
        tool_call: ToolCall | None = None
        text_block: TextBlock | None = None

        # Track the usage.
        usage = Usage()

        # Iterate over the response stream.
        start = time.monotonic()
        params = self._get_params(
            messages=messages,
            system=system,
            tools=tools,
            stream=True,
            **run_args,
        )
        response_stream = await self.client.messages.create(**params)
        async for chunk in response_stream:
            # Add the usage.
            # This is the starting chunk.
            if hasattr(chunk, "message"):
                usage += get_usage_block(chunk.message.usage)
            # This is the continuation chunk.
            if hasattr(chunk, "usage"):
                usage += get_usage_block(chunk.usage)

            # Content start blocks.
            if chunk.type == "content_block_start":
                content = chunk.content_block
                # This is a text block.
                if content.type == "text":
                    text_block = TextBlock(content.text)
                    yield text_block

                # This is a tool block.
                else:
                    # Yield the initial tool call with no input.
                    tool_call = ToolCall(id=content.id, name=content.name, input="")
                    yield tool_call

            # A continuation of the content block.
            elif chunk.type == "content_block_delta":
                delta = chunk.delta
                # This is a text delta.
                if delta.type == "text_delta":
                    if text_block is None:
                        raise ValueError("Text block is None.")
                    text_block = text_block.append(delta.text)
                    yield TextBlock(delta.text)

                # This is a tool delta.
                else:
                    if tool_call is None:
                        raise ValueError("Tool call is None.")
                    # Add to the input buffer and yield the partial JSON.
                    tool_call = tool_call.append_input(delta.partial_json)
                    yield TextBlock(delta.partial_json)

            # The end of the content block.
            elif chunk.type == "message_stop":
                # Parse the tool from the buffer and convert it to a tool call.
                usage.generation_time = time.monotonic() - start

                # Send the final text message.
                content = None
                if text_block:
                    content = text_block
                    text_block = None
                elif tool_call:
                    # Send the tool call message.
                    content = tool_call.load_input()
                    tool_call = None

                # Send the final message.
                if content:
                    yield AIMessage(
                        content=[content],
                        usage=usage,
                    )

    def _add_cache_control(self, params: dict) -> dict:
        """Add cache control to the params.

        Args:
            params: The params to add cache control to.

        Returns:
            The params with cache control added.
        """
        cache_control = {
            "cache_control": {
                "type": "ephemeral",
            }
        }

        # Cache tool definitions.
        if "tools" in params and len(params["tools"]) > 0:
            params["tools"][-1].update(**cache_control)

        if not self.cache_messages:
            return params

        # Cache the system message.
        if params.get("system"):
            params["system"][0].update(**cache_control)

        # Find the most recent user message
        user_idxs = [
            idx
            for idx, message in enumerate(params["messages"])
            if message["role"] == "user"
        ]
        for idx in user_idxs[-2:]:
            message = params["messages"][idx]
            if isinstance(message["content"], str):
                message["content"] = [{"type": "text", "text": message["content"]}]
            message["content"][-1].update(**cache_control)

        return params

    def _get_params(
        self,
        messages: list[Message],
        system: str | SystemMessage,
        tools: Sequence[Tool] | None,
        stream: bool,
        **run_args: Unpack[AgentRunArgs],
    ) -> dict:
        """Get the common params to send to the model.

        Args:
            messages: The messages to send to the model.
            system: The system message or string.
            tools: List of available tools.
            stream: Whether to stream the response.
            **run_args: Additional arguments including temperature, force_tool,
                allow_tool, thinking_budget and other run parameters.

        Returns:
            The common params to send to the model.
        """
        # Convert the system prompt to a list of message content.
        if isinstance(system, str):
            system = SystemMessage([TextBlock(system)])

        # Extract the run arguments we care about
        temperature = run_args["temperature"]
        thinking_budget = run_args["thinking_budget"]
        allow_tool = run_args["allow_tool"]
        force_tool = run_args["force_tool"]

        thinking_args = (
            {"thinking": {"type": "disabled"}}
            if thinking_budget == 0
            else {"thinking": {"type": "enabled", "budget_tokens": thinking_budget}}
            if thinking_budget and thinking_budget > 0
            else {}
        )

        params = {
            "max_tokens": self.max_tokens,
            "messages": self._format_content(messages, allow_tool),
            "model": self.model,
            "temperature": temperature,
            "extra_headers": self.extra_headers,
            **thinking_args,
        }

        # Only add system message if it's not empty
        system_content = self._format_message_content(
            system.normalize().content, allow_tool
        )
        if system_content and any(
            content.get("text", "").strip() for content in system_content
        ):
            params["system"] = system_content

        # If tools are provided, force the model to use them (for now).
        if tools:
            params["tools"] = sorted(
                [self.format_tool(tool) for tool in tools], key=lambda x: x["name"]
            )
            force_tool = False
            # Default to disabling parallel tool use.
            tool_choice: dict[str, Any] = {
                "type": "auto",
                "disable_parallel_tool_use": True,
            }
            if force_tool:
                tool_choice["type"] = "any"
            params["tool_choice"] = tool_choice

        else:
            params["tools"] = []

        if stream:
            params["stream"] = True

        # Add cache control to the params.
        return self._add_cache_control(params)

    async def _get_structured_response(
        self,
        messages: list[Message],
        model_to_use: type[BaseModel],
        system: str | SystemMessage = "",
        tools: Sequence[Tool] | None = None,
        **run_args: Unpack[AgentRunArgs],
    ) -> AIMessage:
        """For anthropic, we have no better option than some funny retry logic to force a structured response. So that is pulled out into this function.

        Args:
            messages: List of messages for the conversation
            model_to_use: The BaseModel type to use for structured response validation
            system: System message or prompt
            tools: Optional list of tools available to the model
            **run_args: Additional arguments for the agent run

        Returns:
            AIMessage: The structured response from the model

        Raises:
            TypeError: If the response is not a string
            ValueError: If model parameter is provided in run_args (to avoid recursion)
        """
        if run_args["model"] is not None:
            raise ValueError("model parameter should be None to avoid recursion.")

        schema = model_to_use.model_json_schema()
        system = f"""{system}
Return your answer according to the 'properties' of the following schema:
{schema}
Return only the JSON object with the properties filled in.
Do not include anything in your response other than the JSON object.
Do not begin your response with ```json or end it with ```.
"""
        run_args["model"] = None  # Prevent recursion
        response = await self.get_chat_response(
            messages,
            system=system,
            tools=tools,
            **run_args,
        )
        content = response.content
        try:
            # Extract text content from TextBlock objects or use string directly
            if isinstance(content, list):
                text_content = ""
                for part in content:
                    if isinstance(part, TextBlock):
                        text_content += part.text
                content = text_content
            if not isinstance(content, str):
                raise TypeError("The response is not a string.")

            # Try to parse the response as a sanity check.
            model_to_use.model_validate_json(content)

            # Return response with string content for structured output
            return AIMessage(
                content=content,
                usage=response.usage,
            )

        except Exception as e:
            # Try again, printing the exception.
            messages = [
                *messages,
                response,
                UserMessage(
                    f"There was an error while parsing. Make sure to only include the JSON. Error: {e}"
                ),
            ]
            return await self._get_structured_response(
                messages,
                model_to_use=model_to_use,
                system=system,
                tools=tools,
                **run_args,
            )

    @staticmethod
    def format_type(arg_type: ToolType):
        if isinstance(arg_type, tuple):
            return {
                "anyOf": [
                    AnthropicClient.format_type(sub_type) for sub_type in arg_type
                ]
            }
        return {
            "type": arg_type,
        }

    @staticmethod
    def format_tool(tool: Tool) -> dict:
        """Convert the tool to a description.

        Args:
            tool: The tool to format.

        Returns:
            A dictionary describing the tool.
        """
        if tool.fn.__name__.startswith("str_replace_editor"):
            return {
                "type": "text_editor_20250124",
                "name": "str_replace_editor",
            }

        input_schema = {
            "type": "object",
            "properties": {},
        }
        for param_name, param_type in tool.params:
            input_schema["properties"][param_name] = AnthropicClient.format_type(
                param_type
            )

        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": input_schema,
        }

    @classmethod
    def _format_tool_result(
        cls,
        result: Any,
    ):
        if isinstance(result, TextBlock):
            return [
                {
                    "type": "text",
                    "text": result.text,
                }
            ]

        if isinstance(result, ImageBlock):
            return [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": result.mime_type,
                        "data": base64.b64encode(result.image).decode("utf-8"),
                    },
                }
            ]

        # For anything else, just fallback to trying to turn it into a string
        return str(result)

    @classmethod
    def _format_message_content(
        cls,
        contents: Sequence[MessageContent],
        allow_tool: bool = True,
    ) -> list[dict[str, Any]]:
        return list(
            itertools.chain.from_iterable(
                [
                    (
                        {
                            "type": "text",
                            "text": content.text,
                        }
                        if not content.cache
                        else {
                            "type": "text",
                            "text": content.text,
                            "cache_control": {"type": "ephemeral"},
                        }
                    )
                ]
                if isinstance(content, TextBlock)
                else [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": content.mime_type,
                            "data": base64.b64encode(content.image).decode("utf-8"),
                        },
                    }
                ]
                if isinstance(content, ImageBlock)
                else (
                    [
                        {
                            "type": "tool_use",
                            "id": content.id,
                            "name": content.name,
                            "input": content.input,
                        }
                    ]
                    if allow_tool
                    else [
                        {
                            "type": "text",
                            "text": str(
                                {
                                    "tool_use": {
                                        "id": content.id,
                                        "name": content.name,
                                        "input": content.input,
                                    }
                                }
                            ),
                        }
                    ]
                )
                if isinstance(content, ToolCall)
                else (
                    [
                        {
                            "type": "tool_result",
                            "tool_use_id": content.tool_call_id,
                            "content": cls._format_tool_result(content.result),
                            "is_error": content.is_error,
                        }
                    ]
                    if allow_tool
                    else [
                        {
                            "type": "text",
                            "text": str(
                                {
                                    "tool_result": {
                                        "tool_call_id": content.tool_call_id,
                                        "result": (
                                            content.result
                                            if not isinstance(
                                                content.result, ImageBlock
                                            )
                                            else "Result was an image, included in the following message.",
                                        ),
                                        "is_error": content.is_error,
                                    },
                                }
                            ),
                        },
                        *(
                            [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": content.result.mime_type,
                                        "data": base64.b64encode(
                                            content.result.image
                                        ).decode("utf-8"),
                                    },
                                }
                            ]
                            if isinstance(content.result, ImageBlock)
                            else []
                        ),
                    ]
                )
                if isinstance(content, ToolResult)
                else (
                    [
                        (_ for _ in ()).throw(
                            TypeError(
                                f"Tried to send {content} to anthropic, which is of an unsupported type."
                            )
                        )
                    ]
                )
                for content in contents
            )
        )

    @classmethod
    def _format_content(
        cls,
        value: Message | Sequence[Message],
        allow_tool: bool = True,
    ) -> list[dict[str, Any]]:
        """Format the message content for the Anthropic API.

        Args:
            value: The value to format.
            allow_tool: Whether to allow tool calls in the content.

        Returns:
            The formatted message content.

        Raises:
            ValueError: If the message content type is unknown.
        """
        # If it's a single message, format it.
        if isinstance(value, Message):
            return [
                {
                    "role": value.role,
                    "content": cls._format_message_content(
                        value.normalize().content, allow_tool
                    ),
                }
            ]

        # If it's a list of messages, format each one.
        if isinstance(value, Sequence) and not isinstance(value, str):
            return [cls._format_content(message, allow_tool)[0] for message in value]

        raise ValueError(f"Unknown message content type: {type(value)}")

    @classmethod
    def load_content(
        cls, content: str | list[dict[str, Any]]
    ) -> str | list[MessageContent]:
        """Load the message content from the Anthropic model to dataclasses.

        Args:
            content: The content to load.

        Returns:
            The loaded message content.

        Raises:
            TypeError: If content is not a sequence of dictionaries.
        """
        # If it's a string, return it.
        if isinstance(content, str):
            return content

        # If it's a list of dictionaries, parse them.
        if not isinstance(content, Sequence) or isinstance(content, str):
            raise TypeError("Content must be a sequence of dictionaries.")
        parsed_content: list[MessageContent] = []

        for entry in content:
            match entry.pop("type"):
                case "text":
                    parsed_content.append(TextBlock(**entry))
                case "data":
                    parsed_content.append(DataBlock(**entry))
                case "tool_use":
                    parsed_content.append(ToolCall(**entry))
                case "tool_result":
                    parsed_content.append(
                        ToolResult(
                            tool_call_id=entry.pop("tool_use_id"),
                            result=entry.pop("content"),
                            **entry,
                        )
                    )

        return parsed_content

from __future__ import annotations

import base64
import json
import os
import time
from collections.abc import AsyncGenerator, Iterable, Sequence
from dataclasses import InitVar, dataclass, field
from typing import Any, TypeVar, Unpack

from openai import AsyncOpenAI
from openai.types import CompletionUsage, ReasoningEffort
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionFunctionToolParam,
    ChatCompletionMessageCustomToolCall,
    ChatCompletionMessageFunctionToolCall,
    ChatCompletionMessageFunctionToolCallParam,
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall
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
from flexai.tool import Tool, ToolType


def get_tool_call(
    tool_use: ChatCompletionMessageFunctionToolCall | ChoiceDeltaToolCall,
) -> ToolCall | None:
    """Get the tool call from a tool use block.

    Args:
        tool_use: The tool use block to get the call from.

    Returns:
        The tool call from the tool use block.
    """
    if (
        not tool_use.id
        or not tool_use.function
        or not tool_use.function.name
        or not tool_use.function.arguments
    ):
        return None
    return ToolCall(
        id=tool_use.id,
        name=tool_use.function.name,
        input=json.loads(tool_use.function.arguments),
    )


def get_usage_block(usage: CompletionUsage | None) -> Usage:
    """Extract usage information from the OpenAI response.

    Args:
        usage: The usage object from OpenAI.

    Returns:
        A Usage object containing input tokens, output tokens, and generation time.
    """
    return (
        Usage(
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
        )
        if usage is not None
        else Usage(input_tokens=0, output_tokens=0)
    )


BASE_MODEL = TypeVar("BASE_MODEL", bound=BaseModel)


@dataclass(frozen=True)
class OpenAIClient(Client):
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
        run_args = self._complete_args_with_defaults(**input_args)

        if run_args["model"] is not None:
            model = run_args["model"]
            run_args["model"] = None  # Clear model from run_args to avoid duplication
            return await self._get_structured_response(
                messages=messages,
                model_to_use=model,
                system=system,
                tools=tools,
                **run_args,
            )

        # Send the messages to the model and get the response.
        params = self._get_params(
            messages=messages,
            system=system,
            tools=tools,
            **run_args,
        )
        start = time.monotonic()
        response = await self.client.chat.completions.create(**params, stream=False)
        generation_time = time.monotonic() - start

        # Parse out the tool uses from the response.
        message = response.choices[0].message
        tool_uses = [
            tool_call
            for tool_use_block in (message.tool_calls or [])
            if not isinstance(tool_use_block, ChatCompletionMessageCustomToolCall)
            if (tool_call := get_tool_call(tool_use_block)) is not None
        ]
        usage = get_usage_block(response.usage)
        usage.generation_time = generation_time

        # Get the content to return.
        content_to_return = tool_uses or message.content or []
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
        run_args = self._complete_args_with_defaults(**input_args)
        stream = await self.client.chat.completions.create(
            **self._get_params(
                messages=messages,
                system=system,
                tools=tools,
                **run_args,
            ),
            stream=True,
        )
        current_tool_call: ToolCall | None = None
        current_text_block: TextBlock | None = None

        async for chunk in stream:
            if not isinstance(chunk.choices, list) or not chunk.choices:
                continue
            content = chunk.choices[0].delta.content

            if content:
                yield TextBlock(text=content)
                if not current_text_block:
                    current_text_block = TextBlock(text="")
                current_text_block = current_text_block.append(content)

            for tool_call in chunk.choices[0].delta.tool_calls or []:
                if (
                    tool_call.function is None
                    or tool_call.function.name is None
                    or tool_call.id is None
                ):
                    continue
                if not current_tool_call:
                    current_tool_call = ToolCall(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        input=tool_call.function.arguments or "",
                    )
                    yield current_tool_call

                if tool_call.function.arguments:
                    yield TextBlock(text=tool_call.function.arguments)
                    current_tool_call = current_tool_call.append_input(
                        tool_call.function.arguments
                    )

        message_content = []

        if current_text_block:
            message_content.append(current_text_block)

        if current_tool_call:
            current_tool_call = current_tool_call.load_input()
            message_content.append(current_tool_call)

        yield AIMessage(content=message_content)

    def _get_params(
        self,
        messages: list[Message],
        system: str | SystemMessage,
        tools: Sequence[Tool] | None,
        **run_args: Unpack[AgentRunArgs],
    ) -> dict:
        """Get the common params to send to the model.

        Args:
            messages: The messages to send to the model.
            system: The system message to send to the model.
            tools: The tools to send to the model.
            **run_args: Additional arguments including temperature, force_tool,
                allow_tool and other run parameters.

        Returns:
            The common params to send to the model.
        """
        # Extract the run arguments we care about.
        temperature = run_args["temperature"]

        if isinstance(system, str):
            system = SystemMessage(system)
        thinking_budget = run_args.get("thinking_budget")
        reasoning_effort: ReasoningEffort | None = (
            None
            if thinking_budget is None
            else "low"
            if thinking_budget <= 10000
            else "medium"
            if thinking_budget <= 20000
            else "high"
        )
        kwargs = {
            "model": self.model,
            "messages": self._format_content([system, *messages]),
            "temperature": temperature,
            "reasoning_effort": reasoning_effort,
        }

        # If tools are provided, force the model to use them (for now).
        if tools:
            kwargs["tools"] = [self.format_tool(tool) for tool in tools]
            kwargs["tool_choice"] = "required"
            kwargs["parallel_tool_calls"] = False

        return kwargs

    async def _get_structured_response(
        self,
        messages: list[Message],
        model_to_use: type[BASE_MODEL],
        system: str | SystemMessage = "",
        tools: Sequence[Tool] | None = None,
        **run_args: Unpack[AgentRunArgs],
    ) -> AIMessage:
        """Get the structured response from the chat model.

        Args:
            messages: List of messages for the conversation
            model_to_use: The BaseModel type to use for structured response parsing
            system: System message or prompt
            tools: Optional list of tools available to the model
            **run_args: Additional arguments for the agent run

        Returns:
            AIMessage: A message containing a single instance of the structured response model

        Raises:
            ValueError: If the response fails to parse
        """
        params = self._get_params(
            messages=messages,
            system=system,
            tools=tools,
            **run_args,
        )
        params.pop("reasoning_effort", None)
        # Send the messages to the model and get the response.
        response = await self.client.chat.completions.parse(
            **params, response_format=model_to_use
        )
        result = response.choices[0].message.parsed
        if result is None:
            raise ValueError("Failed to parse the response.")
        usage = get_usage_block(response.usage)

        return AIMessage(
            content=result.model_dump_json(),
            usage=usage,
        )

    @staticmethod
    def format_type(arg_type: ToolType):
        if isinstance(arg_type, tuple):
            return {
                "anyOf": [OpenAIClient.format_type(sub_type) for sub_type in arg_type]
            }
        return {
            "type": arg_type,
        }

    @staticmethod
    def format_tool(tool: Tool) -> ChatCompletionFunctionToolParam:
        """Convert the tool to a description.

        Args:
            tool: The tool to format.

        Returns:
            A dictionary describing the tool.
        """
        input_schema = {
            "type": "object",
            "properties": {},
        }
        for param_name, param_type in tool.params:
            input_schema["properties"][param_name] = OpenAIClient.format_type(
                param_type
            )

        return ChatCompletionFunctionToolParam(
            type="function",
            function={
                "name": tool.name,
                "description": tool.description,
                "parameters": input_schema,
            },
        )

    @classmethod
    def _format_tool_result_image(
        cls, tool_result: ToolResult
    ) -> list[ChatCompletionToolMessageParam | ChatCompletionUserMessageParam]:
        return [
            cls._format_tool_result(
                ToolResult(
                    tool_call_id=tool_result.tool_call_id,
                    result="Result was an image, included in the following message.",
                )
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=[
                    cls._format_text_block(
                        TextBlock(
                            text=f"This is the result of the tool call: {tool_result.tool_call_id}"
                        )
                    ),
                    cls._format_image_block(tool_result.result),
                ],
            ),
        ]

    @classmethod
    def _format_tool_result(
        cls, tool_result: ToolResult
    ) -> ChatCompletionToolMessageParam:
        return ChatCompletionToolMessageParam(
            role="tool",
            tool_call_id=tool_result.tool_call_id,
            content=str(tool_result.result),
        )

    @classmethod
    def _format_tool_call(
        cls, tool_call: ToolCall
    ) -> ChatCompletionAssistantMessageParam:
        return ChatCompletionAssistantMessageParam(
            role="assistant",
            tool_calls=[
                ChatCompletionMessageFunctionToolCallParam(
                    type="function",
                    id=tool_call.id,
                    function={
                        "name": tool_call.name,
                        "arguments": json.dumps(tool_call.input),
                    },
                )
            ],
        )

    @classmethod
    def _format_text_block(
        cls, text_block: TextBlock
    ) -> ChatCompletionContentPartTextParam:
        return ChatCompletionContentPartTextParam(
            type="text",
            text=text_block.text,
        )

    @classmethod
    def _format_image_block(
        cls, image_block: ImageBlock
    ) -> ChatCompletionContentPartImageParam:
        return ChatCompletionContentPartImageParam(
            type="image_url",
            image_url={
                "url": f"data:{image_block.mime_type};base64,{base64.b64encode(image_block.image).decode('utf-8')}",
            },
        )

    @classmethod
    def _format_message_content_no_tool(
        cls,
        contents: Sequence[TextBlock | ImageBlock],
    ) -> list[ChatCompletionContentPartTextParam | ChatCompletionContentPartImageParam]:
        return [
            cls._format_text_block(content)
            if isinstance(content, TextBlock)
            else cls._format_image_block(content)
            if isinstance(content, ImageBlock)
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
    def _format_message_content(
        cls,
        contents: Sequence[TextBlock | ImageBlock | ToolCall | ToolResult],
    ):
        return [
            cls._format_tool_result(content)
            if isinstance(content, ToolResult)
            else cls._format_tool_call(content)
            if isinstance(content, ToolCall)
            else cls._format_message_content_no_tool([content])[0]
            for content in contents
        ]

    @classmethod
    def _format_content(
        cls, value: Message | Sequence[Message]
    ) -> Iterable[ChatCompletionMessageParam]:
        """Format the message content for the OpenAI API.

        Args:
            value: The value to format.

        Returns:
            The formatted message content.

        Raises:
            ValueError: If the message content type is unknown.
            TypeError: If an ImageBlock is sent as part of a user message.
        """
        if isinstance(value, Message):
            content = value.normalize().content
            if value.role == "user":
                # Tool calls use a "tool" role instead of "user".
                messages: list[ChatCompletionMessageParam] = []
                # OpenAI wants ToolResults, which currently are simply items in value.content, to be their own messages
                # Following is logic to extract those into their own messages, and then format the remainder of value.content as a single entity
                result_content: list[ImageBlock | TextBlock] = []
                for item in content:
                    if isinstance(item, ToolResult):
                        if isinstance(item.result, ImageBlock):
                            messages.extend(cls._format_tool_result_image(item))
                        else:
                            messages.append(cls._format_tool_result(item))
                    elif isinstance(item, ToolCall):
                        messages.append(cls._format_tool_call(item))
                    else:
                        result_content.append(item)
                if result_content:
                    messages.append(
                        ChatCompletionUserMessageParam(
                            role=value.role,
                            content=cls._format_message_content_no_tool(result_content),
                        )
                    )
                return messages

            messages: list[ChatCompletionMessageParam] = []
            for item in content:
                if isinstance(item, ToolCall):
                    messages.append(cls._format_tool_call(item))
                elif isinstance(item, ToolResult):
                    if isinstance(item.result, ImageBlock):
                        messages.extend(cls._format_tool_result_image(item))
                    else:
                        messages.append(cls._format_tool_result(item))
                else:
                    if value.role == "user":
                        messages.append(
                            ChatCompletionUserMessageParam(
                                role=value.role,
                                content=cls._format_message_content_no_tool([item]),
                            )
                        )
                        continue
                    if isinstance(item, ImageBlock):
                        raise TypeError(
                            f"ImageBlocks cannot be sent as part of {value.role} messages."
                        )
                    if value.role not in ("assistant", "system", "developer"):
                        raise ValueError(
                            f"Unknown message role: {value.role}. Only 'user', 'assistant', 'system', and 'developer' are supported."
                        )
                    # This looks a bit silly, but pyright wouldn't help us otherwise.
                    match value.role:
                        case "system":
                            messages.append(
                                {
                                    "role": value.role,
                                    "content": [cls._format_text_block(item)],
                                }
                            )
                        case "assistant":
                            messages.append(
                                {
                                    "role": value.role,
                                    "content": [cls._format_text_block(item)],
                                }
                            )
                        case "developer":
                            messages.append(
                                {
                                    "role": value.role,
                                    "content": [cls._format_text_block(item)],
                                }
                            )

            return messages

        # If it's a list of messages, format them.
        if isinstance(value, Sequence) and not isinstance(value, str):
            return [
                formatted_message
                for item in value
                for formatted_message in cls._format_content(item)
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
        if not isinstance(content, Sequence) or isinstance(content, str):
            raise TypeError("Content must be a sequence of dictionaries.")
        parsed_content: list[MessageContent] = []

        for entry in content:
            match entry.pop("type"):
                case "text":
                    parsed_content.append(TextBlock(**entry))
                case "function":
                    parsed_content.append(
                        ToolCall(
                            id=entry["id"],
                            name=entry["function"]["name"],
                            input=json.loads(entry["function"]["arguments"]),
                        )
                    )
                case "tool":
                    parsed_content.append(
                        ToolResult(
                            tool_call_id=entry.pop("tool_call_id"),
                            result=json.loads(entry.pop("content")),
                            **entry,
                        )
                    )

        return parsed_content

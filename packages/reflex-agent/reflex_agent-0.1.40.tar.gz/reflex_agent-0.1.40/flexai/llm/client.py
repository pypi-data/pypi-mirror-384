from __future__ import annotations

import functools
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, TypedDict, TypeVar, Unpack

from flexai.llm.exceptions import LLMException, map_exception
from flexai.message import AIMessage, Message, MessageContent, SystemMessage
from flexai.tool import Tool


class AgentRunArgs(TypedDict):
    """Any arguments passed to an agent run that control the response, aside from the base parameters (message list, system prompts, tools)."""

    # Whether we are forcing the AI to call a tool or not.
    force_tool: bool

    # Whether to format past tool calls literally in the input or not (to avoid some risk of misinterpretation by the AI).
    allow_tool: bool

    # Allowed thinking budget tokens for the AI. 0 if we want to disable thinking. None if we don't care (and want to use the provider's default).
    thinking_budget: int | None

    # Whether to include the LLM's internal thoughts in the response, wherever applicable.
    include_thoughts: bool

    # Sampling temperature for the model. None if to use the provider's default.
    temperature: float | None

    # A (usually pydantic) model, in case we want to force the AI's response to be structured. None if we don't need a structured response.
    model: Any | None

    # Whether to raise an exception when the AI responds with null content, or to just have the default behavior (which is to silently exit the loop).
    raise_on_null_content: bool

    # Whether to allow text responses from the model.
    allow_text: bool

    # Whether to allow image responses from the model.
    allow_image: bool


class PartialAgentRunArgs(TypedDict, total=False):
    """AgentRunArgs, but some fields are allowed to be unspecified."""

    force_tool: bool
    allow_tool: bool
    thinking_budget: int | None
    include_thoughts: bool
    temperature: float | None
    model: Any | None
    raise_on_null_content: bool
    allow_text: bool
    allow_image: bool


def with_defaults(**kwargs: Unpack[PartialAgentRunArgs]) -> AgentRunArgs:
    """Create AgentRunArgs with default values filled in.

    Args:
        **kwargs: Partial AgentRunArgs to override defaults

    Returns:
        AgentRunArgs: Complete AgentRunArgs with defaults filled in
    """
    defaults: AgentRunArgs = {
        "force_tool": False,
        "allow_tool": True,
        "thinking_budget": None,
        "include_thoughts": False,
        "temperature": None,
        "model": None,
        "raise_on_null_content": False,
        "allow_text": True,
        "allow_image": False,
    }
    return {**defaults, **kwargs}


T = TypeVar("T")


def _handle_provider_exceptions_coroutine(
    func: Callable[..., Awaitable[T]], provider: str
) -> Callable[..., Awaitable[T]]:
    """Handle provider-specific exceptions and convert them to generic LLMExceptions.

    Args:
        func: The coroutine function to wrap
        provider: The provider name ("openai", "anthropic", "gemini", etc.)

    Returns:
        A wrapper around the input function that does the improved exception handling
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Skip our own exceptions
            if isinstance(e, LLMException):
                raise
            # Map provider-specific exceptions to our generic ones
            mapped_exception = map_exception(e, provider)
            raise mapped_exception.with_traceback(e.__traceback__) from None

    return wrapper


def _handle_provider_exceptions_generator(
    func: Callable[..., AsyncIterator[T]], provider: str
) -> Callable[..., AsyncIterator[T]]:
    """Handle provider-specific exceptions and convert them to generic LLMExceptions for async generators.

    Args:
        func: The async generator function to wrap
        provider: The provider name ("openai", "anthropic", "gemini", etc.)

    Returns:
        A wrapper around the input function that does the improved exception handling
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> AsyncGenerator[T, None]:
        try:
            async for item in func(*args, **kwargs):
                yield item
        except Exception as e:
            # Skip our own exceptions
            if isinstance(e, LLMException):
                raise
            # Map provider-specific exceptions to our generic ones
            mapped_exception = map_exception(e, provider)
            raise mapped_exception.with_traceback(e.__traceback__) from None

    return wrapper


@dataclass(frozen=True)
class Client(ABC):
    """Abstract base class for language model clients.

    Defines the interface for interacting with various language models.
    Subclasses should implement the necessary methods for specific LLM providers.
    """

    # Provider name (e.g., "openai", "anthropic", "gemini")
    provider: str = field(kw_only=True)

    # Default thinking budget for LLM calls (0 if disabled, None if we don't care)
    default_thinking_budget: int | None = None

    def _complete_args_with_defaults(
        self, **run_args: Unpack[PartialAgentRunArgs]
    ) -> AgentRunArgs:
        """Fill in missing run arguments with default values.

        Default behavior is use dummy values, but this can be overriden by different clients.

        Args:
            run_args: PartialAgentRunArgs with some fields possibly missing

        Returns:
            Complete AgentRunArgs with defaults filled in
        """
        return with_defaults(**run_args)

    @abstractmethod
    async def get_chat_response(
        self,
        messages: list[Message],
        system: str | SystemMessage = "",
        tools: Sequence[Tool] | None = None,
        **input_args: Unpack[PartialAgentRunArgs],
    ) -> AIMessage:
        """Retrieve a response from the chat model.

        Args:
            messages: Conversation history to send to the model.
            system: Optional system message to set the behavior of the AI.
            tools: Optional list of tools available for the model to use.
            **input_args: Additional arguments including force_tool, thinking_budget,
                and other run parameters.

        Returns:
            A list of AI-generated messages in response to the input.

        Raises:
            LLMException: For various generic LLM-related errors
        """
        # This method will be implemented by subclasses and automatically wrapped with exception handling

    @abstractmethod
    def stream_chat_response(
        self,
        messages: list[Message],
        system: str | SystemMessage = "",
        tools: Sequence[Tool] | None = None,
        **input_args: Unpack[PartialAgentRunArgs],
    ) -> AsyncIterator[MessageContent | AIMessage]:
        """Stream the response from the chat model in real-time.

        Args:
            messages: Conversation history to send to the model.
            system: Optional system message to set the behavior of the AI.
            tools: Optional list of tools available for the model to use.
            **input_args: Additional arguments including allow_tool, force_tool,
                thinking_budget and other run parameters.

        Yields:
            AI-generated messages as they are generated by the model.

        Raises:
            LLMException: For various generic LLM-related errors
        """
        # This method will be implemented by subclasses and automatically wrapped with exception handling

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        wrapped = _handle_provider_exceptions_coroutine(
            cls.get_chat_response, cls.provider
        )
        cls.get_chat_response = wrapped  # pyright: ignore[reportAttributeAccessIssue]

        wrapped = _handle_provider_exceptions_generator(
            cls.stream_chat_response, cls.provider
        )
        cls.stream_chat_response = wrapped

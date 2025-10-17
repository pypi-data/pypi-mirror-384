import base64
import functools
import json
import operator
import os
import time
import uuid
from collections.abc import AsyncGenerator, Sequence
from dataclasses import InitVar, dataclass, field
from pathlib import Path
from typing import Any, Unpack

from google import genai
from google.genai import types
from google.genai._api_client import BaseApiClient
from google.genai.types import (
    FunctionDeclaration,
    GenerateContentResponseUsageMetadata,
    Schema,
)
from google.genai.types import Type as DataType
from google.oauth2 import service_account

from flexai.llm.client import AgentRunArgs, Client, PartialAgentRunArgs, with_defaults
from flexai.llm.exceptions import NoContentException
from flexai.message import (
    AIMessage,
    DataBlock,
    ImageBlock,
    Message,
    MessageContent,
    SystemMessage,
    TextBlock,
    ThoughtBlock,
    ToolCall,
    ToolResult,
    Usage,
)
from flexai.tool import Tool, ToolType


def get_tool_call(function_call) -> ToolCall:
    """Convert a Gemini function call to a ToolCall object.

    Args:
        function_call: The Gemini function call object containing id, name, and args.

    Returns:
        A ToolCall object with the function call information.
    """
    return ToolCall(
        id=function_call.id or str(uuid.uuid4()),
        name=function_call.name,
        input=function_call.args,
    )


def get_usage_block(
    usage_metadata: GenerateContentResponseUsageMetadata | None,
) -> Usage:
    """Extract usage information from Gemini's usage metadata.

    Args:
        usage_metadata: The usage metadata from Gemini response.

    Returns:
        A Usage object with token counts and timing information.
    """
    if not usage_metadata:
        return Usage()

    return Usage(
        input_tokens=usage_metadata.prompt_token_count or 0,
        output_tokens=usage_metadata.candidates_token_count or 0,
        thought_tokens=usage_metadata.thoughts_token_count or 0,
        cache_read_tokens=usage_metadata.cached_content_token_count or 0,
        cache_write_tokens=0,  # Currently not provided by Gemini
    )


@dataclass(frozen=True)
class GeminiClient(Client):
    """Client for the Gemini API with support for both direct API and Vertex AI endpoints.

    This client supports:
    - Direct Gemini API access using API keys
    - Vertex AI regional endpoints with Google Cloud authentication
    - Global endpoints for higher availability and reliability

    Global Endpoint:
    The global endpoint provides higher availability and reliability than single regions.
    It's supported for Gemini 2.5 Pro, 2.5 Flash, 2.0 Flash, and 2.0 Flash-Lite models.

    Usage Examples:

    # Direct API access (default)
    client = GeminiClient(api_key="your-api-key")

    # Vertex AI regional endpoint
    client = GeminiClient(
        project_id="your-project",
        location="us-central1",
        use_vertex=True
    )

    # Global endpoint (recommended for production)
    client = GeminiClient(
        project_id="your-project",
        location="global",
        use_vertex=True
    )

    Environment Variables:
    - GEMINI_API_KEY: API key for direct access
    - GOOGLE_PROJECT_ID: Default project ID for Vertex AI
    - VERTEX_AI_LOCATION: Default location (defaults to us-central1)
    - GEMINI_MODEL: Default model name

    Note: Global endpoint has some limitations:
    - No tuning support
    - No batch prediction
    - No context caching
    - No RAG corpus (RAG requests are supported)
    """

    # The provider name.
    provider: str = "gemini"

    # The API key to use for interacting with the model.
    api_key: InitVar[str] = field(default=os.environ.get("GEMINI_API_KEY", ""))

    # The client to use for interacting with the model.
    _client: genai.client.AsyncClient | None = None

    # The base URL for the Gemini API.
    base_url: InitVar[str] = field(
        default=os.environ.get(
            "GEMINI_BASE_URL",
            "https://www.googleapis.com/auth/generative-language",
        )
    )

    # The model to use for the client.
    model: str = os.getenv("GEMINI_MODEL") or "gemini-2.5-pro-preview-06-05"

    # Project ID for Vertex AI (required when using Vertex AI or global endpoint)
    project_id: str | None = field(default=os.environ.get("GOOGLE_PROJECT_ID"))

    # Location for Vertex AI endpoints (use 'global' for global endpoint)
    location: str = field(default=os.environ.get("VERTEX_AI_LOCATION", "us-central1"))

    # Whether to use Vertex AI instead of direct API
    use_vertex: bool = False

    @staticmethod
    def _get_credentials(
        use_vertex: bool, location: str, project_id: str, credential_file_path: str
    ) -> service_account.Credentials:
        """Get Google Cloud credentials for Vertex AI or global endpoint access.

        Args:
            use_vertex: Whether using Vertex AI endpoint.
            location: The location/region for the endpoint.
            project_id: Google Cloud project ID.
            credential_file_path: Path to service account credentials file.

        Returns:
            Google Cloud service account credentials.

        Raises:
            ValueError: If project_id is missing when required or if authentication fails.
        """
        credentials = None

        if use_vertex or location == "global":
            # Using Vertex AI or global endpoint
            if not project_id:
                raise ValueError(
                    "project_id is required when using Vertex AI or global endpoint. "
                    "Set GOOGLE_PROJECT_ID environment variable or pass project_id parameter."
                )

            scopes = [
                "https://www.googleapis.com/auth/cloud-platform",
                "https://www.googleapis.com/auth/generative-language",
            ]

            # Handle authentication
            if credential_file_path and Path(credential_file_path).exists():
                # Use service account file
                credentials = service_account.Credentials.from_service_account_file(
                    credential_file_path, scopes=scopes
                )
            else:
                # Use default credentials (ADC)
                try:
                    from google.auth import default

                    creds, _ = default(scopes=scopes)
                    credentials = creds

                except Exception as e:
                    raise ValueError(
                        "Failed to load default credentials. Either set up Application Default Credentials "
                        "or provide credential_file_path."
                    ) from e

        if credentials is None:
            raise ValueError(
                "No credentials were fetched for an unknown reason.",
            )

        return credentials  # pyright: ignore[reportReturnType]

    @staticmethod
    @functools.lru_cache
    def _get_vertex_client(location: str, project_id: str, credential_file_path: str):
        """Get a cached Vertex AI client instance.

        Args:
            location: The location/region for Vertex AI.
            project_id: Google Cloud project ID.
            credential_file_path: Path to service account credentials file.

        Returns:
            A cached AsyncClient configured for Vertex AI.
        """
        return genai.client.AsyncClient(
            api_client=BaseApiClient(
                vertexai=True,
                credentials=GeminiClient._get_credentials(
                    use_vertex=True,
                    location=location,
                    project_id=project_id,
                    credential_file_path=credential_file_path,
                ),
                location=location,
                project=project_id,
            )
        )

    @staticmethod
    @functools.lru_cache
    def _get_client(api_key: str):
        """Get a cached direct API client instance.

        Args:
            api_key: The Gemini API key for direct access.

        Returns:
            A cached AsyncClient configured for direct API access.
        """
        return genai.client.AsyncClient(api_client=BaseApiClient(api_key=api_key))

    def __post_init__(self, api_key, base_url, **kwargs):
        use_vertex = kwargs.get("use_vertex", self.use_vertex)
        credential_file_path = kwargs.get("credential_file_path", "")

        if use_vertex:
            object.__setattr__(
                self,
                "_client",
                GeminiClient._get_vertex_client(
                    location=self.location,
                    project_id=self.project_id,
                    credential_file_path=credential_file_path,
                ),
            )
        else:
            # Using direct API
            object.__setattr__(
                self,
                "_client",
                GeminiClient._get_client(
                    api_key=api_key,
                ),
            )

    @property
    def client(self) -> genai.client.AsyncClient:
        if self._client is None:
            raise ValueError("No Gemini Client Configured.")
        return self._client

    def _complete_args_with_defaults(
        self, **run_args: Unpack[PartialAgentRunArgs]
    ) -> AgentRunArgs:
        defaults = with_defaults(**run_args)
        if "force_tool" not in run_args:
            defaults["force_tool"] = True
        if run_args.get("thinking_budget") is None:
            defaults["thinking_budget"] = self.default_thinking_budget
        return defaults

    @staticmethod
    def format_type(arg_type: ToolType) -> Schema:
        if isinstance(arg_type, tuple):
            return Schema(
                any_of=[GeminiClient.format_type(sub_type) for sub_type in arg_type]
            )
        return Schema(type=DataType(arg_type))

    @staticmethod
    def format_tool(tool: Tool) -> FunctionDeclaration:
        """Convert a FlexAI Tool to a Gemini FunctionDeclaration.

        Args:
            tool: The FlexAI Tool object to convert.

        Returns:
            A Gemini FunctionDeclaration with the tool's name, description, and parameters.
        """
        return FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters=Schema(
                type=DataType.OBJECT,
                properties={
                    param_name: GeminiClient.format_type(param_type)
                    for param_name, param_type in tool.params
                },
            ),
        )

    @staticmethod
    def _extract_content_from_part_object(part_object: types.Part):
        """Extract content from a Gemini Part object.

        Args:
            part_object: The Gemini Part object containing text or function call data.

        Yields:
            TextBlock, ThoughtBlock, or ToolCall objects extracted from the part.
        """
        if part_object.text is not None:
            if part_object.thought is not None:
                yield ThoughtBlock(
                    text=part_object.text or "",
                )
            else:
                yield TextBlock(
                    text=part_object.text,
                )

        if part_object.function_call is not None:
            yield get_tool_call(part_object.function_call)

        if (
            part_object.inline_data is not None
            and part_object.inline_data.data is not None
            and part_object.inline_data.mime_type is not None
        ):
            yield ImageBlock(
                image=part_object.inline_data.data,
                mime_type=part_object.inline_data.mime_type,
            )

    @classmethod
    def _format_tool_call(
        cls,
        content: ToolCall,
        allow_tool: bool,
    ):
        if allow_tool:
            return {
                "functionCall": {
                    "id": content.id,
                    "name": content.name,
                    "args": content.input,
                }
            }
        return {"text": str(content)}

    @classmethod
    def _format_tool_result(
        cls,
        content: ToolResult,
        name_context: dict,
        allow_tool: bool,
    ):
        if allow_tool:
            return {
                "functionResponse": {
                    "id": content.tool_call_id,
                    "name": name_context[content.tool_call_id],
                    "response": content.result,
                }
            }
        return {"text": str(content)}

    @classmethod
    def _format_message_content(
        cls,
        content: str | MessageContent | Sequence[MessageContent],
        name_context: dict,
        allow_tool: bool,
    ):
        """Format message content for Gemini API.

        Args:
            content: The message content to format (string, MessageContent, or sequence).
            name_context: Dictionary to track tool call names by ID.
            allow_tool: Whether to allow tool-related content in the formatting.

        Returns:
            Formatted content structure for Gemini API.

        Raises:
            ValueError: If unsupported content type or tool call context issues.
        """
        if isinstance(content, str):
            return [{"text": content}]

        if isinstance(content, Sequence):
            formatted_contents = [
                cls._format_message_content(
                    item, name_context=name_context, allow_tool=allow_tool
                )
                for item in content
            ]
            # Just a list flatten. I don't like itertools.chain.from_iterable personally
            formatted_contents = [
                [item] if not isinstance(item, list) else item
                for item in formatted_contents
            ]
            return functools.reduce(operator.iadd, formatted_contents, [])

        if isinstance(content, ImageBlock):
            return {
                "inlineData": {
                    "mimeType": content.mime_type,
                    "data": base64.b64encode(content.image).decode("utf-8")
                    if isinstance(content.image, bytes)
                    else content.image,
                }
            }
        if isinstance(content, TextBlock):
            return {
                "text": content.text,
            }
        if isinstance(content, DataBlock):
            return [
                cls._format_message_content(
                    item, name_context=name_context, allow_tool=allow_tool
                )
                for item in content.into_text_and_image_blocks()
            ]

        if isinstance(content, ToolCall):
            name_context[content.id] = content.name
            return cls._format_tool_call(
                content,
                allow_tool=allow_tool,
            )

        if isinstance(content, ToolResult):
            formatted_result = content.result

            if isinstance(formatted_result, str):
                formatted_result = TextBlock(
                    text=formatted_result,
                )

            if isinstance(formatted_result, ImageBlock):
                return [
                    cls._format_tool_result(
                        content.with_result(
                            {
                                "text": "The result of this tool is an image. The next part will contain this image."
                            }
                        ),
                        name_context=name_context,
                        allow_tool=allow_tool,
                    ),
                    cls._format_message_content(
                        formatted_result,
                        name_context=name_context,
                        allow_tool=allow_tool,
                    ),
                ]

            try:
                formatted_result = cls._format_message_content(
                    formatted_result, name_context=name_context, allow_tool=allow_tool
                )
            except ValueError:
                formatted_result = {"result": str(formatted_result)}

            if content.tool_call_id not in name_context:
                raise ValueError(
                    f"Tool call {content.tool_call_id} not found in context, but a result for it was found."
                )

            return cls._format_tool_result(
                content.with_result(formatted_result),
                name_context=name_context,
                allow_tool=allow_tool,
            )

        raise ValueError(f"Unsupported content type: {type(content)}")

    def _get_params(
        self,
        messages: list[Message],
        system: str | SystemMessage,
        tools: Sequence[Tool] | None,
        stream: bool,
        **run_args: Unpack[AgentRunArgs],
    ):
        """Build parameters for Gemini API request.

        Args:
            messages: The messages to send to the model.
            system: The system message or string.
            tools: List of available tools.
            stream: Whether to stream the response.
            **run_args: Additional arguments including force_tool, include_thoughts,
                thinking_budget, use_url_context, use_google_search,
                google_search_dynamic_threshold and other parameters.

        Returns:
            Dictionary of formatted parameters for Gemini API call.
        """
        # Extract run arguments that we care about
        force_tool = run_args["force_tool"]
        allow_tool = run_args["allow_tool"]
        include_thoughts = run_args["include_thoughts"]
        model = run_args["model"]
        thinking_budget = run_args["thinking_budget"]
        allow_text = run_args["allow_text"]
        allow_image = run_args["allow_image"]

        name_context = {}

        formatted_messages = [
            {
                "role": "model" if message.role == "assistant" else "user",
                "parts": self._format_message_content(
                    message.content,
                    name_context=name_context,
                    allow_tool=allow_tool,
                ),
            }
            for message in messages
        ]

        if isinstance(system, str):
            system = SystemMessage(content=system)

        formatted_system = json.dumps(
            self._format_message_content(
                system.normalize().content,
                name_context=name_context,
                allow_tool=allow_tool,
            )
        )

        config_args: dict[str, Any] = {
            "system_instruction": formatted_system,
        }

        thinking_args = {}

        if thinking_budget is not None:
            thinking_args["thinking_budget"] = thinking_budget

        if include_thoughts:
            thinking_args["include_thoughts"] = True

        if thinking_args:
            config_args["thinking_config"] = types.ThinkingConfig(**thinking_args)

        gemini_tools = []

        if tools:
            # Create a formatted tool list
            formatted_tool_list = types.Tool(
                function_declarations=[self.format_tool(tool) for tool in tools]
            )
            gemini_tools.append(formatted_tool_list)

        if gemini_tools:
            # Create a tool config object
            tool_config = None
            if force_tool and tools:
                tool_config = types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode=types.FunctionCallingConfigMode.ANY,
                    ),
                )
            config_args.update(
                {
                    "tools": gemini_tools,
                    "tool_config": tool_config,
                }
            )

        if model is not None:
            config_args.update(
                {
                    "response_mime_type": "application/json",
                    "response_schema": model,
                }
            )

        response_modalities = []

        if allow_text:
            response_modalities.append(types.Modality.TEXT)

        if allow_image:
            response_modalities.append(types.Modality.IMAGE)

        config_args["response_modalities"] = response_modalities

        config = types.GenerateContentConfig(
            **config_args,
        )
        return {
            "model": self.model,
            "contents": formatted_messages,
            "config": config,
        }

    async def get_chat_response(
        self,
        messages: list[Message],
        system: str | SystemMessage = "",
        tools: Sequence[Tool] | None = None,
        **input_args: Unpack[PartialAgentRunArgs],
    ) -> AIMessage:
        """Get a chat response from the Gemini model.

        Args:
            messages: List of conversation messages.
            system: System message to set AI behavior.
            tools: Available tools for the model to use.
            **input_args: Additional arguments including force_tool, thinking_budget,
                include_thoughts, etc.
                google_search_dynamic_threshold and other parameters.

        Returns:
            An AIMessage containing the model's response and usage information.

        Raises:
            ValueError: If the model doesn't respond with usage metadata.
            NoContentException: If the model doesn't return any content.
        """
        run_args = self._complete_args_with_defaults(**input_args)

        params = self._get_params(
            messages=messages,
            system=system,
            tools=tools,
            stream=False,
            **run_args,
        )
        start = time.monotonic()
        response_object = await self.client.models.generate_content(
            **params,
        )
        usage_metadata = response_object.usage_metadata
        if not usage_metadata:
            raise ValueError("Gemini did not respond with any usage metadata.")
        input_tokens = usage_metadata.prompt_token_count or 0
        output_tokens = (usage_metadata.total_token_count or 0) - input_tokens
        cache_read = usage_metadata.cached_content_token_count or 0
        usage = Usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read,
            cache_write_tokens=0,  # Currently not accounted for
            generation_time=time.monotonic() - start,
        )

        # Argument to raise if no content is returned
        raise_on_null_content = run_args["raise_on_null_content"]

        if not response_object.candidates or not response_object.candidates[0].content:
            if raise_on_null_content:
                raise NoContentException(
                    message="Gemini did not respond with any content, and the candidates are null.",
                    provider="gemini",
                )
            return AIMessage(content=[], usage=usage)

        response_content_parts = response_object.candidates[0].content.parts
        if not response_content_parts:
            if raise_on_null_content:
                raise NoContentException(
                    message="Gemini did not respond with any content.",
                    provider="gemini",
                )
            return AIMessage(content=[], usage=usage)

        formatted_content_parts: list[
            ImageBlock | TextBlock | ThoughtBlock | ToolCall
        ] = []

        for part in response_content_parts:
            formatted_content_parts.extend(
                list(self._extract_content_from_part_object(part))
            )

        return AIMessage(
            content=formatted_content_parts,
            usage=usage,
        )

    async def stream_chat_response(
        self,
        messages: list[Message],
        system: str | SystemMessage = "",
        tools: Sequence[Tool] | None = None,
        **input_args: Unpack[PartialAgentRunArgs],
    ) -> AsyncGenerator[MessageContent | AIMessage, None]:
        """Stream a chat response from the Gemini model.

        Args:
            messages: List of conversation messages.
            system: System message to set AI behavior.
            tools: Available tools for the model to use.
            **input_args: Additional arguments including force_tool, thinking_budget,
                include_thoughts, use_url_context, use_google_search,
                google_search_dynamic_threshold, model, temperature,
                raise_on_null_content and other parameters.

        Yields:
            TextBlock, ThoughtBlock, ToolCall content as they're generated,
            followed by a final AIMessage with complete response and usage data.

        Raises:
            ValueError: If the model doesn't respond with usage metadata.
        """
        run_args = self._complete_args_with_defaults(**input_args)

        usage = Usage()
        params = self._get_params(
            messages=messages,
            system=system,
            tools=tools,
            stream=True,
            **run_args,
        )
        start = time.monotonic()
        response_object = await self.client.models.generate_content_stream(
            **params,
        )
        text_buffer = None
        total_content_list: list[TextBlock | ThoughtBlock | ToolCall] = []

        async for chunk in response_object:
            # Handle this case
            if not chunk.candidates or not chunk.candidates[0].content:
                continue

            usage_metadata = chunk.usage_metadata
            if not usage_metadata:
                raise ValueError("Gemini did not respond with any usage metadata.")

            # Obtaining chunk parts
            chunk_parts = chunk.candidates[0].content.parts

            usage += get_usage_block(usage_metadata)

            if isinstance(chunk_parts, list):
                for part in chunk_parts:
                    for to_yield in self._extract_content_from_part_object(part):
                        if isinstance(to_yield, TextBlock):
                            # We don't need to keep thoughts in the final message
                            if not isinstance(to_yield, ThoughtBlock):
                                if not text_buffer:
                                    text_buffer = TextBlock(text="")
                                text_buffer = text_buffer.append(to_yield.text)
                            yield to_yield
                        elif isinstance(to_yield, ToolCall):
                            total_content_list.append(to_yield)
                            yield to_yield

        usage.generation_time = time.monotonic() - start
        if text_buffer:
            total_content_list.append(text_buffer)

        yield AIMessage(
            content=total_content_list,
            usage=usage,
        )

    def _extract_text_content(self, content: Any) -> str:
        """Extract text content from response, handling various formats.

        Args:
            content: The response content to extract text from.

        Returns:
            The extracted text content.

        Raises:
            TypeError: If the response is not a string.
            ValueError: If no text content found in response.
        """
        if isinstance(content, list):
            # Filter to only TextBlock content, ignoring other types
            text_blocks = [item for item in content if isinstance(item, TextBlock)]
            if len(text_blocks) == 1:
                content = text_blocks[0]
            elif len(text_blocks) > 1:
                # Concatenate multiple text blocks
                content = "".join(block.text for block in text_blocks)
            elif len(content) == 1:
                # Fallback for single non-TextBlock item
                content = content[0]
            else:
                raise ValueError("No text content found in response.")

        if isinstance(content, TextBlock):
            content = content.text

        if not isinstance(content, str):
            raise TypeError("The response is not a string.")

        return content

    def get_endpoint_info(self) -> dict[str, str | bool]:
        """Get information about the current endpoint configuration.

        Returns:
            Dictionary with endpoint information
        """
        return {
            "location": self.location,
            "project_id": self.project_id or "",
            "is_global": self.location == "global",
            "use_vertex": self.use_vertex or self.location == "global",
            "model": self.model,
        }

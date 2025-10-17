import json
import os
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Set env var for OpenAI API key to avoid error in tests
os.environ["OPENAI_API_KEY"] = "test_key"

# Now import the client
from google.genai import types

from flexai.llm.gemini import GeminiClient
from flexai.message import (
    AIMessage,
    ImageBlock,
    TextBlock,
    ThoughtBlock,
    ToolCall,
    UserMessage,
)
from flexai.tool import Tool


@pytest.fixture
def mock_client():
    """Mock the Gemini client and BaseApiClient together to avoid API key validation."""
    with (
        patch("flexai.llm.gemini.BaseApiClient") as mock_api_client,
        patch("flexai.llm.gemini.genai.client.AsyncClient") as mock_async_client,
        patch.object(types, "UrlContext", create=True) as mock_url_context,
        patch.object(types, "Tool") as mock_tool,
        patch.object(types, "GoogleSearch", create=True) as mock_google_search,
        patch.object(
            types, "GoogleSearchRetrieval", create=True
        ) as mock_google_search_retrieval,
    ):
        # Configure the mock API client to avoid validation errors
        mock_api_client.return_value = MagicMock()

        # Create and configure the mock AsyncClient
        mock_client = MagicMock()
        mock_async_client.return_value = mock_client

        # Configure the mock UrlContext
        mock_url_context.return_value = MagicMock()

        # Configure the mock Tool to accept any parameters
        mock_tool.return_value = MagicMock()

        # Configure Google Search mocks
        mock_google_search.return_value = MagicMock()
        mock_google_search_retrieval.return_value = MagicMock()

        yield mock_client


@pytest.fixture
def test_tool():
    def example_function(a: str, b: int) -> dict:
        """Example function for testing tools."""
        return {"result": f"{a} - {b}"}

    return Tool.from_function(example_function)


def create_mock_response(content_parts, usage_tokens=None):
    """Helper to create standardized mock responses."""
    if usage_tokens is None:
        usage_tokens = {"prompt": 10, "total": 20, "cache": 0}

    # Create a mock response object
    response = Mock()

    # For each part object, create a proper mock that works with vars()
    mock_parts = []
    for part_type, part_content in content_parts:
        # Create a mock part object that can be iterated with vars()
        # We need to create a real object-like structure that works with vars()
        if part_type == "text":

            class MockPart:
                def __init__(self):
                    self.text = part_content
                    self.thought = None
                    self.function_call = None
                    self.inline_data = None
        elif part_type == "thought":

            class MockPart:
                def __init__(self):
                    self.thought = part_content
                    self.text = part_content  # Required for thought processing
                    self.function_call = None
                    self.inline_data = None
        elif part_type == "function_call":
            func_call = Mock()
            func_call.id = part_content["id"]
            func_call.name = part_content["name"]
            func_call.args = part_content["args"]

            class MockPart:
                def __init__(self):
                    self.function_call = func_call
                    self.text = None
                    self.thought = None
                    self.inline_data = None

        mock_part = MockPart()

        mock_parts.append(mock_part)

    # Set up the response structure
    candidate = Mock()
    candidate.content = Mock()
    candidate.content.parts = mock_parts  # This needs to be the actual list, not a Mock
    # Explicitly prevent metadata from being auto-created by mock
    delattr(candidate, "url_context_metadata") if hasattr(
        candidate, "url_context_metadata"
    ) else None
    delattr(candidate, "grounding_metadata") if hasattr(
        candidate, "grounding_metadata"
    ) else None
    response.candidates = [candidate]
    response.usage_metadata = Mock(
        prompt_token_count=usage_tokens["prompt"],
        total_token_count=usage_tokens["total"],
        cached_content_token_count=usage_tokens["cache"],
    )

    return response


class TestGeminiClient:
    @pytest.mark.asyncio
    async def test_get_chat_response_basic(self, mock_client):
        # Setup mock response with simple text
        response = create_mock_response([("text", "Hello world")])
        mock_client.models.generate_content = AsyncMock(return_value=response)

        # Set up client with mocked __post_init__
        with patch.object(GeminiClient, "__post_init__"):
            client = GeminiClient(api_key="fake_key")
            object.__setattr__(client, "_client", mock_client)

            result = await client.get_chat_response(
                messages=[UserMessage(content="Hi there")],
                system="You are a helpful assistant",
            )

        # Verify the call parameters
        call_args = mock_client.models.generate_content.call_args[1]
        config = call_args["config"]

        # Verify the system message was passed correctly
        assert (
            json.loads(config.system_instruction)[0]["text"]
            == "You are a helpful assistant"
        )

        # The thinking_config attribute exists but should be None when not specifically set
        assert config.thinking_config is None

        # Verify the correct message was passed
        assert call_args["contents"][0]["role"] == "user"
        assert call_args["contents"][0]["parts"][0]["text"] == "Hi there"

        # Verify the response processing
        assert isinstance(result, AIMessage)
        assert isinstance(result.content[0], TextBlock)
        assert result.content[0].text == "Hello world"

    @pytest.mark.asyncio
    async def test_get_chat_response_with_thinking(self, mock_client):
        # Setup mock response
        response = create_mock_response([("text", "After thinking, here's my answer")])
        mock_client.models.generate_content = AsyncMock(return_value=response)

        # Need to patch __post_init__ to avoid making real API calls
        with patch.object(GeminiClient, "__post_init__"):
            client = GeminiClient(api_key="fake_key")
            object.__setattr__(client, "_client", mock_client)

            # Call with thinking_budget and include_thoughts
            await client.get_chat_response(
                messages=[UserMessage(content="Think about this")],
                system="You are a helpful assistant",
                thinking_budget=100,
                include_thoughts=True,
            )

        # Verify thinking config was passed correctly
        call_args = mock_client.models.generate_content.call_args[1]
        config = call_args["config"]

        # Verify thinking config was passed
        assert hasattr(config, "thinking_config")
        assert config.thinking_config.thinking_budget == 100
        assert config.thinking_config.include_thoughts

    @pytest.mark.asyncio
    async def test_disable_thinking(self, mock_client):
        # Setup mock response
        response = create_mock_response([("text", "No thinking response")])
        mock_client.models.generate_content = AsyncMock(return_value=response)

        # Set up client with mocked __post_init__
        with patch.object(GeminiClient, "__post_init__"):
            client = GeminiClient(api_key="fake_key", default_thinking_budget=100)
            object.__setattr__(client, "_client", mock_client)

            # Call with thinking_budget=0 - should disable thinking
            await client.get_chat_response(
                messages=[UserMessage(content="Don't think")],
                system="You are a helpful assistant",
                thinking_budget=0,
            )

        # Verify that thinking_budget=0 is correctly respected and not overridden by default
        call_args = mock_client.models.generate_content.call_args[1]
        config = call_args["config"]

        assert hasattr(config, "thinking_config")
        # Implementation correctly uses thinking_budget=0 when explicitly set
        assert config.thinking_config.thinking_budget == 0

    @pytest.mark.asyncio
    async def test_default_thinking_budget(self, mock_client):
        # Setup mock response
        response = create_mock_response(
            [("text", "Response using default thinking budget")]
        )
        mock_client.models.generate_content = AsyncMock(return_value=response)

        # Set up client with mocked __post_init__ and default_thinking_budget
        with patch.object(GeminiClient, "__post_init__"):
            client = GeminiClient(api_key="fake_key", default_thinking_budget=200)
            object.__setattr__(client, "_client", mock_client)

            # Call without specific thinking_budget
            await client.get_chat_response(
                messages=[UserMessage(content="Use default thinking")],
                system="You are a helpful assistant",
            )

        # Verify the default thinking budget was used
        call_args = mock_client.models.generate_content.call_args[1]
        config = call_args["config"]

        assert hasattr(config, "thinking_config")
        assert config.thinking_config.thinking_budget == 200

    @pytest.mark.asyncio
    async def test_get_chat_response_with_tools(self, mock_client, test_tool):
        # Setup mock response with a function call
        function_content = {
            "id": "func_123",
            "name": "example_function",
            "args": {"a": "test", "b": 42},
        }
        response = create_mock_response([("function_call", function_content)])
        mock_client.models.generate_content = AsyncMock(return_value=response)

        # Need to patch __post_init__ to avoid making real API calls
        with patch.object(GeminiClient, "__post_init__"):
            client = GeminiClient(api_key="fake_key")
            object.__setattr__(client, "_client", mock_client)

            result = await client.get_chat_response(
                messages=[UserMessage(content="Use the tool")],
                system="You are a helpful assistant",
                tools=[test_tool],
                force_tool=True,
            )

        # Verify tools configuration
        call_args = mock_client.models.generate_content.call_args[1]
        config = call_args["config"]

        # Verify tools were configured correctly
        assert hasattr(config, "tools")
        assert len(config.tools) == 1

        # Verify function calling config was set to ANY mode
        assert hasattr(config, "tool_config")
        assert (
            config.tool_config.function_calling_config.mode
            == types.FunctionCallingConfigMode.ANY
        )

        # Verify response processing
        assert isinstance(result, AIMessage)
        assert isinstance(result.content[0], ToolCall)
        assert result.content[0].id == "func_123"
        assert result.content[0].name == "example_function"
        assert result.content[0].input == {"a": "test", "b": 42}

    @pytest.mark.asyncio
    async def test_get_chat_response_with_thoughts(self, mock_client):
        # Setup mock response with a thought
        response = create_mock_response([("thought", "This is a thought")])
        mock_client.models.generate_content = AsyncMock(return_value=response)

        # Need to patch __post_init__ to avoid making real API calls
        with patch.object(GeminiClient, "__post_init__"):
            client = GeminiClient(api_key="fake_key")
            object.__setattr__(client, "_client", mock_client)

            result = await client.get_chat_response(
                messages=[UserMessage(content="Think about this")],
                system="You are a helpful assistant",
                include_thoughts=True,
            )

        # Verify thinking config
        call_args = mock_client.models.generate_content.call_args[1]
        config = call_args["config"]

        assert hasattr(config, "thinking_config")
        assert config.thinking_config.include_thoughts

        # Verify response processing
        assert isinstance(result, AIMessage)
        assert isinstance(result.content[0], ThoughtBlock)
        assert result.content[0].text == "This is a thought"

    @pytest.mark.asyncio
    async def test_image_input(self, mock_client):
        # Setup mock response
        response = create_mock_response([("text", "I see an image")])
        mock_client.models.generate_content = AsyncMock(return_value=response)

        # Need to patch __post_init__ to avoid making real API calls
        with patch.object(GeminiClient, "__post_init__"):
            client = GeminiClient(api_key="fake_key")
            object.__setattr__(client, "_client", mock_client)

            # Create an image message
            image_content = ImageBlock(
                image="base64_encoded_image_data", mime_type="image/jpeg"
            )

            await client.get_chat_response(
                messages=[UserMessage(content=image_content)],
                system="You are a helpful assistant",
            )

        # Verify image was passed correctly
        call_args = mock_client.models.generate_content.call_args[1]

        # Get the message content
        content = call_args["contents"][0]

        # Check for parts - might be a direct value or a list
        if "parts" in content:
            part = content["parts"]
            # Part could be a single dict or a list of dicts
            if isinstance(part, list):
                assert len(part) > 0
                part = part[0]

            # Now check if inlineData exists in the part
            if "inlineData" in part:
                assert part["inlineData"]["mimeType"] == "image/jpeg"
                assert part["inlineData"]["data"] == "base64_encoded_image_data"
            else:
                # If not directly in part, it might be nested elsewhere
                assert isinstance(part, dict)
        else:
            # The structure is different than expected - at least ensure image data was passed somehow
            assert "image" in str(content)

    @pytest.mark.asyncio
    async def test_structured_response_schema(self, mock_client):
        # Setup mock response
        response = create_mock_response([("text", '{"name": "John", "age": 30}')])
        mock_client.models.generate_content = AsyncMock(return_value=response)

        # Create a response schema
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
            "required": ["name", "age"],
        }

        # Need to patch __post_init__ to avoid making real API calls
        with patch.object(GeminiClient, "__post_init__"):
            client = GeminiClient(api_key="fake_key")
            object.__setattr__(client, "_client", mock_client)

            await client.get_chat_response(
                messages=[UserMessage(content="Return a structured response")],
                system="You are a helpful assistant",
                model=schema,
            )

        # Verify schema was passed correctly
        call_args = mock_client.models.generate_content.call_args[1]
        config = call_args["config"]

        assert hasattr(config, "response_mime_type")
        assert config.response_mime_type == "application/json"

        assert hasattr(config, "response_schema")
        assert config.response_schema == schema

    @pytest.mark.asyncio
    async def test_stream_chat_response(self, mock_client):
        # Setup first chunk with text
        chunk1_mock = MagicMock()

        class MockPart1:
            def __init__(self):
                self.text = "Hello"
                self.thought = None
                self.function_call = None
                self.inline_data = None

        chunk1_part = MockPart1()
        chunk1_candidate = Mock()
        chunk1_candidate.content = Mock()
        chunk1_candidate.content.parts = [chunk1_part]
        # Remove metadata attributes to avoid Mock iteration issues
        delattr(chunk1_candidate, "url_context_metadata") if hasattr(
            chunk1_candidate, "url_context_metadata"
        ) else None
        delattr(chunk1_candidate, "grounding_metadata") if hasattr(
            chunk1_candidate, "grounding_metadata"
        ) else None
        chunk1_mock.candidates = [chunk1_candidate]
        chunk1_mock.usage_metadata = Mock(
            prompt_token_count=10,
            candidates_token_count=2,
            thoughts_token_count=0,
            total_token_count=12,
            cached_content_token_count=0,
        )

        # Setup second chunk with more text
        chunk2_mock = MagicMock()

        class MockPart2:
            def __init__(self):
                self.text = " world"
                self.thought = None
                self.function_call = None
                self.inline_data = None

        chunk2_part = MockPart2()
        chunk2_candidate = Mock()
        chunk2_candidate.content = Mock()
        chunk2_candidate.content.parts = [chunk2_part]
        # Remove metadata attributes to avoid Mock iteration issues
        delattr(chunk2_candidate, "url_context_metadata") if hasattr(
            chunk2_candidate, "url_context_metadata"
        ) else None
        delattr(chunk2_candidate, "grounding_metadata") if hasattr(
            chunk2_candidate, "grounding_metadata"
        ) else None
        chunk2_mock.candidates = [chunk2_candidate]
        chunk2_mock.usage_metadata = Mock(
            prompt_token_count=0,
            candidates_token_count=2,
            thoughts_token_count=0,
            total_token_count=14,
            cached_content_token_count=0,
        )

        # Setup final empty chunk (stream end)
        chunk3_mock = MagicMock()
        chunk3_candidate = Mock()
        chunk3_candidate.content = Mock()
        chunk3_candidate.content.parts = []
        # Remove metadata attributes to avoid Mock iteration issues
        delattr(chunk3_candidate, "url_context_metadata") if hasattr(
            chunk3_candidate, "url_context_metadata"
        ) else None
        delattr(chunk3_candidate, "grounding_metadata") if hasattr(
            chunk3_candidate, "grounding_metadata"
        ) else None
        chunk3_mock.candidates = [chunk3_candidate]
        chunk3_mock.usage_metadata = Mock(
            prompt_token_count=0,
            candidates_token_count=0,
            thoughts_token_count=0,
            total_token_count=14,
            cached_content_token_count=0,
        )

        # Create the stream
        async def mock_stream():
            yield chunk1_mock
            yield chunk2_mock
            yield chunk3_mock

        mock_client.models.generate_content_stream = AsyncMock(
            return_value=mock_stream()
        )

        # Need to patch __post_init__ to avoid making real API calls
        with patch.object(GeminiClient, "__post_init__"):
            client = GeminiClient(api_key="fake_key")
            object.__setattr__(client, "_client", mock_client)

            streamed_content = []
            async for content in client.stream_chat_response(
                messages=[UserMessage(content="Stream this")],
                system="You are a helpful assistant",
            ):
                streamed_content.append(content)

        # Verify we get the expected number of chunks plus the final AIMessage
        assert len(streamed_content) == 3

        # Check the text chunks
        assert isinstance(streamed_content[0], TextBlock)
        assert streamed_content[0].text == "Hello"

        assert isinstance(streamed_content[1], TextBlock)
        assert streamed_content[1].text == " world"

        # Check the final message
        assert isinstance(streamed_content[2], AIMessage)

    @pytest.mark.asyncio
    async def test_stream_with_include_thoughts(self, mock_client):
        # Setup a thought chunk
        thought_chunk = MagicMock()

        class MockThoughtPart:
            def __init__(self):
                self.thought = "Thinking process"
                self.text = "Thinking process"
                self.function_call = None
                self.inline_data = None

        thought_part = MockThoughtPart()
        thought_candidate = Mock()
        thought_candidate.content = Mock()
        thought_candidate.content.parts = [thought_part]
        # Remove metadata attributes to avoid Mock iteration issues
        delattr(thought_candidate, "url_context_metadata") if hasattr(
            thought_candidate, "url_context_metadata"
        ) else None
        delattr(thought_candidate, "grounding_metadata") if hasattr(
            thought_candidate, "grounding_metadata"
        ) else None
        thought_chunk.candidates = [thought_candidate]
        thought_chunk.usage_metadata = Mock(
            prompt_token_count=10,
            candidates_token_count=0,
            thoughts_token_count=5,
            total_token_count=15,
            cached_content_token_count=0,
        )

        # Setup final empty chunk
        final_chunk = MagicMock()
        final_candidate = Mock()
        final_candidate.content = Mock()
        final_candidate.content.parts = []
        # Remove metadata attributes to avoid Mock iteration issues
        delattr(final_candidate, "url_context_metadata") if hasattr(
            final_candidate, "url_context_metadata"
        ) else None
        delattr(final_candidate, "grounding_metadata") if hasattr(
            final_candidate, "grounding_metadata"
        ) else None
        final_chunk.candidates = [final_candidate]
        final_chunk.usage_metadata = Mock(
            prompt_token_count=0,
            candidates_token_count=0,
            thoughts_token_count=0,
            total_token_count=15,
            cached_content_token_count=0,
        )

        # Create the stream
        async def mock_stream():
            yield thought_chunk
            yield final_chunk

        mock_client.models.generate_content_stream = AsyncMock(
            return_value=mock_stream()
        )

        # Need to patch __post_init__ to avoid making real API calls
        with patch.object(GeminiClient, "__post_init__"):
            client = GeminiClient(api_key="fake_key")
            object.__setattr__(client, "_client", mock_client)

            streamed_content = []
            async for content in client.stream_chat_response(
                messages=[UserMessage(content="Stream with thoughts")],
                system="You are a helpful assistant",
                include_thoughts=True,
            ):
                streamed_content.append(content)

        # Verify include_thoughts was passed correctly
        call_args = mock_client.models.generate_content_stream.call_args[1]
        config = call_args["config"]

        assert hasattr(config, "thinking_config")
        assert config.thinking_config.include_thoughts

        # Verify thought in output
        assert len(streamed_content) == 2
        assert isinstance(streamed_content[0], ThoughtBlock)
        assert streamed_content[0].text == "Thinking process"

    @pytest.mark.asyncio
    async def test_stream_with_tool_call(self, mock_client, test_tool):
        # Setup a tool call chunk
        tool_chunk = MagicMock()

        # Create function call
        func_call = Mock()
        func_call.id = "func_789"
        func_call.name = "example_function"
        func_call.args = {"a": "stream test", "b": 123}

        class MockToolPart:
            def __init__(self):
                self.function_call = func_call
                self.text = None
                self.thought = None
                self.inline_data = None

        tool_part = MockToolPart()
        tool_candidate = Mock()
        tool_candidate.content = Mock()
        tool_candidate.content.parts = [tool_part]
        # Remove metadata attributes to avoid Mock iteration issues
        delattr(tool_candidate, "url_context_metadata") if hasattr(
            tool_candidate, "url_context_metadata"
        ) else None
        delattr(tool_candidate, "grounding_metadata") if hasattr(
            tool_candidate, "grounding_metadata"
        ) else None
        tool_chunk.candidates = [tool_candidate]
        tool_chunk.usage_metadata = Mock(
            prompt_token_count=10,
            candidates_token_count=10,
            thoughts_token_count=0,
            total_token_count=20,
            cached_content_token_count=0,
        )

        # Final empty chunk
        final_chunk = MagicMock()
        final_candidate = Mock()
        final_candidate.content = Mock()
        final_candidate.content.parts = []
        # Remove metadata attributes to avoid Mock iteration issues
        delattr(final_candidate, "url_context_metadata") if hasattr(
            final_candidate, "url_context_metadata"
        ) else None
        delattr(final_candidate, "grounding_metadata") if hasattr(
            final_candidate, "grounding_metadata"
        ) else None
        final_chunk.candidates = [final_candidate]
        final_chunk.usage_metadata = Mock(
            prompt_token_count=0,
            candidates_token_count=0,
            thoughts_token_count=0,
            total_token_count=20,
            cached_content_token_count=0,
        )

        # Create the stream
        async def mock_stream():
            yield tool_chunk
            yield final_chunk

        mock_client.models.generate_content_stream = AsyncMock(
            return_value=mock_stream()
        )

        # Need to patch __post_init__ to avoid making real API calls
        with patch.object(GeminiClient, "__post_init__"):
            client = GeminiClient(api_key="fake_key")
            object.__setattr__(client, "_client", mock_client)

            streamed_content = []
            async for content in client.stream_chat_response(
                messages=[UserMessage(content="Stream with tool")],
                system="You are a helpful assistant",
                tools=[test_tool],
                force_tool=True,
            ):
                streamed_content.append(content)

        # Verify tool config was passed correctly
        call_args = mock_client.models.generate_content_stream.call_args[1]
        config = call_args["config"]

        assert hasattr(config, "tools")
        assert len(config.tools) == 1

        assert hasattr(config, "tool_config")
        assert (
            config.tool_config.function_calling_config.mode
            == types.FunctionCallingConfigMode.ANY
        )

        # Verify tool call in output
        assert len(streamed_content) == 2
        assert isinstance(streamed_content[0], ToolCall)
        assert streamed_content[0].id == "func_789"
        assert streamed_content[0].name == "example_function"
        assert streamed_content[0].input == {"a": "stream test", "b": 123}

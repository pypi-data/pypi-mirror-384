from collections.abc import Sequence
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import BaseModel

from flexai.llm.anthropic import AnthropicClient
from flexai.llm.openai import OpenAIClient
from flexai.message import AIMessage, SystemMessage, TextBlock, ToolResult, UserMessage
from flexai.tool import Tool


# Test AnthropicClient class
@pytest.fixture
def mock_anthropic_client():
    with patch("flexai.llm.anthropic.AsyncAnthropic") as mock:
        yield mock.return_value


@pytest.mark.asyncio
async def test_anthropic_get_chat_response(mock_anthropic_client):
    client = AnthropicClient(client=mock_anthropic_client)
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=Mock(
            content=[Mock(text="AI response")],
        )
    )
    response = await client.get_chat_response([UserMessage("Hello")])
    assert isinstance(response, AIMessage)
    assert isinstance(response.content, list)
    assert len(response.content) == 1
    assert isinstance(response.content[0], TextBlock)
    assert response.content[0].text == "AI response"


# @pytest.mark.asyncio
# async def test_anthropic_stream_chat_response(mock_anthropic_client):
#     client = AnthropicClient(client=mock_anthropic_client)

#     async def mock_text_stream():
#         messages = ["Hello", " world"]
#         for message in messages:
#             yield message

#     mock_anthropic_client.messages.stream.return_value.__aenter__.return_value.text_stream = mock_text_stream()
#     responses = [
#         resp async for resp in client.stream_chat_response([UserMessage(content="Hi")])
#     ]
#     assert len(responses) == 2
#     assert all(isinstance(resp, AIMessage) for resp in responses)
#     assert [resp.content for resp in responses] == ["Hello", " world"]


def test_anthropic_to_llm_messages():
    messages = [UserMessage("Hello"), AIMessage("Hi there")]
    llm_messages = AnthropicClient._format_content(messages)
    assert llm_messages == [
        {"role": "user", "content": [{"type": "text", "text": "Hello"}]},
        {"role": "assistant", "content": [{"type": "text", "text": "Hi there"}]},
    ]


@pytest.mark.asyncio
async def test_anthropic_get_structured_response(mock_anthropic_client):
    class TestModel(BaseModel):
        name: str
        age: int

    client = AnthropicClient(client=mock_anthropic_client)
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=Mock(
            content=[Mock(text='{"name": "John", "age": 30}')],
            usage=Mock(
                input_tokens=10,
                output_tokens=20,
                cache_read_input_tokens=0,
                cache_creation_input_tokens=0,
            ),
        )
    )

    # Use the correct public interface - pass model as parameter to get_chat_response
    result = await client.get_chat_response([UserMessage("Get info")], model=TestModel)

    # The result will be an AIMessage with JSON content, we need to parse it
    assert isinstance(result, AIMessage)
    assert isinstance(result.content, str)
    parsed_result = TestModel.model_validate_json(result.content)
    assert parsed_result.name == "John"
    assert parsed_result.age == 30


def test_anthropic_add_cache_control():
    client = AnthropicClient(cache_messages=True)
    params = {
        "system": AnthropicClient._format_message_content(
            SystemMessage(
                [TextBlock("System message 1"), TextBlock("System message 2")]
            )
            .normalize()
            .content
        ),
        "tools": [{"name": "tool1"}, {"name": "tool2"}],
        "messages": [
            {"content": "Message 1", "role": "user"},
            {"content": "Message 2", "role": "assistant"},
            {"content": "Message 3", "role": "user"},
            {"content": "Message 4", "role": "assistant"},
            {"content": "Message 5", "role": "user"},
        ],
    }
    result = client._add_cache_control(params)

    # Check the system message is cached.
    assert isinstance(result["system"], Sequence)
    assert not isinstance(result["system"], str)
    assert len(result["system"]) == 2
    assert result["system"][0]["type"] == "text"
    assert result["system"][0]["text"] == "System message 1"
    assert result["system"][0]["cache_control"]["type"] == "ephemeral"
    assert "cache_control" not in result["system"][1]

    # Check only the last tool is cached.
    assert isinstance(result["tools"], Sequence)
    assert not isinstance(result["tools"], str)
    assert len(result["tools"]) == 2
    assert result["tools"][0]["name"] == "tool1"
    assert result["tools"][1]["name"] == "tool2"
    assert "cache_control" not in result["tools"][0]
    assert result["tools"][1]["cache_control"]["type"] == "ephemeral"

    # Check that the last two user messages are cached.
    assert isinstance(result["messages"], Sequence)
    assert not isinstance(result["messages"], str)
    assert len(result["messages"]) == 5
    assert isinstance(result["messages"][0]["content"], str)
    assert isinstance(result["messages"][1]["content"], str)
    assert isinstance(result["messages"][3]["content"], str)

    assert isinstance(result["messages"][2]["content"], Sequence)
    assert not isinstance(result["messages"][2]["content"], str)
    assert result["messages"][2]["content"][0]["cache_control"]
    assert isinstance(result["messages"][4]["content"], Sequence)
    assert not isinstance(result["messages"][4]["content"], str)
    assert result["messages"][4]["content"][0]["cache_control"]


def test_anthropic_tool_format():
    def complex_function(a: int, b: str, c: list) -> dict:
        """A more complex function for testing."""
        return {}

    tool = Tool.from_function(complex_function)
    description = AnthropicClient.format_tool(tool)

    assert description["name"] == "complex_function"
    assert description["description"] == "A more complex function for testing."
    assert description["input_schema"] == {
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "string"},
            "c": {"type": "array"},
        },
    }


# Test OpenAI _format_message_content with tool results
def test_openai_format_message_content_tool_result_string():
    """Test that tool results are formatted as strings for OpenAI."""
    # Test with string result
    tool_result = ToolResult(tool_call_id="call_123", result="simple string")
    formatted = OpenAIClient._format_message_content([tool_result])

    expected = [
        {"role": "tool", "tool_call_id": "call_123", "content": "simple string"}
    ]
    assert formatted == expected


def test_openai_format_message_content_tool_result_int():
    """Test that integer tool results are converted to strings."""
    tool_result = ToolResult(tool_call_id="call_456", result=42)
    formatted = OpenAIClient._format_message_content([tool_result])

    expected = [{"role": "tool", "tool_call_id": "call_456", "content": "42"}]
    assert formatted == expected


def test_openai_format_message_content_tool_result_float():
    """Test that float tool results are converted to strings."""
    tool_result = ToolResult(tool_call_id="call_789", result=3.14159)
    formatted = OpenAIClient._format_message_content([tool_result])

    expected = [{"role": "tool", "tool_call_id": "call_789", "content": "3.14159"}]
    assert formatted == expected


def test_openai_format_message_content_tool_result_bool():
    """Test that boolean tool results are converted to strings."""
    tool_result_true = ToolResult(tool_call_id="call_true", result=True)
    tool_result_false = ToolResult(tool_call_id="call_false", result=False)

    formatted_true = OpenAIClient._format_message_content([tool_result_true])
    formatted_false = OpenAIClient._format_message_content([tool_result_false])

    assert formatted_true == [
        {"role": "tool", "tool_call_id": "call_true", "content": "True"}
    ]
    assert formatted_false == [
        {"role": "tool", "tool_call_id": "call_false", "content": "False"}
    ]


def test_openai_format_message_content_tool_result_none():
    """Test that None tool results are converted to strings."""
    tool_result = ToolResult(tool_call_id="call_none", result=None)
    formatted = OpenAIClient._format_message_content([tool_result])

    expected = [{"role": "tool", "tool_call_id": "call_none", "content": "None"}]
    assert formatted == expected


def test_openai_format_message_content_tool_result_list():
    """Test that list tool results are converted to strings."""
    tool_result = ToolResult(tool_call_id="call_list", result=[1, 2, "three", True])
    formatted = OpenAIClient._format_message_content([tool_result])

    expected = [
        {
            "role": "tool",
            "tool_call_id": "call_list",
            "content": "[1, 2, 'three', True]",
        }
    ]
    assert formatted == expected


def test_openai_format_message_content_tool_result_dict():
    """Test that dict tool results are converted to strings."""
    tool_result = ToolResult(
        tool_call_id="call_dict",
        result={"key": "value", "number": 42, "nested": {"inner": True}},
    )
    formatted = OpenAIClient._format_message_content([tool_result])

    expected = [
        {
            "role": "tool",
            "tool_call_id": "call_dict",
            "content": "{'key': 'value', 'number': 42, 'nested': {'inner': True}}",
        }
    ]
    assert formatted == expected


def test_openai_format_message_content_tool_result_complex_object():
    """Test that complex object tool results are converted to strings."""

    class TestObject:
        def __init__(self):
            self.value = "test"

        def __str__(self):
            return f"TestObject(value={self.value})"

    test_obj = TestObject()
    tool_result = ToolResult(tool_call_id="call_obj", result=test_obj)
    formatted = OpenAIClient._format_message_content([tool_result])

    expected = [
        {
            "role": "tool",
            "tool_call_id": "call_obj",
            "content": "TestObject(value=test)",
        }
    ]
    assert formatted == expected


def test_openai_format_message_content_multiple_tool_results():
    """Test formatting multiple tool results in one call."""
    tool_results = [
        ToolResult(tool_call_id="call_1", result="string result"),
        ToolResult(tool_call_id="call_2", result=123),
        ToolResult(tool_call_id="call_3", result={"data": "value"}),
    ]
    formatted = OpenAIClient._format_message_content(tool_results)

    expected = [
        {"role": "tool", "tool_call_id": "call_1", "content": "string result"},
        {"role": "tool", "tool_call_id": "call_2", "content": "123"},
        {"role": "tool", "tool_call_id": "call_3", "content": "{'data': 'value'}"},
    ]
    assert formatted == expected


def test_openai_format_message_content_mixed_content_types():
    """Test formatting mixed content types including tool results."""
    content = [
        TextBlock("Hello world"),
        ToolResult(tool_call_id="call_mixed", result={"status": "success"}),
    ]
    formatted = OpenAIClient._format_message_content(content)

    expected = [
        {"type": "text", "text": "Hello world"},
        {
            "role": "tool",
            "tool_call_id": "call_mixed",
            "content": "{'status': 'success'}",
        },
    ]
    assert formatted == expected

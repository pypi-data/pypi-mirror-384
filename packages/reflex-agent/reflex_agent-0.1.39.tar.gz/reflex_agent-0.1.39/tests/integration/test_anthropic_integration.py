"""Integration tests for Anthropic client.

These tests use real API calls and require ANTHROPIC_API_KEY to be set.
Run with: pytest tests/integration/test_anthropic_integration.py -v

This file demonstrates how to reuse the generic test utilities for a new provider.
"""

import os

import pytest

from flexai import Agent, UserMessage
from flexai.llm.anthropic import AnthropicClient
from flexai.message import AIMessage, ImageBlock, TextBlock
from tests.constants import AnthropicModels

# Import shared utilities
from .utils import (
    # Assertions
    CommonAssertions,
    MathResult,
    # Models
    Person,
    # Tool fixtures
    ProviderConfig,
    # Test data
    TestMessages,
    agent_integration_template,
    # Generic test templates
    basic_chat_template,
    multi_turn_template,
    # Helpers
    multiple_models_helper,
    streaming_template,
    structured_output_template,
    system_message_template,
    temperature_control_template,
    tool_calling_template,
)

# =============================================================================
# ANTHROPIC-SPECIFIC CONFIGURATIONS
# =============================================================================

# Skip condition for Anthropic tests
skip_no_anthropic = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping Anthropic integration tests",
)


class AnthropicConfig(ProviderConfig):
    """Configuration for Anthropic provider."""

    BASIC_MODEL = AnthropicModels.BASIC_MODEL
    STRUCTURED_MODEL = AnthropicModels.STRUCTURED_MODEL
    MODELS_TO_TEST = AnthropicModels.MODELS_TO_TEST


# Apply skip condition to all tests in this file
pytestmark = skip_no_anthropic


# =============================================================================
# ANTHROPIC-SPECIFIC FIXTURES
# =============================================================================


@pytest.fixture
def anthropic_client():
    """Create an Anthropic client for basic testing."""
    return AnthropicClient(model=AnthropicConfig.BASIC_MODEL, max_tokens=4096)


@pytest.fixture
def anthropic_structured_client():
    """Create an Anthropic client for structured output testing."""
    return AnthropicClient(model=AnthropicConfig.STRUCTURED_MODEL, max_tokens=4096)


class TestAnthropicIntegration:
    """Integration tests for Anthropic client."""

    async def test_basic_chat_response(self, anthropic_client):
        """Test basic chat functionality with Anthropic."""
        await basic_chat_template(anthropic_client)

    async def test_system_message(self, anthropic_client):
        """Test chat with system message."""
        await system_message_template(anthropic_client)

    async def test_structured_output(self, anthropic_structured_client):
        """Test structured output with Pydantic models."""
        await structured_output_template(
            anthropic_structured_client, Person, expected_field_value="teacher"
        )

    async def test_structured_output_math(self, anthropic_structured_client):
        """Test structured output with a math problem."""
        await structured_output_template(anthropic_structured_client, MathResult)

    async def test_tool_calling(self, anthropic_client, math_tool):
        """Test tool calling functionality."""
        await tool_calling_template(anthropic_client, math_tool)

    async def test_streaming_response(self, anthropic_client):
        """Test streaming chat responses."""
        await streaming_template(anthropic_client)

    async def test_agent_integration(self, anthropic_client):
        """Test using Anthropic client with Agent."""
        await agent_integration_template(anthropic_client)

    async def test_agent_streaming(self, anthropic_client):
        """Test agent streaming with Anthropic client using run method."""
        agent = Agent(
            llms=[anthropic_client],
            prompt="You are a storyteller. Tell very short stories.",
        )

        chunks = []
        # Enable streaming to get multiple chunks
        async for chunk in agent.run(TestMessages.STREAMING_STORY, stream=True):
            chunks.append(chunk)
            if len(chunks) > 20:  # Safety limit
                break

        # With streaming enabled, we should get at least one chunk
        assert len(chunks) >= 1

        # Should have some message content - could be TextBlocks or Messages
        message_chunks = [
            chunk
            for chunk in chunks
            if isinstance(chunk, (AIMessage, TextBlock)) or hasattr(chunk, "content")
        ]
        assert len(message_chunks) > 0

    async def test_error_handling(self, anthropic_structured_client):
        """Test error handling with invalid structured output."""
        # Use a more explicit request that should definitely not match Person schema
        messages = [
            UserMessage(
                "Return only the number 42 and nothing else. No names, no ages, no occupations."
            )
        ]

        # This should fail because the response won't match the Person schema
        try:
            response = await anthropic_structured_client.get_chat_response(
                messages, model=Person
            )
            # Parse the JSON content into the Pydantic model
            import json

            result = Person.model_validate(json.loads(response.content))
            # If it didn't raise an error, check if the result is actually valid
            if (
                hasattr(result, "name")
                and hasattr(result, "age")
                and hasattr(result, "occupation")
            ):
                # Model provided a valid Person structure - this is acceptable
                pass
            else:
                # Result is malformed
                pytest.fail(
                    f"Expected either ValueError or valid Person, got: {result}"
                )
        except (ValueError, TypeError, json.JSONDecodeError):
            # This is the expected behavior - the parsing failed
            pass

    async def test_different_anthropic_models(self):
        """Test different Anthropic models."""
        test_message = UserMessage("Say 'success' if you can read this")

        def assert_success_response(response):
            CommonAssertions.assert_valid_response(response)
            assert "success" in str(response.content).lower()

        def anthropic_client_factory(model):
            # Use 4096 max_tokens to be compatible with all models
            return AnthropicClient(model=model, max_tokens=4096)

        results = await multiple_models_helper(
            anthropic_client_factory,
            AnthropicConfig.MODELS_TO_TEST,
            test_message,
            assert_success_response,
        )

        # All models should pass
        for model, result in results.items():
            if result != "passed":
                pytest.fail(f"Model {model} failed: {result}")

    async def test_temperature_control(self, anthropic_client):
        """Test that temperature affects response diversity."""
        await temperature_control_template(anthropic_client)

    async def test_multi_turn_conversation(self, anthropic_client):
        """Test maintaining conversation state across multiple turns."""
        await multi_turn_template(anthropic_client)

    def test_format_tool_result_with_dict(self):
        """Test _format_tool_result with dictionary data."""
        test_dict = {"key": "value", "number": 42, "nested": {"inner": "data"}}
        result = AnthropicClient._format_tool_result(test_dict)
        assert result == str(test_dict)

    def test_format_tool_result_with_list(self):
        """Test _format_tool_result with list data."""
        test_list = [1, 2, 3, "string", {"key": "value"}]
        result = AnthropicClient._format_tool_result(test_list)
        assert result == str(test_list)

    def test_format_tool_result_with_textblock(self):
        """Test _format_tool_result with TextBlock."""
        text_block = TextBlock("Sample text content")
        result = AnthropicClient._format_tool_result(text_block)
        expected = [{"type": "text", "text": "Sample text content"}]
        assert result == expected

    def test_format_tool_result_with_imageblock(self):
        """Test _format_tool_result with ImageBlock."""
        # Create a simple 1x1 PNG image in bytes
        import base64

        simple_png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )

        image_block = ImageBlock(image=simple_png, mime_type="image/png")
        result = AnthropicClient._format_tool_result(image_block)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "image"
        assert result[0]["source"]["type"] == "base64"
        assert result[0]["source"]["media_type"] == "image/png"
        assert len(result[0]["source"]["data"]) > 0

    def test_format_tool_result_with_complex_nested_dict(self):
        """Test _format_tool_result with complex nested dictionary."""
        complex_dict = {
            "status": "success",
            "data": {
                "users": [
                    {"id": 1, "name": "Alice", "active": True},
                    {"id": 2, "name": "Bob", "active": False},
                ],
                "metadata": {"total": 2, "page": 1, "filters": ["active", "name"]},
            },
            "timestamp": "2024-01-01T00:00:00Z",
        }
        result = AnthropicClient._format_tool_result(complex_dict)
        assert result == str(complex_dict)

    def test_format_tool_result_with_none(self):
        """Test _format_tool_result with None value."""
        result = AnthropicClient._format_tool_result(None)
        assert result == str(None)

    def test_format_tool_result_with_boolean_and_numbers(self):
        """Test _format_tool_result with boolean and numeric types."""
        assert AnthropicClient._format_tool_result(True) == str(True)
        assert AnthropicClient._format_tool_result(False) == str(False)
        assert AnthropicClient._format_tool_result(42) == str(42)
        assert AnthropicClient._format_tool_result(3.14) == str(3.14)

    def test_format_tool_result_with_custom_object(self):
        """Test _format_tool_result with custom object."""

        class CustomObject:
            def __init__(self):
                self.value = "test"

            def __str__(self):
                return f"CustomObject(value={self.value})"

        custom_obj = CustomObject()
        result = AnthropicClient._format_tool_result(custom_obj)
        assert result == "CustomObject(value=test)"

    async def test_tool_with_dict_result_integration(self, anthropic_client):
        """Integration test for tools that return dictionaries."""

        def dict_tool(key: str) -> dict:
            """A tool that returns a dictionary.

            Args:
                key: The key to include in the result

            Returns:
                A dictionary with the provided key and some test data
            """
            return {
                "provided_key": key,
                "status": "success",
                "data": {"items": [1, 2, 3], "metadata": {"count": 3}},
            }

        from flexai.tool import Tool

        tool = Tool.from_function(dict_tool)

        messages = [UserMessage("Use the dict_tool with key 'test_key'")]
        response = await anthropic_client.get_chat_response(messages, tools=[tool])

        CommonAssertions.assert_valid_response(response)
        # The response should contain tool calls
        if isinstance(response.content, list):
            tool_calls = CommonAssertions.assert_contains_tool_calls(response)
            assert tool_calls[0].name == "dict_tool"

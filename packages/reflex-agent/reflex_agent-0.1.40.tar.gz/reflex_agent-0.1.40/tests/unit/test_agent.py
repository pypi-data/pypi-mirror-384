import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from flexai.agent import Agent, send_message
from flexai.message import (
    AIMessage,
    Message,
    SystemMessage,
    TextBlock,
    ToolCall,
    ToolResult,
    UserMessage,
)


@pytest.fixture
def mock_llm():
    return AsyncMock()


@pytest.fixture
def mock_capability():
    return AsyncMock()


def test_agent_initialization():
    agent = Agent()
    assert len(agent.capabilities) == 0

    def custom_tool(x):
        return x

    custom_capability = Mock()
    agent_with_custom = Agent(tools=[custom_tool], capabilities=[custom_capability])
    assert custom_tool.__name__ in agent_with_custom.toolbox
    assert len(agent_with_custom.capabilities) == 1


@pytest.mark.asyncio
async def test_modify_messages(mock_capability):
    correct_argument_found = False

    async def yielder(*args):
        if args[0] == messages:
            nonlocal correct_argument_found
            correct_argument_found = True
        yield messages

    mock_capability.modify_messages = yielder
    agent = Agent(capabilities=[mock_capability])
    messages = [
        UserMessage("Test 1"),
        AIMessage("Response 1"),
        UserMessage("Test 2"),
        UserMessage("Test 3"),
    ]
    async for message in agent.modify_messages(messages):
        result = message

    assert correct_argument_found
    assert result == messages


@pytest.mark.asyncio
async def test_get_system_message(mock_capability):
    agent = Agent(prompt="Original prompt", capabilities=[mock_capability])
    correct_argument_found = False

    async def yielder(*args):
        if args[0] == SystemMessage("Original prompt"):
            nonlocal correct_argument_found
            correct_argument_found = True
        yield SystemMessage("Modified prompt")

    mock_capability.modify_prompt = yielder

    async for message in agent.get_system_message():
        result = message

    assert correct_argument_found
    assert result == SystemMessage("Modified prompt")


@pytest.mark.asyncio
async def test_invoke_tool():
    def sync_tool(x):
        return x * 2

    async def async_tool(x):
        return x * 3

    agent = Agent(tools=[sync_tool, async_tool])

    async for message in agent.invoke_tool(
        ToolCall(id="1", name="sync_tool", input={"x": 2}), []
    ):
        sync_result = message
    assert sync_result.result == 4
    assert not sync_result.is_error

    async for message in agent.invoke_tool(
        ToolCall(id="1", name="async_tool", input={"x": 2}), []
    ):
        async_result = message
    assert async_result.result == 6
    assert not async_result.is_error


@pytest.mark.asyncio
async def test_step(mock_llm):
    agent = Agent(llms=[mock_llm])
    messages: list[Message] = [UserMessage("Test")]
    mock_llm.get_chat_response.return_value = AIMessage("Response")

    result = None
    async for response in agent.run(messages):
        result = response
    assert result is not None

    mock_llm.get_chat_response.assert_called_once()
    assert isinstance(result, AIMessage)
    assert result.content == "Response"


@pytest.mark.asyncio
async def test_multiple_tool_execution():
    def tool1(x):
        return x * 2

    def tool2(y):
        return y + 10

    agent = Agent(tools=[tool1, tool2])
    response = AIMessage(
        [
            ToolCall(id="1", name="tool1", input={"x": 5}),
            ToolCall(id="2", name="tool2", input={"y": 7}),
        ]
    )

    results = []
    for tool_call in response.content:
        async for message in agent.invoke_tool(tool_call, []):
            final_response = message
        results.append(final_response)
    assert len(results) == 2
    assert results[0].result == 10
    assert results[1].result == 17


@pytest.mark.asyncio
async def test_error_handling_in_tools():
    def faulty_tool():
        raise ValueError("Tool error")

    agent = Agent(tools=[faulty_tool])
    tool_call = ToolCall(id="1", name="faulty_tool", input={})
    async for message in agent.invoke_tool(tool_call, []):
        result = message

    assert result.is_error
    assert "Tool error" in str(result.result)


@pytest.mark.asyncio
async def test_capability_chaining():
    mock_capability1 = AsyncMock()
    mock_capability2 = AsyncMock()

    generator_one_calls = []
    gen_one_return = "Generator 1 Return"

    async def generator1(*args):
        nonlocal generator_one_calls
        generator_one_calls.append(args)
        yield gen_one_return

    generator_two_calls = []

    async def generator2(*args):
        nonlocal generator_two_calls
        generator_two_calls.append(args)
        yield ""

    mock_capability1.modify_messages = generator1
    mock_capability2.modify_messages = generator2

    agent = Agent(capabilities=[mock_capability1, mock_capability2])
    messages: list[Message] = [UserMessage("test")]

    async for _ in agent.modify_messages(messages):
        pass

    assert len(generator_one_calls) == 1
    assert len(generator_two_calls) == 1
    assert generator_two_calls[0][0] == gen_one_return


@pytest.mark.asyncio
async def test_agent_stream():
    class TestAgent(Agent):
        async def invoke_tool(self, tool_call, messages):
            yield ToolResult(
                tool_call_id=tool_call.id,
                result="Tool result",
                execution_time=0.1,
                is_error=False,
            )

    def mock_tool(x):
        return x

    mock_llm = AsyncMock()
    agent = TestAgent(llms=[mock_llm], tools=[mock_tool, send_message])
    messages: list[Message] = [UserMessage("Initial message")]

    # Mock the responses from the LLM
    mock_llm.get_chat_response.side_effect = [
        AIMessage([ToolCall(id="1", name="mock_tool", input={"x": "x"})]),
        AIMessage(
            [ToolCall(id="2", name="send_message", input={"message": "Finished"})]
        ),
    ]

    out_messages = messages.copy()
    async for message in agent.run(messages):
        if isinstance(message, Message):
            print(message)
            out_messages.append(message)

    assert len(out_messages) == 4  # Initial + Tool call + Tool result + Final response
    assert isinstance(out_messages[0], UserMessage)
    assert isinstance(out_messages[1], AIMessage)
    assert isinstance(out_messages[2], UserMessage)
    assert isinstance(out_messages[3], AIMessage)
    assert out_messages[1].content[0].input["x"] == "x"
    assert out_messages[2].content == [
        ToolResult(
            tool_call_id="1", result="Tool result", execution_time=0.1, is_error=False
        )
    ]
    assert out_messages[3].content == "Finished"


@pytest.mark.asyncio
async def test_rate_limiting_simulation():
    async def slow_tool():
        await asyncio.sleep(0.1)
        return "Slow result"

    agent = Agent(tools=[slow_tool])
    tool_call = ToolCall(id="1", name="slow_tool", input={})

    async for message in agent.invoke_tool(tool_call, []):
        result = message

    assert result.execution_time >= 0.1
    assert result.result == "Slow result"


@pytest.mark.asyncio
async def test_invoke_tool_missing():
    agent = Agent(tools=[])
    tool_call = ToolCall(id="1", name="nonexistent_tool", input={})

    result = None
    async for message in agent.invoke_tool(tool_call, []):
        result = message

    assert isinstance(result, ToolResult)
    assert result.is_error
    assert isinstance(result.result, TextBlock)
    assert "not available" in result.result.text.lower()


class MockClient:
    """Mock LLM client that can be configured to raise exceptions or return responses."""

    def __init__(
        self, name: str, exception_to_raise=None, response=None, stream_response=None
    ):
        self.name = name
        self.exception_to_raise = exception_to_raise
        self.response = response or AIMessage(f"Response from {name}")
        self.stream_response = stream_response or [
            AIMessage(f"Streamed response from {name}")
        ]
        self.get_chat_response_called = False
        self.stream_chat_response_called = False

    async def get_chat_response(self, messages, system="", tools=None, **kwargs):
        self.get_chat_response_called = True
        if self.exception_to_raise:
            raise self.exception_to_raise
        return self.response

    async def stream_chat_response(self, messages, system="", tools=None, **kwargs):
        self.stream_chat_response_called = True
        if self.exception_to_raise:
            raise self.exception_to_raise
        for item in self.stream_response:
            yield item


@pytest.mark.asyncio
async def test_get_chat_response_first_client_succeeds():
    """Test _get_chat_response when the first client succeeds."""
    client1 = MockClient("client1")
    client2 = MockClient("client2")
    agent = Agent(llms=[client1, client2])

    messages = [UserMessage("Test")]
    system = SystemMessage("System prompt")
    tools = []

    response = await agent._get_chat_response(messages, system, tools)

    assert client1.get_chat_response_called
    assert not client2.get_chat_response_called
    assert response.content == "Response from client1"


@pytest.mark.asyncio
async def test_get_chat_response_first_client_fails_second_succeeds():
    """Test _get_chat_response when first client fails but second succeeds."""
    client1 = MockClient("client1", exception_to_raise=ValueError("Client1 failed"))
    client2 = MockClient("client2")
    agent = Agent(llms=[client1, client2])

    messages = [UserMessage("Test")]
    system = SystemMessage("System prompt")
    tools = []

    response = await agent._get_chat_response(messages, system, tools)

    assert client1.get_chat_response_called
    assert client2.get_chat_response_called
    assert response.content == "Response from client2"


@pytest.mark.asyncio
async def test_get_chat_response_multiple_clients_some_fail():
    """Test _get_chat_response with multiple clients where some fail."""
    client1 = MockClient("client1", exception_to_raise=ValueError("Client1 failed"))
    client2 = MockClient("client2", exception_to_raise=RuntimeError("Client2 failed"))
    client3 = MockClient("client3")
    client4 = MockClient("client4")
    agent = Agent(llms=[client1, client2, client3, client4])

    messages = [UserMessage("Test")]
    system = SystemMessage("System prompt")
    tools = []

    response = await agent._get_chat_response(messages, system, tools)

    assert client1.get_chat_response_called
    assert client2.get_chat_response_called
    assert client3.get_chat_response_called
    assert not client4.get_chat_response_called  # Should stop at client3
    assert response.content == "Response from client3"


@pytest.mark.asyncio
async def test_get_chat_response_all_clients_fail():
    """Test _get_chat_response when all clients fail."""
    client1 = MockClient("client1", exception_to_raise=ValueError("Client1 failed"))
    client2 = MockClient("client2", exception_to_raise=RuntimeError("Client2 failed"))
    client3 = MockClient(
        "client3", exception_to_raise=ConnectionError("Client3 failed")
    )
    agent = Agent(llms=[client1, client2, client3])

    messages = [UserMessage("Test")]
    system = SystemMessage("System prompt")
    tools = []

    with pytest.raises(ConnectionError, match="Client3 failed"):
        await agent._get_chat_response(messages, system, tools)

    assert client1.get_chat_response_called
    assert client2.get_chat_response_called
    assert client3.get_chat_response_called


@pytest.mark.asyncio
async def test_get_chat_response_with_callback_blocks_retry():
    """Test _get_chat_response with callback that prevents retries."""
    client1 = MockClient("client1", exception_to_raise=ValueError("Client1 failed"))
    client2 = MockClient("client2")
    agent = Agent(llms=[client1, client2])

    def callback(exception, llm_index):
        return False  # Don't retry

    messages = [UserMessage("Test")]
    system = SystemMessage("System prompt")
    tools = []

    with pytest.raises(ValueError, match="Client1 failed"):
        await agent._get_chat_response(
            messages, system, tools, llm_exception_callback=callback
        )

    assert client1.get_chat_response_called
    assert not client2.get_chat_response_called


@pytest.mark.asyncio
async def test_get_chat_response_with_callback_allows_retry():
    """Test _get_chat_response with callback that allows retries."""
    client1 = MockClient("client1", exception_to_raise=ValueError("Client1 failed"))
    client2 = MockClient("client2")
    agent = Agent(llms=[client1, client2])

    def callback(exception, llm_index):
        return True  # Always retry

    messages = [UserMessage("Test")]
    system = SystemMessage("System prompt")
    tools = []

    response = await agent._get_chat_response(
        messages, system, tools, llm_exception_callback=callback
    )

    assert client1.get_chat_response_called
    assert client2.get_chat_response_called
    assert response.content == "Response from client2"


@pytest.mark.asyncio
async def test_stream_chat_response_first_client_succeeds():
    """Test _stream_chat_response when the first client succeeds."""
    client1 = MockClient(
        "client1", stream_response=["chunk1", "chunk2", AIMessage("Final from client1")]
    )
    client2 = MockClient("client2")
    agent = Agent(llms=[client1, client2])

    messages = [UserMessage("Test")]
    system = SystemMessage("System prompt")
    tools = []

    results = []
    async for chunk in agent._stream_chat_response(messages, system, tools):
        results.append(chunk)

    assert client1.stream_chat_response_called
    assert not client2.stream_chat_response_called
    assert len(results) == 3
    assert results[0] == "chunk1"
    assert results[1] == "chunk2"
    assert results[2].content == "Final from client1"


@pytest.mark.asyncio
async def test_stream_chat_response_first_client_fails_second_succeeds():
    """Test _stream_chat_response when first client fails but second succeeds."""
    client1 = MockClient("client1", exception_to_raise=ValueError("Client1 failed"))
    client2 = MockClient(
        "client2", stream_response=[AIMessage("Response from client2")]
    )
    agent = Agent(llms=[client1, client2])

    messages = [UserMessage("Test")]
    system = SystemMessage("System prompt")
    tools = []

    results = []
    async for chunk in agent._stream_chat_response(messages, system, tools):
        results.append(chunk)

    assert client1.stream_chat_response_called
    assert client2.stream_chat_response_called
    assert len(results) == 1
    assert results[0].content == "Response from client2"


@pytest.mark.asyncio
async def test_stream_chat_response_multiple_clients_some_fail():
    """Test _stream_chat_response with multiple clients where some fail."""
    client1 = MockClient("client1", exception_to_raise=ValueError("Client1 failed"))
    client2 = MockClient("client2", exception_to_raise=RuntimeError("Client2 failed"))
    client3 = MockClient(
        "client3", stream_response=["chunk", AIMessage("Success from client3")]
    )
    client4 = MockClient("client4")
    agent = Agent(llms=[client1, client2, client3, client4])

    messages = [UserMessage("Test")]
    system = SystemMessage("System prompt")
    tools = []

    results = []
    async for chunk in agent._stream_chat_response(messages, system, tools):
        results.append(chunk)

    assert client1.stream_chat_response_called
    assert client2.stream_chat_response_called
    assert client3.stream_chat_response_called
    assert not client4.stream_chat_response_called  # Should stop at client3
    assert len(results) == 2
    assert results[0] == "chunk"
    assert results[1].content == "Success from client3"


@pytest.mark.asyncio
async def test_stream_chat_response_all_clients_fail():
    """Test _stream_chat_response when all clients fail."""
    client1 = MockClient("client1", exception_to_raise=ValueError("Client1 failed"))
    client2 = MockClient("client2", exception_to_raise=RuntimeError("Client2 failed"))
    client3 = MockClient(
        "client3", exception_to_raise=ConnectionError("Client3 failed")
    )
    agent = Agent(llms=[client1, client2, client3])

    messages = [UserMessage("Test")]
    system = SystemMessage("System prompt")
    tools = []

    results = []
    with pytest.raises(ConnectionError, match="Client3 failed"):
        async for chunk in agent._stream_chat_response(messages, system, tools):
            results.append(chunk)

    assert client1.stream_chat_response_called
    assert client2.stream_chat_response_called
    assert client3.stream_chat_response_called
    assert len(results) == 0  # No chunks should be yielded on failure


@pytest.mark.asyncio
async def test_stream_chat_response_with_callback_blocks_retry():
    """Test _stream_chat_response with callback that prevents retries."""
    client1 = MockClient("client1", exception_to_raise=ValueError("Client1 failed"))
    client2 = MockClient("client2")
    agent = Agent(llms=[client1, client2])

    def callback(exception, llm_index):
        return False  # Don't retry

    messages = [UserMessage("Test")]
    system = SystemMessage("System prompt")
    tools = []

    results = []
    with pytest.raises(ValueError, match="Client1 failed"):
        async for chunk in agent._stream_chat_response(
            messages, system, tools, llm_exception_callback=callback
        ):
            results.append(chunk)

    assert client1.stream_chat_response_called
    assert not client2.stream_chat_response_called
    assert len(results) == 0


@pytest.mark.asyncio
async def test_stream_chat_response_with_callback_allows_retry():
    """Test _stream_chat_response with callback that allows retries."""
    client1 = MockClient("client1", exception_to_raise=ValueError("Client1 failed"))
    client2 = MockClient("client2", stream_response=[AIMessage("Success from client2")])
    agent = Agent(llms=[client1, client2])

    def callback(exception, llm_index):
        return True  # Always retry

    messages = [UserMessage("Test")]
    system = SystemMessage("System prompt")
    tools = []

    results = []
    async for chunk in agent._stream_chat_response(
        messages, system, tools, llm_exception_callback=callback
    ):
        results.append(chunk)

    assert client1.stream_chat_response_called
    assert client2.stream_chat_response_called
    assert len(results) == 1
    assert results[0].content == "Success from client2"


@pytest.mark.asyncio
async def test_mixed_exception_scenarios():
    """Test complex scenarios with different types of exceptions."""
    # Different exception types for variety
    client1 = MockClient("client1", exception_to_raise=TimeoutError("Timeout"))
    client2 = MockClient("client2", exception_to_raise=PermissionError("Access denied"))
    client3 = MockClient("client3")
    agent = Agent(llms=[client1, client2, client3])

    messages = [UserMessage("Test")]
    system = SystemMessage("System prompt")
    tools = []

    # Test get_chat_response
    response = await agent._get_chat_response(messages, system, tools)
    assert response.content == "Response from client3"

    # Reset call flags
    client1.get_chat_response_called = False
    client1.stream_chat_response_called = False
    client2.get_chat_response_called = False
    client2.stream_chat_response_called = False
    client3.get_chat_response_called = False
    client3.stream_chat_response_called = False

    # Test stream_chat_response
    results = []
    async for chunk in agent._stream_chat_response(messages, system, tools):
        results.append(chunk)

    assert len(results) == 1
    assert results[0].content == "Streamed response from client3"


@pytest.mark.asyncio
async def test_get_system_message_no_capabilities():
    agent = Agent(prompt="Test system prompt")

    result = None
    async for message in agent.get_system_message():
        result = message

    assert isinstance(result, SystemMessage)
    assert result.content == "Test system prompt"


@pytest.mark.asyncio
async def test_get_system_message_with_modifying_capability():
    from flexai.capability import Capability

    class ModifyingCapability(Capability):
        async def modify_prompt(self, prompt):
            yield SystemMessage("Modified: " + prompt.content)

    capability = ModifyingCapability()
    agent = Agent(prompt="Original prompt", capabilities=[capability])

    result = None
    async for message in agent.get_system_message():
        result = message

    assert isinstance(result, SystemMessage)
    assert result.content == "Modified: Original prompt"


@pytest.mark.asyncio
async def test_get_tools_no_capabilities():
    def test_tool():
        return "test"

    agent = Agent(tools=[test_tool])

    result = None
    async for tools in agent.get_tools():
        result = tools

    assert len(result) == 1
    assert result[0].name == "test_tool"


@pytest.mark.asyncio
async def test_get_tools_with_modifying_capability():
    from flexai.capability import Capability

    def test_tool():
        return "test"

    def additional_tool():
        return "additional"

    class ModifyingCapability(Capability):
        async def modify_tools(self, tools):
            from flexai.tool import Tool

            new_tool = Tool.from_function(additional_tool)
            yield [*tools, new_tool]

    capability = ModifyingCapability()
    agent = Agent(tools=[test_tool], capabilities=[capability])

    result = None
    async for tools in agent.get_tools():
        result = tools

    assert len(result) == 2
    tool_names = [tool.name for tool in result]
    assert "test_tool" in tool_names
    assert "additional_tool" in tool_names

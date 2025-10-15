from unittest.mock import Mock

from pydantic_ai import RunUsage

from verse_sdk.integrations.pydantic_ai.utils import (
    calculate_total_tokens,
    get_finish_reason,
    get_generation_messages,
    get_operation_type,
    get_usage,
)


class TestCalculateTotalTokens:
    def test_calculate_total_tokens_with_valid_usage(self):
        assert (
            calculate_total_tokens(
                RunUsage(
                    input_tokens=100,
                    output_tokens=50,
                    cache_read_tokens=0,
                    requests=1,
                    tool_calls=0,
                    details={},
                )
            )
            == 150
        )

    def test_calculate_total_tokens_with_zero_tokens(self):
        assert (
            calculate_total_tokens(
                RunUsage(
                    input_tokens=0,
                    output_tokens=0,
                    cache_read_tokens=0,
                    requests=1,
                    tool_calls=0,
                    details={},
                )
            )
            is None
        )

    def test_calculate_total_tokens_with_none_input_tokens(self):
        assert (
            calculate_total_tokens(
                RunUsage(
                    input_tokens=None,
                    output_tokens=50,
                    cache_read_tokens=0,
                    requests=1,
                    tool_calls=0,
                    details={},
                )
            )
            is None
        )

    def test_calculate_total_tokens_with_none_output_tokens(self):
        assert (
            calculate_total_tokens(
                RunUsage(
                    input_tokens=100,
                    output_tokens=None,
                    cache_read_tokens=0,
                    requests=1,
                    tool_calls=0,
                    details={},
                )
            )
            is None
        )


class TestGetFinishReason:
    def test_get_finish_reason_with_messages(self):
        mock_message = Mock()
        mock_message.finish_reason = "stop"

        mock_ctx = Mock()
        mock_ctx.messages = [mock_message]
        assert get_finish_reason(mock_ctx) == "stop"

    def test_get_finish_reason_with_multiple_messages(self):
        mock_message1 = Mock()
        mock_message1.finish_reason = "length"
        mock_message2 = Mock()
        mock_message2.finish_reason = "tool_call"

        mock_ctx = Mock()
        mock_ctx.messages = [mock_message1, mock_message2]
        assert get_finish_reason(mock_ctx) == "tool_call"

    def test_get_finish_reason_with_no_messages(self):
        mock_ctx = Mock()
        mock_ctx.messages = []
        assert get_finish_reason(mock_ctx) == ""

    def test_get_finish_reason_with_no_messages_attribute(self):
        mock_ctx = Mock()
        del mock_ctx.messages
        assert get_finish_reason(mock_ctx) == ""

    def test_get_finish_reason_with_none_messages(self):
        mock_ctx = Mock()
        mock_ctx.messages = None
        assert get_finish_reason(mock_ctx) == ""

    def test_get_finish_reason_with_empty_finish_reason(self):
        mock_message = Mock()
        mock_message.finish_reason = ""

        mock_ctx = Mock()
        mock_ctx.messages = [mock_message]
        assert get_finish_reason(mock_ctx) == ""


class TestGetGenerationMessages:
    def test_get_generation_messages_with_no_messages(self):
        mock_ctx = Mock()
        mock_ctx.messages = []
        assert get_generation_messages(mock_ctx) == []

    def test_get_generation_messages_with_no_messages_attribute(self):
        mock_ctx = Mock()
        del mock_ctx.messages
        assert get_generation_messages(mock_ctx) == []

    def test_get_generation_messages_with_system_prompt(self):
        mock_part = Mock()
        mock_part.__class__.__name__ = "SystemPromptPart"
        mock_part.content = "You are a helpful assistant"

        mock_message = Mock()
        mock_message.parts = [mock_part]

        mock_ctx = Mock()
        mock_ctx.messages = [mock_message]
        result = get_generation_messages(mock_ctx)

        assert len(result) == 1
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are a helpful assistant"
        assert result[0]["function_call"] is None
        assert result[0]["name"] is None
        assert result[0]["tool_calls"] is None

    def test_get_generation_messages_with_user_prompt(self):
        mock_part = Mock()
        mock_part.__class__.__name__ = "UserPromptPart"
        mock_part.content = "Hello, how are you?"

        mock_message = Mock()
        mock_message.parts = [mock_part]

        mock_ctx = Mock()
        mock_ctx.messages = [mock_message]

        result = get_generation_messages(mock_ctx)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello, how are you?"
        assert result[0]["function_call"] is None
        assert result[0]["name"] is None
        assert result[0]["tool_calls"] is None

    def test_get_generation_messages_with_tool_call(self):
        mock_part = Mock()
        mock_part.__class__.__name__ = "ToolCallPart"
        mock_part.tool_name = "get_weather"
        mock_part.args = '{"location": "New York"}'
        mock_part.tool_call_id = "call_123"

        mock_message = Mock()
        mock_message.parts = [mock_part]

        mock_ctx = Mock()
        mock_ctx.messages = [mock_message]
        result = get_generation_messages(mock_ctx)

        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == ""
        assert result[0]["function_call"] is None
        assert result[0]["name"] is None
        assert len(result[0]["tool_calls"]) == 1
        assert result[0]["tool_calls"][0]["id"] == "call_123"
        assert result[0]["tool_calls"][0]["type"] == "function"
        assert result[0]["tool_calls"][0]["function"]["name"] == "get_weather"
        assert (
            result[0]["tool_calls"][0]["function"]["arguments"]
            == '{"location": "New York"}'
        )

    def test_get_generation_messages_with_text_part(self):
        mock_part = Mock()
        mock_part.__class__.__name__ = "TextPart"
        mock_part.content = "I can help you with that."

        mock_message = Mock()
        mock_message.parts = [mock_part]

        mock_ctx = Mock()
        mock_ctx.messages = [mock_message]
        result = get_generation_messages(mock_ctx)

        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == "I can help you with that."
        assert result[0]["function_call"] is None
        assert result[0]["name"] is None
        assert result[0]["tool_calls"] is None

    def test_get_generation_messages_with_tool_return_part(self):
        mock_part = Mock()
        mock_part.__class__.__name__ = "ToolReturnPart"
        mock_part.content = "Tool result"
        mock_part.tool_call_id = "call_123"

        mock_message = Mock()
        mock_message.parts = [mock_part]

        mock_ctx = Mock()
        mock_ctx.messages = [mock_message]

        result = get_generation_messages(mock_ctx)
        assert result == [
            {
                "role": "tool",
                "content": '"Tool result"',
                "id": "call_123",
            }
        ]

    def test_get_generation_messages_with_multiple_parts(self):
        mock_text_part = Mock()
        mock_text_part.__class__.__name__ = "TextPart"
        mock_text_part.content = "I'll help you with that."

        mock_tool_part = Mock()
        mock_tool_part.__class__.__name__ = "ToolCallPart"
        mock_tool_part.tool_name = "search"
        mock_tool_part.args = '{"query": "test"}'
        mock_tool_part.tool_call_id = "call_456"

        mock_message = Mock()
        mock_message.parts = [mock_text_part, mock_tool_part]

        mock_ctx = Mock()
        mock_ctx.messages = [mock_message]

        result = get_generation_messages(mock_ctx)

        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == "I'll help you with that."
        assert len(result[0]["tool_calls"]) == 1

    def test_get_generation_messages_with_multiple_messages(self):
        mock_system_part = Mock()
        mock_system_part.__class__.__name__ = "SystemPromptPart"
        mock_system_part.content = "You are helpful"

        mock_user_part = Mock()
        mock_user_part.__class__.__name__ = "UserPromptPart"
        mock_user_part.content = "Hello"

        mock_system_message = Mock()
        mock_system_message.parts = [mock_system_part]

        mock_user_message = Mock()
        mock_user_message.parts = [mock_user_part]

        mock_ctx = Mock()
        mock_ctx.messages = [mock_system_message, mock_user_message]

        result = get_generation_messages(mock_ctx)

        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are helpful"
        assert result[1]["role"] == "user"
        assert result[1]["content"] == "Hello"

    def test_get_generation_messages_with_message_without_parts(self):
        mock_message = Mock()
        del mock_message.parts

        mock_ctx = Mock()
        mock_ctx.messages = [mock_message]

        assert get_generation_messages(mock_ctx) == []


class TestGetOperationType:
    def test_get_operation_type_with_messages(self):
        mock_ctx = Mock()
        mock_ctx.messages = [Mock()]
        assert get_operation_type(mock_ctx) == "chat"

    def test_get_operation_type_with_no_messages(self):
        mock_ctx = Mock()
        mock_ctx.messages = []
        assert get_operation_type(mock_ctx) == "completion"

    def test_get_operation_type_with_no_messages_attribute(self):
        mock_ctx = Mock()
        del mock_ctx.messages
        assert get_operation_type(mock_ctx) == "completion"

    def test_get_operation_type_with_none_messages(self):
        mock_ctx = Mock()
        mock_ctx.messages = None
        assert get_operation_type(mock_ctx) == "completion"


class TestGetUsage:
    def test_get_usage_with_valid_data(self):
        usage = RunUsage(
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=25,
            requests=1,
            tool_calls=2,
            details={},
        )

        result = get_usage(usage)
        assert result["completion_tokens"] == 50
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        assert result["prompt_tokens"] == 100
        assert result["tool_calls"] == 2
        assert result["total_tokens"] == 150

    def test_get_usage_with_none_tokens(self):
        usage = RunUsage(
            input_tokens=None,
            output_tokens=None,
            cache_read_tokens=0,
            requests=1,
            tool_calls=0,
            details={},
        )

        result = get_usage(usage)
        assert result["completion_tokens"] is None
        assert result["input_tokens"] is None
        assert result["output_tokens"] is None
        assert result["prompt_tokens"] is None
        assert result["tool_calls"] == 0
        assert result["total_tokens"] is None

    def test_get_usage_with_zero_tokens(self):
        usage = RunUsage(
            input_tokens=0,
            output_tokens=0,
            cache_read_tokens=0,
            requests=1,
            tool_calls=0,
            details={},
        )

        result = get_usage(usage)
        assert result["completion_tokens"] == 0
        assert result["input_tokens"] == 0
        assert result["output_tokens"] == 0
        assert result["prompt_tokens"] == 0
        assert result["tool_calls"] == 0
        assert result["total_tokens"] is None

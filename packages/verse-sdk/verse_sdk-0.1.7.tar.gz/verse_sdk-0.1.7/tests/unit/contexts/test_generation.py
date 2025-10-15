from unittest.mock import Mock

from verse_sdk.contexts.generation import GenerationContext


class TestGenerationContextCompletions:
    def setup_method(self):
        self.mock_span = Mock()
        self.mock_span.get_span_context.return_value.is_valid = True
        self.mock_span.set_attribute = Mock()
        self.mock_span.add_event = Mock()

        self.context = GenerationContext.__new__(GenerationContext)
        self.context._span = self.mock_span
        self.context.set_attributes = Mock(return_value=self.context)

    def test_completions_empty_list(self):
        result = self.context.completions([])
        assert result is self.context
        self.context.set_attributes.assert_not_called()

    def test_completions_single_text_choice(self):
        choice = {"text": "Hello, world!"}
        choices = [choice]

        result = self.context.completions(choices)
        assert result is self.context
        self.context.set_attributes.assert_called_once_with(
            **{
                "gen_ai.completion.0.role": "assistant",
                "gen_ai.completion.0.content": "Hello, world!",
            }
        )

    def test_completions_multiple_text_choices(self):
        choices = [
            {"text": "First response"},
            {"text": "Second response"},
            {"text": "Third response"},
        ]

        result = self.context.completions(choices)

        assert result is self.context
        expected_calls = [
            {
                "gen_ai.completion.0.role": "assistant",
                "gen_ai.completion.0.content": "First response",
            },
            {
                "gen_ai.completion.1.role": "assistant",
                "gen_ai.completion.1.content": "Second response",
            },
            {
                "gen_ai.completion.2.role": "assistant",
                "gen_ai.completion.2.content": "Third response",
            },
        ]

        assert self.context.set_attributes.call_count == 3
        for i, call in enumerate(self.context.set_attributes.call_args_list):
            call.assert_called_once_with(**expected_calls[i])

    def test_completions_with_message_object(self):
        message = {"role": "assistant", "content": "This is a test message"}
        choice = {"message": message}
        choices = [choice]

        result = self.context.completions(choices)
        result.set_attributes.assert_called_once_with(
            **{
                "gen_ai.completion.0.content": "This is a test message",
                "gen_ai.completion.0.function_call.name": None,
                "gen_ai.completion.0.function_call.arguments": None,
                "gen_ai.completion.0.role": "assistant",
            }
        )

    def test_completions_with_function_call(self):
        message = {
            "role": "assistant",
            "content": "I'll call a function",
            "function_call": {
                "name": "get_weather",
                "arguments": '{"location": "New York"}',
            },
        }
        choice = {"message": message}
        choices = [choice]

        result = self.context.completions(choices)
        result.set_attributes.assert_called_once_with(
            **{
                "gen_ai.completion.0.content": "I'll call a function",
                "gen_ai.completion.0.function_call.name": "get_weather",
                "gen_ai.completion.0.function_call.arguments": '{"location": "New York"}',
                "gen_ai.completion.0.role": "assistant",
            }
        )

    def test_completions_with_tool_calls(self):
        message = {
            "role": "assistant",
            "content": "I'll use some tools",
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "search_database",
                        "arguments": '{"query": "test"}',
                    },
                },
                {
                    "id": "call_456",
                    "type": "function",
                    "function": {
                        "name": "send_email",
                        "arguments": '{"to": "user@example.com"}',
                    },
                },
            ],
        }
        choice = {"message": message}
        choices = [choice]

        result = self.context.completions(choices)
        result.set_attributes.assert_called_once_with(
            **{
                "gen_ai.completion.0.content": "I'll use some tools",
                "gen_ai.completion.0.function_call.name": None,
                "gen_ai.completion.0.function_call.arguments": None,
                "gen_ai.completion.0.role": "assistant",
                "gen_ai.completion.0.tool_call.0.id": "call_123",
                "gen_ai.completion.0.tool_call.0.type": "function",
                "gen_ai.completion.0.tool_call.0.function.name": "search_database",
                "gen_ai.completion.0.tool_call.0.function.arguments": '{"query": "test"}',
                "gen_ai.completion.0.tool_call.1.id": "call_456",
                "gen_ai.completion.0.tool_call.1.type": "function",
                "gen_ai.completion.0.tool_call.1.function.name": "send_email",
                "gen_ai.completion.0.tool_call.1.function.arguments": '{"to": "user@example.com"}',
            }
        )

    def test_completions_with_delta_object(self):
        delta = {"role": "assistant", "content": "Streaming content"}
        choice = {"delta": delta}
        choices = [choice]

        result = self.context.completions(choices)
        result.set_attributes.assert_called_once_with(
            **{
                "gen_ai.completion.0.content": "Streaming content",
                "gen_ai.completion.0.function_call.name": None,
                "gen_ai.completion.0.function_call.arguments": None,
                "gen_ai.completion.0.role": "assistant",
            }
        )

    def test_completions_mixed_choices(self):
        choices = [
            {"text": "Simple text response"},
            {"message": {"role": "assistant", "content": "Message response"}},
            {"delta": {"role": "assistant", "content": "Delta response"}},
        ]

        result = self.context.completions(choices)
        assert result.set_attributes.call_count == 3

    def test_completions_none_choice(self):
        choices = [None]
        result = self.context.completions(choices)
        result.set_attributes.assert_not_called()

    def test_completions_empty_message(self):
        choice = {"text": ""}
        choices = [choice]
        result = self.context.completions(choices)
        result.set_attributes.assert_called_once_with(
            **{
                "gen_ai.completion.0.role": "assistant",
                "gen_ai.completion.0.content": "",
            }
        )

    def test_completions_exception_handling(self):
        self.context.set_attributes.side_effect = Exception("Test error")
        choices = [{"text": "Test"}]
        result = self.context.completions(choices)
        assert result is self.context

    def test_completions_with_complex_content(self):
        message = {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Hello"},
                {"type": "text", "text": "World"},
            ],
        }
        choice = {"message": message}
        choices = [choice]
        result = self.context.completions(choices)
        result.set_attributes.assert_called_once()

    def test_completions_return_value_chaining(self):
        choices = [{"text": "Test"}]
        result = self.context.completions(choices)
        assert result is self.context
        chained_result = result.completions(choices)
        assert chained_result is self.context


class TestGenerationContextMessages:
    def setup_method(self):
        self.mock_span = Mock()
        self.mock_span.get_span_context.return_value.is_valid = True
        self.mock_span.set_attribute = Mock()
        self.mock_span.add_event = Mock()

        self.context = GenerationContext.__new__(GenerationContext)
        self.context._span = self.mock_span
        self.context.set_attributes = Mock(return_value=self.context)

    def test_messages_empty_list(self):
        result = self.context.messages([])
        result.set_attributes.assert_not_called()

    def test_messages_single_simple_message(self):
        message = {"role": "user", "content": "Hello, how are you?"}
        messages = [message]

        result = self.context.messages(messages)
        result.set_attributes.assert_called_once_with(
            **{
                "gen_ai.prompt.0.id": None,
                "gen_ai.prompt.0.role": "user",
                "gen_ai.prompt.0.content": "Hello, how are you?",
                "gen_ai.prompt.0.function_call.name": None,
                "gen_ai.prompt.0.function_call.arguments": None,
                "gen_ai.prompt.0.name": None,
            }
        )

    def test_messages_multiple_simple_messages(self):
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "Second message"},
            {"role": "user", "content": "Third message"},
        ]

        result = self.context.messages(messages)
        assert result.set_attributes.call_count == 3

    def test_messages_with_function_call(self):
        message = {
            "role": "assistant",
            "content": "I'll call a function",
            "function_call": {"name": "calculate_sum", "arguments": '{"a": 5, "b": 3}'},
        }

        messages = [message]
        result = self.context.messages(messages)
        result.set_attributes.assert_called_once_with(
            **{
                "gen_ai.prompt.0.id": None,
                "gen_ai.prompt.0.role": "assistant",
                "gen_ai.prompt.0.content": "I'll call a function",
                "gen_ai.prompt.0.function_call.name": "calculate_sum",
                "gen_ai.prompt.0.function_call.arguments": '{"a": 5, "b": 3}',
                "gen_ai.prompt.0.name": None,
            }
        )

    def test_messages_with_tool_calls(self):
        message = {
            "role": "assistant",
            "content": "I'll use tools",
            "tool_calls": [
                {
                    "id": "call_abc",
                    "type": "function",
                    "function": {
                        "name": "search_web",
                        "arguments": '{"query": "python"}',
                    },
                }
            ],
        }
        messages = [message]

        result = self.context.messages(messages)
        result.set_attributes.assert_called_once_with(
            **{
                "gen_ai.prompt.0.id": None,
                "gen_ai.prompt.0.tool_call.0.id": "call_abc",
                "gen_ai.prompt.0.tool_call.0.type": "function",
                "gen_ai.prompt.0.tool_call.0.function.name": "search_web",
                "gen_ai.prompt.0.tool_call.0.function.arguments": '{"query": "python"}',
                "gen_ai.prompt.0.role": "assistant",
                "gen_ai.prompt.0.content": "I'll use tools",
                "gen_ai.prompt.0.function_call.name": None,
                "gen_ai.prompt.0.function_call.arguments": None,
                "gen_ai.prompt.0.name": None,
            }
        )

    def test_messages_with_complex_content(self):
        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": "Hello"},
                {"type": "text", "text": "World"},
                {"text": "Extra text"},
            ],
        }
        messages = [message]

        result = self.context.messages(messages)
        call_args = result.set_attributes.call_args
        assert "Hello\nWorld\nExtra text" in call_args[1]["gen_ai.prompt.0.content"]

    def test_messages_with_none_message(self):
        messages = [
            {"role": "user", "content": "Valid message"},
            None,
            {"role": "assistant", "content": "Another valid message"},
        ]

        result = self.context.messages(messages)
        assert result.set_attributes.call_count == 2

    def test_messages_with_empty_message(self):
        message = {}
        messages = [message]

        result = self.context.messages(messages)
        result.set_attributes.assert_not_called()

    def test_messages_exception_handling(self):
        self.context.set_attributes.side_effect = Exception("Test error")

        messages = [{"role": "user", "content": "Test"}]
        result = self.context.messages(messages)
        assert result is self.context

    def test_messages_return_value_chaining(self):
        messages = [{"role": "user", "content": "Test"}]
        result = self.context.messages(messages)

        assert result is self.context
        chained_result = result.messages(messages)
        assert chained_result is self.context

    def test_messages_mixed_content_types(self):
        messages = [
            {"role": "user", "content": "Simple string"},
            {"role": "assistant", "content": ["Complex", "content"]},
            {"role": "system", "content": 123},
        ]

        result = self.context.messages(messages)
        assert result.set_attributes.call_count == 3

    def test_messages_with_multiple_tool_calls(self):
        message = {
            "role": "assistant",
            "content": "Multiple tools",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "tool1", "arguments": "{}"},
                },
                {
                    "id": "call_2",
                    "type": "function",
                    "function": {"name": "tool2", "arguments": "{}"},
                },
            ],
        }
        messages = [message]

        result = self.context.messages(messages)
        call_args = result.set_attributes.call_args[1]

        assert "gen_ai.prompt.0.tool_call.0.id" in call_args
        assert "gen_ai.prompt.0.tool_call.1.id" in call_args
        assert call_args["gen_ai.prompt.0.tool_call.0.function.name"] == "tool1"
        assert call_args["gen_ai.prompt.0.tool_call.1.function.name"] == "tool2"

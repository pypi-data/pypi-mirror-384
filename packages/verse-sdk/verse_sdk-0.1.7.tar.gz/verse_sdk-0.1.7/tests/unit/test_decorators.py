from unittest.mock import Mock, patch

import pytest

from verse_sdk.decorators import with_decorators


class TestDecorators:
    def setup_method(self):
        self.mock_sdk = Mock()
        self.mock_observation = Mock()
        self.mock_sdk.generation.return_value.__enter__ = Mock(
            return_value=self.mock_observation
        )
        self.mock_sdk.generation.return_value.__exit__ = Mock(return_value=None)
        self.mock_sdk.span.return_value.__enter__ = Mock(
            return_value=self.mock_observation
        )
        self.mock_sdk.span.return_value.__exit__ = Mock(return_value=None)
        self.mock_sdk.trace.return_value.__enter__ = Mock(
            return_value=self.mock_observation
        )
        self.mock_sdk.trace.return_value.__exit__ = Mock(return_value=None)

        self.sdk_with_decorators = with_decorators(self.mock_sdk)

    def test_with_decorators_adds_observe_methods(self):
        assert hasattr(self.sdk_with_decorators, "observe_generation")
        assert hasattr(self.sdk_with_decorators, "observe_span")
        assert hasattr(self.sdk_with_decorators, "observe_trace")

    def test_observe_generation_decorator(self):
        @self.sdk_with_decorators.observe_generation()
        def test_func():
            return "test_result"

        result = test_func()
        assert result == "test_result"
        self.mock_sdk.generation.assert_called_once_with("test_func")
        self.mock_observation.input.assert_called_once()
        self.mock_observation.output.assert_called_once()
        self.mock_observation.set_attributes.assert_called_once()

    def test_observe_span_decorator(self):
        @self.sdk_with_decorators.observe_span()
        def test_func():
            return "test_result"

        result = test_func()
        assert result == "test_result"
        self.mock_sdk.span.assert_called_once_with("test_func")
        self.mock_observation.input.assert_called_once()
        self.mock_observation.output.assert_called_once()
        self.mock_observation.set_attributes.assert_called_once()

    def test_observe_trace_decorator(self):
        @self.sdk_with_decorators.observe_trace()
        def test_func():
            return "test_result"

        result = test_func()
        assert result == "test_result"
        self.mock_sdk.trace.assert_called_once_with("test_func")
        self.mock_observation.input.assert_called_once()
        self.mock_observation.output.assert_called_once()
        self.mock_observation.set_attributes.assert_called_once()

    def test_decorator_with_custom_name(self):
        @self.sdk_with_decorators.observe_generation(name="custom_name")
        def test_func():
            return "test_result"

        result = test_func()
        assert result == "test_result"
        self.mock_sdk.generation.assert_called_once_with("custom_name")
        self.mock_observation.input.assert_called_once()
        self.mock_observation.output.assert_called_once()
        self.mock_observation.set_attributes.assert_called_once()

    def test_decorator_with_attrs(self):
        @self.sdk_with_decorators.observe_generation(custom_attr="value")
        def test_func():
            return "test_result"

        result = test_func()
        assert result == "test_result"
        self.mock_sdk.generation.assert_called_once_with(
            "test_func", custom_attr="value"
        )
        self.mock_observation.input.assert_called_once()
        self.mock_observation.output.assert_called_once()
        self.mock_observation.set_attributes.assert_called_once_with(
            custom_attr="value"
        )

    def test_decorator_capture_input_false(self):
        @self.sdk_with_decorators.observe_generation(capture_input=False)
        def test_func():
            return "test_result"

        result = test_func()
        assert result == "test_result"
        self.mock_sdk.generation.assert_called_once_with("test_func")
        self.mock_observation.input.assert_not_called()
        self.mock_observation.output.assert_called_once()
        self.mock_observation.set_attributes.assert_called_once()

    def test_decorator_capture_output_false(self):
        @self.sdk_with_decorators.observe_generation(capture_output=False)
        def test_func():
            return "test_result"

        result = test_func()
        assert result == "test_result"
        self.mock_sdk.generation.assert_called_once_with("test_func")
        self.mock_observation.input.assert_called_once()
        self.mock_observation.output.assert_not_called()
        self.mock_observation.set_attributes.assert_called_once()

    def test_decorator_capture_metadata_false(self):
        @self.sdk_with_decorators.observe_generation(capture_metadata=False)
        def test_func():
            return "test_result"

        result = test_func()
        assert result == "test_result"
        self.mock_sdk.generation.assert_called_once_with("test_func")
        self.mock_observation.input.assert_called_once()
        self.mock_observation.output.assert_called_once()
        self.mock_observation.metadata.assert_not_called()
        self.mock_observation.set_attributes.assert_called_once()

    def test_decorator_with_metadata_kwarg(self):
        @self.sdk_with_decorators.observe_generation()
        def test_func(metadata=None):
            return "test_result"

        result = test_func(metadata={"key": "value"})
        assert result == "test_result"
        self.mock_sdk.generation.assert_called_once_with("test_func")
        self.mock_observation.input.assert_called_once()
        self.mock_observation.output.assert_called_once()
        self.mock_observation.metadata.assert_called_once_with(
            metadata={"key": "value"}
        )
        self.mock_observation.set_attributes.assert_called_once()

    def test_decorator_preserves_function_metadata(self):
        @self.sdk_with_decorators.observe_generation()
        def test_func():
            """Test function docstring."""
            return "test_result"

        result = test_func()
        assert result == "test_result"
        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test function docstring."
        self.mock_sdk.generation.assert_called_once_with("test_func")
        self.mock_observation.input.assert_called_once()
        self.mock_observation.output.assert_called_once()
        self.mock_observation.set_attributes.assert_called_once()

    def test_decorator_handles_exception(self):
        @self.sdk_with_decorators.observe_generation()
        def test_func():
            raise ValueError("Test error")

        with patch("verse_sdk.decorators.logging"), pytest.raises(
            ValueError, match="Test error"
        ):
            test_func()

        self.mock_sdk.generation.assert_called_once_with("test_func")
        self.mock_observation.input.assert_called_once()
        self.mock_observation.error.assert_called_once()

    def test_decorator_handles_sdk_exception(self):
        self.mock_sdk.generation.side_effect = Exception("SDK error")

        @self.sdk_with_decorators.observe_generation()
        def test_func():
            return "test_result"

        with patch("verse_sdk.decorators.logging") as mock_logging:
            result = test_func()
            assert result == "test_result"
            mock_logging.warning.assert_called_once()

    def test_decorator_with_args_and_kwargs(self):
        @self.sdk_with_decorators.observe_generation()
        def test_func(arg1, arg2, kwarg1=None):
            return f"{arg1}_{arg2}_{kwarg1}"

        result = test_func("a", "b", kwarg1="c")
        assert result == "a_b_c"
        self.mock_sdk.generation.assert_called_once_with("test_func")
        self.mock_observation.input.assert_called_once()
        self.mock_observation.output.assert_called_once()
        self.mock_observation.set_attributes.assert_called_once()

    def test_decorator_returns_sdk_instance(self):
        result = with_decorators(self.mock_sdk)
        assert result is self.mock_sdk

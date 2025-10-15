from unittest.mock import Mock

import pytest

from verse_sdk.utils import (
    apply_value,
    create_basic_auth_token,
    merge,
    to_json,
)


class TestApplyValue:
    def test_apply_value_with_valid_value(self):
        mock_obj = Mock()
        apply_value(mock_obj, "set_name", "test_value")
        mock_obj.set_name.assert_called_once_with("test_value")

    def test_apply_value_with_none_value(self):
        mock_obj = Mock()
        apply_value(mock_obj, "set_name", None)
        mock_obj.set_name.assert_not_called()

    def test_apply_value_with_empty_string(self):
        mock_obj = Mock()
        apply_value(mock_obj, "set_name", "")
        mock_obj.set_name.assert_called_once_with("")

    def test_apply_value_with_zero(self):
        mock_obj = Mock()
        apply_value(mock_obj, "set_name", 0)
        mock_obj.set_name.assert_called_once_with(0)

    def test_apply_value_with_false(self):
        mock_obj = Mock()
        apply_value(mock_obj, "set_name", False)
        mock_obj.set_name.assert_called_once_with(False)

    def test_apply_value_with_list(self):
        mock_obj = Mock()
        test_list = [1, 2, 3]
        apply_value(mock_obj, "set_items", test_list)
        mock_obj.set_items.assert_called_once_with(test_list)

    def test_apply_value_with_dict(self):
        mock_obj = Mock()
        test_dict = {"key": "value"}
        apply_value(mock_obj, "set_config", test_dict)
        mock_obj.set_config.assert_called_once_with(test_dict)


class TestCreateBasicAuthToken:
    def test_create_basic_auth_token(self):
        result = create_basic_auth_token("user", "pass")
        assert result == "Basic dXNlcjpwYXNz"

    def test_create_basic_auth_token_with_special_chars(self):
        result = create_basic_auth_token("user@domain", "pass:word")
        assert result == "Basic dXNlckBkb21haW46cGFzczp3b3Jk"

    def test_create_basic_auth_token_with_empty_strings(self):
        result = create_basic_auth_token("", "")
        assert result == "Basic Og=="

    def test_create_basic_auth_token_with_unicode(self):
        result = create_basic_auth_token("测试", "密码")
        assert result == "Basic 5rWL6K+VOuWvhueggQ=="

    def test_create_basic_auth_token_with_numbers(self):
        result = create_basic_auth_token("123", "456")
        assert result == "Basic MTIzOjQ1Ng=="

    def test_create_basic_auth_token_with_spaces(self):
        result = create_basic_auth_token("user name", "pass word")
        assert result == "Basic dXNlciBuYW1lOnBhc3Mgd29yZA=="


class TestMerge:
    def test_merge_both_none(self):
        result = merge(None, None)
        assert result == {}

    def test_merge_a_none_b_empty(self):
        result = merge(None, {})
        assert result == {}

    def test_merge_a_none_b_with_data(self):
        b = {"key1": "value1", "key2": "value2"}
        result = merge(None, b)
        assert result == {"key1": "value1", "key2": "value2"}
        assert result is not b

    def test_merge_a_empty_b_none(self):
        result = merge({}, None)
        assert result == {}

    def test_merge_a_with_data_b_none(self):
        a = {"key1": "value1", "key2": "value2"}
        result = merge(a, None)
        assert result == {"key1": "value1", "key2": "value2"}
        assert result is not a

    def test_merge_both_with_data(self):
        a = {"key1": "value1", "key2": "value2"}
        b = {"key2": "new_value2", "key3": "value3"}
        result = merge(a, b)
        assert result == {"key1": "value1", "key2": "new_value2", "key3": "value3"}

    def test_merge_b_overrides_a(self):
        a = {"key1": "value1", "key2": "value2"}
        b = {"key2": "override", "key3": "value3"}
        result = merge(a, b)
        assert result["key2"] == "override"

    def test_merge_with_nested_dicts(self):
        a = {"config": {"host": "localhost", "port": 8080}}
        b = {"config": {"port": 9090, "ssl": True}}
        result = merge(a, b)
        assert result == {"config": {"port": 9090, "ssl": True}}

    def test_merge_with_different_types(self):
        a = {"string": "value", "number": 42, "boolean": True}
        b = {"string": "new_value", "list": [1, 2, 3]}
        result = merge(a, b)
        assert result == {
            "string": "new_value",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
        }

    def test_merge_preserves_original_dicts(self):
        a = {"key1": "value1"}
        b = {"key2": "value2"}
        original_a = a.copy()
        original_b = b.copy()

        result = merge(a, b)

        assert a == original_a
        assert b == original_b
        assert result == {"key1": "value1", "key2": "value2"}


class TestToJson:
    def test_to_json_with_simple_dict(self):
        data = {"key": "value", "number": 42}
        result = to_json(data)
        assert result == '{"key": "value", "number": 42}'

    def test_to_json_with_nested_dict(self):
        data = {"config": {"host": "localhost", "port": 8080}}
        result = to_json(data)
        assert result == '{"config": {"host": "localhost", "port": 8080}}'

    def test_to_json_with_list(self):
        data = {"items": [1, 2, 3], "name": "test"}
        result = to_json(data)
        assert result == '{"items": [1, 2, 3], "name": "test"}'

    def test_to_json_with_boolean(self):
        data = {"enabled": True, "disabled": False}
        result = to_json(data)
        assert result == '{"enabled": true, "disabled": false}'

    def test_to_json_with_none_values(self):
        data = {"key1": "value", "key2": None}
        result = to_json(data)
        assert result == '{"key1": "value", "key2": null}'

    def test_to_json_with_empty_dict(self):
        data = {}
        result = to_json(data)
        assert result == "{}"

    def test_to_json_with_unicode(self):
        data = {"message": "Hello 世界", "emoji": "🚀"}
        result = to_json(data)
        assert (
            result == '{"message": "Hello \\u4e16\\u754c", "emoji": "\\ud83d\\ude80"}'
        )

    def test_to_json_with_non_serializable_object(self):
        class NonSerializable:
            def __repr__(self):
                return "NonSerializable()"

        data = {"obj": NonSerializable()}
        result = to_json(data)
        assert result == "{'obj': NonSerializable()}"

    def test_to_json_with_circular_reference(self):
        data = {"key": "value"}
        data["self"] = data
        result = to_json(data)
        assert "key" in result
        assert "value" in result
        assert "..." in result

    def test_to_json_with_custom_object(self):
        class CustomObject:
            def __init__(self, value):
                self.value = value

            def __repr__(self):
                return f"CustomObject({self.value})"

        data = {"custom": CustomObject("test")}
        result = to_json(data)
        assert result == "{'custom': CustomObject(test)}"

    def test_to_json_with_exception_during_serialization(self):
        class FailingObject:
            def __repr__(self):
                raise Exception("Repr failed")

        data = {"failing": FailingObject()}
        with pytest.raises(Exception, match="Repr failed"):
            to_json(data)

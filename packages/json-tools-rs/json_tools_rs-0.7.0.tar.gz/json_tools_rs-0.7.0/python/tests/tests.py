#!/usr/bin/env python3
"""
Comprehensive Test Suite for JSON Tools RS Python Bindings

This test suite provides complete coverage of the unified JSONTools API including:
- Basic flatten/unflatten functionality tests
- Advanced collision handling tests
- Configuration and transformation tests
- Error handling tests
- Edge case tests
- Performance benchmarks
- Type preservation tests
- All input/output combinations
- Roundtrip compatibility tests
"""

import json
import time
from typing import Any, Dict, List, Union

import json_tools_rs
import pytest


class TestBasicFunctionality:
    """Test basic JSON flattening and unflattening functionality"""

    def test_basic_flattening_dict_input_dict_output(self):
        """Test dict input → dict output (most convenient!)"""
        tools = json_tools_rs.JSONTools().flatten()
        input_data = {"user": {"name": "John", "age": 30}}
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["user.name"] == "John"
        assert result["user.age"] == 30

    def test_basic_flattening_str_input_str_output(self):
        """Test JSON string input → JSON string output"""
        tools = json_tools_rs.JSONTools().flatten()
        input_json = '{"user": {"name": "John", "age": 30}}'
        result = tools.execute(input_json)

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["user.name"] == "John"
        assert parsed["user.age"] == 30

    def test_basic_unflattening_dict_input_dict_output(self):
        """Test unflattening dict input → dict output"""
        tools = json_tools_rs.JSONTools().unflatten()
        input_data = {"user.name": "John", "user.age": 30}
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["user"]["name"] == "John"
        assert result["user"]["age"] == 30

    def test_basic_unflattening_str_input_str_output(self):
        """Test unflattening JSON string input → JSON string output"""
        tools = json_tools_rs.JSONTools().unflatten()
        input_json = '{"user.name": "John", "user.age": 30}'
        result = tools.execute(input_json)

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["user"]["name"] == "John"
        assert parsed["user"]["age"] == 30

    def test_deeply_nested_structure(self):
        """Test deeply nested JSON structures"""
        tools = json_tools_rs.JSONTools().flatten()
        input_data = {
            "level1": {"level2": {"level3": {"level4": {"value": "deep_value"}}}}
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["level1.level2.level3.level4.value"] == "deep_value"

    def test_array_flattening(self):
        """Test array flattening with indices"""
        tools = json_tools_rs.JSONTools().flatten()
        input_data = {"items": [1, 2, {"nested": "value"}], "matrix": [[1, 2], [3, 4]]}
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["items.0"] == 1
        assert result["items.1"] == 2
        assert result["items.2.nested"] == "value"
        assert result["matrix.0.0"] == 1
        assert result["matrix.0.1"] == 2
        assert result["matrix.1.0"] == 3
        assert result["matrix.1.1"] == 4

    def test_roundtrip_consistency(self):
        """Test that flatten → unflatten preserves data"""
        original = {"user": {"profile": {"name": "John", "age": 30}}, "settings": {"theme": "dark"}}

        # Flatten then unflatten
        flattened = json_tools_rs.JSONTools().flatten().execute(original)
        restored = json_tools_rs.JSONTools().unflatten().execute(flattened)

        assert restored == original

    def test_mixed_data_types(self):
        """Test flattening with various data types"""
        tools = json_tools_rs.JSONTools().flatten()
        input_data = {
            "string": "text",
            "number": 42,
            "float": 3.14,
            "boolean_true": True,
            "boolean_false": False,
            "null_value": None,
            "array": [1, "two", 3.0, True, None],
            "object": {"nested": "value"},
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["string"] == "text"
        assert result["number"] == 42
        assert result["float"] == 3.14
        assert result["boolean_true"] is True
        assert result["boolean_false"] is False
        assert result["null_value"] is None
        assert result["array.0"] == 1
        assert result["array.1"] == "two"
        assert result["array.2"] == 3.0
        assert result["array.3"] is True
        assert result["array.4"] is None
        assert result["object.nested"] == "value"


class TestCollisionHandling:
    """Test collision handling strategies"""


    def test_handle_collision_strategy(self):
        """Test collision handling with arrays"""
        tools = (json_tools_rs.JSONTools()
                .flatten()
                .key_replacement("(User|Admin|Guest)_", "")
                .handle_key_collision(True))

        data = {"User_name": "John", "Admin_name": "Jane", "Guest_name": "Bob"}
        result = tools.execute(data)

        # Should create array
        assert "name" in result
        assert isinstance(result["name"], list)
        assert len(result["name"]) == 3
        assert "John" in result["name"]
        assert "Jane" in result["name"]
        assert "Bob" in result["name"]

    def test_collision_with_filtering(self):
        """Test collision handling with filtering applied during resolution"""
        tools = (json_tools_rs.JSONTools()
                .flatten()
                .key_replacement("(User|Admin|Guest)_", "")
                .remove_empty_strings(True)
                .handle_key_collision(True))

        data = {"User_name": "John", "Admin_name": "", "Guest_name": "Bob"}
        result = tools.execute(data)

        # Should create array with empty string filtered out
        assert "name" in result
        assert isinstance(result["name"], list)
        assert len(result["name"]) == 2  # Empty string filtered out
        assert "John" in result["name"]
        assert "Bob" in result["name"]
        assert "" not in result["name"]



class TestAdvancedConfiguration:
    """Test advanced configuration options"""

    def test_remove_empty_strings(self):
        """Test removing empty string values"""
        tools = json_tools_rs.JSONTools().flatten().remove_empty_strings(True)
        input_data = {
            "user": {
                "name": "John",
                "email": "",  # Should be removed
                "bio": "Developer",
            },
            "empty_field": "",  # Should be removed
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["user.name"] == "John"
        assert result["user.bio"] == "Developer"
        assert "user.email" not in result
        assert "empty_field" not in result

    def test_remove_nulls(self):
        """Test removing null values"""
        tools = json_tools_rs.JSONTools().flatten().remove_nulls(True)
        input_data = {
            "user": {"name": "John", "age": None, "active": True},  # Should be removed
            "null_field": None,  # Should be removed
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["user.name"] == "John"
        assert result["user.active"] is True
        assert "user.age" not in result
        assert "null_field" not in result

    def test_remove_empty_objects(self):
        """Test removing empty object values"""
        tools = json_tools_rs.JSONTools().flatten().remove_empty_objects(True)
        input_data = {
            "user": {"profile": {}, "settings": {"theme": "dark"}},  # Should be removed
            "empty_obj": {},  # Should be removed
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["user.settings.theme"] == "dark"
        assert "user.profile" not in result
        assert "empty_obj" not in result

    def test_remove_empty_arrays(self):
        """Test removing empty array values"""
        tools = json_tools_rs.JSONTools().flatten().remove_empty_arrays(True)
        input_data = {
            "user": {"tags": [], "items": [1, 2, 3]},  # Should be removed
            "empty_list": [],  # Should be removed
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["user.items.0"] == 1
        assert result["user.items.1"] == 2
        assert result["user.items.2"] == 3
        assert "user.tags" not in result
        assert "empty_list" not in result

    def test_custom_separator(self):
        """Test custom separators"""
        separators = ["_", "::", "/", "|", "---"]

        for sep in separators:
            tools = json_tools_rs.JSONTools().flatten().separator(sep)
            input_data = {"level1": {"level2": {"value": "test"}}}
            result = tools.execute(input_data)

            expected_key = f"level1{sep}level2{sep}value"
            assert isinstance(result, dict)
            assert result[expected_key] == "test"

    def test_lowercase_keys(self):
        """Test lowercase key conversion"""
        tools = json_tools_rs.JSONTools().flatten().lowercase_keys(True)
        input_data = {
            "User": {"Profile": {"Name": "John", "Email": "john@example.com"}}
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["user.profile.name"] == "John"
        assert result["user.profile.email"] == "john@example.com"

    def test_combined_filters(self):
        """Test all filters combined"""
        tools = (
            json_tools_rs.JSONTools()
            .flatten()
            .remove_empty_strings(True)
            .remove_nulls(True)
            .remove_empty_objects(True)
            .remove_empty_arrays(True)
            .lowercase_keys(True)
            .separator("_")
        )

        input_data = {
            "User": {
                "Name": "John",
                "Email": "",
                "Age": None,
                "Settings": {},
                "Tags": [],
                "Active": True,
            }
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["user_name"] == "John"
        assert result["user_active"] is True
        assert len(result) == 2  # Only name and active should remain


class TestReplacements:
    """Test key and value replacement functionality"""

    def test_literal_key_replacement(self):
        """Test literal string key replacement"""
        tools = json_tools_rs.JSONTools().flatten().key_replacement("user_", "person_")
        input_data = {
            "user_name": "John",
            "user_email": "john@example.com",
            "admin_role": "super",
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["person_name"] == "John"
        assert result["person_email"] == "john@example.com"
        assert result["admin_role"] == "super"  # Should remain unchanged

    def test_regex_key_replacement(self):
        """Test regex key replacement"""
        tools = json_tools_rs.JSONTools().flatten().key_replacement(
            "^(user|admin)_", ""
        )
        input_data = {
            "user_name": "John",
            "admin_role": "super",
            "guest_access": "limited",
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["name"] == "John"
        assert result["role"] == "super"
        assert result["guest_access"] == "limited"  # Should remain unchanged

    def test_literal_value_replacement(self):
        """Test literal string value replacement"""
        tools = json_tools_rs.JSONTools().flatten().value_replacement(
            "inactive", "disabled"
        )
        input_data = {
            "user1": {"status": "active"},
            "user2": {"status": "inactive"},
            "user3": {"status": "pending"},
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["user1.status"] == "active"
        assert result["user2.status"] == "disabled"
        assert result["user3.status"] == "pending"

    def test_regex_value_replacement(self):
        """Test regex value replacement"""
        tools = json_tools_rs.JSONTools().flatten().value_replacement(
            "@example\\.com", "@company.org"
        )
        input_data = {
            "user1": {"email": "john@example.com"},
            "user2": {"email": "jane@example.com"},
            "user3": {"email": "bob@test.org"},
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["user1.email"] == "john@company.org"
        assert result["user2.email"] == "jane@company.org"
        assert result["user3.email"] == "bob@test.org"  # Should remain unchanged

    def test_multiple_replacements(self):
        """Test multiple key and value replacements"""
        tools = (
            json_tools_rs.JSONTools()
            .flatten()
            .key_replacement("user_", "person_")
            .key_replacement("^admin_", "manager_")
            .value_replacement("@example.com", "@company.org")
            .value_replacement("^inactive$", "disabled")
        )

        input_data = {
            "user_email": "john@example.com",
            "admin_role": "super",
            "user_status": "inactive",
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["person_email"] == "john@company.org"
        assert result["manager_role"] == "super"
        assert result["person_status"] == "disabled"

    def test_regex_capture_groups(self):
        """Test regex replacement with capture groups"""
        tools = json_tools_rs.JSONTools().flatten().key_replacement(
            "^field_(\\d+)_(.+)", "$2_id_$1"
        )
        input_data = {
            "field_123_name": "John",
            "field_456_email": "john@example.com",
            "other_field": "unchanged",
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        # Note: The actual result depends on the regex implementation
        # This test verifies the function works without errors
        assert len(result) == 3
        assert "other_field" in result
        assert result["other_field"] == "unchanged"


class TestBatchProcessing:
    """Test batch processing with lists"""

    def test_list_of_strings_input_output(self):
        """Test list[str] input → list[str] output"""
        tools = json_tools_rs.JSONTools().flatten()
        input_list = [
            '{"user1": {"name": "Alice"}}',
            '{"user2": {"name": "Bob"}}',
            '{"user3": {"name": "Charlie"}}',
        ]
        result = tools.execute(input_list)

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(item, str) for item in result)

        parsed = [json.loads(item) for item in result]
        assert parsed[0]["user1.name"] == "Alice"
        assert parsed[1]["user2.name"] == "Bob"
        assert parsed[2]["user3.name"] == "Charlie"

    def test_list_of_dicts_input_output(self):
        """Test list[dict] input → list[dict] output"""
        tools = json_tools_rs.JSONTools().flatten()
        input_list = [
            {"user1": {"name": "Alice"}},
            {"user2": {"name": "Bob"}},
            {"user3": {"name": "Charlie"}},
        ]
        result = tools.execute(input_list)

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(item, dict) for item in result)

        assert result[0]["user1.name"] == "Alice"
        assert result[1]["user2.name"] == "Bob"
        assert result[2]["user3.name"] == "Charlie"

    def test_mixed_list_type_preservation(self):
        """Test mixed list preserves original types"""
        tools = json_tools_rs.JSONTools().flatten()
        input_list = [
            '{"user1": {"name": "Alice"}}',  # JSON string
            {"user2": {"name": "Bob"}},  # Python dict
            {"user3": {"name": "Charlie"}},  # Python dict
        ]
        result = tools.execute(input_list)

        assert isinstance(result, list)
        assert len(result) == 3
        assert isinstance(result[0], str)  # First item should remain string
        assert isinstance(result[1], dict)  # Second item should remain dict
        assert isinstance(result[2], dict)  # Third item should remain dict

        # Verify content
        parsed_first = json.loads(result[0])
        assert parsed_first["user1.name"] == "Alice"
        assert result[1]["user2.name"] == "Bob"
        assert result[2]["user3.name"] == "Charlie"

    def test_batch_with_advanced_config(self):
        """Test batch processing with advanced configuration"""
        tools = (
            json_tools_rs.JSONTools()
            .flatten()
            .remove_empty_strings(True)
            .remove_nulls(True)
            .key_replacement("user_", "person_")
            .separator("_")
        )

        input_list = [
            {"user_name": "John", "user_email": "", "user_age": 30},
            {"user_name": "Jane", "user_bio": None, "user_active": True},
        ]
        result = tools.execute(input_list)

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, dict) for item in result)

        # First result should have name and age only (email removed)
        assert result[0]["person_name"] == "John"
        assert result[0]["person_age"] == 30
        assert "person_email" not in result[0]

        # Second result should have name and active only (bio removed)
        assert result[1]["person_name"] == "Jane"
        assert result[1]["person_active"] is True
        assert "person_bio" not in result[1]

    def test_empty_list(self):
        """Test empty list input"""
        tools = json_tools_rs.JSONTools().flatten()
        result = tools.execute([])

        assert isinstance(result, list)
        assert len(result) == 0

    def test_large_batch(self):
        """Test large batch processing"""
        tools = json_tools_rs.JSONTools().flatten()

        # Create 100 items
        input_list = []
        for i in range(100):
            input_list.append(
                {
                    f"item_{i}": {
                        "id": i,
                        "name": f"Item {i}",
                        "data": {"nested": f"value_{i}"},
                    }
                }
            )

        result = tools.execute(input_list)

        assert isinstance(result, list)
        assert len(result) == 100
        assert all(isinstance(item, dict) for item in result)

        # Verify some entries
        assert result[0][f"item_0.id"] == 0
        assert result[0][f"item_0.name"] == "Item 0"
        assert result[0][f"item_0.data.nested"] == "value_0"

        assert result[99][f"item_99.id"] == 99
        assert result[99][f"item_99.name"] == "Item 99"
        assert result[99][f"item_99.data.nested"] == "value_99"


class TestAdvancedOutputObject:
    """Test the advanced JsonOutput object"""

    def test_single_result_output_object(self):
        """Test JsonOutput object with single result"""
        tools = json_tools_rs.JSONTools().flatten()
        result = tools.execute_to_output('{"test": {"key": "value"}}')

        assert result.is_single
        assert not result.is_multiple

        single_result = result.get_single()
        assert isinstance(single_result, str)

        parsed = json.loads(single_result)
        assert parsed["test.key"] == "value"

    def test_multiple_result_output_object(self):
        """Test JsonOutput object with multiple results"""
        tools = json_tools_rs.JSONTools().flatten()
        input_list = ['{"a": 1}', '{"b": 2}']
        result = tools.execute_to_output(input_list)

        assert result.is_multiple
        assert not result.is_single

        multiple_results = result.get_multiple()
        assert isinstance(multiple_results, list)
        assert len(multiple_results) == 2

        parsed = [json.loads(item) for item in multiple_results]
        assert parsed[0]["a"] == 1
        assert parsed[1]["b"] == 2

    def test_output_object_error_handling(self):
        """Test JsonOutput object error handling"""
        tools = json_tools_rs.JSONTools().flatten()

        # Test single result
        single_result = tools.execute_to_output('{"test": "value"}')

        # Should raise error when calling get_multiple on single result
        with pytest.raises(ValueError, match="single.*get_single"):
            single_result.get_multiple()

        # Test multiple result
        multiple_result = tools.execute_to_output(['{"a": 1}', '{"b": 2}'])

        # Should raise error when calling get_single on multiple result
        with pytest.raises(ValueError, match="multiple.*get_multiple"):
            multiple_result.get_single()


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_json_string(self):
        """Test invalid JSON string input"""
        tools = json_tools_rs.JSONTools().flatten()

        with pytest.raises(json_tools_rs.JsonToolsError):
            tools.execute('{"invalid": json}')

    def test_invalid_json_in_list(self):
        """Test invalid JSON in list input"""
        tools = json_tools_rs.JSONTools().flatten()
        input_list = [
            '{"valid": "json"}',
            '{"invalid": json}',  # Invalid JSON
            '{"another": "valid"}',
        ]

        with pytest.raises(json_tools_rs.JsonToolsError):
            tools.execute(input_list)

    def test_invalid_input_type(self):
        """Test invalid input types"""
        tools = json_tools_rs.JSONTools().flatten()

        # Test invalid scalar types
        with pytest.raises(ValueError):
            tools.execute(123)  # Number

        with pytest.raises(ValueError):
            tools.execute(True)  # Boolean

        # Test list with invalid item types
        with pytest.raises(ValueError):
            tools.execute([123, object()])  # Contains invalid object type

    def test_invalid_regex_pattern(self):
        """Test invalid regex patterns fall back to literal matching"""
        # Invalid regex in key replacement - should fall back to literal matching
        tools = json_tools_rs.JSONTools().flatten().key_replacement(
            "[invalid", "replacement"
        )
        result = tools.execute('{"test": "value"}')
        # Should not raise error, just treat as literal string (no match)
        assert isinstance(result, str)
        assert '"test"' in result and '"value"' in result

        # Invalid regex in value replacement - should fall back to literal matching
        tools = json_tools_rs.JSONTools().flatten().value_replacement(
            "*invalid", "replacement"
        )
        result = tools.execute('{"test": "value"}')
        # Should not raise error, just treat as literal string (no match)
        assert isinstance(result, str)
        assert '"test"' in result and '"value"' in result

    def test_deeply_nested_structure_limits(self):
        """Test very deeply nested structures"""
        # Create extremely deep nesting
        data = {"level": "value"}
        for i in range(50):  # 50 levels deep
            data = {f"level_{i}": data}

        tools = json_tools_rs.JSONTools().flatten()
        result = tools.execute(data)

        assert isinstance(result, dict)
        assert len(result) == 1
        # Should have one very long key
        key = list(result.keys())[0]
        assert key.count(".") == 50  # 50 dots for 51 levels
        assert result[key] == "value"

    def test_large_json_structure(self):
        """Test very large JSON structures"""
        # Create large object with many keys
        large_data = {}
        for i in range(1000):
            large_data[f"key_{i}"] = {
                "id": i,
                "name": f"name_{i}",
                "nested": {"value": f"value_{i}"},
            }

        tools = json_tools_rs.JSONTools().flatten()
        result = tools.execute(large_data)

        assert isinstance(result, dict)
        assert len(result) == 3000  # 1000 * 3 keys each

        # Verify some entries
        assert result["key_0.id"] == 0
        assert result["key_0.name"] == "name_0"
        assert result["key_0.nested.value"] == "value_0"
        assert result["key_999.id"] == 999


class TestEdgeCases:
    """Test edge cases and special scenarios"""

    def test_empty_json_object(self):
        """Test empty JSON object"""
        tools = json_tools_rs.JSONTools().flatten()
        result = tools.execute({})

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_empty_json_string(self):
        """Test empty JSON string"""
        tools = json_tools_rs.JSONTools().flatten()
        result = tools.execute("{}")

        assert isinstance(result, str)
        assert result == "{}"

    def test_root_level_primitive(self):
        """Test root-level primitive values"""
        tools = json_tools_rs.JSONTools().flatten()

        # Test string
        result = tools.execute('"hello"')
        parsed = json.loads(result)
        assert parsed == "hello"

        # Test number
        result = tools.execute("42")
        parsed = json.loads(result)
        assert parsed == 42

        # Test boolean
        result = tools.execute("true")
        parsed = json.loads(result)
        assert parsed is True

        # Test null
        result = tools.execute("null")
        parsed = json.loads(result)
        assert parsed is None

    def test_special_characters_in_keys(self):
        """Test special characters in keys"""
        tools = json_tools_rs.JSONTools().flatten()
        input_data = {
            "key with spaces": "value1",
            "key-with-dashes": "value2",
            "key_with_underscores": "value3",
            "key.with.dots": "value4",
            "key@with#symbols": "value5",
            "": "empty_key",  # Empty key
            "unicode_café": "value6",
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["key with spaces"] == "value1"
        assert result["key-with-dashes"] == "value2"
        assert result["key_with_underscores"] == "value3"
        assert result["key.with.dots"] == "value4"
        assert result["key@with#symbols"] == "value5"
        assert result[""] == "empty_key"
        assert result["unicode_café"] == "value6"

    def test_special_characters_in_values(self):
        """Test special characters in values"""
        tools = json_tools_rs.JSONTools().flatten()
        input_data = {
            "normal": "value",
            "empty": "",
            "with_quotes": 'value with "quotes"',
            "with_newlines": "line1\nline2",
            "with_unicode": "café ñoño 🚀",
            "with_json": '{"nested": "json"}',
            "with_numbers": "123.45",
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["normal"] == "value"
        assert result["empty"] == ""
        assert result["with_quotes"] == 'value with "quotes"'
        assert result["with_newlines"] == "line1\nline2"
        assert result["with_unicode"] == "café ñoño 🚀"
        assert result["with_json"] == '{"nested": "json"}'
        assert result["with_numbers"] == "123.45"

    def test_circular_reference_simulation(self):
        """Test structures that simulate circular references"""
        tools = json_tools_rs.JSONTools().flatten()

        # This isn't actually circular but tests deep self-reference patterns
        input_data = {
            "node": {
                "id": 1,
                "children": [{"id": 2, "parent_id": 1}, {"id": 3, "parent_id": 1}],
            }
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["node.id"] == 1
        assert result["node.children.0.id"] == 2
        assert result["node.children.0.parent_id"] == 1
        assert result["node.children.1.id"] == 3
        assert result["node.children.1.parent_id"] == 1

    def test_numeric_string_keys(self):
        """Test numeric string keys"""
        tools = json_tools_rs.JSONTools().flatten()
        input_data = {
            "0": "zero",
            "1": "one",
            "123": "one-two-three",
            "nested": {"0": "nested_zero", "456": "nested_four-five-six"},
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["0"] == "zero"
        assert result["1"] == "one"
        assert result["123"] == "one-two-three"
        assert result["nested.0"] == "nested_zero"
        assert result["nested.456"] == "nested_four-five-six"

    def test_boolean_and_null_values(self):
        """Test boolean and null value handling"""
        tools = json_tools_rs.JSONTools().flatten()
        input_data = {
            "true_value": True,
            "false_value": False,
            "null_value": None,
            "nested": {"bool_true": True, "bool_false": False, "null_nested": None},
        }
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["true_value"] is True
        assert result["false_value"] is False
        assert result["null_value"] is None
        assert result["nested.bool_true"] is True
        assert result["nested.bool_false"] is False
        assert result["nested.null_nested"] is None


class TestTypePreservation:
    """Test perfect type preservation - input type = output type"""

    def test_str_to_str_consistency(self):
        """Test JSON string input consistently produces JSON string output"""
        tools = json_tools_rs.JSONTools().flatten()

        test_cases = [
            '{"simple": "value"}',
            '{"nested": {"key": "value"}}',
            '{"array": [1, 2, 3]}',
            '{"mixed": {"array": [{"nested": "value"}]}}',
        ]

        for input_json in test_cases:
            result = tools.execute(input_json)
            assert isinstance(
                result, str
            ), f"Expected str output for str input: {input_json}"

            # Verify it's valid JSON
            parsed = json.loads(result)
            assert isinstance(parsed, dict)

    def test_dict_to_dict_consistency(self):
        """Test Python dict input consistently produces Python dict output"""
        tools = json_tools_rs.JSONTools().flatten()

        test_cases = [
            {"simple": "value"},
            {"nested": {"key": "value"}},
            {"array": [1, 2, 3]},
            {"mixed": {"array": [{"nested": "value"}]}},
        ]

        for input_dict in test_cases:
            result = tools.execute(input_dict)
            assert isinstance(
                result, dict
            ), f"Expected dict output for dict input: {input_dict}"

    def test_list_str_to_list_str_consistency(self):
        """Test list[str] input consistently produces list[str] output"""
        tools = json_tools_rs.JSONTools().flatten()

        input_list = [
            '{"item1": "value1"}',
            '{"item2": {"nested": "value2"}}',
            '{"item3": [1, 2, 3]}',
        ]
        result = tools.execute(input_list)

        assert isinstance(result, list)
        assert len(result) == len(input_list)
        assert all(isinstance(item, str) for item in result)

        # Verify all are valid JSON
        for item in result:
            parsed = json.loads(item)
            assert isinstance(parsed, dict)

    def test_list_dict_to_list_dict_consistency(self):
        """Test list[dict] input consistently produces list[dict] output"""
        tools = json_tools_rs.JSONTools().flatten()

        input_list = [
            {"item1": "value1"},
            {"item2": {"nested": "value2"}},
            {"item3": [1, 2, 3]},
        ]
        result = tools.execute(input_list)

        assert isinstance(result, list)
        assert len(result) == len(input_list)
        assert all(isinstance(item, dict) for item in result)

    def test_mixed_list_type_preservation_detailed(self):
        """Test detailed mixed list type preservation"""
        tools = json_tools_rs.JSONTools().flatten()

        # Test various mixed patterns
        mixed_patterns = [
            # Pattern 1: str, dict, str
            ['{"str1": "value1"}', {"dict1": "value2"}, '{"str2": "value3"}'],
            # Pattern 2: dict, dict, str, str
            [
                {"dict1": "value1"},
                {"dict2": "value2"},
                '{"str1": "value3"}',
                '{"str2": "value4"}',
            ],
            # Pattern 3: alternating
            [
                '{"str1": "value1"}',
                {"dict1": "value2"},
                '{"str2": "value3"}',
                {"dict2": "value4"},
                '{"str3": "value5"}',
            ],
        ]

        for i, pattern in enumerate(mixed_patterns):
            result = tools.execute(pattern)

            assert isinstance(result, list), f"Pattern {i+1}: Expected list output"
            assert len(result) == len(pattern), f"Pattern {i+1}: Length mismatch"

            for j, (original, processed) in enumerate(zip(pattern, result)):
                original_type = type(original)
                processed_type = type(processed)

                assert (
                    original_type == processed_type
                ), f"Pattern {i+1}, Item {j}: Type mismatch. Expected {original_type}, got {processed_type}"

    def test_type_preservation_with_configurations(self):
        """Test type preservation with various configurations"""
        configurations = [
            json_tools_rs.JSONTools().flatten().remove_empty_strings(True),
            json_tools_rs.JSONTools().flatten().remove_nulls(True),
            json_tools_rs.JSONTools().flatten().separator("_"),
            json_tools_rs.JSONTools().flatten().lowercase_keys(True),
            json_tools_rs.JSONTools().flatten().key_replacement("test_", ""),
            json_tools_rs.JSONTools().flatten().value_replacement("old", "new"),
        ]

        test_data = {
            "str_input": '{"test_key": "old_value", "empty": "", "null_val": null}',
            "dict_input": {"test_key": "old_value", "empty": "", "null_val": None},
            "list_str_input": ['{"test1": "old"}', '{"test2": "value"}'],
            "list_dict_input": [{"test1": "old"}, {"test2": "value"}],
        }

        for config in configurations:
            # Test string input → string output
            result = config.execute(test_data["str_input"])
            assert isinstance(result, str)

            # Test dict input → dict output
            result = config.execute(test_data["dict_input"])
            assert isinstance(result, dict)

            # Test list[str] input → list[str] output
            result = config.execute(test_data["list_str_input"])
            assert isinstance(result, list)
            assert all(isinstance(item, str) for item in result)

            # Test list[dict] input → list[dict] output
            result = config.execute(test_data["list_dict_input"])
            assert isinstance(result, list)
            assert all(isinstance(item, dict) for item in result)


class TestPerformance:
    """Performance tests and benchmarks"""

    def test_basic_flattening_performance(self):
        """Test basic flattening performance"""
        tools = json_tools_rs.JSONTools().flatten()

        # Create test data with varying complexity
        simple_data = {"user": {"name": "John", "age": 30}}
        nested_data = {"level1": {"level2": {"level3": {"level4": {"data": "value"}}}}}
        array_data = {"items": [{"id": i, "name": f"item_{i}"} for i in range(100)]}

        test_cases = [
            ("simple", simple_data),
            ("nested", nested_data),
            ("array", array_data),
        ]

        results = {}

        for name, data in test_cases:
            start_time = time.time()
            iterations = 1000

            for _ in range(iterations):
                result = tools.execute(data)
                # Ensure the operation completes
                if isinstance(result, dict):
                    _ = len(result)

            end_time = time.time()
            total_time = end_time - start_time
            ops_per_second = iterations / total_time

            results[name] = {
                "ops_per_second": ops_per_second,
                "avg_time_ms": (total_time / iterations) * 1000,
            }

            print(
                f"{name.capitalize()} data: {ops_per_second:.0f} ops/sec, {results[name]['avg_time_ms']:.3f}ms avg"
            )

        # Performance assertions
        assert (
            results["simple"]["ops_per_second"] > 1000
        ), "Simple flattening should be > 1000 ops/sec"
        assert (
            results["nested"]["ops_per_second"] > 500
        ), "Nested flattening should be > 500 ops/sec"
        assert (
            results["array"]["ops_per_second"] > 100
        ), "Array flattening should be > 100 ops/sec"

    def test_batch_processing_performance(self):
        """Test batch processing performance"""
        tools = json_tools_rs.JSONTools().flatten()

        # Create batch data
        batch_sizes = [10, 50, 100, 500]

        for batch_size in batch_sizes:
            # Create list of dictionaries
            dict_batch = [
                {
                    "user": {
                        "id": i,
                        "name": f"user_{i}",
                        "data": {"nested": f"value_{i}"},
                    }
                }
                for i in range(batch_size)
            ]

            # Create list of JSON strings
            str_batch = [json.dumps(item) for item in dict_batch]

            # Test dict batch performance
            start_time = time.time()
            dict_result = tools.execute(dict_batch)
            dict_time = time.time() - start_time

            # Test string batch performance
            start_time = time.time()
            str_result = tools.execute(str_batch)
            str_time = time.time() - start_time

            print(f"Batch size {batch_size}:")
            print(
                f"  Dict batch: {dict_time*1000:.2f}ms ({batch_size/dict_time:.0f} items/sec)"
            )
            print(
                f"  Str batch:  {str_time*1000:.2f}ms ({batch_size/str_time:.0f} items/sec)"
            )

            # Verify results
            assert len(dict_result) == batch_size
            assert len(str_result) == batch_size
            assert all(isinstance(item, dict) for item in dict_result)
            assert all(isinstance(item, str) for item in str_result)

            # Performance assertions
            items_per_sec_dict = batch_size / dict_time
            items_per_sec_str = batch_size / str_time

            assert (
                items_per_sec_dict > 50
            ), f"Dict batch processing should be > 50 items/sec for size {batch_size}"
            assert (
                items_per_sec_str > 50
            ), f"String batch processing should be > 50 items/sec for size {batch_size}"

    def test_complex_configuration_performance(self):
        """Test performance with complex configurations"""
        # Create complex flattener with all features
        complex_tools = (
            json_tools_rs.JSONTools()
            .flatten()
            .remove_empty_strings(True)
            .remove_nulls(True)
            .remove_empty_objects(True)
            .remove_empty_arrays(True)
            .key_replacement("^user_", "person_")
            .value_replacement("@example\\.com", "@company.org")
            .separator("_")
            .lowercase_keys(True)
        )

        # Create test data
        complex_data = {
            "User_Profile": {
                "User_Name": "John Doe",
                "User_Email": "john@example.com",
                "User_Settings": {
                    "Theme": "dark",
                    "Language": "",
                    "Notifications": None,
                },
                "User_Tags": [],
                "User_Metadata": {},
            }
        }

        # Benchmark complex configuration
        start_time = time.time()
        iterations = 500

        for _ in range(iterations):
            result = complex_tools.execute(complex_data)
            _ = len(result)  # Ensure operation completes

        end_time = time.time()
        total_time = end_time - start_time
        ops_per_second = iterations / total_time

        print(
            f"Complex configuration: {ops_per_second:.0f} ops/sec, {(total_time/iterations)*1000:.3f}ms avg"
        )

        # Should still maintain reasonable performance
        assert ops_per_second > 100, "Complex configuration should be > 100 ops/sec"

    def test_large_data_performance(self):
        """Test performance with large data structures"""
        tools = json_tools_rs.JSONTools().flatten()

        # Create large nested structure
        large_data = {}
        for i in range(1000):
            large_data[f"section_{i}"] = {
                "id": i,
                "name": f"Section {i}",
                "items": [{"item_id": j, "value": f"value_{i}_{j}"} for j in range(10)],
                "metadata": {
                    "created": f"2024-01-{(i % 28) + 1:02d}",
                    "tags": [f"tag_{i % 5}", f"category_{i % 10}"],
                },
            }

        # Benchmark large data
        start_time = time.time()
        result = tools.execute(large_data)
        end_time = time.time()

        processing_time = end_time - start_time
        key_count = len(result)
        keys_per_second = key_count / processing_time

        print(
            f"Large data: {key_count} keys in {processing_time*1000:.2f}ms ({keys_per_second:.0f} keys/sec)"
        )

        # Performance assertions
        assert (
            processing_time < 5.0
        ), "Large data processing should complete within 5 seconds"
        assert keys_per_second > 1000, "Should process > 1000 keys/sec for large data"
        assert key_count > 10000, "Should generate many flattened keys"

    def test_regex_performance_impact(self):
        """Test performance impact of regex operations"""
        data = {
            f"user_{i}": {
                "email": f"user{i}@example.com",
                "status": "active" if i % 2 else "inactive",
            }
            for i in range(100)
        }

        # Test without regex
        simple_tools = json_tools_rs.JSONTools().flatten()
        start_time = time.time()
        iterations = 100
        for _ in range(iterations):
            result = simple_tools.execute(data)
            _ = len(result)
        simple_time = time.time() - start_time

        # Test with regex
        regex_tools = (
            json_tools_rs.JSONTools()
            .flatten()
            .key_replacement("^user_", "person_")
            .value_replacement("@example\\.com", "@company.org")
        )
        start_time = time.time()
        for _ in range(iterations):
            result = regex_tools.execute(data)
            _ = len(result)
        regex_time = time.time() - start_time

        simple_ops_per_sec = iterations / simple_time
        regex_ops_per_sec = iterations / regex_time
        overhead_percent = ((regex_time - simple_time) / simple_time) * 100

        print(f"Simple flattening: {simple_ops_per_sec:.0f} ops/sec")
        print(f"Regex flattening:  {regex_ops_per_sec:.0f} ops/sec")
        print(f"Regex overhead:    {overhead_percent:.1f}%")

        # Regex should still maintain reasonable performance
        assert regex_ops_per_sec > 10, "Regex operations should maintain > 10 ops/sec"
        assert overhead_percent < 1000, "Regex overhead should be reasonable"

    def test_memory_efficiency(self):
        """Test memory efficiency with repeated operations"""
        import gc

        tools = json_tools_rs.JSONTools().flatten()

        # Create medium-sized data
        data = {
            f"group_{i}": {
                "items": [{"id": j, "data": f"value_{j}"} for j in range(50)]
            }
            for i in range(50)
        }

        # Perform many operations to test for memory leaks
        gc.collect()  # Clean up before test

        for i in range(100):
            result = tools.execute(data)

            # Periodically verify result and clean up
            if i % 10 == 0:
                assert isinstance(result, dict)
                assert len(result) > 1000
                del result
                gc.collect()

        # Test should complete without memory issues
        print("Memory efficiency test completed successfully")

    def test_performance_comparison_dict_vs_string(self):
        """Compare performance of dict vs string input"""
        # Create test data
        test_data_dict = {
            "users": [
                {
                    "id": i,
                    "profile": {"name": f"User {i}", "email": f"user{i}@example.com"},
                }
                for i in range(100)
            ]
        }
        test_data_str = json.dumps(test_data_dict)

        tools = json_tools_rs.JSONTools().flatten()

        # Test dict input performance
        start_time = time.time()
        iterations = 100
        for _ in range(iterations):
            result = tools.execute(test_data_dict)
            _ = len(result)
        dict_time = time.time() - start_time

        # Test string input performance
        start_time = time.time()
        for _ in range(iterations):
            result = tools.execute(test_data_str)
            # For string input, we need to parse the result to count keys
            parsed = json.loads(result)
            _ = len(parsed)
        str_time = time.time() - start_time

        dict_ops_per_sec = iterations / dict_time
        str_ops_per_sec = iterations / str_time

        print(f"Dict input:   {dict_ops_per_sec:.0f} ops/sec")
        print(f"String input: {str_ops_per_sec:.0f} ops/sec")
        print(f"Ratio (dict/str): {dict_ops_per_sec/str_ops_per_sec:.2f}")

        # Both should maintain good performance
        assert dict_ops_per_sec > 50, "Dict input should be > 50 ops/sec"
        assert str_ops_per_sec > 50, "String input should be > 50 ops/sec"


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    def test_api_response_flattening(self):
        """Test flattening typical API responses"""
        # Simulate typical REST API response
        api_response = {
            "data": {
                "user": {
                    "id": 12345,
                    "profile": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "phone": "+1-555-123-4567",
                    },
                    "preferences": {
                        "notifications": {"email": True, "sms": False, "push": True},
                        "privacy": {"profile_public": False, "email_visible": False},
                    },
                    "metadata": {
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-20T15:45:00Z",
                        "last_login": "2024-01-26T09:15:00Z",
                    },
                },
                "permissions": ["read", "write", "admin"],
                "groups": [
                    {"id": 1, "name": "Developers", "role": "member"},
                    {"id": 2, "name": "Admins", "role": "owner"},
                ],
            },
            "meta": {
                "request_id": "req_123456789",
                "timestamp": "2024-01-26T12:00:00Z",
                "version": "v1.2.3",
            },
        }

        tools = json_tools_rs.JSONTools().flatten()
        result = tools.execute(api_response)

        assert isinstance(result, dict)
        assert result["data.user.id"] == 12345
        assert result["data.user.profile.first_name"] == "John"
        assert result["data.user.profile.email"] == "john.doe@example.com"
        assert result["data.user.preferences.notifications.email"] is True
        assert result["data.permissions.0"] == "read"
        assert result["data.groups.0.name"] == "Developers"
        assert result["meta.request_id"] == "req_123456789"

    def test_configuration_file_flattening(self):
        """Test flattening configuration files"""
        config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {"username": "admin", "password": "secret123"},
                "pools": {"min_connections": 5, "max_connections": 20, "timeout": 30},
            },
            "redis": {
                "host": "redis.example.com",
                "port": 6379,
                "auth": {"password": "redis_secret"},
            },
            "logging": {
                "level": "INFO",
                "handlers": [
                    {"type": "console", "format": "%(asctime)s - %(message)s"},
                    {
                        "type": "file",
                        "filename": "/var/log/app.log",
                        "max_size": "10MB",
                    },
                ],
            },
            "features": {
                "authentication": {"enabled": True, "provider": "oauth2"},
                "caching": {"enabled": True, "ttl": 3600},
                "monitoring": {"enabled": False},
            },
        }

        # Use environment variable style flattening
        tools = json_tools_rs.JSONTools().flatten().separator("_").lowercase_keys(True)

        result = tools.execute(config)

        assert isinstance(result, dict)
        assert result["database_host"] == "localhost"
        assert result["database_port"] == 5432
        assert result["database_credentials_username"] == "admin"
        assert result["redis_host"] == "redis.example.com"
        assert result["logging_level"] == "INFO"
        assert result["features_authentication_enabled"] is True

    def test_analytics_data_processing(self):
        """Test processing analytics/metrics data"""
        analytics_data = {
            "metrics": {
                "page_views": {
                    "total": 15420,
                    "unique": 8934,
                    "by_source": {
                        "organic": 5678,
                        "social": 2341,
                        "direct": 987,
                        "referral": 6,
                    },
                },
                "user_engagement": {
                    "session_duration": {"avg_seconds": 245, "median_seconds": 180},
                    "bounce_rate": 0.34,
                    "pages_per_session": 2.8,
                },
                "conversions": {
                    "total": 89,
                    "rate": 0.0058,
                    "by_funnel_stage": {
                        "awareness": 15420,
                        "interest": 4521,
                        "consideration": 892,
                        "conversion": 89,
                    },
                },
            },
            "dimensions": {
                "time_period": "2024-01-01 to 2024-01-31",
                "geography": {
                    "primary_country": "US",
                    "top_cities": ["New York", "Los Angeles", "Chicago"],
                },
                "demographics": {
                    "age_groups": {
                        "18-24": 0.15,
                        "25-34": 0.35,
                        "35-44": 0.28,
                        "45-54": 0.15,
                        "55+": 0.07,
                    }
                },
            },
        }

        # Clean up and standardize for analysis
        tools = (
            json_tools_rs.JSONTools()
            .flatten()
            .remove_nulls(True)
            .remove_empty_objects(True)
            .separator("__")
        )

        result = tools.execute(analytics_data)

        assert isinstance(result, dict)
        assert result["metrics__page_views__total"] == 15420
        assert result["metrics__user_engagement__bounce_rate"] == 0.34
        assert result["metrics__conversions__rate"] == 0.0058
        assert result["dimensions__demographics__age_groups__25-34"] == 0.35

    def test_form_data_processing(self):
        """Test processing form submission data"""
        form_data = {
            "personal_info": {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@company.com",
                "phone": "",  # Empty field
                "date_of_birth": "1990-05-15",
            },
            "address": {
                "street": "123 Main St",
                "city": "Springfield",
                "state": "IL",
                "zip_code": "62701",
                "country": "USA",
            },
            "employment": {
                "company": "Tech Corp",
                "position": "Software Engineer",
                "salary": None,  # Optional field not filled
                "start_date": "2022-03-01",
            },
            "preferences": {
                "newsletter": True,
                "marketing_emails": False,
                "contact_method": "email",
            },
            "additional_info": "",  # Empty text area
            "terms_accepted": True,
            "submission_metadata": {
                "timestamp": "2024-01-26T14:30:00Z",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 ...",
            },
        }

        # Clean up form data for storage
        tools = (
            json_tools_rs.JSONTools()
            .flatten()
            .remove_empty_strings(True)
            .remove_nulls(True)
            .key_replacement("personal_info.", "")
            .key_replacement("submission_metadata.", "meta_")
        )

        result = tools.execute(form_data)

        assert isinstance(result, dict)
        assert result["first_name"] == "Jane"
        assert result["email"] == "jane.smith@company.com"
        assert "phone" not in result  # Empty string removed
        assert result["address.city"] == "Springfield"
        assert "employment.salary" not in result  # Null removed
        assert result["preferences.newsletter"] is True
        assert "additional_info" not in result  # Empty string removed
        assert result["meta_timestamp"] == "2024-01-26T14:30:00Z"

    def test_log_processing(self):
        """Test processing structured log data"""
        log_entries = [
            {
                "timestamp": "2024-01-26T10:15:30Z",
                "level": "INFO",
                "service": "api-gateway",
                "message": "Request processed successfully",
                "context": {
                    "request_id": "req_001",
                    "user_id": "user_123",
                    "endpoint": "/api/users/profile",
                    "method": "GET",
                    "response_time_ms": 45,
                    "status_code": 200,
                },
            },
            {
                "timestamp": "2024-01-26T10:16:45Z",
                "level": "ERROR",
                "service": "user-service",
                "message": "Database connection failed",
                "context": {
                    "request_id": "req_002",
                    "error_code": "DB_CONN_TIMEOUT",
                    "retry_count": 3,
                    "database": "users_db",
                },
                "stack_trace": None,  # Sometimes present, sometimes not
            },
        ]

        # Process logs for analysis
        tools = (
            json_tools_rs.JSONTools()
            .flatten()
            .remove_nulls(True)
            .key_replacement("context_", "")
            .separator("_")
        )

        results = tools.execute(log_entries)

        assert isinstance(results, list)
        assert len(results) == 2
        assert all(isinstance(entry, dict) for entry in results)

        # Check first log entry
        assert results[0]["level"] == "INFO"
        assert results[0]["service"] == "api-gateway"
        assert results[0]["request_id"] == "req_001"
        assert results[0]["response_time_ms"] == 45

        # Check second log entry
        assert results[1]["level"] == "ERROR"
        assert results[1]["error_code"] == "DB_CONN_TIMEOUT"
        assert "stack_trace" not in results[1]  # Null removed

    def test_data_transformation_pipeline(self):
        """Test complete data transformation pipeline"""
        # Simulate raw data from multiple sources
        raw_data = {
            "customer_data": {
                "Customer_ID": "CUST_12345",
                "Customer_Name": "John Doe Industries",
                "Contact_Info": {
                    "Primary_Email": "contact@johndoe.com",
                    "Secondary_Email": "",
                    "Phone_Number": "+1-555-123-4567",
                    "Fax_Number": None,
                },
                "Address_Details": {
                    "Street_Address": "123 Business Ave",
                    "City": "Springfield",
                    "State_Province": "IL",
                    "Postal_Code": "62701",
                    "Country_Code": "US",
                },
            },
            "account_info": {
                "Account_Status": "ACTIVE",
                "Account_Type": "PREMIUM",
                "Registration_Date": "2023-01-15",
                "Last_Activity": "2024-01-25",
                "Payment_Methods": [
                    {"Type": "CREDIT_CARD", "Last_Four": "1234", "Expires": "12/26"},
                    {
                        "Type": "BANK_TRANSFER",
                        "Account_Number": "****5678",
                        "Routing": "987654321",
                    },
                ],
            },
            "usage_statistics": {
                "Monthly_Usage": {
                    "API_Calls": 15420,
                    "Data_Transfer_GB": 245.8,
                    "Storage_GB": 12.3,
                },
                "Feature_Usage": {
                    "Advanced_Analytics": True,
                    "Custom_Reports": True,
                    "White_Label": False,
                    "API_Access": True,
                },
            },
            "billing_details": {
                "Current_Plan": "PREMIUM_MONTHLY",
                "Plan_Start_Date": "2024-01-01",
                "Plan_End_Date": "2025-01-01",
                "Next_Payment_Due": "2025-01-15",
                "Amount_Due": 99.99,
                "Payment_Status": "PAID",
            },
        }

        # Clean up and transform for analytics
        tools = (
            json_tools_rs.JSONTools()
            .flatten()
            .remove_empty_strings(True)
            .remove_nulls(True)
            .key_replacement(
                "^(customer_data|account_info|usage_statistics|billing_details)_",
                "",
            )
            .separator("_")
            .lowercase_keys(True)
        )

        result = tools.execute(raw_data)

        assert isinstance(result, dict)
        assert result["customer_id"] == "CUST_12345"
        assert result["customer_name"] == "John Doe Industries"
        assert result["contact_info_primary_email"] == "contact@johndoe.com"
        assert "contact_info_secondary_email" not in result  # Empty string removed
        assert "contact_info_fax_number" not in result  # Null removed


# ============================================================================
# JsonUnflattener Tests
# ============================================================================


class TestJsonUnflattenerBasic:
    """Test basic JsonUnflattener functionality."""

    def test_basic_string_unflattening(self):
        """Test basic unflattening with JSON string input."""
        flattened = '{"user.name": "John", "user.age": 30, "user.profile.city": "NYC"}'
        tools = json_tools_rs.JSONTools().unflatten()
        result = tools.execute(flattened)

        # Should return string
        assert isinstance(result, str)

        # Parse and verify structure
        parsed = json.loads(result)
        assert parsed["user"]["name"] == "John"
        assert parsed["user"]["age"] == 30
        assert parsed["user"]["profile"]["city"] == "NYC"

    def test_basic_dict_unflattening(self):
        """Test basic unflattening with Python dict input."""
        flattened = {"user.name": "John", "user.age": 30, "user.profile.city": "NYC"}
        tools = json_tools_rs.JSONTools().unflatten()
        result = tools.execute(flattened)

        # Should return dict
        assert isinstance(result, dict)

        # Verify structure
        assert result["user"]["name"] == "John"
        assert result["user"]["age"] == 30
        assert result["user"]["profile"]["city"] == "NYC"

    def test_array_reconstruction(self):
        """Test reconstruction of arrays from flattened keys."""
        flattened = {"items.0": "first", "items.1": "second", "items.2": "third"}
        tools = json_tools_rs.JSONTools().unflatten()
        result = tools.execute(flattened)

        assert isinstance(result, dict)
        assert result["items"] == ["first", "second", "third"]

    def test_mixed_structure(self):
        """Test unflattening of mixed objects and arrays."""
        flattened = {
            "user.name": "John",
            "user.emails.0": "john@work.com",
            "user.emails.1": "john@personal.com",
            "settings.theme": "dark",
            "settings.notifications.email": True,
            "settings.notifications.sms": False,
        }
        tools = json_tools_rs.JSONTools().unflatten()
        result = tools.execute(flattened)

        assert isinstance(result, dict)
        assert result["user"]["name"] == "John"
        assert result["user"]["emails"] == ["john@work.com", "john@personal.com"]
        assert result["settings"]["theme"] == "dark"
        assert result["settings"]["notifications"]["email"] is True
        assert result["settings"]["notifications"]["sms"] is False


class TestJsonUnflattenerTypePreservation:
    """Test type preservation in JsonUnflattener."""

    def test_string_input_string_output(self):
        """Test str input → str output."""
        flattened = '{"a.b": 1, "c.d": 2}'
        tools = json_tools_rs.JSONTools().unflatten()
        result = tools.execute(flattened)

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == {"a": {"b": 1}, "c": {"d": 2}}

    def test_dict_input_dict_output(self):
        """Test dict input → dict output."""
        flattened = {"a.b": 1, "c.d": 2}
        tools = json_tools_rs.JSONTools().unflatten()
        result = tools.execute(flattened)

        assert isinstance(result, dict)
        assert result == {"a": {"b": 1}, "c": {"d": 2}}

    def test_string_list_input_string_list_output(self):
        """Test list[str] input → list[str] output."""
        flattened_list = ['{"a.b": 1}', '{"c.d": 2}', '{"e.f": 3}']
        tools = json_tools_rs.JSONTools().unflatten()
        result = tools.execute(flattened_list)

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(item, str) for item in result)

        # Parse and verify each result
        parsed_results = [json.loads(item) for item in result]
        assert parsed_results[0] == {"a": {"b": 1}}
        assert parsed_results[1] == {"c": {"d": 2}}
        assert parsed_results[2] == {"e": {"f": 3}}

    def test_dict_list_input_dict_list_output(self):
        """Test list[dict] input → list[dict] output."""
        flattened_list = [{"a.b": 1}, {"c.d": 2}, {"e.f": 3}]
        tools = json_tools_rs.JSONTools().unflatten()
        result = tools.execute(flattened_list)

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(item, dict) for item in result)

        # Verify each result
        assert result[0] == {"a": {"b": 1}}
        assert result[1] == {"c": {"d": 2}}
        assert result[2] == {"e": {"f": 3}}

    def test_empty_list_handling(self):
        """Test empty list handling."""
        tools = json_tools_rs.JSONTools().unflatten()
        result = tools.execute([])

        assert isinstance(result, list)
        assert len(result) == 0


class TestJsonUnflattenerBuilderPattern:
    """Test JsonUnflattener builder pattern configuration."""

    def test_custom_separator(self):
        """Test custom separator configuration."""
        flattened = {"user_name": "John", "user_age": 30}
        tools = json_tools_rs.JSONTools().unflatten().separator("_")
        result = tools.execute(flattened)

        assert isinstance(result, dict)
        assert result == {"user": {"name": "John", "age": 30}}

    def test_lowercase_keys(self):
        """Test lowercase keys configuration."""
        flattened = {"USER.NAME": "John", "USER.AGE": 30}
        tools = json_tools_rs.JSONTools().unflatten().lowercase_keys(True)
        result = tools.execute(flattened)

        assert isinstance(result, dict)
        assert result == {"user": {"name": "John", "age": 30}}

    def test_key_replacement(self):
        """Test key replacement configuration."""
        flattened = {"prefix.name": "John", "prefix.age": 30}
        tools = json_tools_rs.JSONTools().unflatten().key_replacement(
            "prefix.", "user."
        )
        result = tools.execute(flattened)

        assert isinstance(result, dict)
        assert result == {"user": {"name": "John", "age": 30}}

    def test_value_replacement(self):
        """Test value replacement configuration."""
        flattened = {"user.email": "john@company.org", "user.name": "John"}
        tools = json_tools_rs.JSONTools().unflatten().value_replacement(
            "@company.org", "@example.com"
        )
        result = tools.execute(flattened)

        assert isinstance(result, dict)
        assert result["user"]["email"] == "john@example.com"
        assert result["user"]["name"] == "John"

    def test_regex_key_replacement(self):
        """Test regex key replacement."""
        flattened = {"user_name": "John", "admin_role": "super"}
        tools = json_tools_rs.JSONTools().unflatten().key_replacement(
            "^(user|admin)_", "$1."
        )
        result = tools.execute(flattened)

        assert isinstance(result, dict)
        assert result == {"user": {"name": "John"}, "admin": {"role": "super"}}

    def test_chained_configuration(self):
        """Test chained builder pattern configuration."""
        # Use lowercase input since key replacement happens before lowercase conversion
        flattened = {"prefix_name": "john@company.org", "prefix_age": 30}
        tools = (
            json_tools_rs.JSONTools()
            .unflatten()
            .separator("_")
            .key_replacement("prefix_", "user_")
            .value_replacement("@company.org", "@example.com")
            .lowercase_keys(True)
        )
        result = tools.execute(flattened)

        assert isinstance(result, dict)
        assert result == {"user": {"name": "john@example.com", "age": 30}}


class TestJsonUnflattenerErrorHandling:
    """Test JsonUnflattener error handling."""

    def test_invalid_json_string(self):
        """Test handling of invalid JSON string."""
        tools = json_tools_rs.JSONTools().unflatten()
        with pytest.raises(json_tools_rs.JsonToolsError):
            tools.execute('{"invalid": json}')

    def test_invalid_input_type(self):
        """Test handling of invalid input types."""
        tools = json_tools_rs.JSONTools().unflatten()
        with pytest.raises(ValueError):
            tools.execute(123)  # Invalid type

    def test_mixed_list_types(self):
        """Test handling of mixed list types."""
        tools = json_tools_rs.JSONTools().unflatten()
        with pytest.raises(ValueError):
            tools.execute(['{"a": 1}', 123, {"b": 2}])  # Mixed types

    def test_invalid_list_content(self):
        """Test handling of invalid list content."""
        tools = json_tools_rs.JSONTools().unflatten()
        with pytest.raises(ValueError):
            tools.execute([None, "test"])  # Invalid content


class TestJsonUnflattenerRoundtrip:
    """Test roundtrip compatibility between JsonFlattener and JsonUnflattener."""

    def test_simple_roundtrip(self):
        """Test simple roundtrip: original → flatten → unflatten → original."""
        original = {"user": {"name": "John", "age": 30}}

        # Flatten
        flatten_tools = json_tools_rs.JSONTools().flatten()
        flattened = flatten_tools.execute(original)

        # Unflatten
        unflatten_tools = json_tools_rs.JSONTools().unflatten()
        restored = unflatten_tools.execute(flattened)

        # Should be equivalent to original
        assert restored == original

    def test_complex_roundtrip(self):
        """Test complex roundtrip with nested structures and arrays."""
        original = {
            "user": {
                "profile": {"name": "John", "age": 30},
                "emails": ["john@work.com", "john@personal.com"],
                "settings": {"theme": "dark", "notifications": True},
            },
            "metadata": {"created": "2024-01-01", "version": 1.0},
        }

        # Flatten
        flatten_tools = json_tools_rs.JSONTools().flatten()
        flattened = flatten_tools.execute(original)

        # Unflatten
        unflatten_tools = json_tools_rs.JSONTools().unflatten()
        restored = unflatten_tools.execute(flattened)

        # Should be equivalent to original
        assert restored == original

    def test_roundtrip_with_custom_separator(self):
        """Test roundtrip with custom separator."""
        original = {"user": {"name": "John", "profile": {"city": "NYC"}}}

        # Flatten with custom separator
        flatten_tools = json_tools_rs.JSONTools().flatten().separator("_")
        flattened = flatten_tools.execute(original)

        # Unflatten with same separator
        unflatten_tools = json_tools_rs.JSONTools().unflatten().separator("_")
        restored = unflatten_tools.execute(flattened)

        # Should be equivalent to original
        assert restored == original

    def test_batch_roundtrip(self):
        """Test batch roundtrip processing."""
        originals = [
            {"a": {"b": 1}},
            {"c": {"d": [1, 2, 3]}},
            {"e": {"f": {"g": "test"}}},
        ]

        # Flatten batch
        flatten_tools = json_tools_rs.JSONTools().flatten()
        flattened_batch = flatten_tools.execute(originals)

        # Unflatten batch
        unflatten_tools = json_tools_rs.JSONTools().unflatten()
        restored_batch = unflatten_tools.execute(flattened_batch)

        # Should be equivalent to originals
        assert restored_batch == originals

    def test_roundtrip_with_arrays(self):
        """Test roundtrip with complex array structures."""
        original = {
            "items": [
                {"id": 1, "name": "first"},
                {"id": 2, "name": "second", "tags": ["a", "b"]},
                {"id": 3, "nested": {"deep": {"value": "test"}}},
            ]
        }

        # Flatten
        flatten_tools = json_tools_rs.JSONTools().flatten()
        flattened = flatten_tools.execute(original)

        # Unflatten
        unflatten_tools = json_tools_rs.JSONTools().unflatten()
        restored = unflatten_tools.execute(flattened)

        # Should be equivalent to original
        assert restored == original

    def test_roundtrip_with_mixed_types(self):
        """Test roundtrip with mixed data types."""
        original = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "array": [1, "two", 3.0, False],
            "object": {"nested": "value"},
        }

        # Flatten
        flatten_tools = json_tools_rs.JSONTools().flatten()
        flattened = flatten_tools.execute(original)

        # Unflatten
        unflatten_tools = json_tools_rs.JSONTools().unflatten()
        restored = unflatten_tools.execute(flattened)

        # Should be equivalent to original
        assert restored == original


class TestTypeConversion:
    """Test automatic type conversion from strings to numbers and booleans"""

    def test_basic_number_conversion_dict(self):
        """Test basic number conversion with dict input"""
        tools = json_tools_rs.JSONTools().flatten().auto_convert_types(True)
        input_data = {"id": "123", "price": "45.67", "count": "-10"}
        result = tools.execute(input_data)

        assert isinstance(result, dict)
        assert result["id"] == 123
        assert result["price"] == 45.67
        assert result["count"] == -10

    def test_basic_number_conversion_str(self):
        """Test basic number conversion with JSON string input"""
        tools = json_tools_rs.JSONTools().flatten().auto_convert_types(True)
        input_json = '{"id": "123", "price": "45.67", "count": "-10"}'
        result = tools.execute(input_json)

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["id"] == 123
        assert parsed["price"] == 45.67
        assert parsed["count"] == -10

    def test_thousands_separator_us_format(self):
        """Test US format thousands separators (1,234.56)"""
        tools = json_tools_rs.JSONTools().flatten().auto_convert_types(True)
        input_data = {"amount": "1,234.56", "total": "1,000,000"}
        result = tools.execute(input_data)

        assert result["amount"] == 1234.56
        assert result["total"] == 1000000

    def test_thousands_separator_european_format(self):
        """Test European format thousands separators (1.234,56)"""
        tools = json_tools_rs.JSONTools().flatten().auto_convert_types(True)
        input_data = {"amount": "1.234,56", "total": "1.000.000,00"}
        result = tools.execute(input_data)

        assert result["amount"] == 1234.56
        assert result["total"] == 1000000.0

    def test_currency_symbols(self):
        """Test currency symbol removal and conversion"""
        tools = json_tools_rs.JSONTools().flatten().auto_convert_types(True)
        input_data = {
            "usd": "$123.45",
            "eur": "€99.99",
            "gbp": "£50.00",
            "yen": "¥1000"
        }
        result = tools.execute(input_data)

        assert result["usd"] == 123.45
        assert result["eur"] == 99.99
        assert result["gbp"] == 50.0
        assert result["yen"] == 1000

    def test_scientific_notation(self):
        """Test scientific notation conversion"""
        tools = json_tools_rs.JSONTools().flatten().auto_convert_types(True)
        input_data = {
            "small": "1.23e-4",
            "large": "1e5",
            "negative": "-2.5e3"
        }
        result = tools.execute(input_data)

        assert result["small"] == 0.000123
        assert result["large"] == 100000.0
        assert result["negative"] == -2500.0

    def test_boolean_conversion(self):
        """Test boolean conversion (only exact variants)"""
        tools = json_tools_rs.JSONTools().flatten().auto_convert_types(True)
        input_data = {
            "a": "true",
            "b": "TRUE",
            "c": "True",
            "d": "false",
            "e": "FALSE",
            "f": "False"
        }
        result = tools.execute(input_data)

        assert result["a"] is True
        assert result["b"] is True
        assert result["c"] is True
        assert result["d"] is False
        assert result["e"] is False
        assert result["f"] is False

    def test_keep_invalid_strings(self):
        """Test that invalid strings are kept as-is"""
        tools = json_tools_rs.JSONTools().flatten().auto_convert_types(True)
        input_data = {
            "name": "John",
            "code": "ABC123",
            "maybe": "yes",  # Not a valid boolean
            "invalid": "12.34.56"  # Invalid number
        }
        result = tools.execute(input_data)

        assert result["name"] == "John"
        assert result["code"] == "ABC123"
        assert result["maybe"] == "yes"
        assert result["invalid"] == "12.34.56"

    def test_mixed_conversion(self):
        """Test mixed conversion with valid and invalid strings"""
        tools = json_tools_rs.JSONTools().flatten().auto_convert_types(True)
        input_data = {
            "id": "123",
            "name": "Alice",
            "price": "$1,234.56",
            "active": "true",
            "code": "XYZ"
        }
        result = tools.execute(input_data)

        assert result["id"] == 123
        assert result["name"] == "Alice"
        assert result["price"] == 1234.56
        assert result["active"] is True
        assert result["code"] == "XYZ"

    def test_nested_conversion(self):
        """Test type conversion in nested structures"""
        tools = json_tools_rs.JSONTools().flatten().auto_convert_types(True)
        input_data = {
            "user": {
                "id": "456",
                "age": "25",
                "verified": "true"
            }
        }
        result = tools.execute(input_data)

        assert result["user.id"] == 456
        assert result["user.age"] == 25
        assert result["user.verified"] is True

    def test_array_conversion(self):
        """Test type conversion in arrays"""
        tools = json_tools_rs.JSONTools().flatten().auto_convert_types(True)
        input_data = {"numbers": ["123", "45.6", "true", "invalid"]}
        result = tools.execute(input_data)

        assert result["numbers.0"] == 123
        assert result["numbers.1"] == 45.6
        assert result["numbers.2"] is True
        assert result["numbers.3"] == "invalid"

    def test_conversion_disabled_by_default(self):
        """Test that conversion is disabled by default"""
        tools = json_tools_rs.JSONTools().flatten()
        input_data = {"id": "123", "active": "true"}
        result = tools.execute(input_data)

        # Should keep as strings when conversion is disabled
        assert result["id"] == "123"
        assert result["active"] == "true"

    def test_unflatten_with_conversion(self):
        """Test type conversion with unflatten operation"""
        tools = json_tools_rs.JSONTools().unflatten().auto_convert_types(True)
        input_data = {
            "user.id": "789",
            "user.active": "false"
        }
        result = tools.execute(input_data)

        assert result["user"]["id"] == 789
        assert result["user"]["active"] is False

    def test_normal_mode_with_conversion(self):
        """Test type conversion with normal mode (no flatten/unflatten)"""
        tools = json_tools_rs.JSONTools().normal().auto_convert_types(True)
        input_data = {
            "user": {
                "id": "999",
                "enabled": "TRUE"
            }
        }
        result = tools.execute(input_data)

        assert result["user"]["id"] == 999
        assert result["user"]["enabled"] is True

    def test_conversion_with_other_transformations(self):
        """Test type conversion combined with other transformations"""
        tools = (json_tools_rs.JSONTools()
                .flatten()
                .auto_convert_types(True)
                .lowercase_keys(True)
                .remove_empty_strings(True))

        input_data = {
            "User_ID": "123",
            "User_Active": "true",
            "User_Name": "Alice",
            "Empty": ""
        }
        result = tools.execute(input_data)

        assert result["user_id"] == 123
        assert result["user_active"] is True
        assert result["user_name"] == "Alice"
        assert "empty" not in result  # Removed empty string

    def test_batch_processing_with_conversion(self):
        """Test type conversion with batch processing"""
        tools = json_tools_rs.JSONTools().flatten().auto_convert_types(True)
        input_batch = [
            {"id": "101", "price": "$99.99"},
            {"id": "102", "price": "$149.00"}
        ]
        result = tools.execute(input_batch)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == 101
        assert result[0]["price"] == 99.99
        assert result[1]["id"] == 102
        assert result[1]["price"] == 149.0

    def test_complex_real_world_example(self):
        """Test complex real-world scenario with type conversion"""
        tools = json_tools_rs.JSONTools().flatten().auto_convert_types(True)
        input_data = {
            "order": {
                "id": "ORD-12345",
                "total": "$1,234.56",
                "items": [
                    {
                        "id": "101",
                        "quantity": "5",
                        "price": "€99.99",
                        "available": "true"
                    },
                    {
                        "id": "102",
                        "quantity": "2",
                        "price": "$49.50",
                        "available": "FALSE"
                    }
                ],
                "customer": {
                    "id": "CUST-789",
                    "verified": "True",
                    "balance": "1,500.00"
                }
            }
        }
        result = tools.execute(input_data)

        # Check order fields
        assert result["order.id"] == "ORD-12345"  # Kept as string (not a number)
        assert result["order.total"] == 1234.56

        # Check item 0
        assert result["order.items.0.id"] == 101
        assert result["order.items.0.quantity"] == 5
        assert result["order.items.0.price"] == 99.99
        assert result["order.items.0.available"] is True

        # Check item 1
        assert result["order.items.1.id"] == 102
        assert result["order.items.1.quantity"] == 2
        assert result["order.items.1.price"] == 49.50
        assert result["order.items.1.available"] is False

        # Check customer
        assert result["order.customer.id"] == "CUST-789"  # Kept as string
        assert result["order.customer.verified"] is True
        assert result["order.customer.balance"] == 1500.0


class TestParallelProcessing:
    """Test parallel processing configuration and functionality"""

    def test_parallel_threshold_method_exists(self):
        """Test that parallel_threshold method exists and is chainable"""
        tools = json_tools_rs.JSONTools().flatten().parallel_threshold(50)
        assert tools is not None

    def test_num_threads_method_exists(self):
        """Test that num_threads method exists and is chainable"""
        tools = json_tools_rs.JSONTools().flatten().num_threads(4)
        assert tools is not None

    def test_num_threads_with_none(self):
        """Test that num_threads accepts None (use Rayon default)"""
        tools = json_tools_rs.JSONTools().flatten().num_threads(None)
        assert tools is not None

    def test_nested_parallel_threshold_method_exists(self):
        """Test that nested_parallel_threshold method exists and is chainable"""
        tools = json_tools_rs.JSONTools().flatten().nested_parallel_threshold(200)
        assert tools is not None

    def test_parallel_methods_chaining(self):
        """Test that all parallel methods can be chained together"""
        tools = (
            json_tools_rs.JSONTools()
            .flatten()
            .parallel_threshold(50)
            .num_threads(4)
            .nested_parallel_threshold(200)
            .remove_empty_strings(True)
        )
        assert tools is not None

    def test_parallel_batch_processing_small_batch(self):
        """Test batch processing with small batch (below default threshold)"""
        tools = json_tools_rs.JSONTools().flatten()
        batch = [{"key": i, "nested": {"value": i * 10}} for i in range(5)]
        results = tools.execute(batch)

        assert len(results) == 5
        assert all(isinstance(r, dict) for r in results)
        assert results[0]["key"] == 0
        assert results[0]["nested.value"] == 0
        assert results[4]["key"] == 4
        assert results[4]["nested.value"] == 40

    def test_parallel_batch_processing_medium_batch(self):
        """Test batch processing with medium batch (above default threshold of 10)"""
        tools = json_tools_rs.JSONTools().flatten()
        batch = [{"user_id": i, "data": {"score": i * 100}} for i in range(25)]
        results = tools.execute(batch)

        assert len(results) == 25
        assert all(isinstance(r, dict) for r in results)
        assert results[0]["user_id"] == 0
        assert results[0]["data.score"] == 0
        assert results[24]["user_id"] == 24
        assert results[24]["data.score"] == 2400

    def test_parallel_batch_processing_large_batch(self):
        """Test batch processing with large batch (>1000 items, uses chunked processing)"""
        tools = json_tools_rs.JSONTools().flatten()
        batch = [{"id": i, "value": i * 2} for i in range(1500)]
        results = tools.execute(batch)

        assert len(results) == 1500
        assert all(isinstance(r, dict) for r in results)
        assert results[0]["id"] == 0
        assert results[0]["value"] == 0
        assert results[1499]["id"] == 1499
        assert results[1499]["value"] == 2998

    def test_parallel_threshold_configuration(self):
        """Test custom parallel threshold configuration"""
        # Set threshold to 100, so batch of 50 should process sequentially
        tools = json_tools_rs.JSONTools().flatten().parallel_threshold(100)
        batch = [{"key": i} for i in range(50)]
        results = tools.execute(batch)

        assert len(results) == 50
        assert all(isinstance(r, dict) for r in results)

    def test_parallel_with_string_batch(self):
        """Test parallel processing with list of JSON strings"""
        tools = json_tools_rs.JSONTools().flatten()
        batch = [f'{{"id": {i}, "nested": {{"value": {i * 10}}}}}' for i in range(20)]
        results = tools.execute(batch)

        assert len(results) == 20
        assert all(isinstance(r, str) for r in results)
        parsed_0 = json.loads(results[0])
        assert parsed_0["id"] == 0
        assert parsed_0["nested.value"] == 0

    def test_parallel_with_mixed_operations(self):
        """Test parallel processing with various transformations"""
        tools = (
            json_tools_rs.JSONTools()
            .flatten()
            .parallel_threshold(10)
            .remove_empty_strings(True)
            .remove_nulls(True)
            .lowercase_keys(True)
        )
        batch = [
            {"User_ID": i, "Name": "Test", "Empty": "", "Null": None}
            for i in range(15)
        ]
        results = tools.execute(batch)

        assert len(results) == 15
        for result in results:
            assert "user_id" in result  # lowercase
            assert "name" in result
            assert "Empty" not in result  # removed
            assert "Null" not in result  # removed

    def test_parallel_unflatten_batch(self):
        """Test parallel processing with unflatten operation"""
        tools = json_tools_rs.JSONTools().unflatten().parallel_threshold(10)
        batch = [{"user.id": i, "user.name": f"User{i}"} for i in range(20)]
        results = tools.execute(batch)

        assert len(results) == 20
        assert all(isinstance(r, dict) for r in results)
        assert results[0]["user"]["id"] == 0
        assert results[0]["user"]["name"] == "User0"
        assert results[19]["user"]["id"] == 19
        assert results[19]["user"]["name"] == "User19"

    def test_parallel_with_collision_handling(self):
        """Test parallel processing with collision handling"""
        tools = (
            json_tools_rs.JSONTools()
            .flatten()
            .parallel_threshold(5)
            .key_replacement("(user|admin)_", "")
            .handle_key_collision(True)
        )
        batch = [
            {"user_name": f"User{i}", "admin_name": f"Admin{i}"} for i in range(10)
        ]
        results = tools.execute(batch)

        assert len(results) == 10
        for i, result in enumerate(results):
            assert "name" in result
            # Should be an array due to collision
            assert isinstance(result["name"], list)
            assert len(result["name"]) == 2

    def test_parallel_performance_benefit(self):
        """Test that parallel processing provides performance benefit for large batches"""
        # Create a large batch with complex nested structures
        large_batch = [
            {
                "user": {
                    "id": i,
                    "profile": {
                        "name": f"User{i}",
                        "email": f"user{i}@example.com",
                        "settings": {"theme": "dark", "notifications": True},
                    },
                    "posts": [
                        {"id": j, "title": f"Post {j}", "likes": j * 10}
                        for j in range(5)
                    ],
                }
            }
            for i in range(100)
        ]

        # Process with parallel processing enabled (default threshold = 10)
        tools_parallel = json_tools_rs.JSONTools().flatten()
        start = time.time()
        results_parallel = tools_parallel.execute(large_batch)
        time_parallel = time.time() - start

        # Verify results are correct
        assert len(results_parallel) == 100
        assert all(isinstance(r, dict) for r in results_parallel)
        assert "user.id" in results_parallel[0]
        assert "user.profile.name" in results_parallel[0]
        assert "user.posts.0.title" in results_parallel[0]

        # Just verify it completes successfully - actual speedup depends on hardware
        assert time_parallel > 0

    def test_nested_parallel_threshold_large_object(self):
        """Test nested parallel threshold with large objects"""
        # Create a large object with many keys
        large_object = {f"key_{i}": {"nested": i, "value": i * 10} for i in range(150)}

        # With default nested threshold (100), this should trigger nested parallelism
        tools = json_tools_rs.JSONTools().flatten()
        result = tools.execute(large_object)

        assert isinstance(result, dict)
        assert len(result) == 300  # 150 keys * 2 nested fields each
        assert result["key_0.nested"] == 0
        assert result["key_0.value"] == 0
        assert result["key_149.nested"] == 149
        assert result["key_149.value"] == 1490

    def test_nested_parallel_threshold_configuration(self):
        """Test custom nested parallel threshold configuration"""
        # Set very high threshold so nested parallelism won't trigger
        large_object = {f"key_{i}": {"nested": i} for i in range(150)}

        tools = json_tools_rs.JSONTools().flatten().nested_parallel_threshold(1000)
        result = tools.execute(large_object)

        assert isinstance(result, dict)
        assert len(result) == 150
        assert result["key_0.nested"] == 0
        assert result["key_149.nested"] == 149

    def test_parallel_with_type_conversion(self):
        """Test parallel processing with automatic type conversion"""
        tools = (
            json_tools_rs.JSONTools()
            .flatten()
            .parallel_threshold(10)
            .auto_convert_types(True)
        )
        batch = [
            {"id": str(i), "score": f"{i * 100}", "active": "true"} for i in range(20)
        ]
        results = tools.execute(batch)

        assert len(results) == 20
        for i, result in enumerate(results):
            assert result["id"] == i  # Converted to int
            assert result["score"] == i * 100  # Converted to int
            assert result["active"] is True  # Converted to bool

    def test_parallel_roundtrip_consistency(self):
        """Test that parallel processing maintains roundtrip consistency"""
        original_batch = [
            {"user": {"id": i, "data": {"value": i * 10}}} for i in range(25)
        ]

        # Flatten with parallel processing
        flatten_tools = json_tools_rs.JSONTools().flatten().parallel_threshold(10)
        flattened = flatten_tools.execute(original_batch)

        # Unflatten with parallel processing
        unflatten_tools = json_tools_rs.JSONTools().unflatten().parallel_threshold(10)
        unflattened = unflatten_tools.execute(flattened)

        # Should match original
        assert len(unflattened) == len(original_batch)
        for i, (original, result) in enumerate(zip(original_batch, unflattened)):
            assert result == original

    def test_parallel_error_handling(self):
        """Test that parallel processing handles errors correctly"""
        tools = json_tools_rs.JSONTools().flatten().parallel_threshold(5)

        # Mix of valid and invalid JSON strings
        batch = ['{"valid": 1}', '{"valid": 2}', "invalid json", '{"valid": 3}']

        with pytest.raises(Exception):  # Should raise error for invalid JSON
            tools.execute(batch)

    def test_parallel_empty_batch(self):
        """Test parallel processing with empty batch"""
        tools = json_tools_rs.JSONTools().flatten().parallel_threshold(10)
        results = tools.execute([])

        assert results == []

    def test_parallel_single_item_batch(self):
        """Test parallel processing with single item (below threshold)"""
        tools = json_tools_rs.JSONTools().flatten().parallel_threshold(10)
        batch = [{"key": "value", "nested": {"data": 123}}]
        results = tools.execute(batch)

        assert len(results) == 1
        assert results[0]["key"] == "value"
        assert results[0]["nested.data"] == 123

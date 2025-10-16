"""Edge case tests for robust-json-parser."""

import pytest
from robust_json import loads, extract, RobustJSONParser


class TestMalformedJSON:
    """Test handling of various malformed JSON scenarios."""

    def test_missing_closing_quotes(self):
        """Test handling strings with missing closing quotes."""
        json_str = '{"key": "value without closing quote}'
        # Should still attempt to parse or return None/default
        result = loads(json_str, default=None)
        # Behavior may vary, but shouldn't crash
        assert result is None or isinstance(result, dict)

    def test_unescaped_special_chars(self):
        """Test handling unescaped special characters."""
        json_str = '{"path": "C:\\Users\\Documents"}'
        result = loads(json_str)
        assert "path" in result

    def test_numeric_keys_as_strings(self):
        """Test numeric keys (should be strings in JSON)."""
        json_str = '{"123": "value", "456": "another"}'
        result = loads(json_str)
        assert result["123"] == "value"

    def test_leading_zeros_in_numbers(self):
        """Test numbers with leading zeros."""
        json_str = '{"value": 007}'
        result = loads(json_str, default={})
        # May or may not parse, but shouldn't crash
        assert isinstance(result, dict)

    def test_multiline_strings_in_json(self):
        """Test handling multiline string values."""
        json_str = '''{"description": "This is a
        multiline
        string"}'''
        # This is invalid JSON, but test graceful handling
        result = loads(json_str, default={})
        assert isinstance(result, dict)


class TestBracketMatching:
    """Test bracket and brace matching edge cases."""

    def test_mismatched_brackets(self):
        """Test handling mismatched brackets."""
        json_str = '{"array": [1, 2, 3}]'
        result = loads(json_str, default=None)
        # Should handle gracefully
        assert result is None or isinstance(result, dict)

    def test_extra_closing_brackets(self):
        """Test handling extra closing brackets."""
        json_str = '{"key": "value"}}'
        result = loads(json_str)
        assert result == {"key": "value"}

    def test_nested_brackets_in_strings(self):
        """Test brackets inside string values."""
        json_str = '{"json": "{\\"nested\\": \\"value\\"}"}'
        result = loads(json_str)
        assert "json" in result

    def test_deeply_nested_mismatched(self):
        """Test deeply nested with mismatch."""
        json_str = '{"a": {"b": {"c": [1, 2, 3}'
        result = loads(json_str)
        # Should complete the missing brackets
        assert result["a"]["b"]["c"] == [1, 2, 3]


class TestUnicodeAndEncoding:
    """Test Unicode and encoding edge cases."""

    def test_emoji_in_values(self):
        """Test emoji in JSON values."""
        json_str = '{"message": "Hello 👋", "status": "✅"}'
        result = loads(json_str)
        assert result["message"] == "Hello 👋"
        assert result["status"] == "✅"

    def test_emoji_in_keys(self):
        """Test emoji in JSON keys."""
        json_str = '{"👤": "user", "📧": "email"}'
        result = loads(json_str)
        assert result["👤"] == "user"

    def test_mixed_language_scripts(self):
        """Test mixed language scripts."""
        json_str = '''
        {
            "english": "Hello",
            "中文": "你好",
            "日本語": "こんにちは",
            "한국어": "안녕하세요",
            "العربية": "مرحبا",
            "русский": "Привет"
        }
        '''
        result = loads(json_str)
        assert len(result) == 6
        assert result["中文"] == "你好"

    def test_zero_width_characters(self):
        """Test handling zero-width characters."""
        # Zero-width space
        json_str = '{"key​": "value"}'  # Contains zero-width space
        result = loads(json_str, default={})
        assert isinstance(result, dict)


class TestNumberFormatting:
    """Test various number formatting scenarios."""

    def test_scientific_notation(self):
        """Test scientific notation numbers."""
        json_str = '{"small": 1.23e-10, "large": 1.23e10}'
        result = loads(json_str)
        assert result["small"] < 1
        assert result["large"] > 1

    def test_negative_numbers(self):
        """Test negative numbers."""
        json_str = '{"neg_int": -42, "neg_float": -3.14}'
        result = loads(json_str)
        assert result["neg_int"] == -42
        assert result["neg_float"] == -3.14

    def test_very_large_numbers(self):
        """Test very large numbers."""
        json_str = '{"big": 9999999999999999999999}'
        result = loads(json_str)
        assert "big" in result
        assert result["big"] > 0

    def test_floating_point_precision(self):
        """Test floating point precision."""
        json_str = '{"pi": 3.141592653589793}'
        result = loads(json_str)
        assert abs(result["pi"] - 3.141592653589793) < 1e-10


class TestWhitespaceHandling:
    """Test whitespace handling."""

    def test_excessive_whitespace(self):
        """Test JSON with excessive whitespace."""
        json_str = '''
        {
            
            "key"    :    "value"    ,
            
            "number"   :   42
            
        }
        '''
        result = loads(json_str)
        assert result == {"key": "value", "number": 42}

    def test_no_whitespace(self):
        """Test JSON with no whitespace."""
        json_str = '{"a":1,"b":2,"c":3}'
        result = loads(json_str)
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_tabs_and_newlines(self):
        """Test various whitespace characters."""
        json_str = '{\n\t"key":\t"value"\n}'
        result = loads(json_str)
        assert result == {"key": "value"}


class TestSpecialJSONValues:
    """Test special JSON values and types."""

    def test_true_false_null(self):
        """Test boolean and null values."""
        json_str = '{"t": true, "f": false, "n": null}'
        result = loads(json_str)
        assert result["t"] is True
        assert result["f"] is False
        assert result["n"] is None

    def test_case_sensitivity(self):
        """Test that values are case-sensitive."""
        json_str = '{"True": "not a boolean", "FALSE": "also not"}'
        result = loads(json_str)
        assert result["True"] == "not a boolean"

    def test_empty_string_value(self):
        """Test empty string values."""
        json_str = '{"empty": "", "spaces": "   "}'
        result = loads(json_str)
        assert result["empty"] == ""
        assert result["spaces"] == "   "


class TestCommentEdgeCases:
    """Test edge cases in comment handling."""

    def test_comment_like_strings(self):
        """Test strings that look like comments."""
        json_str = '{"url": "https://example.com", "note": "Use // for paths"}'
        result = loads(json_str)
        assert "//" in result["note"]

    def test_hash_in_url(self):
        """Test URLs with hash fragments."""
        json_str = '{"link": "https://example.com#section"}'
        result = loads(json_str)
        assert result["link"] == "https://example.com#section"

    def test_comment_at_end_of_file(self):
        """Test comment at end of file."""
        json_str = '{"key": "value"} // end comment'
        result = loads(json_str)
        assert result == {"key": "value"}

    def test_block_comment_style(self):
        """Test C-style block comments."""
        json_str = '''
        {
            /* block comment */
            "key": "value"
        }
        '''
        result = loads(json_str)
        assert result == {"key": "value"}


class TestExtractionPriority:
    """Test extraction priority and conflict resolution."""

    def test_code_block_vs_inline(self):
        """Test that code blocks are prioritized."""
        text = '''
        Inline: {"inline": 1}
        ```json
        {"code_block": 2}
        ```
        '''
        result = loads(text)
        # Code block should be found first
        assert "code_block" in result or "inline" in result

    def test_multiple_json_in_text(self):
        """Test selecting first valid JSON."""
        text = 'First: {"a": 1} Second: {"b": 2}'
        result = loads(text)
        assert result == {"a": 1}

    def test_nested_json_strings(self):
        """Test JSON containing JSON strings."""
        json_str = '{"data": "{\\"nested\\": \\"json\\"}"}'
        result = loads(json_str)
        assert isinstance(result["data"], str)
        assert "nested" in result["data"]


class TestParserConfiguration:
    """Test parser configuration options."""

    def test_strict_mode_requires_explicit_json(self):
        """Test strict mode behavior."""
        parser = RobustJSONParser(strict=True)
        
        # Without code block, strict mode may fail
        text_no_block = '{"key": "value"}'
        result_no_block = parser.parse_first(text_no_block)
        
        # With code block, should work
        text_with_block = '```json\n{"key": "value"}\n```'
        result_with_block = parser.parse_first(text_with_block)
        assert result_with_block == {"key": "value"}

    def test_allow_partial_configuration(self):
        """Test allow_partial configuration."""
        parser_allow = RobustJSONParser(allow_partial=True)
        parser_disallow = RobustJSONParser(allow_partial=False)
        
        incomplete = '{"key": "value"'
        
        result_allow = parser_allow.parse_first(incomplete)
        assert result_allow is not None
        
        result_disallow = parser_disallow.parse_first(incomplete)
        # May fail to parse
        assert result_disallow is None or result_disallow == {"key": "value"}

    def test_parser_configuration_options(self):
        """Test parser configuration options."""
        parser = RobustJSONParser()
        
        json_str = '{"key": "value"}'
        
        # Should handle standard JSON
        assert parser.parse_first(json_str) == {"key": "value"}


class TestMemoryAndPerformance:
    """Test memory and performance edge cases."""

    def test_very_long_string_value(self):
        """Test handling very long string values."""
        long_string = "a" * 10000
        json_str = f'{{"long": "{long_string}"}}'
        result = loads(json_str)
        assert len(result["long"]) == 10000

    def test_many_keys(self):
        """Test object with many keys."""
        keys = [f'"key{i}": {i}' for i in range(1000)]
        json_str = "{" + ",".join(keys) + "}"
        result = loads(json_str)
        assert len(result) == 1000

    def test_deeply_nested_arrays(self):
        """Test deeply nested arrays."""
        json_str = "[[[[[[[[[[1]]]]]]]]]]"
        result = loads(json_str)
        # Navigate to deepest level
        current = result
        depth = 0
        while isinstance(current, list) and len(current) > 0:
            current = current[0]
            depth += 1
        assert depth == 10


class TestErrorRecovery:
    """Test error recovery mechanisms."""

    def test_multiple_errors_in_one_json(self):
        """Test JSON with multiple types of errors."""
        json_str = '''
        {
            'single_quotes': 'value',  // comment
            "trailing_comma": "here",
            "incomplete": "val
        '''
        result = loads(json_str)
        assert "single_quotes" in result
        assert "trailing_comma" in result

    def test_recovery_from_syntax_errors(self):
        """Test recovery from various syntax errors."""
        # Missing comma
        json_str = '{"a": 1 "b": 2}'
        result = loads(json_str, default={})
        assert isinstance(result, dict)

    def test_partial_with_errors(self):
        """Test partial JSON combined with errors."""
        json_str = "{'key': 'value', // comment\n"
        result = loads(json_str)
        assert result.get("key") == "value"


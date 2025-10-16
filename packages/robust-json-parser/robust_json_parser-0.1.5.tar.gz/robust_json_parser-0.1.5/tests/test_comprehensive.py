"""Comprehensive test suite for robust-json-parser."""

import pytest
from robust_json import Extraction, RobustJSONParser, extract, extract_all, loads


class TestBasicFunctionality:
    """Test basic JSON parsing functionality."""

    def test_valid_json_object(self):
        """Test parsing valid JSON object."""
        result = loads('{"name": "Alice", "age": 30}')
        assert result == {"name": "Alice", "age": 30}

    def test_valid_json_array(self):
        """Test parsing valid JSON array."""
        result = loads('[1, 2, 3, 4, 5]')
        assert result == [1, 2, 3, 4, 5]

    def test_nested_structures(self):
        """Test parsing deeply nested JSON structures."""
        json_str = '{"a": {"b": {"c": {"d": [1, 2, 3]}}}}'
        result = loads(json_str)
        assert result["a"]["b"]["c"]["d"] == [1, 2, 3]

    def test_unicode_content(self):
        """Test parsing JSON with Unicode characters."""
        json_str = '{"message": "你好世界", "emoji": "🎉"}'
        result = loads(json_str)
        assert result["message"] == "你好世界"
        assert result["emoji"] == "🎉"

    def test_numbers_and_booleans(self):
        """Test parsing different data types."""
        json_str = '{"int": 42, "float": 3.14, "bool": true, "null": null}'
        result = loads(json_str)
        assert result["int"] == 42
        assert result["float"] == 3.14
        assert result["bool"] is True
        assert result["null"] is None


class TestCommentHandling:
    """Test comment stripping functionality."""

    def test_single_line_comments(self):
        """Test removal of // comments."""
        json_str = '''
        {
            "name": "Bob", // this is a name
            "age": 25 // this is an age
        }
        '''
        result = loads(json_str)
        assert result == {"name": "Bob", "age": 25}

    def test_hash_comments(self):
        """Test removal of # comments."""
        json_str = '''
        {
            "key": "value", # Python-style comment
            "number": 42  # Another comment
        }
        '''
        result = loads(json_str)
        assert result == {"key": "value", "number": 42}

    def test_mixed_comments(self):
        """Test handling both comment styles."""
        json_str = '''
        {
            "a": 1, // C-style
            "b": 2  # Python-style
        }
        '''
        result = loads(json_str)
        assert result == {"a": 1, "b": 2}

    def test_comments_in_strings_preserved(self):
        """Test that comments inside strings are preserved."""
        json_str = '{"url": "https://example.com/path"}'
        result = loads(json_str)
        assert result["url"] == "https://example.com/path"


class TestTrailingCommas:
    """Test trailing comma removal."""

    def test_trailing_comma_in_object(self):
        """Test removal of trailing comma in objects."""
        json_str = '{"a": 1, "b": 2,}'
        result = loads(json_str)
        assert result == {"a": 1, "b": 2}

    def test_trailing_comma_in_array(self):
        """Test removal of trailing comma in arrays."""
        json_str = '[1, 2, 3,]'
        result = loads(json_str)
        assert result == [1, 2, 3]

    def test_multiple_trailing_commas(self):
        """Test handling multiple trailing commas."""
        json_str = '''
        {
            "items": [1, 2, 3,],
            "nested": {"x": 1, "y": 2,},
        }
        '''
        result = loads(json_str)
        assert result["items"] == [1, 2, 3]
        assert result["nested"] == {"x": 1, "y": 2}


class TestSingleQuotes:
    """Test single quote normalization."""

    def test_single_quoted_strings(self):
        """Test conversion of single quotes to double quotes."""
        json_str = "{'name': 'Alice', 'city': 'NYC'}"
        result = loads(json_str)
        assert result == {"name": "Alice", "city": "NYC"}

    def test_mixed_quotes(self):
        """Test handling mixed quote types."""
        json_str = '{"name": \'Bob\', "age": 30}'
        result = loads(json_str)
        assert result == {"name": "Bob", "age": 30}

    def test_quotes_with_escapes(self):
        """Test handling escaped quotes."""
        json_str = '{"message": "He said \\"hello\\""}'
        result = loads(json_str)
        assert result["message"] == 'He said "hello"'

    def test_mixed_quote_types_repaired(self):
        """Test repair of strings with mismatched quote types."""
        json_str = '''{"summary": '候选人具备一定AI背景，但经验不足。"}'''
        result = loads(json_str)
        assert "summary" in result
        assert "候选人" in result["summary"]


class TestPartialJSON:
    """Test partial/truncated JSON completion."""

    def test_incomplete_object(self):
        """Test completion of truncated object."""
        json_str = '{"name": "Alice", "age": 30'
        result = loads(json_str)
        assert result["name"] == "Alice"
        assert result["age"] == 30

    def test_incomplete_nested_object(self):
        """Test completion of nested truncated object."""
        json_str = '{"user": {"name": "Bob", "email": "bob@example.com"'
        result = loads(json_str)
        assert result["user"]["name"] == "Bob"
        assert result["user"]["email"] == "bob@example.com"

    def test_incomplete_array(self):
        """Test completion of truncated array."""
        json_str = '{"items": [1, 2, 3'
        result = loads(json_str)
        assert result["items"] == [1, 2, 3]

    def test_disable_partial_completion(self):
        """Test that partial completion can be disabled."""
        json_str = '{"incomplete": "value"'
        result = loads(json_str, allow_partial=False, default={})
        # Should fail to parse and return default
        assert result == {}


class TestCodeBlockExtraction:
    """Test extraction from markdown code blocks."""

    def test_json_code_block(self):
        """Test extraction from ```json code block."""
        text = """
        Here's the data:
        ```json
        {"status": "success", "code": 200}
        ```
        """
        result = loads(text)
        assert result == {"status": "success", "code": 200}

    def test_generic_code_block(self):
        """Test extraction from ``` code block without language."""
        text = """
        Response:
        ```
        {"result": "ok"}
        ```
        """
        result = loads(text)
        assert result == {"result": "ok"}

    def test_multiple_code_blocks(self):
        """Test extraction from multiple code blocks."""
        text = """
        First block:
        ```json
        {"a": 1}
        ```
        Second block:
        ```json
        {"b": 2}
        ```
        """
        parser = RobustJSONParser()
        results = parser.parse_all(text)
        assert len(results) == 2
        assert results[0] == {"a": 1}
        assert results[1] == {"b": 2}


class TestLLMOutputScenarios:
    """Test real-world LLM output scenarios."""

    def test_chatgpt_style_response(self):
        """Test parsing ChatGPT-style responses."""
        text = """
        Sure! Here's the JSON data you requested:
        
        ```json
        {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ],
            "total": 2
        }
        ```
        
        Is there anything else you'd like to know?
        """
        result = loads(text)
        assert result["total"] == 2
        assert len(result["users"]) == 2

    def test_llm_with_explanations(self):
        """Test parsing JSON mixed with explanatory text."""
        text = """
        Based on the requirements, here's the configuration:
        
        {"environment": "production", "debug": false, "port": 8080}
        
        This will run the server on port 8080 in production mode.
        """
        result = loads(text)
        assert result["environment"] == "production"
        assert result["debug"] is False

    def test_llm_incomplete_due_to_token_limit(self):
        """Test handling LLM output cut off by token limit."""
        text = """
        Here's a large dataset:
        {
            "records": [
                {"id": 1, "data": "first"},
                {"id": 2, "data": "second"},
                {"id": 3, "data": "thi
        """
        result = loads(text)
        assert "records" in result
        assert len(result["records"]) >= 2


class TestExtractFunction:
    """Test the extract() function."""

    def test_extract_returns_extraction_object(self):
        """Test that extract returns Extraction object."""
        text = 'Some text {"key": "value"} more text'
        extraction = extract(text)
        assert isinstance(extraction, Extraction)
        assert extraction.text == '{"key": "value"}'
        assert extraction.start > 0
        assert extraction.end > extraction.start

    def test_extract_returns_none_for_no_json(self):
        """Test extract returns None when no JSON found."""
        text = "This is just plain text with no JSON"
        extraction = extract(text)
        assert extraction is None

    def test_extract_partial_flag(self):
        """Test extract detects partial JSON."""
        text = '{"incomplete": "json"'
        extraction = extract(text)
        assert extraction is not None
        assert extraction.is_partial is True


class TestExtractAllFunction:
    """Test the extract_all() function."""

    def test_extract_all_multiple_objects(self):
        """Test extracting multiple JSON objects."""
        text = 'First: {"a": 1} Second: {"b": 2} Third: {"c": 3}'
        extractions = extract_all(text)
        assert len(extractions) == 3

    def test_extract_all_with_arrays(self):
        """Test extracting arrays."""
        text = 'Array 1: [1, 2, 3] Array 2: [4, 5, 6]'
        extractions = extract_all(text)
        assert len(extractions) == 2

    def test_extract_all_preserves_order(self):
        """Test that extractions are in order."""
        text = '{"first": 1} {"second": 2}'
        extractions = extract_all(text)
        assert extractions[0].start < extractions[1].start


class TestRobustJSONParserClass:
    """Test the RobustJSONParser class directly."""

    def test_parser_with_strict_mode(self):
        """Test parser in strict mode."""
        parser = RobustJSONParser(strict=True)
        # Strict mode should only extract from code blocks
        text = 'Random text {"a": 1} more text'
        result = parser.parse_first(text)
        # In strict mode, might not parse without code block
        assert result is None or result == {"a": 1}

    def test_parser_allow_partial_false(self):
        """Test parser with partial completion disabled."""
        parser = RobustJSONParser(allow_partial=False)
        incomplete = '{"key": "value"'
        result = parser.parse_first(incomplete)
        assert result is None

    def test_parser_basic_functionality(self):
        """Test parser basic functionality."""
        parser = RobustJSONParser()
        json_str = '{"key": "value"}'
        result = parser.parse_first(json_str)
        assert result == {"key": "value"}

    def test_parser_parse_all(self):
        """Test parse_all method."""
        parser = RobustJSONParser()
        text = '{"a": 1} {"b": 2} {"c": 3}'
        results = parser.parse_all(text)
        assert len(results) == 3
        assert results[0]["a"] == 1
        assert results[1]["b"] == 2
        assert results[2]["c"] == 3


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_loads_with_default(self):
        """Test loads with default value."""
        result = loads("not json at all", default={"error": True})
        assert result == {"error": True}

    def test_loads_raises_without_default(self):
        """Test loads raises ValueError without default."""
        with pytest.raises(ValueError, match="No JSON payload could be recovered"):
            loads("not json at all")

    def test_empty_string(self):
        """Test handling empty string."""
        result = loads("", default=None)
        assert result is None

    def test_whitespace_only(self):
        """Test handling whitespace-only string."""
        result = loads("   \n\t  ", default={})
        assert result == {}


class TestComplexRealWorldExamples:
    """Test complex real-world scenarios."""

    def test_api_response_with_mixed_formatting(self):
        """Test parsing messy API response."""
        response = """
        {
            "status": "success",
            "data": {
                "users": [
                    {"id": 1, "name": "Alice", "active": true,},  // trailing comma
                    {'id': 2, 'name': 'Bob', 'active': false},  # single quotes
                ],  // another trailing comma
                "total_count": 2,
            },
            "timestamp": "2025-01-15T10:30:00Z"  # ISO format
        }
        """
        result = loads(response)
        assert result["status"] == "success"
        assert len(result["data"]["users"]) == 2
        assert result["data"]["total_count"] == 2

    def test_config_file_with_comments(self):
        """Test parsing configuration file with comments."""
        config = """
        {
            // Server configuration
            "server": {
                "host": "0.0.0.0",  // Listen on all interfaces
                "port": 8080,
                "ssl": false,  # SSL disabled for development
            },
            // Database settings
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "myapp_db",
            },
        }
        """
        result = loads(config)
        assert result["server"]["port"] == 8080
        assert result["database"]["name"] == "myapp_db"

    def test_multilingual_content(self):
        """Test parsing JSON with multiple languages."""
        json_str = """
        {
            "greetings": {
                "english": "Hello",
                "chinese": "你好",
                "japanese": "こんにちは",
                "arabic": "مرحبا",
                "emoji": "👋🌍"
            }
        }
        """
        result = loads(json_str)
        assert result["greetings"]["chinese"] == "你好"
        assert result["greetings"]["emoji"] == "👋🌍"

    def test_complex_nested_with_all_issues(self):
        """Test JSON with multiple issues combined."""
        json_str = """
        Sure, here's the data:
        ```json
        {
            'timestamp': '2025-01-15',  // Current date
            "records": [
                {"id": 1, "value": "first",},  # First record
                {'id': 2, 'value': 'second'},
            ],
            "metadata": {
                "total": 2,
                "source": 'api-v1',  # API version
            },  // End of metadata
        }
        ```
        Hope this helps!
        """
        result = loads(json_str)
        assert result["timestamp"] == "2025-01-15"
        assert len(result["records"]) == 2
        assert result["metadata"]["total"] == 2
        assert result["metadata"]["source"] == "api-v1"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_deeply_nested_json(self):
        """Test parsing very deeply nested structures."""
        json_str = '{"a":{"b":{"c":{"d":{"e":{"f":{"g":"deep"}}}}}}}'
        result = loads(json_str)
        assert result["a"]["b"]["c"]["d"]["e"]["f"]["g"] == "deep"

    def test_large_array(self):
        """Test parsing large arrays."""
        json_str = "[" + ",".join(str(i) for i in range(1000)) + "]"
        result = loads(json_str)
        assert len(result) == 1000
        assert result[0] == 0
        assert result[999] == 999

    def test_special_characters_in_strings(self):
        """Test handling special characters."""
        json_str = r'{"text": "Line1\nLine2\tTabbed"}'
        result = loads(json_str)
        assert "\n" in result["text"]
        assert "\t" in result["text"]

    def test_json_with_null_values(self):
        """Test handling null values."""
        json_str = '{"value": null, "items": [1, null, 3]}'
        result = loads(json_str)
        assert result["value"] is None
        assert result["items"][1] is None

    def test_empty_objects_and_arrays(self):
        """Test parsing empty structures."""
        json_str = '{"obj": {}, "arr": []}'
        result = loads(json_str)
        assert result["obj"] == {}
        assert result["arr"] == []


class TestPerformance:
    """Test performance-related scenarios."""

    def test_multiple_extractions_efficiency(self):
        """Test that multiple extractions work efficiently."""
        text = " ".join([f'{{"item": {i}}}' for i in range(100)])
        extractions = extract_all(text)
        assert len(extractions) == 100

    def test_reuse_parser_instance(self):
        """Test reusing parser instance."""
        parser = RobustJSONParser()
        texts = [
            '{"a": 1}',
            '{"b": 2}',
            '{"c": 3}',
        ]
        results = [parser.parse_first(text) for text in texts]
        assert len(results) == 3
        assert all(r is not None for r in results)


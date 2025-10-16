"""Performance tests for robust-json-parser."""

import time
import random
import string
import json
from typing import List, Dict, Any
import pytest
from robust_json import loads, extract_all, RobustJSONParser


class TestPerformance:
    """Test performance characteristics of the parser."""

    def test_large_json_parsing(self):
        """Test parsing large JSON objects."""
        # Create a large JSON object
        large_data = {
            "users": [
                {
                    "id": i,
                    "name": f"User {i}",
                    "email": f"user{i}@example.com",
                    "profile": {
                        "age": random.randint(18, 80),
                        "city": random.choice(["New York", "London", "Tokyo", "Paris"]),
                        "interests": [f"interest_{j}" for j in range(random.randint(1, 10))]
                    },
                    "metadata": {
                        "created": "2025-01-15T10:30:00Z",
                        "last_login": "2025-01-15T09:15:00Z",
                        "active": random.choice([True, False])
                    }
                }
                for i in range(1000)
            ],
            "total": 1000,
            "page": 1,
            "per_page": 1000
        }
        
        import json
        json_str = json.dumps(large_data)
        
        start_time = time.time()
        result = loads(json_str)
        end_time = time.time()
        
        assert result["total"] == 1000
        assert len(result["users"]) == 1000
        assert (end_time - start_time) < 1.0  # Should parse in under 1 second

    def test_many_small_json_objects(self):
        """Test parsing many small JSON objects."""
        small_objects = []
        for i in range(1000):
            obj = {
                "id": i,
                "name": f"Item {i}",
                "value": random.randint(1, 100),
                "active": random.choice([True, False])
            }
            small_objects.append(json.dumps(obj))
        
        start_time = time.time()
        results = []
        for obj_str in small_objects:
            result = loads(obj_str)
            results.append(result)
        end_time = time.time()
        
        assert len(results) == 1000
        assert (end_time - start_time) < 2.0  # Should parse 1000 objects in under 2 seconds

    def test_deeply_nested_json(self):
        """Test parsing deeply nested JSON structures."""
        # Create a deeply nested structure
        current = {}
        for i in range(50):  # 50 levels deep
            current = {"level": i, "data": current}
        
        import json
        json_str = json.dumps(current)
        
        start_time = time.time()
        result = loads(json_str)
        end_time = time.time()
        
        # Navigate to the deepest level
        current = result
        depth = 0
        while "data" in current and isinstance(current["data"], dict):
            current = current["data"]
            depth += 1
        
        assert depth == 50  # 50 levels total
        assert (end_time - start_time) < 0.5  # Should parse quickly

    def test_large_string_values(self):
        """Test parsing JSON with very large string values."""
        # Create a large string
        large_string = "A" * 100000  # 100KB string
        
        data = {
            "large_text": large_string,
            "metadata": {"size": len(large_string)},
            "chunks": [large_string[i:i+1000] for i in range(0, len(large_string), 1000)]
        }
        
        import json
        json_str = json.dumps(data)
        
        start_time = time.time()
        result = loads(json_str)
        end_time = time.time()
        
        assert len(result["large_text"]) == 100000
        assert len(result["chunks"]) == 100
        assert (end_time - start_time) < 1.0  # Should handle large strings efficiently

    def test_mixed_formatting_performance(self):
        """Test performance with mixed formatting (comments, trailing commas, etc.)."""
        # Create JSON with various formatting issues
        messy_json = '''
        {
            "users": [
                {"id": 1, "name": "Alice", "active": true,},  // trailing comma
                {'id': 2, 'name': 'Bob', 'active': false},  # single quotes
                {"id": 3, "name": "Charlie", "active": true,},  // another trailing comma
            ],  // trailing comma
            "metadata": {
                "total": 3,
                "created": "2025-01-15",  # date
                "version": "1.0.0",
            },  // end metadata
        }
        '''
        
        start_time = time.time()
        result = loads(messy_json)
        end_time = time.time()
        
        assert result["metadata"]["total"] == 3
        assert len(result["users"]) == 3
        assert (end_time - start_time) < 0.1  # Should handle mixed formatting quickly

    def test_conversational_text_performance(self):
        """Test performance with conversational text extraction."""
        # Create text with embedded JSON
        conversational_texts = []
        for i in range(100):
            text = f"""
            Here's the data for user {i}:
            
            {{
                "user_id": {i},
                "name": "User {i}",
                "email": "user{i}@example.com",
                "active": true
            }}
            
            This user has been active for {random.randint(1, 365)} days.
            """
            conversational_texts.append(text)
        
        start_time = time.time()
        results = []
        for text in conversational_texts:
            result = loads(text)
            results.append(result)
        end_time = time.time()
        
        assert len(results) == 100
        assert all("user_id" in result for result in results)
        assert (end_time - start_time) < 2.0  # Should extract from 100 texts in under 2 seconds

    def test_extract_all_performance(self):
        """Test performance of extract_all function."""
        # Create text with multiple JSON objects
        text_parts = []
        for i in range(50):
            text_parts.append(f'{{"item_{i}": "value_{i}"}}')
        
        text = " ".join(text_parts)
        
        start_time = time.time()
        extractions = extract_all(text)
        end_time = time.time()
        
        assert len(extractions) == 50
        assert (end_time - start_time) < 1.0  # Should extract 50 objects quickly

    def test_parser_reuse_performance(self):
        """Test performance when reusing parser instances."""
        parser = RobustJSONParser()
        json_strings = [f'{{"id": {i}, "value": "test_{i}"}}' for i in range(1000)]
        
        start_time = time.time()
        results = []
        for json_str in json_strings:
            result = parser.parse_first(json_str)
            results.append(result)
        end_time = time.time()
        
        assert len(results) == 1000
        assert (end_time - start_time) < 1.5  # Should be efficient with parser reuse

    def test_memory_usage_large_dataset(self):
        """Test memory usage with large datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create and parse large dataset
        large_objects = []
        for i in range(10000):
            obj = {
                "id": i,
                "data": "x" * 100,  # 100 char string
                "nested": {
                    "value": i * 2,
                    "text": f"text_{i}"
                }
            }
            large_objects.append(json.dumps(obj))
        
        results = []
        for obj_str in large_objects:
            result = loads(obj_str)
            results.append(result)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        assert len(results) == 10000
        assert memory_increase < 100  # Should not use more than 100MB additional memory


class TestPerformanceRegression:
    """Test for performance regressions."""

    def test_basic_parsing_speed(self):
        """Test that basic parsing is fast."""
        json_str = '{"name": "test", "value": 42}'
        
        start_time = time.time()
        for _ in range(10000):
            result = loads(json_str)
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / 10000
        
        assert avg_time < 0.001  # Should parse in under 1ms on average
        assert total_time < 10.0  # 10k operations should complete in under 10 seconds

    def test_complex_parsing_speed(self):
        """Test that complex parsing is reasonably fast."""
        complex_json = '''
        {
            "users": [
                {"id": 1, "name": "Alice", "profile": {"age": 30, "city": "NYC"}},
                {"id": 2, "name": "Bob", "profile": {"age": 25, "city": "LA"}}
            ],
            "metadata": {"total": 2, "version": "1.0"}
        }
        '''
        
        start_time = time.time()
        for _ in range(1000):
            result = loads(complex_json)
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / 1000
        
        assert avg_time < 0.01  # Should parse in under 10ms on average
        assert total_time < 10.0  # 1k operations should complete in under 10 seconds


if __name__ == "__main__":
    # Run performance tests
    import json
    pytest.main([__file__, "-v"])

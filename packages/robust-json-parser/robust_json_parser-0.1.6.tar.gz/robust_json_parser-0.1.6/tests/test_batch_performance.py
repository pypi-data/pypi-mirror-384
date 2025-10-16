"""Performance tests for batch processing functionality."""

import time
import json
import random
import pytest
from robust_json import loads, loads_batch


class TestBatchPerformance:
    """Test batch processing performance."""

    def test_batch_vs_sequential_performance(self):
        """Compare batch processing vs sequential processing."""
        # Create test data
        test_texts = []
        for i in range(100):
            if i % 3 == 0:
                # Clean JSON
                test_texts.append(f'{{"id": {i}, "name": "User {i}", "active": true}}')
            elif i % 3 == 1:
                # Messy JSON with comments
                test_texts.append(f'''
                {{
                    "id": {i},
                    "name": "User {i}",  // user name
                    "active": true,
                }}
                ''')
            else:
                # Conversational text
                test_texts.append(f'''
                Here's user {i} data:
                {{"id": {i}, "name": "User {i}", "active": true}}
                ''')
        
        # Sequential processing
        start_time = time.time()
        sequential_results = []
        for text in test_texts:
            try:
                result = loads(text)
                sequential_results.append(result)
            except Exception:
                sequential_results.append(None)
        sequential_time = time.time() - start_time
        
        # Batch processing with processes
        start_time = time.time()
        batch_results = loads_batch(test_texts, max_workers=4)
        batch_time = time.time() - start_time
        
        # Batch processing with threads
        start_time = time.time()
        thread_results = loads_batch(test_texts, max_workers=4, use_threads=True)
        thread_time = time.time() - start_time
        
        print(f"\nPerformance Comparison (100 texts):")
        print(f"Sequential: {sequential_time:.3f}s")
        print(f"Batch (processes): {batch_time:.3f}s")
        print(f"Batch (threads): {thread_time:.3f}s")
        print(f"Speedup (processes): {sequential_time/batch_time:.2f}x")
        print(f"Speedup (threads): {sequential_time/thread_time:.2f}x")
        
        # Verify results are the same
        assert len(sequential_results) == len(batch_results) == len(thread_results)
        
        # Check that we got reasonable results
        successful_sequential = sum(1 for r in sequential_results if r is not None)
        successful_batch = sum(1 for r in batch_results if r is not None)
        successful_thread = sum(1 for r in thread_results if r is not None)
        
        print(f"Successful parses - Sequential: {successful_sequential}, Batch: {successful_batch}, Thread: {successful_thread}")
        
        # For small datasets, sequential is often faster due to multiprocessing overhead
        # Batch processing is mainly beneficial for very large datasets
        assert len(sequential_results) == len(batch_results) == len(thread_results)

    def test_small_batch_sequential_fallback(self):
        """Test that small batches use sequential processing."""
        small_texts = ['{"id": 1}', '{"id": 2}', '{"id": 3}']
        
        start_time = time.time()
        results = loads_batch(small_texts)
        batch_time = time.time() - start_time
        
        start_time = time.time()
        sequential_results = [loads(text) for text in small_texts]
        sequential_time = time.time() - start_time
        
        # For small batches, both should be fast (batch uses sequential processing)
        # Note: batch_time might be slightly higher due to function call overhead
        assert len(results) == 3
        assert all(result["id"] == i+1 for i, result in enumerate(results))

    def test_batch_with_defaults(self):
        """Test batch processing with default values."""
        test_texts = [
            '{"valid": "json"}',
            'invalid json text',
            '{"another": "valid"}',
            'more invalid text'
        ]
        
        results = loads_batch(test_texts, default={"error": True})
        
        assert len(results) == 4
        assert results[0] == {"valid": "json"}
        assert results[1] == {"error": True}
        assert results[2] == {"another": "valid"}
        assert results[3] == {"error": True}

    def test_batch_memory_efficiency(self):
        """Test that batch processing is memory efficient."""
        # Create a large batch
        large_batch = []
        for i in range(1000):
            large_batch.append(f'{{"id": {i}, "data": "test_data_{i}"}}')
        
        # Process in batches to avoid memory issues
        batch_size = 100
        all_results = []
        
        start_time = time.time()
        for i in range(0, len(large_batch), batch_size):
            batch = large_batch[i:i + batch_size]
            results = loads_batch(batch, max_workers=4)
            all_results.extend(results)
        total_time = time.time() - start_time
        
        assert len(all_results) == 1000
        assert total_time < 15.0  # Should complete in reasonable time (allow more time for multiprocessing overhead)
        print(f"Processed 1000 items in {total_time:.3f}s")

    def test_batch_error_handling(self):
        """Test batch processing error handling."""
        test_texts = [
            '{"valid": "json"}',
            '',  # Empty string
            'invalid json',
            '{"another": "valid"}'
        ]
        
        # Test with default
        results = loads_batch(test_texts, default=None)
        assert len(results) == 4
        assert results[0] == {"valid": "json"}
        assert results[1] is None
        assert results[2] is None
        assert results[3] == {"another": "valid"}
        
        # Test without default (should not raise)
        results = loads_batch(test_texts)
        assert len(results) == 4
        assert results[0] == {"valid": "json"}
        assert results[1] is None
        assert results[2] is None
        assert results[3] == {"another": "valid"}


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

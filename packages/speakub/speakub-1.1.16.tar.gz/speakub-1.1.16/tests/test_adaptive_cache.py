
#!/usr/bin/env python3
"""
Unit tests for AdaptiveCache functionality.
"""

import time
import unittest

from speakub.core.content_renderer import AdaptiveCache


class TestAdaptiveCache(unittest.TestCase):
    """Test cases for AdaptiveCache."""

    def test_basic_cache_operations(self):
        """Test basic get/set operations."""
        cache = AdaptiveCache(max_size=3, ttl=300)

        # Test set and get
        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")

        # Test non-existent key
        self.assertIsNone(cache.get("nonexistent"))

        # Test statistics
        stats = cache.get_stats()
        self.assertEqual(stats["size"], 1)
        self.assertEqual(stats["max_size"], 3)
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertAlmostEqual(stats["hit_rate"], 0.5)

    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = AdaptiveCache(max_size=2, ttl=300)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1

        self.assertIsNone(cache.get("key1"))  # Evicted
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")

    def test_ttl_expiration(self):
        """Test TTL-based expiration."""
        cache = AdaptiveCache(max_size=3, ttl=1)  # 1 second TTL

        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")

        # Wait for expiration
        time.sleep(1.1)
        self.assertIsNone(cache.get("key1"))  # Should be expired

    def test_access_time_update(self):
        """Test that access time is updated on get operations."""
        cache = AdaptiveCache(max_size=2, ttl=300)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Access key1 to make it recently used
        self.assertEqual(cache.get("key1"), "value1")

        # Add key3, should evict key2 (least recently used)
        cache.set("key3", "value3")

        self.assertEqual(cache.get("key1"), "value1")  # Still there
        self.assertIsNone(cache.get("key2"))  # Evicted
        self.assertEqual(cache.get("key3"), "value3")

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        cache = AdaptiveCache(max_size=3, ttl=300)

        # 3 hits, 2 misses
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("key2")  # miss
        cache.get("key1")  # hit
        cache.get("key3")  # miss

        stats = cache.get_stats()
        self.assertEqual(stats["hits"], 3)
        self.assertEqual(stats["misses"], 2)
        self.assertAlmostEqual(stats["hit_rate"], 0.6)


if __name__ == "__main__":
    unittest.main()

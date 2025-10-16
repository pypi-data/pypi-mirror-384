"""Tests for the cache service."""

import time
import unittest

from mvn_mcp_server.services.cache import MavenCache


class TestMavenCache(unittest.TestCase):
    """Test cases for the MavenCache class."""

    def setUp(self):
        """Set up test fixtures."""
        self.cache = MavenCache()

    def test_get_set_basic(self):
        """Test basic get/set operations."""
        # Set a value
        self.cache.set("test-key", "test-value")

        # Get the value
        value = self.cache.get("test-key")

        # Check the value
        self.assertEqual(value, "test-value")

    def test_get_nonexistent(self):
        """Test getting a nonexistent key."""
        value = self.cache.get("nonexistent-key")
        self.assertIsNone(value)

    def test_expiration(self):
        """Test cache entry expiration."""
        # Set a value with a short TTL (1 second)
        self.cache.set("short-ttl", "will-expire", ttl=1)

        # Value should be available immediately
        self.assertEqual(self.cache.get("short-ttl"), "will-expire")

        # Wait for expiration
        time.sleep(1.1)

        # Value should be None after expiration
        self.assertIsNone(self.cache.get("short-ttl"))

    def test_invalidate_specific(self):
        """Test invalidating specific cache entries."""
        # Set multiple values
        self.cache.set("user:1", "John")
        self.cache.set("user:2", "Jane")
        self.cache.set("product:1", "Laptop")

        # Invalidate user entries
        count = self.cache.invalidate(r"^user:")

        # Check that only user entries were invalidated
        self.assertEqual(count, 2)
        self.assertIsNone(self.cache.get("user:1"))
        self.assertIsNone(self.cache.get("user:2"))
        self.assertEqual(self.cache.get("product:1"), "Laptop")

    def test_invalidate_all(self):
        """Test invalidating the entire cache."""
        # Set multiple values
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")

        # Check initial cache size
        self.assertEqual(self.cache.size(), 2)

        # Invalidate all entries
        count = self.cache.invalidate()

        # Check that all entries were invalidated
        self.assertEqual(count, 2)
        self.assertEqual(self.cache.size(), 0)

    def test_cleanup(self):
        """Test cleaning up expired entries."""
        # Set values with different TTLs
        self.cache.set("expires-soon", "value1", ttl=1)
        self.cache.set("expires-later", "value2", ttl=30)

        # Wait for the first entry to expire
        time.sleep(1.1)

        # Run cleanup
        count = self.cache.cleanup()

        # Check that only the expired entry was removed
        self.assertEqual(count, 1)
        self.assertIsNone(self.cache.get("expires-soon"))
        self.assertEqual(self.cache.get("expires-later"), "value2")

    def test_cache_size(self):
        """Test the size method."""
        # Empty cache
        self.assertEqual(self.cache.size(), 0)

        # Add entries
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")

        # Check size
        self.assertEqual(self.cache.size(), 2)

        # Remove an entry
        self.cache.invalidate("key1")

        # Check updated size
        self.assertEqual(self.cache.size(), 1)


if __name__ == "__main__":
    unittest.main()

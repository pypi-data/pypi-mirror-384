"""Cache service for mvn MCP Server.

This module implements a simple in-memory caching mechanism to reduce
redundant API calls to Maven Central.
"""

import time
import re
import logging
from typing import Any, Dict, Optional, Pattern, Union

# Set up logging
logger = logging.getLogger("mvn-mcp-server")


class MavenCache:
    """Simple in-memory cache with TTL for Maven API responses.

    This cache helps reduce redundant API calls by storing responses
    with a time-to-live value. Expired entries are automatically
    invalidated upon access.
    """

    def __init__(self):
        """Initialize an empty cache."""
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a cached value if not expired.

        Args:
            key: The cache key to retrieve

        Returns:
            The cached value, or None if not found or expired
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        current_time = time.time()

        # Check if entry has expired
        if current_time > entry["expires_at"]:
            # Remove expired entry
            logger.debug(f"Cache entry for {key} has expired")
            del self._cache[key]
            return None

        logger.debug(f"Cache hit for {key}")
        return entry["value"]

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Store a value with expiration time.

        Args:
            key: The cache key
            value: The value to store
            ttl: Time-to-live in seconds (default: 300 seconds / 5 minutes)
        """
        expires_at = time.time() + ttl

        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
        }

        logger.debug(f"Cached {key} for {ttl} seconds")

    def invalidate(self, key_pattern: Optional[Union[str, Pattern]] = None) -> int:
        """Invalidate cache entries.

        Args:
            key_pattern: Optional regex pattern or string to match keys against.
                If None, invalidates the entire cache.

        Returns:
            Number of entries invalidated
        """
        if key_pattern is None:
            # Clear entire cache
            count = len(self._cache)
            self._cache.clear()
            logger.debug(f"Invalidated entire cache ({count} entries)")
            return count

        # Create compiled regex if a string pattern is provided
        if isinstance(key_pattern, str):
            pattern = re.compile(key_pattern)
        else:
            pattern = key_pattern

        # Track keys to remove (can't modify dict during iteration)
        keys_to_remove = []

        for key in self._cache.keys():
            if pattern.search(key):
                keys_to_remove.append(key)

        # Remove matched keys
        for key in keys_to_remove:
            del self._cache[key]

        logger.debug(f"Invalidated {len(keys_to_remove)} entries matching pattern")
        return len(keys_to_remove)

    def size(self) -> int:
        """Get the current size of the cache.

        Returns:
            Number of entries in the cache
        """
        return len(self._cache)

    def cleanup(self) -> int:
        """Remove all expired entries from the cache.

        Returns:
            Number of expired entries removed
        """
        current_time = time.time()
        keys_to_remove = []

        for key, entry in self._cache.items():
            if current_time > entry["expires_at"]:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._cache[key]

        logger.debug(f"Cleaned up {len(keys_to_remove)} expired cache entries")
        return len(keys_to_remove)

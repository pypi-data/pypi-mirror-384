"""
Query result caching system for ParquetFrame SQL operations.

Provides deterministic caching based on normalized SQL queries and data characteristics.
"""

import hashlib
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd


@dataclass
class CacheConfig:
    """Configuration for the SQL query cache system."""

    enabled: bool = True
    max_size: int = 128
    ttl_seconds: int | None = None  # Time to live, None for no expiration
    persist_to_disk: bool = False
    cache_directory: str | Path | None = None
    max_memory_mb: int = 512  # Maximum cache memory usage

    def __post_init__(self):
        """Validate configuration."""
        if self.max_size < 1:
            raise ValueError("max_size must be at least 1")
        if self.ttl_seconds is not None and self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive or None")
        if self.max_memory_mb < 1:
            raise ValueError("max_memory_mb must be at least 1")


@dataclass
class CacheEntry:
    """A single cache entry with metadata."""

    data: pd.DataFrame
    execution_time: float
    timestamp: float = field(default_factory=time.time)
    query: str = ""
    hit_count: int = 0
    memory_usage_mb: float = 0.0
    duckdb_profile: dict | None = None
    query_plan: str | None = None

    def __post_init__(self):
        """Calculate memory usage after initialization."""
        if self.memory_usage_mb == 0.0:
            try:
                self.memory_usage_mb = self.data.memory_usage(deep=True).sum() / (
                    1024 * 1024
                )
            except Exception:
                self.memory_usage_mb = 0.0

    @property
    def age_seconds(self) -> float:
        """Get the age of this cache entry in seconds."""
        return time.time() - self.timestamp

    def is_expired(self, ttl_seconds: int | None) -> bool:
        """Check if this cache entry has expired."""
        if ttl_seconds is None:
            return False
        return self.age_seconds > ttl_seconds


class SQLQueryCache:
    """
    Intelligent caching system for SQL query results.

    Features:
    - LRU eviction policy
    - Optional TTL (time-to-live) expiration
    - Memory usage tracking and limits
    - Deterministic cache keys based on query + data characteristics
    - Optional disk persistence
    """

    def __init__(self, config: CacheConfig | None = None):
        """Initialize the cache with given configuration."""
        self.config = config or CacheConfig()
        self._cache: dict[str, CacheEntry] = {}
        self._access_order: list[str] = []  # For LRU tracking
        self._total_memory_mb = 0.0

        if self.config.persist_to_disk and self.config.cache_directory:
            self.cache_dir = Path(self.config.cache_directory)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.cache_dir = None

    def _generate_cache_key(
        self,
        query: str,
        df_characteristics: dict,
        context_params: dict | None = None,
    ) -> str:
        """
        Generate a deterministic cache key.

        Args:
            query: Normalized SQL query string
            df_characteristics: DataFrame shape, dtypes, and sample data hash
            context_params: QueryContext parameters that affect results

        Returns:
            Hexadecimal cache key
        """
        # Normalize query (remove extra whitespace, convert to lowercase)
        normalized_query = " ".join(query.strip().lower().split())

        # Include context parameters that affect query results
        context_str = ""
        if context_params:
            # Only include parameters that could affect results
            relevant_params = {
                k: v
                for k, v in context_params.items()
                if k in ["predicate_pushdown", "projection_pushdown", "custom_pragmas"]
            }
            context_str = str(sorted(relevant_params.items()))

        # Create cache key from all components
        key_components = [
            normalized_query,
            str(sorted(df_characteristics.items())),
            context_str,
        ]
        key_data = "|".join(key_components)

        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def _get_df_characteristics(self, df: pd.DataFrame) -> dict:
        """
        Extract characteristics of a DataFrame for cache key generation.

        Args:
            df: DataFrame to analyze

        Returns:
            Dictionary with shape, dtypes, and content hash
        """
        characteristics = {
            "shape": df.shape,
            "dtypes": str(df.dtypes.to_dict()),
            "columns": sorted(df.columns.tolist()),
        }

        # Add content hash based on a sample of the data
        try:
            # Use first and last few rows to detect data changes
            sample_size = min(5, len(df))
            if sample_size > 0:
                sample_df = pd.concat(
                    [df.head(sample_size), df.tail(sample_size)]
                ).drop_duplicates()

                # Create hash from string representation
                content_str = sample_df.to_string()
                characteristics["content_hash"] = hashlib.md5(
                    content_str.encode()
                ).hexdigest()[:8]
        except Exception:
            characteristics["content_hash"] = "unknown"

        return characteristics

    def _update_access_order(self, cache_key: str):
        """Update LRU access order for a cache key."""
        if cache_key in self._access_order:
            self._access_order.remove(cache_key)
        self._access_order.append(cache_key)

    def _evict_lru(self):
        """Evict least recently used cache entries."""
        while (
            len(self._cache) >= self.config.max_size
            or self._total_memory_mb > self.config.max_memory_mb
        ):
            if not self._access_order:
                break

            lru_key = self._access_order.pop(0)
            if lru_key in self._cache:
                entry = self._cache.pop(lru_key)
                self._total_memory_mb -= entry.memory_usage_mb

    def _evict_expired(self):
        """Remove expired cache entries."""
        if self.config.ttl_seconds is None:
            return

        expired_keys = [
            key
            for key, entry in self._cache.items()
            if entry.is_expired(self.config.ttl_seconds)
        ]

        for key in expired_keys:
            entry = self._cache.pop(key, None)
            if entry:
                self._total_memory_mb -= entry.memory_usage_mb
                if key in self._access_order:
                    self._access_order.remove(key)

    def get(
        self,
        query: str,
        df_characteristics: dict,
        context_params: dict | None = None,
    ) -> CacheEntry | None:
        """
        Retrieve a cached query result.

        Args:
            query: SQL query string
            df_characteristics: DataFrame characteristics for cache key
            context_params: QueryContext parameters

        Returns:
            CacheEntry if found and valid, None otherwise
        """
        if not self.config.enabled:
            return None

        cache_key = self._generate_cache_key(query, df_characteristics, context_params)

        # Clean expired entries periodically
        self._evict_expired()

        entry = self._cache.get(cache_key)
        if entry is None:
            return None

        # Check if expired
        if entry.is_expired(self.config.ttl_seconds):
            self._cache.pop(cache_key, None)
            if cache_key in self._access_order:
                self._access_order.remove(cache_key)
            return None

        # Update access tracking
        entry.hit_count += 1
        self._update_access_order(cache_key)

        return entry

    def put(
        self,
        query: str,
        result: pd.DataFrame,
        execution_time: float,
        df_characteristics: dict,
        context_params: dict | None = None,
        duckdb_profile: dict | None = None,
        query_plan: str | None = None,
    ) -> str:
        """
        Store a query result in the cache.

        Args:
            query: SQL query string
            result: Query result DataFrame
            execution_time: Query execution time in seconds
            df_characteristics: DataFrame characteristics for cache key
            context_params: QueryContext parameters
            duckdb_profile: Optional profiling information
            query_plan: Optional query execution plan

        Returns:
            Cache key used for storage
        """
        if not self.config.enabled:
            return ""

        cache_key = self._generate_cache_key(query, df_characteristics, context_params)

        # Create cache entry
        entry = CacheEntry(
            data=result.copy(),
            execution_time=execution_time,
            query=query,
            duckdb_profile=duckdb_profile,
            query_plan=query_plan,
        )

        # Evict entries to make room if needed
        self._evict_lru()

        # Store entry
        self._cache[cache_key] = entry
        self._total_memory_mb += entry.memory_usage_mb
        self._update_access_order(cache_key)

        return cache_key

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._access_order.clear()
        self._total_memory_mb = 0.0

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_hits = sum(entry.hit_count for entry in self._cache.values())

        return {
            "enabled": self.config.enabled,
            "entries": len(self._cache),
            "max_size": self.config.max_size,
            "memory_usage_mb": round(self._total_memory_mb, 2),
            "max_memory_mb": self.config.max_memory_mb,
            "total_hits": total_hits,
            "ttl_seconds": self.config.ttl_seconds,
        }

    def get_entry_info(self) -> list[dict]:
        """Get information about all cache entries."""
        return [
            {
                "query": (
                    entry.query[:100] + "..." if len(entry.query) > 100 else entry.query
                ),
                "age_seconds": round(entry.age_seconds, 2),
                "hit_count": entry.hit_count,
                "memory_mb": round(entry.memory_usage_mb, 2),
                "execution_time": round(entry.execution_time, 4),
            }
            for entry in self._cache.values()
        ]


# Global cache instance
_global_cache: SQLQueryCache | None = None


def get_cache() -> SQLQueryCache:
    """Get or create the global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = SQLQueryCache()
    return _global_cache


def configure_cache(config: CacheConfig):
    """Configure the global cache."""
    global _global_cache
    _global_cache = SQLQueryCache(config)


def clear_cache():
    """Clear the global cache."""
    cache = get_cache()
    cache.clear()


def get_cache_stats() -> dict:
    """Get global cache statistics."""
    cache = get_cache()
    return cache.get_stats()


@lru_cache(maxsize=256)
def normalize_query(query: str) -> str:
    """
    Normalize a SQL query for consistent caching.

    Args:
        query: Raw SQL query string

    Returns:
        Normalized query string
    """
    # Remove comments and normalize whitespace
    lines = []
    for line in query.split("\n"):
        line = line.strip()
        if line and not line.startswith("--"):
            lines.append(line)

    # Join and normalize whitespace
    normalized = " ".join(" ".join(lines).split())

    return normalized.upper()

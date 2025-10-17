"""
DuckDB-based caching layer for API responses.

Provides intelligent caching with configurable TTL, cache invalidation,
and statistics tracking to reduce API calls and improve performance.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, cast

try:
    import duckdb
except ImportError:
    duckdb = None  # type: ignore

from functools import wraps

logger = logging.getLogger(__name__)

# Type variable for generic function return types
T = TypeVar("T")


class CacheManager:
    """
    Manages API response caching with DuckDB backend.

    Features:
    - Per-source TTL configuration
    - Automatic cache invalidation
    - Hit/miss statistics tracking
    - Thread-safe operations
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        default_ttl_seconds: int = 3600,
    ):
        """
        Initialize cache manager.

        Args:
            db_path: Path to DuckDB database file. If None, uses in-memory DB.
            default_ttl_seconds: Default cache TTL in seconds (1 hour default).
        """
        if duckdb is None:
            raise ImportError(
                "duckdb is required for caching. Install with: pip install duckdb"
            )

        self.db_path = db_path or ":memory:"
        self.default_ttl_seconds = default_ttl_seconds
        self.conn = duckdb.connect(str(self.db_path))

        # Source-specific TTL configuration (in seconds)
        self.source_ttls = {
            # Real-time data - short TTL
            "yahoo_finance": 60,  # 1 minute
            "finnhub": 60,  # 1 minute
            "alpha_vantage": 300,  # 5 minutes
            "tiingo": 300,  # 5 minutes
            # Fundamental data - medium TTL
            "fmp": 3600,  # 1 hour
            "sec_edgar": 3600,  # 1 hour
            # Economic data - longer TTL
            "fred": 86400,  # 24 hours
            "treasury": 86400,  # 24 hours
            # News - short TTL
            "newsapi": 300,  # 5 minutes
            # File operations - no caching
            "file_reader": 0,  # Never cache
        }

        self._initialize_schema()
        logger.info(
            f"CacheManager initialized with db_path={self.db_path}, "
            f"default_ttl={default_ttl_seconds}s"
        )

    def _initialize_schema(self) -> None:
        """Create cache tables if they don't exist."""
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache_entries (
                cache_key VARCHAR PRIMARY KEY,
                source VARCHAR NOT NULL,
                tool_name VARCHAR NOT NULL,
                args_hash VARCHAR NOT NULL,
                response TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                hits INTEGER DEFAULT 0
            )
        """
        )

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache_statistics (
                source VARCHAR NOT NULL,
                tool_name VARCHAR NOT NULL,
                date DATE NOT NULL,
                hits INTEGER DEFAULT 0,
                misses INTEGER DEFAULT 0,
                PRIMARY KEY (source, tool_name, date)
            )
        """
        )

        # Create indices for faster lookups
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_cache_entries_expires
            ON cache_entries(expires_at)
        """
        )

        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_cache_entries_source
            ON cache_entries(source, tool_name)
        """
        )

        logger.debug("Cache schema initialized")

    def _generate_cache_key(
        self, source: str, tool_name: str, args: tuple, kwargs: dict
    ) -> str:
        """
        Generate deterministic cache key from function arguments.

        Args:
            source: Data source name (e.g., 'yahoo_finance')
            tool_name: Tool function name (e.g., 'get_quote')
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            SHA256 hash as cache key
        """
        # Create deterministic representation of arguments
        args_repr = json.dumps(
            {"args": args, "kwargs": sorted(kwargs.items())},
            sort_keys=True,
            default=str,
        )

        # Generate hash
        args_hash = hashlib.sha256(args_repr.encode()).hexdigest()

        # Combine source, tool, and hash for uniqueness
        cache_key = f"{source}:{tool_name}:{args_hash}"

        return cache_key

    def get(
        self, source: str, tool_name: str, args: tuple, kwargs: dict
    ) -> Optional[Any]:
        """
        Retrieve cached response if available and not expired.

        Args:
            source: Data source name
            tool_name: Tool function name
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Cached response if available, None if cache miss or expired
        """
        cache_key = self._generate_cache_key(source, tool_name, args, kwargs)

        try:
            result = self.conn.execute(
                """
                SELECT response, expires_at
                FROM cache_entries
                WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP
            """,
                [cache_key],
            ).fetchone()

            if result:
                response_json, expires_at = result

                # Update hit count
                self.conn.execute(
                    """
                    UPDATE cache_entries
                    SET hits = hits + 1
                    WHERE cache_key = ?
                """,
                    [cache_key],
                )

                # Record cache hit
                self._record_statistics(source, tool_name, hit=True)

                logger.debug(
                    f"Cache HIT: {source}.{tool_name} (expires: {expires_at})"
                )
                return json.loads(response_json)

            # Record cache miss
            self._record_statistics(source, tool_name, hit=False)
            logger.debug(f"Cache MISS: {source}.{tool_name}")
            return None

        except Exception as e:
            logger.error(f"Cache retrieval error: {e}", exc_info=True)
            return None

    def set(
        self,
        source: str,
        tool_name: str,
        args: tuple,
        kwargs: dict,
        response: Any,
    ) -> None:
        """
        Store response in cache with appropriate TTL.

        Args:
            source: Data source name
            tool_name: Tool function name
            args: Positional arguments
            kwargs: Keyword arguments
            response: Response to cache
        """
        # Check if this source should be cached
        ttl_seconds = self.source_ttls.get(source, self.default_ttl_seconds)

        if ttl_seconds == 0:
            logger.debug(f"Caching disabled for source: {source}")
            return

        cache_key = self._generate_cache_key(source, tool_name, args, kwargs)
        args_hash = hashlib.sha256(
            json.dumps(
                {"args": args, "kwargs": sorted(kwargs.items())},
                sort_keys=True,
                default=str,
            ).encode()
        ).hexdigest()

        now = datetime.now()
        expires_at = now + timedelta(seconds=ttl_seconds)

        try:
            # Serialize response
            response_json = json.dumps(response, default=str)

            # Upsert cache entry
            self.conn.execute(
                """
                INSERT INTO cache_entries (
                    cache_key, source, tool_name, args_hash,
                    response, created_at, expires_at, hits
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT (cache_key)
                DO UPDATE SET
                    response = excluded.response,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at
            """,
                [
                    cache_key,
                    source,
                    tool_name,
                    args_hash,
                    response_json,
                    now,
                    expires_at,
                ],
            )

            logger.debug(
                f"Cache SET: {source}.{tool_name} (TTL: {ttl_seconds}s, expires: {expires_at})"
            )

        except Exception as e:
            logger.error(f"Cache storage error: {e}", exc_info=True)

    def _record_statistics(self, source: str, tool_name: str, hit: bool) -> None:
        """
        Record cache hit/miss statistics.

        Args:
            source: Data source name
            tool_name: Tool function name
            hit: True for cache hit, False for cache miss
        """
        try:
            today = datetime.now().date()

            if hit:
                self.conn.execute(
                    """
                    INSERT INTO cache_statistics (source, tool_name, date, hits, misses)
                    VALUES (?, ?, ?, 1, 0)
                    ON CONFLICT (source, tool_name, date)
                    DO UPDATE SET hits = cache_statistics.hits + 1
                """,
                    [source, tool_name, today],
                )
            else:
                self.conn.execute(
                    """
                    INSERT INTO cache_statistics (source, tool_name, date, misses, hits)
                    VALUES (?, ?, ?, 1, 0)
                    ON CONFLICT (source, tool_name, date)
                    DO UPDATE SET misses = cache_statistics.misses + 1
                """,
                    [source, tool_name, today],
                )

        except Exception as e:
            logger.error(f"Statistics recording error: {e}", exc_info=True)

    def invalidate(
        self, source: Optional[str] = None, tool_name: Optional[str] = None
    ) -> int:
        """
        Invalidate cache entries matching criteria.

        Args:
            source: If provided, invalidate only this source
            tool_name: If provided, invalidate only this tool

        Returns:
            Number of entries invalidated
        """
        try:
            if source and tool_name:
                result = self.conn.execute(
                    "DELETE FROM cache_entries WHERE source = ? AND tool_name = ?",
                    [source, tool_name],
                )
            elif source:
                result = self.conn.execute(
                    "DELETE FROM cache_entries WHERE source = ?", [source]
                )
            elif tool_name:
                result = self.conn.execute(
                    "DELETE FROM cache_entries WHERE tool_name = ?", [tool_name]
                )
            else:
                result = self.conn.execute("DELETE FROM cache_entries")

            count = result.fetchone()[0] if result else 0
            logger.info(
                f"Invalidated {count} cache entries (source={source}, tool={tool_name})"
            )
            return count

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}", exc_info=True)
            return 0

    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        try:
            result = self.conn.execute(
                "DELETE FROM cache_entries WHERE expires_at <= CURRENT_TIMESTAMP"
            )
            count = result.fetchone()[0] if result else 0

            if count > 0:
                logger.info(f"Cleaned up {count} expired cache entries")

            return count

        except Exception as e:
            logger.error(f"Cache cleanup error: {e}", exc_info=True)
            return 0

    def get_statistics(
        self, source: Optional[str] = None, days: int = 7
    ) -> dict[str, Any]:
        """
        Retrieve cache performance statistics.

        Args:
            source: If provided, filter statistics by source
            days: Number of days to include (default: 7)

        Returns:
            Dictionary with cache statistics
        """
        try:
            cutoff_date = datetime.now().date() - timedelta(days=days)

            if source:
                query = """
                    SELECT
                        source,
                        tool_name,
                        SUM(hits) as total_hits,
                        SUM(misses) as total_misses,
                        ROUND(SUM(hits) * 100.0 / (SUM(hits) + SUM(misses)), 2) as hit_rate
                    FROM cache_statistics
                    WHERE source = ? AND date >= ?
                    GROUP BY source, tool_name
                    ORDER BY total_hits DESC
                """
                results = self.conn.execute(query, [source, cutoff_date]).fetchall()
            else:
                query = """
                    SELECT
                        source,
                        tool_name,
                        SUM(hits) as total_hits,
                        SUM(misses) as total_misses,
                        ROUND(SUM(hits) * 100.0 / (SUM(hits) + SUM(misses)), 2) as hit_rate
                    FROM cache_statistics
                    WHERE date >= ?
                    GROUP BY source, tool_name
                    ORDER BY total_hits DESC
                """
                results = self.conn.execute(query, [cutoff_date]).fetchall()

            # Get cache size
            cache_size = self.conn.execute(
                "SELECT COUNT(*) FROM cache_entries"
            ).fetchone()[0]

            # Build statistics dict
            stats = {
                "cache_size": cache_size,
                "days": days,
                "by_tool": [
                    {
                        "source": row[0],
                        "tool_name": row[1],
                        "hits": row[2],
                        "misses": row[3],
                        "hit_rate": row[4],
                    }
                    for row in results
                ],
            }

            # Calculate overall hit rate
            total_hits = sum(tool["hits"] for tool in stats["by_tool"])
            total_misses = sum(tool["misses"] for tool in stats["by_tool"])
            total_requests = total_hits + total_misses

            if total_requests > 0:
                stats["overall_hit_rate"] = round(
                    total_hits * 100.0 / total_requests, 2
                )
            else:
                stats["overall_hit_rate"] = 0.0

            stats["total_hits"] = total_hits
            stats["total_misses"] = total_misses

            return stats

        except Exception as e:
            logger.error(f"Statistics retrieval error: {e}", exc_info=True)
            return {
                "cache_size": 0,
                "days": days,
                "by_tool": [],
                "overall_hit_rate": 0.0,
                "total_hits": 0,
                "total_misses": 0,
            }

    async def warm_cache(self, queries: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Warm the cache by pre-populating it with common queries.

        This method executes a list of common queries to populate the cache,
        improving initial user experience by reducing API calls for frequently
        accessed data.

        Args:
            queries: List of query dictionaries, each containing:
                - source: Data source name (e.g., 'yahoo_finance')
                - tool_name: Tool function name (e.g., 'get_quote')
                - args: Tuple of positional arguments
                - kwargs: Dict of keyword arguments
                - func: Async function to call for cache miss

        Returns:
            Dictionary with warming statistics:
                - total: Total queries attempted
                - cached: Number already cached (skipped)
                - warmed: Number newly cached
                - failed: Number that failed

        Example:
            queries = [
                {
                    "source": "yahoo_finance",
                    "tool_name": "get_quote",
                    "args": ("AAPL",),
                    "kwargs": {},
                    "func": get_quote_cached
                },
                {
                    "source": "treasury",
                    "tool_name": "get_treasury_yield_curve",
                    "args": (),
                    "kwargs": {},
                    "func": get_treasury_yield_curve_cached
                }
            ]
            stats = await cache.warm_cache(queries)
        """
        import asyncio

        stats = {
            "total": len(queries),
            "cached": 0,
            "warmed": 0,
            "failed": 0,
        }

        for query in queries:
            source = query["source"]
            tool_name = query["tool_name"]
            args = query.get("args", ())
            kwargs = query.get("kwargs", {})
            func = query["func"]

            try:
                # Check if already cached
                cached_response = self.get(source, tool_name, args, kwargs)

                if cached_response is not None:
                    stats["cached"] += 1
                    logger.debug(
                        f"Cache warm: {source}.{tool_name} already cached (skipped)"
                    )
                    continue

                # Execute the function to populate cache
                if asyncio.iscoroutinefunction(func):
                    response = await func(*args, **kwargs)
                else:
                    response = func(*args, **kwargs)

                # Store in cache
                self.set(source, tool_name, args, kwargs, response)
                stats["warmed"] += 1
                logger.info(f"Cache warm: {source}.{tool_name} populated")

            except Exception as e:
                stats["failed"] += 1
                logger.error(
                    f"Cache warm failed for {source}.{tool_name}: {str(e)}",
                    exc_info=True,
                )

        logger.info(
            f"Cache warming complete: {stats['warmed']} warmed, "
            f"{stats['cached']} already cached, {stats['failed']} failed"
        )

        return stats

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Cache manager connection closed")


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(
    db_path: Optional[Path] = None, default_ttl_seconds: int = 3600
) -> CacheManager:
    """
    Get or create global cache manager instance.

    Args:
        db_path: Path to DuckDB database file
        default_ttl_seconds: Default cache TTL

    Returns:
        CacheManager instance
    """
    global _cache_manager

    if _cache_manager is None:
        # Use persistent cache in user's home directory
        if db_path is None:
            cache_dir = Path.home() / ".navam-invest" / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = cache_dir / "api_cache.duckdb"

        _cache_manager = CacheManager(db_path, default_ttl_seconds)

    return _cache_manager


def cached(source: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to cache function results with DuckDB backend.

    Supports both synchronous and asynchronous functions.

    Usage:
        @cached(source="yahoo_finance")
        def get_quote(symbol: str) -> dict:
            # Expensive API call
            return api.get_quote(symbol)

        @cached(source="fred")
        async def get_indicator(series_id: str) -> dict:
            # Async API call
            return await api.get_indicator(series_id)

    Args:
        source: Data source name for TTL configuration

    Returns:
        Decorated function with caching
    """
    import asyncio
    import inspect

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Check if function is async
        is_async = inspect.iscoroutinefunction(func)

        if is_async:
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                cache = get_cache_manager()
                tool_name = func.__name__

                # Try to get from cache
                cached_response = cache.get(source, tool_name, args, kwargs)

                if cached_response is not None:
                    return cast(T, cached_response)

                # Cache miss - call original async function
                response = await func(*args, **kwargs)

                # Store in cache
                cache.set(source, tool_name, args, kwargs, response)

                return response

            return cast(Callable[..., T], async_wrapper)
        else:
            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> T:
                cache = get_cache_manager()
                tool_name = func.__name__

                # Try to get from cache
                cached_response = cache.get(source, tool_name, args, kwargs)

                if cached_response is not None:
                    return cast(T, cached_response)

                # Cache miss - call original function
                response = func(*args, **kwargs)

                # Store in cache
                cache.set(source, tool_name, args, kwargs, response)

                return response

            return cast(Callable[..., T], sync_wrapper)

    return decorator

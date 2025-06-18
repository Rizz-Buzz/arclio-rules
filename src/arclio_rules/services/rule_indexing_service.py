import hashlib
import json
import os
from typing import Any, Callable

import redis
from fastapi import HTTPException
from loguru import logger

from arclio_rules.services.rule_fetching_service import RuleFetchingService


class RuleIndexingService:
    """Service to cache results of RuleFetchingService operations in Redis."""

    def __init__(self, max_cache_size: int = 1000, ttl_seconds: int = 3600):
        """Initialize the Redis cache service.

        Args:
            max_cache_size (int): Maximum number of items to store in cache (enforced by Redis LRU).
            ttl_seconds (int): Time-to-live for cached items in seconds (default: 1 hour).
        """  # noqa: E501
        self.max_cache_size = max_cache_size
        self.ttl_seconds = ttl_seconds
        self.fetcher = RuleFetchingService()

        # Initialize Redis connection
        redis_host = os.environ.get("REDIS_HOST", "localhost")
        redis_port = int(os.environ.get("REDIS_PORT", 6379))
        redis_password = os.environ.get("REDIS_PASSWORD")
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise Exception(f"Redis connection failed: {str(e)}")
        logger.info(
            f"Initialized RuleIndexingService with max_cache_size={max_cache_size}, ttl_seconds={ttl_seconds}"  # noqa: E501
        )

    def _generate_cache_key(self, method: str, **params: Any) -> str:
        """Generate a unique cache key based on method name and parameters.

        Args:
            method (str): The name of the RuleFetchingService method (e.g., 'list_all_companies').
            **params: Keyword arguments for the method (e.g., company, category, rule).

        Returns:
            str: A unique SHA-256 hash for the cache key.
        """  # noqa: E501
        params_str = "&".join(f"{k}={str(v)}" for k, v in sorted(params.items()))
        key_input = f"{method}:{params_str}"
        cache_key = hashlib.sha256(key_input.encode()).hexdigest()
        logger.debug(
            f"Generated cache key: {cache_key} for method={method}, params={params}"
        )
        return cache_key

    def _get_cached_or_fetch(
        self, method: str, fetch_func: Callable[..., Any], **params: Any
    ) -> Any:
        """Retrieve data from Redis cache or fetch using the provided function.

        Args:
            method (str): The name of the method to cache (e.g., 'list_all_companies').
            fetch_func (callable): The RuleFetchingService method to call on cache miss.
            **params: Parameters to pass to the fetch function and for cache key generation.

        Returns:
            Any: The cached or fetched data.
        """  # noqa: E501
        cache_key = self._generate_cache_key(method, **params)

        # Check Redis cache
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                logger.info(
                    f"Cache hit for {method} with params {params}, key={cache_key}"
                )
                return json.loads(
                    cached_data
                )  # pyright: ignore[reportArgumentType]  # noqa: E501
        except redis.RedisError as e:
            logger.error(f"Redis error while checking cache for {cache_key}: {str(e)}")
            # Fall through to fetch on Redis error

        # Cache miss or Redis error
        logger.info(f"Cache miss for {method} with params {params}, key={cache_key}")
        try:
            data = fetch_func(**params)
        except HTTPException as e:
            logger.error(f"Failed to fetch data for {method}: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {method}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

        # Store in Redis with TTL
        try:
            # Check approximate cache size
            cache_size = self.redis_client.dbsize()
            if int(cache_size) >= self.max_cache_size:  # type: ignore[reportArgumentType]  # noqa: E501
                logger.warning(
                    f"Redis cache size {cache_size} reached max_cache_size={self.max_cache_size}. Relying on LRU eviction."  # noqa: E501
                )
            self.redis_client.setex(
                name=cache_key,
                time=self.ttl_seconds,
                value=json.dumps(data, default=str),  # Serialize data to JSON
            )
            logger.debug(f"Cached data for {method} with key={cache_key}")
        except redis.RedisError as e:
            logger.error(f"Failed to cache data for {cache_key}: {str(e)}")
            # Continue without caching to avoid blocking the request

        return data

    def list_all_companies(self) -> list[str]:
        """List all company directories under rules/, with caching.

        Returns:
            list[str]: A list of company names.
        """
        return self._get_cached_or_fetch(
            method="list_all_companies", fetch_func=self.fetcher.list_all_companies
        )

    def list_company_categories(self, company: str) -> list[str]:
        """List all categories for a specific company, with caching.

        Args:
            company (str): The name of the company.

        Returns:
            list[str]: A a list of category names.
        """
        return self._get_cached_or_fetch(
            method="list_company_categories",
            fetch_func=self.fetcher.list_company_categories,
            company=company,
        )

    def list_category_rules(self, company: str, category: str) -> list[str]:
        """List all .mdc rules in a specific company category, with caching.

        Args:
            company (str): The name of the company.
            category (str): The name of the category.

        Returns:
            list[str]: A list of rule names (without .mdc extension).
        """
        return self._get_cached_or_fetch(
            method="list_category_rules",
            fetch_func=self.fetcher.list_category_rules,
            company=company,
            category=category,
        )

    def get_rule(
        self, company: str, category: str, rule: str, is_main_rule: bool = False
    ) -> dict:
        """Fetch the content of a specific .mdc rule file, with caching.

        Args:
            company (str): The name of the company.
            category (str): The category of the rule.
            rule (str): The name of the rule (without .mdc extension).
            is_main_rule (bool): Whether the rule is the main rule (index.mdc).

        Returns:
            dict: A dictionary containing the rule content and metadata.
        """
        return self._get_cached_or_fetch(
            method="get_rule",
            fetch_func=self.fetcher.get_rule,
            company=company,
            category=category,
            rule=rule,
            is_main_rule=is_main_rule,
        )

    def invalidate_cache(self, method: str, **params: Any):
        """Invalidate a specific cache entry in Redis.

        Args:
            method (str): The name of the method to invalidate (e.g., 'list_all_companies').
            **params: Parameters used to generate the cache key.
        """  # noqa: E501
        cache_key = self._generate_cache_key(method, **params)
        try:
            if self.redis_client.exists(cache_key):
                self.redis_client.delete(cache_key)
                logger.info(
                    f"Invalidated cache for {method} with params {params}, key={cache_key}"  # noqa: E501
                )
            else:
                logger.debug(
                    f"No cache entry to invalidate for {method}, key={cache_key}"
                )
        except redis.RedisError as e:
            logger.error(f"Failed to invalidate cache for {cache_key}: {str(e)}")

import hashlib
import threading
import time
from typing import Any, Callable, Dict, List

from fastapi import HTTPException
from loguru import logger

from arclio_rules.services.rule_fetching_service import RuleFetchingService


class RuleIndexingService:
    """Service to cache results of RuleFetchingService operations in memory."""

    def __init__(
        self, config: Dict, max_cache_size: int = 1000, ttl_seconds: int = 300
    ):
        """Initialize the in-memory cache service.

        Args:
            config (Dict): Configuration dictionary for RuleFetchingService.
            max_cache_size (int): Maximum number of items to store in cache (LRU).
            ttl_seconds (int): Time-to-live for cached items in seconds (default: 5 minutes).
        """  # noqa: E501
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_cache_size = max_cache_size
        self.ttl_seconds = ttl_seconds
        self.lock = threading.Lock()
        self.fetcher = RuleFetchingService(config)
        self.access_times: Dict[str, float] = {}  # Track access times for LRU
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

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if a cache entry is still valid based on TTL.

        Args:
            cache_entry (Dict[str, Any]): The cache entry with data and timestamp.

        Returns:
            bool: True if the entry is valid, False if expired.
        """
        is_valid = time.time() - cache_entry["timestamp"] < self.ttl_seconds
        logger.debug(
            f"Cache entry valid: {is_valid}, age={time.time() - cache_entry['timestamp']} seconds"
        )
        return is_valid

    def _evict_oldest(self):
        """Evict the least recently used item if cache is full."""
        if len(self.cache) >= self.max_cache_size:
            oldest_key = min(self.access_times, key=self.access_times.get)
            with self.lock:
                logger.info(f"Evicting oldest cache entry: {oldest_key}")
                self.cache.pop(oldest_key, None)
                self.access_times.pop(oldest_key, None)

    def _get_cached_or_fetch(
        self, method: str, fetch_func: Callable[..., Any], **params: Any
    ) -> Any:
        """Retrieve data from cache or fetch using the provided function.

        Args:
            method (str): The name of the method to cache (e.g., 'list_all_companies').
            fetch_func (callable): The RuleFetchingService method to call on cache miss.
            **params: Parameters to pass to the fetch function and for cache key generation.

        Returns:
            Any: The cached or fetched data.
        """  # noqa: E501
        cache_key = self._generate_cache_key(method, **params)

        with self.lock:
            if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
                logger.info(
                    f"Cache hit for {method} with params {params}, key={cache_key}"
                )
                self.access_times[cache_key] = time.time()
                return self.cache[cache_key]["data"]

        logger.info(f"Cache miss for {method} with params {params}, key={cache_key}")
        try:
            data = fetch_func(**params)
        except HTTPException as e:
            logger.error(f"Failed to fetch data for {method}: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {method}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

        with self.lock:
            self._evict_oldest()
            logger.debug(f"Caching data for {method} with key={cache_key}")
            self.cache[cache_key] = {"data": data, "timestamp": time.time()}
            self.access_times[cache_key] = time.time()

        return data

    def list_all_companies(self) -> List[str]:
        """List all company directories under rules/, with caching.

        Returns:
            List[str]: A list of company names.
        """
        return self._get_cached_or_fetch(
            method="list_all_companies", fetch_func=self.fetcher.list_all_companies
        )

    def list_company_categories(self, company: str) -> List[str]:
        """List all categories for a specific company, with caching.

        Args:
            company (str): The name of the company.

        Returns:
            List[str]: A list of category names.
        """
        return self._get_cached_or_fetch(
            method="list_company_categories",
            fetch_func=self.fetcher.list_company_categories,
            company=company,
        )

    def list_category_rules(self, company: str, category: str) -> List[str]:
        """List all .mdc rules in a specific company category, with caching.

        Args:
            company (str): The name of the company.
            category (str): The name of the category.

        Returns:
            List[str]: A list of rule names (without .mdc extension).
        """
        return self._get_cached_or_fetch(
            method="list_category_rules",
            fetch_func=self.fetcher.list_category_rules,
            company=company,
            category=category,
        )

    def get_rule(
        self, company: str, category: str, rule: str, is_main_rule: bool = False
    ) -> Dict:
        """Fetch the content of a specific .mdc rule file, with caching.

        Args:
            company (str): The name of the company.
            category (str): The category of the rule.
            rule (str): The name of the rule (without .mdc extension).
            is_main_rule (bool): Whether the rule is the main rule (index.mdc).

        Returns:
            Dict: A dictionary containing the rule content and metadata.
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
        """Invalidate a specific cache entry.

        Args:
            method (str): The name of the method to invalidate (e.g., 'list_all_companies'). # noqa: E501
            **params: Parameters used to generate the cache key.
        """
        cache_key = self._generate_cache_key(method, **params)
        with self.lock:
            if cache_key in self.cache:
                logger.info(
                    f"Invalidating cache for {method} with params {params}, key={cache_key}"  # noqa: E501
                )
                self.cache.pop(cache_key, None)
                self.access_times.pop(cache_key, None)

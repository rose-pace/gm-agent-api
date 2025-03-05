from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple, OrderedDict
from collections import OrderedDict

class CacheEntry:
    """
    Represents a single cached query result with expiration.
    """
    def __init__(self, query: str, results: List[Any], ttl_seconds: int):
        """
        Initialize a new cache entry.
        
        Args:
            query: The query string that was executed
            results: The results that were returned
            ttl_seconds: Time-to-live in seconds
        """
        self.query = query
        self.results = results
        self.expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        self.last_accessed = datetime.now(timezone.utc)
    
    def is_expired(self) -> bool:
        """
        Check if this cache entry has expired.
        
        Returns:
            True if the entry has expired, False otherwise
        """
        return datetime.now(timezone.utc) > self.expiry
    
    def update_access_time(self) -> None:
        """
        Update the last access time to now.
        """
        self.last_accessed = datetime.now(timezone.utc)

class QueryCache:
    """
    Cache for storing and retrieving query results with LRU eviction.
    """
    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        """
        Initialize the query cache.
        
        Args:
            ttl_seconds: Default time-to-live for cache entries in seconds
            max_size: Maximum number of items to keep in cache
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
    
    def get(self, query: str, metadata_filter: Optional[Dict[str, Any]] = None) -> Optional[List[Any]]:
        """
        Get cached results for a query if available and not expired.
        
        Args:
            query: The query string
            metadata_filter: Optional metadata filter applied to the query
            
        Returns:
            Cached results if available and not expired, None otherwise
        """
        cache_key = self._make_key(query, metadata_filter)
        entry = self.cache.get(cache_key)
        if entry:
            if entry.is_expired():
                # Remove expired entry
                del self.cache[cache_key]
                return None
            else:
                # Update access time for LRU tracking
                entry.update_access_time()
                return entry.results
        return None
    
    def set(self, query: str, results: List[Any], metadata_filter: Optional[Dict[str, Any]] = None) -> None:
        """
        Store results for a query in the cache.
        Enforces the maximum cache size by evicting least recently used items if needed.
        
        Args:
            query: The query string
            results: The results to cache
            metadata_filter: Optional metadata filter applied to the query
        """
        cache_key = self._make_key(query, metadata_filter)
        
        # Create the new entry
        self.cache[cache_key] = CacheEntry(query, results, self.ttl_seconds)
        
        # If we've exceeded the cache size limit, remove LRU entry
        if len(self.cache) > self.max_size:
            self._evict_lru()
    
    def _evict_lru(self) -> None:
        """
        Evict the least recently used item from the cache.
        """
        if not self.cache:
            return
            
        # Find the least recently used entry
        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].last_accessed)
        del self.cache[lru_key]
    
    def _make_key(self, query: str, metadata_filter: Optional[Dict[str, Any]]) -> str:
        """
        Create a unique cache key based on query and metadata filter.
        
        Args:
            query: The query string
            metadata_filter: Optional metadata filter
            
        Returns:
            A string key for the cache
        TODO: 
            We can improve this by using a hash function to generate a unique key
            and possibly by converting to semantically equivalent queries
        """
        if metadata_filter:
            # Convert dict to sorted, stable string representation
            metadata_str = str(sorted(metadata_filter.items()))
            return f'{query}::{metadata_str}'
        return query
    
    def clear(self) -> None:
        """
        Clear all entries from the cache.
        """
        self.cache = {}

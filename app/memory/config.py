from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ContextMemoryConfig(BaseModel):
    """
    Configuration settings for ContextMemory features.
    
    Controls which features are enabled and their parameters.
    """
    # Caching settings
    enable_caching: bool = Field(default=True, description='Enable caching of query results')
    cache_ttl_seconds: int = Field(default=300, description='Time-to-live for cached results in seconds')
    max_cache_size: int = Field(default=100, description='Maximum number of items in the cache before LRU eviction')
    
    # Retry settings
    enable_retry: bool = Field(default=False, description='Enable retry for insufficient results')
    min_results_threshold: int = Field(default=2, description='Minimum number of results before triggering retry')
    max_retries: int = Field(default=2, description='Maximum number of retries')
    
    # Query optimization settings
    enable_query_optimization: bool = Field(default=False, description='Enable query optimization/inference')
    
    # Tracing settings
    enable_tracing: bool = Field(default=False, description='Enable tracing of queries and results')
    trace_log_path: Optional[str] = Field(default=None, description='Path to log trace data, if None, uses stdout')

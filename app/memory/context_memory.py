import uuid
import time
from typing import List, Dict, Any, Optional

from app.memory.context_provider import ContextProvider
from app.memory.config import ContextMemoryConfig
from app.memory.cache import QueryCache
from app.memory.optimizer import QueryOptimizer
from app.memory.tracer import TracingSystem

class ContextMemory:
    """
    A class to manage chat history and context using a pluggable context provider.
    Provides capabilities to store, retrieve, and query context based on metadata filters.
    """
    
    def __init__(self, provider: ContextProvider, config: Optional[ContextMemoryConfig] = None):
        """
        Initialize the context memory with the given provider and optional config.
        
        Args:
            provider: The context provider implementation to use
            config: Optional configuration to control advanced features
        """
        self.provider = provider
        self.config = config or ContextMemoryConfig()
        
        # Initialize cache if enabled
        if self.config.enable_caching:
            self.cache = QueryCache(
                ttl_seconds=self.config.cache_ttl_seconds,
                max_size=self.config.max_cache_size
            )
        else:
            self.cache = None
            
        # Initialize query optimizer if enabled
        if self.config.enable_query_optimization:
            self.query_optimizer = QueryOptimizer()
        else:
            self.query_optimizer = None
            
        # Initialize tracing if enabled
        if self.config.enable_tracing:
            self.tracer = TracingSystem(log_path=self.config.trace_log_path)
        else:
            self.tracer = None
    
    async def add_context(self, content: str, metadata: Dict[str, Any], document_id: Optional[str] = None) -> None:
        """
        Add a piece of context/chat history to the memory.
        
        Args:
            content: The text content to store
            metadata: Associated metadata (user_id, session_id, timestamp, etc.)
            document_id: Optional unique identifier for the document
        """
        await self.provider.add_context(content, metadata, document_id)
        
        # Clear cache if we have one since the context has changed
        if self.cache:
            self.cache.clear()
    
    async def query_context(self, query_text: str, top_k: int = 5, 
                           metadata_filter: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Query the context memory with optional metadata filtering.
        Includes caching, retry, and optimization features if enabled.
        
        Args:
            query_text: The semantic query text
            top_k: Maximum number of results to return
            metadata_filter: Dictionary of metadata constraints (e.g. {'user_id': '123'})
            
        Returns:
            List of relevant context items
        """
        # Generate query ID for tracing
        query_id = str(uuid.uuid4())
        
        # Start timing for performance tracing
        start_time = time.time()
        was_cached = False
        retry_count = 0
        
        # Trace the query if enabled
        if self.tracer:
            self.tracer.trace_query(query_id, query_text, metadata_filter)
        
        # Check cache if enabled
        if self.cache:
            cached_results = self.cache.get(query_text, metadata_filter)
            if cached_results:
                was_cached = True
                if self.tracer:
                    duration_ms = (time.time() - start_time) * 1000
                    self.tracer.trace_results(query_id, cached_results, duration_ms, was_cached)
                return cached_results
        
        # Optimize query if enabled
        if self.query_optimizer:
            optimized_query = self.query_optimizer.optimize_query(query_text)
            
            # If no metadata filter was provided, try to infer one
            if metadata_filter is None:
                inferred_metadata = self.query_optimizer.classify_query(query_text)
                if inferred_metadata:
                    metadata_filter = inferred_metadata
                    if self.tracer:
                        self.tracer.trace_query(
                            query_id, 
                            optimized_query, 
                            metadata_filter,
                            {'action': 'query_optimization', 'original': query_text}
                        )
        else:
            optimized_query = query_text
        
        # Query the provider
        results = await self.provider.query_context(optimized_query, top_k, metadata_filter)
        
        # Retry logic for insufficient results
        if self.config.enable_retry and len(results) < self.config.min_results_threshold:
            for _ in range(self.config.max_retries):
                retry_count += 1
                # TODO: Could implement more sophisticated retry strategies here
                # TODO: Also may want to adjust metadata filter to exclude already seen results
                retry_results = await self.provider.query_context(optimized_query, top_k, metadata_filter)
                results.extend(retry_results)
                if len(results) >= self.config.min_results_threshold:
                    break
        
        # Update cache if enabled
        if self.cache:
            self.cache.set(query_text, results, metadata_filter)
        
        # Trace results if enabled
        if self.tracer:
            duration_ms = (time.time() - start_time) * 1000
            self.tracer.trace_results(query_id, results, duration_ms, was_cached, retry_count)
        
        return results
    
    async def get_user_context(self, query_text: str, user_id: str, top_k: int = 5) -> List[Any]:
        """
        Get context specific to a particular user.
        
        Args:
            query_text: The semantic query text
            user_id: The user identifier to filter by
            top_k: Maximum number of results to return
            
        Returns:
            List of relevant context items for the specified user
        """
        return await self.query_context(query_text, top_k=top_k, metadata_filter={'user_id': user_id})
    
    async def get_session_context(self, query_text: str, session_id: str, top_k: int = 5) -> List[Any]:
        """
        Get context specific to a particular session.
        
        Args:
            query_text: The semantic query text
            session_id: The session identifier to filter by
            top_k: Maximum number of results to return
            
        Returns:
            List of relevant context items for the specified session
        """
        return await self.query_context(query_text, top_k=top_k, metadata_filter={'session_id': session_id})
    
    def clear_context(self, metadata_filter: Optional[Dict[str, Any]] = None) -> None:
        """
        Clear context based on metadata filter or all context if no filter provided.
        
        Args:
            metadata_filter: Dictionary of metadata constraints to filter what to delete
        """
        self.provider.clear_context(metadata_filter)
        
        # Also clear the cache if we have one
        if self.cache:
            self.cache.clear()
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

class TracingSystem:
    """
    System for tracing query execution and results for debugging and improvement.
    """
    def __init__(self, log_path: Optional[str] = None):
        """
        Initialize the tracing system.
        
        Args:
            log_path: Optional path to save trace logs, if None logs to stdout
        """
        self.logger = logging.getLogger('context_memory_tracer')
        self.logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        if self.logger.handlers:
            for handler in self.logger.handlers:
                self.logger.removeHandler(handler)
                
        # Set up logging
        if log_path:
            handler = logging.FileHandler(log_path)
        else:
            handler = logging.StreamHandler()
            
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def trace_query(self, query_id: str, query_text: str, 
                   metadata_filter: Optional[Dict[str, Any]] = None,
                   extra_info: Optional[Dict[str, Any]] = None) -> None:
        """
        Log information about a query being executed.
        
        Args:
            query_id: Unique identifier for the query
            query_text: The query text
            metadata_filter: Any metadata filters applied
            extra_info: Any additional information to log
        """
        trace_data = {
            'query_id': query_id,
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'query',
            'query_text': query_text,
            'metadata_filter': metadata_filter or {}
        }
        
        if extra_info:
            trace_data.update(extra_info)
            
        self.logger.info(json.dumps(trace_data))
    
    def trace_results(self, query_id: str, results: List[Any], 
                     duration_ms: float, 
                     was_cached: bool = False,
                     retry_count: int = 0) -> None:
        """
        Log information about query results.
        
        Args:
            query_id: Unique identifier for the query
            results: The results that were returned
            duration_ms: Query execution time in milliseconds
            was_cached: Whether results came from cache
            retry_count: Number of retries performed
        """
        # Extract just enough info from results to be useful without being excessive
        result_summaries = []
        for result in results:
            # Assuming results have an id and possibly content
            summary = {'id': getattr(result, 'id', 'unknown')}
            if hasattr(result, 'metadata'):
                summary['metadata'] = result.metadata
            result_summaries.append(summary)
        
        trace_data = {
            'query_id': query_id,
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'results',
            'result_count': len(results),
            'duration_ms': duration_ms,
            'was_cached': was_cached,
            'retry_count': retry_count,
            'results': result_summaries
        }
        
        self.logger.info(json.dumps(trace_data))

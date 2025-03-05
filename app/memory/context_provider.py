from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class ContextProvider(ABC):
    """
    Abstract base class for context providers that store and retrieve context.
    """
    
    @abstractmethod
    async def add_context(self, content: str, metadata: Dict[str, Any], document_id: Optional[str] = None) -> None:
        """
        Add a piece of context to storage.
        
        Args:
            content: The text content to store
            metadata: Associated metadata
            document_id: Optional unique identifier for the document
        """
        pass
    
    @abstractmethod
    async def query_context(self, query_text: str, top_k: int = 5, 
                           metadata_filter: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Query the context with optional metadata filtering.
        
        Args:
            query_text: The semantic query text
            top_k: Maximum number of results to return
            metadata_filter: Dictionary of metadata constraints
            
        Returns:
            List of relevant context items
        """
        pass
    
    @abstractmethod
    def clear_context(self, metadata_filter: Optional[Dict[str, Any]] = None) -> None:
        """
        Clear context based on metadata filter or all context if no filter provided.
        
        Args:
            metadata_filter: Dictionary of metadata constraints to filter what to delete
        """
        pass

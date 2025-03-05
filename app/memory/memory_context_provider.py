from typing import List, Dict, Any, Optional
import uuid
from app.memory.context_provider import ContextProvider
from app.models import Document

class MemoryContextProvider(ContextProvider):
    """
    Context provider implementation using in-memory storage.
    """
    
    def __init__(self):
        """
        Initialize the memory context provider with an empty context store.
        """
        self.context_store = []
    
    async def add_context(self, content: str, metadata: Dict[str, Any], document_id: Optional[str] = None) -> None:
        """
        Add a piece of context to memory.
        
        Args:
            content: The text content to store
            metadata: Associated metadata
            document_id: Optional unique identifier for the document
        """
        if document_id is None:
            document_id = str(uuid.uuid4())
            
        document = Document(
            id=document_id,
            content=content,
            metadata=metadata
        )
        self.context_store.append(document)
    
    async def query_context(self, query_text: str, top_k: int = 5, 
                           metadata_filter: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Query the in-memory context with optional metadata filtering.
        
        Args:
            query_text: The semantic query text (not used for actual semantic matching in this implementation)
            top_k: Maximum number of results to return
            metadata_filter: Dictionary of metadata constraints
            
        Returns:
            List of relevant context items
        """
        # Filter by metadata if provided
        results = self.context_store
        
        if metadata_filter:
            results = [
                doc for doc in results
                if all(doc.metadata.get(key) == value for key, value in metadata_filter.items())
            ]
        
        # Note: This implementation doesn't do actual semantic matching
        # It just returns the most recent contexts up to top_k
        return results[-top_k:]
    
    def clear_context(self, metadata_filter: Optional[Dict[str, Any]] = None) -> None:
        """
        Clear context based on metadata filter or all context if no filter provided.
        
        Args:
            metadata_filter: Dictionary of metadata constraints to filter what to delete
        """
        if metadata_filter is None:
            # Clear all context
            self.context_store = []
        else:
            # Delete documents matching the metadata filter
            self.context_store = [
                doc for doc in self.context_store
                if not all(doc.metadata.get(key) == value for key, value in metadata_filter.items())
            ]

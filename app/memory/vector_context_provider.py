from typing import List, Dict, Any, Optional
from app.db.vector_store import VectorStore
from app.models import Document
from app.memory.context_provider import ContextProvider

class VectorContextProvider(ContextProvider):
    """
    Context provider implementation using vector store embeddings.
    """
    
    def __init__(self, collection_name: str = 'context_memory', persist_directory: str = './data/context_memory'):
        """
        Initialize the vector context provider.
        
        Args:
            collection_name: Name of the collection to use in the vector store
            persist_directory: Directory to persist the vector database
        """
        self.vector_store = VectorStore(
            collection_name=collection_name,
            persist_directory=persist_directory
        )
    
    async def add_context(self, content: str, metadata: Dict[str, Any], document_id: Optional[str] = None) -> None:
        """
        Add a piece of context to the vector store.
        
        Args:
            content: The text content to store
            metadata: Associated metadata
            document_id: Optional unique identifier for the document
        """
        document = Document(
            id=document_id,
            content=content,
            metadata=metadata
        )
        self.vector_store.add_documents([document])
    
    async def query_context(self, query_text: str, top_k: int = 5, 
                           metadata_filter: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Query the vector store with optional metadata filtering.
        
        Args:
            query_text: The semantic query text
            top_k: Maximum number of results to return
            metadata_filter: Dictionary of metadata constraints
            
        Returns:
            List of relevant context items
        """
        # First get semantic matches
        results = await self.vector_store.query(query_text, top_k=top_k)
        
        # If metadata filter is provided, apply it
        if metadata_filter:
            filtered_results = []
            for result in results:
                # Check if all metadata constraints are satisfied
                if all(result.metadata.get(key) == value for key, value in metadata_filter.items()):
                    filtered_results.append(result)
            return filtered_results
        
        return results
    
    def clear_context(self, metadata_filter: Optional[Dict[str, Any]] = None) -> None:
        """
        Clear context based on metadata filter or all context if no filter provided.
        
        Args:
            metadata_filter: Dictionary of metadata constraints to filter what to delete
        """
        if metadata_filter is None:
            # Clear all context
            self.vector_store.clear()
        else:
            # Delete documents matching the metadata filter
            self.vector_store.delete_documents(where=metadata_filter)

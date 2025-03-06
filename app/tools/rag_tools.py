from app.models import RAGResult
from app.utils.prompt_generator import generate_rag_query, RAGQueryParams
    
class RAGTool:
    """
    Retrieval-Augmented Generation tool that uses the vector store
    to retrieve relevant context for answering questions.
    """
    
    def __init__(self, vector_store=None):
        """
        Initialize the RAG tool with a vector store
        
        Args:
            vector_store: The vector store to use for retrieval
        """
        self.vector_store = vector_store
    
    async def retrieve(self, query: str, top_k: int = 3, context: str = None, query_type: str = 'specific') -> RAGResult:
        """
        Retrieve relevant documents for the given query
        
        Args:
            query: The query to retrieve documents for
            top_k: Maximum number of documents to retrieve
            context: Additional context for the query
            query_type: Type of query ('specific', 'creative', or 'rules')
            
        Returns:
            RAGResult containing retrieved text and sources
        """
        if not self.vector_store:
            return RAGResult(text='No vector store available')
            
        # Generate optimized search query using the template
        search_query = generate_rag_query(RAGQueryParams(
            user_query=query,
            context=context,
            query_type=query_type
        ))
        
        # Retrieve relevant documents
        results = await self.vector_store.query(search_query, top_k=top_k)
        
        # Extract the content and metadata
        documents = []
        combined_text = ''
        
        for doc in results:
            if hasattr(doc, 'metadata'):
                documents.append({
                    'content': doc.page_content if hasattr(doc, 'page_content') else str(doc),
                    'metadata': doc.metadata
                })
                combined_text += doc.page_content if hasattr(doc, 'page_content') else str(doc)
                combined_text += '\n\n'
        
        return RAGResult(
            text=combined_text.strip(),
            sources=documents
        )

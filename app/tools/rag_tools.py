from app.models import RAGResult
from app.utils.prompt_generator import generate_rag_query, RAGQueryParams
from app.db.vector_store import VectorStore
from app.classifiers.light_embed_classifier import LightEmbeddingClassifier
from typing import Optional, Dict, Any
    
class RAGTool:
    """
    Retrieval-Augmented Generation tool that uses the vector store
    to retrieve relevant context for answering questions.
    """
    
    def __init__(self, vector_store: VectorStore=None, 
                 classifier: Optional[LightEmbeddingClassifier]=None,
                 metadata_path: str='./data/document_metadata.json'):
        """
        Initialize the RAG tool with a vector store
        
        Args:
            vector_store: The vector store to use for retrieval
            classifier: Optional pre-initialized LightEmbeddingClassifier
            metadata_path: Path to metadata JSON file for classifier initialization
        """
        self.vector_store = vector_store
        self.name = 'rag_tool'
        self.classifier = classifier
        if not self.classifier:
            try:
                self.classifier = LightEmbeddingClassifier(metadata_path)
            except Exception as e:
                print(f"Could not initialize classifier: {e}")
                self.classifier = None
    
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
        
        # Use classifier to generate metadata filters if available
        metadata_filter = None
        if self.classifier:
            classification = self.classifier.classify(query)
            if classification['collections'] or classification['tags']:
                metadata_filter = {}
                if classification['collections']:
                    metadata_filter['Collection'] = classification['collections'][0]
                if classification['tags']:
                    metadata_filter['Tags'] = classification['tags'][0]
        
        # Retrieve relevant documents with metadata filtering
        results = await self.vector_store.query(search_query, top_k=top_k, metadata_filters=metadata_filter)
        
        # If no results with metadata filter, retry without filter
        if not results and metadata_filter:
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

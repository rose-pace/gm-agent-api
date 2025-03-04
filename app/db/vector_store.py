import os
import chromadb
from chromadb.utils import embedding_functions
import os

# import the Document model
from app.models import Document

class VectorStore:
    """
    Vector store implementation using Chroma DB
    """
    
    def __init__(self, collection_name: str = 'campaign_notes', persist_directory: str = './data/vector_db'):
        """
        Initialize the vector store
        
        Args:
            collection_name: Name of the collection to use
            persist_directory: Directory to persist the database
        """
        # Create the persist directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize the chroma client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use sentence transformers embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name='all-MiniLM-L6-v2'
        )
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
    
    def add_documents(self, documents: list[Document]):
        """
        Add a document to the vector store
        
        Args:
            document: The document to add
        """
        documents = [d.content for d in documents]
        metadatas = [d.metadata for d in documents]
        ids = [d.id if d.id is not None else str(hash(d.content)) for d in documents]
        
        # Add the document to the collection
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    async def query(self, query_text: str, top_k: int = 3):
        """
        Query the vector store for relevant documents
        
        Args:
            query_text: The query text
            top_k: Maximum number of results to return
            
        Returns:
            List of relevant documents
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k
        )
        
        documents = []
        
        # Format the results
        if results and 'documents' in results:
            for i, doc in enumerate(results['documents'][0]):
                metadata = {}
                if 'metadatas' in results and i < len(results['metadatas'][0]):
                    metadata = results['metadatas'][0][i]
                
                document = type('Document', (), {
                    'page_content': doc,
                    'metadata': metadata
                })
                documents.append(document)
        
        return documents
    
    def delete_document(self, document_id: str):
        """
        Delete a document from the vector store
        
        Args:
            document_id: The ID of the document to delete
        """
        self.collection.delete(ids=[document_id])
    
    def clear(self):
        """
        Clear all documents from the collection
        """
        self.collection.delete()

import os
from typing import Any
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
        # self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        #     model_name='all-MiniLM-L6-v2'
        # )

        # TODO: Set up through configuration
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv('GITHUB_TOKEN'),
            api_base='https://models.inference.ai.azure.com',
            model_name='text-embedding-3-large'
        )
        
        # Get or create the collection
        self._get_or_create_collection(collection_name)

    def _get_or_create_collection(self, collection_name: str):
        """
        Set the collection name for the vector store
        """
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
        contents = [d.content for d in documents]
        metadatas = [d.metadata for d in documents]
        ids = [d.id if d.id is not None else str(hash(d.content)) for d in documents]
        
        # Add the document to the collection
        self.collection.add(
            documents=contents,
            metadatas=self._transform_metadatas_for_storage(metadatas),
            ids=ids
        )

    async def query(self, query_text: str, metadata_filters: dict = None, documents_filter: dict = None, top_k: int = 3):
        """
        Query the vector store for relevant documents
        
        Args:
            query_text: The query text
            metadata_filters: Optional dictionary of metadata filters
            documents_filter: Optional dictionary of document content filters
            top_k: Maximum number of results to return
            
        Returns:
            List of relevant documents
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=metadata_filters,
            where_document=documents_filter
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
    
    def delete_documents(self, document_ids: list[str] = None, where: dict = None):
        """
        Delete documents from the vector store
        
        Args:
            document_ids: Optional list of document IDs to delete
            where: Optional dictionary of metadata filters for deletion
            
        Raises:
            ValueError: If neither document_ids nor where is provided
        """
        if document_ids is None and where is None:
            raise ValueError('Either document_ids or where must be provided')
        
        self.collection.delete(
            ids=document_ids,
            where=where
        )
    
    def clear(self):
        """
        Clear all documents from the collection
        """
        collection_name = self.collection.name
        self.client.delete_collection(collection_name)
        self._get_or_create_collection(collection_name)

    def _transform_metadatas_for_storage(self, metadatas: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Transform metadata for storage in the vector store
        by flattening nested lists and dictionaries.
        
        Args:
            metadatas: List of metadata dictionaries
        
        Returns:
            List of transformed metadata dictionaries
        """
        transformed_metadatas = []
        for metadata in metadatas:
            transformed_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, dict):
                    transformed_metadata.update(self._flatten_dict(value, parent_key=key))
                elif isinstance(value, list):
                    transformed_metadata.update(self._flatten_list(value, parent_key=key))
                else:
                    transformed_metadata[key] = value
            transformed_metadatas.append(transformed_metadata)
        return transformed_metadatas
    
    def _flatten_dict(self, d: dict, parent_key: str = '') -> dict:
        """
        Flatten a dictionary by concatenating nested keys.
        
        Args:
            d: The dictionary to flatten
            parent_key: The parent key for the current dictionary
        
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f'{parent_key}_{k}' if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, parent_key=new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _flatten_list(self, l: list, parent_key: str = '') -> dict:
        """
        Flatten a list by concatenating nested keys.
        
        Args:
            l: The list to flatten
            parent_key: The parent key for the current list

        Returns:
#             Flattened dictionary
#         """
        items = []
        for i, v in enumerate(l):
            new_key = f'{parent_key}_{i}' if parent_key else str(i)  
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, parent_key=new_key).items())
            elif isinstance(v, list):
                items.extend(self._flatten_list(v, parent_key=new_key).items())
            else:
                new_key = f'{parent_key}_{v}' if parent_key else str(v)
                items.append((new_key, 1))
        return dict(items)
    
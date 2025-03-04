import re
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    MarkdownTextSplitter,
    TokenTextSplitter
)

# import vector store module
from app.db import VectorStore
from app.models import Document

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, 
                 vector_store: VectorStore,
                 docs_dir: str = 'documents'):
        """
        Initialize the document processor
        
        Args:
            docs_dir: Directory containing documents to process
            db_dir: Directory to store the ChromaDB database
            embedding_model: Name of the embedding model to use
        """
        self.client = vector_store
        self.docs_dir = Path(docs_dir)

    def extract_yaml_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Extract YAML blocks from document content"""
        yaml_pattern = r'```yaml\s+(.*?)\s+```'
        yaml_blocks = []
        
        for yaml_match in re.finditer(yaml_pattern, content, re.DOTALL):
            try:
                yaml_content = yaml_match.group(1)
                yaml_data = yaml.safe_load(yaml_content)
                yaml_blocks.append(yaml_data)
            except Exception as e:
                logger.error(f'Error parsing YAML block: {e}')
        
        return yaml_blocks

    def process_document(self, content: str, file_name: str, chunking_strategy: str = 'markdown') -> None:
        """
        Process all documents using the specified chunking strategy
        
        Args:
            chunking_strategy: The strategy to use for chunking documents
                Options: 'fixed', 'markdown', 'yaml', 'sliding'
        """
        content = self.read_document(file_name)
            
        if not content:
            return
            
        # Process content based on chunking strategy
        chunks = self.chunk_document(content, file_name, chunking_strategy)
        
        # Add chunks to the vector store
        self.add_chunks_to_db(chunks, file_name)

    def chunk_document(self, 
                       content: str, 
                       file_name: str, 
                       strategy: str) -> List[Dict[str, Any]]:
        """
        Chunk document based on selected strategy
        
        Args:
            content: Document content
            file_name: str to the document
            strategy: Chunking strategy to use
            
        Returns:
            List of chunk dictionaries with text, metadata, and IDs
        """
        if strategy == 'fixed':
            return self.fixed_size_chunking(content, file_name)
        elif strategy == 'markdown':
            return self.markdown_chunking(content, file_name)
        elif strategy == 'yaml':
            return self.yaml_structure_chunking(content, file_name)    
        else:
            return self.sliding_window_chunking(content, file_name)

    def fixed_size_chunking(self, content: str, file_name: str) -> List[Dict[str, Any]]:
        """
        Split document into fixed-size chunks (character or token-based)
        
        Advantages:
         - Simple and consistent chunk sizes
         - Good for general-purpose RAG applications
         - Predictable performance characteristics
        
        Disadvantages:
         - May split content at semantically inappropriate places
         - Loses structural information from the document
         - Can separate related content
        """
        # Using Character-based splitting for simplicity
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=['\n## ', '\n### ', '\n#### ', '\n', ' ', '']
        )
        
        chunks = text_splitter.split_text(content)
        
        return [
            {
                'id': f'{file_name}-chunk-{i}',
                'text': chunk,
                'metadata': {
                    'source': str(file_name),
                    'chunk_type': 'fixed_size',
                    'chunk_index': i
                }
            }
            for i, chunk in enumerate(chunks)
        ]

    def yaml_structure_chunking(self, content: str, file_name: str) -> List[Dict[str, Any]]:
        """
        Extract and process YAML blocks as structured data chunks
        """
        yaml_blocks = self.extract_yaml_blocks(content)
        chunks = []
        
        for i, yaml_block in enumerate(yaml_blocks):
            # Convert YAML block to a string representation
            yaml_text = yaml.dump(yaml_block)
            
            chunks.append({
                'id': f'{file_name}-yaml-{i}',
                'text': yaml_text,
                'metadata': {
                    'source': str(file_name),
                    'chunk_type': 'yaml_structure',
                    'chunk_index': i,
                    'is_structured': True,
                    'yaml_keys': list(yaml_block.keys()) if isinstance(yaml_block, dict) else []
                }
            })
            
        return chunks

    def markdown_chunking(self, content: str, file_name: str) -> List[Dict[str, Any]]:
        """
        Combine markdown text with related YAML data for context-rich chunks
        """
        # split markdown text
        md_splitter = MarkdownTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100
        )
        
        chunks = md_splitter.split_text(content)

        # Get document title from first block
        title = chunks[0].split('\n')[0].strip(' #') if chunks else file_name

        # Loop through markdown chunks and extract YAML blocks
        for i, chunk in enumerate(chunks):
            chunk_header = chunk.split('\n')[0].strip(' #')
            yaml_blocks = self.extract_yaml_blocks(chunk)
            for j, yaml_block in enumerate(yaml_blocks):
                # Convert YAML block to a string representation
                yaml_text = yaml.dump(yaml_block)
                yaml_chunk_id = f'{file_name}-yaml-{i}-{j}'

                # replace YAML block in markdown chunk
                chunks[i] = chunks[i].replace(yaml_text, f'YAML BLOCK: {yaml_chunk_id}')
                
                chunks.append({
                    'id': yaml_chunk_id,
                    'text': yaml_text,
                    'metadata': {
                        'document_title': title,
                        'source': str(file_name),
                        'chunk_type': 'markdown_yaml',
                        'chunk_index': i,
                        'chunk_header': chunk_header,
                        'yaml_keys': list(yaml_block.keys()) if isinstance(yaml_block, dict) else []
                    }
                })
            #append markdown chunk
            chunks.append({
                'id': f'{file_name}-markdown-{i}',
                'text': chunk,
                'metadata': {
                    'document_title': title,
                    'source': str(file_name),
                    'chunk_type': 'markdown',
                    'chunk_index': i,
                    'chunk_header': chunk_header,
                    'has_yaml': len(yaml_blocks) > 0
                }
            })
            
        return chunks

    def sliding_window_chunking(self, content: str, file_name: str) -> List[Dict[str, Any]]:
        """
        Create overlapping chunks to preserve context across chunk boundaries
        """
        # Using TokenTextSplitter for token-based sliding window
        text_splitter = TokenTextSplitter(
            chunk_size=500,  # Tokens per chunk
            chunk_overlap=150  # Significant overlap
        )
        
        chunks = text_splitter.split_text(content)
        
        return [
            {
                'id': f'{file_name}-sliding-{i}',
                'text': chunk,
                'metadata': {
                    'source': str(file_name),
                    'chunk_type': 'sliding_window',
                    'chunk_index': i
                }
            }
            for i, chunk in enumerate(chunks)
        ]

    def add_chunks_to_db(self, chunks: List[Dict[str, Any]], file_name: str) -> None:
        """Add processed chunks to the vector database"""
        if not chunks:
            return
                    
        # Add to collection
        self.client.add_documents(
            [Document(content=c['text'], metadata=c['metadata'], id=c['id']) for c in chunks]
        )
        
        logger.info(f'Added {len(chunks)} chunks from {file_name} to vector database')

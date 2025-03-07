"""
Vector Store Processor

Handles chunking documents and adding them to the vector database.
"""
import re
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    MarkdownTextSplitter,
    TokenTextSplitter
)

from app.db import VectorStore
from app.models import Document
from app.processors.base_processor import BaseProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VectorProcessor(BaseProcessor):
    """
    Processor that handles document chunking and storage in vector database.
    """
    
    def __init__(self, vector_store: VectorStore, chunking_strategy: str = 'markdown'):
        """
        Initialize the vector processor.
        
        Args:
            vector_store: The vector store to add documents to
            chunking_strategy: Strategy to use for chunking documents
        """
        self.vector_store = vector_store
        self.chunking_strategy = chunking_strategy
        self.chunks = []
    
    def process_document(self, content: str, file_path: Path, metadata: Dict[str, Any]) -> None:
        """
        Process a document by chunking it and adding to vector store.
        
        Args:
            content: Document content
            file_path: Path to the document
            metadata: Additional metadata
        """
        if not content:
            return
        
        # Process content based on chunking strategy
        chunks = self._chunk_document(content, file_path.stem, self.chunking_strategy)
        
        # Add to collection
        self.vector_store.add_documents(
            [Document(content=c['text'], metadata=c['metadata'], id=c['id']) for c in chunks]
        )
        
        logger.info(f'Added {len(chunks)} chunks from {file_path.stem} to vector database')
        
    def finalize(self) -> None:
        """No finalization needed for vector processor."""
        pass
        
    def _extract_yaml_blocks(self, content: str) -> List[Dict[str, Any]]:
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
        
    def _chunk_document(self, content: str, file_name: str, strategy: str) -> List[Dict[str, Any]]:
        """
        Chunk document based on selected strategy
        
        Args:
            content: Document content
            file_name: Name of the document
            strategy: Chunking strategy to use
            
        Returns:
            List of chunk dictionaries with text, metadata, and IDs
        """
        if strategy == 'fixed':
            return self._fixed_size_chunking(content, file_name)
        elif strategy == 'markdown':
            return self._markdown_chunking(content, file_name)
        elif strategy == 'yaml':
            return self._yaml_structure_chunking(content, file_name)    
        else:
            return self._sliding_window_chunking(content, file_name)

    # ...existing code from DocumentProcessor for the different chunking methods...
    def _fixed_size_chunking(self, content: str, file_name: str) -> List[Dict[str, Any]]:
        """Split document into fixed-size chunks"""
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

    def _yaml_structure_chunking(self, content: str, file_name: str) -> List[Dict[str, Any]]:
        """Extract and process YAML blocks as structured data chunks"""
        yaml_blocks = self._extract_yaml_blocks(content)
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

    def _markdown_chunking(self, content: str, file_name: str) -> List[Dict[str, Any]]:
        """Combine markdown text with related YAML data"""
        # split markdown text
        md_splitter = MarkdownTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100
        )
        
        chunks = md_splitter.split_text(content)

        # Get document title from first block
        title = chunks[0].split('\n')[0].strip(' #') if chunks else file_name

        # Loop through markdown chunks and extract YAML blocks
        processed_chunks = []
        
        for i, chunk in enumerate(chunks):
            chunk_header = chunk.split('\n')[0].strip(' #')
            yaml_blocks = self._extract_yaml_blocks(chunk)
            
            for j, yaml_block in enumerate(yaml_blocks):
                # Convert YAML block to a string representation
                yaml_text = yaml.dump(yaml_block)
                yaml_chunk_id = f'{file_name}-yaml-{i}-{j}'
                
                processed_chunks.append({
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
            
            # Add markdown chunk
            processed_chunks.append({
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
            
        return processed_chunks

    def _sliding_window_chunking(self, content: str, file_name: str) -> List[Dict[str, Any]]:
        """Create overlapping chunks to preserve context"""
        # Using TokenTextSplitter for token-based sliding window
        text_splitter = TokenTextSplitter(
            chunk_size=500,
            chunk_overlap=150
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

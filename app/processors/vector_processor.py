"""
Vector Store Processor

Handles chunking documents and adding them to the vector database.
"""
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
    
    def __init__(self, vector_store: VectorStore, chunking_strategy: str = 'markdown', **kwargs):
        """
        Initialize the vector processor.
        
        Args:
            vector_store: The vector store to add documents to
            chunking_strategy: Strategy to use for chunking documents
        """
        self.vector_store = vector_store
        self.chunking_strategy = chunking_strategy
        self.chunks = []

        if kwargs.items():
            self.chunk_size = kwargs.get('chunk_size')
            self.chunk_overlap = kwargs.get('chunk_overlap')
    
    def process_document(self, content: str, file_path: Path) -> None:
        """
        Process a document by chunking it and adding to vector store.
        
        Args:
            content: Document content
            file_path: Path to the document
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
        """
        Extract YAML blocks from document content, handling cases where closing
        backticks might be in a different chunk.
        
        Args:
            content: Document content containing YAML blocks
            
        Returns:
            List of parsed YAML data dictionaries
        """
        # Pattern for complete YAML blocks
        complete_pattern = r'```yaml\s+(.*?)\s+```'
        # Pattern for YAML blocks without closing backticks
        open_pattern = r'```yaml\s+(.*?)(?:\Z|(?=\n#))'
        
        yaml_blocks = []
        
        # First try to find complete blocks
        complete_matches = list(re.finditer(complete_pattern, content, re.DOTALL))
        
        if complete_matches:
            # Process complete matches
            for yaml_match in complete_matches:
                try:
                    yaml_content = yaml_match.group(1)
                    yaml_data = yaml.safe_load(yaml_content)
                    yaml_blocks.append(yaml_data)
                except Exception as e:
                    logger.error(f'Error parsing YAML block: {e}', exc_info=True)
        else:
            # If no complete blocks found, look for open blocks
            for yaml_match in re.finditer(open_pattern, content, re.DOTALL):
                try:
                    yaml_content = yaml_match.group(1).strip()
                    # Clean up any trailing text that might not be part of the YAML
                    if '```' in yaml_content:
                        yaml_content = yaml_content.split('```')[0]
                    yaml_data = yaml.safe_load(yaml_content)
                    yaml_blocks.append(yaml_data)
                except Exception as e:
                    logger.error(f'Error parsing partial YAML block: {e}', exc_info=True)
        
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
            chunk_size=self.chunk_size or 1000,
            chunk_overlap=self.chunk_overlap or 200,
            length_function=len,
            separators=['\n## ', '\n### ', '\n#### ', '\n', ' ', '']
        )
        
        chunks = text_splitter.split_text(content)
        
        return [
            {
                'id': f'{file_name}-chunk-{i}',
                'text': chunk,
                'metadata': {
                    'document_title': file_name,
                    'source': str(file_name),
                    'chunk_type': 'fixed_size',
                    'chunk_index': i
                }
            }
            for i, chunk in enumerate(chunks)
        ]

    def _yaml_structure_chunking(self, content: str, file_name: str) -> List[Dict[str, Any]]:
        """Extract and process YAML blocks as structured data chunks"""
        # TODO: I don't think adding YAML to the vector store is necessary but keeping this for now
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
            chunk_size=self.chunk_size or 1000, 
            chunk_overlap=self.chunk_overlap or 100
        )
        
        chunks = md_splitter.split_text(content)

        # Get document title from first block
        title = chunks[0].split('\n')[0].strip(' #') if chunks else file_name

        metadata = {
            'document_title': title,
            'source': str(file_name),
            'collection': None,
            'tags': [],
        }
        # Extract metadata from YAML block beneath ## Document Notes
        document_notes = next((chunk for chunk in chunks if '## Document Notes' in chunk), None)
        if document_notes:
            yaml_block = self._extract_yaml_blocks(document_notes)
            if yaml_block:
                metadata['collection'] = yaml_block[0].get('Collection', 'Setting Notes')
                metadata['tags'] = yaml_block[0].get('Tags', [])

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
                    'metadata': metadata | {
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
                'metadata': metadata | {
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
            chunk_size=self.chunk_size or 500,
            chunk_overlap=self.chunk_overlap or 150
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

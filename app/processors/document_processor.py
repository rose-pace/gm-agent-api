"""
Document Processor Coordinator

Orchestrates the document processing workflow, delegating to specialized processors.
"""
import logging
from pathlib import Path
from typing import List, Optional

from app.processors.base_processor import BaseProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Coordinates the document processing workflow, delegating to specialized processors.
    """
    
    def __init__(self, processors: List[BaseProcessor] = None):
        """
        Initialize the document processor with a list of processors.
        
        Args:
            processors: List of document processors to use
        """
        self.processors = processors or []
    
    def add_processor(self, processor: BaseProcessor) -> None:
        """
        Add a processor to the workflow.
        
        Args:
            processor: The processor to add
        """
        self.processors.append(processor)
    
    def process_documents(self, docs_dir: str) -> None:
        """
        Process all documents in a directory using registered processors.
        
        Args:
            docs_dir: Directory containing documents to process
        """
        docs_path = Path(docs_dir)
        document_paths = self._find_documents(docs_path)
        
        logger.info(f'Found {len(document_paths)} documents to process')
        
        for doc_path in document_paths:
            try:
                content = self._read_document(doc_path)
                if not content:
                    continue
                
                # Process with each registered processor
                for processor in self.processors:
                    processor.process_document(content, doc_path)
                
            except Exception as e:
                logger.error(f'Error processing {doc_path}: {e}', exc_info=True)
        
        # Let each processor perform any final operations
        for processor in self.processors:
            processor.finalize()
    
    def _find_documents(self, docs_dir: Path) -> List[Path]:
        """
        Find all document files in the specified directory.
        
        Args:
            docs_dir: Directory to search for documents
            
        Returns:
            List of document paths
        """
        if not docs_dir.exists():
            logger.warning(f'Documents directory not found: {docs_dir}')
            return []
        
        # Find all markdown and YAML files
        return list(docs_dir.glob('**/*.md')) + list(docs_dir.glob('**/*.yaml'))
    
    def _read_document(self, file_path: Path) -> Optional[str]:
        """
        Read a document file and return its content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Document content as string, or None if there was an error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f'Error reading file {file_path}: {e}', exc_info=True)
            return None

import re
import sys
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any

from app.db import DocumentProcessor, VectorStore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_documents(docs_dir: str) -> List[Path]:
    """Find all markdown files in the documents directory"""
    return list(docs_dir.glob('**/*.md')) + list(docs_dir.glob('**/*.yaml'))

def read_document(file_path: Path) -> str:
    """Read a document file and return its content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f'Error reading file {file_path}: {e}')
        return ''

def main():
    """Main function to run document processing"""
    # Default values
    docs_dir = 'documents'
    chunking_strategy = 'markdown'
    import_mode = 'overwrite'
    
    # Initialize vector store
    vector_store = VectorStore(
        collection_name='campaign_notes',
        persist_directory='./data/vector_db'
    )
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        import_mode = 'append' if sys.argv[1] == '-a' else 'overwrite'

    if import_mode == 'overwrite':
        logger.info('Clearing existing documents from the vector store')
        vector_store.clear()
    
    # Initialize and run processor
    processor = DocumentProcessor(vector_store=vector_store)

    files = find_documents(docs_dir=docs_dir)
    logger.info(f'Found {len(files)} documents to process')
    
    for file_path in files:
        logger.info(f'Processing {file_path}')
        content = read_document(file_path)
        
        if not content:
            continue

        chunking_strategy = 'markdown' if file_path.stem.endswith('.md') else 'yaml'

        processor.process_document(content, file_path.stem, chunking_strategy)
    
    logger.info(f'Document processing complete. Used \'{chunking_strategy}\' chunking strategy.')

if __name__ == '__main__':
    main()
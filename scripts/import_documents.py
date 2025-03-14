"""
Document Import Script

Imports documents into both vector store and graph database.
"""
import logging
import click
import json
import yaml
import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Check if environment is running it github codespaces
if 'CODESPACES' in os.environ:
    # If so, update the version of sqlite
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# Add the project root to sys.path before importing app modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.db import VectorStore
from app.db.graph_store import GraphStore
from app.models.processor_config import (
    ProcessorRegistry
)
from app.utils.processor_factory import (
    create_processors_from_config,
    create_document_processor
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Optional[ProcessorRegistry]:
    """
    Load configuration from a JSON or YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Loaded configuration or None if failed
    """
    if not config_path:
        return None
    
    try:
        path = Path(config_path)
        if not path.exists():
            logger.error(f"Configuration file not found: {config_path}", exc_info=True)
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix.lower() == '.json':
                config_data = json.load(f)
            elif path.suffix.lower() in ['.yaml', '.yml']:
                config_data = yaml.safe_load(f)
            else:
                logger.error(f"Unsupported configuration format: {path.suffix}", exc_info=True)
                return None
        
        return ProcessorRegistry.model_validate(config_data)
        
    except Exception as e:
        logger.error(f"Error loading configuration: {e}", exc_info=True)
        return None


@click.command()
@click.option('--docs_dir', 
              default=os.getenv('DOCUMENTS_DIR', 'documents'),
              help='Directory containing documents')
@click.option('--vector_dir', 
              default=os.getenv('VECTOR_DIR', './data/vector_db'),
              help='Vector database directory')
@click.option('--graph_path', 
              default=os.getenv('GRAPH_PATH', './data/graph.json'),
              help='Path to save graph database')
@click.option('--config',
              default=os.getenv('CONFIG_PATH'),
              help='Path to configuration file (JSON or YAML)')
@click.option('--mode',
              default=os.getenv('PROCESSOR_MODE', 'both'),
              type=click.Choice(['vector', 'graph', 'both']),
              help='Which processors to run')
@click.option('--append', '-a', 
              is_flag=False, 
              help='Append to existing databases. Default is to clear existing data.')
@click.option('--verbose', '-v', 
              is_flag=True, 
              help='Enable verbose logging')
def main(docs_dir: str, vector_dir: str, graph_path: str, config: Optional[str], 
         mode: str, append: bool, verbose: bool) -> None:
    """
    Main entry point for document import script.
    
    Imports documents into vector store and/or graph database based on options.
    """
    # Set logging level
    if verbose:
        logger.setLevel(logging.DEBUG)
        
    # Load configuration if specified
    config_obj = load_config(config) if config else None
    if not config_obj:
        raise ValueError('Configuration file not found or invalid. Specify with --config or set CONFIG_PATH environment variable.')
    
    vector_store: VectorStore = None
    graph_store: GraphStore = None
    
    # Add vector store processor if requested
    if mode in ['vector', 'both']:
        vector_store = VectorStore(
            collection_name='campaign_notes',
            persist_directory=vector_dir
        )
        
        if not append:
            logger.info('Clearing existing documents from the vector store')
            vector_store.clear()
    
    # Add graph processor if requested
    if mode in ['graph', 'both']:
        # Initialize graph store
        graph_store = GraphStore()
        
        # Load existing graph if in append mode
        if append and Path(graph_path).exists():
            logger.info(f'Loading existing graph from {graph_path}')
            graph_store.load_from_file(graph_path)

    # Initialize the document processor coordinator
    doc_processor = create_document_processor(
        create_processors_from_config(
            config=config_obj,
            vector_store=vector_store,
            graph_store=graph_store
        ) 
    )
    
    # Process all documents
    logger.info(f'Processing documents from {docs_dir}')
    doc_processor.process_documents(docs_dir)
    
    # Save graph if we processed it
    if mode in ['graph', 'both']:
        logger.info(f'Saving graph to {graph_path}')
        graph_store.save_to_file(graph_path)
        
        # Print summary of graph data
        entity_count = len(graph_store.nodes)
        relationship_count = len(graph_store.edges)
        logger.info(f'Graph database contains {entity_count} entities and {relationship_count} relationships')
    
    logger.info('Document processing complete.')

if __name__ == '__main__':
    main()
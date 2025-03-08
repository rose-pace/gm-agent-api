"""
Document Import Script

Imports documents into both vector store and graph database.
"""
import sys
import logging
import click
import json
import yaml
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from app.db import VectorStore
from app.db.graph_store import GraphStore
from app.processors.document_processor import DocumentProcessor
from app.processors.vector_processor import VectorProcessor
from app.processors.graph_processor import GraphProcessor
from app.models.processor_config import (
    ProcessorRegistry, VectorProcessorConfig, GraphProcessorConfig,
    EntityExtractionPattern, RelationshipExtractionPattern
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
            logger.error(f"Configuration file not found: {config_path}")
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix.lower() == '.json':
                config_data = json.load(f)
            elif path.suffix.lower() in ['.yaml', '.yml']:
                config_data = yaml.safe_load(f)
            else:
                logger.error(f"Unsupported configuration format: {path.suffix}")
                return None
        
        return ProcessorRegistry.model_validate(config_data)
        
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
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
@click.option('--chunking', 
              default=os.getenv('CHUNKING_STRATEGY', 'markdown'),
              type=click.Choice(['markdown', 'fixed', 'yaml', 'sliding']),
              help='Document chunking strategy')
@click.option('--mode',
              default=os.getenv('PROCESSOR_MODE', 'both'),
              type=click.Choice(['vector', 'graph', 'both']),
              help='Which processors to run')
@click.option('--append', '-a', 
              is_flag=True, 
              help='Append to existing databases')
def main(docs_dir: str, vector_dir: str, graph_path: str, config: Optional[str], 
         chunking: str, mode: str, append: bool) -> None:
    """
    Main entry point for document import script.
    
    Imports documents into vector store and/or graph database based on options.
    """
    # Load configuration if specified
    config_obj = load_config(config) if config else None
    
    # Initialize the document processor coordinator
    doc_processor = DocumentProcessor()
    
    # Add vector store processor if requested
    if mode in ['vector', 'both']:
        vector_store = VectorStore(
            collection_name='campaign_notes',
            persist_directory=vector_dir
        )
        
        if not append:
            logger.info('Clearing existing documents from the vector store')
            vector_store.clear()
        
        # Use config if available, otherwise use command line args
        vector_config = config_obj.vector_processor if config_obj else None
        chunking_strategy = vector_config.chunking_strategy.value if vector_config else chunking
        
        vector_processor = VectorProcessor(
            vector_store=vector_store,
            chunking_strategy=chunking_strategy
        )
        doc_processor.add_processor(vector_processor)
        logger.info(f'Added vector processor with {chunking_strategy} chunking strategy')
    
    # Add graph processor if requested
    if mode in ['graph', 'both']:
        # Initialize graph store
        graph_store = GraphStore()
        
        # Load existing graph if in append mode
        if append and Path(graph_path).exists():
            logger.info(f'Loading existing graph from {graph_path}')
            graph_store.load_from_file(graph_path)
        
        # Use config if available
        graph_config = config_obj.graph_processor if config_obj else None
        
        graph_processor = GraphProcessor(
            graph_store=graph_store,
            config=graph_config
        )
        doc_processor.add_processor(graph_processor)
        logger.info('Added graph processor')
    
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
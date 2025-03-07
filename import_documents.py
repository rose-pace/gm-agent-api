"""
Document Import Script

Imports documents into both vector store and graph database.
"""
import sys
import logging
import argparse
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


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Import documents into vector and graph databases")
    
    # Get defaults from environment variables
    default_docs_dir = os.getenv('DOCUMENTS_DIR', 'documents')
    default_vector_dir = os.getenv('VECTOR_DIR', './data/vector_db')
    default_graph_path = os.getenv('GRAPH_PATH', './data/graph.json')
    default_chunking = os.getenv('CHUNKING_STRATEGY', 'markdown')
    default_config_path = os.getenv('CONFIG_PATH', None)
    default_mode = os.getenv('PROCESSOR_MODE', 'both')
    
    parser.add_argument("--docs_dir", default=default_docs_dir, 
                        help=f"Directory containing documents (default: {default_docs_dir})")
    parser.add_argument("--vector_dir", default=default_vector_dir, 
                        help=f"Vector database directory (default: {default_vector_dir})")
    parser.add_argument("--graph_path", default=default_graph_path, 
                        help=f"Path to save graph database (default: {default_graph_path})")
    parser.add_argument("--config", default=default_config_path,
                        help="Path to configuration file (JSON or YAML)")
    parser.add_argument("--chunking", default=default_chunking, 
                        choices=["markdown", "fixed", "yaml", "sliding"], 
                        help=f"Document chunking strategy (default: {default_chunking})")
    parser.add_argument("--mode", default=default_mode,
                        choices=["vector", "graph", "both"],
                        help=f"Which processors to run (default: {default_mode})")
    parser.add_argument("-a", "--append", action="store_true", 
                        help="Append to existing databases")
    return parser.parse_args()


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
        
        return ProcessorRegistry.parse_obj(config_data)
        
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None


def main():
    """Main entry point"""
    args = parse_args()
    
    # Load configuration if specified
    config = load_config(args.config) if args.config else None
    
    # Initialize the document processor coordinator
    doc_processor = DocumentProcessor()
    
    # Add vector store processor if requested
    if args.mode in ["vector", "both"]:
        vector_store = VectorStore(
            collection_name='campaign_notes',
            persist_directory=args.vector_dir
        )
        
        if not args.append:
            logger.info('Clearing existing documents from the vector store')
            vector_store.clear()
        
        # Use config if available, otherwise use command line args
        vector_config = config.vector_processor if config else None
        chunking_strategy = vector_config.chunking_strategy.value if vector_config else args.chunking
        
        vector_processor = VectorProcessor(
            vector_store=vector_store,
            chunking_strategy=chunking_strategy
        )
        doc_processor.add_processor(vector_processor)
        logger.info(f'Added vector processor with {chunking_strategy} chunking strategy')
    
    # Add graph processor if requested
    if args.mode in ["graph", "both"]:
        # Initialize graph store
        graph_store = GraphStore()
        
        # Load existing graph if in append mode
        if args.append and Path(args.graph_path).exists():
            logger.info(f'Loading existing graph from {args.graph_path}')
            graph_store.load_from_file(args.graph_path)
        
        # Use config if available
        graph_config = config.graph_processor if config else None
        
        graph_processor = GraphProcessor(
            graph_store=graph_store,
            config=graph_config
        )
        doc_processor.add_processor(graph_processor)
        logger.info('Added graph processor')
    
    # Process all documents
    logger.info(f'Processing documents from {args.docs_dir}')
    doc_processor.process_documents(args.docs_dir)
    
    # Save graph if we processed it
    if args.mode in ["graph", "both"]:
        logger.info(f'Saving graph to {args.graph_path}')
        graph_store.save_to_file(args.graph_path)
        
        # Print summary of graph data
        entity_count = len(graph_store.nodes)
        relationship_count = len(graph_store.edges)
        logger.info(f'Graph database contains {entity_count} entities and {relationship_count} relationships')
    
    logger.info('Document processing complete.')

if __name__ == '__main__':
    main()
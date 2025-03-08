"""
Processor Factory Utilities

Provides factory functions to create and configure document processors.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.db import VectorStore
from app.db.graph_store import GraphStore
from app.models.processor_config import (
    ProcessorRegistry, 
    VectorProcessorConfig, 
    GraphProcessorConfig
)
from app.processors.document_processor import DocumentProcessor
from app.processors.vector_processor import VectorProcessor
from app.processors.graph_processor import GraphProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_processors_from_config(
    config: ProcessorRegistry,
    vector_store: Optional[VectorStore] = None,
    graph_store: Optional[GraphStore] = None
) -> List[Any]:
    """
    Create processor instances based on configuration.
    
    Args:
        config: Processor configuration registry
        vector_store: Optional vector store instance
        graph_store: Optional graph store instance
        
    Returns:
        List of configured processor instances
    """
    processors = []
    
    # Create vector processor if configured
    if config.vector_processor and vector_store:
        vector_processor = create_vector_processor(
            config=config.vector_processor,
            vector_store=vector_store
        )
        processors.append(vector_processor)
        logger.info('Created vector processor')
    
    # Create graph processor if configured
    if config.graph_processor and graph_store:
        graph_processor = create_graph_processor(
            config=config.graph_processor,
            graph_store=graph_store
        )
        processors.append(graph_processor)
        logger.info('Created graph processor')
    
    return processors


def create_vector_processor(
    config: VectorProcessorConfig,
    vector_store: VectorStore
) -> VectorProcessor:
    """
    Create a configured vector processor.
    
    Args:
        config: Vector processor configuration
        vector_store: Vector store instance
        
    Returns:
        Configured VectorProcessor instance
    """
    return VectorProcessor(
        vector_store=vector_store,
        chunking_strategy=config.chunking_strategy.value,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )


def create_graph_processor(
    config: GraphProcessorConfig,
    graph_store: GraphStore
) -> GraphProcessor:
    """
    Create a configured graph processor.
    
    Args:
        config: Graph processor configuration
        graph_store: Graph store instance
        
    Returns:
        Configured GraphProcessor instance
    """
    return GraphProcessor(graph_store=graph_store, config=config)


def create_document_processor(
    processors: List[Any]
) -> DocumentProcessor:
    """
    Create a document processor with the given processors.
    
    Args:
        processors: List of processor instances
        
    Returns:
        Configured DocumentProcessor instance
    """
    doc_processor = DocumentProcessor()
    
    for processor in processors:
        doc_processor.add_processor(processor)
    
    return doc_processor

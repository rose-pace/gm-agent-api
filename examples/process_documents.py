"""
Example script demonstrating how to use the document processors.
"""
import logging

from app.db import VectorStore
from app.db.graph_store import GraphStore
from app.models.processor_config import (
    ProcessorRegistry, 
    VectorProcessorConfig, 
    GraphProcessorConfig,
    ChunkingStrategy
)
from app.utils.processor_factory import (
    create_processors_from_config,
    create_document_processor
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def process_with_all_processors(docs_dir: str = 'documents'):
    """
    Process documents with both vector and graph processors.
    
    Args:
        docs_dir: Directory containing documents to process
    """
    # Create stores
    vector_store = VectorStore(
        collection_name='campaign_notes',
        persist_directory='./data/vector_db'
    )
    
    graph_store = GraphStore()
    
    # Create processor configuration
    config = ProcessorRegistry(
        vector_processor=VectorProcessorConfig(
            chunking_strategy=ChunkingStrategy.MARKDOWN,
            chunk_size=1000,
            chunk_overlap=200
        ),
        graph_processor=GraphProcessorConfig(
            extract_entities=True,
            extract_relationships=True
        )
    )
    
    # Create processors
    processors = create_processors_from_config(
        config=config,
        vector_store=vector_store,
        graph_store=graph_store
    )
    
    # Create document processor
    doc_processor = create_document_processor(processors)
    
    # Process documents
    doc_processor.process_documents(docs_dir)
    
    # Save the graph
    graph_store.save_to_file('./data/campaign_graph.json')
    logger.info(f'Processed documents from {docs_dir}')
    logger.info(f'Graph contains {len(graph_store.nodes)} nodes and {len(graph_store.edges)} edges')


if __name__ == '__main__':
    process_with_all_processors()

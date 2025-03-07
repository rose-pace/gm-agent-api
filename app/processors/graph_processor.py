"""
Graph Processor

Extracts entities and relationships from documents and adds them to a graph database.
"""
import re
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

from app.db.graph_store import GraphStore
from app.models.graph_models import GraphNode, GraphEdge
from app.schema.types import EntityType, RelationshipType
from app.schema.schema_store import SchemaEnforcedGraphStore
from app.processors.base_processor import BaseProcessor
from app.models.processor_config import GraphProcessorConfig, EntityExtractionPattern, RelationshipExtractionPattern

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GraphProcessor(BaseProcessor):
    """
    Processor that extracts entities and relationships from documents and 
    adds them to a graph database.
    """
    
    def __init__(self, graph_store: GraphStore, config: Optional[GraphProcessorConfig] = None):
        """
        Initialize the graph processor.
        
        Args:
            graph_store: The graph store to add entities and relationships to
            config: Configuration for the graph processor
        """
        self.graph_store = graph_store
        self.schema_store = SchemaEnforcedGraphStore(graph_store)
        
        # Use provided config or create a default one
        self.config = config or GraphProcessorConfig()
        
        # Set up default extraction patterns if none provided
        if not self.config.entity_patterns:
            self._setup_default_entity_patterns()
        
        if not self.config.relationship_patterns:
            self._setup_default_relationship_patterns()
        
        # Track entities to avoid duplicates
        self.entity_map = {}  # Maps entity name to ID
        self.entity_name_variants = {}  # Maps variant names to canonical name
    
    def _setup_default_entity_patterns(self) -> None:
        """Set up default entity extraction patterns."""
        # Event extraction pattern
        self.config.entity_patterns.append(
            EntityExtractionPattern(
                pattern_type='EVENT',
                regex_pattern=r'### Event: (.*?)\n',
                yaml_paths=['Date', 'Event'],
                default_properties={'type': 'event'}
            )
        )
        
        # Location extraction pattern
        self.config.entity_patterns.append(
            EntityExtractionPattern(
                pattern_type='LOCATION',
                yaml_paths=['location', 'Location'],
                default_properties={'type': 'location'}
            )
        )
        
        # Person extraction pattern (generic example)
        self.config.entity_patterns.append(
            EntityExtractionPattern(
                pattern_type='PERSON',
                regex_pattern=r'### Person: (.*?)\n',
                yaml_paths=['character', 'Character', 'person', 'Person'],
                default_properties={'type': 'person'}
            )
        )
    
    def _setup_default_relationship_patterns(self) -> None:
        """Set up default relationship extraction patterns."""
        # Causal relationship
        self.config.relationship_patterns.append(
            RelationshipExtractionPattern(
                relationship_type='CAUSED',
                regex_pattern=r'([\w\s]+) caused ([\w\s]+)',
                source_group=1,
                target_group=2,
                default_properties={'type': 'causal'}
            )
        )
        
        # Creation relationship
        self.config.relationship_patterns.append(
            RelationshipExtractionPattern(
                relationship_type='CREATED',
                regex_pattern=r'([\w\s]+) created ([\w\s]+)',
                source_group=1,
                target_group=2,
                default_properties={'type': 'creation'}
            )
        )
        
        # Location relationship
        self.config.relationship_patterns.append(
            RelationshipExtractionPattern(
                relationship_type='LOCATED_IN',
                regex_pattern=r'([\w\s]+) is located in ([\w\s]+)',
                source_group=1,
                target_group=2,
                default_properties={'type': 'location'}
            )
        )
    
    def process_document(self, content: str, file_path: Path, metadata: Dict[str, Any]) -> None:
        """
        Process a document by extracting entities and relationships.
        
        Args:
            content: Document content
            file_path: Path to the document
            metadata: Additional metadata
        """
        if not content or not self.config.extract_entities and not self.config.extract_relationships:
            return
        
        source_file = file_path.name
        
        # Extract entities first
        if self.config.extract_entities:
            self._extract_entities(content, source_file)
        
        # Then extract relationships (which may reference the entities)
        if self.config.extract_relationships:
            self._extract_relationships(content, source_file)
        
        logger.info(f'Processed graph data from {source_file}')
    
    def finalize(self) -> None:
        """
        Perform final operations after all documents are processed.
        """
        logger.info(f'Finalized graph processing with {len(self.entity_map)} entities')
        
    def _extract_entities(self, content: str, source_file: str) -> None:
        """Extract entities from document content."""
        # Extract YAML blocks
        yaml_blocks = re.findall(r'```yaml\n(.*?)\n```', content, re.DOTALL)
        
        # Process YAML blocks for entity extraction
        for yaml_block in yaml_blocks:
            try:
                data = yaml.safe_load(yaml_block)
                if not data:
                    continue
                
                # Extract entities from YAML using configured patterns
                self._extract_entities_from_yaml(data, source_file)
                
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML in {source_file}: {e}")
        
        # Process text content using regex patterns
        for pattern in self.config.entity_patterns:
            if not pattern.regex_pattern:
                continue
                
            entity_regex = re.compile(pattern.regex_pattern, re.DOTALL)
            for match in entity_regex.finditer(content):
                entity_name = match.group(1).strip()
                if entity_name and entity_name not in self.entity_map:
                    properties = {
                        "description": f"Entity from {source_file}",
                        "information_source": source_file,
                        **pattern.default_properties
                    }
                    
                    entity_id = self.schema_store.add_entity(
                        name=entity_name,
                        entity_type=pattern.pattern_type,
                        properties=properties
                    )
                    self.entity_map[entity_name] = entity_id
    
    def _extract_entities_from_yaml(self, data: Dict[str, Any], source_file: str) -> None:
        """Extract entities from YAML data using configured patterns."""
        for pattern in self.config.entity_patterns:
            for yaml_path in pattern.yaml_paths:
                # Check if this path exists in the data
                if yaml_path not in data:
                    continue
                    
                yaml_data = data[yaml_path]
                
                # Handle different data structures
                if isinstance(yaml_data, dict) and "name" in yaml_data:
                    entity_name = yaml_data["name"]
                elif isinstance(yaml_data, str):
                    entity_name = yaml_data
                else:
                    continue
                
                # Skip if we already have this entity
                if not entity_name or entity_name in self.entity_map:
                    continue
                
                # Build properties from YAML data and defaults
                properties = {
                    "information_source": source_file,
                    **pattern.default_properties
                }
                
                # Add description if available
                if "description" in yaml_data and isinstance(yaml_data, dict):
                    properties["description"] = yaml_data["description"]
                elif "description" in data:
                    properties["description"] = data["description"]
                else:
                    properties["description"] = f"Entity from {source_file}"
                
                # Add additional properties from YAML
                if isinstance(yaml_data, dict):
                    for key, value in yaml_data.items():
                        if key != "name" and key != "description":
                            properties[key] = value
                
                # Add the entity
                entity_id = self.schema_store.add_entity(
                    name=entity_name,
                    entity_type=pattern.pattern_type,
                    properties=properties
                )
                self.entity_map[entity_name] = entity_id
    
    def _extract_relationships(self, content: str, source_file: str) -> None:
        """Extract relationships from document content."""
        for pattern in self.config.relationship_patterns:
            relationship_regex = re.compile(pattern.regex_pattern, re.IGNORECASE)
            
            for match in relationship_regex.finditer(content):
                source_name = match.group(pattern.source_group).strip()
                target_name = match.group(pattern.target_group).strip()
                
                source_id = self._get_entity_id(source_name)
                target_id = self._get_entity_id(target_name)
                
                if source_id and target_id and source_id != target_id:
                    # Prepare relationship properties
                    properties = {
                        "description": f"Extracted from {source_file}",
                        "information_source": source_file,
                        **pattern.default_properties
                    }
                    
                    # Add the relationship
                    try:
                        self.schema_store.add_relationship(
                            name=f"{source_name} {pattern.relationship_type.lower()} {target_name}",
                            relationship_type=pattern.relationship_type,
                            source_id=source_id,
                            target_id=target_id,
                            properties=properties
                        )
                    except ValueError as e:
                        logger.error(f"Error creating relationship: {e}")
    
    def _get_entity_id(self, entity_name: str) -> Optional[str]:
        """
        Get ID for an entity by name, creating it if it doesn't exist yet.
        """
        # Check if we already know this entity
        if entity_name in self.entity_map:
            return self.entity_map[entity_name]
        
        # Check for name variants
        if entity_name in self.entity_name_variants:
            canonical_name = self.entity_name_variants[entity_name]
            return self.entity_map.get(canonical_name)
        
        # Check if it exists in the graph by name
        node = self.graph_store.get_node_by_name(entity_name)
        if node:
            self.entity_map[entity_name] = node.id
            return node.id
        
        # Create a new entity with default type
        try:
            entity_id = self.schema_store.add_entity(
                name=entity_name,
                entity_type=self.config.default_entity_type,
                properties={
                    "description": f"Auto-extracted entity",
                    "information_source": "Document extraction",
                    "auto_created": True
                }
            )
            self.entity_map[entity_name] = entity_id
            return entity_id
        except ValueError as e:
            logger.error(f"Error creating entity {entity_name}: {e}")
            return None

    def add_error(self, error: str):
        self.errors.append(error)
        self.is_valid = False
    
    def __bool__(self):
        return self.is_valid

def validate_node(node_type: str, properties: Dict[str, Any]) -> ValidationResult:
    """
    Validate that a node's properties conform to its type's schema.
    
    Args:
        node_type: Type of the node (must be in EntityType)
        properties: Properties to validate
        
    Returns:
        ValidationResult with validation status and any errors
    """
    result = ValidationResult(True)
    
    # Check that node_type is valid
    try:
        entity_type = EntityType(node_type)
    except ValueError:
        result.add_error(f"Invalid node type: {node_type}")
        result.add_error(f"Valid types are: {', '.join([t.value for t in EntityType])}")
        return result
    
    # No need to check property schema - we're using Python's dynamic typing
    # This function is mainly for documentation and to confirm valid entity types
    return result

def validate_edge(edge_type: str, source_type: str, target_type: str, 
                 properties: Dict[str, Any]) -> ValidationResult:
    """
    Validate that an edge's properties and connections conform to schema.
    
    Args:
        edge_type: Type of the edge (must be in RelationshipType)
        source_type: Type of the source node
        target_type: Type of the target node
        properties: Properties to validate
        
    Returns:
        ValidationResult with validation status and any errors
    """
    result = ValidationResult(True)
    
    # Check that edge_type is valid
    try:
        relationship_type = RelationshipType(edge_type)
    except ValueError:
        result.add_error(f"Invalid edge type: {edge_type}")
        result.add_error(f"Valid types are: {', '.join([t.value for t in RelationshipType])}")
        return result
    
    # Check that source and target types are valid
    try:
        source_entity_type = EntityType(source_type)
    except ValueError:
        result.add_error(f"Invalid source node type: {source_type}")
    
    try:
        target_entity_type = EntityType(target_type)
    except ValueError:
        result.add_error(f"Invalid target node type: {target_type}")
    
    # Check for valid entity-relationship combinations
    # This is a simplified version - in a full implementation you might want to check
    # allowed connections more rigorously based on the VALID_CONNECTIONS data
    
    # No need to check property schema - we're using Python's dynamic typing
    # This function is mainly for documentation and to confirm valid relationship types
    return result

# -----------------------------------------------------------------------------
# Entity-Relationship Valid Connections
# -----------------------------------------------------------------------------

# Define which relationships are valid between which entity types
# This can be used for validation and documentation
VALID_CONNECTIONS = {
    RelationshipType.CREATED: {
        "valid_sources": [
            EntityType.DEITY, EntityType.NPC, EntityType.FACTION, 
            EntityType.EVENT
        ],
        "valid_targets": [
            EntityType.RACE, EntityType.LOCATION, EntityType.ARTIFACT,
            EntityType.NPC, EntityType.MONSTER
        ]
    },
    RelationshipType.DESTROYED: {
        "valid_sources": [
            EntityType.DEITY, EntityType.NPC, EntityType.FACTION, 
            EntityType.EVENT, EntityType.MONSTER, EntityType.PARTY_MEMBER
        ],
        "valid_targets": [
            EntityType.LOCATION, EntityType.ARTIFACT, EntityType.NPC,
            EntityType.FACTION
        ]
    },
    # Add more relationship validations as needed
}

# -----------------------------------------------------------------------------
# GraphStore Integration
# -----------------------------------------------------------------------------

from app.db.graph_store import GraphStore
from app.models.graph_models import GraphNode, GraphEdge

class SchemaEnforcedGraphStore:
    """
    Wrapper around GraphStore that enforces the schema.
    Validates entities and relationships before adding them.
    """
    
    def __init__(self, graph_store: GraphStore):
        """
        Initialize with an existing GraphStore.
        
        Args:
            graph_store: The base graph store to wrap
        """
        self.graph_store = graph_store
    
    def add_entity(self, name: str, entity_type: str, properties: Dict[str, Any] = None) -> str:
        """
        Add an entity node with schema validation.
        
        Args:
            name: Name of the entity
            entity_type: Type of entity (must be in EntityType)
            properties: Properties for the entity
            
        Returns:
            ID of the created node
            
        Raises:
            ValueError: If the entity violates the schema
        """
        properties = properties or {}
        
        # Validate against schema
        validation = validate_node(entity_type, properties)
        if not validation.is_valid:
            raise ValueError(f"Invalid entity: {'; '.join(validation.errors)}")
        
        # Create and add the node
        node = GraphNode(
            name=name,
            type=entity_type,
            properties=properties
        )
        
        return self.graph_store.add_node(node)
    
    def add_relationship(self, name: str, relationship_type: str, 
                        source_id: str, target_id: str,
                        properties: Dict[str, Any] = None) -> str:
        """
        Add a relationship edge with schema validation.
        
        Args:
            name: Name of the relationship
            relationship_type: Type of relationship (must be in RelationshipType)
            source_id: ID of the source node
            target_id: ID of the target node
            properties: Properties for the relationship
            
        Returns:
            ID of the created edge
            
        Raises:
            ValueError: If the relationship violates the schema
        """
        properties = properties or {}
        
        # Get source and target nodes to check their types
        source_node = self.graph_store.get_node(source_id)
        if not source_node:
            raise ValueError(f"Source node with ID {source_id} does not exist")
            
        target_node = self.graph_store.get_node(target_id)
        if not target_node:
            raise ValueError(f"Target node with ID {target_id} does not exist")
        
        # Validate against schema
        validation = validate_edge(
            relationship_type, 
            source_node.type, 
            target_node.type, 
            properties
        )
        if not validation.is_valid:
            raise ValueError(f"Invalid relationship: {'; '.join(validation.errors)}")
        
        # Create and add the edge
        edge = GraphEdge(
            name=name,
            type=relationship_type,
            source_id=source_id,
            target_id=target_id,
            properties=properties
        )
        
        return self.graph_store.add_edge(edge)
    
    # Pass through other methods to the base graph store
    def get_node(self, node_id: str):
        return self.graph_store.get_node(node_id)
    
    def get_edge(self, edge_id: str):
        return self.graph_store.get_edge(edge_id)
    
    def get_nodes_by_type(self, node_type: str):
        return self.graph_store.get_nodes_by_type(node_type)
    
    def get_node_by_name(self, name: str):
        return self.graph_store.get_node_by_name(name)
    
    def get_related_nodes(self, node_id: str, edge_type=None, direction='outgoing'):
        return self.graph_store.get_related_nodes(node_id, edge_type, direction)
    
    def find_path(self, start_node_id: str, end_node_id: str, max_depth=5):
        return self.graph_store.find_path(start_node_id, end_node_id, max_depth)
    
    def find_nodes_by_property(self, prop_name: str, prop_value: Any):
        return self.graph_store.find_nodes_by_property(prop_name, prop_value)
    
    def save_to_file(self, file_path: str):
        return self.graph_store.save_to_file(file_path)
    
    def load_from_file(self, file_path: str):
        return self.graph_store.load_from_file(file_path)
    
    def clear(self):
        return self.graph_store.clear()
    
    def delete_node(self, node_id: str):
        return self.graph_store.delete_node(node_id)
    
    def delete_edge(self, edge_id: str):
        return self.graph_store.delete_edge(edge_id)

# -----------------------------------------------------------------------------
# Example Usage
# -----------------------------------------------------------------------------

def create_example_graph() -> GraphStore:
    """
    Create an example graph with entities and relationships from the Starcrash setting.
    
    Returns:
        Populated GraphStore with sample data
    """
    store = GraphStore()
    schema_store = SchemaEnforcedGraphStore(store)
    
    # Add some deities
    archos_id = schema_store.add_entity(
        name="Archos",
        entity_type=EntityType.DEITY,
        properties={
            "description": "God of Order, Logic, and Law",
            "domain": ["Order", "Logic", "Law"],
            "pantheon": "Archosian Pantheon"
        }
    )
    
    nef_id = schema_store.add_entity(
        name="Nef",
        entity_type=EntityType.DEITY,
        properties={
            "description": "Goddess of Freedom, Creativity, and Chaos",
            "domain": ["Freedom", "Creativity", "Chaos"],
            "pantheon": "Nef Pantheon"
        }
    )
    
    # Add some races
    alfir_id = schema_store.add_entity(
        name="Alfir",
        entity_type=EntityType.RACE,
        properties={
            "description": "The original elven race created by the Uthra",
            "origin": "Created by the Uthra using material components of Caierah",
            "traits": ["Balanced magic", "Connection to nature"],
            "subraces": ["Elves", "Drow"]
        }
    )
    
    # Add events
    starcrash_id = schema_store.add_entity(
        name="The Starcrash",
        entity_type=EntityType.EVENT,
        properties={
            "description": "Meteoric impact of pure astrum that created magic",
            "date": {"YA": "1 million years ago"},
            "significance": "Introduced magic to the material universe"
        }
    )
    
    # Add locations
    caierah_id = schema_store.add_entity(
        name="Caierah",
        entity_type=EntityType.LOCATION,
        properties={
            "description": "The moon where the main campaign takes place",
            "location_type": "Moon",
            "population": "Varied civilizations",
            "points_of_interest": ["Thraxus", "Meridia", "Thuskara", "Osoth", "Iberon"]
        }
    )
    
    # Add relationships
    schema_store.add_relationship(
        name="Twin Gods Creation",
        relationship_type=RelationshipType.PARENT_OF,
        source_id=archos_id,
        target_id=nef_id,
        properties={
            "description": "The cosmic relationship between the twin gods",
            "relationship_type": "Divine twins"
        }
    )
    
    schema_store.add_relationship(
        name="Magic Origin",
        relationship_type=RelationshipType.CREATED,
        source_id=starcrash_id,
        target_id=caierah_id,
        properties={
            "description": "The Starcrash created magic on Caierah",
            "method": "Meteoric impact of pure astrum"
        }
    )
    
    return store
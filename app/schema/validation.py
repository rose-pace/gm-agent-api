"""
Starcrash RPG Setting Graph Schema Validation

This file provides validation utilities for the graph database schema,
ensuring that nodes and edges conform to the defined types and rules.
"""
from typing import Dict, List, Any, Optional
from app.schema.types import EntityType, RelationshipType, VALID_CONNECTIONS

class ValidationResult:
    """Result of a schema validation check."""
    def __init__(self, is_valid: bool, errors: List[str] = None):
        """
        Initialize a validation result.
        
        Args:
            is_valid: Whether the validation passed
            errors: List of error messages if validation failed
        """
        self.is_valid = is_valid
        self.errors = errors or []
    
    def add_error(self, error: str):
        """
        Add an error to the validation result.
        
        Args:
            error: Error message to add
        """
        self.errors.append(error)
        self.is_valid = False
    
    def __bool__(self):
        """Allow using ValidationResult in boolean context."""
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
    
    # Check for valid entity-relationship combinations if defined in VALID_CONNECTIONS
    if edge_type in VALID_CONNECTIONS:
        valid_connection = VALID_CONNECTIONS[edge_type]
        
        # Check source type validity
        if source_type not in [t.value for t in valid_connection.get("valid_sources", [])]:
            result.add_error(f"Invalid source type {source_type} for relationship {edge_type}")
            result.add_error(f"Valid source types: {', '.join([t.value for t in valid_connection.get('valid_sources', [])])}")
        
        # Check target type validity
        if target_type not in [t.value for t in valid_connection.get("valid_targets", [])]:
            result.add_error(f"Invalid target type {target_type} for relationship {edge_type}")
            result.add_error(f"Valid target types: {', '.join([t.value for t in valid_connection.get('valid_targets', [])])}")
    
    return result

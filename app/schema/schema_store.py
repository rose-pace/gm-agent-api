"""
Schema Enforced Graph Store

This module provides a wrapper around the GraphStore that enforces
schema validation rules for the Starcrash setting graph database.
"""
from typing import Dict, Any, Optional
from app.db.graph_store import GraphStore
from app.models.graph_models import GraphNode, GraphEdge
from app.schema.validation import validate_node, validate_edge

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
        """
        Get a node by ID.
        
        Args:
            node_id: ID of the node to retrieve
            
        Returns:
            The node if found, None otherwise
        """
        return self.graph_store.get_node(node_id)
    
    def get_edge(self, edge_id: str):
        """
        Get an edge by ID.
        
        Args:
            edge_id: ID of the edge to retrieve
            
        Returns:
            The edge if found, None otherwise
        """
        return self.graph_store.get_edge(edge_id)
    
    def get_nodes_by_type(self, node_type: str):
        """
        Get all nodes of a specific type.
        
        Args:
            node_type: The type of nodes to retrieve
            
        Returns:
            List of nodes with the specified type
        """
        return self.graph_store.get_nodes_by_type(node_type)
    
    def get_node_by_name(self, name: str):
        """
        Get a node by its name.
        
        Args:
            name: Name of the node to retrieve
            
        Returns:
            The node if found, None otherwise
        """
        return self.graph_store.get_node_by_name(name)
    
    def get_related_nodes(self, node_id: str, edge_type=None, direction='outgoing'):
        """
        Get all nodes related to this node, optionally filtered by edge type and direction.
        
        Args:
            node_id: ID of the node to find relationships for
            edge_type: Optional type of relationships to filter by
            direction: 'outgoing', 'incoming', or 'both' to specify relationship direction
            
        Returns:
            List of tuples containing (related_node, edge_between_nodes)
        """
        return self.graph_store.get_related_nodes(node_id, edge_type, direction)
    
    def find_path(self, start_node_id: str, end_node_id: str, max_depth=5):
        """
        Find a path between two nodes using breadth-first search.
        
        Args:
            start_node_id: ID of the starting node
            end_node_id: ID of the target node
            max_depth: Maximum path length to consider
            
        Returns:
            List of (node, edge) tuples representing the path, or None if no path exists
        """
        return self.graph_store.find_path(start_node_id, end_node_id, max_depth)
    
    def find_nodes_by_property(self, prop_name: str, prop_value: Any):
        """
        Find nodes with a specific property value.
        
        Args:
            prop_name: Name of the property to search
            prop_value: Value to match
            
        Returns:
            List of nodes with matching property
        """
        return self.graph_store.find_nodes_by_property(prop_name, prop_value)
    
    def save_to_file(self, file_path: str):
        """
        Save the graph to disk.
        
        Args:
            file_path: Path to save the graph data
        """
        return self.graph_store.save_to_file(file_path)
    
    def load_from_file(self, file_path: str):
        """
        Load the graph from disk.
        
        Args:
            file_path: Path to load the graph data from
        """
        return self.graph_store.load_from_file(file_path)
    
    def clear(self):
        """
        Clear all data from the graph.
        """
        return self.graph_store.clear()
    
    def delete_node(self, node_id: str):
        """
        Delete a node and all its connected edges.
        
        Args:
            node_id: ID of the node to delete
            
        Returns:
            True if node was deleted, False if it didn't exist
        """
        return self.graph_store.delete_node(node_id)
    
    def delete_edge(self, edge_id: str):
        """
        Delete an edge.
        
        Args:
            edge_id: ID of the edge to delete
            
        Returns:
            True if edge was deleted, False if it didn't exist
        """
        return self.graph_store.delete_edge(edge_id)

from typing import Dict, List, Optional, Any, Set, Tuple
import json
import os
from collections import defaultdict
from app.models.graph_models import GraphNode, GraphEdge

class GraphStore:
    """
    In-memory graph data store for entities and their relationships.
    Provides CRUD operations for nodes and edges, as well as persistence.
    """
    
    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize an empty graph store or load from file if specified.
        
        Args:
            file_path: Optional path to load graph data from disk
        """
        # Core storage for nodes and edges
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        
        # Indexes for efficient querying
        self.node_type_index: Dict[str, Set[str]] = defaultdict(set)
        self.node_name_index: Dict[str, str] = {}
        self.outgoing_edges: Dict[str, List[str]] = defaultdict(list)
        self.incoming_edges: Dict[str, List[str]] = defaultdict(list)
        self.edge_type_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Load data if file path is provided
        if file_path and os.path.exists(file_path):
            self.load_from_file(file_path)
    
    def add_node(self, node: GraphNode) -> str:
        """
        Add a node to the graph.
        
        Args:
            node: The node to add
            
        Returns:
            The ID of the added node
        """
        # Store the node
        self.nodes[node.id] = node
        
        # Update indexes
        self.node_type_index[node.type].add(node.id)
        self.node_name_index[node.name] = node.id
        
        return node.id
    
    def add_edge(self, edge: GraphEdge) -> str:
        """
        Add an edge between nodes.
        
        Args:
            edge: The edge to add
            
        Returns:
            The ID of the added edge
            
        Raises:
            ValueError: If source or target nodes don't exist
        """
        # Validate source and target nodes exist
        if edge.source_id not in self.nodes:
            raise ValueError(f'Source node {edge.source_id} does not exist')
        if edge.target_id not in self.nodes:
            raise ValueError(f'Target node {edge.target_id} does not exist')
        
        # Store the edge
        self.edges[edge.id] = edge
        
        # Update indexes
        self.outgoing_edges[edge.source_id].append(edge.id)
        self.incoming_edges[edge.target_id].append(edge.id)
        self.edge_type_index[edge.type].add(edge.id)
        
        return edge.id
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """
        Get a node by ID.
        
        Args:
            node_id: ID of the node to retrieve
            
        Returns:
            The node if found, None otherwise
        """
        return self.nodes.get(node_id)
    
    def get_edge(self, edge_id: str) -> Optional[GraphEdge]:
        """
        Get an edge by ID.
        
        Args:
            edge_id: ID of the edge to retrieve
            
        Returns:
            The edge if found, None otherwise
        """
        return self.edges.get(edge_id)
    
    def get_nodes_by_type(self, node_type: str) -> List[GraphNode]:
        """
        Get all nodes of a specific type.
        
        Args:
            node_type: The type of nodes to retrieve
            
        Returns:
            List of nodes with the specified type
        """
        node_ids = self.node_type_index.get(node_type, set())
        return [self.nodes[node_id] for node_id in node_ids]
    
    def get_node_by_name(self, name: str) -> Optional[GraphNode]:
        """
        Get a node by its name.
        
        Args:
            name: Name of the node to retrieve
            
        Returns:
            The node if found, None otherwise
        """
        node_id = self.node_name_index.get(name)
        if node_id:
            return self.nodes.get(node_id)
        return None
    
    def get_related_nodes(self, node_id: str, edge_type: Optional[str] = None, 
                         direction: str = 'outgoing') -> List[Tuple[GraphNode, GraphEdge]]:
        """
        Get all nodes related to this node, optionally filtered by edge type and direction.
        
        Args:
            node_id: ID of the node to find relationships for
            edge_type: Optional type of relationships to filter by
            direction: 'outgoing', 'incoming', or 'both' to specify relationship direction
            
        Returns:
            List of tuples containing (related_node, edge_between_nodes)
        """
        results = []
        
        # Handle outgoing edges (node_id -> target)
        if direction in ('outgoing', 'both'):
            edge_ids = self.outgoing_edges.get(node_id, [])
            for edge_id in edge_ids:
                edge = self.edges[edge_id]
                if edge_type is None or edge.type == edge_type:
                    target_node = self.nodes[edge.target_id]
                    results.append((target_node, edge))
        
        # Handle incoming edges (source -> node_id)
        if direction in ('incoming', 'both'):
            edge_ids = self.incoming_edges.get(node_id, [])
            for edge_id in edge_ids:
                edge = self.edges[edge_id]
                if edge_type is None or edge.type == edge_type:
                    source_node = self.nodes[edge.source_id]
                    results.append((source_node, edge))
        
        return results
    
    def find_path(self, start_node_id: str, end_node_id: str, 
                max_depth: int = 5) -> Optional[List[Tuple[GraphNode, GraphEdge]]]:
        """
        Find a path between two nodes using breadth-first search.
        
        Args:
            start_node_id: ID of the starting node
            end_node_id: ID of the target node
            max_depth: Maximum path length to consider
            
        Returns:
            List of (node, edge) tuples representing the path, or None if no path exists
        """
        if start_node_id == end_node_id:
            return [(self.nodes[start_node_id], None)]
        
        # BFS to find shortest path
        visited = {start_node_id}
        queue = [(start_node_id, [])]  # (node_id, path_so_far)
        
        while queue and len(visited) <= max_depth:
            current_id, path = queue.pop(0)
            
            # Check all outgoing edges
            for edge_id in self.outgoing_edges.get(current_id, []):
                edge = self.edges[edge_id]
                target_id = edge.target_id
                
                # If we found the target, return the path
                if target_id == end_node_id:
                    full_path = path + [(self.nodes[current_id], edge), (self.nodes[target_id], None)]
                    return full_path
                
                # Otherwise, add to queue if not visited
                if target_id not in visited:
                    visited.add(target_id)
                    new_path = path + [(self.nodes[current_id], edge)]
                    queue.append((target_id, new_path))
        
        # No path found within max_depth
        return None
    
    def find_nodes_by_property(self, prop_name: str, prop_value: Any) -> List[GraphNode]:
        """
        Find nodes with a specific property value.
        
        Args:
            prop_name: Name of the property to search
            prop_value: Value to match
            
        Returns:
            List of nodes with matching property
        """
        matching_nodes = []
        for node in self.nodes.values():
            if prop_name in node.properties and node.properties[prop_name] == prop_value:
                matching_nodes.append(node)
        return matching_nodes
    
    def save_to_file(self, file_path: str) -> None:
        """
        Save the graph to disk.
        
        Args:
            file_path: Path to save the graph data
        """
        # Create data structure to serialize
        data = {
            'nodes': [node.dict() for node in self.nodes.values()],
            'edges': [edge.dict() for edge in self.edges.values()]
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write to file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, file_path: str) -> None:
        """
        Load the graph from disk.
        
        Args:
            file_path: Path to load the graph data from
        """
        # Clear existing data
        self.nodes = {}
        self.edges = {}
        self.node_type_index = defaultdict(set)
        self.node_name_index = {}
        self.outgoing_edges = defaultdict(list)
        self.incoming_edges = defaultdict(list)
        self.edge_type_index = defaultdict(set)
        
        # Load and parse data
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Add nodes first
            for node_data in data.get('nodes', []):
                node = GraphNode(**node_data)
                self.add_node(node)
            
            # Then add edges
            for edge_data in data.get('edges', []):
                edge = GraphEdge(**edge_data)
                self.add_edge(edge)
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise ValueError(f'Error loading graph data: {str(e)}')
    
    def clear(self) -> None:
        """
        Clear all data from the graph.
        """
        self.nodes = {}
        self.edges = {}
        self.node_type_index = defaultdict(set)
        self.node_name_index = {}
        self.outgoing_edges = defaultdict(list)
        self.incoming_edges = defaultdict(list)
        self.edge_type_index = defaultdict(set)
    
    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node and all its connected edges.
        
        Args:
            node_id: ID of the node to delete
            
        Returns:
            True if node was deleted, False if it didn't exist
        """
        node = self.nodes.get(node_id)
        if not node:
            return False
        
        # Remove from indexes
        self.node_type_index[node.type].discard(node_id)
        if node.name in self.node_name_index:
            del self.node_name_index[node.name]
        
        # Delete all connected edges
        for edge_id in list(self.outgoing_edges.get(node_id, [])):
            self.delete_edge(edge_id)
        
        for edge_id in list(self.incoming_edges.get(node_id, [])):
            self.delete_edge(edge_id)
        
        # Remove from edge collections
        if node_id in self.outgoing_edges:
            del self.outgoing_edges[node_id]
        if node_id in self.incoming_edges:
            del self.incoming_edges[node_id]
        
        # Delete the node itself
        del self.nodes[node_id]
        return True
    
    def delete_edge(self, edge_id: str) -> bool:
        """
        Delete an edge.
        
        Args:
            edge_id: ID of the edge to delete
            
        Returns:
            True if edge was deleted, False if it didn't exist
        """
        edge = self.edges.get(edge_id)
        if not edge:
            return False
        
        # Remove from indexes
        self.edge_type_index[edge.type].discard(edge_id)
        
        # Remove from node connections
        if edge.source_id in self.outgoing_edges:
            self.outgoing_edges[edge.source_id] = [
                e for e in self.outgoing_edges[edge.source_id] if e != edge_id
            ]
        
        if edge.target_id in self.incoming_edges:
            self.incoming_edges[edge.target_id] = [
                e for e in self.incoming_edges[edge.target_id] if e != edge_id
            ]
        
        # Delete the edge itself
        del self.edges[edge_id]
        return True

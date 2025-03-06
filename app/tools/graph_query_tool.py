from typing import List, Dict, Any, Optional, Tuple
from app.db.graph_store import GraphStore
from app.models.graph_models import GraphNode, GraphEdge
from app.models import RAGResult

class GraphQueryTool:
    """
    Tool for querying the graph data store to find entities and relationships.
    Provides a simple interface for agents to interact with the graph data.
    """
    
    def __init__(self, graph_store: GraphStore):
        """
        Initialize the graph query tool.
        
        Args:
            graph_store: The graph store to query
        """
        self.graph_store = graph_store
        self.name = 'graph_query_tool'
        self.description = 'Get information about entities and their relationships'
    
    async def get_entity(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get an entity by ID or name.
        
        Args:
            identifier: Either an ID or name of the entity
            
        Returns:
            Dict representation of the entity or None if not found
        """
        # Try as ID first
        node = self.graph_store.get_node(identifier)
        
        # Try as name if not found
        if not node:
            node = self.graph_store.get_node_by_name(identifier)
            
        # Return formatted result
        if node:
            return self._format_node_result(node)
        return None
    
    async def get_related_entities(self, identifier: str, 
                                  relation_type: Optional[str] = None,
                                  direction: str = 'both') -> List[Dict[str, Any]]:
        """
        Get entities related to the specified entity.
        
        Args:
            identifier: ID or name of the entity
            relation_type: Optional type of relationships to filter by
            direction: 'outgoing', 'incoming', or 'both' to specify relationship direction
            
        Returns:
            List of related entities with relationship information
        """
        # First get the node ID if identifier is a name
        node_id = identifier
        node = self.graph_store.get_node(identifier)
        
        if not node:
            node = self.graph_store.get_node_by_name(identifier)
            if node:
                node_id = node.id
            else:
                return []
        
        # Get related nodes with their connecting edges
        related = self.graph_store.get_related_nodes(node_id, relation_type, direction)
        
        # Format the results
        results = []
        for related_node, edge in related:
            result = self._format_node_result(related_node)
            result['relationship'] = {
                'name': edge.name,
                'type': edge.type,
                'properties': edge.properties,
                'direction': 'outgoing' if edge.source_id == node_id else 'incoming'
            }
            results.append(result)
            
        return results
    
    async def find_path_between(self, start_identifier: str, end_identifier: str, 
                              max_depth: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Find a path between two entities.
        
        Args:
            start_identifier: ID or name of the starting entity
            end_identifier: ID or name of the target entity
            max_depth: Maximum path length to consider
            
        Returns:
            List representing the path between entities or None if no path exists
        """
        # Resolve start node ID
        start_id = start_identifier
        start_node = self.graph_store.get_node(start_identifier)
        if not start_node:
            start_node = self.graph_store.get_node_by_name(start_identifier)
            if start_node:
                start_id = start_node.id
            else:
                return None
                
        # Resolve end node ID
        end_id = end_identifier
        end_node = self.graph_store.get_node(end_identifier)
        if not end_node:
            end_node = self.graph_store.get_node_by_name(end_identifier)
            if end_node:
                end_id = end_node.id
            else:
                return None
        
        # Find path
        path = self.graph_store.find_path(start_id, end_id, max_depth)
        
        # Format results
        if not path:
            return None
            
        result_path = []
        for node, edge in path:
            step = self._format_node_result(node)
            if edge:
                step['via_relationship'] = {
                    'name': edge.name,
                    'type': edge.type
                }
            result_path.append(step)
            
        return result_path
    
    async def search_entities(self, property_name: str, property_value: Any, 
                           entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for entities with specific property values.
        
        Args:
            property_name: Name of the property to search
            property_value: Value to match
            entity_type: Optional entity type to filter by
            
        Returns:
            List of matching entities
        """
        # Get all nodes by property
        nodes = self.graph_store.find_nodes_by_property(property_name, property_value)
        
        # Filter by type if specified
        if entity_type:
            nodes = [node for node in nodes if node.type == entity_type]
            
        # Format results
        return [self._format_node_result(node) for node in nodes]
    
    async def enrich_rag_results(self, result: RAGResult) -> RAGResult:
        """
        Add relationship information to RAG results.
        
        Args:
            result: The RAG result to enrich
            
        Returns:
            Enhanced RAG result with graph relationship data
        """
        # Process the text to identify potential entities
        # This is a simple implementation - in production you might use NER or other techniques
        enriched_result = result
        
        # Simple extraction of entity names that might be in the knowledge base
        # For each source in the RAG result
        for source in enriched_result.sources:
            # Check if source has a title or content field we can use as an entity identifier
            entity_name = source.get('title', source.get('content', '')[:50])
            
            # Try to find this entity in the graph
            entity = await self.get_entity(entity_name)
            if entity:
                # Add entity data to the source
                source['entity_data'] = entity
                
                # Add relationship data
                related = await self.get_related_entities(entity['id'])
                if related:
                    source['related_entities'] = related
        
        return enriched_result
    
    def _format_node_result(self, node: GraphNode) -> Dict[str, Any]:
        """
        Format a node into a standardized result dictionary.
        
        Args:
            node: The node to format
            
        Returns:
            Dict representing the node
        """
        return {
            'id': node.id,
            'name': node.name,
            'type': node.type,
            'properties': node.properties
        }

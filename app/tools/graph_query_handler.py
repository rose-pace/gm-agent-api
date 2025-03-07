"""
Graph Query Handler

This module provides a specialized handler that can use the graph database
to answer natural language questions about RPG campaign settings.
"""

from typing import Dict, List, Any, Optional
import re
import asyncio

from app.db.graph_store import GraphStore
from app.tools.graph_query_tool import GraphQueryTool

class GraphQueryHandler:
    """
    Handler class that interprets natural language queries about a campaign setting
    and uses the graph database to find answers.
    """
    
    def __init__(self, graph_tool: GraphQueryTool):
        """
        Initialize the query handler with a graph tool.
        
        Args:
            graph_tool: The graph query tool to use for database operations
        """
        self.graph_tool = graph_tool
    
    async def answer_query(self, query: str) -> str:
        """
        Answer a query about the campaign setting.
        
        Args:
            query: Natural language query
            
        Returns:
            Response based on graph database information
        """
        # Simple keyword-based query routing
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["created", "made", "built"]):
            return await self._handle_creation_query(query)
        elif any(word in query_lower for word in ["located", "where", "place"]):
            return await self._handle_location_query(query)
        elif any(word in query_lower for word in ["related", "connection", "relationship"]):
            return await self._handle_relationship_query(query)
        elif any(word in query_lower for word in ["path", "connected", "between", "link"]):
            return await self._handle_path_query(query)
        else:
            # Generic entity lookup
            return await self._handle_entity_query(query)
    
    async def _handle_creation_query(self, query: str) -> str:
        """Handle creation-related queries."""
        # Extract entity names from query using simple pattern matching
        words = query.replace("?", "").replace(".", "").split()
        
        for i, word in enumerate(words):
            if word.lower() in ["created", "made", "built"] and i > 0 and i < len(words) - 1:
                creator_name = words[i-1]
                created_name = words[i+1]
                
                # Look up the entities
                creator = await self.graph_tool.get_entity(creator_name)
                if not creator:
                    return f"I don't have information about {creator_name} in my database."
                
                # Get related entities with creation relationships
                # Note: We're not specifying a specific relationship type like before
                # Instead we'll check the relationship types we get back
                related = await self.graph_tool.get_related_entities(
                    creator["id"], 
                    direction="outgoing"
                )
                
                # Filter for creation-type relationships
                creation_relationships = []
                for entity in related:
                    rel_type = entity.get("relationship", {}).get("type", "").lower()
                    if any(create_word in rel_type for create_word in ["creat", "made", "built", "forge"]):
                        creation_relationships.append(entity)
                        if entity["name"].lower() == created_name.lower():
                            return f"Yes, {creator['name']} created {entity['name']}. {entity.get('relationship', {}).get('properties', {}).get('description', '')}"
                
                # Check for any creations by this entity
                if creation_relationships:
                    creations = ", ".join([entity["name"] for entity in creation_relationships])
                    return f"I don't have information that {creator['name']} created {created_name}, but they did create: {creations}."
                else:
                    return f"I don't have any information about what {creator['name']} created."
        
        return "I couldn't understand your creation question. Try asking something like 'Did X create Y?'"
    
    async def _handle_location_query(self, query: str) -> str:
        """Handle location-related queries."""
        # Extract entity name from query using simple pattern matching
        words = query.replace("?", "").replace(".", "").split()
        words = [word.lower() for word in words]
        
        if "where" in words:
            where_index = words.index("where")
            if where_index + 2 < len(words) and words[where_index+1] == "is":
                entity_name = words[where_index+2]
                
                # Look up the entity
                entity = await self.graph_tool.get_entity(entity_name)
                if not entity:
                    return f"I don't have information about {entity_name} in my database."
                
                # Look for location relationships without specifying exact relationship type
                related = await self.graph_tool.get_related_entities(
                    entity["id"],
                    direction="outgoing"
                )
                
                # Filter for location-type relationships
                location_relationships = []
                for rel_entity in related:
                    rel_type = rel_entity.get("relationship", {}).get("type", "").lower()
                    if any(loc_word in rel_type for loc_word in ["locat", "in", "at", "place"]):
                        location_relationships.append(rel_entity)
                
                if location_relationships:
                    locations = ", ".join([location["name"] for location in location_relationships])
                    return f"{entity['name']} is located in {locations}."
                else:
                    # Check if this entity is a location that contains other entities
                    contained = await self.graph_tool.get_related_entities(
                        entity["id"],
                        direction="incoming"
                    )
                    
                    # Filter for location-type relationships
                    contained_entities = []
                    for rel_entity in contained:
                        rel_type = rel_entity.get("relationship", {}).get("type", "").lower()
                        if any(loc_word in rel_type for loc_word in ["locat", "in", "at", "place"]):
                            contained_entities.append(rel_entity)
                    
                    if contained_entities:
                        entities = ", ".join([item["name"] for item in contained_entities])
                        return f"{entity['name']} is a location that contains: {entities}."
                    else:
                        # Check properties for location information
                        properties = entity.get("properties", {})
                        for key, value in properties.items():
                            if any(loc_word in key.lower() for loc_word in ["location", "place", "where"]):
                                return f"{entity['name']} is located in {value}."
                        
                        return f"I don't have specific location information for {entity['name']}."
        
        return "I couldn't understand your location question. Try asking something like 'Where is X?'"
    
    async def _handle_relationship_query(self, query: str) -> str:
        """Handle queries about relationships between entities."""
        # Extract entity names from query using simple pattern matching
        words = query.replace("?", "").replace(".", "").split()
        
        # Look for "between" pattern: "relationship between X and Y"
        if "between" in words:
            between_index = words.index("between")
            if between_index + 3 < len(words) and "and" in words[between_index+1:]:
                # Find the "and" after "between"
                remaining = words[between_index+1:]
                and_index = remaining.index("and")
                
                entity1_name = remaining[0]
                entity2_name = remaining[and_index+1]
                
                # Look up the entities
                entity1 = await self.graph_tool.get_entity(entity1_name)
                entity2 = await self.graph_tool.get_entity(entity2_name)
                
                if not entity1:
                    return f"I don't have information about {entity1_name} in my database."
                if not entity2:
                    return f"I don't have information about {entity2_name} in my database."
                
                # Find path between them
                path = await self.graph_tool.find_path_between(entity1["id"], entity2["id"])
                
                if path:
                    # Format the path as a readable relationship
                    path_str = []
                    for i, step in enumerate(path):
                        if i > 0:
                            relation = step.get("via_relationship", {}).get("name", "is connected to")
                            path_str.append(f"→ {relation} → {step['name']}")
                        else:
                            path_str.append(step["name"])
                    
                    return "Relationship: " + " ".join(path_str)
                else:
                    return f"I couldn't find a direct relationship between {entity1['name']} and {entity2['name']} in my database."
        
        # Handle "related to X" pattern
        if "related" in words and "to" in words:
            related_index = words.index("related")
            if related_index + 2 < len(words) and words[related_index+1] == "to":
                entity_name = words[related_index+2]
                
                # Look up the entity
                entity = await self.graph_tool.get_entity(entity_name)
                if not entity:
                    return f"I don't have information about {entity_name} in my database."
                
                # Get all relationships
                related = await self.graph_tool.get_related_entities(
                    entity["id"], 
                    direction="both"
                )
                
                if related:
                    # Format relationships
                    relationships = []
                    for item in related:
                        rel = item.get("relationship", {})
                        direction = rel.get("direction", "")
                        rel_name = rel.get("name", "is connected to")
                        
                        if direction == "outgoing":
                            relationships.append(f"{entity['name']} {rel_name} {item['name']}")
                        else:
                            relationships.append(f"{item['name']} {rel_name} {entity['name']}")
                    
                    return "Relationships:\n- " + "\n- ".join(relationships)
                else:
                    return f"I don't have any relationship information for {entity['name']} in my database."
        
        return "I couldn't understand your relationship question. Try asking something like 'What is the relationship between X and Y?' or 'What is related to Z?'"
    
    async def _handle_path_query(self, query: str) -> str:
        """Handle queries about paths or connections between entities."""
        # Extract entity names from query using simple pattern matching
        words = query.replace("?", "").replace(".", "").split()
        
        # Look for "between" pattern: "path between X and Y"
        if "between" in words:
            between_index = words.index("between")
            if between_index + 3 < len(words) and "and" in words[between_index+1:]:
                # Find the "and" after "between"
                remaining = words[between_index+1:]
                and_index = remaining.index("and")
                
                entity1_name = remaining[0]
                entity2_name = remaining[and_index+1]
                
                # Look up the entities
                entity1 = await self.graph_tool.get_entity(entity1_name)
                entity2 = await self.graph_tool.get_entity(entity2_name)
                
                if not entity1:
                    return f"I don't have information about {entity1_name} in my database."
                if not entity2:
                    return f"I don't have information about {entity2_name} in my database."
                
                # Find path between them
                path = await self.graph_tool.find_path_between(entity1["id"], entity2["id"])
                
                if path:
                    # Format the path as a readable relationship
                    path_description = f"Path from {entity1['name']} to {entity2['name']}:\n"
                    
                    for i, step in enumerate(path):
                        if i > 0:
                            relation = step.get("via_relationship", {})
                            rel_name = relation.get("name", "connected to")
                            rel_type = relation.get("type", "")
                            path_description += f"→ {rel_name} ({rel_type}) → {step['name']}\n"
                        else:
                            path_description += f"Start: {step['name']}\n"
                    
                    return path_description
                else:
                    return f"I couldn't find a connection path between {entity1['name']} and {entity2['name']} in my database."
        
        return "I couldn't understand your path question. Try asking something like 'What is the path between X and Y?'"
    
    async def _handle_entity_query(self, query: str) -> str:
        """Handle general entity information queries."""
        # Try to extract an entity name from the query
        words = query.replace("?", "").replace(".", "").split()
        
        # Try each word as a potential entity
        for word in words:
            entity = await self.graph_tool.get_entity(word)
            if entity:
                # Format entity information
                info = f"Information about {entity['name']} ({entity['type']}):\n\n"
                
                # Add description if available
                if "description" in entity.get("properties", {}):
                    info += f"{entity['properties']['description']}\n\n"
                
                # Include other properties
                other_props = []
                for key, value in entity.get("properties", {}).items():
                    if key != "description" and key != "information_source":
                        if isinstance(value, list):
                            value_str = ", ".join(value)
                            other_props.append(f"{key}: {value_str}")
                        else:
                            other_props.append(f"{key}: {value}")
                
                if other_props:
                    info += "Additional information:\n- " + "\n- ".join(other_props)
                
                # Get relationships
                related = await self.graph_tool.get_related_entities(entity["id"])
                if related:
                    info += "\n\nRelationships:\n"
                    for item in related:
                        rel = item.get("relationship", {})
                        direction = rel.get("direction", "")
                        rel_type = rel.get("type", "connected")
                        
                        if direction == "outgoing":
                            info += f"- {entity['name']} {rel_type} {item['name']}\n"
                        else:
                            info += f"- {item['name']} {rel_type} {entity['name']}\n"
                
                return info
        
        # If no entity found, try to extract key terms
        if "who" in words or "what" in words:
            # Look for capitalized words as potential entity names
            key_terms = [word for word in words if word[0].isupper()]
            if key_terms:
                # Search for entities with a matching name
                for term in key_terms:
                    entities = await self.graph_tool.search_entities("name", term)
                    if entities:
                        return f"Found information about {term}:\n\n" + "\n".join([e["name"] for e in entities])
        
        return "I couldn't find specific information about the entities in your query. Try asking about a specific name."

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid

class GraphNode(BaseModel):
    """
    Entity node in the graph store representing a game element like a character or location.
    
    Attributes:
        id: Unique identifier for the node
        name: Human-readable name of the entity
        type: Classification of the entity (e.g., 'character', 'location')
        properties: Additional key-value data associated with this entity
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    """
    Relationship edge between nodes in the graph store.
    
    Attributes:
        id: Unique identifier for the edge
        name: Human-readable name of the relationship
        type: Classification of the relationship (e.g., 'located_in', 'knows')
        source_id: ID of the source node
        target_id: ID of the target node
        properties: Additional key-value data associated with this relationship
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str
    source_id: str
    target_id: str
    properties: Dict[str, Any] = Field(default_factory=dict)

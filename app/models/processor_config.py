"""
Processor Configuration Models

Defines Pydantic models for configuring document processors.
"""
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ChunkingStrategy(str, Enum):
    """Available chunking strategies for text processing."""
    FIXED = 'fixed'
    MARKDOWN = 'markdown'
    YAML = 'yaml'
    SLIDING = 'sliding'


class VectorProcessorConfig(BaseModel):
    """Configuration for vector store processor."""
    chunking_strategy: ChunkingStrategy = Field(
        default=ChunkingStrategy.MARKDOWN,
        description='Strategy to use for document chunking'
    )
    chunk_size: int = Field(
        default=1000,
        description='Target chunk size (characters or tokens depending on strategy)'
    )
    chunk_overlap: int = Field(
        default=200,
        description='Overlap between consecutive chunks'
    )


class EntityExtractionPattern(BaseModel):
    """Configuration for entity extraction patterns."""
    pattern_type: str = Field(..., description='Type of entity to extract')
    regex_pattern: Optional[str] = Field(None, description='Regular expression pattern')
    yaml_paths: List[str] = Field(default_factory=list, description='YAML paths to extract from')
    default_properties: Dict[str, Any] = Field(default_factory=dict, description='Default properties')

class RelationshipExtractionPattern(BaseModel):
    """Configuration for relationship extraction patterns."""
    relationship_type: str = Field(..., description='Type of relationship to extract')
    regex_pattern: str = Field(..., description='Regular expression pattern')
    source_group: int = Field(default=1, description='Regex group for source entity')
    target_group: int = Field(default=2, description='Regex group for target entity')
    default_properties: Dict[str, Any] = Field(default_factory=dict, description='Default properties')

class GraphProcessorConfig(BaseModel):
    """Configuration for graph database processor."""
    extract_entities: bool = Field(
        default=True, 
        description='Whether to extract entities from documents'
    )
    extract_relationships: bool = Field(
        default=True, 
        description='Whether to extract relationships from documents'
    )
    validate_schema: bool = Field(
        default=True, 
        description='Whether to enforce schema validation'
    )
    default_entity_type: str = Field(
        default='ENTITY', 
        description='Default entity type for extracted entities'
    )
    entity_patterns: List[EntityExtractionPattern] = Field(
        default_factory=list,
        description='Patterns for extracting entities'
    )
    relationship_patterns: List[RelationshipExtractionPattern] = Field(
        default_factory=list,
        description='Patterns for extracting relationships'
    )


class ProcessorRegistry(BaseModel):
    """Registry of available processors and their configurations."""
    vector_processor: Optional[VectorProcessorConfig] = None
    graph_processor: Optional[GraphProcessorConfig] = None
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True

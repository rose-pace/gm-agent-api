# Starcrash Graph Database Implementation

This extension to the `gm-agent-api` project adds a comprehensive graph database for managing the complex relationships in the Starcrash RPG setting. The graph database enables rich querying of entities, relationships, and pathfinding between connected concepts.

## Features

- **Comprehensive Schema**: Defines entity types (DEITY, LOCATION, NPC, etc.) and relationship types (CREATED, LOCATED_IN, ALLY_OF, etc.)
- **Schema Validation**: Ensures data integrity when adding nodes and relationships
- **Document Loader**: Extracts entities and relationships from Markdown files
- **Query Agent**: Answers natural language questions using the graph database

## Components

### Schema Definition

The schema is defined in `app/schema/graph_schema.py` and includes:

- Entity types for lore (DEITY, RACE, LOCATION, EVENT, etc.)
- Entity types for gameplay (NPC, FACTION, PARTY_MEMBER, etc.)
- Relationship types for lore connections (CREATED, RULES, CAUSED, etc.)
- Relationship types for social relationships (ALLY_OF, FAMILY_OF, TEACHES, etc.)
- Property definitions for each entity and relationship type

### Document Graph Loader

Located in `scripts/document_graph_loader.py`, this utility:

- Extracts entities from Markdown files with YAML blocks
- Identifies relationships between entities
- Populates the graph database with structured information

### Graph Agent

Found in `app/agents/graph_agent.py`, this class:

- Answers queries about the Starcrash setting using the graph
- Handles questions about entities, locations, relationships, and connections
- Provides pathfinding between related concepts

## Usage

### Setting Up the Graph Database

1. **Initialize the Graph Store**:

```python
from app.db.graph_store import GraphStore
from app.schema.graph_schema import SchemaEnforcedGraphStore

# Create a new graph store
graph_store = GraphStore()

# Wrap with schema validation
schema_store = SchemaEnforcedGraphStore(graph_store)
```

2. **Adding Entities and Relationships**:

```python
# Add an entity
diety_id = schema_store.add_entity(
    name="Archos",
    entity_type="DEITY",
    properties={
        "description": "God of Order, Logic, and Law",
        "domain": ["Order", "Logic", "Law"],
        "pantheon": "Archosian Pantheon"
    }
)

# Add a relationship
schema_store.add_relationship(
    name="Twin Gods Creation",
    relationship_type="PARENT_OF",
    source_id=source_id,
    target_id=target_id,
    properties={
        "description": "The cosmic relationship between the twin gods"
    }
)
```

3. **Loading from Documents**:

```bash
python scripts/document_graph_loader.py \
    --documents_dir data/documents \
    --graph_path data/starcrash_graph.json
```

4. **Using the Graph Agent**:

```python
from app.agents.graph_agent import StarcrashGraphAgent
import asyncio

async def ask_question():
    agent = StarcrashGraphAgent("data/starcrash_graph.json")
    answer = await agent.answer_query("What is the relationship between Archos and Nef?")
    print(answer)

asyncio.run(ask_question())
```

## Integration with LLM Agents

This graph database can be integrated with LLM agents to enhance their knowledge retrieval capabilities:

1. **RAG Enhancement**: Use the graph to enrich document retrieval with relationship data
2. **Complex Queries**: Answer complex queries that require traversing relationships
3. **Knowledge Verification**: Cross-check generated content against structured data

## Schema Modification

To extend the schema for your own needs:

1. Add new entity types to the `EntityType` enum in `graph_schema.py`
2. Add new relationship types to the `RelationshipType` enum
3. Create property classes for your new types
4. Update the `ENTITY_PROPERTIES` and `RELATIONSHIP_PROPERTIES` dictionaries

## Future Enhancements

- NLP-based entity extraction from text
- Automated schema inference from documents
- Visualization tools for exploring the graph
- Integration with external graph databases like Neo4j
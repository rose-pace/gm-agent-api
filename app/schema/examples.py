"""
Example Graph Creation for Starcrash Setting

This module provides utility functions to create example graph data
that demonstrates the schema and data structure for the Starcrash setting.
"""
from app.db.graph_store import GraphStore
from app.schema.schema_store import SchemaEnforcedGraphStore
from app.schema.types import EntityType, RelationshipType

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

def create_larger_example():
    """
    Create a more extensive example graph with additional entities and relationships.
    
    Returns:
        Populated GraphStore with comprehensive sample data
    """
    store = GraphStore()
    schema_store = SchemaEnforcedGraphStore(store)
    
    # Start with the basic example
    basic_store = create_example_graph()
    
    # Copy all nodes and edges from the basic example
    for node_id, node in basic_store.nodes.items():
        schema_store.add_entity(
            name=node.name,
            entity_type=node.type,
            properties=node.properties
        )
    
    for edge_id, edge in basic_store.edges.items():
        # Get the nodes by name since IDs will be different
        source_node = basic_store.get_node(edge.source_id)
        target_node = basic_store.get_node(edge.target_id)
        
        source = schema_store.get_node_by_name(source_node.name)
        target = schema_store.get_node_by_name(target_node.name)
        
        if source and target:
            schema_store.add_relationship(
                name=edge.name,
                relationship_type=edge.type,
                source_id=source.id,
                target_id=target.id,
                properties=edge.properties
            )
    
    # Add more entities and relationships
    # Add an NPC
    mage_id = schema_store.add_entity(
        name="Thalindra the Archmage",
        entity_type=EntityType.NPC,
        properties={
            "description": "An ancient elf who has studied the Starcrash for centuries",
            "race": "Alfir",
            "class_type": "Wizard",
            "level": 20,
            "motivation": "To understand the true nature of astrum magic",
            "personality": "Curious, methodical, somewhat detached from daily concerns"
        }
    )
    
    # Add an artifact
    orb_id = schema_store.add_entity(
        name="Orb of Astral Resonance",
        entity_type=EntityType.ARTIFACT,
        properties={
            "description": "A crystalline sphere that thrums with magical power",
            "powers": ["Detect magic", "Enhance spellcasting", "Store spells"],
            "materials": ["Astrum crystal", "Celestial silver"],
            "sentience": False
        }
    )
    
    # Add relationships for these new entities
    caierah = schema_store.get_node_by_name("Caierah")
    alfir = schema_store.get_node_by_name("Alfir")
    
    if caierah and mage_id:
        schema_store.add_relationship(
            name="Residence of Thalindra",
            relationship_type=RelationshipType.LOCATED_IN,
            source_id=mage_id,
            target_id=caierah.id,
            properties={
                "description": "Thalindra lives in a tower on the eastern coast of Caierah",
                "position": "Eastern Coast",
                "permanence": "Centuries"
            }
        )
    
    if alfir and mage_id:
        schema_store.add_relationship(
            name="Racial Heritage",
            relationship_type=RelationshipType.MEMBER_OF,
            source_id=mage_id,
            target_id=alfir.id,
            properties={
                "description": "Thalindra is one of the eldest living Alfir",
                "role": "Elder Sage",
                "standing": "Highly respected"
            }
        )
    
    if mage_id and orb_id:
        schema_store.add_relationship(
            name="Creator of the Orb",
            relationship_type=RelationshipType.CREATED,
            source_id=mage_id,
            target_id=orb_id,
            properties={
                "description": "Thalindra created the Orb after decades of research",
                "method": "Complex ritual during astral conjunction",
                "purpose": "To study the nature of astrum magic"
            }
        )
    
    return store

if __name__ == "__main__":
    # Create and save an example graph if this script is run directly
    store = create_larger_example()
    store.save_to_file("starcrash_example.json")
    print(f"Created example graph with {len(store.nodes)} nodes and {len(store.edges)} edges")
    print("Saved to starcrash_example.json")

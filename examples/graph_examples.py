"""
Example Graph Creation for Eternal Uruk: A Gilgamesh Campaign Setting

This module provides utility functions to create example graph data
that demonstrates the schema and data structure for the Gilgamesh campaign setting.
"""
from app.db.graph_store import GraphStore
from app.schema.schema_store import SchemaEnforcedGraphStore
from app.schema.types import EntityType, RelationshipType

def create_example_graph() -> GraphStore:
    """
    Create an example graph with entities and relationships from the Gilgamesh setting.
    
    Returns:
        Populated GraphStore with sample data
    """
    store = GraphStore()
    schema_store = SchemaEnforcedGraphStore(store)
    
    # Add some deities
    shamash_id = schema_store.add_entity(
        name='Shamash',
        entity_type=EntityType.DEITY,
        properties={
            'description': 'God of Sun and Justice',
            'domain': ['Sun', 'Justice', 'Truth'],
            'alignment': 'Lawful Good',
            'divine_portfolio': 'Light, truth, judgment, aid to heroes',
            'symbol': 'Sun disc with rays'
        }
    )
    
    ishtar_id = schema_store.add_entity(
        name='Ishtar',
        entity_type=EntityType.DEITY,
        properties={
            'description': 'Goddess of Love, War, and Fertility',
            'domain': ['Love', 'War', 'Fertility'],
            'alignment': 'Chaotic Neutral',
            'divine_portfolio': 'Passion, battle, desire, rejection',
            'symbol': 'Eight-pointed star'
        }
    )
    
    # Add some heroes
    gilgamesh_id = schema_store.add_entity(
        name='Gilgamesh',
        entity_type=EntityType.HERO,
        properties={
            'description': 'Two-thirds divine, one-third mortal king of Uruk',
            'domains': ['Leadership', 'Strength', 'Civilization'],
            'motivation': 'Initially glory and power, later immortality, finally wisdom',
            'appearance': 'Imposing figure of great height and strength, adorned with royal regalia'
        }
    )
    
    # Add events
    flood_id = schema_store.add_entity(
        name='The Great Flood',
        entity_type=EntityType.EVENT,
        properties={
            'description': 'World-covering flood that destroys civilization',
            'code': 'EVT_FLD_DELUGE',
            'significance': 'Divine punishment and cleansing of the world'
        }
    )
    
    # Add locations
    uruk_id = schema_store.add_entity(
        name='Uruk',
        entity_type=EntityType.LOCATION,
        properties={
            'description': 'Mighty city-state with imposing walls, temples, and palaces',
            'location_type': 'City-State',
            'code': 'LOC_MES_URUK',
            'notable_features': ['Walls of Uruk', 'Temple of Ishtar', 'Royal Palace'],
            'points_of_interest': ['Walls of Uruk', 'Temple of Ishtar', 'Royal Palace']
        }
    )
    
    # Add relationships
    schema_store.add_relationship(
        name='Divine Protection',
        relationship_type=RelationshipType.PROTECTS,
        source_id=shamash_id,
        target_id=gilgamesh_id,
        properties={
            'description': 'Shamash provides divine guidance and protection to Gilgamesh',
            'relationship_type': 'Divine Patronage'
        }
    )
    
    schema_store.add_relationship(
        name='Ruler of',
        relationship_type=RelationshipType.RULES,
        source_id=gilgamesh_id,
        target_id=uruk_id,
        properties={
            'description': 'Gilgamesh is the king and ruler of Uruk',
            'method': 'Divine Right Kingship'
        }
    )
    
    return schema_store

def create_larger_example() -> GraphStore:
    """
    Create a more extensive example graph with additional entities and relationships
    from the Gilgamesh campaign setting.
    
    Returns:
        Populated GraphStore with comprehensive sample data
    """
    # Start with the basic example
    schema_store = create_example_graph()
    
    # Add more entities and relationships
    # Add heroes and companions
    enkidu_id = schema_store.add_entity(
        name='Enkidu',
        entity_type=EntityType.HERO,
        properties={
            'description': 'Wild man created by the gods from clay',
            'domains': ['Wilderness', 'Primal Strength', 'Friendship'],
            'motivation': 'Initially freedom, later loyalty to Gilgamesh',
            'appearance': 'Hairy, powerful body, unrefined but noble in bearing'
        }
    )
    
    # Add a monster
    humbaba_id = schema_store.add_entity(
        name='Humbaba',
        entity_type=EntityType.MONSTER,
        properties={
            'description': 'Guardian of the Cedar Forest',
            'appearance': 'Terrifying face, breath of fire, seven supernatural radiances',
            'abilities': ['Control of forest', 'Supernatural aura of fear', 'Divine protection'],
            'challenge_rating': 12
        }
    )
    
    # Add a location - Cedar Forest
    cedar_forest_id = schema_store.add_entity(
        name='Cedar Forest',
        entity_type=EntityType.LOCATION,
        properties={
            'description': 'Vast, sacred forest of immense cedar trees',
            'location_type': 'Wilderness',
            'code': 'LOC_WLD_CEDAR',
            'notable_features': [
                'Heart of the Forest',
                'Sacred Cedars',
                'Hidden Shrines'
            ]
        }
    )
    
    # Add relationships for these new entities
    gilgamesh = schema_store.get_node_by_name('Gilgamesh')
    uruk = schema_store.get_node_by_name('Uruk')
    
    if gilgamesh and enkidu_id:
        schema_store.add_relationship(
            name='Epic Friendship',
            relationship_type=RelationshipType.ALLIED_WITH,
            source_id=gilgamesh.id,
            target_id=enkidu_id,
            properties={
                'description': 'The legendary friendship between Gilgamesh and Enkidu',
                'strength': 'Unbreakable bond',
                'significance': 'Central relationship of the Epic'
            }
        )
    
    if cedar_forest_id and humbaba_id:
        schema_store.add_relationship(
            name='Guardian of the Forest',
            relationship_type=RelationshipType.GUARDS,
            source_id=humbaba_id,
            target_id=cedar_forest_id,
            properties={
                'description': 'Humbaba is the divinely appointed guardian of the Cedar Forest',
                'role': 'Protector',
                'divine_mandate': 'Appointed by Enlil'
            }
        )
    
    if gilgamesh and enkidu_id and humbaba_id:
        schema_store.add_relationship(
            name='Epic Confrontation',
            relationship_type=RelationshipType.OPPOSES,
            source_id=gilgamesh.id,
            target_id=humbaba_id,
            properties={
                'description': 'Gilgamesh and Enkidu journey to fight and slay Humbaba',
                'outcome': 'Humbaba is slain',
                'event_code': 'EVT_CED_SLAY'
            }
        )
    
    return schema_store

if __name__ == '__main__':
    # Create and save an example graph if this script is run directly
    store = create_larger_example()
    store.save_to_file('gilgamesh_example.json')
    print(f'Created example graph with {len(store.nodes)} nodes and {len(store.edges)} edges')
    print('Saved to gilgamesh_example.json')

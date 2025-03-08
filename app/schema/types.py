"""
RPG Setting Graph Schema Types

This file defines the schema types for the graph database used to store RPG setting
information for the campaign setting. It includes entity types,
relationship types, and property definitions.
"""
from enum import Enum
from typing import Dict, List, Any, TypedDict, Optional

# -----------------------------------------------------------------------------
# Entity Types (Node Types)
# -----------------------------------------------------------------------------

class EntityType(str, Enum):
    # Lore-based entities
    DEITY = "DEITY"
    RACE = "RACE"
    LOCATION = "LOCATION"
    EVENT = "EVENT"
    ERA = "ERA"
    ARTIFACT = "ARTIFACT"
    CONCEPT = "CONCEPT"
    PLANE = "PLANE"
    
    # Gameplay entities
    NPC = "NPC"
    FACTION = "FACTION"
    VILLAIN = "VILLAIN"
    MONSTER = "MONSTER"
    PARTY_MEMBER = "PARTY_MEMBER"
    QUEST = "QUEST"
    SHOP = "SHOP"
    TREASURE = "TREASURE"
    SESSION = "SESSION"

# -----------------------------------------------------------------------------
# Relationship Types (Edge Types)
# -----------------------------------------------------------------------------

class RelationshipType(str, Enum):
    # Lore relationships
    CREATED = "CREATED"               # Entity created another entity
    DESTROYED = "DESTROYED"           # Entity destroyed another entity
    RULES = "RULES"                   # Entity has authority over another entity
    CAUSED = "CAUSED"                 # Event led to another event
    LOCATED_IN = "LOCATED_IN"         # Entity is physically located within another
    MEMBER_OF = "MEMBER_OF"           # Entity belongs to a group or category
    TRANSFORMED_INTO = "TRANSFORMED_INTO"  # Entity changed into another form
    PARENT_OF = "PARENT_OF"           # Entity is the parent of another
    OCCURRED_DURING = "OCCURRED_DURING"  # Event happened during an era
    CONNECTED_TO = "CONNECTED_TO"     # Physical or metaphysical connection
    
    # Social relationships
    ALLY_OF = "ALLY_OF"               # Friendly relationship
    ENEMY_OF = "ENEMY_OF"             # Hostile relationship
    ACQUAINTED_WITH = "ACQUAINTED_WITH"  # Knows but not deeply connected
    FAMILY_OF = "FAMILY_OF"           # Related by blood or similar bond
    SERVES = "SERVES"                 # Works for or obeys
    LEADS = "LEADS"                   # Commands or directs
    PROTECTS = "PROTECTS"             # Guards or defends
    THREATENS = "THREATENS"           # Poses danger to
    HIRED = "HIRED"                   # Employed for a task
    RESCUED = "RESCUED"               # Saved from danger
    DEFEATED = "DEFEATED"             # Overcame in combat or contest
    COMPLETED = "COMPLETED"           # Finished a task or quest
    KNOWS_SECRET_ABOUT = "KNOWS_SECRET_ABOUT"  # Has hidden knowledge
    OWES_FAVOR_TO = "OWES_FAVOR_TO"   # Indebted for past assistance
    DISTRUSTS = "DISTRUSTS"           # Suspicious or wary of
    SELLS_TO = "SELLS_TO"             # Provides goods or services
    TEACHES = "TEACHES"               # Trains or educates

# -----------------------------------------------------------------------------
# Property Schemas for Entities
# -----------------------------------------------------------------------------

# Base properties every entity should have
class BaseEntityProperties(TypedDict, total=False):
    description: str                  # General description
    creation_date: str                # When entity was added to the database
    last_updated: str                 # When entity was last modified
    canonical_id: str                 # Reference ID in source material
    information_source: str           # Where the information comes from
    image_url: str                    # URL to an image representing this entity
    campaign_notes: str               # Private GM notes
    player_knowledge: str             # What players know about this entity

# Properties for Deity entities
class DeityProperties(BaseEntityProperties, total=False):
    domain: List[str]                 # Areas of divine influence
    pantheon: str                     # Divine group membership
    alignment: str                    # Moral and ethical stance
    symbol: str                       # Divine symbol
    holy_days: List[str]              # Sacred days or celebrations
    clergy_title: str                 # Title for priests of this deity
    associated_plane: str             # Connected planar domain

# Properties for Race entities
class RaceProperties(BaseEntityProperties, total=False):
    origin: str                       # How this race came to be
    traits: List[str]                 # Notable racial characteristics
    lifespan: str                     # Typical longevity
    homeland: str                     # Traditional territory
    language: List[str]               # Languages commonly spoken
    subraces: List[str]               # Variants within the race
    racial_abilities: List[str]       # Special capabilities

# Properties for Location entities
class LocationProperties(BaseEntityProperties, total=False):
    location_type: str                # City, dungeon, wilderness, etc.
    population: str                   # Approximate number of inhabitants
    government: str                   # Ruling system
    climate: str                      # Weather patterns
    resources: List[str]              # Notable resources or exports
    dangers: List[str]                # Threats or hazards
    points_of_interest: List[str]     # Notable sites
    maps: List[str]                   # References to map images
    accessibility: str                # How easy it is to reach
    coordinates: Dict[str, float]     # Position on world map

# Properties for Event entities
class EventProperties(BaseEntityProperties, total=False):
    date: Dict[str, str]              # When it occurred (in multiple dating systems)
    duration: str                     # How long it lasted
    participants: List[str]           # Who was involved
    outcome: str                      # Result of the event
    significance: str                 # Historical importance
    witnesses: List[str]              # Who observed the event
    historical_evidence: str          # How this event is known

# Properties for Era entities
class EraProperties(BaseEntityProperties, total=False):
    start_date: Dict[str, str]        # Beginning (in multiple dating systems)
    end_date: Dict[str, str]          # Ending (in multiple dating systems)
    defining_events: List[str]        # Major historical moments
    societal_changes: str             # How society evolved
    technological_level: str          # Advancement of technology/magic
    preceding_era: str                # What came before
    following_era: str                # What came after

# Properties for Artifact entities
class ArtifactProperties(BaseEntityProperties, total=False):
    creator: str                      # Who made it
    creation_date: Dict[str, str]     # When it was made
    materials: List[str]              # What it's made of
    powers: List[str]                 # Magical abilities
    current_location: str             # Where it is now
    previous_owners: List[str]        # Who has possessed it
    sentience: bool                   # Whether it has a mind
    alignment: str                    # Moral and ethical stance
    destruction_method: str           # How it can be destroyed
    game_mechanics: Dict[str, Any]    # Rules for using this item

# Properties for Concept entities
class ConceptProperties(BaseEntityProperties, total=False):
    category: str                     # Type of concept (magical, cultural, etc.)
    practitioners: List[str]          # Who uses or believes this concept
    origin: str                       # How it came to be
    limitations: List[str]            # Constraints or weaknesses
    related_concepts: List[str]       # Connected ideas
    applications: List[str]           # How it's used
    variations: List[str]             # Different forms or interpretations

# Properties for Plane entities
class PlaneProperties(BaseEntityProperties, total=False):
    plane_type: str                   # Material, elemental, divine, etc.
    physical_laws: List[str]          # How reality works here
    inhabitants: List[str]            # Native beings
    entry_points: List[str]           # How to get there
    hazards: List[str]                # Dangers specific to this plane
    affinity: List[str]               # Elements or concepts it resonates with
    parent_plane: str                 # What plane it's derived from

# Properties for NPC entities
class NPCProperties(BaseEntityProperties, total=False):
    race: str                         # Species or lineage
    class_type: str                   # Character class if applicable
    level: int                        # Power level
    occupation: str                   # Job or role
    current_location: str             # Where they are now
    motivation: str                   # What drives them
    secrets: List[str]                # Hidden information
    personality: str                  # Character traits
    appearance: str                   # Physical description
    possessions: List[str]            # Notable items they own
    stats: Dict[str, Any]             # Game statistics
    quest_giver: bool                 # Whether they offer quests
    first_appearance: str             # When introduced to campaign

# Properties for Faction entities
class FactionProperties(BaseEntityProperties, total=False):
    faction_type: str                 # Guild, kingdom, cult, etc.
    headquarters: str                 # Base of operations
    leader: str                       # Who's in charge
    influence: int                    # Power scale (1-10)
    resources: List[str]              # Available assets
    goals: List[str]                  # What they want to achieve
    territory: List[str]              # Areas they control
    allies: List[str]                 # Friendly organizations
    enemies: List[str]                # Hostile organizations
    members: List[str]                # Notable individuals
    hierarchy: str                    # Organizational structure
    founding_date: Dict[str, str]     # When established
    reputation: str                   # How they're perceived
    symbol: str                       # Identifying mark

# Properties for Villain entities
class VillainProperties(BaseEntityProperties, total=False):
    villain_type: str                 # Mastermind, enforcer, corrupted hero, etc.
    threat_level: int                 # Danger scale (1-10)
    motivation: str                   # Evil goals
    methods: List[str]                # How they operate
    minions: List[str]                # Followers or servants
    weaknesses: List[str]             # Vulnerabilities
    base: str                         # Headquarters
    schemes: List[str]                # Current plots
    backstory: str                    # Origin and history
    stats: Dict[str, Any]             # Game statistics
    escape_plans: List[str]           # How they avoid defeat

# Properties for Monster entities
class MonsterProperties(BaseEntityProperties, total=False):
    monster_type: str                 # Beast, undead, construct, etc.
    challenge_rating: float           # Difficulty rating
    habitat: List[str]                # Where they're found
    behavior: str                     # How they act
    abilities: List[str]              # Special powers
    weaknesses: List[str]             # Vulnerabilities
    loot: List[str]                   # Items they carry
    diet: str                         # What they eat
    variants: List[str]               # Different forms
    stats: Dict[str, Any]             # Game statistics
    encounter_tables: List[str]       # Where they appear in random encounters

# Properties for Party Member entities
class PartyMemberProperties(BaseEntityProperties, total=False):
    player: str                       # Real player's name
    race: str                         # Character race
    class_type: str                   # Character class
    level: int                        # Character level
    background: str                   # Character backstory
    goals: List[str]                  # Character motivations
    connections: List[Dict[str, str]] # Personal storylines/ties
    character_sheet: str              # Link to full character data
    favorite_tactics: List[str]       # Preferred methods in battle
    personality_traits: List[str]     # Character quirks and behavior
    personal_quests: List[str]        # Individual storylines

# Properties for Quest entities
class QuestProperties(BaseEntityProperties, total=False):
    quest_type: str                   # Main, side, personal
    quest_giver: str                  # Who assigned the quest
    objectives: List[str]             # What needs to be done
    rewards: List[str]                # What players get
    difficulty: int                   # Challenge scale (1-10)
    status: str                       # Active, completed, failed
    location: List[str]               # Where it takes place
    prerequisites: List[str]          # Required before starting
    follow_up: List[str]              # What happens after
    time_sensitive: bool              # Whether there's a deadline
    hidden_outcome: str               # Secret results

# Properties for Shop entities
class ShopProperties(BaseEntityProperties, total=False):
    shop_type: str                    # General, magical, blacksmith, etc.
    owner: str                        # Proprietor
    location: str                     # Where it's found
    inventory: List[Dict[str, Any]]   # What's for sale
    prices: str                       # Cost modifier (cheap, expensive)
    quality: str                      # Grade of merchandise
    specialty: str                    # Unique offerings
    haggling: bool                    # Whether negotiation is possible
    schedule: str                     # When it's open
    services: List[str]               # Non-item offerings

# Properties for Treasure entities
class TreasureProperties(BaseEntityProperties, total=False):
    treasure_type: str                # Coins, gems, magic items, etc.
    value: str                        # Worth in currency
    location: str                     # Where it's found
    guardian: str                     # What protects it
    origin: str                       # Where it came from
    curse: str                        # Negative effects
    detection: str                    # How to find it
    legal_status: str                 # Stolen, abandoned, etc.
    special_properties: List[str]     # Unique qualities

# Properties for Session entities
class SessionProperties(BaseEntityProperties, total=False):
    session_number: int               # Sequential identifier
    date_played: str                  # When the session occurred
    summary: str                      # Brief description of events
    locations_visited: List[str]      # Places the party went
    npcs_encountered: List[str]       # Characters interacted with
    quests_advanced: List[Dict[str, str]]  # Progress on objectives
    quests_completed: List[str]       # Finished storylines
    treasure_found: List[str]         # Items acquired
    combat_encounters: List[str]      # Battles fought
    player_decisions: List[str]       # Important choices made
    plot_revelations: List[str]       # Secrets uncovered
    future_hooks: List[str]           # Setup for coming sessions

# All property types mapped to entity types
ENTITY_PROPERTIES = {
    EntityType.DEITY: DeityProperties,
    EntityType.RACE: RaceProperties,
    EntityType.LOCATION: LocationProperties,
    EntityType.EVENT: EventProperties,
    EntityType.ERA: EraProperties,
    EntityType.ARTIFACT: ArtifactProperties,
    EntityType.CONCEPT: ConceptProperties,
    EntityType.PLANE: PlaneProperties,
    EntityType.NPC: NPCProperties,
    EntityType.FACTION: FactionProperties,
    EntityType.VILLAIN: VillainProperties,
    EntityType.MONSTER: MonsterProperties,
    EntityType.PARTY_MEMBER: PartyMemberProperties,
    EntityType.QUEST: QuestProperties,
    EntityType.SHOP: ShopProperties,
    EntityType.TREASURE: TreasureProperties,
    EntityType.SESSION: SessionProperties
}

# -----------------------------------------------------------------------------
# Property Schemas for Relationships
# -----------------------------------------------------------------------------

# Base properties every relationship should have
class BaseRelationshipProperties(TypedDict, total=False):
    description: str                  # Details about relationship
    strength: int                     # How strong the connection is (1-10)
    start_date: Dict[str, str]        # When the relationship began
    end_date: Dict[str, str]          # When relationship ended (if applicable)
    public_knowledge: bool            # Whether relationship is widely known
    notes: str                        # Additional information

# Properties for Created relationships
class CreatedProperties(BaseRelationshipProperties, total=False):
    method: str                       # How creation occurred
    purpose: str                      # Why it was created
    assistance: List[str]             # Others who helped
    materials: List[str]              # What was used
    timeframe: str                    # How long it took

# Properties for Destroyed relationships
class DestroyedProperties(BaseRelationshipProperties, total=False):
    method: str                       # How destruction occurred
    reason: str                       # Why it was destroyed
    witnesses: List[str]              # Who saw it happen
    remains: str                      # What's left
    aftermath: str                    # Consequences

# Properties for Rules relationships
class RulesProperties(BaseRelationshipProperties, total=False):
    authority_type: str               # Kind of rulership
    legitimacy: str                   # Source of right to rule
    opposition: List[str]             # Challengers to authority
    laws: List[str]                   # Notable regulations
    enforcement: str                  # How rules are upheld

# Properties for Caused relationships
class CausedProperties(BaseRelationshipProperties, total=False):
    mechanism: str                    # How causation worked
    directness: str                   # Immediate or indirect
    inevitability: int                # How certain the outcome was (1-10)
    awareness: bool                   # Whether causer knew outcome
    prevention_attempts: List[str]    # Efforts to stop it

# Properties for Located In relationships
class LocatedInProperties(BaseRelationshipProperties, total=False):
    position: str                     # Specific location within container
    accessibility: str                # How easily reached
    permanence: str                   # Temporary or permanent
    history: str                      # How long it's been there
    visibility: str                   # How obvious the location is

# Properties for Member Of relationships
class MemberOfProperties(BaseRelationshipProperties, total=False):
    role: str                         # Position within group
    standing: str                     # Status in the group
    responsibilities: List[str]       # Duties to perform
    benefits: List[str]               # Advantages gained
    term: str                         # Duration of membership

# Properties for Transformed Into relationships
class TransformedIntoProperties(BaseRelationshipProperties, total=False):
    cause: str                        # What triggered transformation
    reversibility: bool               # Whether it can be undone
    completeness: int                 # How total the change was (1-10)
    awareness: bool                   # Memory of previous form
    process: str                      # How transformation worked

# Properties for Parent Of relationships
class ParentOfProperties(BaseRelationshipProperties, total=False):
    relationship_type: str            # Biological, adoptive, creator
    knowledge: bool                   # Whether both know the relationship
    closeness: int                    # Emotional connection (1-10)
    responsibilities: str             # Parent's duties
    influence: str                    # Impact on child

# Properties for Occurred During relationships
class OccurredDuringProperties(BaseRelationshipProperties, total=False):
    timeframe: str                    # When during the era
    significance: str                 # Importance to the era
    typicality: int                   # How representative of era (1-10)
    recorded: bool                    # Whether the event was documented
    witnesses: List[str]              # Who observed it

# Properties for Connected To relationships
class ConnectedToProperties(BaseRelationshipProperties, total=False):
    connection_type: str              # Physical, magical, conceptual
    stability: int                    # How reliable the connection is (1-10)
    directionality: str               # One-way or bidirectional
    access_requirements: List[str]    # What's needed to use the connection
    traffic: str                      # How frequently used

# Properties for Ally Of relationships
class AllyOfProperties(BaseRelationshipProperties, total=False):
    alliance_type: str                # Military, economic, political
    terms: List[str]                  # Conditions of alliance
    reliability: int                  # How dependable (1-10)
    benefits: List[str]               # What each party gains
    public: bool                      # Whether alliance is known
    tensions: List[str]               # Points of disagreement

# Properties for Enemy Of relationships
class EnemyOfProperties(BaseRelationshipProperties, total=False):
    conflict_type: str                # Military, economic, personal
    cause: str                        # Reason for enmity
    intensity: int                    # How severe the hatred is (1-10)
    status: str                       # Active conflict or cold war
    confrontations: List[str]         # Past clashes
    peace_potential: int              # Likelihood of resolution (1-10)

# All property types mapped to relationship types
RELATIONSHIP_PROPERTIES = {
    RelationshipType.CREATED: CreatedProperties,
    RelationshipType.DESTROYED: DestroyedProperties,
    RelationshipType.RULES: RulesProperties,
    RelationshipType.CAUSED: CausedProperties,
    RelationshipType.LOCATED_IN: LocatedInProperties,
    RelationshipType.MEMBER_OF: MemberOfProperties,
    RelationshipType.TRANSFORMED_INTO: TransformedIntoProperties,
    RelationshipType.PARENT_OF: ParentOfProperties,
    RelationshipType.OCCURRED_DURING: OccurredDuringProperties,
    RelationshipType.CONNECTED_TO: ConnectedToProperties,
    RelationshipType.ALLY_OF: AllyOfProperties,
    RelationshipType.ENEMY_OF: EnemyOfProperties,
    # Add remaining relationship properties as needed
}

# Define which relationships are valid between which entity types
# This can be used for validation and documentation
VALID_CONNECTIONS = {
    RelationshipType.CREATED: {
        "valid_sources": [
            EntityType.DEITY, EntityType.NPC, EntityType.FACTION, 
            EntityType.EVENT
        ],
        "valid_targets": [
            EntityType.RACE, EntityType.LOCATION, EntityType.ARTIFACT,
            EntityType.NPC, EntityType.MONSTER
        ]
    },
    RelationshipType.DESTROYED: {
        "valid_sources": [
            EntityType.DEITY, EntityType.NPC, EntityType.FACTION, 
            EntityType.EVENT, EntityType.MONSTER, EntityType.PARTY_MEMBER
        ],
        "valid_targets": [
            EntityType.LOCATION, EntityType.ARTIFACT, EntityType.NPC,
            EntityType.FACTION
        ]
    },
    # Add more relationship validations as needed
}

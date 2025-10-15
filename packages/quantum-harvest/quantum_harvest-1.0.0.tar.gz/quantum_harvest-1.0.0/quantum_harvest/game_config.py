"""
Game Configuration Constants for Quantum Harvest

This file contains all configurable constants used throughout the game.
Modify these values to adjust game balance and mechanics without 
changing the core game code.
"""

# =============================================================================
# GAME ENVIRONMENT SETTINGS
# =============================================================================

# Map and Game Settings
DEFAULT_MAP_SIZE = 12
DEFAULT_MAX_TURNS = 1000
# DEFAULT_MAX_UNITS removed - no unit limits

# Victory Conditions
ENERGY_VICTORY_THRESHOLD = 100000.0
TERRITORY_VICTORY_THRESHOLD = 0.7
TERRITORY_VICTORY_TURNS = 10

# =============================================================================
# UNIT COSTS
# =============================================================================

UNIT_COSTS = {
    "HARVESTER": 10,
    "WARRIOR": 100,
    "SCOUT": 10
}

# =============================================================================
# BUILDING COSTS
# =============================================================================

BUILDING_COSTS = {
    "DECOHERENCE_FIELD": 100,
    "QUANTUM_BARRIER": 200,
    "QUANTUM_GATE": 100,
    "ENTANGLEMENT_ZONE": 100
}

# =============================================================================
# UNIT STATS
# =============================================================================

UNIT_STATS = {
    "HARVESTER": {
        "harvest_efficiency": 2.0,
        "combat_power": 0
    },
    "WARRIOR": {
        "harvest_efficiency": 0.0,  # Warriors cannot harvest
        "combat_power": 2.0
    },
    "SCOUT": {
        "harvest_efficiency": 1.0,
        "combat_power": 0
    }
}

# =============================================================================
# EXPLORATION RANGES
# =============================================================================

EXPLORATION_RANGES = {
    "SCOUT": 3,
    "HARVESTER": 1,
    "WARRIOR": 1
}

# =============================================================================
# COMBAT SETTINGS
# =============================================================================

# Attack Settings
WARRIOR_BASE_DAMAGE = 15.0
ATTACK_ENERGY_COST = 15
BOOSTED_ATTACK_RANGE = 4
NORMAL_ATTACK_RANGE = 1
ENTANGLEMENT_DAMAGE_MULTIPLIER = 1.5

# Combat Rewards
UNIT_DEFEAT_REWARD = 50.0

# =============================================================================
# ENERGY AND HARVESTING
# =============================================================================

# Energy Node Settings
ENERGY_NODE_MIN_VALUE = 1000
ENERGY_NODE_MAX_VALUE = 2000
ENERGY_NODE_DEPLETION_RATE = 1.0  # Energy lost per harvest

# Harvest Base Amounts (before efficiency multipliers)
HARVEST_BASE_AMOUNTS = {
    "SCOUT": 0.25,
    "HARVESTER": 0.5,
    "WARRIOR": 0  # Though warriors can't harvest (efficiency = 0)
}

# Energy Boost Multiplier
ENERGY_BOOST_MULTIPLIER = 0.2  # Each energy boost point adds 20% to harvest/damage

# =============================================================================
# QUANTUM MECHANICS
# =============================================================================

# Entanglement Zone Settings
ENTANGLEMENT_ZONE_CREATION_BASE_COST = BUILDING_COSTS.get("ENTANGLEMENT_ZONE", 100)
ENTANGLEMENT_ZONE_CREATION_BOOST_COST = 10  # Additional cost per energy boost
ENTANGLEMENT_ZONE_INITIAL_POWER = 200
ENTANGLEMENT_ZONE_BOOST_COST = 50  # Power consumed when boosting a warrior
ENTANGLEMENT_ZONE_BOOST_ATTACKS = 2  # Number of boosted attacks granted

# Decoherence Field Settings
DECOHERENCE_DAMAGE_REDUCTION = 0.5  # 50% damage reduction for units on decoherence tiles

# Quantum Gate Settings
QUANTUM_GATE_HEALTH_BOOST_PERCENTAGE = 0.5  # 50% health boost
QUANTUM_GATE_MAX_HEALTH_LIMIT = 300.0
QUANTUM_GATE_HEALTH_GAIN_COST = 50  # Energy cost for health gain action
QUANTUM_GATE_HEALTH_GAIN_AMOUNT = 50.0  # Health gained from health gain action
QUANTUM_GATE_TELEPORT_COST = 25

# =============================================================================
# MAP GENERATION
# =============================================================================

# Tile Generation Ratios (relative to map size)
ENERGY_NODE_MIN_PAIRS_RATIO = 4  # map_size // 4
ENERGY_NODE_MAX_PAIRS_RATIO = 2  # map_size // 2

BARRIER_MIN_PAIRS_RATIO = 8  # map_size // 8
BARRIER_MAX_PAIRS_RATIO = 4  # map_size // 4

DECOHERENCE_MIN_PAIRS_RATIO = 12  # map_size // 12
DECOHERENCE_MAX_PAIRS_RATIO = 6   # map_size // 6

GATE_MIN_PAIRS_RATIO = 16  # map_size // 16
GATE_MAX_PAIRS_RATIO = 8   # map_size // 8

# =============================================================================
# ACTION REWARDS
# =============================================================================

# Movement Rewards
MOVE_REWARD = 1.0
QUANTUM_MOVE_BASE_REWARD = 2.0

# Quantum Action Rewards
ENTANGLE_BASE_REWARD = 5.0
ENTANGLEMENT_ZONE_BONUS_MULTIPLIER = 1.5
MEASURE_BASE_REWARD = 3.0
SCOUT_MEASURE_MULTIPLIER = 1.3

# Shield and Boost Rewards
SHIELD_BASE_REWARD = 2.0
SHIELD_ENERGY_MULTIPLIER = 0.5
QUANTUM_GATE_SHIELD_MULTIPLIER = 1.5
BOOST_BASE_REWARD = 1.0
BOOST_ENERGY_MULTIPLIER = 0.3

# Spawn Rewards
SPAWN_HARVESTER_REWARD = 20.0
SPAWN_WARRIOR_REWARD = 30.0
SPAWN_SCOUT_REWARD = 25.0

# Entanglement Zone Creation Reward
CREATE_ENTANGLEMENT_ZONE_BASE_REWARD = 30.0
CREATE_ENTANGLEMENT_ZONE_BOOST_REWARD = 5.0

# Quantum Gate Action Rewards
QUANTUM_GATE_HEALTH_GAIN_REWARD = 10.0
QUANTUM_GATE_TELEPORT_REWARD = 15.0

# =============================================================================
# UNIT HEALTH
# =============================================================================

DEFAULT_UNIT_HEALTH = 45 #100.0
DEFAULT_UNIT_ENERGY = 0.0

# =============================================================================
# QUANTUM NOISE
# =============================================================================

QUANTUM_NOISE_MEAN = 0.0
QUANTUM_NOISE_STD = 0.01

# =============================================================================
# RENDERING SETTINGS
# =============================================================================

RENDER_FPS = 4
RENDER_MODES = ['human']

# =============================================================================
# AI AGENT SETTINGS
# =============================================================================

# Greedy Agent Settings
GREEDY_SPAWN_COOLDOWN = 5  # Minimum turns between spawns
GREEDY_MIN_ENERGY_FOR_HARVESTER = 50
GREEDY_MIN_ENERGY_FOR_WARRIOR = 100
GREEDY_MIN_ENERGY_FOR_SCOUT = 75
GREEDY_MAX_HARVESTERS = 2
GREEDY_MAX_WARRIORS = 1

# Strategic Agent Settings
STRATEGIC_SPAWN_COOLDOWN = 3
STRATEGIC_EARLY_GAME_TURNS = 50
STRATEGIC_MID_GAME_TURNS = 150
STRATEGIC_ENERGY_ADVANTAGE_THRESHOLD = 1.5  # 50% more energy to change strategy

# Strategic Agent Unit Limits by Phase
STRATEGIC_EARLY_MAX_HARVESTERS = 3
STRATEGIC_EARLY_MAX_SCOUTS = 2
STRATEGIC_MID_MAX_HARVESTERS = 4
STRATEGIC_MID_MAX_WARRIORS = 2
STRATEGIC_AGGRESSIVE_MAX_WARRIORS = 2

# =============================================================================
# ACTION SPACE CONFIGURATION
# =============================================================================

ACTION_SPACE_DIMENSIONS = {
    "ACTION_TYPES": 17,  # Total number of action types (including building actions)
    "DIRECTION_X": 3,    # -1, 0, 1
    "DIRECTION_Y": 3,    # -1, 0, 1  
    "ENERGY_BOOST": 5    # 0-4
    # MAX_UNITS removed - no unit limits
}

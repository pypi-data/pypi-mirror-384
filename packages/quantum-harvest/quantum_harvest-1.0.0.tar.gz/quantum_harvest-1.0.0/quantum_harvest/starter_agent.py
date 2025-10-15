"""
Starter Agent for Quantum Harvest game.

This skeleton shows the expected input/output formats for creating your own agent.
Use this as a template to understand the observation structure and action format.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from quantum_harvest.agents import BaseAgent
from quantum_harvest.utils import UnitType, ActionType, TileType


class Agent(BaseAgent):
    """
    Starter Agent Template for Quantum Harvest
    
    This agent demonstrates:
    1. How to parse the observation dictionary
    2. How to structure actions for each unit
    3. How to access game state information
    4. Common helper methods for agent development
    """

    def __init__(self, player_id: int):
        """
        Initialize the agent.
        
        Args:
            player_id: ID of the player this agent controls (0 or 1)
        """
        super().__init__(player_id)
        
    def get_action(self, observation: Dict[str, np.ndarray], player_id: int = 0) -> Dict[int, np.ndarray]:
        """
        Get actions for all units
        
        Args:
            observation: Current game observation with the following structure:
                {
                    'map': np.ndarray,           # 2D array representing the game map
                    'units': np.ndarray,         # Array of all units [unit_id, player_id, unit_type, x, y, health, is_boosted, boost_attacks]
                    'player_energy': np.ndarray, # Array of player energy levels [player_0_energy, player_1_energy]
                    'turn': np.ndarray,          # Current turn number [turn]
                    'fog_maps': np.ndarray,     # Optional: Player-specific fog of war maps
                    'territory_control': np.ndarray, # Optional: Territory control values
                    'victory_conditions': dict   # Optional: Victory condition status
                }
            player_id: Player ID (0 or 1)
            
        Returns:
            actions: Dictionary mapping unit_id to action array [action_type, direction_x, direction_y, energy_boost]
            
        Action Format:
            Each action is a numpy array with 4 elements:
            [action_type, direction_x, direction_y, energy_boost]
            
            action_type: Integer from 0-16 (see ActionType enum)
            direction_x: Integer from 0-2 (0=left, 1=no_move, 2=right)
            direction_y: Integer from 0-2 (0=up, 1=no_move, 2=down)
            energy_boost: Integer from 0-4 (energy to spend on action)
        """
        
        # Parse observation
        map_data = observation['map']
        units_array = observation['units']
        player_energy = observation['player_energy'][self.player_id]
        current_turn = observation['turn'][0]
        
        # Get all units belonging to this player
        player_units = self._get_player_units(observation)
        
        # Initialize actions dictionary
        actions = {}
        
        # Process each unit
        for unit_id, unit_type, health, pos in player_units:
            # Get action for this unit
            action = self._get_unit_action(unit_id, unit_type, pos, map_data, observation)
            actions[unit_id] = action
        
        return actions

    def _get_player_units(self, observation: Dict[str, np.ndarray]) -> List[Tuple[int, int, int, Tuple[int, int]]]:
        """
        Get all units belonging to this player.
        
        Returns:
            List of tuples: (unit_id, unit_type, health, position)
        """
        units = []
        units_array = observation['units']
        
        for i in range(units_array.shape[0]):
            unit_id, player_id, unit_type, x, y, health, is_boosted, boost_attacks = units_array[i]
            if player_id == self.player_id:
                units.append((unit_id, unit_type, health, (x, y)))
        
        return units

    def _get_unit_action(self, unit_id: int, unit_type: int, pos: Tuple[int, int], map_data: np.ndarray, observation: Dict) -> np.ndarray:
        """
        Get action for a specific unit.
        
        Args:
            unit_id: ID of the unit
            unit_type: Type of unit (0=Harvester, 1=Warrior, 2=Scout)
            pos: Current position of the unit
            map_data: 2D array representing the game map
            observation: Full game observation
            
        Returns:
            Action array [action_type, direction_x, direction_y, energy_boost]
        """
        # TODO: Implement your unit logic here
        # Example structure:
        # if unit_type == UnitType.HARVESTER.value:
        #     return self._get_harvester_action(unit_id, pos, map_data, observation)
        # elif unit_type == UnitType.WARRIOR.value:
        #     return self._get_warrior_action(unit_id, pos, map_data, observation)
        # elif unit_type == UnitType.SCOUT.value:
        #     return self._get_scout_action(unit_id, pos, map_data, observation)
        
        # Default action: do nothing
        return np.array([ActionType.MOVE.value, 1, 1, 0])

    def _get_enemy_units(self, observation: Dict[str, np.ndarray]) -> List[Tuple[int, int, int, Tuple[int, int]]]:
        """
        Get all enemy units.
        
        Returns:
            List of tuples: (unit_id, unit_type, health, position)
        """
        enemy_units = []
        units_array = observation['units']
        
        for i in range(units_array.shape[0]):
            unit_id, player_id, unit_type, x, y, health, is_boosted, boost_attacks = units_array[i]
            if player_id != self.player_id:
                enemy_units.append((unit_id, unit_type, health, (x, y)))
        
        return enemy_units

    def reset(self):
        """Reset the agent's state."""
        super().reset()


# =============================================================================
# ACTION TYPES REFERENCE
# =============================================================================
"""
Available Action Types (ActionType enum):

Movement Actions:
- MOVE (0): Regular movement
- QUANTUM_MOVE (1): Quantum movement (can move through some obstacles)

Resource Actions:
- HARVEST (2): Collect energy from energy nodes
- BOOST (6): Spend energy to boost action effectiveness

Combat Actions:
- ATTACK (7): Attack adjacent enemy units
- SHIELD (5): Defend against attacks

Quantum Actions:
- ENTANGLE (3): Create quantum entanglement with adjacent units
- MEASURE (4): Measure quantum state of adjacent tiles
- CREATE_ENTANGLEMENT_ZONE (11): Create an entanglement zone
- QUANTUM_GATE_HEALTH_GAIN (12): Use quantum gate for health
- QUANTUM_GATE_TELEPORT (13): Use quantum gate for teleportation

Construction Actions:
- BUILD_DECOHERENCE_FIELD (14): Build decoherence field
- BUILD_QUANTUM_BARRIER (15): Build quantum barrier
- BUILD_QUANTUM_GATE (16): Build quantum gate

Spawning Actions (Scouts only):
- SPAWN_HARVESTER (8): Spawn a new harvester unit
- SPAWN_WARRIOR (9): Spawn a new warrior unit
- SPAWN_SCOUT (10): Spawn a new scout unit
"""

# =============================================================================
# UNIT TYPES REFERENCE
# =============================================================================
"""
Unit Types (UnitType enum):

HARVESTER (0):
- Specializes in collecting energy from energy nodes
- Can harvest energy more efficiently
- Lower combat effectiveness

WARRIOR (1):
- Specializes in combat and territory control
- Higher health and attack power
- Can use entanglement boosts for enhanced attacks

SCOUT (2):
- Specializes in exploration and quantum operations
- Can spawn new units
- Access to quantum movement and measurement
- Can build quantum structures
"""

# =============================================================================
# TILE TYPES REFERENCE
# =============================================================================
"""
Tile Types (TileType enum):

EMPTY (0): Regular empty tile
ENERGY_NODE (1): Contains energy that can be harvested
QUANTUM_BARRIER (2): Blocks movement and affects quantum operations
ENTANGLEMENT_ZONE (3): Enables quantum entanglement between units
DECOHERENCE_FIELD (4): Disrupts quantum states
QUANTUM_GATE (5): Allows teleportation and health restoration
"""

# =============================================================================
# DIRECTION COORDINATES REFERENCE
# =============================================================================
"""
Direction coordinates for actions:
- direction_x: 0=left, 1=no_move, 2=right
- direction_y: 0=up, 1=no_move, 2=down

Examples:
- Move right: direction_x=2, direction_y=1
- Move up-left: direction_x=0, direction_y=0
- No movement: direction_x=1, direction_y=1
"""

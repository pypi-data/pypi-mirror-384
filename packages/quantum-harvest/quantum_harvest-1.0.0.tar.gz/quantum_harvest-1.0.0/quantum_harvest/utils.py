"""
Utility classes and enums for Quantum Harvest game.
"""

from enum import IntEnum
import numpy as np
from dataclasses import dataclass
from typing import Tuple, List, Optional
from .game_config import DEFAULT_UNIT_HEALTH, DEFAULT_UNIT_ENERGY


class TileType(IntEnum):
    """Types of tiles on the game map."""
    EMPTY = 0
    ENERGY_NODE = 1
    QUANTUM_BARRIER = 2
    ENTANGLEMENT_ZONE = 3
    DECOHERENCE_FIELD = 4
    QUANTUM_GATE = 5


class UnitType(IntEnum):
    """Types of units in the game."""
    HARVESTER = 0
    WARRIOR = 1
    SCOUT = 2


class ActionType(IntEnum):
    """Types of actions units can perform."""
    MOVE = 0
    QUANTUM_MOVE = 1
    HARVEST = 2
    ENTANGLE = 3
    MEASURE = 4
    SHIELD = 5
    BOOST = 6
    ATTACK = 7
    SPAWN_HARVESTER = 8
    SPAWN_WARRIOR = 9
    SPAWN_SCOUT = 10
    CREATE_ENTANGLEMENT_ZONE = 11
    QUANTUM_GATE_HEALTH_GAIN = 12
    QUANTUM_GATE_TELEPORT = 13
    BUILD_DECOHERENCE_FIELD = 14
    BUILD_QUANTUM_BARRIER = 15
    BUILD_QUANTUM_GATE = 16


@dataclass
class Unit:
    """Represents a unit in the game."""
    unit_id: int
    player_id: int
    unit_type: UnitType
    position: Tuple[int, int]
    health: float = DEFAULT_UNIT_HEALTH
    energy: float = DEFAULT_UNIT_ENERGY
    quantum_state: Optional[np.ndarray] = None
    # Entanglement boost tracking for warriors
    is_boosted: bool = False
    boost_attacks_remaining: int = 0
    
    def __post_init__(self):
        if self.quantum_state is None:
            self.quantum_state = np.array([1.0, 0.0])  # |0⟩ state


@dataclass
class GameState:
    """Represents the complete game state."""
    map: np.ndarray
    units: List[Unit]
    player_energy: List[float]
    turn: int
    territory_control: List[float]
    victory_conditions: dict
    
    def get_player_units(self, player_id: int) -> List[Unit]:
        """Get all units belonging to a specific player."""
        return [unit for unit in self.units if unit.player_id == player_id]
    
    def get_unit_at_position(self, position: Tuple[int, int]) -> Optional[Unit]:
        """Get unit at a specific position, if any."""
        for unit in self.units:
            if unit.position == position:
                return unit
        return None


def manhattan_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """Calculate Manhattan distance between two positions."""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def is_valid_position(pos: Tuple[int, int], map_size: int) -> bool:
    """Check if a position is within the map bounds."""
    return 0 <= pos[0] < map_size and 0 <= pos[1] < map_size


def get_neighbors(pos: Tuple[int, int], map_size: int) -> List[Tuple[int, int]]:
    """Get all valid neighboring positions."""
    x, y = pos
    neighbors = []
    
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        new_pos = (x + dx, y + dy)
        if is_valid_position(new_pos, map_size):
            neighbors.append(new_pos)
    
    return neighbors


def calculate_territory_control(units: List[Unit], map_size: int) -> List[float]:
    """Calculate territory control for each player."""
    territory = np.zeros((map_size, map_size), dtype=np.int8)
    
    # Mark territory based on unit positions
    for unit in units:
        x, y = unit.position
        territory[x, y] = unit.player_id + 1  # +1 to distinguish from 0 (no control)
    
    # Calculate control percentages
    total_tiles = map_size * map_size
    player1_control = np.sum(territory == 1) / total_tiles
    player2_control = np.sum(territory == 2) / total_tiles
    
    return [player1_control, player2_control] 
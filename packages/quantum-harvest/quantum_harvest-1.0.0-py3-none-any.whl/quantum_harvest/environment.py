"""
Quantum Harvest Environment - Main game environment implementation.
"""

import numpy as np
import random
import json
import os
from datetime import datetime
from typing import Tuple, List, Optional, Dict, Any
from gymnasium import spaces
from .utils import (
    TileType, UnitType, ActionType, Unit, GameState,
    manhattan_distance, is_valid_position, get_neighbors,
    calculate_territory_control
)
from .game_config import (
    DEFAULT_MAP_SIZE, DEFAULT_MAX_TURNS,
    ENERGY_VICTORY_THRESHOLD, TERRITORY_VICTORY_THRESHOLD, TERRITORY_VICTORY_TURNS,
    UNIT_COSTS, BUILDING_COSTS, UNIT_STATS, EXPLORATION_RANGES,
    WARRIOR_BASE_DAMAGE, ATTACK_ENERGY_COST, BOOSTED_ATTACK_RANGE, NORMAL_ATTACK_RANGE,
    ENTANGLEMENT_DAMAGE_MULTIPLIER, UNIT_DEFEAT_REWARD,
    ENERGY_NODE_MIN_VALUE, ENERGY_NODE_MAX_VALUE, ENERGY_NODE_DEPLETION_RATE,
    HARVEST_BASE_AMOUNTS, ENERGY_BOOST_MULTIPLIER,
    ENTANGLEMENT_ZONE_CREATION_BASE_COST, ENTANGLEMENT_ZONE_CREATION_BOOST_COST,
    ENTANGLEMENT_ZONE_INITIAL_POWER, ENTANGLEMENT_ZONE_BOOST_COST, ENTANGLEMENT_ZONE_BOOST_ATTACKS,
    DECOHERENCE_DAMAGE_REDUCTION,
    QUANTUM_GATE_HEALTH_BOOST_PERCENTAGE, QUANTUM_GATE_MAX_HEALTH_LIMIT,
    QUANTUM_GATE_HEALTH_GAIN_COST, QUANTUM_GATE_HEALTH_GAIN_AMOUNT, QUANTUM_GATE_TELEPORT_COST,
    ENERGY_NODE_MIN_PAIRS_RATIO, ENERGY_NODE_MAX_PAIRS_RATIO,
    BARRIER_MIN_PAIRS_RATIO, BARRIER_MAX_PAIRS_RATIO,
    DECOHERENCE_MIN_PAIRS_RATIO, DECOHERENCE_MAX_PAIRS_RATIO,
    GATE_MIN_PAIRS_RATIO, GATE_MAX_PAIRS_RATIO,
    MOVE_REWARD, QUANTUM_MOVE_BASE_REWARD, ENTANGLE_BASE_REWARD,
    ENTANGLEMENT_ZONE_BONUS_MULTIPLIER, MEASURE_BASE_REWARD, SCOUT_MEASURE_MULTIPLIER,
    SHIELD_BASE_REWARD, SHIELD_ENERGY_MULTIPLIER, QUANTUM_GATE_SHIELD_MULTIPLIER,
    BOOST_BASE_REWARD, BOOST_ENERGY_MULTIPLIER,
    SPAWN_HARVESTER_REWARD, SPAWN_WARRIOR_REWARD, SPAWN_SCOUT_REWARD,
    CREATE_ENTANGLEMENT_ZONE_BASE_REWARD, CREATE_ENTANGLEMENT_ZONE_BOOST_REWARD,
    QUANTUM_GATE_HEALTH_GAIN_REWARD, QUANTUM_GATE_TELEPORT_REWARD,
    DEFAULT_UNIT_HEALTH, DEFAULT_UNIT_ENERGY, QUANTUM_NOISE_MEAN, QUANTUM_NOISE_STD,
    RENDER_FPS, RENDER_MODES, ACTION_SPACE_DIMENSIONS
)


class QuantumHarvestEnv:
    """
    Quantum Harvest Environment - A competitive 1v1 AI game combining quantum mechanics 
    with strategic resource management and territory control.
    """
    
    def __init__(
        self,
        map_size: int = DEFAULT_MAP_SIZE,
        max_turns: int = DEFAULT_MAX_TURNS,
        energy_victory_threshold: float = ENERGY_VICTORY_THRESHOLD,
        territory_victory_threshold: float = TERRITORY_VICTORY_THRESHOLD,
        territory_victory_turns: int = TERRITORY_VICTORY_TURNS,
        render_mode: Optional[str] = None,
        seed: Optional[int] = None,
        log_game: bool = False,
        log_file: Optional[str] = None,
        player1_username: Optional[str] = None,
        player2_username: Optional[str] = None
    ):
        """
        Initialize the Quantum Harvest environment.
        
        Args:
            map_size: Size of the square game map
            max_turns: Maximum number of turns per game
            energy_victory_threshold: Energy needed for victory
            territory_victory_threshold: Territory control needed for victory
            territory_victory_turns: Turns needed for territory victory
            render_mode: Rendering mode ("human" for visualization)
            seed: Random seed for reproducibility
            log_game: Whether to log game states for replay
            log_file: Path to log file (if None, auto-generated)
        """
        self.map_size = map_size
        self.max_turns = max_turns
        self.energy_victory_threshold = energy_victory_threshold
        self.territory_victory_threshold = territory_victory_threshold
        self.territory_victory_turns = territory_victory_turns
        self.render_mode = render_mode
        
        # Game logging setup
        self.log_game = log_game
        self.log_file = log_file
        self.game_log = []
        
        if self.log_game:
            if self.log_file is None:
                # Auto-generate log file name with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.log_file = f"game_log_{timestamp}.json"
            
            # Initialize log with game configuration
            self.game_log = [{
                "type": "game_config",
                "map_size": map_size,
                "max_turns": max_turns,
                "energy_victory_threshold": energy_victory_threshold,
                "territory_victory_threshold": territory_victory_threshold,
                "territory_victory_turns": territory_victory_turns,
                "max_units": "unlimited",
                "seed": seed,
                "player1_username": player1_username,
                "player2_username": player2_username,
                "timestamp": datetime.now().isoformat()
            }]
        
        # Set random seed
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # Game state
        self.map = None
        self.units = []
        self.player_energy = [0.0, 0.0]
        self.turn = 0
        self.territory_control = [0.0, 0.0]
        self.territory_control_turns = [0, 0]  # Consecutive turns with territory control
        self.energy_nodes = []
        self.energy_values = []
        self.player_start_positions = []
        
        # Unit ID counters per player to ensure unique IDs within each team
        self.next_unit_id = [0, 0]  # [player_0_next_id, player_1_next_id]
        
        # Entanglement zone tracking
        self.entanglement_zones = []  # List of positions with entanglement zones
        self.entanglement_zone_power = []  # Corresponding boost power for each zone
        
        # Animation tracking for combat events
        self.combat_events = []  # List of combat events for animation
        self.animation_frame = 0  # Current animation frame
        
        # Fog of war and exploration tracking
        self.explored_tiles = [set(), set()]  # Explored tiles for each player
        self.exploration_ranges = {
            UnitType.SCOUT: EXPLORATION_RANGES["SCOUT"],
            UnitType.HARVESTER: EXPLORATION_RANGES["HARVESTER"],
            UnitType.WARRIOR: EXPLORATION_RANGES["WARRIOR"]
        }
        
        # Unit costs
        self.unit_costs = {
            UnitType.HARVESTER: UNIT_COSTS["HARVESTER"],
            UnitType.WARRIOR: UNIT_COSTS["WARRIOR"],
            UnitType.SCOUT: UNIT_COSTS["SCOUT"]
        }
        
        # Unit stats
        self.unit_stats = {
            UnitType.HARVESTER: UNIT_STATS["HARVESTER"],
            UnitType.WARRIOR: UNIT_STATS["WARRIOR"],  # Warriors cannot harvest
            UnitType.SCOUT: UNIT_STATS["SCOUT"]
        }
        
        # Action space: [unit_id, action_type, direction_x, direction_y, energy_boost]
        # Note: unit_id is now unlimited - we'll validate during action execution
        self.action_space = spaces.MultiDiscrete([
            1000,  # unit_id (large enough for any reasonable game)
            ACTION_SPACE_DIMENSIONS["ACTION_TYPES"],  # action_type (12 action types including CREATE_ENTANGLEMENT_ZONE)
            ACTION_SPACE_DIMENSIONS["DIRECTION_X"],   # direction_x (-1, 0, 1)
            ACTION_SPACE_DIMENSIONS["DIRECTION_Y"],   # direction_y (-1, 0, 1)
            ACTION_SPACE_DIMENSIONS["ENERGY_BOOST"]    # energy_boost (0-4)
        ])
        
        # Observation space
        self.observation_space = spaces.Dict({
            'map': spaces.Box(low=0, high=5, shape=(map_size, map_size), dtype=np.int8),
            'fog_maps': spaces.Box(low=-1, high=5, shape=(2, map_size, map_size), dtype=np.int8),  # Fog of war for each player
            'units': spaces.Box(low=0, high=255, shape=(1000, 8), dtype=np.int16),  # [unit_id, player_id, unit_type, x, y, health, is_boosted, boost_attacks_remaining] - dynamic size
            'player_energy': spaces.Box(low=0, high=energy_victory_threshold, shape=(2,), dtype=np.float32),
            'turn': spaces.Box(low=0, high=max_turns, shape=(1,), dtype=np.int32),
            'territory_control': spaces.Box(low=0, high=1, shape=(2,), dtype=np.float32),
            'exploration_percentage': spaces.Box(low=0, high=1, shape=(2,), dtype=np.float32)
        })
        
        # Metadata
        self.metadata = {
            'render_modes': RENDER_MODES,
            'render_fps': RENDER_FPS
        }
        
        # Initialize visualizer if render mode is specified
        self.visualizer = None
        if self.render_mode == "human":
            from .visualizer import GameVisualizer
            self.visualizer = GameVisualizer(map_size)  # Auto-calculate cell_size
    
    def reset(self, seed: Optional[int] = None) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """
        Reset the environment to initial state.
        
        Returns:
            observation: Initial game state
            info: Additional information
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # Reset game state
        self.turn = 0
        self.player_energy = [0.0, 0.0]
        self.territory_control = [0.0, 0.0]
        self.territory_control_turns = [0, 0]
        
        # Reset exploration history for new game
        self.explored_tiles = [set(), set()]
        
        # Reset entanglement zones
        self.entanglement_zones = []
        self.entanglement_zone_power = []
        
        # Generate map and initial units
        self._generate_map()
        self._create_initial_units()
        
        # Calculate initial territory control
        self.territory_control = calculate_territory_control(self.units, self.map_size)
        
        # Update initial exploration based on starting units
        self._update_exploration()
        
        observation = self._get_observation()
        info = self._get_info()
        
        # Log initial game state
        if self.log_game:
            self._log_game_state("reset", None, observation, info)
        
        return observation, info
    
    def step(self, action: Dict[int, np.ndarray]) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        """
        Execute one step in the environment with multi-action support.
        
        Args:
            action: Dictionary mapping unit_id to action array [action_type, direction_x, direction_y, energy_boost]
                   or single action array for backward compatibility
            
        Returns:
            observation: Current game state
            reward: Reward for the action
            terminated: Whether the episode has terminated
            truncated: Whether the episode was truncated
            info: Additional information
        """
        # Clear combat events from previous turn
        self.combat_events = []
        self.animation_frame = 0
        
        total_reward = 0.0
        
        # Handle both dictionary format and legacy array format
        if isinstance(action, dict):
            # Multi-action format: {unit_id: [action_type, direction_x, direction_y, energy_boost]}
            for action_key, action_array in action.items():
                if len(action_array) == 5:  # Legacy format with unit_id included
                    _, action_type, direction_x, direction_y, energy_boost = action_array
                else:  # New format without unit_id
                    action_type, direction_x, direction_y, energy_boost = action_array
                
                # Parse action key to get unit_id (and optionally player_id for disambiguation)
                if isinstance(action_key, str) and action_key.startswith(('p0_', 'p1_')):
                    # New format: "p0_15" -> player_id=0, unit_id=15
                    player_id = int(action_key[1])
                    unit_id = int(action_key[3:])
                    # Find unit by both unit_id and player_id for disambiguation
                    unit = None
                    for u in self.units:
                        if u.unit_id == unit_id and u.player_id == player_id:
                            unit = u
                            break
                else:
                    # Legacy format: just unit_id
                    unit_id = int(action_key)
                    # Find unit by unit_id only (legacy behavior)
                    unit = None
                    for u in self.units:
                        if u.unit_id == unit_id:
                            unit = u
                            break
                
                if unit is None:
                    continue  # Skip if unit not found
                
                # Convert direction from (-1, 0, 1) to actual direction
                direction = (direction_x - 1, direction_y - 1)  # Convert to (-1, 0, 1)
                
                # Execute action
                reward = self._execute_unit_action_for_unit(unit, action_type, direction, energy_boost)
                total_reward += reward
        else:
            # Legacy single action format: [unit_id, action_type, direction_x, direction_y, energy_boost]
            unit_id, action_type, direction_x, direction_y, energy_boost = action
            
            # Convert direction from (-1, 0, 1) to actual direction
            direction = (direction_x - 1, direction_y - 1)  # Convert to (-1, 0, 1)
            
            # Execute action
            total_reward = self._execute_unit_action(unit_id, action_type, direction, energy_boost)
        
        # Update game state
        self._update_energy_nodes()
        self._update_quantum_states()
        self._cleanup_dead_units()  # Remove dead units from the game
        self._update_exploration()
        self.territory_control = calculate_territory_control(self.units, self.map_size)
        
        # Check victory conditions
        terminated, winner = self._check_victory_conditions()
        
        # Update turn
        self.turn += 1
        
        # Check if game should be truncated
        truncated = self.turn >= self.max_turns
        
        observation = self._get_observation()
        info = self._get_info()
        
        if terminated:
            info['winner'] = winner
        
        # Log game state after step
        if self.log_game:
            self._log_game_state("step", action, observation, info, total_reward, terminated, truncated)
        
        return observation, total_reward, terminated, truncated, info
    
    def _generate_map(self):
        """Generate the game map with perfect mirror symmetry between players."""
        self.map = np.zeros((self.map_size, self.map_size), dtype=np.int8)
        
        # Define player starting positions
        player1_start = (0, 0)
        player2_start = (self.map_size-1, self.map_size-1)
        self.player_start_positions = [player1_start, player2_start]
        
        # Initialize energy nodes and values
        self.energy_nodes = []
        self.energy_values = []
        
        # Calculate tile counts for perfect symmetry with randomization
        # Randomize the number of resources while keeping reasonable bounds
        min_energy_pairs = max(1, self.map_size // ENERGY_NODE_MIN_PAIRS_RATIO)
        max_energy_pairs = self.map_size // ENERGY_NODE_MAX_PAIRS_RATIO
        num_energy_pairs = random.randint(min_energy_pairs, max_energy_pairs)
        
        min_barrier_pairs = max(1, self.map_size // BARRIER_MIN_PAIRS_RATIO)
        max_barrier_pairs = self.map_size // BARRIER_MAX_PAIRS_RATIO
        num_barrier_pairs = random.randint(min_barrier_pairs, max_barrier_pairs)
        
        # No entanglement zones at start - they must be created by players
        num_entanglement_pairs = 0
        
        min_decoherence_pairs = max(1, self.map_size // DECOHERENCE_MIN_PAIRS_RATIO)
        max_decoherence_pairs = self.map_size // DECOHERENCE_MAX_PAIRS_RATIO
        num_decoherence_pairs = random.randint(min_decoherence_pairs, max_decoherence_pairs)
        
        min_gate_pairs = max(1, self.map_size // GATE_MIN_PAIRS_RATIO)
        max_gate_pairs = self.map_size // GATE_MAX_PAIRS_RATIO
        num_gate_pairs = random.randint(min_gate_pairs, max_gate_pairs)
        
        # Define available positions for Player 1 (top-left half, excluding starting positions)
        player1_positions = []
        for x in range(self.map_size):
            for y in range(self.map_size):
                if (x, y) != player1_start and (x, y) != player2_start:
                    # Player 1 gets top-left half
                    if x < self.map_size // 2 and y < self.map_size // 2:
                        player1_positions.append((x, y))
        
        # Ensure we have enough positions
        total_tiles_needed = num_energy_pairs + num_barrier_pairs + num_entanglement_pairs + num_decoherence_pairs + num_gate_pairs
        if len(player1_positions) < total_tiles_needed:
            # Fallback: reduce tile counts
            num_energy_pairs = min(num_energy_pairs, len(player1_positions) // 5)
            num_barrier_pairs = min(num_barrier_pairs, len(player1_positions) // 5)
            num_entanglement_pairs = min(num_entanglement_pairs, len(player1_positions) // 5)
            num_decoherence_pairs = min(num_decoherence_pairs, len(player1_positions) // 5)
            num_gate_pairs = min(num_gate_pairs, len(player1_positions) // 5)
        
        # Place energy nodes with mirror symmetry
        for _ in range(num_energy_pairs):
            if player1_positions:
                # Place for player 1
                pos1 = random.choice(player1_positions)
                player1_positions.remove(pos1)
                self.map[pos1] = TileType.ENERGY_NODE.value
                self.energy_nodes.append(pos1)
                energy_val = random.randint(ENERGY_NODE_MIN_VALUE, ENERGY_NODE_MAX_VALUE)  # Random energy value (int)
                self.energy_values.append(energy_val)
                
                # Place mirror for player 2
                pos2 = self._get_mirror_position(pos1)
                self.map[pos2] = TileType.ENERGY_NODE.value
                self.energy_nodes.append(pos2)
                self.energy_values.append(energy_val)  # Same energy value for fairness
        
        # Place quantum barriers with mirror symmetry
        for _ in range(num_barrier_pairs):
            if player1_positions:
                pos1 = random.choice(player1_positions)
                player1_positions.remove(pos1)
                self.map[pos1] = TileType.QUANTUM_BARRIER.value
                
                pos2 = self._get_mirror_position(pos1)
                self.map[pos2] = TileType.QUANTUM_BARRIER.value
        
        # Entanglement zones are no longer placed at map generation
        # They must be created by warriors and scouts during gameplay
        
        # Place decoherence fields with mirror symmetry
        for _ in range(num_decoherence_pairs):
            if player1_positions:
                pos1 = random.choice(player1_positions)
                player1_positions.remove(pos1)
                self.map[pos1] = TileType.DECOHERENCE_FIELD.value
                
                pos2 = self._get_mirror_position(pos1)
                self.map[pos2] = TileType.DECOHERENCE_FIELD.value
        
        # Place quantum gates with mirror symmetry
        for _ in range(num_gate_pairs):
            if player1_positions:
                pos1 = random.choice(player1_positions)
                player1_positions.remove(pos1)
                self.map[pos1] = TileType.QUANTUM_GATE.value
                
                pos2 = self._get_mirror_position(pos1)
                self.map[pos2] = TileType.QUANTUM_GATE.value
        
        # Verify mirror symmetry
        self._verify_map_symmetry()
    
    def _get_mirror_position(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """
        Get the mirror position of a given position.
        Mirror is across both x and y axes (diagonal mirror).
        
        Args:
            pos: Original position (x, y)
            
        Returns:
            Mirror position (map_size-1-x, map_size-1-y)
        """
        x, y = pos
        return (self.map_size - 1 - x, self.map_size - 1 - y)
    
    def _verify_map_symmetry(self):
        """Verify that the map has perfect mirror symmetry between players."""
        # Check mirror symmetry for each tile
        mirror_symmetric = True
        tile_counts = {TileType.ENERGY_NODE: 0, TileType.QUANTUM_BARRIER: 0, 
                      TileType.ENTANGLEMENT_ZONE: 0, TileType.DECOHERENCE_FIELD: 0, 
                      TileType.QUANTUM_GATE: 0}
        
        # Check each position and its mirror
        for x in range(self.map_size):
            for y in range(self.map_size):
                tile_type = self.map[x, y]
                if tile_type != TileType.EMPTY.value:
                    # Get mirror position
                    mirror_x, mirror_y = self._get_mirror_position((x, y))
                    mirror_tile = self.map[mirror_x, mirror_y]
                    
                    # Check if mirror position has the same tile type
                    if tile_type != mirror_tile:
                        print(f"Warning: Mirror asymmetry at ({x},{y}) -> ({mirror_x},{mirror_y})")
                        print(f"  Original: {TileType(tile_type).name}, Mirror: {TileType(mirror_tile).name}")
                        mirror_symmetric = False
                    else:
                        tile_counts[TileType(tile_type)] += 1
        
        # Report results
        if mirror_symmetric:
            print("✓ Perfect mirror symmetry verified!")
            for tile_type, count in tile_counts.items():
                if count > 0:
                    print(f"  {tile_type.name}: {count} pairs (mirrored)")
        else:
            print("✗ Mirror symmetry verification failed!")
        
        return mirror_symmetric
    
    def _create_initial_units(self):
        """Create initial units for both players."""
        self.units = []
        
        # Reset unit ID counters
        self.next_unit_id = [0, 0]
        
        # Player 1 starts with 1 Scout at (0, 0)
        scout1 = Unit(
            unit_id=self.next_unit_id[0],
            player_id=0,
            unit_type=UnitType.SCOUT,
            position=(0, 0)
        )
        self.next_unit_id[0] += 1
        self.units.append(scout1)
        
        # Player 2 starts with 1 Scout at (map_size-1, map_size-1)
        scout2 = Unit(
            unit_id=self.next_unit_id[1],
            player_id=1,
            unit_type=UnitType.SCOUT,
            position=(self.map_size-1, self.map_size-1)
        )
        self.next_unit_id[1] += 1
        self.units.append(scout2)
    
    def _generate_spawn_points(self):
        """Generate spawn points for units."""
        # Only use player starting positions as spawn points
        return self.player_start_positions
    
    def _spawn_unit(self, player_id: int, unit_type: UnitType, position: Tuple[int, int]) -> Optional[int]:
        """
        Spawn a new unit for a player.
        
        Args:
            player_id: ID of the player spawning the unit
            unit_type: Type of unit to spawn
            position: Position to spawn the unit at
            
        Returns:
            unit_id: ID of the spawned unit, or None if spawning failed
        """
        cost = self.unit_costs[unit_type]
        
        # Check if player has enough energy
        if self.player_energy[player_id] < cost:
            return None
        
        # Check if the original position is valid for spawning
        if not self._is_valid_spawn_position(position, player_id):
            # If original position is blocked (e.g., by quantum barrier), find closest empty tile
            alternative_position = self._find_closest_empty_spawn_position(position, player_id)
            if alternative_position is None:
                return None  # No valid spawn position found
            position = alternative_position
        
        # Create new unit with unique ID for this player
        unit_id = self.next_unit_id[player_id]
        self.next_unit_id[player_id] += 1  # Increment counter for this player
        
        new_unit = Unit(
            unit_id=unit_id,
            player_id=player_id,
            unit_type=unit_type,
            position=position
        )
        

        # Deduct energy and add unit
        self.player_energy[player_id] -= cost
        self.units.append(new_unit)
        
        return unit_id
    
    def _execute_unit_action(self, unit_id: int, action_type: int, direction: Tuple[int, int], energy_boost: int) -> float:
        """
        Execute an action for a specific unit.
        
        Args:
            unit_id: ID of the unit performing the action
            action_type: Type of action to perform
            direction: Direction for movement actions
            energy_boost: Amount of energy to boost the action
            
        Returns:
            reward: Reward for the action
        """
        # Find the unit by matching unit_id
        unit = None
        for u in self.units:
            if u.unit_id == unit_id:
                unit = u
                break
        
        if unit is None:
            return 0.0
        
        return self._execute_unit_action_for_unit(unit, action_type, direction, energy_boost)
    
    def _execute_unit_action_for_unit(self, unit: Unit, action_type: int, direction: Tuple[int, int], energy_boost: int) -> float:
        """
        Execute an action for a specific unit object.
        
        Args:
            unit: The unit object performing the action
            action_type: Type of action to perform
            direction: Direction for movement actions
            energy_boost: Amount of energy to boost the action
            
        Returns:
            reward: Reward for the action
        """
        
        # Check if player has enough energy for boost (only for ATTACK action)
        if action_type == ActionType.ATTACK.value:
            if energy_boost > 0 and self.player_energy[unit.player_id] < energy_boost:
                energy_boost = 0
            
            # Deduct boost energy
            if energy_boost > 0:
                self.player_energy[unit.player_id] -= energy_boost
        
        reward = 0.0
        
        if action_type == ActionType.MOVE.value:
            reward = self._execute_move(unit, direction, energy_boost)
        elif action_type == ActionType.QUANTUM_MOVE.value:
            reward = self._execute_quantum_move(unit, direction, energy_boost)
        elif action_type == ActionType.HARVEST.value:
            reward = self._execute_harvest(unit, energy_boost)
        elif action_type == ActionType.ENTANGLE.value:
            reward = self._execute_entangle(unit, direction, energy_boost)
        elif action_type == ActionType.MEASURE.value:
            reward = self._execute_measure(unit, direction, energy_boost)
        elif action_type == ActionType.SHIELD.value:
            reward = self._execute_shield(unit, energy_boost)
        elif action_type == ActionType.BOOST.value:
            reward = self._execute_boost(unit, energy_boost)
        elif action_type == ActionType.ATTACK.value:
            reward = self._execute_attack(unit, direction, energy_boost)
        elif action_type == ActionType.SPAWN_HARVESTER.value:
            # Only scouts can spawn units
            if unit.unit_type != UnitType.SCOUT:
                return 0.0
            
            # Use player's starting position for spawning
            spawn_point = self.player_start_positions[unit.player_id]
            new_unit_id = self._spawn_unit(unit.player_id, UnitType.HARVESTER, spawn_point)
            if new_unit_id is not None:
                reward += SPAWN_HARVESTER_REWARD
        elif action_type == ActionType.SPAWN_WARRIOR.value:
            # Only scouts can spawn units
            if unit.unit_type != UnitType.SCOUT:
                return 0.0
            
            # Use player's starting position for spawning
            spawn_point = self.player_start_positions[unit.player_id]
            new_unit_id = self._spawn_unit(unit.player_id, UnitType.WARRIOR, spawn_point)
            if new_unit_id is not None:
                reward += SPAWN_WARRIOR_REWARD
        elif action_type == ActionType.SPAWN_SCOUT.value:
            # Only scouts can spawn units
            if unit.unit_type != UnitType.SCOUT:
                return 0.0
            
            # Use player's starting position for spawning
            spawn_point = self.player_start_positions[unit.player_id]
            new_unit_id = self._spawn_unit(unit.player_id, UnitType.SCOUT, spawn_point)
            if new_unit_id is not None:
                reward += SPAWN_SCOUT_REWARD
        elif action_type == ActionType.CREATE_ENTANGLEMENT_ZONE.value:
            reward = self._execute_create_entanglement_zone(unit, direction, energy_boost)
        elif action_type == ActionType.QUANTUM_GATE_HEALTH_GAIN.value:
            reward = self._execute_quantum_gate_health_gain(unit, energy_boost)
        elif action_type == ActionType.QUANTUM_GATE_TELEPORT.value:
            reward = self._execute_quantum_gate_teleport(unit, direction, energy_boost)
        elif action_type == ActionType.BUILD_DECOHERENCE_FIELD.value:
            reward = self._execute_build_decoherence_field(unit, direction, energy_boost)
        elif action_type == ActionType.BUILD_QUANTUM_BARRIER.value:
            reward = self._execute_build_quantum_barrier(unit, direction, energy_boost)
        elif action_type == ActionType.BUILD_QUANTUM_GATE.value:
            reward = self._execute_build_quantum_gate(unit, direction, energy_boost)
        
        return reward
    
    def _execute_move(self, unit: Unit, direction: Tuple[int, int], energy_boost: int) -> float:
        """Execute a move action."""
        new_x = unit.position[0] + direction[0]
        new_y = unit.position[1] + direction[1]
        new_pos = (new_x, new_y)
        
        if not is_valid_position(new_pos, self.map_size):
            return 0.0
        
        # Check if position has opposing units
        if self._has_opposing_units(new_pos, unit.player_id):
            return 0.0
        
        # Check if barrier blocks movement
        if self.map[new_x, new_y] == TileType.QUANTUM_BARRIER.value:
            return 0.0  # Regular move cannot pass through barriers
        
        # Move unit
        unit.position = new_pos
        
        # Check for entanglement boost if warrior lands on entanglement zone
        if unit.unit_type == UnitType.WARRIOR:
            self._check_and_apply_entanglement_boost(unit)
            
        # Check if unit lands on decoherence field and remove boosts
        if self.map[new_x, new_y] == TileType.DECOHERENCE_FIELD.value:
            if unit.unit_type == UnitType.WARRIOR and unit.is_boosted:
                unit.is_boosted = False
                unit.boost_attacks_remaining = 0
        
        return MOVE_REWARD
    
    def _execute_quantum_move(self, unit: Unit, direction: Tuple[int, int], energy_boost: int) -> float:
        """Execute a quantum move action."""
        # Quantum moves always cost energy but can pass through barriers
        new_x = unit.position[0] + direction[0]
        new_y = unit.position[1] + direction[1]
        new_pos = (new_x, new_y)
        
        if not is_valid_position(new_pos, self.map_size):
            return 0.0
        
        # Check if position has opposing units
        if self._has_opposing_units(new_pos, unit.player_id):
            return 0.0
        
        # Quantum move always costs energy (0.5 * quantum barrier build cost)
        quantum_move_cost = BUILDING_COSTS["QUANTUM_BARRIER"] * 0.5  # 100 energy (0.5 * 200)
        if self.player_energy[unit.player_id] < quantum_move_cost:
            return 0.0  # Not enough energy to use quantum move
        
        # Deduct energy cost for quantum movement
        self.player_energy[unit.player_id] -= quantum_move_cost
        
        # Move unit (can pass through barriers)
        unit.position = new_pos
        
        # Check if unit lands on decoherence field and remove boosts
        if self.map[new_x, new_y] == TileType.DECOHERENCE_FIELD.value:
            if unit.unit_type == UnitType.WARRIOR and unit.is_boosted:
                unit.is_boosted = False
                unit.boost_attacks_remaining = 0
        
        return QUANTUM_MOVE_BASE_REWARD + energy_boost
    
    def _execute_harvest(self, unit: Unit, energy_boost: int) -> float:
        """Execute a harvest action."""
        # Warriors cannot harvest
        if unit.unit_type == UnitType.WARRIOR:
            return 0.0
        
        x, y = unit.position
        
        # Check if unit is on an energy node
        if self.map[x, y] != TileType.ENERGY_NODE.value:
            return 0.0
        
        # Find energy node index
        node_index = None
        for i, node_pos in enumerate(self.energy_nodes):
            if node_pos == (x, y):
                node_index = i
                break
        
        if node_index is None:
            return 0.0
        
        # Calculate harvest amount based on unit type (energy_boost ignored)
        if unit.unit_type == UnitType.SCOUT:
            base_harvest = HARVEST_BASE_AMOUNTS["SCOUT"]
        elif unit.unit_type == UnitType.HARVESTER:
            base_harvest = HARVEST_BASE_AMOUNTS["HARVESTER"]
        else:
            base_harvest = HARVEST_BASE_AMOUNTS["WARRIOR"]
        
        unit_efficiency = self.unit_stats[unit.unit_type]["harvest_efficiency"]
        harvest_amount = base_harvest * unit_efficiency
        
        # Add energy to player
        self.player_energy[unit.player_id] += harvest_amount
        
        # Deplete node energy
        self.energy_values[node_index] -= ENERGY_NODE_DEPLETION_RATE
        
        # Check if node is depleted
        if self.energy_values[node_index] <= 0:
            # Convert to ordinary tile
            self.map[x, y] = TileType.EMPTY.value
            # Remove from energy nodes list
            self.energy_nodes.pop(node_index)
            self.energy_values.pop(node_index)
        
        return harvest_amount
    
    def _execute_entangle(self, unit: Unit, direction: Tuple[int, int], energy_boost: int) -> float:
        """Execute an entangle action."""
        target_x = unit.position[0] + direction[0]
        target_y = unit.position[1] + direction[1]
        target_pos = (target_x, target_y)
        
        if not is_valid_position(target_pos, self.map_size):
            return 0.0
        
        target_unit = self._get_unit_at_position(target_pos)
        if target_unit is None or target_unit.player_id == unit.player_id:
            return 0.0
        
        # Create entanglement
        reward = ENTANGLE_BASE_REWARD + energy_boost
        
        # Check if in entanglement zone for bonus
        if self.map[unit.position[0], unit.position[1]] == TileType.ENTANGLEMENT_ZONE.value:
            reward *= ENTANGLEMENT_ZONE_BONUS_MULTIPLIER
        
        return reward
    
    def _execute_measure(self, unit: Unit, direction: Tuple[int, int], energy_boost: int) -> float:
        """Execute a measure action."""
        target_x = unit.position[0] + direction[0]
        target_y = unit.position[1] + direction[1]
        target_pos = (target_x, target_y)
        
        if not is_valid_position(target_pos, self.map_size):
            return 0.0
        
        target_unit = self._get_unit_at_position(target_pos)
        if target_unit is None:
            return 0.0
        
        # Measurement reward based on information gained
        reward = MEASURE_BASE_REWARD + energy_boost
        
        # Scout units are better at measurement
        if unit.unit_type == UnitType.SCOUT:
            reward *= SCOUT_MEASURE_MULTIPLIER
        
        return reward
    
    def _execute_shield(self, unit: Unit, energy_boost: int) -> float:
        """Execute a shield action."""
        # Shield provides protection and energy
        shield_bonus = SHIELD_BASE_REWARD + energy_boost * SHIELD_ENERGY_MULTIPLIER
        
        # Check if in quantum gate for bonus
        if self.map[unit.position[0], unit.position[1]] == TileType.QUANTUM_GATE.value:
            shield_bonus *= QUANTUM_GATE_SHIELD_MULTIPLIER
        
        return shield_bonus
    
    def _execute_boost(self, unit: Unit, energy_boost: int) -> float:
        """Execute a boost action."""
        # Boost enhances unit capabilities
        boost_amount = BOOST_BASE_REWARD + energy_boost * BOOST_ENERGY_MULTIPLIER
        unit.energy += boost_amount
        return boost_amount
    
    def _execute_attack(self, unit: Unit, direction: Tuple[int, int], energy_boost: int) -> float:
        """Execute an attack action with extended range and boost mechanics."""
        # Only warriors can attack
        if unit.unit_type != UnitType.WARRIOR:
            return 0.0
        
        # Determine attack range based on boost status
        max_range = BOOSTED_ATTACK_RANGE if unit.is_boosted else NORMAL_ATTACK_RANGE
        
        # Find target within range
        target_unit, target_pos = self._find_attack_target_in_range(unit, direction, max_range)
        
        if target_unit is None:
            return 0.0  # No valid target found
        
        # Check if player has enough energy for attack
        if self.player_energy[unit.player_id] < ATTACK_ENERGY_COST:
            return 0.0  # Cannot attack without enough energy
        
        # Deduct attack cost
        self.player_energy[unit.player_id] -= ATTACK_ENERGY_COST
        
        # Calculate damage based on combat power and energy boost
        combat_power = self.unit_stats[unit.unit_type]["combat_power"]
        damage = WARRIOR_BASE_DAMAGE * combat_power * (1 + energy_boost * ENERGY_BOOST_MULTIPLIER)
        
        # Apply entanglement boost damage multiplier
        if unit.is_boosted:
            damage *= ENTANGLEMENT_DAMAGE_MULTIPLIER
            # Consume one boost attack
            unit.boost_attacks_remaining -= 1
            if unit.boost_attacks_remaining <= 0:
                unit.is_boosted = False
                unit.boost_attacks_remaining = 0
        
        # Record combat event for animation
        combat_event = {
            'type': 'attack',
            'attacker_pos': unit.position,
            'target_pos': target_pos,
            'damage': damage,
            'attacker_player': unit.player_id,
            'target_player': target_unit.player_id,
            'target_health_before': target_unit.health,
            'energy_boost': energy_boost,
            'is_boosted': unit.is_boosted or unit.boost_attacks_remaining > 0,  # Show boost status
            'is_long_range': manhattan_distance(unit.position, target_pos) > 1,
            'frame': 0  # Animation frame counter
        }
        self.combat_events.append(combat_event)
        
        # Check if target is on a decoherence field for damage reduction
        target_x, target_y = target_unit.position
        if self.map[target_x, target_y] == TileType.DECOHERENCE_FIELD.value:
            damage *= DECOHERENCE_DAMAGE_REDUCTION  # 50% damage reduction
            combat_event['decoherence_reduction'] = True
        else:
            combat_event['decoherence_reduction'] = False
        
        # Apply damage to target
        target_unit.health -= damage
        
        # Check if target is defeated
        if target_unit.health <= 0:
            target_unit.health = 0
            # Remove defeated unit from the game
            self.units.remove(target_unit)
            reward = UNIT_DEFEAT_REWARD  # Bonus for defeating enemy unit
            # Add defeat event
            combat_event['defeated'] = True
        else:
            reward = damage  # Reward based on damage dealt
            combat_event['defeated'] = False
        
        return reward
    
    def _select_attack_target(self, enemy_units: List[Unit]) -> Unit:
        """
        Select the best target from a list of enemy units.
        Prioritizes: 1) Low health units, 2) Non-warrior units, 3) Unit type priority
        """
        if not enemy_units:
            return None
        
        # Priority order: Harvester (0) > Scout (2) > Warrior (1)
        # This makes sense as harvesters are valuable for economy, scouts for vision, warriors for combat
        unit_type_priority = {
            UnitType.HARVESTER: 3,  # Highest priority (most valuable)
            UnitType.SCOUT: 2,      # Medium priority
            UnitType.WARRIOR: 1     # Lowest priority (can fight back)
        }
        
        # Score each unit based on health and type priority
        best_target = None
        best_score = float('-inf')
        
        for enemy_unit in enemy_units:
            # Lower health = higher priority (easier to kill)
            health_score = 100 - enemy_unit.health
            
            # Type priority (higher number = higher priority)
            type_score = unit_type_priority.get(enemy_unit.unit_type, 0) * 50
            
            # Combined score
            total_score = health_score + type_score
            
            if total_score > best_score:
                best_score = total_score
                best_target = enemy_unit
        
        return best_target
    
    def _execute_create_entanglement_zone(self, unit: Unit, direction: Tuple[int, int], energy_boost: int) -> float:
        """Execute creating an entanglement zone action."""
        # Only warriors and scouts can create entanglement zones
        if unit.unit_type not in [UnitType.WARRIOR, UnitType.SCOUT]:
            return 0.0
        
        # Calculate target position (can be current position if direction is (0,0))
        target_x = unit.position[0] + direction[0]
        target_y = unit.position[1] + direction[1]
        target_pos = (target_x, target_y)
        
        # Validate position
        if not is_valid_position(target_pos, self.map_size):
            return 0.0
        
        # Check if tile is empty (no existing special tiles)
        if self.map[target_x, target_y] != TileType.EMPTY.value:
            return 0.0  # Can only build on empty tiles
        
        # Check if there are opposing units at the target position
        if self._has_opposing_units(target_pos, unit.player_id):
            return 0.0  # Cannot build on tiles with opposing units
        
        # Energy cost for creating entanglement zone (fixed cost, energy_boost ignored)
        creation_cost = ENTANGLEMENT_ZONE_CREATION_BASE_COST
        if self.player_energy[unit.player_id] < creation_cost:
            return 0.0  # Not enough energy
        
        # Deduct energy cost
        self.player_energy[unit.player_id] -= creation_cost
        
        # Create the entanglement zone
        self.map[target_x, target_y] = TileType.ENTANGLEMENT_ZONE.value
        self.entanglement_zones.append(target_pos)
        self.entanglement_zone_power.append(ENTANGLEMENT_ZONE_INITIAL_POWER)
        
        # Reward for successful creation (base reward only, energy_boost ignored)
        reward = CREATE_ENTANGLEMENT_ZONE_BASE_REWARD
        
        return reward
    
    def _check_and_apply_entanglement_boost(self, unit: Unit) -> bool:
        """Check if warrior is on entanglement zone and apply boost if possible."""
        if unit.unit_type != UnitType.WARRIOR:
            return False
        
        # Check if already boosted
        if unit.is_boosted:
            return False
        
        # Check if on entanglement zone
        if unit.position not in self.entanglement_zones:
            return False
        
        # Find the zone index
        zone_index = self.entanglement_zones.index(unit.position)
        
        # Check if zone has enough power
        if self.entanglement_zone_power[zone_index] < ENTANGLEMENT_ZONE_BOOST_COST:
            return False
        
        # Apply boost
        unit.is_boosted = True
        unit.boost_attacks_remaining = ENTANGLEMENT_ZONE_BOOST_ATTACKS
        
        # Deduct power from zone
        self.entanglement_zone_power[zone_index] -= ENTANGLEMENT_ZONE_BOOST_COST
        
        # Check if zone is depleted
        if self.entanglement_zone_power[zone_index] <= 0:
            # Remove the zone
            depleted_pos = self.entanglement_zones[zone_index]
            self.map[depleted_pos[0], depleted_pos[1]] = TileType.EMPTY.value
            self.entanglement_zones.pop(zone_index)
            self.entanglement_zone_power.pop(zone_index)
        
        return True
    
    def _find_attack_target_in_range(self, unit: Unit, direction: Tuple[int, int], max_range: int) -> Tuple[Optional[Unit], Optional[Tuple[int, int]]]:
        """Find the best attack target within range in the given direction."""
        # Start from the unit's position and search in the direction
        current_x, current_y = unit.position
        
        # Search along the direction up to max_range
        for distance in range(1, max_range + 1):
            target_x = current_x + direction[0] * distance
            target_y = current_y + direction[1] * distance
            target_pos = (target_x, target_y)
            
            # Check if position is valid
            if not is_valid_position(target_pos, self.map_size):
                break  # Hit map boundary
            
            # Get all units at this position
            units_at_target = self._get_units_at_position(target_pos)
            enemy_units = [u for u in units_at_target if u.player_id != unit.player_id]
            
            if enemy_units:
                # Found enemy units, select the best target
                target_unit = self._select_attack_target(enemy_units)
                return target_unit, target_pos
            
            # Check if there's a barrier or other obstacle that blocks further attacks
            if self.map[target_x, target_y] == TileType.QUANTUM_BARRIER.value:
                break  # Blocked by barrier
        
        return None, None
    
    def _get_unit_at_position(self, position: Tuple[int, int]) -> Optional[Unit]:
        """Get unit at a specific position."""
        for unit in self.units:
            if unit.position == position:
                return unit
        return None
    
    def _get_units_at_position(self, position: Tuple[int, int]) -> List[Unit]:
        """Get all units at a specific position."""
        units_at_pos = []
        for unit in self.units:
            if unit.position == position:
                units_at_pos.append(unit)
        return units_at_pos
    
    def _has_opposing_units(self, position: Tuple[int, int], player_id: int) -> bool:
        """Check if there are any opposing units at a position."""
        # Allow both teams to occupy quantum gate tiles
        x, y = position
        if self.map[x, y] == TileType.QUANTUM_GATE.value:
            return False  # Quantum gates allow shared occupancy
        
        for unit in self.units:
            if unit.position == position and unit.player_id != player_id:
                return True
        return False
    
    def _find_closest_empty_spawn_position(self, original_position: Tuple[int, int], player_id: int) -> Optional[Tuple[int, int]]:
        """
        Find the closest empty tile to the original spawn position that can be used for spawning.
        
        Args:
            original_position: The original intended spawn position
            player_id: ID of the player trying to spawn
            
        Returns:
            Closest valid spawn position, or None if no valid position found within reasonable distance
        """
        x, y = original_position
        max_search_radius = min(self.map_size // 2, 10)  # Limit search to reasonable distance
        
        # Use BFS to find closest empty position
        from collections import deque
        queue = deque([(x, y, 0)])  # (x, y, distance)
        visited = {(x, y)}
        
        while queue:
            curr_x, curr_y, distance = queue.popleft()
            
            # Skip if we've searched too far
            if distance > max_search_radius:
                continue
                
            # Check if current position is valid for spawning
            if self._is_valid_spawn_position((curr_x, curr_y), player_id):
                return (curr_x, curr_y)
            
            # Add adjacent positions to search
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                new_x, new_y = curr_x + dx, curr_y + dy
                
                # Check bounds
                if (0 <= new_x < self.map_size and 0 <= new_y < self.map_size and 
                    (new_x, new_y) not in visited):
                    visited.add((new_x, new_y))
                    queue.append((new_x, new_y, distance + 1))
        
        return None  # No valid spawn position found
    
    def _is_valid_spawn_position(self, position: Tuple[int, int], player_id: int) -> bool:
        """
        Check if a position is valid for spawning a unit.
        
        Args:
            position: Position to check
            player_id: ID of the player trying to spawn
            
        Returns:
            True if position is valid for spawning, False otherwise
        """
        x, y = position
        
        # Check bounds
        if not (0 <= x < self.map_size and 0 <= y < self.map_size):
            return False
        
        # Check if tile is blocked by quantum barrier
        if self.map[x, y] == TileType.QUANTUM_BARRIER.value:
            return False
        
        # Check if position has opposing units (same-team units can share spawn positions)
        if self._has_opposing_units(position, player_id):
            return False
        
        # Position is valid for spawning
        return True
    
    def _update_energy_nodes(self):
        """Update energy node values over time."""
        # Energy nodes no longer regenerate - they are finite resources
        pass
    
    def _update_quantum_states(self):
        """Update quantum states of all units."""
        for unit in self.units:
            # Simple quantum state evolution
            if unit.quantum_state is not None:
                # Add some quantum noise
                noise = np.random.normal(QUANTUM_NOISE_MEAN, QUANTUM_NOISE_STD, 2)
                unit.quantum_state += noise
                # Normalize
                norm = np.linalg.norm(unit.quantum_state)
                if norm > 0:
                    unit.quantum_state /= norm
    
    def _cleanup_dead_units(self):
        """Remove all dead units from the game."""
        # Remove units with health <= 0
        self.units = [unit for unit in self.units if unit.health > 0]
    
    def _update_exploration(self):
        """Update exploration for each player based on unit positions."""
        # Add newly explored tiles to permanent exploration history
        for unit in self.units:
            # Only living units can explore (health > 0)
            if unit.health > 0:
                exploration_range = self.exploration_ranges[unit.unit_type]
                player_id = unit.player_id
                
                # Explore tiles within range
                for dx in range(-exploration_range, exploration_range + 1):
                    for dy in range(-exploration_range, exploration_range + 1):
                        # Check if within range (Manhattan distance)
                        if abs(dx) + abs(dy) <= exploration_range:
                            explore_x = unit.position[0] + dx
                            explore_y = unit.position[1] + dy
                            
                            # Check if position is valid
                            if 0 <= explore_x < self.map_size and 0 <= explore_y < self.map_size:
                                self.explored_tiles[player_id].add((explore_x, explore_y))
    
    def _check_victory_conditions(self) -> Tuple[bool, Optional[int]]:
        """
        Check if any victory conditions are met.
        
        Returns:
            terminated: Whether the game has ended
            winner: Player ID of winner (None if no winner yet)
        """
        # Elimination victory - check if a player has no units left
        player_0_units = [unit for unit in self.units if unit.player_id == 0]
        player_1_units = [unit for unit in self.units if unit.player_id == 1]
        
        if len(player_0_units) == 0 and len(player_1_units) > 0:
            return True, 1  # Player 1 wins by elimination
        if len(player_1_units) == 0 and len(player_0_units) > 0:
            return True, 0  # Player 0 wins by elimination
        if len(player_0_units) == 0 and len(player_1_units) == 0:
            return True, None  # Mutual elimination - tie
        
        # Energy victory
        if self.player_energy[0] >= self.energy_victory_threshold:
            return True, 0
        if self.player_energy[1] >= self.energy_victory_threshold:
            return True, 1
        
        # Territory victory
        if self.territory_control[0] >= self.territory_victory_threshold:
            self.territory_control_turns[0] += 1
            if self.territory_control_turns[0] >= self.territory_victory_turns:
                return True, 0
        else:
            self.territory_control_turns[0] = 0
        
        if self.territory_control[1] >= self.territory_victory_threshold:
            self.territory_control_turns[1] += 1
            if self.territory_control_turns[1] >= self.territory_victory_turns:
                return True, 1
        else:
            self.territory_control_turns[1] = 0
        
        # Turn limit victory
        if self.turn >= self.max_turns:
            if self.player_energy[0] > self.player_energy[1]:
                return True, 0
            elif self.player_energy[1] > self.player_energy[0]:
                return True, 1
            else:
                return True, None  # Tie
        
        return False, None
    
    def _get_observation(self) -> Dict[str, np.ndarray]:
        """Get the current observation with fog of war."""
        # Convert units to array format (expanded to include boost info)
        # NOTE: This returns ALL units for internal use - use get_player_observation for fog of war
        # Create dynamic array that can hold all units (no artificial limits)
        max_array_size = max(1000, len(self.units) + 100)  # Ensure enough space
        units_array = np.zeros((max_array_size, 8), dtype=np.int16)
        for i, unit in enumerate(self.units):  # Include ALL units, no limits
            units_array[i] = [
                unit.unit_id,  # Use actual unit ID to match _execute_unit_action lookup
                unit.player_id,
                unit.unit_type.value,
                unit.position[0],
                unit.position[1],
                int(unit.health),
                int(unit.is_boosted),  # Boost status (0 or 1)
                unit.boost_attacks_remaining  # Remaining boosted attacks
            ]
        
        # Create fog of war map for each player
        fog_maps = []
        for player_id in range(2):
            fog_map = np.zeros((self.map_size, self.map_size), dtype=np.int8)
            
            # Copy explored tiles
            for x, y in self.explored_tiles[player_id]:
                fog_map[x, y] = self.map[x, y]
            
            # Hide unexplored tiles (set to -1 for unknown)
            for x in range(self.map_size):
                for y in range(self.map_size):
                    if (x, y) not in self.explored_tiles[player_id]:
                        fog_map[x, y] = -1
            
            fog_maps.append(fog_map)
        
        return {
            'map': self.map.copy(),  # Full map (for internal use)
            'fog_maps': np.array(fog_maps, dtype=np.int8),  # Fog of war maps for each player
            'units': units_array,  # All units (for internal use - agents should use get_player_observation)
            'player_energy': np.array(self.player_energy, dtype=np.float32),
            'turn': np.array([self.turn], dtype=np.int32),
            'territory_control': np.array(self.territory_control, dtype=np.float32),
            'exploration_percentage': np.array([
                len(self.explored_tiles[0]) / (self.map_size * self.map_size),
                len(self.explored_tiles[1]) / (self.map_size * self.map_size)
            ], dtype=np.float32)
        }
    
    def get_player_observation(self, player_id: int) -> Dict[str, np.ndarray]:
        """
        Get observation specific to a player (prevents cheating).
        
        Args:
            player_id: ID of the player (0 or 1)
            
        Returns:
            observation: Player-specific observation with fog of war applied to units
        """
        # Get base observation
        base_obs = self._get_observation()
        
        # Create player-specific observation
        player_obs = base_obs.copy()
        
        # Replace fog_maps with only this player's fog map
        player_obs['fog_maps'] = base_obs['fog_maps'][player_id:player_id+1]  # Keep as 3D array
        
        # Replace exploration_percentage with only this player's percentage
        player_obs['exploration_percentage'] = np.array([
            base_obs['exploration_percentage'][player_id]
        ], dtype=np.float32)
        
        # CRITICAL FIX: Filter units array based on fog of war
        filtered_units = self._filter_units_by_fog_of_war(base_obs['units'], player_id)
        player_obs['units'] = filtered_units
        
        return player_obs
    
    def _filter_units_by_fog_of_war(self, units_array: np.ndarray, player_id: int) -> np.ndarray:
        """
        Filter units array to only show units visible to the specified player.
        
        Args:
            units_array: Full units array from base observation
            player_id: ID of the player (0 or 1)
            
        Returns:
            Filtered units array with fog of war applied
        """
        filtered_units = np.zeros_like(units_array)
        filtered_count = 0
        
        for i in range(units_array.shape[0]):
            unit_data = units_array[i]
            unit_id_obs, unit_player_id, unit_type, unit_x, unit_y, health = unit_data[:6]
            
            # Skip empty unit slots (check if all fields are zero, not just unit_id)
            if health == 0:
                continue
                
            # Always show own units
            if unit_player_id == player_id:
                filtered_units[filtered_count] = unit_data
                filtered_count += 1
                continue
            
            # For enemy units, check if they're in explored areas
            unit_pos = (int(unit_x), int(unit_y))
            if unit_pos in self.explored_tiles[player_id]:
                # Enemy unit is in an explored area - show it
                filtered_units[filtered_count] = unit_data
                filtered_count += 1
            # If enemy unit is in unexplored area, don't include it (fog of war hides it)
        
        return filtered_units
    
    def _get_info(self) -> Dict[str, Any]:
        """Get additional information about the game state."""
        return {
            'turn': self.turn,
            'player_energy': self.player_energy.copy(),
            'territory_control': self.territory_control.copy(),
            'territory_control_turns': self.territory_control_turns.copy(),
            'units': [(u.unit_id, u.player_id, u.unit_type.value, u.position) for u in self.units],
            'energy_nodes': self.energy_nodes.copy(),
            'energy_values': self.energy_values.copy(),
            'exploration_percentage': [
                len(self.explored_tiles[0]) / (self.map_size * self.map_size),
                len(self.explored_tiles[1]) / (self.map_size * self.map_size)
            ],
            'explored_tiles': [list(self.explored_tiles[0]), list(self.explored_tiles[1])],
            'combat_events': self.combat_events.copy(),  # Include combat events for animation
            'entanglement_zones': self.entanglement_zones.copy(),
            'entanglement_zone_power': self.entanglement_zone_power.copy()
        }
    
    def render(self):
        """Render the current game state."""
        if self.render_mode == "human" and self.visualizer is not None:
            observation = self._get_observation()
            info = self._get_info()
            return self.visualizer.render(observation, info)
        return True
    
    def _execute_quantum_gate_health_gain(self, unit: Unit, energy_boost: int) -> float:
        """Execute quantum gate health gain action."""
        # Check if unit is on a quantum gate
        x, y = unit.position
        if self.map[x, y] != TileType.QUANTUM_GATE.value:
            return 0.0  # Not on quantum gate
        
        # Energy cost for health gain
        if self.player_energy[unit.player_id] < QUANTUM_GATE_HEALTH_GAIN_COST:
            return 0.0  # Not enough energy
        
        # Deduct energy cost
        self.player_energy[unit.player_id] -= QUANTUM_GATE_HEALTH_GAIN_COST
        
        # Give health with max health limit
        unit.health = min(unit.health + QUANTUM_GATE_HEALTH_GAIN_AMOUNT, QUANTUM_GATE_MAX_HEALTH_LIMIT)
        
        return QUANTUM_GATE_HEALTH_GAIN_REWARD
    
    def _execute_quantum_gate_teleport(self, unit: Unit, direction: Tuple[int, int], energy_boost: int) -> float:
        """Execute quantum gate teleport action."""
        # Check if unit is on a quantum gate
        x, y = unit.position
        if self.map[x, y] != TileType.QUANTUM_GATE.value:
            return 0.0  # Not on quantum gate
        
        # Find target quantum gate position from direction
        # Direction should encode the target quantum gate coordinates
        # For simplicity, we'll use direction as offset to find target gate
        target_x = direction[0] if direction[0] >= 0 else self.map_size + direction[0]
        target_y = direction[1] if direction[1] >= 0 else self.map_size + direction[1]
        target_pos = (target_x, target_y)
        
        # Validate target position
        if not is_valid_position(target_pos, self.map_size):
            return 0.0
        
        # Check if target position is a quantum gate
        if self.map[target_x, target_y] != TileType.QUANTUM_GATE.value:
            return 0.0  # Target is not a quantum gate
        
        # Energy cost for teleportation
        if self.player_energy[unit.player_id] < QUANTUM_GATE_TELEPORT_COST:
            return 0.0  # Not enough energy
        
        # Deduct energy cost
        self.player_energy[unit.player_id] -= QUANTUM_GATE_TELEPORT_COST
        
        # Teleport unit to target quantum gate
        unit.position = target_pos
        
        return QUANTUM_GATE_TELEPORT_REWARD
    
    def _execute_build_decoherence_field(self, unit: Unit, direction: Tuple[int, int], energy_boost: int) -> float:
        """Execute build decoherence field action."""
        # Calculate target position
        target_x = unit.position[0] + direction[0]
        target_y = unit.position[1] + direction[1]
        target_pos = (target_x, target_y)
        
        # Validate target position
        if not is_valid_position(target_pos, self.map_size):
            return 0.0
        
        # Check if target tile is empty
        if self.map[target_x, target_y] != TileType.EMPTY.value:
            return 0.0  # Can only build on empty tiles
        
        # Check energy cost
        if self.player_energy[unit.player_id] < BUILDING_COSTS["DECOHERENCE_FIELD"]:
            return 0.0  # Not enough energy
        
        # Deduct energy cost
        self.player_energy[unit.player_id] -= BUILDING_COSTS["DECOHERENCE_FIELD"]
        
        # Place decoherence field
        self.map[target_x, target_y] = TileType.DECOHERENCE_FIELD.value
        
        return 10.0  # Base reward for building
    
    def _execute_build_quantum_barrier(self, unit: Unit, direction: Tuple[int, int], energy_boost: int) -> float:
        """Execute build quantum barrier action."""
        # Calculate target position
        target_x = unit.position[0] + direction[0]
        target_y = unit.position[1] + direction[1]
        target_pos = (target_x, target_y)
        
        # Validate target position
        if not is_valid_position(target_pos, self.map_size):
            return 0.0
        
        # Check if target tile is empty
        if self.map[target_x, target_y] != TileType.EMPTY.value:
            return 0.0  # Can only build on empty tiles
        
        # Check energy cost
        if self.player_energy[unit.player_id] < BUILDING_COSTS["QUANTUM_BARRIER"]:
            return 0.0  # Not enough energy
        
        # Deduct energy cost
        self.player_energy[unit.player_id] -= BUILDING_COSTS["QUANTUM_BARRIER"]
        
        # Place quantum barrier
        self.map[target_x, target_y] = TileType.QUANTUM_BARRIER.value
        
        return 10.0  # Base reward for building
    
    def _execute_build_quantum_gate(self, unit: Unit, direction: Tuple[int, int], energy_boost: int) -> float:
        """Execute build quantum gate action."""
        # Calculate target position
        target_x = unit.position[0] + direction[0]
        target_y = unit.position[1] + direction[1]
        target_pos = (target_x, target_y)
        
        # Validate target position
        if not is_valid_position(target_pos, self.map_size):
            return 0.0
        
        # Check if target tile is empty
        if self.map[target_x, target_y] != TileType.EMPTY.value:
            return 0.0  # Can only build on empty tiles
        
        # Check energy cost
        if self.player_energy[unit.player_id] < BUILDING_COSTS["QUANTUM_GATE"]:
            return 0.0  # Not enough energy
        
        # Deduct energy cost
        self.player_energy[unit.player_id] -= BUILDING_COSTS["QUANTUM_GATE"]
        
        # Place quantum gate
        self.map[target_x, target_y] = TileType.QUANTUM_GATE.value
        
        return 25.0  # Higher reward for expensive quantum gate
    
    def close(self):
        """Close the environment."""
        if self.visualizer is not None:
            self.visualizer.close()
        
        # Save game log if logging is enabled
        if self.log_game and self.game_log:
            self._save_game_log()
    
    def _log_game_state(self, event_type: str, action: Optional[Dict], observation: Dict[str, np.ndarray], 
                       info: Dict[str, Any], reward: float = 0.0, terminated: bool = False, truncated: bool = False):
        """Log the current game state for replay."""
        if not self.log_game:
            return
        
        # Convert numpy arrays to lists for JSON serialization
        log_entry = {
            "type": event_type,
            "turn": int(observation['turn'][0]),
            "timestamp": datetime.now().isoformat(),
            "observation": {
                "map": observation['map'].tolist(),
                "fog_maps": observation['fog_maps'].tolist(),
                "units": observation['units'].tolist(),
                "player_energy": observation['player_energy'].tolist(),
                "turn": observation['turn'].tolist(),
                "territory_control": observation['territory_control'].tolist(),
                "exploration_percentage": observation['exploration_percentage'].tolist()
            },
            "info": {
                "turn": info['turn'],
                "player_energy": info['player_energy'],
                "territory_control": info['territory_control'],
                "territory_control_turns": info['territory_control_turns'],
                "units": info['units'],
                "energy_nodes": info['energy_nodes'],
                "energy_values": info['energy_values'],
                "exploration_percentage": info['exploration_percentage'],
                "explored_tiles": info['explored_tiles'],
                "combat_events": info['combat_events'],
                "entanglement_zones": info['entanglement_zones'],
                "entanglement_zone_power": info['entanglement_zone_power']
            }
        }
        
        # Add action data for step events
        if event_type == "step" and action is not None:
            # Convert action dict to serializable format
            serializable_action = {}
            for unit_id, action_array in action.items():
                serializable_action[str(unit_id)] = action_array.tolist() if hasattr(action_array, 'tolist') else list(action_array)
            
            log_entry["action"] = serializable_action
            log_entry["reward"] = float(reward)
            log_entry["terminated"] = terminated
            log_entry["truncated"] = truncated
        
        # Add winner info if game ended
        if terminated and 'winner' in info:
            log_entry["winner"] = info['winner']
        
        self.game_log.append(log_entry)
    
    def _save_game_log(self):
        """Save the game log to a compressed JSON file."""
        try:
            # Create logs directory if it doesn't exist
            log_dir = "game_logs"
            os.makedirs(log_dir, exist_ok=True)
            
            # Full path to log file (will be compressed)
            log_path = os.path.join(log_dir, self.log_file)
            
            # Import compression utilities
            from .replay_compression import save_replay_data
            
            # Save with compression enabled
            saved_path = save_replay_data(self.game_log, log_path, compress=True)
            
            print(f"Game log saved to: {saved_path}")
            
        except Exception as e:
            print(f"Error saving game log: {e}")
    
    def get_log_file_path(self) -> Optional[str]:
        """Get the full path to the log file."""
        if self.log_game and self.log_file:
            # Return the compressed file path since we now save as .json.gz
            if not self.log_file.endswith('.json.gz'):
                compressed_filename = self.log_file.replace('.json', '.json.gz')
            else:
                compressed_filename = self.log_file
            return os.path.join("game_logs", compressed_filename)
        return None 
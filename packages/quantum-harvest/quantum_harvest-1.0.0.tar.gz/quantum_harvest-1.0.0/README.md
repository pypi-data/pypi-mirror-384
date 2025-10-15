# Quantum Harvest

A competitive 1v1 AI strategy game combining quantum mechanics with strategic resource management and territory control.

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Game Rules](#game-rules)
5. [State Space Reference](#state-space-reference)
6. [Action Space Reference](#action-space-reference)
7. [Agent Development Guide](#agent-development-guide)
8. [Running Games](#running-games)
9. [Replay Visualization](#replay-visualization)
10. [License](#license)

---

## Overview

Quantum Harvest is a turn-based strategy game where two AI agents compete for quantum energy resources on a procedurally generated map. Players control units that can harvest energy, engage in combat, and manipulate quantum mechanics to gain strategic advantages.

### Key Features
- **Multi-victory paths**: Win by unit elimination, energy accumulation, or territory control
- **Quantum mechanics**: Leverage entanglement, decoherence, and quantum gates for tactical advantages
- **Strategic depth**: Balance resource management, unit production, and combat
- **AI-focused design**: Built specifically for reinforcement learning and AI agent development
- **Full observability**: Comprehensive state space with fog-of-war exploration mechanics

---

## Installation

### From PyPI (Recommended)

```bash
pip install quantum-harvest
```

### From Source

```bash
git clone https://github.com/tanaka-chiromo/quantum-harvest.git
cd quantum-harvest
pip install -e .
```

### Requirements
- Python 3.8+
- numpy >= 1.21.0
- pygame >= 2.1.0
- gymnasium >= 0.28.0

---

## Quick Start

### 1. Run a Game

```bash
# Run two agents against each other (using CLI)
quantum-harvest play --agent1 my_agent.py --agent2 opponent_agent.py

# Or using Python module directly
python -m quantum_harvest.agent_v_agent_script --agent1 my_agent.py --agent2 opponent_agent.py

# With custom settings
quantum-harvest play \
    --agent1 my_agent.py \
    --agent2 opponent_agent.py \
    --map-size 16 \
    --max-turns 500
```

### 2. View Replay

```bash
# Launch replay visualizer (using CLI)
quantum-harvest replay game_log_20241201_143022.json

# Or using Python module directly
python -m quantum_harvest.run_replay_visualizer game_log_20241201_143022.json
```

### 3. Get Help

```bash
# Show CLI help
quantum-harvest --help

# Show package info
quantum-harvest info

# Show version
quantum-harvest version
```

### 4. Start Developing

See `quantum_harvest/starter_agent.py` for a complete template and example agent implementation.

---

## Game Rules

### Victory Conditions

Players can win by achieving any of the following in order:

1. **Unit Elimination**: Eliminate all of the opponent's units
2. **Energy Victory**: Accumulate more energy than your opponent by episode end
3. **Territory Victory**: Control more territory than your opponent by episode end
4. **Turn Limit**: Episodes end after 1000 turns (default, configurable)

### Map Generation

- **Size**: Default 12×12 grid (configurable)
- **Energy Nodes**: Randomly placed pairs containing 1000-2000 energy each
- **Quantum Structures**: Barriers, entanglement zones, decoherence fields, and quantum gates
- **Symmetric Layout**: Both players start with equal resources and positioning

### Turn Flow

1. Both players receive game state observation
2. Players select actions for all their units simultaneously
3. Actions are executed in resolution order (see below)
4. Game state updates and victory conditions are checked
5. Next turn begins

### Action Resolution Order

**Player 1 (player_id=0) has first-move advantage:**
- All of Player 1's unit actions are processed **first**
- All of Player 2's unit actions are processed **second**

**Strategic implications:**
- **Contested tiles**: If both players move to the same empty tile, Player 1's unit gets it
- **Resource competition**: Player 1 can claim energy nodes first
- **Attack priority**: Player 1's attacks resolve before Player 2's
- **Position blocking**: Player 1 can occupy strategic positions before Player 2 can reach them

**Example - Contested Tile:**
```
Setup: Both players move units to the same empty tile (3, 3)
Resolution:
  1. Player 1's unit moves to (3, 3) ✅ (processed first)
  2. Player 2's unit tries to move to (3, 3) ❌ (blocked by Player 1's unit)
Result: Player 1's unit occupies (3, 3), Player 2's unit stays at original position
```

**Strategic considerations:**
- Player 1 should be aggressive in contested situations (has advantage)
- Player 2 should anticipate Player 1's moves and plan alternative strategies
- Quantum gates allow shared occupancy, negating this advantage for those tiles

### Fog of War and Exploration

**Exploration System:**

Each unit explores tiles around it based on its **exploration range** (Manhattan distance):
- **Scouts**: 3 tiles (best vision)
- **Harvesters**: 1 tile
- **Warriors**: 1 tile

**Permanent Exploration:**
- Once a tile is explored, it remains **permanently visible** to that player
- Explored tiles never become "fog of war" again
- You have **continuous real-time vision** of all explored tiles

**What You Can See in Explored Tiles:**

✅ **Always Visible:**
- **Tile types**: Energy nodes, barriers, gates, zones, decoherence fields
- **Resources**: Current energy levels in energy nodes
- **Structures**: All quantum structures and their states
- **Enemy units**: Enemy units are visible **whenever** they are in explored tiles
- **Unit details**: Full information about visible enemy units (type, health, position, boost status)

❌ **Never Visible:**
- **Unexplored tiles**: Show as unknown (`-1` in fog_maps)
- **Enemy units in unexplored areas**: Completely hidden until you explore those tiles

**Strategic implications:**
- **Scouts are crucial** for map vision (3-tile range vs 1-tile for others)
- **Early exploration** gives permanent vision advantage
- **Enemy movements are tracked** in real-time within explored areas
- **Enemies can hide** by retreating to unexplored territory
- **Resource monitoring** - you can track enemy harvesting activity in explored areas
- **No re-exploration needed** - once explored, always visible

### Unit Types

#### Harvester (Unit Type 0)
**Role**: Resource collection specialist

- **Cost**: 10 energy
- **Health**: 45 HP
- **Harvest Rate**: 1.0 energy/turn (most efficient)
- **Attack Damage**: Cannot attack
- **Movement**: 1 tile per turn
- **Exploration Range**: 1 tile
- **Building Abilities**: Decoherence fields, quantum barriers, quantum gates

**Strategy**: Essential for early game energy accumulation. Vulnerable to warriors—protect accordingly.

#### Warrior (Unit Type 1)
**Role**: Combat and territory control specialist

- **Cost**: 100 energy
- **Health**: 45 HP
- **Harvest Rate**: Cannot harvest
- **Attack Damage**: 30 HP/attack (normal), 45 HP/attack (boosted)
- **Attack Range**: 1 tile (normal), 4 tiles (boosted)
- **Movement**: 1 tile per turn
- **Exploration Range**: 1 tile
- **Special Abilities**: 
  - Can receive entanglement boosts (1.5× damage multiplier, 4-tile range)
  - Can create entanglement zones
  - Can build all quantum structures
  - Boost duration: 2 attacks, then returns to normal

**Strategy**: Primary combat unit. Use entanglement zones to boost attack power and range. Expensive but powerful.

#### Scout (Unit Type 2)
**Role**: Exploration, spawning, and quantum operations specialist

- **Cost**: 10 energy
- **Health**: 45 HP
- **Harvest Rate**: 0.25 energy/turn (moderate)
- **Attack Damage**: Cannot attack
- **Movement**: 1 tile per turn
- **Exploration Range**: 3 tiles (best vision)
- **Special Abilities**:
  - Can spawn new units (harvesters, warriors, scouts)
  - Can create entanglement zones
  - Can build all quantum structures
  - Access to quantum movement and measurement
  - Can use quantum gates

**Strategy**: Versatile support unit. Superior vision range makes it excellent for reconnaissance. Can spawn units and build structures.

### Tile Types and Quantum Mechanics

#### Energy Nodes (TileType.ENERGY_NODE = 1)
**Purpose**: Harvestable resource nodes

- **Energy content**: 1000-2000 units per node
- **Harvest formula**: `harvest_amount = base_amount × unit_efficiency`
- **Fixed harvest amounts**:
  - Harvester: 1.0 energy per harvest (0.5 base × 2.0 efficiency)
  - Scout: 0.25 energy per harvest (0.25 base × 1.0 efficiency)
  - Warrior: Cannot harvest (0.0 efficiency)
- **Depletion**: Each harvest reduces node energy by 1.0; nodes become empty when depleted
- **Usage**: Units must use HARVEST action while standing on the node

**Strategy**: Core resource for economy. Protect with warriors and harvest efficiently with harvesters.

#### Quantum Barriers (TileType.QUANTUM_BARRIER = 2)
**Purpose**: Movement blocking and area denial

- **Construction cost**: 200 energy
- **Built by**: Any unit on adjacent empty tiles
- **Movement blocking**: Regular MOVE action fails on barriers
- **Quantum movement**: QUANTUM_MOVE always costs 100 energy but can pass through barriers
- **Line-of-sight blocking**: Blocks warrior attack line-of-sight

**Strategy**: Force enemies to use expensive quantum movement (100 energy) instead of free regular movement. Use defensively to protect key areas or offensively to limit enemy mobility.

#### Entanglement Zones (TileType.ENTANGLEMENT_ZONE = 3)
**Purpose**: Combat enhancement for warriors

- **Construction cost**: 100 energy
- **Built by**: Warriors and scouts only
- **Zone power**: 200 entanglement-units (depletes with use)
- **Automatic boost**: Warriors automatically receive boosts when stepping onto entanglement zones (if not already boosted and zone has power)
- **Boost effects**: 
  - 1.5× damage multiplier
  - 4-tile attack range (vs normal 1-tile)
  - Lasts for exactly 2 attacks
  - Consumes 50 entanglement-units from zone per boost
- **Occupancy**: Multiple units from same team can occupy; opposing teams cannot share
- **Depletion**: Zone becomes empty when entanglement-units reach zero

⚠️ **Critical**: Can boost enemy warriors too! Use carefully.

**Strategy**: Build near frontlines to enhance warrior attacks. Be cautious—enemies can use your zones against you.

#### Decoherence Fields (TileType.DECOHERENCE_FIELD = 4)
**Purpose**: Defensive protection and boost removal

- **Construction cost**: 100 energy
- **Built by**: Any unit
- **Defensive effect**: 50% damage reduction for units on these tiles
- **Anti-boost effect**: Removes all boosts from warriors who land on these tiles (both regular and quantum movement trigger this)

**Strategy**: Use defensively to reduce incoming damage. Place strategically to neutralize enemy boosted warriors.

#### Quantum Gates (TileType.QUANTUM_GATE = 5)
**Purpose**: Health restoration and teleportation

- **Construction cost**: 100 energy
- **Built by**: Any unit
- **Health restoration**: QUANTUM_GATE_HEALTH_GAIN action restores 50 health for 50 energy (max 300 health)
- **Teleportation**: QUANTUM_GATE_TELEPORT action allows instant movement to any other quantum gate for 25 energy
  - Must be standing on a quantum gate to teleport
  - Target must also be a quantum gate
  - Failed teleports cost 0 energy
- **Shared occupation**: Both teams can occupy the same quantum gate simultaneously

**Strategy**: Create gate networks for rapid repositioning and healing. Useful for quick reinforcement or retreat.

### Combat Mechanics

#### Attack Range and Line-of-Sight

When a warrior attacks (Action Type 7), the game searches for targets along the specified direction:

**Rules:**
1. **First-target priority**: Attack hits the **first enemy unit** encountered along the attack direction
2. **Range limits**: 
   - Normal warriors: 1 tile range (adjacent only)
   - Entanglement-boosted warriors: 4 tiles range
3. **Line-of-sight blocking**: 
   - ✅ **Can attack through**: Empty tiles, energy nodes, entanglement zones, decoherence fields, quantum gates
   - ❌ **Cannot attack through**: Quantum barriers (block line of sight)
4. **Map boundaries**: Attack search stops at map edges

**Examples:**

```
Example 1 - Clear line of sight:
W . . E .    (W = Your boosted warrior, E = Enemy, . = Empty)
Action: [7, 2, 1, 0] (attack right)
Result: ✅ Hits enemy at distance 3

Example 2 - Multiple enemies in line:
W . E E .
Action: [7, 2, 1, 0] (attack right)
Result: ✅ Hits the FIRST enemy at distance 2 (not the farther one)

Example 3 - Barrier blocking:
W . B E .    (B = Quantum barrier)
Action: [7, 2, 1, 0] (attack right)
Result: ❌ Cannot attack - barrier blocks line of sight

Example 4 - Out of range (normal warrior):
W . . E .
Action: [7, 2, 1, 0] (attack right, not boosted)
Result: ❌ Cannot attack - enemy at distance 3, normal warriors only have 1-tile range
```

#### Damage Calculation

**Damage Formula**: 
```
damage = 15 × 2.0 × (1 + energy_boost × 0.2) × entanglement_multiplier
```

Where:
- `entanglement_multiplier = 1.5` (if warrior is boosted) or `1.0` (normal)
- `energy_boost` ranges from 0 to 4

**Damage and Energy Cost Table:**

| energy_boost | Normal Damage | Boosted Damage | Energy Cost |
|--------------|---------------|----------------|-------------|
| 0 (base)     | 30 HP         | 45 HP          | 15 energy   |
| 1            | 36 HP         | 54 HP          | 16 energy   |
| 2            | 42 HP         | 63 HP          | 17 energy   |
| 3            | 48 HP         | 72 HP          | 18 energy   |
| 4            | 54 HP         | 81 HP          | 19 energy   |

**Strategic implications:**
- Use quantum barriers defensively to block enemy warrior line-of-sight
- Boosted warriors can attack from safer distances (up to 4 tiles)
- Position units carefully—warriors always hit the closest enemy in their line of fire
- Energy boost provides marginal damage increases at increasing cost

#### Unit Stacking and Target Selection

**Where Units Can Stack:**

1. **Quantum Gates**: ✅ Both teams can occupy the same quantum gate simultaneously
   - Multiple friendly units can stack
   - Multiple enemy units can stack on the same gate
   - This is the ONLY tile type that allows enemy stacking

2. **All Other Tiles**: ❌ Enemy units cannot occupy the same tile
   - Multiple units from the same team CAN stack
   - Units from opposing teams CANNOT stack (movement blocked)

**Attack Target Selection on Stacked Units:**

When a warrior attacks a tile with multiple enemy units, the game automatically selects ONE target based on a priority system.

**Priority Formula**: `Score = (100 - unit_health) + (unit_type_priority × 50)`

**Unit Type Priorities:**
- **Harvester**: Priority 3 (150 points) - Highest priority
- **Scout**: Priority 2 (100 points) - Medium priority  
- **Warrior**: Priority 1 (50 points) - Lowest priority

**Selection rules:**
1. Lower health increases priority (wounded units more likely targeted)
2. Unit type matters more than health in most cases
3. Only ONE unit takes damage per attack (highest scoring target)

**Examples:**

```
Example 1 - Type priority dominates:
Quantum Gate has:
- Enemy Harvester (45 HP): Score = (100-45) + (3×50) = 205
- Enemy Warrior (30 HP): Score = (100-30) + (1×50) = 120
Target: Harvester (despite having more health)

Example 2 - Long-range attack on stacked enemies:
Your boosted warrior is 3 tiles away from stacked enemies:
- Enemy Scout (45 HP): Score = 155
- Enemy Harvester (30 HP): Score = 220
- Enemy Warrior (45 HP): Score = 105
Target: Harvester at 30 HP (highest score)
Result: Only the Harvester takes damage
```

**Strategic implications:**
- Don't stack harvesters with other units—they're almost always targeted first
- Stacking is risky even from long range
- Warriors are the best "shields" (lowest target priority)
- Low-health units become more attractive targets
- Quantum gates are especially risky for valuable units
- Spread out valuable units when possible

---

## State Space Reference

### Observation Structure

The game provides a comprehensive observation dictionary:

```python
observation = {
    'map': np.ndarray,                    # 2D array (map_size × map_size) of tile types
    'units': np.ndarray,                  # Array of all units [unit_id, player_id, unit_type, x, y, health, energy, is_boosted, boost_attacks]
    'player_energy': np.ndarray,          # Array [player_0_energy, player_1_energy]
    'turn': np.ndarray,                   # Current turn number [turn]
    'fog_maps': np.ndarray,               # Player-specific fog of war maps
    'territory_control': np.ndarray,      # Territory control percentages [p1_control, p2_control]
    'exploration_percentage': np.ndarray, # Exploration percentage per player
    'victory_conditions': dict            # Victory condition status
}
```

### Map Array (`observation['map']`)

2D numpy array where each tile is represented by an integer from the `TileType` enum:

- **-1 (UNEXPLORED)**: Tile not yet explored (appears in `fog_maps` only)
- **0 (EMPTY)**: Regular empty tile that can be built upon
- **1 (ENERGY_NODE)**: Contains harvestable energy
- **2 (QUANTUM_BARRIER)**: Blocks regular movement
- **3 (ENTANGLEMENT_ZONE)**: Provides quantum boosts to warriors
- **4 (DECOHERENCE_FIELD)**: Provides defensive protection
- **5 (QUANTUM_GATE)**: Allows health restoration and teleportation

### Units Array (`observation['units']`)

Each unit is represented as an array with 9 elements:

```python
[unit_id, player_id, unit_type, x, y, health, energy, is_boosted, boost_attacks_remaining]
```

- **unit_id**: Unique identifier for the unit (int)
- **player_id**: 0 for Player 1, 1 for Player 2
- **unit_type**: 0=Harvester, 1=Warrior, 2=Scout
- **x, y**: Position coordinates on the map
- **health**: Current health points (default: 45, max: 300)
- **energy**: ⚠️ **Deprecated** - Always 0, not used in gameplay
- **is_boosted**: Boolean (0 or 1) indicating if unit has entanglement boost
- **boost_attacks_remaining**: Number of boosted attacks remaining (0-2)

**Note**: Only units in explored tiles are visible to each player (own units always visible).

### Other Observation Fields

- **player_energy**: `[player_0_energy, player_1_energy]` - visible to both players
- **turn**: `[current_turn_number]` - shared information
- **fog_maps**: Player-specific explored/unexplored tile maps (unexplored = -1)
- **territory_control**: `[player_0_control%, player_1_control%]` - visible to both players
- **exploration_percentage**: `[player_0_explored%, player_1_explored%]` - player-specific

---

## Action Space Reference

### Action Format

Each action is a 4-element array:

```python
[action_type, direction_x, direction_y, energy_boost]
```

- **action_type**: Integer 0-16 (see below)
- **direction_x**: 0=left, 1=no_move, 2=right (for most actions)
- **direction_y**: 0=up, 1=no_move, 2=down (for most actions)
- **energy_boost**: 0-4 energy points for attack damage boost (only used by Action 7)

**Special case**: For QUANTUM_GATE_TELEPORT (Action 13), `direction_x` and `direction_y` represent absolute target coordinates instead.

### Movement Actions

#### Action 0: MOVE
Regular movement to adjacent tile (free, blocked by quantum barriers)

- **Cost**: Free
- **Range**: 1 tile (adjacent, including diagonals)
- **Blocked by**: Quantum barriers, enemy units
- **Examples**:
  - `[0, 2, 1, 0]` - Move right
  - `[0, 0, 0, 0]` - Move diagonally up-left
  - `[0, 1, 2, 0]` - Move down

#### Action 1: QUANTUM_MOVE
Quantum movement (always costs 100 energy, can pass through barriers)

- **Cost**: 100 energy (always, regardless of tile type)
- **Range**: 1 tile (adjacent, including diagonals)
- **Benefit**: Can pass through quantum barriers
- **Blocked by**: Enemy units (except on quantum gates)
- **Examples**:
  - `[1, 2, 1, 0]` - Quantum move right (100 energy)
  - `[1, 0, 2, 0]` - Quantum move diagonally down-left (100 energy)

**Strategic note**: Use when barriers block regular movement. Costs 50% of barrier build cost.

### Resource Actions

#### Action 2: HARVEST
Collect energy from energy nodes (must be standing on node)

- **Cost**: Free
- **Requirements**: Unit must be on an energy node tile
- **Amount**: Fixed based on unit type (see unit harvest rates)
- **Examples**:
  - `[2, 0, 0, 0]` - Harvest energy (direction and energy_boost ignored)

**Note**: Warriors cannot harvest (0 efficiency).

### Combat Actions

#### Action 7: ATTACK
Attack enemy units along a direction (warriors only)

- **Cost**: 15 energy + energy_boost
- **Range**: 1 tile (normal warriors), 4 tiles (boosted warriors)
- **Requires**: Warrior unit type
- **Line-of-sight**: Blocked by quantum barriers
- **Target selection**: First enemy in line-of-sight (see Combat Mechanics)
- **Examples**:
  - `[7, 2, 1, 0]` - Attack enemy to the right (30 HP damage, 15 energy cost)
  - `[7, 0, 0, 2]` - Attack diagonally up-left with boost (42 HP damage, 17 energy cost)
  - `[7, 1, 0, 0]` - Attack enemy above (if boosted, can reach 4 tiles, 45 HP damage)

**Damage formula**: See Combat Mechanics section for full damage table.

### Construction Actions

All units can build these structures:

#### Action 14: BUILD_DECOHERENCE_FIELD
Build decoherence field (100 energy)

- **Cost**: 100 energy
- **Effect**: 50% damage reduction, removes boosts from warriors
- **Target**: Adjacent empty tile
- **Examples**:
  - `[14, 1, 1, 0]` - Build on current tile
  - `[14, 2, 0, 0]` - Build on tile to the right

#### Action 15: BUILD_QUANTUM_BARRIER
Build quantum barrier (200 energy)

- **Cost**: 200 energy
- **Effect**: Blocks regular movement, not quantum movement
- **Target**: Adjacent empty tile
- **Examples**:
  - `[15, 2, 1, 0]` - Build on tile to the right
  - `[15, 1, 0, 0]` - Build on tile above

#### Action 16: BUILD_QUANTUM_GATE
Build quantum gate (100 energy)

- **Cost**: 100 energy
- **Effect**: Enables health restoration and teleportation
- **Target**: Adjacent empty tile
- **Examples**:
  - `[16, 1, 2, 0]` - Build on tile below
  - `[16, 0, 0, 0]` - Build diagonally up-left

### Quantum Actions

#### Action 11: CREATE_ENTANGLEMENT_ZONE
Create an entanglement zone (100 energy, warriors/scouts only)

- **Cost**: 100 energy (fixed, energy_boost ignored)
- **Power**: 200 entanglement-units (fixed, can boost 4 warriors)
- **Built by**: Warriors and scouts only
- **Target**: Adjacent empty tile
- **Examples**:
  - `[11, 1, 1, 0]` - Create on current tile
  - `[11, 2, 1, 0]` - Create on tile to the right

#### Action 12: QUANTUM_GATE_HEALTH_GAIN
Use quantum gate for health restoration (50 energy)

- **Cost**: 50 energy
- **Effect**: +50 health (max 300 HP)
- **Requirements**: Unit must be on a quantum gate
- **Examples**:
  - `[12, 1, 1, 0]` - Gain 50 health (direction ignored)

#### Action 13: QUANTUM_GATE_TELEPORT
Use quantum gate for teleportation (25 energy)

- **Cost**: 25 energy (0 if failed)
- **Requirements**:
  - Unit must be on a quantum gate (origin)
  - Target coordinates must point to another quantum gate
  - Target must be within map boundaries
- **Special**: `direction_x` and `direction_y` are **absolute coordinates** (not relative directions)
- **Examples**:
  - `[13, 5, 8, 0]` - Teleport to quantum gate at position (5, 8)
  - `[13, 10, 3, 0]` - Teleport to quantum gate at position (10, 3)

**Failed teleport**: If requirements not met, action fails with no energy cost.

### Spawning Actions

Scouts only - units spawn at player's origin/starting position:

#### Action 8: SPAWN_HARVESTER
Spawn a new harvester (10 energy)

- **Cost**: 10 energy
- **Spawn location**: Player's starting position
- **Requires**: Scout unit type
- **Examples**: `[8, 1, 1, 0]` (direction ignored)

#### Action 9: SPAWN_WARRIOR
Spawn a new warrior (100 energy)

- **Cost**: 100 energy
- **Spawn location**: Player's starting position
- **Requires**: Scout unit type
- **Examples**: `[9, 1, 1, 0]` (direction ignored)

#### Action 10: SPAWN_SCOUT
Spawn a new scout (10 energy)

- **Cost**: 10 energy
- **Spawn location**: Player's starting position
- **Requires**: Scout unit type
- **Examples**: `[10, 1, 1, 0]` (direction ignored)

### Deprecated Actions

The following actions are present in the code but have no functional effect:

- **Action 3**: ⚠️ Deprecated
- **Action 4**: ⚠️ Deprecated
- **Action 5**: ⚠️ Deprecated
- **Action 6**: ⚠️ Deprecated

These actions remain in the enum for backward compatibility but should not be used in agent strategies.

---

## Agent Development Guide

### Getting Started

**Reference Implementation**: See `quantum_harvest/starter_agent.py` for a starter example.

The starter agent demonstrates:
- How to parse the observation dictionary
- How to structure actions for each unit
- How to access game state information
- Common helper methods for agent development

### Agent Interface

Your agent class must inherit from `BaseAgent` and implement the required methods:

```python
from quantum_harvest.agents import BaseAgent
from quantum_harvest.utils import UnitType, ActionType, TileType
from typing import Dict
import numpy as np

class Agent(BaseAgent):
    """Your custom agent implementation."""
    
    def __init__(self, player_id: int):
        """
        Initialize the agent.
        
        Args:
            player_id: ID of the player this agent controls (0 or 1)
        """
        super().__init__(player_id)
    
    def get_action(self, observation: Dict[str, np.ndarray], player_id: int = 0) -> Dict[int, np.ndarray]:
        """
        Get actions for all units.
        
        Args:
            observation: Current game observation (see State Space Reference)
            player_id: Player ID (0 or 1) - defaults to 0
            
        Returns:
            actions: Dictionary mapping unit_id to action array 
                    [action_type, direction_x, direction_y, energy_boost]
        """
        actions = {}
        # Your agent logic here
        return actions
    
    def reset(self):
        """Reset agent state between games."""
        super().reset()
```

### Development Tips

1. **Parse Units Correctly**: Use the observation structure to identify your units and their states
   ```python
   player_units = observation['units'][observation['units'][:, 1] == self.player_id]
   ```

2. **Handle Action Validation**: The environment validates actions, but invalid actions are ignored
   - Check energy before expensive actions
   - Verify tile types before building
   - Confirm unit types match action requirements

3. **Energy Management**: Balance energy spending between:
   - Unit production (harvesters = 10, warriors = 100, scouts = 10)
   - Structure building (barriers = 200, others = 100)
   - Combat boosts (15 base + 0-4 boost for attacks)
   - Quantum operations (quantum move = 100, teleport = 25)

4. **Territory Control**: Consider multiple strategies:
   - Energy accumulation (harvesters on nodes)
   - Map control (spread units for territory percentage)
   - Combat dominance (eliminate enemy units)

5. **Quantum Mechanics**: Learn to leverage:
   - Entanglement zones for warrior enhancement
   - Decoherence fields for defense
   - Quantum gates for mobility and healing
   - Barriers for area denial

6. **Exploration Priority**: Early scouting provides permanent vision advantage
   - Use scouts (3-tile vision range) for efficient exploration
   - Track enemy movements in explored areas
   - Monitor resource depletion in real-time

### Example Agent Logic

```python
def get_action(self, observation):
    actions = {}
    player_units = self._get_player_units(observation)
    
    for unit_id, player_id, unit_type, x, y, health, energy, is_boosted, boost_attacks in player_units:
        pos = (x, y)
        
        if unit_type == UnitType.HARVESTER.value:
            # Move toward nearest energy node
            action = self._harvester_strategy(pos, observation)
            
        elif unit_type == UnitType.WARRIOR.value:
            # Attack nearby enemies or move toward enemy territory
            action = self._warrior_strategy(pos, health, is_boosted, observation)
            
        elif unit_type == UnitType.SCOUT.value:
            # Explore, spawn units, or build structures
            action = self._scout_strategy(pos, observation)
        
        actions[unit_id] = action
    
    return actions

def _get_player_units(self, observation):
    """Extract and return player's units from observation."""
    units = observation['units']
    return units[units[:, 1] == self.player_id]

def _get_enemy_units(self, observation):
    """Extract and return enemy units from observation."""
    units = observation['units']
    return units[units[:, 1] != self.player_id]
```

---

## Running Games

### Command Line Interface

Run agent vs agent games using `agent_v_agent_script.py`:

```bash
# Basic usage
python -m quantum_harvest.agent_v_agent_script \
    --agent1 my_agent.py \
    --agent2 opponent_agent.py

# With custom settings
python -m quantum_harvest.agent_v_agent_script \
    --agent1 my_agent.py \
    --agent2 opponent_agent.py \
    --map-size 16 \
    --max-turns 500

# Headless mode (no visualization)
python -m quantum_harvest.agent_v_agent_script \
    --agent1 my_agent.py \
    --agent2 opponent_agent.py \
    --no-visualization

# Fast simulation
python -m quantum_harvest.agent_v_agent_script \
    --agent1 my_agent.py \
    --agent2 opponent_agent.py \
    --no-visualization \
    --turn-delay 0
```

### Command Line Options

- `--agent1`: Path to Python file containing agent for player 1 (required)
- `--agent2`: Path to Python file containing agent for player 2 (required)
- `--map-size`: Size of the game map (default: 12)
- `--max-turns`: Maximum number of turns (default: 1000)
- `--no-visualization`: Disable pygame visualization
- `--no-logging`: Disable game state logging
- `--turn-delay`: Delay between turns in seconds (default: 0.1)

### Agent File Requirements

Your agent file must:
- Contain a class named `Agent`
- Inherit from `BaseAgent`
- Implement `get_action(observation, player_id)` method
- Implement `reset()` method
- Accept `player_id` parameter in constructor

The script automatically detects and instantiates the `Agent` class.

### Example Agent File Structure

```python
# my_agent.py
import numpy as np
from quantum_harvest.agents import BaseAgent
from quantum_harvest.utils import UnitType, ActionType, TileType

class Agent(BaseAgent):
    def __init__(self, player_id: int):
        super().__init__(player_id)
        # Your initialization here
    
    def get_action(self, observation, player_id=0):
        actions = {}
        # Your strategy here
        return actions
    
    def reset(self):
        super().reset()
        # Reset your agent state here
```

---

## Replay Visualization

### HTML Replay Visualizer

The game includes a powerful HTML-based replay visualizer that runs in your web browser.

### Launching the Visualizer

```bash
# Open visualizer without loading a replay
python -m quantum_harvest.run_replay_visualizer

# Open visualizer with a specific replay file
python -m quantum_harvest.run_replay_visualizer game_log_20241201_143022.json

# Open compressed replay file
python -m quantum_harvest.run_replay_visualizer compressed_replay.json.gz
```

The visualizer will automatically open in your default web browser.

### Features

- **🌐 Web-based**: Runs in any modern web browser
- **📁 File Upload**: Drag & drop or click to upload replay files
- **🎮 Playback Controls**: Play/pause, step forward/backward, speed control
- **📊 Real-time Stats**: Energy, territory control, unit counts
- **🎯 Combat Animations**: Visual attack effects and damage indicators
- **🗺️ Fog of War**: Team-specific exploration visualization
- **📈 Progress Bar**: Click to jump to any frame
- **⌨️ Keyboard Shortcuts**: Full keyboard control support

### Controls

**Mouse Controls:**
- **Upload Area**: Click or drag files to upload
- **Progress Bar**: Click to jump to specific frames
- **Buttons**: Play/Pause, Step Back/Forward, Speed Control, Reset

**Keyboard Shortcuts:**
- `SPACE`: Play/Pause
- `←` `→`: Step Back/Forward
- `+` `-`: Increase/Decrease Speed
- `HOME`: Go to Start
- `END`: Go to End

### Visual Elements

**Map Tiles:**
- 🟡 **Energy Nodes**: Yellow tiles with energy levels
- ⬜ **Barriers**: Gray quantum barriers
- 🔵 **Entanglement Zones**: Cyan quantum entanglement
- 🟣 **Decoherence Fields**: Magenta decoherence zones
- 🟠 **Quantum Gates**: Orange quantum gates

**Units:**
- 🔴 **Player 1 Units**: Red circles with symbols (H=Harvester, W=Warrior, S=Scout)
- 🔵 **Player 2 Units**: Blue circles with symbols
- 🔢 **Stacked Units**: Numbers show multiple units at same position
- ❤️ **Health Bars**: Green/yellow/red health indicators

### File Support

- **JSON Files**: Standard uncompressed replay files (`.json`)
- **Compressed Files**: Gzip-compressed replay files (`.json.gz`)
- **Auto-detection**: Automatically detects and handles both formats

---

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International License**.

See the [LICENSE](LICENSE) file for details.

**Important**: This license allows you to use, modify, and distribute the software for **non-commercial purposes only**. Commercial use is not permitted without explicit permission from the author.

---

## Support and Contributing

For issues, questions, or contributions:
- **Repository**: https://github.com/tanaka-chiromo/quantum-harvest
- **Issues**: https://github.com/tanaka-chiromo/quantum-harvest/issues

---

**Good luck building your Quantum Harvest AI agent!** 🎮🤖⚛️

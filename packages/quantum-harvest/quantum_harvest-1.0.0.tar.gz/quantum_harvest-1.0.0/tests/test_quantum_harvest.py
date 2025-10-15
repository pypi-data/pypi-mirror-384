"""
Basic tests for Quantum Harvest package.
"""

import pytest
import numpy as np
from quantum_harvest.environment import QuantumHarvestEnv
from quantum_harvest.starter_agent import Agent
from quantum_harvest.agents import BaseAgent
from quantum_harvest.utils import TileType, UnitType, ActionType


class TestEnvironment:
    """Test the game environment."""
    
    def test_environment_creation(self):
        """Test that environment can be created."""
        env = QuantumHarvestEnv()
        assert env is not None
        
    def test_environment_reset(self):
        """Test environment reset functionality."""
        env = QuantumHarvestEnv()
        observation, info = env.reset()
        assert isinstance(observation, dict)
        assert "map" in observation
        assert "units" in observation
        assert isinstance(info, dict)
        
    def test_environment_step(self):
        """Test environment step functionality."""
        env = QuantumHarvestEnv()
        observation, info = env.reset()
        
        # Get first unit for each player
        units_array = observation['units']
        player_0_unit = None
        player_1_unit = None
        
        for i in range(units_array.shape[0]):
            unit_id, player_id, unit_type, x, y, health, is_boosted, boost_attacks = units_array[i]
            if health > 0:
                if player_id == 0 and player_0_unit is None:
                    player_0_unit = int(unit_id)
                elif player_id == 1 and player_1_unit is None:
                    player_1_unit = int(unit_id)
        
        # Create actions using player-specific keys
        combined_actions = {}
        if player_0_unit is not None:
            combined_actions[f"p0_{player_0_unit}"] = np.array([ActionType.MOVE.value, 1, 1, 0])
        if player_1_unit is not None:
            combined_actions[f"p1_{player_1_unit}"] = np.array([ActionType.MOVE.value, 1, 1, 0])
        
        observation, reward, terminated, truncated, info = env.step(combined_actions)
        
        assert isinstance(observation, dict)
        assert isinstance(reward, (int, float))
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)


class TestAgents:
    """Test AI agents."""
    
    def test_base_agent_creation(self):
        """Test BaseAgent creation."""
        agent = BaseAgent(player_id=0)
        assert agent.player_id == 0
        
    def test_starter_agent_creation(self):
        """Test starter Agent creation."""
        agent = Agent(player_id=1)
        assert agent.player_id == 1
        
    def test_agent_action_generation(self):
        """Test that agents can generate actions."""
        env = QuantumHarvestEnv()
        observation, info = env.reset()
        
        agent1 = Agent(player_id=0)
        agent2 = Agent(player_id=1)
        
        # Get player-specific observations
        player1_obs = env.get_player_observation(0)
        player2_obs = env.get_player_observation(1)
        
        action1 = agent1.get_action(player1_obs)
        action2 = agent2.get_action(player2_obs)
        
        assert isinstance(action1, dict)
        assert isinstance(action2, dict)
        # Check that actions are properly formatted (dict of unit_id -> action arrays)
        for unit_id, action in action1.items():
            assert isinstance(action, np.ndarray)
            assert len(action) == 4  # [action_type, direction_x, direction_y, energy_boost]


class TestUtils:
    """Test utility functions and enums."""
    
    def test_tile_types(self):
        """Test TileType enum."""
        assert TileType.EMPTY.value == 0
        assert TileType.ENERGY_NODE.value == 1
        assert TileType.QUANTUM_BARRIER.value == 2
        assert TileType.ENTANGLEMENT_ZONE.value == 3
        assert TileType.DECOHERENCE_FIELD.value == 4
        assert TileType.QUANTUM_GATE.value == 5
        
    def test_unit_types(self):
        """Test UnitType enum."""
        assert UnitType.HARVESTER.value == 0
        assert UnitType.WARRIOR.value == 1
        assert UnitType.SCOUT.value == 2
        
    def test_action_types(self):
        """Test ActionType enum."""
        assert ActionType.MOVE.value == 0
        assert ActionType.QUANTUM_MOVE.value == 1
        assert ActionType.HARVEST.value == 2
        assert ActionType.ATTACK.value == 7
        assert ActionType.SPAWN_HARVESTER.value == 8
        assert ActionType.BUILD_QUANTUM_BARRIER.value == 15


if __name__ == "__main__":
    pytest.main([__file__])

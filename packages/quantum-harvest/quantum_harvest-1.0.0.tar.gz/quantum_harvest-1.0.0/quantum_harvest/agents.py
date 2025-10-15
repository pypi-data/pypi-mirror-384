"""
AI Agents for Quantum Harvest game.
"""

import numpy as np
from typing import Dict, Any


class BaseAgent:
    """Base class for all AI agents."""
    
    def __init__(self, player_id: int):
        """
        Initialize the agent.
        
        Args:
            player_id: ID of the player this agent controls (0 or 1)
        """
        self.player_id = player_id
        self.memory = {}
    
    def get_action(self, observation: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Get the next action for this agent.
        
        Args:
            observation: Current game observation
            
        Returns:
            action: Action array [unit_id, action_type, direction_x, direction_y, energy_boost]
        """
        raise NotImplementedError("Subclasses must implement get_action")
    
    def reset(self):
        """Reset the agent's state."""
        self.memory = {}
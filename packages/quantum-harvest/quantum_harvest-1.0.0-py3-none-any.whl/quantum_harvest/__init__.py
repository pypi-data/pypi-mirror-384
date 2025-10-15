"""
Quantum Harvest - A competitive 1v1 AI game combining quantum mechanics with strategic resource management.
"""

from .environment import QuantumHarvestEnv
from .agents import BaseAgent
from .visualizer import GameVisualizer
from .utils import TileType, UnitType, ActionType
from . import agent_v_agent_script
from . import agent_v_agent_config

__version__ = "1.0.0"
__author__ = "Tanaka Chiromo"

__all__ = [
    "QuantumHarvestEnv",
    "BaseAgent",
    "GameVisualizer",
    "TileType",
    "UnitType", 
    "ActionType",
    "agent_v_agent_script",
    "agent_v_agent_config"
] 
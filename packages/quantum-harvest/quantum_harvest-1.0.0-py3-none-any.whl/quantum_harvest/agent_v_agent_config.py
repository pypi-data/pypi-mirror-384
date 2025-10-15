"""
Configuration file for agent vs agent script
Contains all constants and settings used by agent_v_agent_script.py
"""

# Game Configuration
DEFAULT_MAP_SIZE = 16
DEFAULT_MAX_TURNS = 1000
DEFAULT_RENDER_MODE = "human"
DEFAULT_LOG_GAME = True

# Timing Configuration
DEFAULT_TURN_DELAY = 0.1  # seconds between turns
DEFAULT_POST_GAME_DELAY = 0.1  # seconds for post-game rendering loop

# Logging Configuration
ENABLE_MOVEMENT_LOGGING = False
ENABLE_PROGRESS_PRINTING = True
PROGRESS_PRINT_INTERVAL = 10  # print progress every N turns

# Display Configuration
ENABLE_VISUALIZATION_CONTROLS_HELP = True
ENABLE_WINDOW_FEATURES_HELP = True
ENABLE_REPLAY_INSTRUCTIONS = True

# Agent Configuration
DEFAULT_AGENT_PLAYER_0_CLASS = "Agent"
DEFAULT_AGENT_PLAYER_1_CLASS = "Agent"

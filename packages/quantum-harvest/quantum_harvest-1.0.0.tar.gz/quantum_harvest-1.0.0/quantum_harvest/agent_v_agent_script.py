#!/usr/bin/env python3
"""
Agent vs Agent script for Quantum Harvest
Allows running two arbitrary agent files against each other
"""
import argparse
import importlib.util
import random
import sys
import time
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from numpy.random import rand

from . import (
    QuantumHarvestEnv, 
    GameVisualizer
)
from .agent_v_agent_config import (
    DEFAULT_MAP_SIZE,
    DEFAULT_MAX_TURNS,
    DEFAULT_RENDER_MODE,
    DEFAULT_LOG_GAME,
    DEFAULT_TURN_DELAY,
    DEFAULT_POST_GAME_DELAY,
    ENABLE_MOVEMENT_LOGGING,
    ENABLE_PROGRESS_PRINTING,
    PROGRESS_PRINT_INTERVAL,
    ENABLE_VISUALIZATION_CONTROLS_HELP,
    ENABLE_WINDOW_FEATURES_HELP,
    ENABLE_REPLAY_INSTRUCTIONS,
    DEFAULT_AGENT_PLAYER_0_CLASS,
    DEFAULT_AGENT_PLAYER_1_CLASS
)


def load_agent_from_file(filepath, player_id):
    """
    Load an agent class from a Python file
    
    Args:
        filepath (str): Path to the Python file containing the agent
        player_id (int): Player ID (0 or 1) for the agent
    
    Returns:
        Agent instance
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Agent file not found: {filepath}")
    
    # Load the module
    spec = importlib.util.spec_from_file_location("agent_module", filepath)
    if spec is None:
        raise ImportError(f"Could not load module from {filepath}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Try to find the Agent class
    agent_class = None
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (isinstance(attr, type) and 
            hasattr(attr, 'get_action') and 
            hasattr(attr, 'reset') and
            attr_name in ['Agent', 'BaseAgent', 'AdvancedLogicalAgent']):
            agent_class = attr
            break
    
    if agent_class is None:
        # Try common agent class names
        for class_name in ['Agent', 'BaseAgent', 'AdvancedLogicalAgent']:
            if hasattr(module, class_name):
                agent_class = getattr(module, class_name)
                break
    
    if agent_class is None:
        raise ImportError(f"No suitable agent class found in {filepath}. "
                         "Agent class must have 'get_action' and 'reset' methods.")
    
    # Create agent instance
    try:
        agent = agent_class(player_id)
    except TypeError:
        # Try without player_id parameter
        try:
            agent = agent_class()
        except TypeError:
            raise ImportError(f"Could not instantiate agent class from {filepath}. "
                             "Agent class must accept either (player_id) or no parameters.")
    
    return agent


def log_unit_movements(turn, observation, actions, movement_log):
    """Log detailed unit movements for troubleshooting."""
    turn_data = {
        'turn': turn,
        'player_0_units': [],
        'player_1_units': [],
        'actions_sent': {},
        'energy': {
            'player_0': float(observation['player_energy'][0]),
            'player_1': float(observation['player_energy'][1])
        }
    }
    
    # Extract unit positions for both players
    units = observation['units']
    for unit in units:
        if len(unit) >= 6 and unit[0] != 0:  # Valid unit
            unit_id, player_id, unit_type, x, y, health = unit[:6]
            unit_info = {
                'unit_id': int(unit_id),
                'unit_type': int(unit_type),  # 0=Harvester, 1=Warrior, 2=Scout
                'position': [int(x), int(y)],
                'health': int(health)
            }
            
            if player_id == 0:
                turn_data['player_0_units'].append(unit_info)
            elif player_id == 1:
                turn_data['player_1_units'].append(unit_info)
    
    # Log actions sent
    for unit_key, action in actions.items():
        action_decoded = decode_action(action)
        # Handle both new format (p0_15) and legacy format (15)
        if isinstance(unit_key, str) and unit_key.startswith(('p0_', 'p1_')):
            # New format: "p0_15" -> store as "p0_15"
            turn_data['actions_sent'][unit_key] = {
                'raw_action': [int(x) for x in action],
                'decoded': action_decoded
            }
        else:
            # Legacy format: store as integer
            turn_data['actions_sent'][int(unit_key)] = {
                'raw_action': [int(x) for x in action],
                'decoded': action_decoded
            }
    
    movement_log.append(turn_data)


def decode_action(action):
    """Decode action array into human-readable format."""
    if len(action) < 4:
        return f"INVALID: {[int(x) for x in action]}"
    
    action_type = int(action[0])
    if action_type == 0:  # MOVE
        dir_x = int(action[1]) - 1
        dir_y = int(action[2]) - 1
        boost = int(action[3])
        return f"MOVE dir=({dir_x},{dir_y}) boost={boost}"
    elif action_type == 1:  # QUANTUM_MOVE
        return f"QUANTUM_MOVE"
    elif action_type == 2:  # HARVEST
        return f"HARVEST"
    elif action_type == 7:  # ATTACK
        dir_x = int(action[1]) - 1
        dir_y = int(action[2]) - 1
        return f"ATTACK dir=({dir_x},{dir_y})"
    elif action_type == 8:  # SPAWN_HARVESTER
        return f"SPAWN_HARVESTER"
    elif action_type == 9:  # SPAWN_WARRIOR
        return f"SPAWN_WARRIOR"
    elif action_type == 10:  # SPAWN_SCOUT
        return f"SPAWN_SCOUT"
    else:
        return f"ACTION_TYPE_{action_type}"


def main():
    parser = argparse.ArgumentParser(
        description="Run Quantum Harvest agent vs agent game",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m quantum_harvest.agent_v_agent_script --agent1 reasonable_agent.py --agent2 my_agent.py
  python -m quantum_harvest.agent_v_agent_script --agent1 agents/reasonable.py --agent2 agents/logical.py --map-size 20
  python -m quantum_harvest.agent_v_agent_script --agent1 reasonable_agent.py --agent2 my_agent.py --max-turns 500 --no-visualization
        """
    )
    
    parser.add_argument(
        '--agent1', 
        required=True,
        help='Path to Python file containing agent for player 1'
    )
    parser.add_argument(
        '--agent2', 
        required=True,
        help='Path to Python file containing agent for player 2'
    )
    parser.add_argument(
        '--map-size', 
        type=int, 
        default=DEFAULT_MAP_SIZE,
        help=f'Map size (default: {DEFAULT_MAP_SIZE})'
    )
    parser.add_argument(
        '--max-turns', 
        type=int, 
        default=DEFAULT_MAX_TURNS,
        help=f'Maximum number of turns (default: {DEFAULT_MAX_TURNS})'
    )
    parser.add_argument(
        '--no-visualization', 
        action='store_true',
        help='Disable visualization (run headless)'
    )
    parser.add_argument(
        '--no-logging', 
        action='store_true',
        help='Disable game logging'
    )
    parser.add_argument(
        '--turn-delay', 
        type=float, 
        default=DEFAULT_TURN_DELAY,
        help=f'Delay between turns in seconds (default: {DEFAULT_TURN_DELAY})'
    )
    parser.add_argument(
        '--no-help', 
        action='store_true',
        help='Disable help text output'
    )
    
    args = parser.parse_args()
    
    # Load agents
    try:
        print(f"Loading agent 1 from: {args.agent1}")
        agent1 = load_agent_from_file(args.agent1, 0)
        print(f"Loading agent 2 from: {args.agent2}")
        agent2 = load_agent_from_file(args.agent2, 1)
    except Exception as e:
        print(f"Error loading agents: {e}")
        sys.exit(1)
    
    # Configuration
    MAP_SIZE = args.map_size
    MAX_TURNS = args.max_turns
    render_mode = None if args.no_visualization else DEFAULT_RENDER_MODE
    log_game = not args.no_logging
    turn_delay = args.turn_delay
    
    if not args.no_help:
        print("=" * 60)
        print("Quantum Harvest - Agent vs Agent")
        print("=" * 60)
        print(f"Map size: {MAP_SIZE}x{MAP_SIZE}")
        print(f"Max turns: {MAX_TURNS}")
        print(f"Player 1: {args.agent1}")
        print(f"Player 2: {args.agent2}")
        print(f"Visualization: {'Enabled' if render_mode else 'Disabled'}")
        print(f"Game logging: {'Enabled' if log_game else 'Disabled'}")
        print("=" * 60)
        
        if render_mode and ENABLE_VISUALIZATION_CONTROLS_HELP:
            print("VISUALIZATION CONTROLS:")
            print("  +/-        : Zoom in/out")
            print("  WASD/Arrows: Pan around map")
            print("  R          : Reset zoom and pan")
            print("  M          : Toggle resize mode")
            print("  Drag corners: Manually resize window")
            print("  ESC        : Exit game")
            print("=" * 60)
        
        if render_mode and ENABLE_WINDOW_FEATURES_HELP:
            print("WINDOW FEATURES:")
            print("• Auto-scaling: Automatically fits your screen")
            print("• Manual resize: Drag window corners/edges to resize")
            print("• Resize modes: Proportional (M key) or Fixed Panel")
            print("• Zoom/Pan: Navigate large maps with +/- and WASD")
            print("=" * 60)
    
    # Create environment
    env = QuantumHarvestEnv(
        map_size=MAP_SIZE, 
        max_turns=MAX_TURNS, 
        render_mode=render_mode, 
        log_game=log_game
    )
    
    if log_game:
        print(f"Game logging enabled. Log will be saved to: {env.get_log_file_path()}")
        print("=" * 60)
    
    # Initialize movement logging
    movement_log = []
    if ENABLE_MOVEMENT_LOGGING:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"unit_movements_{timestamp}.json"
        print(f"Unit movement logging enabled. Log will be saved to: {log_filename}")
    
    # Reset environment
    observation, info = env.reset()
    agent1.reset()
    agent2.reset()
    
    done = False
    turn = 0
    
    while not done and turn < MAX_TURNS:
        # Get actions - each agent gets their own player-specific observation
        player1_obs = env.get_player_observation(0)
        player2_obs = env.get_player_observation(1)
        
        action1 = agent1.get_action(player1_obs)
        action2 = agent2.get_action(player2_obs)
        
        # Execute actions for both players in a single step
        # Combine actions from both players using player-specific keys to avoid conflicts
        combined_actions = {}
        
        # Add player 1 actions with player prefix to avoid ID conflicts
        for unit_id, action in action1.items():
            # Use player-specific key format: "p0_unitid" for player 0
            combined_actions[f"p0_{unit_id}"] = action
        
        # Add player 2 actions with player prefix
        for unit_id, action in action2.items():
            # Use player-specific key format: "p1_unitid" for player 1  
            combined_actions[f"p1_{unit_id}"] = action
        
        # Log unit movements before step
        if ENABLE_MOVEMENT_LOGGING:
            log_unit_movements(turn + 1, observation, combined_actions, movement_log)
        
        # Execute all actions in one step
        observation, reward, terminated, truncated, info = env.step(combined_actions)
        
        # Render the game state
        if render_mode and not env.render():
            print("Game window closed by user")
            break
        
        turn += 1
        
        # Print progress
        if ENABLE_PROGRESS_PRINTING and turn % PROGRESS_PRINT_INTERVAL == 0:
            print(f"Turn {turn}: P1 Energy={observation['player_energy'][0]:.0f}, "
                  f"P2 Energy={observation['player_energy'][1]:.0f}")
        
        done = terminated or truncated
        if turn_delay > 0:
            time.sleep(turn_delay)
    
    print(f"\nGame finished after {turn} turns!")
    
    # Save movement log
    if ENABLE_MOVEMENT_LOGGING:
        try:
            with open(log_filename, 'w') as f:
                json.dump(movement_log, f, indent=2)
            print(f"Unit movement log saved to: {log_filename}")
        except Exception as e:
            print(f"Failed to save movement log: {e}")
    
    # Determine winner based on final state
    if terminated:
        winner = info.get('winner', None)
        if winner is not None:
            print(f"Player {winner + 1} wins!")
        else:
            print("It's a tie!")
    else:
        # Turn limit reached, check energy
        p1_energy = observation['player_energy'][0]
        p2_energy = observation['player_energy'][1]
        print(f"Final scores: P1={p1_energy:.1f}, P2={p2_energy:.1f}")
        
        if p1_energy > p2_energy:
            print("Player 1 wins!")
        elif p2_energy > p1_energy:
            print("Player 2 wins!")
        else:
            print("It's a tie!")
    
    # Keep the pygame window open until user closes it (if visualization enabled)
    if render_mode:
        print("\n" + "="*60)
        print("GAME OVER - Window will stay open until you close it")
        print("Press ESC or click the X button to close the window")
        print("="*60)
        
        # Show replay instructions
        if ENABLE_REPLAY_INSTRUCTIONS and log_game:
            log_path = env.get_log_file_path()
            if log_path:
                print(f"\nREPLAY INSTRUCTIONS:")
                print(f"To replay this game, run:")
                print(f"  python replay_visualizer.py {log_path}")
                print("="*60)
        
        # Post-game loop - keep rendering until user closes window
        while True:
            # Continue rendering the final game state
            if not env.render():
                print("Game window closed by user")
                break
            time.sleep(DEFAULT_POST_GAME_DELAY)
    
    # Close environment
    env.close()


if __name__ == "__main__":
    main()

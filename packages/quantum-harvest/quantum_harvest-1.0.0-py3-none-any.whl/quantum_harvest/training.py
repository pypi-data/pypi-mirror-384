"""
Training utilities for Quantum Harvest agents.
"""

import numpy as np
import random
from typing import Dict, List, Tuple, Optional, Any
from .environment import QuantumHarvestEnv
from .agents import RandomAgent, GreedyAgent, StrategicAgent, PPOAgent
from .visualizer import GameVisualizer


def train_agent(
    agent_type: str = "ppo",
    num_episodes: int = 1000,
    learning_rate: float = 0.001,
    save_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Train an agent using reinforcement learning.
    
    Args:
        agent_type: Type of agent to train ("ppo", "random", "greedy", "strategic")
        num_episodes: Number of training episodes
        learning_rate: Learning rate for training
        save_path: Path to save the trained model
        
    Returns:
        Training statistics
    """
    print(f"Training {agent_type} agent for {num_episodes} episodes...")
    
    # Create environment
    env = QuantumHarvestEnv(map_size=12, max_turns=1000)
    
    # Create agent
    if agent_type == "ppo":
        agent = PPOAgent(0)
    elif agent_type == "random":
        agent = RandomAgent(0)
    elif agent_type == "greedy":
        agent = GreedyAgent(0)
    elif agent_type == "strategic":
        agent = StrategicAgent(0)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    # Create opponent (random agent for training)
    opponent = RandomAgent(1)
    
    # Training statistics
    stats = {
        'episodes': [],
        'rewards': [],
        'wins': 0,
        'losses': 0,
        'ties': 0
    }
    
    for episode in range(num_episodes):
        # Reset environment
        observation, info = env.reset()
        agent.reset()
        opponent.reset()
        
        total_reward = 0
        done = False
        turn = 0
        
        while not done and turn < 200:
            # Get actions
            action1 = agent.get_action(observation)
            action2 = opponent.get_action(observation)
            
            # Execute actions
            observation, reward1, terminated, truncated, info = env.step(action1)
            total_reward += reward1
            
            if not terminated:
                observation, reward2, terminated, truncated, info = env.step(action2)
            
            done = terminated or truncated
            turn += 1
        
        # Record episode results
        stats['episodes'].append(episode)
        stats['rewards'].append(total_reward)
        
        # Check winner
        if terminated:
            winner = info.get('winner', None)
            if winner == 0:
                stats['wins'] += 1
            elif winner == 1:
                stats['losses'] += 1
            else:
                stats['ties'] += 1
        else:
            # Turn limit reached, check energy
            if observation['player_energy'][0] > observation['player_energy'][1]:
                stats['wins'] += 1
            elif observation['player_energy'][1] > observation['player_energy'][0]:
                stats['losses'] += 1
            else:
                stats['ties'] += 1
        
        # Print progress
        if episode % 100 == 0:
            win_rate = stats['wins'] / (episode + 1)
            avg_reward = np.mean(stats['rewards'][-100:]) if stats['rewards'] else 0
            print(f"Episode {episode}: Win Rate: {win_rate:.2f}, Avg Reward: {avg_reward:.2f}")
    
    # Save model if requested
    if save_path and hasattr(agent, 'save_model'):
        agent.save_model(save_path)
        print(f"Model saved to {save_path}")
    
    # Final statistics
    final_win_rate = stats['wins'] / num_episodes
    final_avg_reward = np.mean(stats['rewards'])
    
    print(f"\nTraining completed!")
    print(f"Final Win Rate: {final_win_rate:.2f}")
    print(f"Final Average Reward: {final_avg_reward:.2f}")
    print(f"Wins: {stats['wins']}, Losses: {stats['losses']}, Ties: {stats['ties']}")
    
    return stats


def evaluate_agent(
    agent_type: str = "ppo",
    model_path: Optional[str] = None,
    num_games: int = 100,
    opponents: List[str] = None
) -> Dict[str, Any]:
    """
    Evaluate an agent against different opponents.
    
    Args:
        agent_type: Type of agent to evaluate
        model_path: Path to load the trained model
        num_games: Number of games to play against each opponent
        opponents: List of opponent types to test against
        
    Returns:
        Evaluation statistics
    """
    if opponents is None:
        opponents = ["random", "greedy", "strategic"]
    
    print(f"Evaluating {agent_type} agent against {opponents}...")
    
    # Create environment
    env = QuantumHarvestEnv(map_size=12, max_turns=1000)
    
    # Create agent
    if agent_type == "ppo":
        agent = PPOAgent(0, model_path)
    elif agent_type == "random":
        agent = RandomAgent(0)
    elif agent_type == "greedy":
        agent = GreedyAgent(0)
    elif agent_type == "strategic":
        agent = StrategicAgent(0)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    results = {}
    
    for opponent_type in opponents:
        print(f"\nTesting against {opponent_type} agent...")
        
        # Create opponent
        if opponent_type == "random":
            opponent = RandomAgent(1)
        elif opponent_type == "greedy":
            opponent = GreedyAgent(1)
        elif opponent_type == "strategic":
            opponent = StrategicAgent(1)
        else:
            raise ValueError(f"Unknown opponent type: {opponent_type}")
        
        wins = 0
        losses = 0
        ties = 0
        total_rewards = []
        
        for game in range(num_games):
            # Reset environment
            observation, info = env.reset()
            agent.reset()
            opponent.reset()
            
            total_reward = 0
            done = False
            turn = 0
            
            while not done and turn < 200:
                # Get actions
                action1 = agent.get_action(observation)
                action2 = opponent.get_action(observation)
                
                # Execute actions
                observation, reward1, terminated, truncated, info = env.step(action1)
                total_reward += reward1
                
                if not terminated:
                    observation, reward2, terminated, truncated, info = env.step(action2)
                
                done = terminated or truncated
                turn += 1
            
            # Record game results
            total_rewards.append(total_reward)
            
            if terminated:
                winner = info.get('winner', None)
                if winner == 0:
                    wins += 1
                elif winner == 1:
                    losses += 1
                else:
                    ties += 1
            else:
                # Turn limit reached, check energy
                if observation['player_energy'][0] > observation['player_energy'][1]:
                    wins += 1
                elif observation['player_energy'][1] > observation['player_energy'][0]:
                    losses += 1
                else:
                    ties += 1
        
        # Calculate statistics
        win_rate = wins / num_games
        avg_reward = np.mean(total_rewards)
        
        results[opponent_type] = {
            'wins': wins,
            'losses': losses,
            'ties': ties,
            'win_rate': win_rate,
            'avg_reward': avg_reward
        }
        
        print(f"Win Rate: {win_rate:.2f}, Avg Reward: {avg_reward:.2f}")
    
    return results


def run_tournament(
    agents: List[str] = None,
    num_games: int = 10,
    visualize: bool = False
) -> Dict[str, Any]:
    """
    Run a tournament between multiple agents.
    
    Args:
        agents: List of agent types to include in tournament
        num_games: Number of games between each pair of agents
        visualize: Whether to visualize games
        
    Returns:
        Tournament results
    """
    if agents is None:
        agents = ["random", "greedy", "strategic"]
    
    print(f"Running tournament with agents: {agents}")
    print(f"Each pair plays {num_games} games")
    
    # Create environment
    env = QuantumHarvestEnv(map_size=12, max_turns=1000)
    
    # Create visualizer if requested
    visualizer = None
    if visualize:
        visualizer = GameVisualizer(map_size=12)
    
    # Tournament results
    results = {agent: {'wins': 0, 'losses': 0, 'ties': 0} for agent in agents}
    
    # Play all pairs
    for i, agent1_type in enumerate(agents):
        for j, agent2_type in enumerate(agents):
            if i >= j:  # Skip self-play and duplicate pairs
                continue
            
            print(f"\n{agent1_type} vs {agent2_type}")
            
            # Create agents
            if agent1_type == "random":
                agent1 = RandomAgent(0)
            elif agent1_type == "greedy":
                agent1 = GreedyAgent(0)
            elif agent1_type == "strategic":
                agent1 = StrategicAgent(0)
            else:
                raise ValueError(f"Unknown agent type: {agent1_type}")
            
            if agent2_type == "random":
                agent2 = RandomAgent(1)
            elif agent2_type == "greedy":
                agent2 = GreedyAgent(1)
            elif agent2_type == "strategic":
                agent2 = StrategicAgent(1)
            else:
                raise ValueError(f"Unknown agent type: {agent2_type}")
            
            # Play games
            for game in range(num_games):
                # Reset environment
                observation, info = env.reset()
                agent1.reset()
                agent2.reset()
                
                done = False
                turn = 0
                
                while not done and turn < 200:
                    # Get actions
                    action1 = agent1.get_action(observation)
                    action2 = agent2.get_action(observation)
                    
                    # Execute actions
                    observation, reward1, terminated, truncated, info = env.step(action1)
                    if not terminated:
                        observation, reward2, terminated, truncated, info = env.step(action2)
                    
                    # Visualize if requested
                    if visualizer:
                        if not visualizer.render(observation, info):
                            print("Visualization closed by user")
                            break
                    
                    done = terminated or truncated
                    turn += 1
                
                # Record results
                if terminated:
                    winner = info.get('winner', None)
                    if winner == 0:
                        results[agent1_type]['wins'] += 1
                        results[agent2_type]['losses'] += 1
                    elif winner == 1:
                        results[agent2_type]['wins'] += 1
                        results[agent1_type]['losses'] += 1
                    else:
                        results[agent1_type]['ties'] += 1
                        results[agent2_type]['ties'] += 1
                else:
                    # Turn limit reached, check energy
                    if observation['player_energy'][0] > observation['player_energy'][1]:
                        results[agent1_type]['wins'] += 1
                        results[agent2_type]['losses'] += 1
                    elif observation['player_energy'][1] > observation['player_energy'][0]:
                        results[agent2_type]['wins'] += 1
                        results[agent1_type]['losses'] += 1
                    else:
                        results[agent1_type]['ties'] += 1
                        results[agent2_type]['ties'] += 1
    
    # Clean up
    if visualizer:
        visualizer.close()
    
    # Calculate final statistics
    total_games = {}
    win_rates = {}
    
    for agent in agents:
        total = results[agent]['wins'] + results[agent]['losses'] + results[agent]['ties']
        total_games[agent] = total
        win_rates[agent] = results[agent]['wins'] / total if total > 0 else 0
    
    # Print results
    print("\n" + "="*50)
    print("TOURNAMENT RESULTS")
    print("="*50)
    
    for agent in agents:
        stats = results[agent]
        win_rate = win_rates[agent]
        print(f"{agent.upper()}:")
        print(f"  Wins: {stats['wins']}, Losses: {stats['losses']}, Ties: {stats['ties']}")
        print(f"  Win Rate: {win_rate:.2f}")
        print()
    
    # Find winner
    winner = max(win_rates, key=win_rates.get)
    print(f"Tournament Winner: {winner.upper()} (Win Rate: {win_rates[winner]:.2f})")
    
    return {
        'results': results,
        'win_rates': win_rates,
        'winner': winner
    } 
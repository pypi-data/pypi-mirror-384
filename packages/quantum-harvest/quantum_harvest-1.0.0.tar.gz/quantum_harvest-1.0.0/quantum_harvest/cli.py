"""
Command-line interface for Quantum Harvest.
"""

import argparse
import sys
import os


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Quantum Harvest - AI Strategy Game",
        epilog="For more information, visit: https://github.com/tanaka-chiromo/quantum-harvest"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Agent vs Agent command
    play_parser = subparsers.add_parser("play", help="Run agent vs agent game")
    play_parser.add_argument(
        "--agent1", 
        required=True,
        help="Path to Python file containing Agent class for player 1"
    )
    play_parser.add_argument(
        "--agent2", 
        required=True,
        help="Path to Python file containing Agent class for player 2"
    )
    play_parser.add_argument(
        "--map-size", 
        type=int, 
        default=12,
        help="Size of the game map (default: 12)"
    )
    play_parser.add_argument(
        "--max-turns", 
        type=int, 
        default=1000,
        help="Maximum number of turns (default: 1000)"
    )
    play_parser.add_argument(
        "--no-visualization", 
        action="store_true",
        help="Disable pygame visualization"
    )
    play_parser.add_argument(
        "--no-logging", 
        action="store_true",
        help="Disable game state logging"
    )
    play_parser.add_argument(
        "--turn-delay", 
        type=float, 
        default=0.1,
        help="Delay between turns in seconds (default: 0.1)"
    )
    
    # Replay visualizer command
    replay_parser = subparsers.add_parser("replay", help="View game replay")
    replay_parser.add_argument(
        "replay_file",
        nargs="?",
        default=None,
        help="Path to replay file (JSON or compressed .json.gz)"
    )
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show package information")
    
    args = parser.parse_args()
    
    if args.command == "play":
        # Import here to avoid loading pygame/numpy if just showing help
        from quantum_harvest import agent_v_agent_script
        
        # Build arguments for agent_v_agent_script
        script_args = [
            "--agent1", args.agent1,
            "--agent2", args.agent2,
            "--map-size", str(args.map_size),
            "--max-turns", str(args.max_turns),
            "--turn-delay", str(args.turn_delay),
        ]
        
        if args.no_visualization:
            script_args.append("--no-visualization")
        if args.no_logging:
            script_args.append("--no-logging")
        
        # Call the agent vs agent script
        sys.argv = ["quantum-harvest"] + script_args
        agent_v_agent_script.main()
        
    elif args.command == "replay":
        # Import here to avoid loading dependencies if just showing help
        from quantum_harvest import run_replay_visualizer
        
        if args.replay_file:
            sys.argv = ["quantum-harvest", args.replay_file]
        else:
            sys.argv = ["quantum-harvest"]
        
        run_replay_visualizer.main()
        
    elif args.command == "version":
        from quantum_harvest import __version__, __author__
        print(f"Quantum Harvest version {__version__}")
        print(f"Author: {__author__}")
        
    elif args.command == "info":
        from quantum_harvest import __version__, __author__
        print("=" * 60)
        print("Quantum Harvest - AI Strategy Game")
        print("=" * 60)
        print(f"Version: {__version__}")
        print(f"Author: {__author__}")
        print(f"License: CC BY-NC 4.0")
        print(f"GitHub: https://github.com/tanaka-chiromo/quantum-harvest")
        print()
        print("A competitive 1v1 AI strategy game combining quantum mechanics")
        print("with strategic resource management and territory control.")
        print()
        print("Usage:")
        print("  quantum-harvest play --agent1 <file> --agent2 <file>")
        print("  quantum-harvest replay <file>")
        print("  quantum-harvest info")
        print()
        print("For detailed documentation, see:")
        print("  https://github.com/tanaka-chiromo/quantum-harvest/blob/main/README.md")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

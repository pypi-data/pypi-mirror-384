#!/usr/bin/env python3
"""
Quantum Harvest HTML Replay Visualizer Launcher

This script launches the HTML-based replay visualizer in the default web browser.
It works cross-platform on Windows, Linux, and macOS.

Usage:
    python run_replay_visualizer.py [replay_file_path]

If no replay file is provided, the visualizer will open with a file upload interface.
If a replay file is provided, it will be automatically loaded.
"""

import sys
import os
import webbrowser
import urllib.parse
from pathlib import Path


def get_visualizer_path():
    """Get the path to the HTML visualizer file."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    visualizer_path = script_dir / "quantum_harvest_replay_visualizer.html"
    
    # If not found in script directory, try looking in the current working directory
    if not visualizer_path.exists():
        cwd_path = Path.cwd() / "quantum_harvest" / "quantum_harvest_replay_visualizer.html"
        if cwd_path.exists():
            visualizer_path = cwd_path
        else:
            raise FileNotFoundError(f"HTML visualizer not found at: {visualizer_path} or {cwd_path}")
    
    return visualizer_path


def launch_visualizer(replay_file_path=None):
    """
    Launch the HTML replay visualizer in the default web browser.
    
    Args:
        replay_file_path: Optional path to a replay file to load automatically
    """
    try:
        visualizer_path = get_visualizer_path()
        
        # Convert to file:// URL
        file_url = visualizer_path.as_uri()
        
        # If a replay file is provided, add it as a URL parameter
        if replay_file_path:
            replay_path = Path(replay_file_path)
            if not replay_path.exists():
                print(f"Warning: Replay file not found: {replay_file_path}")
                print("Opening visualizer without auto-loading replay file.")
            else:
                # Convert replay file to absolute path and encode as URL parameter
                replay_url = replay_path.resolve().as_uri()
                file_url += f"?replay_url={urllib.parse.quote(replay_url)}"
        
        print("=" * 60)
        print("Quantum Harvest - HTML Replay Visualizer")
        print("=" * 60)
        print(f"Opening visualizer: {visualizer_path}")
        if replay_file_path:
            print(f"Auto-loading replay: {replay_file_path}")
        print("=" * 60)
        
        # Open in default web browser
        webbrowser.open(file_url)
        
        print("Visualizer opened in your default web browser.")
        print("\nControls:")
        print("  - Upload replay files by clicking the upload area or dragging files")
        print("  - Use keyboard shortcuts: SPACE (play/pause), arrows (step), +/- (speed)")
        print("  - Click progress bar to jump to specific frames")
        print("  - Supports both .json and .json.gz replay files")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching visualizer: {e}")
        sys.exit(1)


def main():
    """Main function."""
    replay_file_path = None
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        replay_file_path = sys.argv[1]
        
        # Validate the replay file path
        if not os.path.exists(replay_file_path):
            print(f"Error: Replay file not found: {replay_file_path}")
            print("Usage: python run_replay_visualizer.py [replay_file_path]")
            sys.exit(1)
        
        # Check file extension
        if not replay_file_path.lower().endswith(('.json', '.json.gz')):
            print(f"Warning: File doesn't have .json or .json.gz extension: {replay_file_path}")
            print("The visualizer may not be able to load this file.")
    
    elif len(sys.argv) > 2:
        print("Usage: python run_replay_visualizer.py [replay_file_path]")
        print("\nExamples:")
        print("  python run_replay_visualizer.py")
        print("  python run_replay_visualizer.py game_logs/replay.json")
        print("  python run_replay_visualizer.py compressed_replay.json.gz")
        sys.exit(1)
    
    # Launch the visualizer
    launch_visualizer(replay_file_path)


if __name__ == "__main__":
    main()

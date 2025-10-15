# Quantum Harvest HTML Replay Visualizer

A cross-platform HTML-based replay visualizer for Quantum Harvest games that runs in your web browser.

## Features

- 🌐 **Web-based**: Runs in any modern web browser
- 📁 **File Upload**: Drag & drop or click to upload replay files
- 🎮 **Playback Controls**: Play/pause, step forward/backward, speed control
- 📊 **Real-time Stats**: Energy, territory control, unit counts
- 🎯 **Combat Animations**: Visual attack effects and damage indicators
- 🗺️ **Fog of War**: Team-specific exploration visualization
- 📈 **Progress Bar**: Click to jump to any frame
- ⌨️ **Keyboard Shortcuts**: Full keyboard control support
- 📦 **Compression Support**: Handles both `.json` and `.json.gz` files

## Quick Start

### Method 1: Python Launcher (Recommended)
```bash
# From the quantum-harvest_old directory
python3 quantum_harvest/run_replay_visualizer.py

# With auto-loading a replay file
python3 quantum_harvest/run_replay_visualizer.py replay1.json
```

### Method 2: Direct Browser Access
1. Open `quantum_harvest/quantum_harvest_replay_visualizer.html` in your browser
2. Upload a replay file using the interface

## Controls

### Mouse Controls
- **Upload Area**: Click or drag files to upload
- **Progress Bar**: Click to jump to specific frames
- **Buttons**: Play/Pause, Step Back/Forward, Speed Control, Reset

### Keyboard Shortcuts
- `SPACE` - Play/Pause
- `←` `→` - Step Back/Forward
- `+` `-` - Increase/Decrease Speed
- `HOME` - Go to Start
- `END` - Go to End
- `ESC` - Exit (when running via Python launcher)

## File Support

- **JSON Files**: Standard uncompressed replay files (`.json`)
- **Compressed Files**: Gzip-compressed replay files (`.json.gz`)
- **Auto-detection**: Automatically detects and handles both formats

## Visual Elements

### Map Tiles
- 🟡 **Energy Nodes**: Yellow tiles with energy levels
- ⬜ **Barriers**: Gray quantum barriers
- 🔵 **Entanglement Zones**: Cyan quantum entanglement
- 🟣 **Decoherence Fields**: Magenta decoherence zones
- 🟠 **Quantum Gates**: Orange quantum gates

### Units
- 🔴 **Player 1 Units**: Red circles with unit symbols (H=Harvester, W=Warrior, S=Scout)
- 🔵 **Player 2 Units**: Blue circles with unit symbols
- 🔢 **Stacked Units**: Numbers show multiple units at same position
- ❤️ **Health Bars**: Green/yellow/red health indicators

### Fog of War
- 🌫️ **Unexplored**: Dark tiles for unexplored areas
- 🔴 **P1 Only**: Light red tint for Player 1 explored areas
- 🔵 **P2 Only**: Light blue tint for Player 2 explored areas
- ⚪ **Both Teams**: Normal colors for mutually explored areas

## Technical Details

- **Browser Compatibility**: Modern browsers with Canvas support
- **Performance**: Optimized for smooth 60fps playback
- **Memory Efficient**: Handles large replay files without issues
- **Cross-platform**: Works on Windows, macOS, and Linux

## Troubleshooting

### Common Issues
1. **File won't load**: Check file format (must be `.json` or `.json.gz`)
2. **Browser compatibility**: Use Chrome, Firefox, Safari, or Edge
3. **Large files**: Allow time for loading large replay files
4. **Python launcher**: Ensure Python 3 is installed and in PATH

### File Locations
- **HTML Visualizer**: `quantum_harvest/quantum_harvest_replay_visualizer.html`
- **Python Launcher**: `quantum_harvest/run_replay_visualizer.py`
- **Replay Files**: Usually in `game_logs/` or `users_files/*/replays/`

## Examples

```bash
# Basic usage
python3 quantum_harvest/run_replay_visualizer.py

# Load specific replay
python3 quantum_harvest/run_replay_visualizer.py game_logs/match_001.json

# Load compressed replay
python3 quantum_harvest/run_replay_visualizer.py compressed_replay.json.gz
```

---

*For more information about Quantum Harvest, see the main project documentation.*

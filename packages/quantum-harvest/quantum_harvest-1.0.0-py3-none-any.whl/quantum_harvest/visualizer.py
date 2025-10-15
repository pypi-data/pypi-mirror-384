"""
Game visualization using Pygame.
"""

import pygame
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from .utils import TileType, UnitType, ActionType
from . import game_config


class GameVisualizer:
    """Pygame-based visualizer for Quantum Harvest game."""
    
    def __init__(self, map_size: int = 12, cell_size: int = None, max_screen_percentage: float = 0.85):
        """
        Initialize the visualizer.
        
        Args:
            map_size: Size of the game map
            cell_size: Size of each cell in pixels (if None, auto-calculated)
            max_screen_percentage: Maximum percentage of screen to use (0.0-1.0)
        """
        self.map_size = map_size
        self.right_panel_width = 250  # Width of the right info panel
        
        # Initialize pygame to get screen info
        pygame.init()
        
        # Get screen dimensions
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h
        
        # Calculate optimal cell size if not provided
        if cell_size is None:
            # Calculate available space (accounting for window decorations and taskbar)
            available_width = int(screen_width * max_screen_percentage) - self.right_panel_width
            available_height = int(screen_height * max_screen_percentage)
            
            # Calculate maximum cell size that fits
            max_cell_width = available_width // map_size
            max_cell_height = available_height // map_size
            
            # Use the smaller dimension and ensure minimum cell size
            cell_size = max(min(max_cell_width, max_cell_height), 20)  # Minimum 20px per cell
            
            print(f"Auto-calculated cell size: {cell_size}px for {map_size}x{map_size} map")
            print(f"Screen: {screen_width}x{screen_height}, Available: {available_width}x{available_height}")
        
        self.cell_size = cell_size
        self.map_width = map_size * cell_size
        self.map_height = map_size * cell_size
        self.width = self.map_width + self.right_panel_width
        self.height = self.map_height
        
        print(f"Window size: {self.width}x{self.height}")
        
        # Ensure window doesn't exceed screen size
        if self.width > screen_width or self.height > screen_height:
            print(f"Warning: Window size ({self.width}x{self.height}) exceeds screen ({screen_width}x{screen_height})")
            print("Consider using a smaller map size or enabling zoom mode.")
        
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption(f"Quantum Harvest - Map: {map_size}x{map_size}, Cell: {cell_size}px")
        
        # Colors
        self.colors = {
            'background': (20, 20, 40),
            'grid': (40, 40, 60),
            'empty': (30, 30, 50),
            'fog_of_war': (10, 10, 20),  # Dark for unexplored areas
            'energy_node': (255, 255, 0),  # Yellow
            'quantum_barrier': (100, 100, 100),  # Gray
            'entanglement_zone': (0, 255, 255),  # Cyan
            'decoherence_field': (255, 0, 255),  # Magenta
            'quantum_gate': (255, 165, 0),  # Orange
            'player1': (255, 0, 0),  # Red
            'player2': (0, 0, 255),  # Blue
            'text': (255, 255, 255),  # White
            'ui_background': (40, 40, 80),
            'projectile': (255, 255, 0),  # Yellow projectile
            'damage_text': (255, 100, 100),  # Red damage numbers
            'screen_shake': (255, 0, 0),  # Red for screen shake effect
            'team_fog_0': (80, 40, 40),  # Light red tint for Player 0 explored only
            'team_fog_1': (40, 40, 80)   # Light blue tint for Player 1 explored only
        }
        
        # Font
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.tiny_font = pygame.font.Font(None, 12)
        
        # Unit symbols
        self.unit_symbols = {
            UnitType.HARVESTER.value: 'H',
            UnitType.WARRIOR.value: 'W',
            UnitType.SCOUT.value: 'S'
        }
        
        # Animation state
        self.animation_frame = 0
        self.animation_speed = 2  # Frames per animation step
        self.screen_shake = 0  # Screen shake counter
        self.damage_texts = []  # List of damage text animations
        
        # Zoom and pan state
        self.zoom_level = 1.0
        self.zoom_step = 0.1
        self.min_zoom = 0.3
        self.max_zoom = 3.0
        self.camera_x = 0  # Camera offset x
        self.camera_y = 0  # Camera offset y
        self.pan_speed = 20  # Pixels per key press
        
        # Effective cell size after zoom
        self.effective_cell_size = self.cell_size
        
        # Window resize state
        self.original_cell_size = cell_size  # Store original for resize calculations
        self.min_window_width = 400  # Minimum window width
        self.min_window_height = 300  # Minimum window height
        self.resize_mode = "proportional"  # "proportional" or "fixed_panel"
    
    def render(self, observation: Dict[str, np.ndarray], info: Dict[str, Any]) -> bool:
        """
        Render the current game state.
        
        Args:
            observation: Current game observation
            info: Additional game information
            
        Returns:
            True if window is still open, False if closed
        """
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.VIDEORESIZE:
                # Handle window resize
                self._handle_window_resize(event.w, event.h)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:  # Zoom in
                    self._zoom_in()
                elif event.key == pygame.K_MINUS:  # Zoom out
                    self._zoom_out()
                elif event.key == pygame.K_r:  # Reset zoom and pan
                    self._reset_view()
                elif event.key == pygame.K_UP or event.key == pygame.K_w:  # Pan up
                    self.camera_y += self.pan_speed
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:  # Pan down
                    self.camera_y -= self.pan_speed
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:  # Pan left
                    self.camera_x += self.pan_speed
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:  # Pan right
                    self.camera_x -= self.pan_speed
                elif event.key == pygame.K_m:  # Toggle resize mode
                    self._toggle_resize_mode()
        
        # Update animation frame
        self.animation_frame += 1
        
        # Update effective cell size based on zoom
        self.effective_cell_size = int(self.cell_size * self.zoom_level)
        
        # Clear screen
        self.screen.fill(self.colors['background'])
        
        # Apply screen shake if active
        shake_offset = (0, 0)
        if self.screen_shake > 0:
            shake_offset = (
                np.random.randint(-3, 4) if self.screen_shake > 0 else 0,
                np.random.randint(-3, 4) if self.screen_shake > 0 else 0
            )
            self.screen_shake -= 1
        
        # Apply camera offset and shake
        total_offset = (self.camera_x + shake_offset[0], self.camera_y + shake_offset[1])
        
        # Draw map with fog of war (show both players' exploration)
        self._draw_map_with_fog(observation, info, total_offset)
        
        # Draw units
        self._draw_units(observation['units'], total_offset)
        
        # Draw combat animations
        self._draw_combat_animations(info.get('combat_events', []), total_offset)
        
        # Draw damage text animations
        self._draw_damage_texts(total_offset)
        
        # Draw UI
        self._draw_ui(observation, info)
        
        # Update display
        pygame.display.flip()
        
        return True
    
    def _draw_map_with_fog(self, observation: Dict[str, np.ndarray], info: Dict[str, Any], shake_offset: Tuple[int, int] = (0, 0)):
        """Draw the game map with team-specific fog of war (matching HTML implementation)."""
        # Get the full map and fog maps
        full_map = observation['map']
        fog_maps = observation.get('fog_maps', None)
        
        # If no fog maps, fall back to full map
        if fog_maps is None:
            self._draw_map(full_map, info, shake_offset)
            return
        
        # Create team-specific exploration maps (matching HTML implementation)
        team_exploration = [
            np.zeros((self.map_size, self.map_size), dtype=bool),  # Player 0
            np.zeros((self.map_size, self.map_size), dtype=bool)   # Player 1
        ]
        
        # Track exploration for each team separately
        for player_id in range(2):
            fog_map = fog_maps[player_id]
            # Mark explored tiles (not -1)
            explored = fog_map != -1
            team_exploration[player_id] = explored
        
        # Get energy node information
        energy_nodes = info.get('energy_nodes', [])
        energy_values = info.get('energy_values', [])
        
        # Draw the map with team-based fog of war (matching HTML implementation)
        for x in range(self.map_size):
            for y in range(self.map_size):
                player0_explored = team_exploration[0][x, y]
                player1_explored = team_exploration[1][x, y]
                
                # Calculate tile rect
                rect = pygame.Rect(
                    y * self.effective_cell_size + shake_offset[0], 
                    x * self.effective_cell_size + shake_offset[1], 
                    self.effective_cell_size, 
                    self.effective_cell_size
                )
                
                if player0_explored and player1_explored:
                    # Both teams explored - show actual tile
                    tile_type = full_map[x, y]
                    
                    # Special handling for energy nodes
                    if tile_type == TileType.ENERGY_NODE.value:
                        self._draw_energy_node_tile(rect, (x, y), energy_nodes, energy_values, exploration_status='both')
                    else:
                        color = self._get_tile_color(tile_type)
                        pygame.draw.rect(self.screen, color, rect)
                        pygame.draw.rect(self.screen, self.colors['grid'], rect, 1)
                        
                elif player0_explored:
                    # Only Player 0 explored - show with light red tint
                    self._draw_team_fog_tile(full_map[x, y], rect, (x, y), energy_nodes, energy_values, team_id=0)
                    
                elif player1_explored:
                    # Only Player 1 explored - show with light blue tint
                    self._draw_team_fog_tile(full_map[x, y], rect, (x, y), energy_nodes, energy_values, team_id=1)
                    
                else:
                    # Neither team explored - show fog of war
                    color = self.colors['fog_of_war']
                    pygame.draw.rect(self.screen, color, rect)
                    pygame.draw.rect(self.screen, self.colors['grid'], rect, 1)
    
    def _draw_map(self, map_data: np.ndarray, info: Dict[str, Any], shake_offset: Tuple[int, int] = (0, 0)):
        """Draw the game map without fog of war."""
        # Get energy node information
        energy_nodes = info.get('energy_nodes', [])
        energy_values = info.get('energy_values', [])
        
        # Get entanglement zone information
        entanglement_zones = info.get('entanglement_zones', [])
        entanglement_zone_power = info.get('entanglement_zone_power', [])
        
        for x in range(self.map_size):
            for y in range(self.map_size):
                tile_type = map_data[x, y]
                
                rect = pygame.Rect(
                    y * self.effective_cell_size + shake_offset[0],  # No offset needed - map is on the left
                    x * self.effective_cell_size + shake_offset[1],
                    self.effective_cell_size,
                    self.effective_cell_size
                )
                
                # Special handling for energy nodes
                if tile_type == TileType.ENERGY_NODE.value:
                    self._draw_energy_node_tile(rect, (x, y), energy_nodes, energy_values)
                # Special handling for entanglement zones with depletion effects
                elif tile_type == TileType.ENTANGLEMENT_ZONE.value:
                    self._draw_entanglement_zone_tile(rect, (x, y), entanglement_zones, entanglement_zone_power)
                else:
                    color = self._get_tile_color(tile_type)
                    pygame.draw.rect(self.screen, color, rect)
                    pygame.draw.rect(self.screen, self.colors['grid'], rect, 1)
    
    def _get_tile_color(self, tile_type: int) -> Tuple[int, int, int]:
        """Get color for a tile type."""
        if tile_type == TileType.EMPTY.value:
            return self.colors['empty']
        elif tile_type == TileType.ENERGY_NODE.value:
            return self.colors['energy_node']
        elif tile_type == TileType.QUANTUM_BARRIER.value:
            return self.colors['quantum_barrier']
        elif tile_type == TileType.ENTANGLEMENT_ZONE.value:
            return self.colors['entanglement_zone']
        elif tile_type == TileType.DECOHERENCE_FIELD.value:
            return self.colors['decoherence_field']
        elif tile_type == TileType.QUANTUM_GATE.value:
            return self.colors['quantum_gate']
        else:
            return self.colors['empty']
    
    def _draw_energy_node_tile(self, rect: pygame.Rect, position: Tuple[int, int], energy_nodes: List, energy_values: List, exploration_status: str = 'both'):
        """
        Draw an energy node tile with proportional energy fill and team-specific exploration coloring.
        
        Args:
            rect: The rectangle to draw the tile in
            position: The (x, y) position of the tile
            energy_nodes: List of energy node positions
            energy_values: List of energy values corresponding to each node
            exploration_status: 'both', 0, or 1 for team-specific exploration coloring
        """
        # Find the energy value for this position
        energy_percentage = 0.0
        current_energy = 0.0
        try:
            node_index = energy_nodes.index(position)
            current_energy = energy_values[node_index]
            
            # Calculate percentage based on energy tiers using config values
            max_energy = game_config.ENERGY_NODE_MAX_VALUE
            min_energy = game_config.ENERGY_NODE_MIN_VALUE
            energy_range = max_energy - min_energy
            
            # Create energy tiers based on config values
            tier_3 = min_energy + (energy_range * 0.75)  # 75% of range
            tier_2 = min_energy + (energy_range * 0.5)   # 50% of range
            tier_1 = min_energy + (energy_range * 0.25)  # 25% of range
            
            if current_energy >= tier_3:
                # High energy: 75-100%
                energy_percentage = 0.75 + (current_energy - tier_3) / (max_energy - tier_3) * 0.25
            elif current_energy >= tier_2:
                # Medium energy: 50-75%
                energy_percentage = 0.5 + (current_energy - tier_2) / (tier_3 - tier_2) * 0.25
            elif current_energy >= tier_1:
                # Low energy: 25-50%
                energy_percentage = 0.25 + (current_energy - tier_1) / (tier_2 - tier_1) * 0.25
            elif current_energy > 0:
                # Very low energy: 0-25%
                energy_percentage = current_energy / tier_1 * 0.25
            else:
                # No energy
                energy_percentage = 0.0
                
            energy_percentage = max(0.0, min(1.0, energy_percentage))
            
        except (ValueError, IndexError):
            # Node not found or invalid index, treat as empty
            energy_percentage = 0.0
        
        # Determine background color based on exploration status (matching HTML implementation)
        if exploration_status == 'both':
            base_color = self.colors['empty']  # Both teams explored - normal empty color
        elif exploration_status == 0:
            base_color = self.colors['team_fog_0']  # Only Player 0 explored - light red
        elif exploration_status == 1:
            base_color = self.colors['team_fog_1']  # Only Player 1 explored - light blue
        else:
            base_color = self.colors['fog_of_war']  # Unexplored - dark fog
        
        # Yellow energy color
        energy_color = self.colors['energy_node']  # Yellow
        
        # Draw base tile
        pygame.draw.rect(self.screen, base_color, rect)
        
        # Draw energy fill based on percentage
        if energy_percentage > 0.0:
            # Calculate the height of the energy fill (from bottom up)
            fill_height = int(rect.height * energy_percentage)
            
            # Create energy fill rectangle (from bottom up like a liquid)
            energy_rect = pygame.Rect(
                rect.x,
                rect.y + (rect.height - fill_height),  # Start from bottom
                rect.width,
                fill_height
            )
            
            # Draw the energy fill
            pygame.draw.rect(self.screen, energy_color, energy_rect)
            
            # Add a subtle gradient effect for more visual appeal
            if fill_height > 2:  # Only add gradient if there's enough space
                # Create lighter yellow for top part of energy
                lighter_yellow = (
                    min(255, energy_color[0] + 30),
                    min(255, energy_color[1] + 30),
                    min(255, energy_color[2] + 20)
                )
                
                # Draw gradient lines
                gradient_height = min(fill_height // 3, 8)  # Top third or max 8 pixels
                for i in range(gradient_height):
                    alpha = 1.0 - (i / gradient_height)
                    gradient_color = (
                        int(energy_color[0] + (lighter_yellow[0] - energy_color[0]) * alpha),
                        int(energy_color[1] + (lighter_yellow[1] - energy_color[1]) * alpha),
                        int(energy_color[2] + (lighter_yellow[2] - energy_color[2]) * alpha)
                    )
                    
                    gradient_rect = pygame.Rect(
                        rect.x,
                        rect.y + (rect.height - fill_height) + i,
                        rect.width,
                        1
                    )
                    pygame.draw.rect(self.screen, gradient_color, gradient_rect)
        
        # Draw grid lines
        pygame.draw.rect(self.screen, self.colors['grid'], rect, 1)
        
        # Energy value text removed - clean visual without numbers
    
    def _draw_team_fog_tile(self, tile_type: int, rect: pygame.Rect, position: Tuple[int, int], 
                           energy_nodes: List, energy_values: List, team_id: int):
        """
        Draw a tile with team-specific fog coloring (matching HTML implementation).
        
        Args:
            tile_type: The type of tile to draw
            rect: The rectangle to draw the tile in
            position: The (x, y) position of the tile
            energy_nodes: List of energy node positions
            energy_values: List of energy values corresponding to each node
            team_id: 0 for Player 0 (red tint), 1 for Player 1 (blue tint)
        """
        # Get team fog color (matching HTML implementation)
        team_fog_color = self.colors['team_fog_0'] if team_id == 0 else self.colors['team_fog_1']
        
        # Draw base tile with team fog color
        pygame.draw.rect(self.screen, team_fog_color, rect)
        
        # Draw tile content with reduced opacity to show it's partially fogged
        # Note: Pygame doesn't have built-in alpha blending for individual rects,
        # so we'll create a semi-transparent surface for the tile content
        if tile_type == TileType.ENERGY_NODE.value:
            # Special handling for energy nodes with team fog
            self._draw_energy_node_tile(rect, position, energy_nodes, energy_values, exploration_status=team_id)
        else:
            # For other tile types, draw with reduced opacity effect
            # Create a semi-transparent surface
            tile_surface = pygame.Surface((rect.width - 4, rect.height - 4), pygame.SRCALPHA)
            
            # Get the tile color
            tile_color = self._get_tile_color(tile_type)
            
            # Apply reduced opacity (matching HTML's 0.6 alpha)
            alpha_color = (*tile_color, int(255 * 0.6))
            tile_surface.fill(alpha_color)
            
            # Blit the semi-transparent tile content
            self.screen.blit(tile_surface, (rect.x + 2, rect.y + 2))
        
        # Draw grid lines
        pygame.draw.rect(self.screen, self.colors['grid'], rect, 1)
    
    def _draw_entanglement_zone_tile(self, rect: pygame.Rect, position: Tuple[int, int], 
                                   entanglement_zones: List, entanglement_zone_power: List):
        """
        Draw an entanglement zone tile with depletion effects.
        
        Args:
            rect: The rectangle to draw the tile in
            position: The (x, y) position of the tile
            entanglement_zones: List of entanglement zone positions
            entanglement_zone_power: List of power values for each zone
        """
        # Find this zone's power level
        zone_power = 200  # Default full power
        if position in entanglement_zones:
            zone_index = entanglement_zones.index(position)
            if zone_index < len(entanglement_zone_power):
                zone_power = entanglement_zone_power[zone_index]
        
        # Calculate power percentage (0.0 to 1.0)
        power_percentage = max(0.0, min(1.0, zone_power / 200.0))
        
        # Base entanglement zone color (cyan)
        base_color = self.colors['entanglement_zone']
        
        # Fade to darker color as power depletes
        depleted_color = (0, 100, 100)  # Dark cyan
        
        # Interpolate between full and depleted colors
        current_color = (
            int(depleted_color[0] + (base_color[0] - depleted_color[0]) * power_percentage),
            int(depleted_color[1] + (base_color[1] - depleted_color[1]) * power_percentage),
            int(depleted_color[2] + (base_color[2] - depleted_color[2]) * power_percentage)
        )
        
        # Draw base tile
        pygame.draw.rect(self.screen, current_color, rect)
        
        # Draw power level indicator (similar to energy nodes)
        if power_percentage > 0:
            # Draw power fill from bottom up
            fill_height = int(rect.height * power_percentage)
            fill_rect = pygame.Rect(
                rect.x,
                rect.y + rect.height - fill_height,
                rect.width,
                fill_height
            )
            
            # Brighter color for the fill
            fill_color = (
                min(255, current_color[0] + 50),
                min(255, current_color[1] + 50),
                min(255, current_color[2] + 50)
            )
            pygame.draw.rect(self.screen, fill_color, fill_rect)
        
        # Draw grid lines
        pygame.draw.rect(self.screen, self.colors['grid'], rect, 1)
        
        # Draw power text for debugging (small)
        if zone_power < 200:
            power_text = f"{int(zone_power)}"
            text_surface = self.tiny_font.render(power_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)
    
    def _draw_units(self, units_array: np.ndarray, shake_offset: Tuple[int, int] = (0, 0)):
        """Draw units on the map with stack indicators."""
        # First, count units at each position
        position_counts = {}
        position_units = {}
        
        for i in range(units_array.shape[0]):
            # Handle both old (6-field) and new (8-field) format for compatibility
            if units_array.shape[1] >= 8:
                unit_id, player_id, unit_type, x, y, health, is_boosted, boost_attacks = units_array[i]
            else:
                unit_id, player_id, unit_type, x, y, health = units_array[i]
                is_boosted, boost_attacks = 0, 0
            
            # Skip invalid units
            if unit_id == 0 and player_id == 0 and unit_type == 0 and x == 0 and y == 0:
                continue
            
            pos = (x, y)
            if pos not in position_counts:
                position_counts[pos] = 0
                position_units[pos] = []
            
            position_counts[pos] += 1
            position_units[pos].append((unit_id, player_id, unit_type, health, is_boosted, boost_attacks))
        
        # Now draw units with stack indicators
        for pos, units_at_pos in position_units.items():
            x, y = pos
            stack_count = position_counts[pos]
            
            # Get the first unit's info for drawing
            if len(units_at_pos[0]) >= 6:  # New format with boost info
                unit_id, player_id, unit_type, health, is_boosted, boost_attacks = units_at_pos[0]
            else:  # Old format compatibility
                unit_id, player_id, unit_type, health = units_at_pos[0]
                is_boosted, boost_attacks = 0, 0
            
            # Check if there are units from both teams at this position
            player_ids_at_pos = set(unit_info[1] for unit_info in units_at_pos)
            has_mixed_teams = len(player_ids_at_pos) > 1
            
            # Get unit color - use mixed color if both teams present
            if has_mixed_teams:
                color = (128, 128, 255)  # Purple for mixed teams
            else:
                color = self.colors['player1'] if player_id == 0 else self.colors['player2']
            
            # Draw unit circle (no offset needed - map is on the left)
            center_x = y * self.effective_cell_size + self.effective_cell_size // 2 + shake_offset[0]
            center_y = x * self.effective_cell_size + self.effective_cell_size // 2 + shake_offset[1]
            radius = max(3, self.effective_cell_size // 3)  # Ensure minimum radius
            
            # Draw boosted warrior visual effect (glowing outline)
            if is_boosted and unit_type == 1:  # UnitType.WARRIOR = 1
                # Draw glowing effect with team color
                glow_color = (255, 255, 100) if player_id == 0 else (255, 100, 255)  # Yellow for P1, Magenta for P2
                for glow_radius in range(radius + 6, radius + 2, -1):
                    alpha = 60 - (glow_radius - radius) * 10  # Fade effect
                    glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surface, (*glow_color, alpha), (glow_radius, glow_radius), glow_radius)
                    self.screen.blit(glow_surface, (center_x - glow_radius, center_y - glow_radius))
            
            pygame.draw.circle(self.screen, color, (center_x, center_y), radius)
            pygame.draw.circle(self.screen, self.colors['text'], (center_x, center_y), radius, 2)
            
            # Draw unit symbol(s) - show all unit types on this tile
            unit_types_on_tile = set()
            for unit_info in units_at_pos:
                if len(unit_info) >= 3:  # Ensure we have unit_type
                    unit_types_on_tile.add(unit_info[2])  # unit_type is at index 2
            
            # Create combined symbol string (sorted for consistency)
            symbols = []
            for unit_type in sorted(unit_types_on_tile):
                symbol = self.unit_symbols.get(unit_type, '?')
                symbols.append(symbol)
            
            combined_symbol = ''.join(symbols)
            text = self.small_font.render(combined_symbol, True, self.colors['text'])
            text_rect = text.get_rect(center=(center_x, center_y))
            self.screen.blit(text, text_rect)
            
            # Draw boost indicator for boosted warriors
            if is_boosted and unit_type == 1:  # UnitType.WARRIOR = 1
                boost_text = f"{boost_attacks}"
                boost_surface = self.tiny_font.render(boost_text, True, (255, 255, 255))
                boost_rect = boost_surface.get_rect(center=(center_x + radius + 8, center_y - radius - 8))
                pygame.draw.circle(self.screen, (255, 0, 0), boost_rect.center, 8)
                self.screen.blit(boost_surface, boost_rect)
            
            # Draw stack indicator if multiple units
            if stack_count > 1:
                # Draw stack count badge with mixed team indicator
                if has_mixed_teams:
                    stack_bg_color = (200, 200, 255)  # Light purple for mixed teams
                    # Show team composition (e.g., "2+1" for 2 from team 1, 1 from team 2)
                    team_counts = {}
                    for unit_info in units_at_pos:
                        team_id = unit_info[1]
                        team_counts[team_id] = team_counts.get(team_id, 0) + 1
                    stack_text_str = "+".join(str(team_counts[tid]) for tid in sorted(team_counts.keys()))
                else:
                    stack_bg_color = (255, 255, 255) if player_id == 0 else (200, 200, 255)
                    stack_text_str = str(stack_count)
                
                stack_text_color = (0, 0, 0)  # Black text for better visibility
                stack_text = self.small_font.render(stack_text_str, True, stack_text_color)
                
                # Position the stack indicator in the top-right corner of the cell
                stack_x = center_x + radius - 5
                stack_y = center_y - radius + 5
                
                # Draw background circle for stack indicator
                stack_radius = 12
                pygame.draw.circle(self.screen, stack_bg_color, (stack_x, stack_y), stack_radius)
                pygame.draw.circle(self.screen, (100, 100, 100), (stack_x, stack_y), stack_radius, 2)  # Darker border
                
                # Draw stack count text
                stack_text_rect = stack_text.get_rect(center=(stack_x, stack_y))
                self.screen.blit(stack_text, stack_text_rect)
            
            # Draw health bar
            health_percentage = health / 100.0
            health_width = int(self.effective_cell_size * 0.8 * health_percentage)
            health_rect = pygame.Rect(
                center_x - self.effective_cell_size // 2 + 2,
                center_y + radius + 2,
                health_width,
                max(2, int(4 * self.zoom_level))  # Scale health bar height with zoom
            )
            health_color = (0, 255, 0) if health_percentage > 0.5 else (255, 255, 0) if health_percentage > 0.25 else (255, 0, 0)
            pygame.draw.rect(self.screen, health_color, health_rect)
    
    def _draw_ui(self, observation: Dict[str, np.ndarray], info: Dict[str, Any]):
        """Draw UI elements in the right panel."""
        # Draw right panel background
        panel_rect = pygame.Rect(self.map_width, 0, self.right_panel_width, self.height)
        pygame.draw.rect(self.screen, self.colors['ui_background'], panel_rect)
        
        # Add a border to separate map from panel
        pygame.draw.line(self.screen, self.colors['grid'], 
                        (self.map_width, 0), 
                        (self.map_width, self.height), 2)
        
        # Starting position for content (offset by map width)
        panel_x = self.map_width + 10
        y_pos = 10
        
        # Game title
        title_text = self.font.render("Quantum Harvest", True, self.colors['text'])
        self.screen.blit(title_text, (panel_x, y_pos))
        y_pos += 35
        
        # Turn information
        turn = observation['turn'][0]
        turn_text = self.small_font.render(f"Turn: {turn}", True, self.colors['text'])
        self.screen.blit(turn_text, (panel_x, y_pos))
        y_pos += 25
        
        # Player stats section
        stats_header = self.small_font.render("PLAYER STATS", True, self.colors['text'])
        self.screen.blit(stats_header, (panel_x, y_pos))
        y_pos += 20
        
        # Player 1 stats
        player1_energy = observation['player_energy'][0]
        energy_text1 = self.small_font.render(f"P1 Energy: {player1_energy:.0f}", True, self.colors['player1'])
        self.screen.blit(energy_text1, (panel_x, y_pos))
        y_pos += 15
        
        # Player 2 stats
        player2_energy = observation['player_energy'][1]
        energy_text2 = self.small_font.render(f"P2 Energy: {player2_energy:.0f}", True, self.colors['player2'])
        self.screen.blit(energy_text2, (panel_x, y_pos))
        y_pos += 20
        
        # Territory control
        territory1 = observation['territory_control'][0]
        territory2 = observation['territory_control'][1]
        
        territory_text1 = self.small_font.render(f"P1 Territory: {territory1:.1%}", True, self.colors['player1'])
        territory_text2 = self.small_font.render(f"P2 Territory: {territory2:.1%}", True, self.colors['player2'])
        
        self.screen.blit(territory_text1, (panel_x, y_pos))
        y_pos += 15
        self.screen.blit(territory_text2, (panel_x, y_pos))
        y_pos += 20
        
        # Unit counts
        units = info.get('units', [])
        player1_units = [u for u in units if u[1] == 0]
        player2_units = [u for u in units if u[1] == 1]
        
        unit_text1 = self.small_font.render(f"P1 Units: {len(player1_units)}", True, self.colors['player1'])
        unit_text2 = self.small_font.render(f"P2 Units: {len(player2_units)}", True, self.colors['player2'])
        
        self.screen.blit(unit_text1, (panel_x, y_pos))
        y_pos += 15
        self.screen.blit(unit_text2, (panel_x, y_pos))
        y_pos += 20
        
        # Exploration metrics
        exploration_percentages = observation.get('exploration_percentage', [0.0, 0.0])
        player1_exploration = exploration_percentages[0]
        player2_exploration = exploration_percentages[1]
        
        exploration_text1 = self.small_font.render(f"P1 Explored: {player1_exploration:.1%}", True, self.colors['player1'])
        exploration_text2 = self.small_font.render(f"P2 Explored: {player2_exploration:.1%}", True, self.colors['player2'])
        
        self.screen.blit(exploration_text1, (panel_x, y_pos))
        y_pos += 15
        self.screen.blit(exploration_text2, (panel_x, y_pos))
        y_pos += 30
        
        # Unit legend section
        unit_legend_header = self.small_font.render("UNIT TYPES", True, self.colors['text'])
        self.screen.blit(unit_legend_header, (panel_x, y_pos))
        y_pos += 20
        
        unit_legend_text = self.small_font.render("H = Harvester", True, self.colors['text'])
        self.screen.blit(unit_legend_text, (panel_x, y_pos))
        y_pos += 15
        
        unit_legend_text = self.small_font.render("W = Warrior", True, self.colors['text'])
        self.screen.blit(unit_legend_text, (panel_x, y_pos))
        y_pos += 15
        
        unit_legend_text = self.small_font.render("S = Scout", True, self.colors['text'])
        self.screen.blit(unit_legend_text, (panel_x, y_pos))
        y_pos += 15
        
        # Stack indicator explanation
        stack_legend_text = self.small_font.render("Numbers = Stacked units", True, self.colors['text'])
        self.screen.blit(stack_legend_text, (panel_x, y_pos))
        y_pos += 15
        
        # Stacked symbols explanation
        stacked_symbols_text = self.small_font.render("SH = Scout+Harvester", True, self.colors['text'])
        self.screen.blit(stacked_symbols_text, (panel_x, y_pos))
        y_pos += 15
        
        stacked_symbols_text2 = self.small_font.render("SHW = All unit types", True, self.colors['text'])
        self.screen.blit(stacked_symbols_text2, (panel_x, y_pos))
        y_pos += 15
        
        # Tile legend section
        tile_legend_header = self.small_font.render("TILE TYPES", True, self.colors['text'])
        self.screen.blit(tile_legend_header, (panel_x, y_pos))
        y_pos += 20
        
        # Define tile legend items with their colors and names (matching HTML implementation)
        tile_items = [
            (self.colors['empty'], "Empty"),
            (self.colors['energy_node'], "Energy Node"),
            (self.colors['quantum_barrier'], "Barrier"),
            (self.colors['entanglement_zone'], "Entanglement"),
            (self.colors['decoherence_field'], "Decoherence"),
            (self.colors['quantum_gate'], "Quantum Gate"),
            (self.colors['empty'], "Both Teams Explored"),
            (self.colors['team_fog_0'], "P1 Explored Only"),
            (self.colors['team_fog_1'], "P2 Explored Only"),
            (self.colors['fog_of_war'], "Unexplored")
        ]
        
        # Draw tile legend items
        for i, (color, name) in enumerate(tile_items):
            # Draw colored square
            square_rect = pygame.Rect(panel_x, y_pos, 12, 12)
            pygame.draw.rect(self.screen, color, square_rect)
            pygame.draw.rect(self.screen, self.colors['grid'], square_rect, 1)
            
            # Draw label
            label_text = self.small_font.render(name, True, self.colors['text'])
            self.screen.blit(label_text, (panel_x + 16, y_pos - 2))
            y_pos += 16
        
        # Controls at the bottom
        y_pos = self.height - 60
        controls_text = self.small_font.render("Controls:", True, self.colors['text'])
        self.screen.blit(controls_text, (panel_x, y_pos))
        y_pos += 15
        
        controls_text = self.small_font.render("+/- : Zoom in/out", True, self.colors['text'])
        self.screen.blit(controls_text, (panel_x, y_pos))
        y_pos += 15
        
        controls_text = self.small_font.render("WASD/Arrows: Pan", True, self.colors['text'])
        self.screen.blit(controls_text, (panel_x, y_pos))
        y_pos += 15
        
        controls_text = self.small_font.render("R: Reset view", True, self.colors['text'])
        self.screen.blit(controls_text, (panel_x, y_pos))
        y_pos += 15
        
        controls_text = self.small_font.render("M: Resize mode", True, self.colors['text'])
        self.screen.blit(controls_text, (panel_x, y_pos))
        y_pos += 15
        
        controls_text = self.small_font.render("Drag corners: Resize", True, self.colors['text'])
        self.screen.blit(controls_text, (panel_x, y_pos))
        y_pos += 15
        
        controls_text = self.small_font.render("ESC: Exit", True, self.colors['text'])
        self.screen.blit(controls_text, (panel_x, y_pos))
        
        # Display zoom level and resize info
        y_pos = self.height - 120
        zoom_text = self.small_font.render(f"Zoom: {self.zoom_level:.1f}x", True, self.colors['text'])
        self.screen.blit(zoom_text, (panel_x, y_pos))
        y_pos += 15
        
        resize_text = self.small_font.render(f"Resize: {self._get_resize_info()}", True, self.colors['text'])
        self.screen.blit(resize_text, (panel_x, y_pos))
        y_pos += 15
        
        cell_text = self.small_font.render(f"Cell: {self.cell_size}px", True, self.colors['text'])
        self.screen.blit(cell_text, (panel_x, y_pos))
    
    def close(self):
        """Close the visualizer."""
        pygame.quit()
    
    def get_screen(self) -> pygame.Surface:
        """Get the pygame screen surface."""
        return self.screen
    
    def _draw_combat_animations(self, combat_events: List[Dict], shake_offset: Tuple[int, int] = (0, 0)):
        """Draw combat animations including projectiles and effects."""
        for event in combat_events:
            if event['type'] == 'attack':
                self._draw_attack_animation(event, shake_offset)
    
    def _draw_attack_animation(self, event: Dict, shake_offset: Tuple[int, int] = (0, 0)):
        """Draw a single attack animation with support for long-range attacks."""
        attacker_pos = event['attacker_pos']
        target_pos = event['target_pos']
        damage = event['damage']
        frame = event.get('frame', 0)
        is_long_range = event.get('is_long_range', False)
        attacker_player = event.get('attacker_player', 0)
        
        # Calculate positions (no offset needed - map is on the left)
        attacker_center = (
            attacker_pos[1] * self.effective_cell_size + self.effective_cell_size // 2 + shake_offset[0],
            attacker_pos[0] * self.effective_cell_size + self.effective_cell_size // 2 + shake_offset[1]
        )
        target_center = (
            target_pos[1] * self.effective_cell_size + self.effective_cell_size // 2 + shake_offset[0],
            target_pos[0] * self.effective_cell_size + self.effective_cell_size // 2 + shake_offset[1]
        )
        
        # Get team color for attack lines
        team_color = (255, 100, 0) if attacker_player == 0 else (0, 100, 255)  # Red for P1, Blue for P2
        
        # Draw attack line for all attacks (both adjacent and long-range)
        if frame <= 15:
            line_alpha = max(0, 255 - frame * 15)  # Fade out over time
            line_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
            line_color = (*team_color, line_alpha)
            
            # Draw attack line
            pygame.draw.line(line_surface, line_color, attacker_center, target_center, 4)
            self.screen.blit(line_surface, (0, 0))
        
        # Animation phases: 0-10 projectile, 11-15 impact, 16-20 damage text
        if frame <= 10:
            # Draw projectile
            progress = frame / 10.0
            projectile_pos = (
                int(attacker_center[0] + (target_center[0] - attacker_center[0]) * progress),
                int(attacker_center[1] + (target_center[1] - attacker_center[1]) * progress)
            )
            
            # Draw projectile with trail effect
            for i in range(3):
                trail_progress = max(0, progress - i * 0.1)
                trail_pos = (
                    int(attacker_center[0] + (target_center[0] - attacker_center[0]) * trail_progress),
                    int(attacker_center[1] + (target_center[1] - attacker_center[1]) * trail_progress)
                )
                trail_alpha = int(255 * (1 - i * 0.3))
                trail_color = (*self.colors['projectile'], trail_alpha)
                
                # Create a surface for the trail
                trail_surface = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(trail_surface, trail_color, (4, 4), 4 - i)
                self.screen.blit(trail_surface, (trail_pos[0] - 4, trail_pos[1] - 4))
            
            # Main projectile
            pygame.draw.circle(self.screen, self.colors['projectile'], projectile_pos, 6)
            pygame.draw.circle(self.screen, (255, 255, 255), projectile_pos, 3)
            
        elif frame <= 15:
            # Impact effect
            impact_radius = (frame - 10) * 3
            impact_color = (255, 255, 0, 255 - (frame - 10) * 50)
            
            # Create impact surface
            impact_surface = pygame.Surface((impact_radius * 2, impact_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(impact_surface, impact_color, (impact_radius, impact_radius), impact_radius)
            self.screen.blit(impact_surface, (target_center[0] - impact_radius, target_center[1] - impact_radius))
            
            # Trigger screen shake on impact
            if frame == 11:
                self.screen_shake = 5
                
        elif frame <= 25:
            # Damage text animation
            damage_text = f"-{int(damage)}"
            text_color = self.colors['damage_text']
            
            # Calculate text position (floating up)
            text_y_offset = (frame - 16) * 2
            text_pos = (target_center[0], target_center[1] - 20 - text_y_offset)
            
            # Render damage text
            damage_surface = self.font.render(damage_text, True, text_color)
            text_rect = damage_surface.get_rect(center=text_pos)
            self.screen.blit(damage_surface, text_rect)
            
            # Add glow effect
            glow_surface = self.font.render(damage_text, True, (255, 255, 255))
            glow_rect = glow_surface.get_rect(center=(text_pos[0] + 1, text_pos[1] + 1))
            self.screen.blit(glow_surface, glow_rect)
        
        # Update frame counter
        event['frame'] = frame + 1
    
    def _draw_damage_texts(self, shake_offset: Tuple[int, int] = (0, 0)):
        """Draw persistent damage text animations."""
        # Update and draw damage texts
        for damage_text in self.damage_texts[:]:
            damage_text['frame'] += 1
            
            if damage_text['frame'] > 30:  # Remove after 30 frames
                self.damage_texts.remove(damage_text)
                continue
            
            # Calculate position
            text_pos = (
                damage_text['x'] + shake_offset[0],
                damage_text['y'] - damage_text['frame'] * 2 + shake_offset[1]
            )
            
            # Calculate alpha for fade effect
            alpha = max(0, 255 - (damage_text['frame'] * 8))
            text_color = (*self.colors['damage_text'], alpha)
            
            # Render text
            text_surface = self.font.render(damage_text['text'], True, text_color)
            text_rect = text_surface.get_rect(center=text_pos)
            self.screen.blit(text_surface, text_rect)
    
    def add_damage_text(self, x: int, y: int, damage: float):
        """Add a new damage text animation."""
        self.damage_texts.append({
            'x': x,
            'y': y,
            'text': f"-{int(damage)}",
            'frame': 0
        })
    
    def _zoom_in(self):
        """Zoom in by increasing zoom level."""
        old_zoom = self.zoom_level
        self.zoom_level = min(self.max_zoom, self.zoom_level + self.zoom_step)
        
        # Adjust camera to keep view centered
        zoom_ratio = self.zoom_level / old_zoom
        center_x = self.map_width // 2
        center_y = self.map_height // 2
        
        self.camera_x = (self.camera_x - center_x) * zoom_ratio + center_x
        self.camera_y = (self.camera_y - center_y) * zoom_ratio + center_y
    
    def _zoom_out(self):
        """Zoom out by decreasing zoom level."""
        old_zoom = self.zoom_level
        self.zoom_level = max(self.min_zoom, self.zoom_level - self.zoom_step)
        
        # Adjust camera to keep view centered
        zoom_ratio = self.zoom_level / old_zoom
        center_x = self.map_width // 2
        center_y = self.map_height // 2
        
        self.camera_x = (self.camera_x - center_x) * zoom_ratio + center_x
        self.camera_y = (self.camera_y - center_y) * zoom_ratio + center_y
    
    def _reset_view(self):
        """Reset zoom and pan to default values."""
        self.zoom_level = 1.0
        self.camera_x = 0
        self.camera_y = 0
    
    def _handle_window_resize(self, new_width: int, new_height: int):
        """Handle window resize events."""
        # Enforce minimum window size
        new_width = max(new_width, self.min_window_width)
        new_height = max(new_height, self.min_window_height)
        
        # Calculate new dimensions based on resize mode
        if self.resize_mode == "proportional":
            # Maintain proportional scaling - adjust cell size to fit
            available_width = new_width - self.right_panel_width
            available_height = new_height
            
            # Calculate new cell size that fits the map
            max_cell_width = available_width // self.map_size if self.map_size > 0 else 20
            max_cell_height = available_height // self.map_size if self.map_size > 0 else 20
            
            # Use the smaller dimension and ensure minimum cell size
            new_cell_size = max(min(max_cell_width, max_cell_height), 10)
            
            # Update cell size and dimensions
            self.cell_size = new_cell_size
            self.map_width = self.map_size * self.cell_size
            self.map_height = self.map_size * self.cell_size
            
        elif self.resize_mode == "fixed_panel":
            # Keep panel width fixed, allow map area to resize freely
            self.map_width = new_width - self.right_panel_width
            self.map_height = new_height
            
            # Calculate cell size based on available space
            if self.map_size > 0:
                new_cell_size = max(min(self.map_width // self.map_size, self.map_height // self.map_size), 10)
                self.cell_size = new_cell_size
        
        # Update window dimensions
        self.width = new_width
        self.height = new_height
        
        # Update the pygame display
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        
        print(f"Window resized to {self.width}x{self.height}, cell size: {self.cell_size}px")
    
    def _toggle_resize_mode(self):
        """Toggle between different resize modes."""
        if self.resize_mode == "proportional":
            self.resize_mode = "fixed_panel"
            print("Resize mode: Fixed panel - map area stretches freely")
        else:
            self.resize_mode = "proportional"
            print("Resize mode: Proportional - maintains map aspect ratio")
    
    def _get_resize_info(self) -> str:
        """Get current resize mode information."""
        if self.resize_mode == "proportional":
            return "Proportional"
        else:
            return "Fixed Panel" 
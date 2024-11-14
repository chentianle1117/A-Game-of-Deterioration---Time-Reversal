# mini_map.py
from cmu_graphics import *
import numpy as np
from dataclasses import dataclass

@dataclass
class MinimapCache:
    """Cache for minimap data to improve performance"""
    terrain_colors: np.ndarray = None
    terrain_updated: float = 0
    viewport: tuple = None
    player_pos: tuple = None

class MiniMap:
    def __init__(self, window_width, window_height, world_width, world_height,
                 cell_width, cell_height, color_map):
        # Window properties
        self.window_width = window_width
        self.window_height = window_height
        
        # World properties
        self.world_width = world_width
        self.world_height = world_height
        self.cell_width = cell_width
        self.cell_height = cell_height
        
        # Minimap dimensions and position
        self.size = {
            'width': 160,
            'height': 120,
            'margin': 10
        }
        self.position = {
            'x': window_width - self.size['width'] - self.size['margin'],
            'y': self.size['margin']
        }
        
        # Visual properties
        self.style = {
            'border': {
                'color': 'black',
                'width': 2
            },
            'player': {
                'color': 'red',
                'size': 3
            },
            'viewport': {
                'color': 'white',
                'width': 1,
                'opacity': 50
            }
        }
        
        # Performance settings
        self.resolution = {
            'scale': 4,  # Draw every 4th cell
            'rows': (world_height + 3) // 4,
            'cols': (world_width + 3) // 4
        }
        
        # Calculate scaling factors
        self.scale = {
            'x': self.size['width'] / world_width,
            'y': self.size['height'] / world_height
        }
        
        # Store color mapping
        self.colors = color_map
        
        # Initialize cache
        self.cache = MinimapCache()
        
        # Precalculate static values
        self._precalculate()

    def _precalculate(self):
        """Precalculate static values for rendering"""
        # Calculate cell dimensions
        self.cell_dims = {
            'width': self.size['width'] / self.world_width,
            'height': self.size['height'] / self.world_height
        }
        
        # Calculate scaled cell dimensions
        self.scaled_cell = {
            'width': self.cell_dims['width'] * self.resolution['scale'] + 1,
            'height': self.cell_dims['height'] * self.resolution['scale'] + 1
        }

    def update_grid(self, grid):
        """Update minimap with new grid data"""
        if grid is None:
            return
            
        # Create color array with reduced resolution
        rows = self.resolution['rows']
        cols = self.resolution['cols']
        colors = np.empty((rows, cols), dtype='U20')
        
        try:
            # Sample grid at reduced resolution
            for i in range(rows):
                for j in range(cols):
                    grid_i = min(i * self.resolution['scale'], len(grid) - 1)
                    grid_j = min(j * self.resolution['scale'], len(grid[0]) - 1)
                    terrain = grid[grid_i][grid_j]['terrain']
                    colors[i, j] = self.colors.get(terrain, 'gray')
            
            self.cache.terrain_colors = colors
            
        except Exception as e:
            print(f"Error updating minimap grid: {e}")

    def update(self, viewport, player_pos):
        """Update minimap state"""
        self.cache.viewport = viewport
        self.cache.player_pos = player_pos

    def world_to_minimap(self, world_x, world_y):
        """Convert world coordinates to minimap coordinates"""
        mini_x = self.position['x'] + (world_x * self.scale['x'])
        mini_y = self.position['y'] + (world_y * self.scale['y'])
        return float(mini_x), float(mini_y)

    def draw_background(self):
        """Draw minimap background and border"""
        # Draw border
        drawRect(
            self.position['x'] - self.style['border']['width'],
            self.position['y'] - self.style['border']['width'],
            self.size['width'] + 2 * self.style['border']['width'],
            self.size['height'] + 2 * self.style['border']['width'],
            fill=self.style['border']['color']
        )

    def draw_terrain(self):
        if self.cache.terrain_colors is None:
            return

        base_x = self.position['x']
        base_y = self.position['y']
        
        for i in range(len(self.cache.terrain_colors)):
            for j in range(len(self.cache.terrain_colors[0])):
                x = base_x + j * self.scaled_cell['width']
                y = base_y + i * self.scaled_cell['height']
                drawRect(x, y, self.scaled_cell['width'], self.scaled_cell['height'], fill=self.cache.terrain_colors[i, j])


    def draw_player(self):
        """Draw player position on minimap"""
        if self.cache.player_pos is None:
            return
            
        char_x, char_y = self.cache.player_pos
        mini_x, mini_y = self.world_to_minimap(
            char_x/self.cell_width,
            char_y/self.cell_height
        )
        
        drawCircle(mini_x, mini_y,
                  self.style['player']['size'],
                  fill=self.style['player']['color'])

    def draw_viewport(self):
        """Draw viewport rectangle on minimap"""
        if self.cache.viewport is None:
            return
            
        start_row, start_col, end_row, end_col = self.cache.viewport
        start_x, start_y = self.world_to_minimap(start_col, start_row)
        end_x, end_y = self.world_to_minimap(end_col, end_row)
        
        drawRect(start_x, start_y,
                end_x - start_x,
                end_y - start_y,
                fill=None,
                border=self.style['viewport']['color'],
                borderWidth=self.style['viewport']['width'],
                opacity=self.style['viewport']['opacity'])

    def draw(self):
        """Main draw method for minimap"""
        try:
            self.draw_background()
            self.draw_terrain()
            self.draw_viewport()
            self.draw_player()
            
        except Exception as e:
            print(f"Error drawing minimap: {e}")
            # Draw error indicator
            drawRect(self.position['x'], self.position['y'],
                    self.size['width'], self.size['height'],
                    fill='red', opacity=50)
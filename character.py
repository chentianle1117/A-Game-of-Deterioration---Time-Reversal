# character.py
from cmu_graphics import *
import math

class Character:
    def __init__(self, world_width, world_height, cell_width, cell_height):
        # World boundaries
        self.WORLD_WIDTH = world_width
        self.WORLD_HEIGHT = world_height
        self.CELL_WIDTH = cell_width
        self.CELL_HEIGHT = cell_height
        
        # Calculate world boundaries in pixels
        self.world_bounds = {
            'left': 0,
            'right': world_width * cell_width,
            'top': 0,
            'bottom': world_height * cell_height
        }
        
        # Character properties
        self.position = {
            'x': (world_width * cell_width) // 2,
            'y': (world_height * cell_height) // 2
        }
        self.direction = 'down'
        self.speed = 2.5  # Reduced for smaller cells
        
        # Visual properties
        self.colors = {
            'body': 'red',
            'outline': 'darkRed',
            'direction': 'white'
        }
        self.visual = {
            'base_size': min(cell_width, cell_height) * 0.4,
            'outline_width': 1,
            'direction_length': 0.7
        }

    def get_position(self):  # <-- This method must be present and working
        """Get current position in world coordinates"""
        return self.position['x'], self.position['y']

    def get_current_cell(self):
        """Get current cell coordinates"""
        col = int(self.position['x'] / self.CELL_WIDTH)
        row = int(self.position['y'] / self.CELL_HEIGHT)
        
        # Ensure within grid bounds
        if (0 <= row < self.WORLD_HEIGHT and 
            0 <= col < self.WORLD_WIDTH):
            return row, col
        return None

    def move(self, dx, dy):
        """Move character with boundary checking"""
        scaled_speed = self.speed * (self.CELL_WIDTH / 20)
        
        # Calculate potential new position
        new_x = self.position['x'] + (dx * scaled_speed)
        new_y = self.position['y'] + (dy * scaled_speed)
        
        # Apply world boundaries
        padding = self.visual['base_size']
        new_x = max(padding, min(new_x, self.world_bounds['right'] - padding))
        new_y = max(padding, min(new_y, self.world_bounds['bottom'] - padding))
        
        # Update position
        self.position['x'] = new_x
        self.position['y'] = new_y

    def draw(self, screen_x, screen_y, zoom_level):
        """Draw character with direction indicator"""
        # Calculate scaled size with minimum size limit
        min_size = 3
        size = max(min_size, self.visual['base_size'] * zoom_level)
        
        # Scale outline width with zoom but keep minimum of 1
        outline_width = max(1, min(self.visual['outline_width'] * zoom_level, 3))
        
        # Draw character body
        drawCircle(screen_x, screen_y, size/2,
                  fill=self.colors['body'],
                  border=self.colors['outline'],
                  borderWidth=outline_width)
        
        # Draw direction indicator
        indicator_length = size * self.visual['direction_length']
        end_x, end_y = screen_x, screen_y
        
        if self.direction == 'right':
            end_x += indicator_length
        elif self.direction == 'left':
            end_x -= indicator_length
        elif self.direction == 'down':
            end_y += indicator_length
        elif self.direction == 'up':
            end_y -= indicator_length
        
        line_width = max(1, min(math.ceil(zoom_level), 3))
        drawLine(screen_x, screen_y, end_x, end_y,
                fill=self.colors['direction'],
                lineWidth=line_width)
        
        dot_size = max(1, size * 0.15)
        drawCircle(end_x, end_y, dot_size,
                  fill=self.colors['direction'])

    def teleport(self, x, y):
        """Teleport character to specific coordinates"""
        self.position['x'] = max(self.visual['base_size'],
                               min(x, self.world_bounds['right'] - self.visual['base_size']))
        self.position['y'] = max(self.visual['base_size'],
                               min(y, self.world_bounds['bottom'] - self.visual['base_size']))

    def get_bounds(self):
        """Get character's bounding box"""
        size = self.visual['base_size']
        return {
            'left': self.position['x'] - size/2,
            'right': self.position['x'] + size/2,
            'top': self.position['y'] - size/2,
            'bottom': self.position['y'] + size/2
        }

    def set_speed(self, speed):
        """Set character movement speed"""
        self.speed = max(1, min(speed, 20))

    def get_info(self):
        """Get character information for debugging"""
        return {
            'position': self.position,
            'cell': self.get_current_cell(),
            'direction': self.direction,
            'speed': self.speed
        }
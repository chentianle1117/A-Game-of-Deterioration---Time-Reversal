# map_editor.py
from cmu_graphics import *
import numpy as np

class MapEditor:
    def __init__(self, width, height, world_width, world_height):
        # Window dimensions
        self.width = width
        self.height = height
        
        # Editor grid dimensions
        self.editor_width = world_width // 4
        self.editor_height = world_height // 4
        self.final_width = self.editor_width * 4
        self.final_height = self.editor_height * 4
        
        # Calculate cell size
        self.cell_width = width / self.editor_width
        self.cell_height = height / self.editor_height
        
        # Initialize grid with all white (1.0)
        self.grid = np.zeros((self.editor_height, self.editor_width))
        
        # Tool settings
        self.brush = {
            'size': 2,
            'min_size': 1,
            'max_size': 10,
            'value': 1.0,  # 0.0 = black, 1.0 = white
            'opacity': 0.2
        }
        
        # UI elements
        self.ui = {
            'save_button': {
                'text': 'Generate World',
                'x': width - 100,
                'y': 30,
                'width': 150,
                'height': 40
            },
            'tools': [
                {'text': 'Black (Water/Low)', 'value': 0.0, 'key': 'b'},
                {'text': 'White (Land/High)', 'value': 1.0, 'key': 'w'}
            ]
        }
        
        # Mouse position
        self.mouseX = 0
        self.mouseY = 0

    def draw(self):
        """Draw the map editor interface"""
        # Draw grid
        for row in range(self.editor_height):
            for col in range(self.editor_width):
                value = self.grid[row, col]
                # Convert value to grayscale
                gray = int(value * 255)
                color = rgb(gray, gray, gray)
                
                drawRect(col * self.cell_width, row * self.cell_height,
                        self.cell_width + 1, self.cell_height + 1,
                        fill=color)
        
        # Draw UI panel
        self._drawUI()
        self._drawBrushPreview()

    def _drawUI(self):
        """Draw UI elements"""
        # Draw tools panel
        panel_height = 150
        drawRect(0, 0, 250, panel_height, fill='black', opacity=50)
        
        # Draw tool buttons
        y = 30
        for tool in self.ui['tools']:
            drawLabel(f"{tool['text']} ({tool['key']})",
                     125, y, fill='white', bold=True)
            y += 25
        
        # Draw brush info
        drawLabel(f"Brush Size: {self.brush['size']} ([ ])",
                 125, y, fill='white', bold=True)
        y += 25
        drawLabel("Higher = Land, Lower = Water",
                 125, y, fill='white', bold=True)
        
        # Draw save button
        btn = self.ui['save_button']
        drawRect(btn['x'] - btn['width']//2,
                btn['y'] - btn['height']//2,
                btn['width'], btn['height'],
                fill='darkGray', border='white')
        drawLabel(btn['text'], btn['x'], btn['y'],
                 fill='white', bold=True)

    def _drawBrushPreview(self):
        """Draw brush preview at cursor"""
        radius = self.brush['size'] * max(self.cell_width, self.cell_height)
        
        # Draw brush outline
        drawCircle(self.mouseX, self.mouseY, radius,
                  fill=None, border='white',
                  borderWidth=2)
        
        # Draw inner circle showing brush value
        value = self.brush['value']
        gray = int(value * 255)
        color = rgb(gray, gray, gray)
        drawCircle(self.mouseX, self.mouseY, radius * 0.2,
                  fill=color, opacity=75)

    def _generateTerrainMap(self):
        """Convert grayscale heightmap to terrain"""
        terrain_map = []
        
        # Upscale the grid
        upscaled = np.repeat(np.repeat(self.grid, 4, axis=0), 4, axis=1)
        upscaled = upscaled[:self.final_height, :self.final_width]
        
        for row in range(self.final_height-1):
            terrain_row = []
            for col in range(self.final_width-1):
                value = upscaled[row, col]
                
                # Convert heightmap value to terrain type
                if value < 0.3:
                    terrain = 'water'
                elif value < 0.5:
                    terrain = 'dirt'
                elif value < 0.8:
                    terrain = 'tall_grass'
                else:
                    terrain = 'path_rocks'
                
                terrain_row.append({
                    'terrain': terrain,
                    'explored': False
                })
            terrain_map.append(terrain_row)
        
        print(f"Generated terrain map: {len(terrain_map)}x{len(terrain_map[0])}")
        return terrain_map

    # Rest of the methods remain the same...
    def updateMousePos(self, mouseX, mouseY):
        self.mouseX = mouseX
        self.mouseY = mouseY

    def _getGridCoords(self, mouseX, mouseY):
        col = int(mouseX / self.cell_width)
        row = int(mouseY / self.cell_height)
        return row, col

    def paint(self, mouseX, mouseY):
        row, col = self._getGridCoords(mouseX, mouseY)
        brush_size = self.brush['size']
        
        y, x = np.ogrid[-brush_size:brush_size+1, -brush_size:brush_size+1]
        mask = x*x + y*y <= brush_size*brush_size
        
        for dy in range(-brush_size, brush_size + 1):
            for dx in range(-brush_size, brush_size + 1):
                new_row, new_col = row + dy, col + dx
                
                if not mask[dy+brush_size, dx+brush_size]:
                    continue
                
                if (0 <= new_row < self.editor_height and 
                    0 <= new_col < self.editor_width):
                    current = self.grid[new_row, new_col]
                    target = self.brush['value']
                    self.grid[new_row, new_col] = (current * (1 - self.brush['opacity']) +
                                                  target * self.brush['opacity'])

    def handle_key(self, key):
        if key == '[':
            self.brush['size'] = max(self.brush['min_size'], 
                                   self.brush['size'] - 1)
        elif key == ']':
            self.brush['size'] = min(self.brush['max_size'], 
                                   self.brush['size'] + 1)
        else:
            for tool in self.ui['tools']:
                if key == tool['key']:
                    self.brush['value'] = tool['value']

    def isOverSaveButton(self, mouseX, mouseY):
        btn = self.ui['save_button']
        return (abs(mouseX - btn['x']) < btn['width']//2 and
                abs(mouseY - btn['y']) < btn['height']//2)

    def handle_click(self, mouseX, mouseY):
        if self.isOverSaveButton(mouseX, mouseY):
            return self._generateTerrainMap()
        return None
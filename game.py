# game.py
from cmu_graphics import *
from cmu_graphics import CMUImage
import random
from texture_manager import TextureManager
from character import Character
from mini_map import MiniMap
from map_editor import MapEditor

class Game:
    def __init__(self, custom_map=None):
            # Core settings
            self.WINDOW_WIDTH = 800
            self.WINDOW_HEIGHT = 600
            self.WORLD_WIDTH = 200
            self.WORLD_HEIGHT = 150
            self.BASE_CELL_WIDTH = 20
            self.BASE_CELL_HEIGHT = 15
            
            # Camera and zoom settings
            self.cameraX = 0
            self.cameraY = 0
            self.zoomLevel = 2.0
            self.MIN_ZOOM = 1.0
            self.MAX_ZOOM = 4.0
            
            # Terrain definitions - match exactly what map editor generates
            self.terrainTypes = {
                'water': 'blue',
                'dirt': 'brown',
                'tall_grass': 'green',
                'path_rocks': 'gray'
            }
            
            # Initialize the texture manager
            self.texture_manager = TextureManager()
            self.texture_manager.verify_textures()
            
            # Initialize grid from custom map
            if custom_map is None:
                raise Exception("Game must be initialized with a custom map")
            
            print("Using custom terrain map")
            print(f"Map size: {len(custom_map)}x{len(custom_map[0])}")
            if len(custom_map) > 0 and len(custom_map[0]) > 0:
                print(f"Sample cell: {custom_map[0][0]}")
                
            self.grid = custom_map
            
            # Initialize remaining components
            self.character = Character(self.WORLD_WIDTH, self.WORLD_HEIGHT,
                                    self.BASE_CELL_WIDTH, self.BASE_CELL_HEIGHT)
            self.miniMap = None
            self.setMiniMap()
            self.updateCamera()
    
    def updateCamera(self):
        """Center camera on character"""
        charX, charY = self.character.get_position()
        self.cameraX = charX - (self.WINDOW_WIDTH / (2 * self.zoomLevel))
        self.cameraY = charY - (self.WINDOW_HEIGHT / (2 * self.zoomLevel))

    def initializeGrid(self):
        """Create the game world grid with terrain"""
        self.grid = []
        for y in range(self.WORLD_HEIGHT):
            row = []
            for x in range(self.WORLD_WIDTH):
                # Default to grass with random variations
                terrain = 'tall_grass' if random.random() < 0.7 else \
                         random.choice(list(self.terrainTypes.keys()))
                cell = {
                    'terrain': terrain,
                    'explored': False
                }
                row.append(cell)
            self.grid.append(row)

    def setMiniMap(self, minimap=None):
        """Initialize or update the minimap"""
        if minimap is None:
            self.miniMap = MiniMap(
                window_width=self.WINDOW_WIDTH,
                window_height=self.WINDOW_HEIGHT,
                world_width=self.WORLD_WIDTH,
                world_height=self.WORLD_HEIGHT,
                cell_width=self.BASE_CELL_WIDTH,
                cell_height=self.BASE_CELL_HEIGHT,
                color_map=self.terrainTypes
            )
        else:
            self.miniMap = minimap
        
        self.miniMap.update_grid(self.grid)

    def worldToScreen(self, worldX, worldY):
        """Convert world coordinates to screen coordinates"""
        screenX = (worldX - self.cameraX) * self.zoomLevel
        screenY = (worldY - self.cameraY) * self.zoomLevel
        return screenX, screenY

    def getVisibleCells(self):
        """Calculate visible cell range"""
        startCol = max(0, int(self.cameraX / self.BASE_CELL_WIDTH))
        startRow = max(0, int(self.cameraY / self.BASE_CELL_HEIGHT))
        
        visibleCols = int(self.WINDOW_WIDTH / (self.BASE_CELL_WIDTH * self.zoomLevel)) + 2
        visibleRows = int(self.WINDOW_HEIGHT / (self.BASE_CELL_HEIGHT * self.zoomLevel)) + 2
        
        endCol = min(self.WORLD_WIDTH, startCol + visibleCols)
        endRow = min(self.WORLD_HEIGHT, startRow + visibleRows)
        
        return startRow, startCol, endRow, endCol

    def drawCell(self, row, col):
        """Draw a cell using texture if available, with fallback to colored rectangles"""
        try:
            # Calculate positions
            worldX = col * self.BASE_CELL_WIDTH
            worldY = row * self.BASE_CELL_HEIGHT
            screenX, screenY = self.worldToScreen(worldX, worldY)
            
            # Calculate dimensions
            width = self.BASE_CELL_WIDTH * self.zoomLevel
            height = self.BASE_CELL_HEIGHT * self.zoomLevel
            
            # Get terrain type
            cell_data = self.grid[row][col]
            if not isinstance(cell_data, dict) or 'terrain' not in cell_data:
                drawRect(screenX, screenY, width, height, 
                        fill='red', border='black', borderWidth=1)
                return
                
            terrain = cell_data['terrain']
            
            # Try to get texture
            texture = self.texture_manager.get_texture(terrain)
            
            if texture is not None and hasattr(texture, '_imageData'):
                try:
                    # Draw texture scaled to cell size
                    drawImage(texture, screenX, screenY, width=width, height=height)
                except Exception as e:
                    color = self.terrainTypes.get(terrain, 'gray')
                    drawRect(screenX, screenY, width, height, 
                            fill=color, border='black', borderWidth=1)
            else:
                # No valid texture, draw colored rectangle
                color = self.terrainTypes.get(terrain, 'gray')
                drawRect(screenX, screenY, width, height, 
                        fill=color, border='black', borderWidth=1)
        
        except Exception as e:
            try:
                drawRect(screenX, screenY, width, height, 
                        fill='red', border='black', borderWidth=1)
            except:
                pass
    
    def setZoom(self, newZoom):
        """Update zoom level within bounds"""
        self.zoomLevel = max(self.MIN_ZOOM, min(self.MAX_ZOOM, newZoom))
        self.updateCamera()

    def drawUI(self):
        """Draw game UI"""
        # Background panel
        drawRect(0, 0, 250, 120, fill='black', opacity=50)
        
        # Get current info
        charX, charY = self.character.get_position()
        currentCell = self.character.get_current_cell()
        
        # Draw labels
        if currentCell:
            row, col = currentCell
            labels = [
                f'Position: ({int(charX)}, {int(charY)})',
                f'Cell: ({col}, {row})',
                f'Camera: ({int(self.cameraX)}, {int(self.cameraY)})',
                f'World: {self.WORLD_WIDTH}x{self.WORLD_HEIGHT}',
                f'Zoom: {self.zoomLevel:.2f}x'
            ]
            
            for i, text in enumerate(labels):
                drawLabel(text, 125, 20 + i*20,
                         size=16, bold=True, fill='white')

    def drawMiniMap(self):
        """Update and draw minimap"""
        if self.miniMap:
            viewport = self.getVisibleCells()
            char_pos = self.character.get_position()
            self.miniMap.update(viewport, char_pos)
            self.miniMap.draw()

    def setCustomGrid(self, new_grid):
        """Set a custom grid from map editor"""
        if len(new_grid) == self.WORLD_HEIGHT and len(new_grid[0]) == self.WORLD_WIDTH:
            self.grid = new_grid
            self.miniMap.update_grid(self.grid)
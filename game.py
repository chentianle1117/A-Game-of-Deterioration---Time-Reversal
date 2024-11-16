from cmu_graphics import *
import random
from texture_manager import TextureManagerOptimized
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
        self.BASE_CELL_WIDTH = 10
        self.BASE_CELL_HEIGHT = 8

        # Camera and zoom settings
        self.cameraX = 0
        self.cameraY = 0
        self.zoomLevel = 4.0
        self.MIN_ZOOM = 3.0
        self.MAX_ZOOM = 7.0

        # Terrain definitions
        self.terrainTypes = {
            'water': 'blue',
            'dirt': 'brown',
            'tall_grass': 'green',
            'path_rocks': 'gray'
        }

        # Initialize the optimized texture manager
        self.texture_manager = TextureManagerOptimized()

        # Initialize grid from custom map
        if custom_map is None:
            raise Exception("Game must be initialized with a custom map")

        print("Using custom terrain map")
        print(f"Map size: {len(custom_map)}x{len(custom_map[0])}")
        if len(custom_map) > 0 and len(custom_map[0]) > 0:
            print(f"Sample cell: {custom_map[0][0]}")

        self.grid = custom_map
        self.character = Character(self.WORLD_WIDTH, self.WORLD_HEIGHT,
                                    self.BASE_CELL_WIDTH, self.BASE_CELL_HEIGHT)
        self.miniMap = None
        self.setMiniMap()
        self.updateCamera()

    def getVisibleCells(self):
        """Calculate visible cell range with padding optimization."""
        padding = 5  # Add small padding for smooth scrolling
        startCol = max(0, int(self.cameraX / self.BASE_CELL_WIDTH) - padding)
        startRow = max(0, int(self.cameraY / self.BASE_CELL_HEIGHT) - padding)

        visibleCols = int(self.WINDOW_WIDTH / (self.BASE_CELL_WIDTH * self.zoomLevel)) + padding * 2
        visibleRows = int(self.WINDOW_HEIGHT / (self.BASE_CELL_HEIGHT * self.zoomLevel)) + padding * 2

        endCol = min(self.WORLD_WIDTH, startCol + visibleCols)
        endRow = min(self.WORLD_HEIGHT, startRow + visibleRows)

        return startRow, startCol, endRow, endCol

    def redrawGame(self):
        """Redraw the game state."""
        drawRect(0, 0, self.WINDOW_WIDTH, self.WINDOW_HEIGHT, fill='white')
        try:
            startRow, startCol, endRow, endCol = self.getVisibleCells()

            for row in range(startRow, endRow):
                for col in range(startCol, endCol):
                    if (0 <= row < self.WORLD_HEIGHT and
                        0 <= col < self.WORLD_WIDTH):
                        self.drawCell(row, col)

            # Draw character
            charX, charY = self.character.get_position()
            screenX, screenY = self.worldToScreen(charX, charY)
            self.character.draw(screenX, screenY, self.zoomLevel)

            # Draw UI and MiniMap
            self.drawUI()
            self.drawMiniMap()
        except Exception as e:
            print(f"Error in redrawGame: {str(e)}")
            drawLabel("Error in rendering", self.WINDOW_WIDTH // 2,
                      self.WINDOW_HEIGHT // 2, fill='red', bold=True, size=20)

    def updateCamera(self):
        """Center camera on character."""
        charX, charY = self.character.get_position()
        self.cameraX = charX - (self.WINDOW_WIDTH / (2 * self.zoomLevel))
        self.cameraY = charY - (self.WINDOW_HEIGHT / (2 * self.zoomLevel))

    def drawCell(self, row, col):
        """Draw a single cell with debug info"""
        worldX = col * self.BASE_CELL_WIDTH
        worldY = row * self.BASE_CELL_HEIGHT
        screenX, screenY = self.worldToScreen(worldX, worldY)

        width = int(self.BASE_CELL_WIDTH * self.zoomLevel)
        height = int(self.BASE_CELL_HEIGHT * self.zoomLevel)

        if (screenX + width > 0 and screenX < self.WINDOW_WIDTH and
            screenY + height > 0 and screenY < self.WINDOW_HEIGHT):
            try:
                cell_data = self.grid[row][col]
                terrain_type = cell_data['terrain']
                print(f"[DEBUG] Drawing cell [{row},{col}] - {terrain_type}")
                
                cmu_image = self.texture_manager.draw_texture(
                    terrain_type, width, height
                )
                
                if cmu_image:
                    drawImage(cmu_image, screenX, screenY, width=width, height=height)
                    print(f"[DEBUG] Successfully drew {terrain_type} at ({screenX}, {screenY})")
                else:
                    print(f"[ERROR] Failed to get texture for {terrain_type}")
                    
            except Exception as e:
                print(f"[ERROR] Failed to draw cell [{row},{col}]: {e}")

    def setZoom(self, newZoom):
        """Update zoom level within bounds."""
        self.zoomLevel = max(self.MIN_ZOOM, min(self.MAX_ZOOM, newZoom))
        self.updateCamera()

    def drawUI(self):
        """Draw game UI."""
        drawRect(0, 0, 250, 120, fill='black', opacity=50)

        # Get current info
        charX, charY = self.character.get_position()
        currentCell = self.character.get_current_cell()

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
                drawLabel(text, 125, 20 + i * 20,
                          size=16, bold=True, fill='white')

    def drawMiniMap(self):
        """Update and draw minimap."""
        if self.miniMap:
            viewport = self.getVisibleCells()
            char_pos = self.character.get_position()
            self.miniMap.update(viewport, char_pos)
            self.miniMap.draw()

    def setMiniMap(self, minimap=None):
        """Initialize or update the minimap."""
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

    def setCustomGrid(self, new_grid):
        """Set a custom grid from map editor."""
        if len(new_grid) == self.WORLD_HEIGHT and len(new_grid[0]) == self.WORLD_WIDTH:
            self.grid = new_grid
            self.miniMap.update_grid(self.grid)

    def worldToScreen(self, worldX, worldY):
        """Convert world coordinates to screen coordinates."""
        screenX = (worldX - self.cameraX) * self.zoomLevel
        screenY = (worldY - self.cameraY) * self.zoomLevel
        return screenX, screenY

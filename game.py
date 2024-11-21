from cmu_graphics import *
import random
from texture_manager import TextureManagerOptimized
from character import Character
from mini_map import MiniMap
from map_editor import MapEditor

class Game:
    def __init__(self, customMap=None):
        self.windowWidth = 800
        self.windowHeight = 600
        self.worldWidth = 200
        self.worldHeight = 150
        self.baseCellWidth = 10
        self.baseCellHeight = 8
        self.cameraX = 0
        self.cameraY = 0
        self.zoomLevel = 11.0
        self.minZoom = 5.0
        self.maxZoom = 13.0
        self.terrainTypes = {
            'water': 'blue',
            'dirt': 'brown',
            'tall_grass': 'green',
            'path_rocks': 'gray'
        }
        self.textureManager = TextureManagerOptimized()
        if customMap is None:
            raise Exception("Game must be initialized with a custom map")
        self.grid = customMap
        self.character = Character(self.worldWidth, self.worldHeight, self.baseCellWidth, self.baseCellHeight)
        self.miniMapState = 'OFF'
        self.miniMap = None
        self.setMiniMap()
        self.updateCamera()
        self.showDebugInfo = True  # Toggle for debug information

    def getVisibleCells(self):
        padding = 5
        startCol = max(0, int(self.cameraX / self.baseCellWidth) - padding)
        startRow = max(0, int(self.cameraY / self.baseCellHeight) - padding)
        visibleCols = int(self.windowWidth / (self.baseCellWidth * self.zoomLevel)) + padding * 2
        visibleRows = int(self.windowHeight / (self.baseCellHeight * self.zoomLevel)) + padding * 2
        endCol = min(self.worldWidth, startCol + visibleCols)
        endRow = min(self.worldHeight, startRow + visibleRows)
        return startRow, startCol, endRow, endCol

    def drawCell(self, row, col):
        worldX = col * self.baseCellWidth
        worldY = row * self.baseCellHeight
        screenX, screenY = self.worldToScreen(worldX, worldY)
        width = int(self.baseCellWidth * self.zoomLevel)
        height = int(self.baseCellHeight * self.zoomLevel)
        
        if (screenX + width > 0 and screenX < self.windowWidth and 
            screenY + height > 0 and screenY < self.windowHeight):
            cellData = self.grid[row][col]
            cmuImage, lifeRatio = self.textureManager.getTextureForCell(
                row, col, 
                cellData['terrain'], 
                width, height,
                character=self.character  # Pass character for restoration effect
            )
            
            if cmuImage:
                drawImage(cmuImage, screenX, screenY, width=width, height=height)
                
                # Debug information display
                if self.showDebugInfo:
                    # Calculate text size based on zoom level
                    textSize = min(12, int(self.zoomLevel * 1.2))
                    
                    # Draw life ratio with background for better visibility
                    lifeText = f"{lifeRatio:.2f}"
                    drawRect(screenX + width/2 - 20, screenY + height/2 - 10,
                            40, 20,
                            fill='black', opacity=40)
                    drawLabel(lifeText, 
                             screenX + width/2, 
                             screenY + height/2,
                             size=textSize,
                             fill='white',
                             bold=True)

    def redrawGame(self):
        drawRect(0, 0, self.windowWidth, self.windowHeight, fill='white')
        try:
            startRow, startCol, endRow, endCol = self.getVisibleCells()
            for row in range(startRow, endRow):
                for col in range(startCol, endCol):
                    if 0 <= row < self.worldHeight and 0 <= col < self.worldWidth:
                        self.drawCell(row, col)
            charX, charY = self.character.getPosition()
            screenX, screenY = self.worldToScreen(charX, charY)
            self.character.draw(screenX, screenY, self.zoomLevel)
            self.drawUI()
            self.drawMiniMap()
        except Exception as e:
            print(f"Error in redrawGame: {str(e)}")
            drawLabel("Error in rendering", self.windowWidth // 2, self.windowHeight // 2, 
                     fill='red', bold=True, size=20)

    def updateCamera(self):
        charX, charY = self.character.getPosition()
        self.cameraX = charX - (self.windowWidth / (2 * self.zoomLevel))
        self.cameraY = charY - (self.windowHeight / (2 * self.zoomLevel))

    def setZoom(self, newZoom):
        self.zoomLevel = max(self.minZoom, min(self.maxZoom, newZoom))
        self.updateCamera()

    def drawUI(self):
        # Draw basic UI panel
        drawRect(0, 0, 250, 140, fill='black', opacity=50)
        
        charX, charY = self.character.getPosition()
        currentCell = self.character.getCurrentCell()
        if currentCell:
            row, col = currentCell
            labels = [
                f'Position: ({int(charX)}, {int(charY)})',
                f'Cell: ({col}, {row})',
                f'Camera: ({int(self.cameraX)}, {int(self.cameraY)})',
                f'World: {self.worldWidth}x{self.worldHeight}',
                f'Zoom: {self.zoomLevel:.2f}x',
                f'Strength: {self.character.strength:.1f}',
                f'Restoration Radius: {self.character.getRestorationRadius():.0f}px'
            ]
            for i, text in enumerate(labels):
                drawLabel(text, 125, 20 + i * 20, size=16, bold=True, fill='white')


    def drawMiniMap(self):
        """Draw the minimap if enabled"""
        if self.miniMapState != 'OFF' and self.miniMap:
            viewport = self.getVisibleCells()
            charPos = self.character.getPosition()
            self.miniMap.setMode(self.miniMapState == 'DETERIORATION')
            self.miniMap.update(viewport, charPos, self.textureManager)
            self.miniMap.draw()

    def toggleMinimapMode(self):
        """Cycle through minimap modes: OFF -> TERRAIN -> DETERIORATION -> OFF"""
        if self.miniMapState == 'OFF':
            self.miniMapState = 'TERRAIN'
            if self.miniMap is None:  # Initialize if needed
                self.setMiniMap()
        elif self.miniMapState == 'TERRAIN':
            self.miniMapState = 'DETERIORATION'
        else:  # DETERIORATION
            self.miniMapState = 'OFF'
        
        print(f"Minimap mode changed to: {self.miniMapState}")  # Debug print

    def setMiniMap(self, minimap=None):
        if minimap is None:
            self.miniMap = MiniMap(
                windowWidth=self.windowWidth,
                windowHeight=self.windowHeight,
                worldWidth=self.worldWidth,
                worldHeight=self.worldHeight,
                cellWidth=self.baseCellWidth,
                cellHeight=self.baseCellHeight,
                colorMap=self.terrainTypes
            )
        else:
            self.miniMap = minimap
        self.miniMap.updateGrid(self.grid)

    def setCustomGrid(self, newGrid):
        if len(newGrid) == self.worldHeight and len(newGrid[0]) == self.worldWidth:
            self.grid = newGrid
            self.miniMap.updateGrid(self.grid)

    def worldToScreen(self, worldX, worldY):
        screenX = (worldX - self.cameraX) * self.zoomLevel
        screenY = (worldY - self.cameraY) * self.zoomLevel
        return screenX, screenY

    def toggleDebugInfo(self):
        self.showDebugInfo = not self.showDebugInfo

    def update(self):
        """Update game state including texture deterioration"""
        # Get actual grid dimensions
        gridHeight = len(self.grid)
        gridWidth = len(self.grid[0]) if gridHeight > 0 else 0
        
        # Initialize all cells in the actual grid
        for row in range(gridHeight):
            for col in range(gridWidth):
                try:
                    cellData = self.grid[row][col]
                    # Initialize cell state if needed
                    self.textureManager.initializeCellState(row, col, cellData['terrain'])
                except Exception as e:
                    print(f"Error initializing cell ({row}, {col}): {e}")
        
        # Update deterioration for all cells
        self.textureManager.updateDeterioration(self.character)
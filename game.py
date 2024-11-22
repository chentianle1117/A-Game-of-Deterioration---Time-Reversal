from cmu_graphics import *
import random
from texture_manager import TextureManagerOptimized
from character import Character
from mini_map import MiniMap
from map_editor import MapEditor
from tree import Tree  # Import the Tree class

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
        
        # Tree system
        self.treeDensity = 0.1  # Adjust this value to control tree density
        self.trees = []
        self.showDebugInfo = True
        self.placeTrees()  # Initialize trees

    def placeTrees(self):
        """Populate the world with trees based on eligible terrain"""
        self.trees = []  # Clear existing trees
        eligibleTerrain = {'dirt', 'tiny_leaves', 'tall_grass'}
        
        # Get actual dimensions of the grid
        gridHeight = len(self.grid)
        gridWidth = len(self.grid[0]) if gridHeight > 0 else 0
        
        for row in range(gridHeight):
            for col in range(gridWidth):
                try:
                    cellData = self.grid[row][col]
                    if cellData['terrain'] in eligibleTerrain:
                        if random.random() < self.treeDensity:
                            # Convert grid position to world coordinates
                            worldX = col * self.baseCellWidth + self.baseCellWidth // 2
                            worldY = row * self.baseCellHeight + self.baseCellHeight // 2
                            self.trees.append(Tree(worldX, worldY))
                except (IndexError, KeyError, TypeError) as e:
                    print(f"Error placing tree at ({row}, {col}): {e}")
                    continue

    def getSurroundingTerrainHealth(self, worldX, worldY):
        """Get health of surrounding terrain for a tree"""
        # Convert world coordinates to grid coordinates
        centerCol = int(worldX / self.baseCellWidth)
        centerRow = int(worldY / self.baseCellHeight)
        surroundingRatios = []

        # Check 3x3 grid around tree
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                newRow, newCol = centerRow + dy, centerCol + dx
                if 0 <= newRow < self.worldHeight and 0 <= newCol < self.worldWidth:
                    cellKey = self.textureManager.getCellKey(newRow, newCol)
                    cellState = self.textureManager.cellStates.get(cellKey)
                    if cellState:
                        surroundingRatios.append(cellState['lifeRatio'])
                    else:
                        surroundingRatios.append(1.0)  # Default to healthy if no state

        return surroundingRatios

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
                character=self.character
            )
            
            if cmuImage:
                drawImage(cmuImage, screenX, screenY, width=width, height=height)
                
                if self.showDebugInfo:
                    textSize = min(12, int(self.zoomLevel * 1.2))
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
            # Draw terrain
            startRow, startCol, endRow, endCol = self.getVisibleCells()
            for row in range(startRow, endRow):
                for col in range(startCol, endCol):
                    if 0 <= row < self.worldHeight and 0 <= col < self.worldWidth:
                        self.drawCell(row, col)

            # Draw trees (after terrain, before character)
            for tree in self.trees:
                screenX, screenY = self.worldToScreen(tree.baseX, tree.baseY)
                # Only draw if tree is visible on screen
                if (-100 < screenX < self.windowWidth + 100 and 
                    -100 < screenY < self.windowHeight + 100):
                    tree.drawTree(None)  # None because we don't use context

            # Draw character
            charX, charY = self.character.getPosition()
            screenX, screenY = self.worldToScreen(charX, charY)
            self.character.draw(screenX, screenY, self.zoomLevel)

            # Draw UI elements
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
        if self.miniMapState != 'OFF' and self.miniMap:
            viewport = self.getVisibleCells()
            charPos = self.character.getPosition()
            self.miniMap.setMode(self.miniMapState == 'DETERIORATION')
            self.miniMap.update(viewport, charPos, self.textureManager)
            self.miniMap.draw()

    def toggleMinimapMode(self):
        if self.miniMapState == 'OFF':
            self.miniMapState = 'TERRAIN'
            if self.miniMap is None:
                self.setMiniMap()
        elif self.miniMapState == 'TERRAIN':
            self.miniMapState = 'DETERIORATION'
        else:
            self.miniMapState = 'OFF'

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
            self.placeTrees()  # Regenerate trees when grid changes

    def worldToScreen(self, worldX, worldY):
        screenX = (worldX - self.cameraX) * self.zoomLevel
        screenY = (worldY - self.cameraY) * self.zoomLevel
        return screenX, screenY

    def toggleDebugInfo(self):
        self.showDebugInfo = not self.showDebugInfo

    def update(self):
        """Update game state including texture deterioration and trees"""
        # Update terrain
        gridHeight = len(self.grid)
        gridWidth = len(self.grid[0]) if gridHeight > 0 else 0
        
        for row in range(gridHeight):
            for col in range(gridWidth):
                try:
                    cellData = self.grid[row][col]
                    self.textureManager.initializeCellState(row, col, cellData['terrain'])
                except Exception as e:
                    print(f"Error initializing cell ({row}, {col}): {e}")
        
        # Update terrain deterioration
        self.textureManager.updateDeterioration(self.character)
        
        # Update trees
        for tree in self.trees:
            surroundingRatios = self.getSurroundingTerrainHealth(tree.baseX, tree.baseY)
            tree.updateTreeLife(surroundingRatios)
from cmu_graphics import *
import random
from texture_manager import TextureManagerOptimized
from character import Character
from mini_map import MiniMap
from map_editor import MapEditor
from tree import Tree

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
        
        self.character = Character(self.worldWidth, self.worldHeight, 
                                 self.baseCellWidth, self.baseCellHeight)
        
        self.miniMapState = 'OFF'
        self.miniMap = None
        self.setMiniMap()
        self.updateCamera()
        
        # Tree system
        self.treeDensity = 0.1  # Initial tree density
        self.trees = []
        self.showDebugInfo = True
        self.placeTrees()  # Initialize trees

    def placeTrees(self):
        """Only create tree instances without generating them"""
        self.trees = []
        eligibleTerrain = {'dirt', 'tiny_leaves', 'tall_grass'}
        
        for row in range(self.worldHeight):
            for col in range(self.worldWidth):
                try:
                    cellData = self.grid[row][col]
                    if cellData['terrain'] in eligibleTerrain:
                        if random.random() < self.treeDensity:
                            worldX = (col + 0.5) * self.baseCellWidth
                            worldY = (row + 0.5) * self.baseCellHeight
                            tree = Tree(worldX, worldY)
                            self.trees.append((tree, (row, col)))  # Store grid position with tree
                except Exception as e:
                    print(f"Error placing tree at ({row}, {col}): {e}")

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
        try:
            # Get visible area
            startRow, startCol, endRow, endCol = self.getVisibleCells()
            
            # Draw terrain
            for row in range(startRow, endRow):
                for col in range(startCol, endCol):
                    if 0 <= row < self.worldHeight and 0 <= col < self.worldWidth:
                        self.drawCell(row, col)
            
            # Update and draw only visible trees
            visibleTrees = []
            for tree, (treeRow, treeCol) in self.trees:
                if (startCol-1 <= treeCol <= endCol+1 and 
                    startRow-1 <= treeRow <= endRow+1):
                    # Generate tree if needed
                    tree.ensureGenerated()
                    
                    # Update tree with surrounding terrain health
                    if tree.needsUpdate:
                        surroundingRatios = self.getSurroundingTerrainHealth(
                            tree.baseX, tree.baseY)
                        tree.updateTreeLife(surroundingRatios)
                        tree.needsUpdate = False
                    
                    screenX, screenY = self.worldToScreen(tree.baseX, tree.baseY)
                    visibleTrees.append((tree, screenX, screenY))
                else:
                    # Tree is out of view, mark it for update when it comes back
                    tree.needsUpdate = True
            
            # Draw visible trees
            for tree, screenX, screenY in sorted(visibleTrees, key=lambda x: x[2]):
                tree.drawTree(self)

            # Draw character and UI
            charX, charY = self.character.getPosition()
            screenX, screenY = self.worldToScreen(charX, charY)
            self.character.draw(screenX, screenY, self.zoomLevel)
            self.drawUI()
            self.drawMiniMap()

        except Exception as e:
            print(f"Error in redrawGame: {str(e)}")

    def updateCamera(self):
        charX, charY = self.character.getPosition()
        self.cameraX = charX - (self.windowWidth / (2 * self.zoomLevel))
        self.cameraY = charY - (self.windowHeight / (2 * self.zoomLevel))

    def setZoom(self, newZoom):
        self.zoomLevel = max(self.minZoom, min(self.maxZoom, newZoom))
        self.updateCamera()

    def drawUI(self):
        drawRect(0, 0, 250, 150, fill='black', opacity=50)
        
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
                f'Trees: {len(self.trees)}',
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
        print("Toggling minimap mode from:", self.miniMapState)  # Debug print
        if self.miniMapState == 'OFF':
            self.miniMapState = 'TERRAIN'
        elif self.miniMapState == 'TERRAIN':
            self.miniMapState = 'DETERIORATION'
        else:
            self.miniMapState = 'OFF'
        print("New minimap mode:", self.miniMapState)  # Debug print

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
        """Convert world coordinates to screen coordinates"""
        screenX = (worldX - self.cameraX) * self.zoomLevel
        screenY = (worldY - self.cameraY) * self.zoomLevel
        return screenX, screenY

    def screenToWorld(self, screenX, screenY):
        """Convert screen coordinates to world coordinates"""
        worldX = (screenX / self.zoomLevel) + self.cameraX
        worldY = (screenY / self.zoomLevel) + self.cameraY
        return worldX, worldY

    def toggleDebugInfo(self):
        self.showDebugInfo = not self.showDebugInfo

    def update(self):
        """Update game state including texture deterioration and trees"""
        # Get visible area first
        startRow, startCol, endRow, endCol = self.getVisibleCells()
        
        # Only update terrain in and around visible area
        padding = 2  # Add some padding to avoid edge effects
        for row in range(max(0, startRow-padding), min(self.worldHeight, endRow+padding)):
            for col in range(max(0, startCol-padding), min(self.worldWidth, endCol+padding)):
                try:
                    cellData = self.grid[row][col]
                    self.textureManager.initializeCellState(row, col, cellData['terrain'])
                except Exception as e:
                    print(f"Error initializing cell ({row}, {col}): {e}")
        
        # Update terrain deterioration
        self.textureManager.updateDeterioration(self.character)
        
        # Only update trees in visible area
        for tree, (treeRow, treeCol) in self.trees:  # Trees now stored with their grid positions
            if (startCol-1 <= treeCol <= endCol+1 and 
                startRow-1 <= treeRow <= endRow+1):
                # Generate tree if it hasn't been generated yet
                if not tree.isGenerated:
                    tree.ensureGenerated()
                
                # Update tree with surrounding terrain health
                surroundingRatios = self.getSurroundingTerrainHealth(tree.baseX, tree.baseY)
                tree.updateTreeLife(surroundingRatios)
                tree.needsUpdate = False
            else:
                # Tree is out of view, mark it for update when it comes back
                tree.needsUpdate = True
                # Optionally, we could also clear the tree's generated data to save memory
                tree.isGenerated = False
                tree.branches = []
                tree.leaves = []

    def debugTrees(self):
        """Debug tree positions and visibility"""
        startRow, startCol, endRow, endCol = self.getVisibleCells()
        print(f"Visible area: ({startCol},{startRow}) to ({endCol},{endRow})")
        print(f"Camera position: ({self.cameraX}, {self.cameraY})")
        print(f"Total trees: {len(self.trees)}")
        
        visibleTrees = 0
        for tree in self.trees:
            # Get tree's grid position
            treeCol = int(tree.baseX / self.baseCellWidth)
            treeRow = int(tree.baseY / self.baseCellHeight)
            screenX, screenY = self.worldToScreen(tree.baseX, tree.baseY)
            
            if (startCol-1 <= treeCol <= endCol+1 and 
                startRow-1 <= treeRow <= endRow+1):
                print(f"Tree at grid({treeRow},{treeCol}) world({tree.baseX},{tree.baseY}) screen({screenX},{screenY})")
                visibleTrees += 1
        
        print(f"Visible trees: {visibleTrees}")
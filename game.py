from cmu_graphics import *
import random
from texture_manager import TextureManagerOptimized
from character import Character
from mini_map import MiniMap
from map_editor import MapEditor
from tree import Tree
import time
import math
from equipment import Equipment

'''
====AI Assistance Summary====
The following features were implemented with Claude 3.5's help:

1. redrawGame() and related rendering methods:
   - Split complex rendering into focused helper methods
   - Implemented visibility-based optimization
   - Added tree rendering with depth sorting
   - Created modular terrain and UI drawing system

2. _updateAndDrawTrees():
   - Tree visibility optimization
   - Health update system
   - Back-to-front rendering sort
   - Screen coordinate conversion

3. Helper Methods:
   - Visibility checking (_isValidCell, _isTreeVisible)
   - World-to-screen coordinate conversion
   - Error handling implementation
'''

class Game:
    def __init__(self, customMap=None):
        self.windowWidth = 800
        self.windowHeight = 600
        self.worldWidth = 200
        self.worldHeight = 150
        self.baseCellWidth = 10
        self.baseCellHeight = 8
        
        self.cameraX = self.cameraY = 0
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
        if not customMap:
            raise Exception("Need a map to start game!")
        self.grid = customMap
        
        # Initialize equipment list and spawn density
        self.equipment = []
        self.equipmentDensity = 0.02  
        
        # Create character first so it exists when spawning equipment
        self.character = Character(self.worldWidth, self.worldHeight, 
                                self.baseCellWidth, self.baseCellHeight)
        self.character.strength = 0.1
        self.character.restorationRadiusMultiplier = 10
        self.character.healingWave['healAmount'] = 0.05
        
        # Spawn equipment
        self._spawnEquipment()
        
        self.miniMapState = 'OFF'
        self.miniMap = None
        self.setMiniMap()
        self.updateCamera()
        
        self.gameOver = False
        self.gameWon = False
        self.startTime = time.time()
        self.gameTime = 60
        self.showGameOverMessage = False
        
        self.treeDensity = 0.05
        self.trees = []
        self.showDebugInfo = True
        self._spawnTrees()

    def _spawnTrees(self):
        ok_terrain = {'dirt', 'tiny_leaves', 'tall_grass'}
        
        for row in range(self.worldHeight):
            for col in range(self.worldWidth):
                try:
                    cell = self.grid[row][col]
                    if cell['terrain'] in ok_terrain and random.random() < self.treeDensity:
                            x = (col + 0.5) * self.baseCellWidth
                            y = (row + 0.5) * self.baseCellHeight
                            self.trees.append((Tree(x, y), (row, col)))
                except Exception as e:
                    print(f"Tree spawn failed at {row}, {col}: {e}")

    def getSurroundingTerrainHealth(self, worldX, worldY):
        # Convert world coordinates to grid position
        col = int(worldX / self.baseCellWidth)
        row = int(worldY / self.baseCellHeight)
        health = []

        # Check each neighboring cell
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                r, c = row + dy, col + dx
                
                # Skip cells outside the world bounds
                if not (0 <= r < self.worldHeight and 0 <= c < self.worldWidth):
                    continue
                    
                # Get cell's current health
                key = self.textureManager.getCellKey(r, c)
                state = self.textureManager.cellStates.get(key)
                health.append(state['lifeRatio'] if state else 1.0)

        return health

    def getVisibleCells(self):
        # Add extra cells around the visible area
        PADDING = 5
        
        # Find top-left corner of visible area
        startCol = int(self.cameraX / self.baseCellWidth)
        startRow = int(self.cameraY / self.baseCellHeight)
        
        # Calculate how many cells fit on screen at current zoom
        cellsWide = int(self.windowWidth / (self.baseCellWidth * self.zoomLevel))
        cellsHigh = int(self.windowHeight / (self.baseCellHeight * self.zoomLevel))
        
        # Add padding and clamp to world bounds
        startCol = max(0, startCol - PADDING)
        startRow = max(0, startRow - PADDING)
        endCol = min(self.worldWidth, startCol + cellsWide + PADDING * 2)
        endRow = min(self.worldHeight, startRow + cellsHigh + PADDING * 2)
        
        return startRow, startCol, endRow, endCol

    def drawCell(self, row, col):
        # Convert grid position to world coordinates
        worldX = col * self.baseCellWidth
        worldY = row * self.baseCellHeight
        
        # Convert to screen coordinates and get cell size
        screenX, screenY = self.worldToScreen(worldX, worldY)
        width = int(self.baseCellWidth * self.zoomLevel)
        height = int(self.baseCellHeight * self.zoomLevel)
        
        # Only draw if cell is visible on screen
        isVisible = (screenX + width > 0 and screenX < self.windowWidth and 
                    screenY + height > 0 and screenY < self.windowHeight)
        
        if isVisible:
            # Get cell data and texture
            cellData = self.grid[row][col]
            texture, health = self.textureManager.getTextureForCell(
                row, col, 
                cellData['terrain'], 
                width, height,
                character=self.character
            )
            
            # Draw the cell if texture exists
            if texture:
                drawImage(texture, screenX, screenY, 
                         width=width, height=height)
                
                # Draw border for unwalkable deteriorated terrain
                if (cellData['terrain'] != 'water' and 
                    not self.isTerrainWalkable(worldX, worldY)):
                    drawRect(screenX, screenY, width, height,
                            fill=None, border='black',
                            borderWidth=2)
                
                # Show debug overlay if enabled
                if self.showDebugInfo:
                    self._drawHealthOverlay(screenX, screenY, 
                                          width, height, health)
    
    def _drawHealthOverlay(self, x, y, width, height, health):
        # Draw background box
        boxWidth = 40
        boxHeight = 20
        boxX = x + width/2 - boxWidth/2
        boxY = y + height/2 - boxHeight/2
        
        drawRect(boxX, boxY, boxWidth, boxHeight,
                fill='black', opacity=40)
        
        # Draw health value
        textSize = min(12, int(self.zoomLevel * 1.2))
        drawLabel(f"{health:.2f}", 
                 x + width/2, y + height/2,
                 size=textSize,
                 fill='white',
                 bold=True)

    def redrawGame(self):
        try:
            # Clear screen
            drawRect(0, 0, self.windowWidth, self.windowHeight, fill='black')
            
            # Get visible area
            visibleArea = self.getVisibleCells()
            startRow, startCol, endRow, endCol = visibleArea
            
            # Draw terrain
            self._drawVisibleTerrain(startRow, startCol, endRow, endCol)
            
            # Draw equipment first (under trees and character)
            for equip in self.equipment:
                if not equip.collected:
                    equip.draw(self)
                    
            # Draw trees
            self._updateAndDrawTrees(startRow, startCol, endRow, endCol)
            
            # Draw character
            charPos = self.character.getPosition()
            screenPos = self.worldToScreen(*charPos)
            self.character.draw(*screenPos, self.zoomLevel)
            
            # Draw UI elements
            self.drawUI()
            self.drawMiniMap()
            
        except Exception as e:
            print(f"Error in redrawGame: {e}")

    def _drawVisibleTerrain(self, startRow, startCol, endRow, endCol):
        # Draw visible cells
        for row in range(startRow, endRow):
            for col in range(startCol, endCol):
                if self._isValidCell(row, col):
                    self.drawCell(row, col)

    def _updateAndDrawTrees(self, startRow, startCol, endRow, endCol):

        treesToDraw = []
        
        for tree, position in self.trees:
            treeRow, treeCol = position
            

            if self._isTreeVisible(treeRow, treeCol, startRow, startCol, endRow, endCol):
                tree.ensureGenerated()
                
                # Update tree health if needed
                if tree.needsUpdate:
                    health = self.getSurroundingTerrainHealth(tree.baseX, tree.baseY)
                    tree.updateTreeLife(health)
                    tree.needsUpdate = False
                
                # Convert world position to screen coordinates
                screenPos = self.worldToScreen(tree.baseX, tree.baseY)
                treesToDraw.append((tree, *screenPos))
            else:
                tree.needsUpdate = True
        
        # Draw trees in order of y-position (back to front)
        for tree, screenX, screenY in sorted(treesToDraw, key=lambda t: t[2]):
            tree.drawTree(self)

    def _drawPlayerAndUI(self):
        # Draw equipment first (under the player)
        for equip in self.equipment:
            if not equip.collected:
                equip.draw(self)
        
        # Then draw the character
        charPos = self.character.getPosition()
        screenPos = self.worldToScreen(*charPos)
        self.character.draw(*screenPos, self.zoomLevel)
        
        self.drawUI()
        self.drawMiniMap()

    def _isValidCell(self, row, col):
        return 0 <= row < self.worldHeight and 0 <= col < self.worldWidth

    def _isTreeVisible(self, treeRow, treeCol, startRow, startCol, endRow, endCol):
        return (startCol-1 <= treeCol <= endCol+1 and 
                startRow-1 <= treeRow <= endRow+1)

    def updateCamera(self):
        charX, charY = self.character.getPosition()
        self.cameraX = charX - (self.windowWidth / (2 * self.zoomLevel))
        self.cameraY = charY - (self.windowHeight / (2 * self.zoomLevel))

    def setZoom(self, newZoom):
        self.zoomLevel = max(self.minZoom, min(self.maxZoom, newZoom))
        self.updateCamera()

    #====Section debugged by Claude 3.5, very complex, mostly attempted to be written by me, but some details added by Claude====
    def drawUI(self):
        # Ability icon and cooldown
        abilitySize = 60
        abilityX = self.windowWidth - 80
        abilityY = self.windowHeight - 80
        centerX = abilityX
        centerY = abilityY
        
        # Ability background
        drawRect(centerX - abilitySize/2, centerY - abilitySize/2, 
                abilitySize, abilitySize, 
                fill='darkBlue', border='lightBlue', 
                borderWidth=2)
        
        # Wave Symbol
        wavePoints = []
        for i in range(12):
            t = i / 11
            x = centerX - abilitySize/2 + t * abilitySize
            y = centerY + math.sin(t * math.pi * 2) * 10
            wavePoints.extend([x, y])
        drawPolygon(*wavePoints, 
                    fill=None, border='lightGreen', 
                    borderWidth=2)
        
        # Cooldown overlay
        currentTime = time.time()
        if not self.character.canUseHealingWave(currentTime):
            cooldown = self.character.getHealingWaveCooldown(currentTime)
            cooldownRatio = cooldown / self.character.healingWave['cooldown']
            cooldownHeight = abilitySize * cooldownRatio
            
            if cooldownHeight > 0:
                drawRect(centerX - abilitySize/2, 
                        centerY - abilitySize/2, 
                        abilitySize, cooldownHeight,
                        fill='black', opacity=60)
                
                # Show cooldown time
                drawLabel(f"{int(cooldown)}s", 
                         centerX, centerY,
                         fill='white', bold=True)
        
        # Key binding
        drawLabel("Space", centerX, centerY + abilitySize/2 + 15,
                 fill='white', bold=True)
        
        # Timer
        elapsedTime = time.time() - self.startTime
        remainingTime = max(0, self.gameTime - elapsedTime)
        minutes = int(remainingTime // 60)
        seconds = int(remainingTime % 60)
        
        timerColor = 'white'
        if remainingTime <= 30:
            timerColor = 'red'
        elif remainingTime <= 60:
            timerColor = 'orange'
            
        drawLabel(f"Time: {minutes:02d}:{seconds:02d}",
                 self.windowWidth - 100, 30,
                 fill=timerColor, bold=True, size=24)
                 
        # deterioration bar at top right
        barWidth = 200
        barHeight = 20
        barX = self.windowWidth - barWidth - 20
        barY = 60
        
        # Background
        drawRect(barX, barY, barWidth, barHeight, fill='darkGray')
        
        # Fill bar
        globalDeterioration = self.textureManager.calculateGlobalDeterioration()
        fillWidth = barWidth * globalDeterioration
        fillColor = 'lightGreen'
        if globalDeterioration >= 0.8:
            fillColor = 'red'
            if not self.gameOver:
                self.gameOver = True
                self.gameWon = False
        elif globalDeterioration >= 0.7:
            fillColor = 'orange'
            
        drawRect(barX, barY, fillWidth, barHeight, fill=fillColor)
        drawRect(barX, barY, barWidth, barHeight, fill=None, border='white')
        
        # Win/lose conditions
        if remainingTime <= 0 and not self.gameOver:
            if globalDeterioration < 0.8:
                self.gameOver = True
                self.gameWon = True
                
        if self.gameOver:
            self.drawGameOverMessage()
    #====Section debugged by Claude 3.5, very complex, mostly attempted to be written by me, but some details added by Claude====
    
    def drawGameOverMessage(self):
        # overlay
        drawRect(0, 0, self.windowWidth, self.windowHeight,
                fill='black', opacity=40)
        
        # Message box
        boxWidth = 400
        boxHeight = 200
        boxX = (self.windowWidth - boxWidth) / 2
        boxY = (self.windowHeight - boxHeight) / 2
        
        drawRect(boxX, boxY, boxWidth, boxHeight,
                fill='white', border='gray',
                borderWidth=3)
        
        # Title
        titleY = boxY + 50
        if self.gameWon:
            message = "Victory!"
            color = 'green'
            subMessage = "You successfully preserved the environment!"
        else:
            message = "Game Over"
            color = 'red'
            subMessage = "The deterioration level became too high!"
        
        drawLabel(message,
                 self.windowWidth / 2, titleY,
                 fill=color, bold=True, size=36)
        
        # Sub-message
        drawLabel(subMessage,
                 self.windowWidth / 2, titleY + 50,
                 fill='black', size=20)
        # Instructions
        drawLabel("Press ESC to return to menu",
                 self.windowWidth / 2, titleY + 100,
                 fill='gray', size=16)
        

    def emitHealingWave(self):
        """Handle healing wave special ability"""
        currentTime = time.time()
        if self.character.canUseHealingWave(currentTime):
            # Start the healing wave animation
            if self.character.emitHealingWave(currentTime):
                # Apply the healing effect
                healAmount = self.character.healingWave['healAmount']  # Get heal amount from character
                self.textureManager.applyGlobalHealing(healAmount)
                return True
        return False
            
    def drawMiniMap(self):
        if self.miniMapState != 'OFF' and self.miniMap:
            viewport = self.getVisibleCells()
            charPos = self.character.getPosition()
            self.miniMap.setMode(self.miniMapState == 'DETERIORATION')
            self.miniMap.update(viewport, charPos, self.textureManager)
            self.miniMap.draw()

    def toggleMinimapMode(self):
        print("Toggling minimap mode from:", self.miniMapState) 
        if self.miniMapState == 'OFF':
            self.miniMapState = 'TERRAIN'
        elif self.miniMapState == 'TERRAIN':
            self.miniMapState = 'DETERIORATION'
        else:
            self.miniMapState = 'OFF'
        print("New minimap mode:", self.miniMapState) 

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
            self._spawnTrees()  # Regenerate trees when grid changes

    def worldToScreen(self, worldX, worldY):
        screenX = (worldX - self.cameraX) * self.zoomLevel
        screenY = (worldY - self.cameraY) * self.zoomLevel
        return screenX, screenY

    def screenToWorld(self, screenX, screenY):
        worldX = (screenX / self.zoomLevel) + self.cameraX
        worldY = (screenY / self.zoomLevel) + self.cameraY
        return worldX, worldY

    def toggleDebugInfo(self):
        self.showDebugInfo = not self.showDebugInfo

    def update(self):
        """Update game state including texture deterioration and trees"""

        startRow, startCol, endRow, endCol = self.getVisibleCells()
        #====Section debugged by Claude 3.5, very complex, mostly attempted to be written by me, but some details added by Claude====
        # Only update terrain in and around visible area
        padding = 2
        for row in range(max(0, startRow-padding), min(self.worldHeight, endRow+padding)):
            for col in range(max(0, startCol-padding), min(self.worldWidth, endCol+padding)):
                try:
                    cellData = self.grid[row][col]
                    self.textureManager.initializeCellState(row, col, cellData['terrain'])
                except Exception as e:
                    print(f"Error initializing cell ({row}, {col}): {e}")
        
        self.textureManager.updateDeterioration(self.character)
        
        # Only update trees in visible area
        for tree, (treeRow, treeCol) in self.trees: 
            if (startCol-1 <= treeCol <= endCol+1 and 
                startRow-1 <= treeRow <= endRow+1):
                # Generate tree if it hasn't been generated yet
                if not tree.isGenerated:
                    tree.ensureGenerated()
                
                surroundingRatios = self.getSurroundingTerrainHealth(tree.baseX, tree.baseY)
                tree.updateTreeLife(surroundingRatios)
                tree.needsUpdate = False
            else:
                tree.needsUpdate = True
                tree.isGenerated = False
                tree.branches = []
                tree.leaves = []
        #====Section debugged by Claude 3.5, very complex, mostly attempted to be written by me, but some details added by Claude====

    def debugTrees(self):
        """Print info about tree positions and visibility for debugging"""
        # Get current viewport bounds
        viewport = self.getVisibleCells()
        startRow, startCol, endRow, endCol = viewport
        
        # Print basic debug info
        print(f"\nDebugging Trees:")
        print(f"Camera at ({self.cameraX:.1f}, {self.cameraY:.1f})")
        print(f"Viewing area from ({startCol}, {startRow}) to ({endCol}, {endRow})")
        print(f"Total trees in world: {len(self.trees)}\n")
        
        # Track visible trees
        treesInView = 0
        
        # Check each tree
        for tree in self.trees:
            # Convert tree position to grid coordinates
            gridX = int(tree.baseX / self.baseCellWidth)
            gridY = int(tree.baseY / self.baseCellHeight)
            
            # Check if tree is in view (with 1-cell padding)
            if (startCol-1 <= gridX <= endCol+1 and 
                startRow-1 <= gridY <= endRow+1):
                
                # Get screen position for debugging
                screenPos = self.worldToScreen(tree.baseX, tree.baseY)
                
                # Print tree info
                print(f"Tree {treesInView + 1}:")
                print(f"  Grid: ({gridY}, {gridX})")
                print(f"  World: ({tree.baseX:.1f}, {tree.baseY:.1f})")
                print(f"  Screen: ({screenPos[0]:.1f}, {screenPos[1]:.1f})")
                
                treesInView += 1
        
        print(f"\nTrees currently visible: {treesInView}")

    def isTerrainWalkable(self, worldX, worldY):
        # Convert world coordinates to grid position
        col = int(worldX / self.baseCellWidth)
        row = int(worldY / self.baseCellHeight)
        
        # Check bounds
        if not self._isValidCell(row, col):
            return False
        
        # Check if water
        cellData = self.grid[row][col]
        if cellData['terrain'] == 'water':
            return False
        
        # Check deterioration level
        key = self.textureManager.getCellKey(row, col)
        state = self.textureManager.cellStates.get(key)
        if state and state['lifeRatio'] >= 0.8:
            return False
        
        return True

    def _spawnEquipment(self):
        """Spawn equipment on valid terrain (not water)"""
        self.equipment = []  # Clear existing equipment
        ok_terrain = {'dirt', 'tall_grass', 'path_rocks'}
        
        for row in range(self.worldHeight):
            for col in range(self.worldWidth):
                try:
                    cell = self.grid[row][col]
                    if cell['terrain'] in ok_terrain and random.random() < self.equipmentDensity:
                        x = (col + 0.5) * self.baseCellWidth
                        y = (row + 0.5) * self.baseCellHeight
                        self.equipment.append(Equipment(x, y))  # Using simplified Equipment constructor
                        print(f"Spawned equipment at ({row}, {col})")
                except Exception as e:
                    print(f"Equipment spawn failed at {row}, {col}: {e}")
        
        print(f"Total equipment spawned: {len(self.equipment)}")

    def updateGame(self, dt):
        # Add to existing update method
        self._checkEquipmentCollection()

    def _checkEquipmentCollection(self):
        charX, charY = self.character.getPosition()
        collection_radius = self.character.visual['baseSize'] * 2  # Increased collection radius
        
        for equip in self.equipment[:]:  # Use slice to allow removal during iteration
            if not equip.collected:
                dx = charX - equip.x
                dy = charY - equip.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < collection_radius:
                    bonuses = equip.getBonuses()
                    # Apply bonuses
                    self.character.strength += bonuses['strength_bonus']
                    self.character.restorationRadiusMultiplier += bonuses['radius_bonus']
                    equip.collected = True
                    self.equipment.remove(equip)  # Remove from list immediately
                    print(f"Equipment collected! New strength: {self.character.strength}")
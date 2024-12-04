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
    def __init__(self, customMap=None, isInfiniteMode=False):
        self.isInfiniteMode = isInfiniteMode
        self.statistics = {
            'deterioration': [],
            'power': [],
            'speed': [],
            'healingRadius': [],
            'timestamps': []
        }
        self.windowWidth = 800
        self.windowHeight = 600
        self.worldWidth = 200
        self.worldHeight = 150
        self.baseCellWidth = 10
        self.baseCellHeight = 8
        
        self.cameraX = self.cameraY = 0
        self.zoomLevel = 8.0
        self.minZoom = 5.0
        self.maxZoom = 10.0
        
        self.terrainTypes = {
            'water': 'blue',
            'dirt': 'brown',
            'tall_grass': 'green',
            'path_rocks': 'gray',
            'bricks': 'darkGray',
            'snow': 'white',
            'bigleaves': 'forestGreen',
            'tiny_leaves': 'lightGreen'
        }
        
        self.textureManager = TextureManagerOptimized()
        if not customMap:
            raise Exception("Need a map to start game!")
        self.grid = customMap
        
        # Initialize equipment list and spawn density
        self.equipment = []
        self.equipmentDensity = 0.05
        
        # Create character with adjusted initial values
        self.character = Character(self.worldWidth, self.worldHeight, 
                                self.baseCellWidth, self.baseCellHeight)
        self.character.strength = 0.1
        self.character.restorationRadiusMultiplier = 5
        self.character.healingWave['healAmount'] = 0.05
        
        try:
            # Spawn character on high ground
            self._spawnCharacter()
        except Exception as e:
            print(f"Failed to spawn character: {e}")
            raise Exception("Cannot start game: No valid spawn position found")
        
        # Spawn equipment
        self._spawnEquipment()
        
        self.miniMapState = 'TERRAIN'  # Instead of 'DETERIORATION'
        self.miniMap = MiniMap(
            windowWidth=self.windowWidth,
            windowHeight=self.windowHeight,
            worldWidth=self.worldWidth,
            worldHeight=self.worldHeight,
            cellWidth=self.baseCellWidth,
            cellHeight=self.baseCellHeight,
            colorMap=self.terrainTypes
        )
        self.miniMap.showDeterioration = True
        self.miniMap.updateGrid(self.grid)
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
        
        self.inventory = {
            'radius': {'count': 0, 'total_bonus': 0},
            'power': {'count': 0, 'total_bonus': 0},
            'speed': {'count': 0, 'total_bonus': 0},
            'burst': {'count': 0}
        }
        self.healingBursts = []  # List to track active burst animations
        
        # Load equipment sprites
        Equipment.loadSprites()

    def _spawnTrees(self):
        ok_terrain = {'dirt', 'tiny_leaves', 'tall_grass'}
        
        # Clear existing trees
        self.trees = []
        
        # Only spawn trees within valid bounds
        for row in range(min(self.worldHeight, len(self.grid))):
            for col in range(min(self.worldWidth, len(self.grid[row]))):
                try:
                    cell = self.grid[row][col]
                    if isinstance(cell, dict) and cell.get('terrain') in ok_terrain:
                        if random.random() < self.treeDensity:
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
            
            if self.gameOver and self.isInfiniteMode:
                self.drawEndGameGraph()
                return
                
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
            
            # Draw healing bursts
            self._drawHealingBursts()
            
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
    
    def endGame(self):
        """Mark game as over without drawing immediately"""
        self.gameOver = True

    def displayStatisticsGraph(self):
        # Implement the logic to display the statistics graph
        # This could involve drawing the graph on the screen using the collected statistics
        print("Displaying statistics graph...")
        # Example: Plotting the statistics using a library or custom drawing logic

    def updateCamera(self):
        charX, charY = self.character.getPosition()
        self.cameraX = charX - (self.windowWidth / (2 * self.zoomLevel))
        self.cameraY = charY - (self.windowHeight / (2 * self.zoomLevel))

    def setZoom(self, newZoom):
        self.zoomLevel = max(self.minZoom, min(self.maxZoom, newZoom))
        self.updateCamera()
    
    def drawEndGameGraph(self):
        # Clear the screen
        drawRect(0, 0, self.windowWidth, self.windowHeight, fill='black')
        
        # Draw graph title
        drawLabel('Game Statistics', self.windowWidth // 2, 30,
                fill='white', bold=True, size=24)
        
        # Set up graph dimensions
        margin = 50
        graphWidth = self.windowWidth - 2 * margin
        graphHeight = self.windowHeight - 2 * margin - 60  # Extra space for title
        
        # Draw axes
        startX = margin
        startY = self.windowHeight - margin
        
        drawLine(startX, startY, startX + graphWidth, startY, fill='white')  # X axis
        drawLine(startX, startY, startX, startY - graphHeight, fill='white')  # Y axis
        
        # Set up stats with their ranges and colors
        stats_config = {
            'deterioration': {
                'color': 'red',
                'min': 0,
                'max': 1,
                'label': 'Deterioration'
            },
            'power': {
                'color': 'yellow',
                'min': 0,
                'max': max(self.statistics['power']) if self.statistics['power'] else 1,
                'label': 'Healing Power'
            },
            'speed': {
                'color': 'green',
                'min': 0,
                'max': max(self.statistics['speed']) if self.statistics['speed'] else 1,
                'label': 'Movement Speed'
            },
            'healingRadius': {
                'color': 'blue',
                'min': 0,
                'max': max(self.statistics['healingRadius']) if self.statistics['healingRadius'] else 1,
                'label': 'Healing Radius'
            }
        }
        
        # Draw legend
        legendX = margin + 20
        legendY = margin + 30
        for stat, config in stats_config.items():
            drawRect(legendX, legendY, 20, 10, fill=config['color'])
            drawLabel(f"{config['label']} ({config['min']:.1f}-{config['max']:.1f})", 
                    legendX + 100, legendY + 5,
                    fill='white', align='left')
            legendY += 25
        
        # Plot data
        times = self.statistics['timestamps']
        if not times:
            return
            
        timeRange = times[-1] - times[0]
        
        for stat, config in stats_config.items():
            data = self.statistics[stat]
            if not data:
                continue
            
            # Plot points
            points = []
            for i in range(len(data)):
                # X coordinate based on time
                x = startX + ((times[i] - times[0]) / timeRange) * graphWidth
                
                # Y coordinate based on value range
                value_range = config['max'] - config['min']
                if value_range == 0:  # Avoid division by zero
                    normalized = 1
                else:
                    normalized = (data[i] - config['min']) / value_range
                y = startY - normalized * graphHeight
                
                points.append((x, y))
            
            # Draw connecting lines
            if len(points) > 1:
                for i in range(len(points) - 1):
                    drawLine(points[i][0], points[i][1],
                            points[i+1][0], points[i+1][1],
                            fill=config['color'],
                            lineWidth=2)
            
            # Draw value range markers on Y axis
            drawLabel(f'{config["max"]:.1f}', 
                    startX - 10, 
                    startY - graphHeight,
                    fill=config['color'],
                    align='right')
            drawLabel(f'{config["min"]:.1f}', 
                    startX - 10,
                    startY,
                    fill=config['color'],
                    align='right')
        
        # Draw time markers on X axis
        timeMarkers = [0, timeRange/2, timeRange]
        for time in timeMarkers:
            x = startX + (time / timeRange) * graphWidth
            drawLine(x, startY, x, startY + 5, fill='white')
            drawLabel(f'{int(time)}s', x, startY + 15, 
                    fill='white', align='center')
            
    #====Section debugged by Claude 3.5, very complex, mostly attempted to be written by me, but some details added by Claude====
    def drawUI(self):
        # Infinite mode
        if self.isInfiniteMode and not self.gameOver:
            # Draw end game button
            buttonWidth = 100
            buttonHeight = 30
            buttonX = self.windowWidth // 2
            buttonY = 30
            
            drawRect(buttonX - buttonWidth//2, buttonY - buttonHeight//2,
                    buttonWidth, buttonHeight,
                    fill='darkRed', border='white')
            drawLabel('End Game', buttonX, buttonY,
                    fill='white', bold=True)
        
        # Draw instructions in top left
        instructions = [
            "Controls:",
            "WASD/Arrows: Move",
            "Space: Healing Wave",
            "Shift: Sprint",
            "+/-: Zoom",
            "M: Toggle Map View",
            "ESC: Menu"
        ]
        
        # Draw instruction background
        padding = 10
        lineHeight = 20
        boxWidth = 150
        boxHeight = len(instructions) * lineHeight + padding * 2
        
        drawRect(padding, padding, boxWidth, boxHeight,
                fill='black', opacity=40)
        
        # Draw instructions
        for i, text in enumerate(instructions):
            drawLabel(text, 
                     padding + boxWidth/2, 
                     padding + lineHeight/2 + i * lineHeight,
                     fill='white', bold=True,
                     size=14)

        # Draw timer only in normal mode
        if not self.isInfiniteMode:
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

        # Draw global deterioration bar
        totalCells = 0
        deterioratedCells = 0
        for key, cell in self.textureManager.cellStates.items():
            if cell['terrain'] != 'water':
                totalCells += 1
                deterioratedCells += cell['lifeRatio']

        if totalCells > 0:
            deteriorationRatio = deterioratedCells / totalCells
            barWidth = 200
            barHeight = 20
            barX = self.windowWidth - barWidth - 20
            barY = 60
            
            # Background
            drawRect(barX, barY, barWidth, barHeight,
                    fill='darkGray')
            
            # Deterioration level
            fillWidth = barWidth * deteriorationRatio
            red = int(255 * deteriorationRatio)
            green = int(255 * (1 - deteriorationRatio))
            drawRect(barX, barY, fillWidth, barHeight,
                    fill=rgb(red, green, 0))
            
            # Border
            drawRect(barX, barY, barWidth, barHeight,
                    fill=None, border='white')
            
            # Label
            drawLabel("Global Deterioration",
                     barX + barWidth/2, barY - 10,
                     fill='white', bold=True)

        # Draw inventory (5 slots)
        slotSize = 40
        spacing = 5
        slots = 5
        barWidth = (slotSize * slots) + (spacing * (slots - 1))
        startX = self.windowWidth/2 - barWidth/2
        startY = self.windowHeight - 60
        
        # Draw inventory background
        drawRect(startX - 5, startY - 5,
                barWidth + 10, slotSize + 10,
                fill='black', opacity=40)
        
        # Draw slots and equipment
        self._drawInventorySlots(startX, startY, slotSize, spacing, slots)

        # Draw healing wave ability icon
        abilitySize = 60
        abilityX = startX - abilitySize - 20
        abilityY = startY + slotSize/2
        self._drawAbilityIcon(abilityX, abilityY, abilitySize)

        # Update game over conditions
        if not self.isInfiniteMode:
            if deteriorationRatio >= 0.8:
                self.gameOver = True
                self.gameWon = False
            elif remainingTime <= 0:
                self.gameOver = True
                self.gameWon = (deteriorationRatio < 0.8)  # Win if under 80% deterioration when time runs out
        
        # Draw game over screen if needed
        if self.gameOver:
            self._drawGameOverScreen()

    def _drawInventorySlots(self, startX, startY, slotSize, spacing, slots):
        # Draw slots
        for i in range(slots):
            x = startX + (slotSize + spacing) * i
            drawRect(x, startY, slotSize, slotSize,
                    fill='gray', opacity=30,
                    border='white', borderWidth=1)
        
        # Group equipment by type and count
        equipment_counts = {}
        for eqType, data in self.inventory.items():
            if data['count'] > 0:
                equipment_counts[eqType] = data['count']
        
        # Draw collected equipment
        currentSlot = 0
        for eqType, count in equipment_counts.items():
            if currentSlot < slots:  # Make sure we don't exceed available slots
                x = startX + (slotSize + spacing) * currentSlot
                y = startY
                
                # Draw background circle
                drawCircle(x + slotSize/2, y + slotSize/2,
                          slotSize/2 - 5,
                          fill=Equipment.TYPES[eqType]['color'],
                          opacity=40)
                
                # Draw equipment sprite if available
                if eqType in Equipment.sprites and Equipment.sprites[eqType]:
                    sprite = Equipment.sprites[eqType]
                    icon_size = slotSize * 0.8  # Slightly smaller than slot
                    drawImage(sprite,
                             x + slotSize/2 - icon_size/2,
                             y + slotSize/2 - icon_size/2,
                             width=icon_size,
                             height=icon_size)
                else:
                    # Fallback to symbol if sprite not available
                    drawLabel(Equipment.TYPES[eqType]['symbol'],
                             x + slotSize/2, y + slotSize/2,
                             fill='white', bold=True,
                             size=20)
                
                # Draw count if more than 1
                if count > 1:
                    # Draw count with background for better visibility
                    countX = x + slotSize - 10
                    countY = y + 10
                    # Draw background circle for count
                    drawCircle(countX, countY, 10,
                              fill='black', opacity=60)
                    drawLabel(str(count),
                             countX, countY,
                             fill='white', bold=True,
                             size=14)
                
                currentSlot += 1

    def _drawAbilityIcon(self, centerX, centerY, abilitySize):
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
        
        # Draw statistics graph if game is over
        if self.gameOver:
            self.drawEndGameGraph()

    def emitHealingWave(self):
        currentTime = time.time()
        if self.character.canUseHealingWave(currentTime):
            # Create healing burst effect
            self.healingBursts.append({
                'x': self.character.position['x'],
                'y': self.character.position['y'],
                'currentRadius': 0,
                'maxRadius': self.character.healingWave['maxRadius'],
                'startTime': currentTime,
                'duration': 1.0,
                'color': 'lightGreen',
                'type': 'wave',
                'healAmount': 0.2,
                'baseOpacity': 20
            })
            
            # Store the current deterioration level before healing
            currentDet = self.getCurrentDeterioration()
            
            # Apply healing through texture manager
            self.textureManager.applyGlobalHealing(0.2)
            
            # Update statistics after healing (if in infinite mode)
            if self.isInfiniteMode:
                self.statistics['deterioration'].append(self.getCurrentDeterioration())
                self.statistics['timestamps'].append(currentTime - self.startTime)
            
            # Start cooldown
            self.character.healingWave['lastUsed'] = currentTime
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
        if self.miniMapState == 'OFF':
            self.miniMapState = 'TERRAIN'
            self.miniMap.showDeterioration = False
        elif self.miniMapState == 'TERRAIN':
            self.miniMapState = 'DETERIORATION'
            self.miniMap.showDeterioration = True
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

#====Section debugged by Claude 3.5, very complex, mostly attempted to be written by me, but some details added by Claude====
    def update(self):
        """Update game state including texture deterioration and trees"""
        startRow, startCol, endRow, endCol = self.getVisibleCells()
        
        # Check for equipment collection
        self._checkEquipmentCollection()
        
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
        
        # Update healing effects
        self._updateHealingEffects()
        
        # Update trees in visible area
        for tree, (treeRow, treeCol) in self.trees:
            if (startCol-1 <= treeCol <= endCol+1 and 
                startRow-1 <= treeRow <= endRow+1):
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
        
        # Adjust equipment density for infinite mode
        density = self.equipmentDensity * 1.5 if self.isInfiniteMode else self.equipmentDensity
        
        for row in range(self.worldHeight):
            for col in range(self.worldWidth):
                try:
                    cell = self.grid[row][col]
                    if cell['terrain'] in ok_terrain and random.random() < density:
                        x = (col + 0.5) * self.baseCellWidth
                        y = (row + 0.5) * self.baseCellHeight
                        self.equipment.append(Equipment(x, y))
                        print(f"Spawned equipment at ({row}, {col})")
                except Exception as e:
                    print(f"Equipment spawn failed at {row}, {col}: {e}")
        
        print(f"Total equipment spawned: {len(self.equipment)}")

    def updateGame(self, dt):
        if not self.gameOver:
            # Remove statistics tracking from here since it's already in update()
            if not self.isInfiniteMode:
                remainingTime = self.gameTime - (time.time() - self.startTime)
                if remainingTime <= 0:
                    self.gameOver = True

    def _checkEquipmentCollection(self):
        charX, charY = self.character.getPosition()
        char_size = self.character.visual['baseSize']
        
        for equip in self.equipment[:]:
            if not equip.collected:
                dx = charX - equip.x
                dy = charY - equip.y
                
                if dx*dx + dy*dy < (char_size * char_size):
                    try:
                        equip_type = equip.type
                        bonuses = equip.getBonuses()
                        
                        equip.collected = True
                        if equip in self.equipment:
                            self.equipment.remove(equip)
                        
                        if equip_type == 'burst':
                            self._applyBurstHeal(equip.x, equip.y, bonuses)
                        else:
                            if equip_type in self.inventory:
                                self.inventory[equip_type]['count'] += 1
                                if equip_type == 'radius':
                                    # Ensure the radius bonus is applied correctly
                                    bonus = bonuses.get('radius_bonus', 1.0)  # Default bonus if not specified
                                    self.character.restorationRadiusMultiplier += bonus
                                    self.inventory[equip_type]['total_bonus'] += bonus
                                elif equip_type == 'power':
                                    bonus = bonuses.get('strength_bonus', 0.75)
                                    self.character.strength += bonus
                                    self.inventory[equip_type]['total_bonus'] += bonus
                                elif equip_type == 'speed':
                                    bonus = bonuses.get('speed_bonus', 0.2)
                                    self.character.setSpeed(self.character.speed + bonus)
                                    self.inventory[equip_type]['total_bonus'] += bonus
                    except Exception as e:
                        print(f"Error collecting equipment: {e}")
                        continue

    def _applyBurstHeal(self, x, y, bonuses):
        """Apply burst heal with reduced radius and matching visuals"""
        if 'heal_radius' not in bonuses or 'heal_amount' not in bonuses:
            print("Invalid burst bonuses")
            return
            
        radius = bonuses['heal_radius']  # Now much smaller (2 cells in each direction)
        healing = bonuses['heal_amount']
        
        # Create burst visual effect
        current_time = time.time()
        self.healingBursts.append({
            'x': x,
            'y': y,
            'currentRadius': 0,
            'maxRadius': radius * self.baseCellWidth * 2,  # Visual radius matches gameplay radius
            'startTime': current_time,
            'duration': 0.6,  # Faster animation for smaller radius
            'color': 'yellow',
            'type': 'burst',
            'healAmount': healing,
            'baseOpacity': 70
        })
        
        # Apply healing effect
        center_col = int(x / self.baseCellWidth)
        center_row = int(y / self.baseCellHeight)
        
        # Iterate through 5x5 area
        for row in range(center_row - radius, center_row + radius + 1):
            for col in range(center_col - radius, center_col + radius + 1):
                if not self._isValidCell(row, col):
                    continue
                    
                key = self.textureManager.getCellKey(row, col)
                cell = self.textureManager.cellStates.get(key)
                if cell and cell['terrain'] != 'water':
                    # Apply strong healing effect within small radius
                    cell['lifeRatio'] = max(0.0, cell['lifeRatio'] - healing)

    def _updateHealingBursts(self):
        currentTime = time.time()
        active_bursts = []
        
        for burst in self.healingBursts:
            if currentTime - burst['startTime'] < burst['duration']:
                # Update radius
                progress = (currentTime - burst['startTime']) / burst['duration']
                burst['currentRadius'] = burst['maxRadius'] * (0.5 - 0.5 * math.cos(progress * math.pi))
                active_bursts.append(burst)
                
        self.healingBursts = active_bursts

    def _drawHealingBursts(self):
        """Draw healing burst effects with appropriate sizing"""
        current_time = time.time()
        
        for burst in self.healingBursts:
            if current_time - burst['startTime'] < burst['duration']:
                progress = (current_time - burst['startTime']) / burst['duration']
                
                # Convert world to screen coordinates
                screenX, screenY = self.worldToScreen(burst['x'], burst['y'])
                
                if burst['type'] == 'burst':
                    # Create pulsing wave effect
                    wave_factor = math.sin(progress * math.pi * 3) * 0.2
                    base_radius = burst['maxRadius'] * (0.5 - 0.5 * math.cos(progress * math.pi))
                    radius = base_radius * (1 + wave_factor) * self.zoomLevel
                    
                    # Calculate opacity with wave-like pulsing
                    base_opacity = burst['baseOpacity']
                    fade = (1 - progress) * (0.7 + 0.3 * math.sin(progress * math.pi * 4))
                    opacity = base_opacity * fade
                    
                    # Draw main burst circle
                    drawCircle(screenX, screenY, radius,
                            fill=burst['color'],
                            opacity=opacity * 0.3)  # Semi-transparent fill
                    
                    # Draw ring effect
                    drawCircle(screenX, screenY, radius,
                            fill=None,
                            border=burst['color'],
                            borderWidth=max(2, min(4, self.zoomLevel)),
                            opacity=opacity)

    def drawInventory(self):
        # Inventory bar settings
        slotSize = 40
        spacing = 5
        slots = 5  # Reduced number of slots to match UI
        barWidth = (slotSize * slots) + (spacing * (slots - 1))
        startX = self.windowWidth/2 - barWidth/2  # Center the inventory
        startY = self.windowHeight - 60
        
        # inventory background
        drawRect(startX - 5, startY - 5,
                barWidth + 10, slotSize + 10,
                fill='black', opacity=40)
        
        # Draw slots and equipment
        self._drawInventorySlots(startX, startY, slotSize, spacing, slots)

    def _drawGameOverScreen(self):
        # Semi-transparent overlay
        drawRect(0, 0, self.windowWidth, self.windowHeight,
                fill='black', opacity=60)
        
        titleY = self.windowHeight / 2 - 50
        
        if self.gameWon:
            message = "Victory!"
            color = 'green'
            subMessage = "You successfully preserved the environment!"
        else:
            message = "Game Over"
            color = 'red'
            if time.time() - self.startTime >= self.gameTime:
                subMessage = "Time's up! Deterioration was too high!"
            else:
                subMessage = "The deterioration level became too high!"
        
        drawLabel(message,
                 self.windowWidth / 2, titleY,
                 fill=color, bold=True, size=36)
        
        # Sub-message
        drawLabel(subMessage,
                 self.windowWidth / 2, titleY + 50,
                 fill='white', size=20)
        
        # Instructions
        drawLabel("Press ESC to return to menu",
                 self.windowWidth / 2, titleY + 100,
                 fill='gray', size=16)
    def _spawnCharacter(self):
        """Spawn character on any walkable terrain"""
        valid_positions = []
        
        # First collect all valid positions
        for row in range(self.worldHeight):
            for col in range(self.worldWidth):
                try:
                    x = (col + 0.5) * self.baseCellWidth
                    y = (row + 0.5) * self.baseCellHeight
                    if self.isTerrainWalkable(x, y):
                        valid_positions.append((row, col))
                except Exception as e:
                    print(f"Error checking position ({row}, {col}): {e}")
                    continue
        
        if valid_positions:
            # Try positions until we find one that works
            random.shuffle(valid_positions)
            row, col = random.choice(valid_positions)
            x = (col + 0.5) * self.baseCellWidth
            y = (row + 0.5) * self.baseCellHeight
            self.character.teleport(x, y)
            print(f"Character spawned at ({row}, {col})")
            return True
        
        raise Exception("No valid spawn position found!")

    def _updateHealingEffects(self):
        active_bursts = []
        currentTime = time.time()
        
        for burst in self.healingBursts:
            progress = (currentTime - burst['startTime']) / burst['duration']
            if progress < 1.0:
                # Apply healing to cells within current radius
                centerX = burst['x']
                centerY = burst['y']
                currentRadius = burst['maxRadius'] * (0.5 - 0.5 * math.cos(progress * math.pi))
                
                # Get affected cells
                centerCol = int(centerX / self.baseCellWidth)
                centerRow = int(centerY / self.baseCellHeight)
                radius_cells = int(currentRadius / self.baseCellWidth)
                
                for row in range(centerRow - radius_cells, centerRow + radius_cells + 1):
                    for col in range(centerCol - radius_cells, centerCol + radius_cells + 1):
                        if not self._isValidCell(row, col):
                            continue
                            
                        cellX = (col + 0.5) * self.baseCellWidth
                        cellY = (row + 0.5) * self.baseCellHeight
                        dx = cellX - centerX
                        dy = cellY - centerY
                        
                        if (dx*dx + dy*dy) <= currentRadius*currentRadius:
                            key = self.textureManager.getCellKey(row, col)
                            cell = self.textureManager.cellStates.get(key)
                            if cell and cell['terrain'] != 'water':
                                # Apply healing with power bonus
                                cell['lifeRatio'] = max(0.0, cell['lifeRatio'] - burst['healAmount'])
                
                burst['currentRadius'] = currentRadius
                active_bursts.append(burst)
        
        self.healingBursts = active_bursts

    def getCurrentDeterioration(self):
        """Calculate current average deterioration level across the map"""
        totalDet = 0.0
        count = 0
        
        for key, cell in self.textureManager.cellStates.items():
            if cell['terrain'] != 'water':
                totalDet += cell['lifeRatio']
                count += 1
        
        return totalDet / max(1, count)  # Returns value between 0 and 1

    def isEndGameButtonClicked(self, mouseX, mouseY):
        if self.isInfiniteMode and not self.gameOver:
            buttonWidth = 100
            buttonHeight = 30
            buttonX = self.windowWidth // 2
            buttonY = 30
            
            # Check if click is within button bounds
            return (abs(mouseX - buttonX) <= buttonWidth//2 and 
                    abs(mouseY - buttonY) <= buttonHeight//2)
        return False
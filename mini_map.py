from cmu_graphics import *
import numpy as np
from dataclasses import dataclass

'''
====MinimapCache Implementation Guide:Provided by Claude 3.5====

 MinimapCache Implementation Guide:
 1. Initialize cache in minimap constructor:
    - Create cache instance when minimap is created
    - Cache stores terrain colors, deterioration values, viewport, and player position

 2. Update cache strategically:
    - Update terrainColors when map terrain changes
    - Update deteriorationColors when terrain health changes
    - Update viewport/playerPos every frame for real-time movement

 3. Use cache for drawing:
    - Draw terrain/deterioration from cached colors instead of recalculating
    - Use cached viewport/player position for overlay elements

 4. Performance benefits:
    - Avoid recalculating static elements (terrain) every frame
    - Only update cache when source data changes
    - Separate storage from rendering logic
'''

#====MinimapCache Implementation:Provided by Claude 3.5====
class MinimapCache:
    def __init__(self, terrainColors=None, deteriorationColors=None, terrainUpdated=0, viewport=None, playerPos=None):
        self.terrainColors = terrainColors
        self.deteriorationColors = deteriorationColors
        self.terrainUpdated = terrainUpdated
        self.viewport = viewport
        self.playerPos = playerPos
        
    def __repr__(self):
        return f"MinimapCache(terrainColors={self.terrainColors}, deteriorationColors={self.deteriorationColors}, ...)"
        
    def __eq__(self, other):
        if not isinstance(other, MinimapCache):
            return NotImplemented
        return (self.terrainColors == other.terrainColors and 
                self.deteriorationColors == other.deteriorationColors and ...)
#====MinimapCache Implementation:Provided by Claude 3.5====

class MiniMap:
    def __init__(self, windowWidth, windowHeight, worldWidth, worldHeight,
                 cellWidth, cellHeight, colorMap):
        self.windowWidth = windowWidth
        self.windowHeight = windowHeight
        self.worldWidth = worldWidth
        self.worldHeight = worldHeight
        self.cellWidth = cellWidth
        self.cellHeight = cellHeight
        self.showDeterioration = False
        
        self.resolution = {
            'scale': 8,
            'rows': (worldHeight + 7) // 8,
            'cols': (worldWidth + 7) // 8
        }
        
        self.size = {
            'width': 240,
            'height': 180,
            'margin': 10
        }
        
        self.position = {
            'x': windowWidth - self.size['width'] - self.size['margin'],
            'y': windowHeight - self.size['height'] - self.size['margin']
        }
        
        self.style = {
            'border': {'color': 'black', 'width': 2},
            'player': {'color': 'red', 'size': 3},
            'viewport': {'color': 'white', 'width': 1, 'opacity': 50}
        }
        
        self.colors = colorMap
        self.cache = MinimapCache()
        
        self.scale = {
            'x': self.size['width'] / worldWidth,
            'y': self.size['height'] / worldHeight
        }
        
        self.precalculate()

    def precalculate(self):
        self.cellDims = {
            'width': self.size['width'] / self.worldWidth,
            'height': self.size['height'] / self.worldHeight
        }
        self.scaledCell = {
            'width': self.size['width'] / self.resolution['cols'],
            'height': self.size['height'] / self.resolution['rows']
        }

    def updateGrid(self, grid):
        if grid is None:
            return
            
        rows = self.resolution['rows']
        cols = self.resolution['cols']
        colors = np.empty((rows, cols), dtype='U20')
        deterioration = np.zeros((rows, cols))
        
        try:
            for i in range(rows):
                for j in range(cols):
                    gridI = min(i * self.resolution['scale'], len(grid) - 1)
                    gridJ = min(j * self.resolution['scale'], len(grid[0]) - 1)
                    
                    terrain = grid[gridI][gridJ]['terrain']
                    colors[i, j] = self.colors.get(terrain, 'gray')
                    
            self.cache.terrainColors = colors
            self.cache.deteriorationColors = deterioration
        except Exception as e:
            print(f"Error updating minimap grid: {e}")

    def update(self, viewport, playerPos, textureManager=None):
        self.cache.viewport = viewport
        self.cache.playerPos = playerPos
        if textureManager and self.cache.deteriorationColors is not None:
            try:
                # Get global deterioration value
                globalDeterioration = textureManager.calculateGlobalDeterioration()
                
                # Calculate scale factors to map entire world to minimap resolution
                scaleY = self.worldHeight / self.resolution['rows']
                scaleX = self.worldWidth / self.resolution['cols']
                
                for i in range(self.resolution['rows']):
                    for j in range(self.resolution['cols']):
                        # Map minimap coordinates to world coordinates
                        worldY = int(i * scaleY)
                        worldX = int(j * scaleX)
                        
                        # Ensure we stay within world bounds
                        worldY = min(worldY, self.worldHeight - 1)
                        worldX = min(worldX, self.worldWidth - 1)
                        
                        # Get cell state for this world position
                        key = f"{worldY},{worldX}"
                        state = textureManager.cellStates.get(key)
                        
                        if state and state['terrain'] != 'water':
                            # Use actual deterioration value
                            self.cache.deteriorationColors[i, j] = state['lifeRatio']
                        else:
                            # Water or invalid cells get 0 deterioration
                            self.cache.deteriorationColors[i, j] = 0.0
                            
            except Exception as e:
                print(f"Error updating deterioration: {e}")

    def drawBackground(self):
        drawRect(
            self.position['x'] - self.style['border']['width'],
            self.position['y'] - self.style['border']['width'],
            self.size['width'] + 2 * self.style['border']['width'],
            self.size['height'] + 2 * self.style['border']['width'],
            fill=self.style['border']['color']
        )
        
        drawRect(
            self.position['x'],
            self.position['y'],
            self.size['width'],
            self.size['height'],
            fill='white'
        )

    def worldToMinimap(self, worldX, worldY):
        miniX = self.position['x'] + (worldX * self.scale['x'])
        miniY = self.position['y'] + (worldY * self.scale['y'])
        return miniX, miniY

    def drawViewport(self):
        if self.cache.viewport is None:
            return
        startRow, startCol, endRow, endCol = self.cache.viewport
        startX, startY = self.worldToMinimap(startCol, startRow)
        endX, endY = self.worldToMinimap(endCol, endRow)
        drawRect(startX, startY, endX - startX, endY - startY,
                fill=None, 
                border=self.style['viewport']['color'],
                borderWidth=self.style['viewport']['width'],
                opacity=self.style['viewport']['opacity'])

    def drawPlayer(self):
        if self.cache.playerPos is None:
            return
        charX, charY = self.cache.playerPos
        miniX, miniY = self.worldToMinimap(charX/self.cellWidth, charY/self.cellHeight)
        drawCircle(miniX, miniY, self.style['player']['size'], 
                  fill=self.style['player']['color'])

    def drawContent(self):
        if self.showDeterioration:
            self._drawDeteriorationView()
        else:
            self._drawTerrainView()

    def _drawTerrainView(self):
        if self.cache.terrainColors is None:
            return
            
        for i in range(self.resolution['rows']):
            for j in range(self.resolution['cols']):
                x = self.position['x'] + j * self.scaledCell['width']
                y = self.position['y'] + i * self.scaledCell['height']
                drawRect(x, y, 
                        self.scaledCell['width'], self.scaledCell['height'],
                        fill=self.cache.terrainColors[i, j])

    def _drawDeteriorationView(self):
        if self.cache.deteriorationColors is None:
            return
            
        for i in range(self.resolution['rows']):
            for j in range(self.resolution['cols']):
                x = self.position['x'] + j * self.scaledCell['width']
                y = self.position['y'] + i * self.scaledCell['height']
                ratio = self.cache.deteriorationColors[i, j]
                
                # More red for higher deterioration, more green for lower
                red = int(255 * ratio)  # Red increases with deterioration
                green = int(255 * (1 - ratio))  # Green decreases with deterioration
                blue = 0
                
                drawRect(x, y, 
                        self.scaledCell['width'], self.scaledCell['height'],
                        fill=rgb(red, green, blue))

    def draw(self):
        try:
            self.drawBackground()
            self.drawContent()
            self.drawViewport()
            self.drawPlayer()
            
            # Draw toggle instruction
            instructionY = self.position['y'] + self.size['height'] + 15
            drawLabel("Press M to toggle map view",
                     self.position['x'] + self.size['width']/2,
                     instructionY,
                     fill='white', bold=True,
                     size=14)
                 
        except Exception as e:
            print(f"Error drawing minimap: {e}")
            drawRect(self.position['x'], self.position['y'],
                    self.size['width'], self.size['height'],
                    fill='red', opacity=50)

    def setMode(self, showDeterioration):
        self.showDeterioration = showDeterioration
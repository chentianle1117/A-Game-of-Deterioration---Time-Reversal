from cmu_graphics import *
import numpy as np
from dataclasses import dataclass

@dataclass
class MinimapCache:
    terrainColors: np.ndarray = None
    deteriorationColors: np.ndarray = None
    terrainUpdated: float = 0
    viewport: tuple = None
    playerPos: tuple = None

class MiniMap:
    def __init__(self, windowWidth, windowHeight, worldWidth, worldHeight,
                 cellWidth, cellHeight, colorMap):
        self.windowWidth = windowWidth
        self.windowHeight = windowHeight
        self.worldWidth = worldWidth
        self.worldHeight = worldHeight
        self.cellWidth = cellWidth
        self.cellHeight = cellHeight
        self.showDeterioration = False  # Toggle between modes

        # Define minimap dimensions (more scaled down)
        self.resolution = {
            'scale': 8,  # Increased scale factor for lower resolution
            'rows': (worldHeight + 7) // 8,
            'cols': (worldWidth + 7) // 8
        }
        
        self.size = {
            'width': 160,
            'height': 120,
            'margin': 10
        }
        
        # Position in bottom-right corner
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
        
        # Calculate scaling factors
        self.scale = {
            'x': self.size['width'] / worldWidth,
            'y': self.size['height'] / worldHeight
        }
        
        self.precalculate()

    def precalculate(self):
        """Precalculate cell dimensions for rendering"""
        self.cellDims = {
            'width': self.size['width'] / self.worldWidth,
            'height': self.size['height'] / self.worldHeight
        }
        self.scaledCell = {
            'width': self.size['width'] / self.resolution['cols'],
            'height': self.size['height'] / self.resolution['rows']
        }

    def updateGrid(self, grid):
        """Update both terrain colors and initialize deterioration states"""
        if grid is None:
            return
            
        rows = self.resolution['rows']
        cols = self.resolution['cols']
        colors = np.empty((rows, cols), dtype='U20')
        deterioration = np.zeros((rows, cols))  # Start all cells fresh (white)
        
        try:
            for i in range(rows):
                for j in range(cols):
                    # Calculate corresponding position in full grid
                    gridI = min(i * self.resolution['scale'], len(grid) - 1)
                    gridJ = min(j * self.resolution['scale'], len(grid[0]) - 1)
                    
                    # Get terrain color
                    terrain = grid[gridI][gridJ]['terrain']
                    colors[i, j] = self.colors.get(terrain, 'gray')
                    
            self.cache.terrainColors = colors
            self.cache.deteriorationColors = deterioration
        except Exception as e:
            print(f"Error updating minimap grid: {e}")

    def update(self, viewport, playerPos, textureManager=None):
            """Update minimap state including deterioration if needed"""
            self.cache.viewport = viewport
            self.cache.playerPos = playerPos
            
            # Always update deterioration data
            if textureManager and self.cache.deteriorationColors is not None:
                try:
                    # Update each minimap cell
                    for i in range(self.resolution['rows']):
                        for j in range(self.resolution['cols']):
                            # Get a sample from the center of this minimap cell
                            baseGridI = i * self.resolution['scale']
                            baseGridJ = j * self.resolution['scale']
                            
                            # Sample multiple points in the full grid for this minimap cell
                            samplePoints = []
                            for di in range(self.resolution['scale']):
                                for dj in range(self.resolution['scale']):
                                    gridI = min(baseGridI + di, self.worldHeight - 1)
                                    gridJ = min(baseGridJ + dj, self.worldWidth - 1)
                                    stats = textureManager.getTerrainStats(gridI, gridJ)
                                    if stats:
                                        samplePoints.append(stats['lifeRatio'])
                            
                            # Average the deterioration values for this cell
                            if samplePoints:
                                self.cache.deteriorationColors[i, j] = sum(samplePoints) / len(samplePoints)
                except Exception as e:
                    print(f"Error updating deterioration: {e}")

    def drawBackground(self):
        """Draw minimap background and border"""
        # Draw border
        drawRect(
            self.position['x'] - self.style['border']['width'],
            self.position['y'] - self.style['border']['width'],
            self.size['width'] + 2 * self.style['border']['width'],
            self.size['height'] + 2 * self.style['border']['width'],
            fill=self.style['border']['color']
        )
        
        # Draw background
        drawRect(
            self.position['x'],
            self.position['y'],
            self.size['width'],
            self.size['height'],
            fill='white'
        )

    def worldToMinimap(self, worldX, worldY):
        """Convert world coordinates to minimap coordinates"""
        miniX = self.position['x'] + (worldX * self.scale['x'])
        miniY = self.position['y'] + (worldY * self.scale['y'])
        return miniX, miniY

    def drawViewport(self):
        """Draw current view window"""
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
        """Draw player position"""
        if self.cache.playerPos is None:
            return
        charX, charY = self.cache.playerPos
        miniX, miniY = self.worldToMinimap(charX/self.cellWidth, charY/self.cellHeight)
        drawCircle(miniX, miniY, self.style['player']['size'], 
                  fill=self.style['player']['color'])

    def drawContent(self):
        """Draw the terrain or deterioration content"""
        if self.showDeterioration:
            self._drawDeteriorationView()
        else:
            self._drawTerrainView()

    def _drawTerrainView(self):
        """Draw terrain colors"""
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
        """Draw deterioration levels with improved color mapping"""
        if self.cache.deteriorationColors is None:
            return
            
        for i in range(self.resolution['rows']):
            for j in range(self.resolution['cols']):
                x = self.position['x'] + j * self.scaledCell['width']
                y = self.position['y'] + i * self.scaledCell['height']
                ratio = self.cache.deteriorationColors[i, j]
                
                # Create smooth white-to-red gradient
                red = 255
                green = blue = int(255 * (1 - ratio))
                color = rgb(red, green, blue)
                
                drawRect(x, y, 
                        self.scaledCell['width'], self.scaledCell['height'],
                        fill=color)

    def draw(self):
        """Draw the complete minimap"""
        try:
            self.drawBackground()
            self.drawContent()
            self.drawViewport()
            #self.drawPlayer()
        except Exception as e:
            print(f"Error drawing minimap: {e}")
            drawRect(self.position['x'], self.position['y'],
                    self.size['width'], self.size['height'],
                    fill='red', opacity=50)

    def setMode(self, showDeterioration):
        """Set the display mode"""
        self.showDeterioration = showDeterioration
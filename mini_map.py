from cmu_graphics import *
import numpy as np
from dataclasses import dataclass

@dataclass
class MinimapCache:
    terrainColors: np.ndarray = None
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
        self.size = {
            'width': 160,
            'height': 120,
            'margin': 10
        }
        self.position = {
            'x': windowWidth - self.size['width'] - self.size['margin'],
            'y': self.size['margin']
        }
        self.style = {
            'border': {'color': 'black', 'width': 2},
            'player': {'color': 'red', 'size': 3},
            'viewport': {'color': 'white', 'width': 1, 'opacity': 50}
        }
        self.resolution = {
            'scale': 4,
            'rows': (worldHeight + 3) // 4,
            'cols': (worldWidth + 3) // 4
        }
        self.scale = {
            'x': self.size['width'] / worldWidth,
            'y': self.size['height'] / worldHeight
        }
        self.colors = colorMap
        self.cache = MinimapCache()
        self.precalculate()

    def precalculate(self):
        self.cellDims = {
            'width': self.size['width'] / self.worldWidth,
            'height': self.size['height'] / self.worldHeight
        }
        self.scaledCell = {
            'width': self.cellDims['width'] * self.resolution['scale'] + 1,
            'height': self.cellDims['height'] * self.resolution['scale'] + 1
        }

    def updateGrid(self, grid):
        if grid is None:
            return
        rows = self.resolution['rows']
        cols = self.resolution['cols']
        colors = np.empty((rows, cols), dtype='U20')
        try:
            for i in range(rows):
                for j in range(cols):
                    gridI = min(i * self.resolution['scale'], len(grid) - 1)
                    gridJ = min(j * self.resolution['scale'], len(grid[0]) - 1)
                    terrain = grid[gridI][gridJ]['terrain']
                    colors[i, j] = self.colors.get(terrain, 'gray')
            self.cache.terrainColors = colors
        except Exception as e:
            print(f"Error updating minimap grid: {e}")

    def update(self, viewport, playerPos):
        self.cache.viewport = viewport
        self.cache.playerPos = playerPos

    def worldToMinimap(self, worldX, worldY):
        miniX = self.position['x'] + (worldX * self.scale['x'])
        miniY = self.position['y'] + (worldY * self.scale['y'])
        return float(miniX), float(miniY)

    def drawBackground(self):
        drawRect(
            self.position['x'] - self.style['border']['width'],
            self.position['y'] - self.style['border']['width'],
            self.size['width'] + 2 * self.style['border']['width'],
            self.size['height'] + 2 * self.style['border']['width'],
            fill=self.style['border']['color']
        )

    def drawTerrain(self):
        if self.cache.terrainColors is None:
            return
        baseX = self.position['x']
        baseY = self.position['y']
        for i in range(len(self.cache.terrainColors)):
            for j in range(len(self.cache.terrainColors[0])):
                x = baseX + j * self.scaledCell['width']
                y = baseY + i * self.scaledCell['height']
                drawRect(x, y, self.scaledCell['width'], self.scaledCell['height'], fill=self.cache.terrainColors[i, j])

    def drawPlayer(self):
        if self.cache.playerPos is None:
            return
        charX, charY = self.cache.playerPos
        miniX, miniY = self.worldToMinimap(charX/self.cellWidth, charY/self.cellHeight)
        drawCircle(miniX, miniY, self.style['player']['size'], fill=self.style['player']['color'])

    def drawViewport(self):
        if self.cache.viewport is None:
            return
        startRow, startCol, endRow, endCol = self.cache.viewport
        startX, startY = self.worldToMinimap(startCol, startRow)
        endX, endY = self.worldToMinimap(endCol, endRow)
        drawRect(startX, startY, endX - startX, endY - startY, fill=None, border=self.style['viewport']['color'], borderWidth=self.style['viewport']['width'], opacity=self.style['viewport']['opacity'])

    def draw(self):
        try:
            self.drawBackground()
            self.drawTerrain()
            self.drawViewport()
            self.drawPlayer()
        except Exception as e:
            print(f"Error drawing minimap: {e}")
            drawRect(self.position['x'], self.position['y'], self.size['width'], self.size['height'], fill='red', opacity=50)

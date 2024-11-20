from cmu_graphics import *
import math

class Character:
    def __init__(self, worldWidth, worldHeight, cellWidth, cellHeight):
        self.worldWidth = worldWidth
        self.worldHeight = worldHeight
        self.cellWidth = cellWidth
        self.cellHeight = cellHeight
        self.worldBounds = {
            'left': 0,
            'right': worldWidth * cellWidth,
            'top': 0,
            'bottom': worldHeight * cellHeight
        }
        self.position = {
            'x': (worldWidth * cellWidth) // 2,
            'y': (worldHeight * cellHeight) // 2
        }
        self.direction = 'down'
        self.speed = 2.5
        self.colors = {
            'body': 'red',
            'outline': 'darkRed',
            'direction': 'white'
        }
        self.visual = {
            'baseSize': min(cellWidth, cellHeight) * 0.4,
            'outlineWidth': 1,
            'directionLength': 0.7
        }

    def getPosition(self):
        return self.position['x'], self.position['y']

    def getCurrentCell(self):
        col = int(self.position['x'] / self.cellWidth)
        row = int(self.position['y'] / self.cellHeight)
        if (0 <= row < self.worldHeight and 
            0 <= col < self.worldWidth):
            return row, col
        return None

    def move(self, dx, dy):
        scaledSpeed = self.speed * (self.cellWidth / 20)
        newX = self.position['x'] + (dx * scaledSpeed)
        newY = self.position['y'] + (dy * scaledSpeed)
        padding = self.visual['baseSize']
        newX = max(padding, min(newX, self.worldBounds['right'] - padding))
        newY = max(padding, min(newY, self.worldBounds['bottom'] - padding))
        self.position['x'] = newX
        self.position['y'] = newY

    def draw(self, screenX, screenY, zoomLevel):
        minSize = 3
        size = max(minSize, self.visual['baseSize'] * zoomLevel)
        outlineWidth = max(1, min(self.visual['outlineWidth'] * zoomLevel, 3))
        drawCircle(screenX, screenY, size / 2,
                   fill=self.colors['body'],
                   border=self.colors['outline'],
                   borderWidth=outlineWidth)
        indicatorLength = size * self.visual['directionLength']
        endX, endY = screenX, screenY
        if self.direction == 'right':
            endX += indicatorLength
        elif self.direction == 'left':
            endX -= indicatorLength
        elif self.direction == 'down':
            endY += indicatorLength
        elif self.direction == 'up':
            endY -= indicatorLength
        lineWidth = max(1, min(math.ceil(zoomLevel), 3))
        drawLine(screenX, screenY, endX, endY,
                 fill=self.colors['direction'],
                 lineWidth=lineWidth)
        dotSize = max(1, size * 0.15)
        drawCircle(endX, endY, dotSize,
                   fill=self.colors['direction'])

    def teleport(self, x, y):
        self.position['x'] = max(self.visual['baseSize'],
                                 min(x, self.worldBounds['right'] - self.visual['baseSize']))
        self.position['y'] = max(self.visual['baseSize'],
                                 min(y, self.worldBounds['bottom'] - self.visual['baseSize']))

    def getBounds(self):
        size = self.visual['baseSize']
        return {
            'left': self.position['x'] - size / 2,
            'right': self.position['x'] + size / 2,
            'top': self.position['y'] - size / 2,
            'bottom': self.position['y'] + size / 2
        }

    def setSpeed(self, speed):
        self.speed = max(1, min(speed, 20))

    def getInfo(self):
        return {
            'position': self.position,
            'cell': self.getCurrentCell(),
            'direction': self.direction,
            'speed': self.speed
        }

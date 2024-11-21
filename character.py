from cmu_graphics import *
import math

class Character:
    def __init__(self, worldWidth, worldHeight, cellWidth, cellHeight):
        # World parameters
        self.worldWidth = worldWidth
        self.worldHeight = worldHeight
        self.cellWidth = cellWidth
        self.cellHeight = cellHeight
        
        # World boundaries
        self.worldBounds = {
            'left': 0,
            'right': worldWidth * cellWidth,
            'top': 0,
            'bottom': worldHeight * cellHeight
        }
        
        # Character state
        self.position = {
            'x': (worldWidth * cellWidth) // 2,
            'y': (worldHeight * cellHeight) // 2
        }
        self.direction = 'down'
        self.speed = 2.5
        
        # Character abilities
        self.strength = 1.0  # Base restoration strength
        self.maxStrength = 5.0
        self.minStrength = 0.0
        self.restorationRadiusMultiplier = 20  # Base pixels per strength point
        
        # Visual properties
        self.colors = {
            'body': 'red',
            'outline': 'darkRed',
            'direction': 'white',
            'restoration': 'lightBlue',
            'strength_high': 'lightGreen',
            'strength_low': 'yellow'
        }
        
        self.visual = {
            'baseSize': min(cellWidth, cellHeight) * 0.4,
            'outlineWidth': 1,
            'directionLength': 0.7,
            'strengthIndicatorHeight': 4,
            'restoreEffectOpacity': 80
        }

        # Animation state
        self.animationFrame = 0
        self.animationSpeed = 0.1
        self.isMoving = False
        
    def getPosition(self):
        """Returns the current position as (x, y) coordinates"""
        return self.position['x'], self.position['y']

    def getCurrentCell(self):
        """Returns the current cell coordinates (row, col) or None if out of bounds"""
        col = int(self.position['x'] / self.cellWidth)
        row = int(self.position['y'] / self.cellHeight)
        if (0 <= row < self.worldHeight and 
            0 <= col < self.worldWidth):
            return row, col
        return None

    def move(self, dx, dy):
        """Moves the character by the given delta, respecting world bounds"""
        # Update movement state
        self.isMoving = dx != 0 or dy != 0
        
        # Calculate new position
        scaledSpeed = self.speed * (self.cellWidth / 20)
        newX = self.position['x'] + (dx * scaledSpeed)
        newY = self.position['y'] + (dy * scaledSpeed)
        
        # Apply bounds
        padding = self.visual['baseSize']
        newX = max(padding, min(newX, self.worldBounds['right'] - padding))
        newY = max(padding, min(newY, self.worldBounds['bottom'] - padding))
        
        # Update position
        self.position['x'] = newX
        self.position['y'] = newY
        
        # Update animation
        if self.isMoving:
            self.animationFrame += self.animationSpeed

    def draw(self, screenX, screenY, zoomLevel):
        """Draws the character and all associated visual elements"""
        self._drawRestorationRadius(screenX, screenY, zoomLevel)
        self._drawCharacterBody(screenX, screenY, zoomLevel)
        self._drawDirectionIndicator(screenX, screenY, zoomLevel)
        self._drawStrengthIndicator(screenX, screenY, zoomLevel)

    def _drawRestorationRadius(self, screenX, screenY, zoomLevel):
        """Draws the restoration effect radius"""
        radiusSize = self.getRestorationRadius() * zoomLevel
        # Draw outer circle
        drawCircle(screenX, screenY, radiusSize,
                  fill=None,
                  border=self.colors['restoration'],
                  borderWidth=2,
                  opacity=self.visual['restoreEffectOpacity'])
        # Draw inner pulse effect
        pulseSize = radiusSize * (0.8 + 0.2 * math.sin(self.animationFrame))
        drawCircle(screenX, screenY, pulseSize,
                  fill=None,
                  border=self.colors['restoration'],
                  borderWidth=1,
                  opacity=self.visual['restoreEffectOpacity'] * 0.5)

    def _drawCharacterBody(self, screenX, screenY, zoomLevel):
        """Draws the main character body"""
        minSize = 3
        size = max(minSize, self.visual['baseSize'] * zoomLevel)
        outlineWidth = max(1, min(self.visual['outlineWidth'] * zoomLevel, 3))
        
        # Add slight bobbing effect when moving
        if self.isMoving:
            screenY += math.sin(self.animationFrame * 4) * 2
            
        drawCircle(screenX, screenY, size / 2,
                  fill=self.colors['body'],
                  border=self.colors['outline'],
                  borderWidth=outlineWidth)

    def _drawDirectionIndicator(self, screenX, screenY, zoomLevel):
        """Draws the direction indicator"""
        minSize = 3
        size = max(minSize, self.visual['baseSize'] * zoomLevel)
        indicatorLength = size * self.visual['directionLength']
        
        # Calculate endpoint based on direction
        endX, endY = screenX, screenY
        if self.direction == 'right':
            endX += indicatorLength
        elif self.direction == 'left':
            endX -= indicatorLength
        elif self.direction == 'down':
            endY += indicatorLength
        elif self.direction == 'up':
            endY -= indicatorLength
            
        # Draw direction line and endpoint dot
        lineWidth = max(1, min(math.ceil(zoomLevel), 3))
        drawLine(screenX, screenY, endX, endY,
                fill=self.colors['direction'],
                lineWidth=lineWidth)
        dotSize = max(1, size * 0.15)
        drawCircle(endX, endY, dotSize,
                  fill=self.colors['direction'])

    def _drawStrengthIndicator(self, screenX, screenY, zoomLevel):
        """Draws the strength indicator"""
        minSize = 3
        size = max(minSize, self.visual['baseSize'] * zoomLevel)
        
        # Draw strength value
        strengthText = f"Strength: {self.strength:.1f}"
        drawLabel(strengthText, 
                 screenX, screenY - size - 10,
                 fill='white',
                 bold=True,
                 border='black',
                 borderWidth=1)
        
        # Draw strength bar
        barWidth = size * 2
        barHeight = self.visual['strengthIndicatorHeight']
        barX = screenX - barWidth / 2
        barY = screenY - size - 5
        
        # Background bar
        drawRect(barX, barY, barWidth, barHeight,
                fill='gray', opacity=50)
        
        # Strength fill bar
        fillWidth = barWidth * (self.strength / self.maxStrength)
        fillColor = (self.colors['strength_high'] if self.strength > self.maxStrength / 2 
                    else self.colors['strength_low'])
        drawRect(barX, barY, fillWidth, barHeight,
                fill=fillColor)

    def setStrength(self, strength):
        """Sets the character's restoration strength within bounds"""
        self.strength = max(self.minStrength, min(self.maxStrength, strength))

    def getRestorationRadius(self):
        """Returns the current restoration effect radius"""
        return self.strength * self.restorationRadiusMultiplier

    def teleport(self, x, y):
        """Instantly moves character to given coordinates, respecting world bounds"""
        self.position['x'] = max(self.visual['baseSize'],
                               min(x, self.worldBounds['right'] - self.visual['baseSize']))
        self.position['y'] = max(self.visual['baseSize'],
                               min(y, self.worldBounds['bottom'] - self.visual['baseSize']))

    def getBounds(self):
        """Returns the character's collision bounds"""
        size = self.visual['baseSize']
        return {
            'left': self.position['x'] - size / 2,
            'right': self.position['x'] + size / 2,
            'top': self.position['y'] - size / 2,
            'bottom': self.position['y'] + size / 2
        }

    def setSpeed(self, speed):
        """Sets the character's movement speed within bounds"""
        self.speed = max(1, min(speed, 20))

    def getInfo(self):
        """Returns a dictionary of character state information"""
        return {
            'position': self.position,
            'cell': self.getCurrentCell(),
            'direction': self.direction,
            'speed': self.speed,
            'strength': self.strength,
            'restorationRadius': self.getRestorationRadius()
        }

    def updateAnimation(self, dt=1):
        """Updates animation state"""
        if self.isMoving:
            self.animationFrame += self.animationSpeed * dt
        self.isMoving = False  # Reset movement state
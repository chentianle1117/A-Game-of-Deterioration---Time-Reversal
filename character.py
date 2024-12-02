from cmu_graphics import *
import math

class Character:
    def __init__(self, worldWidth, worldHeight, cellWidth, cellHeight):
        self.worldWidth = worldWidth
        self.worldHeight = worldHeight
        self.cellWidth = cellWidth
        self.cellHeight = cellHeight
        
        self.worldBounds = {
            'left': 0, 'right': worldWidth * cellWidth,
            'top': 0, 'bottom': worldHeight * cellHeight
        }
        
        self.visual = {
            'baseSize': min(cellWidth, cellHeight) * 0.4,
            'outlineWidth': 2,
            'directionLength': 0.7,
            'strengthIndicatorHeight': 4,
            'restoreEffectOpacity': 80,
            'spriteSize': min(cellWidth, cellHeight) * 1.5  # Add sprite size here
        }

        # Add sprite loading with detailed logging
        try:
            spritePath = 'assets/objects/characters/'
            print(f"\nInitializing character sprites from: {spritePath}")
            
            self.sprites = {}
            sprite_files = {
                'down': 'Char1_front.png',
                'up': 'Char1_back.png',
                'left': 'Char1_left.png',
                'right': 'Char1_right.png'
            }
            
            for direction, filename in sprite_files.items():
                full_path = f'{spritePath}{filename}'
                print(f"Loading {direction} sprite: {full_path}")
                try:
                    self.sprites[direction] = CMUImage(full_path)
                    print(f"✓ Successfully loaded {direction} sprite")
                except Exception as e:
                    print(f"✗ Failed to load {direction} sprite: {e}")
                    self.sprites[direction] = None
                
        except Exception as e:
            print(f"Error during sprite initialization: {e}")
            self.sprites = None
        
        # Rest of the initialization remains the same
        self.position = {
            'x': (worldWidth * cellWidth) // 2,
            'y': (worldHeight * cellHeight) // 2
        }
        self.direction = 'down'
        self.speed = 2.5
        
        self.strength = 0.1
        self.maxStrength = 5.0
        self.minStrength = 1.0
        self.restorationRadiusMultiplier = 15
        
        self.colors = {
            'body': 'red',
            'outline': 'darkRed',
            'direction': 'white',
            'restoration': 'lightBlue',
            'strength_high': 'lightGreen',
            'strength_low': 'yellow'
        }
        
        self.animationFrame = 0
        self.animationSpeed = 0.1
        self.isMoving = False
        
        self.healingWave = {
            'isActive': False,
            'cooldown': 10,  
            'lastUsed': 0,
            'healAmount': 0.05,
            'radius': 0,
            'maxRadius': math.sqrt(worldWidth**2 + worldHeight**2) * max(cellWidth, cellHeight),
            'expansionSpeed': 5
        }

    def emitHealingWave(self, currentTime):
        if self.canUseHealingWave(currentTime):
            self.healingWave['lastUsed'] = currentTime
            self.healingWave['isActive'] = True
            self.healingWave['radius'] = 0
            return True
        return False

    def updateAnimation(self, dt=1):
        if self.isMoving:
            self.animationFrame += self.animationSpeed * dt
        self.isMoving = False
        self.updateHealingWave()

    def canUseHealingWave(self, currentTime):
        return currentTime - self.healingWave['lastUsed'] >= self.healingWave['cooldown']

    def getHealingWaveCooldown(self, currentTime):
        return max(0, self.healingWave['cooldown'] - (currentTime - self.healingWave['lastUsed']))
        
    def getPosition(self):
        return self.position['x'], self.position['y']

    def getCurrentCell(self):
        col = int(self.position['x'] / self.cellWidth)
        row = int(self.position['y'] / self.cellHeight)
        if 0 <= row < self.worldHeight and 0 <= col < self.worldWidth:
            return row, col
        return None
    
    def updateHealingWave(self):
        if self.healingWave['isActive']:
            self.healingWave['radius'] += self.healingWave['expansionSpeed']
            if self.healingWave['radius'] >= self.healingWave['maxRadius']:
                self.healingWave['isActive'] = False
                self.healingWave['radius'] = 0
                
    def move(self, game, dx, dy):
        if dx == 0 and dy == 0:
            self.isMoving = False
            return False
        
        # Update direction based on movement
        if abs(dx) > abs(dy):
            self.direction = 'right' if dx > 0 else 'left'
        else:
            self.direction = 'down' if dy > 0 else 'up'
            
        newX = self.position['x'] + dx * self.speed
        newY = self.position['y'] + dy * self.speed
        
        # Check if new position is walkable
        if self.canMoveTo(game, newX, newY):
            self.position['x'] = newX
            self.position['y'] = newY
            self.isMoving = True
            return True
            
        self.isMoving = False
        return False
        return False

    def draw(self, screenX, screenY, zoomLevel):
        try:
            # Draw passive healing radius first (underneath everything)
            radius = self.getRestorationRadius() * zoomLevel
            
            # Main circle with higher opacity
            drawCircle(screenX, screenY, radius,
                    fill=self.colors['restoration'],
                    opacity=40)  # Increased from previous value
            
            # Add a border to make it more visible
            drawCircle(screenX, screenY, radius,
                    fill=None,
                    border=self.colors['restoration'],
                    borderWidth=2,
                    opacity=60)
            
            # Pulsing effect
            pulseRadius = radius * (0.8 + 0.2 * math.sin(self.animationFrame))
            drawCircle(screenX, screenY, pulseRadius,
                    fill=None,
                    border=self.colors['restoration'],
                    borderWidth=1,
                    opacity=30)
            
            # Draw healing wave if active
            if self.healingWave['isActive']:
                waveRadius = self.healingWave['radius'] * zoomLevel
                drawCircle(screenX, screenY, waveRadius,
                        fill=None,
                        border='lightGreen',
                        borderWidth=2,
                        opacity=40)
            
            # Draw character body
            self._drawCharacterBody(screenX, screenY, zoomLevel)
            
            # Draw UI elements
            self._drawDirectionIndicator(screenX, screenY, zoomLevel)
            self._drawStrengthBar(screenX, screenY, zoomLevel)
            
        except Exception as e:
            print(f"Error in character draw: {e}")
            # Fallback to simple circle if drawing fails
            drawCircle(screenX, screenY, 10, fill='red')

    def _drawRestorationRadius(self, screenX, screenY, zoomLevel):
        # Main restoration circle
        radius = self.getRestorationRadius() * zoomLevel
        drawCircle(screenX, screenY, radius,
                fill=None,
                border='lightBlue',
                borderWidth=2,
                opacity=80)
        
        # Pulsing effect
        pulseRadius = radius * (0.8 + 0.2 * math.sin(self.animationFrame))
        drawCircle(screenX, screenY, pulseRadius,
                fill=None,
                border='lightBlue',
                borderWidth=1,
                opacity=40)
        
    def _drawCharacterBody(self, screenX, screenY, zoomLevel):
        try:
            # Calculate size based on zoom
            size = max(3, self.visual['spriteSize'] * zoomLevel)
            
            # Add bounce animation when moving
            if self.isMoving:
                screenY += math.sin(self.animationFrame * 4) * 2
            
            print(f"\nDrawing character at ({screenX}, {screenY})")
            print(f"Current direction: {self.direction}")
            print(f"Sprite dictionary exists: {hasattr(self, 'sprites')}")
            if hasattr(self, 'sprites') and self.sprites:
                print(f"Available sprites: {list(self.sprites.keys())}")
                sprite = self.sprites.get(self.direction)
                print(f"Sprite for {self.direction}: {'Found' if sprite else 'Not found'}")
                
                if sprite:
                    # Remove align parameter as it might cause issues
                    drawImage(sprite, 
                             screenX - size/2, 
                             screenY - size/2,
                             width=size, 
                             height=size)
                    print("Drew sprite successfully")
                    return
                
            raise Exception("No valid sprite available")
                
        except Exception as e:
            print(f"Falling back to circle drawing due to: {e}")
            # Fallback to circle
            size = max(3, self.visual['baseSize'] * zoomLevel)
            drawCircle(screenX, screenY, size/2,
                      fill=self.colors['body'],
                      border=self.colors['outline'])

    def _drawDirectionIndicator(self, screenX, screenY, zoomLevel):
        size = max(3, self.visual['baseSize'] * zoomLevel)
        length = size * self.visual['directionLength']
        
        # Calculate endpoint based on direction
        endX, endY = screenX, screenY
        if self.direction == 'right': endX += length
        elif self.direction == 'left': endX -= length
        elif self.direction == 'down': endY += length
        elif self.direction == 'up': endY -= length
        
        # Draw direction line and endpoint
        lineWidth = max(1, min(math.ceil(zoomLevel), 3))
        drawLine(screenX, screenY, endX, endY,
                fill=self.colors['direction'], 
                lineWidth=lineWidth)
        drawCircle(endX, endY, max(1, size * 0.15),
                  fill=self.colors['direction'])

    def _drawStrengthBar(self, screenX, screenY, zoomLevel):
        size = max(3, self.visual['baseSize'] * zoomLevel)
        
        # Draw strength value
        drawLabel(f"Strength: {self.strength:.1f}", 
                 screenX, screenY - size - 10,
                 fill='white', bold=True,
                 border='black', borderWidth=1)
        
        # Draw strength bar
        barWidth = size * 2
        barHeight = self.visual['strengthIndicatorHeight']
        barX = screenX - barWidth/2
        barY = screenY - size - 5
        
        # Background
        drawRect(barX, barY, barWidth, barHeight, 
                fill='gray', opacity=50)
        
        # Fill bar based on current strength
        fillWidth = barWidth * (self.strength / self.maxStrength)
        fillColor = (self.colors['strength_high'] if self.strength > self.maxStrength/2 
                    else self.colors['strength_low'])
        drawRect(barX, barY, fillWidth, barHeight, fill=fillColor)

    def setStrength(self, strength):
        self.strength = max(self.minStrength, min(self.maxStrength, strength))

    def getRestorationRadius(self):
        # Make sure we return a reasonable minimum radius
        baseRadius = self.strength * self.restorationRadiusMultiplier
        minRadius = self.visual['baseSize'] * 2  # Minimum radius should be visible
        return max(baseRadius, minRadius)

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
            'speed': self.speed,
            'strength': self.strength,
            'restorationRadius': self.getRestorationRadius()
        }

    def canMoveTo(self, game, x, y):
        # Check bounds
        if not (self.worldBounds['left'] <= x <= self.worldBounds['right'] and
                self.worldBounds['top'] <= y <= self.worldBounds['bottom']):
            return False
        
        # Check terrain walkability
        return game.isTerrainWalkable(x, y)
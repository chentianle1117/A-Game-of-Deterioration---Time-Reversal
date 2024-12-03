from cmu_graphics import *
import math
import os
from PIL import Image

'''
Character Sprite Image Creidt: https://www.sandromaglione.com/articles/pixel-art-top-down-game-sprite-design-and-animation
'''

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
            'baseSize': 15,
            'strengthIndicatorHeight': 4,
            'restoreEffectOpacity': 80,
            'spriteSize': min(cellWidth, cellHeight) * 0.8,
            'backgroundColor': None,
        }

        # Initialize sprites after setting up visual parameters
        self._loadSprites()
        
        print(f"\nSprite initialization complete:")
        print(f"Sprite dictionary exists: {hasattr(self, 'sprites')}")
        if hasattr(self, 'sprites') and self.sprites:
            print(f"Available sprites: {list(self.sprites.keys())}")
        else:
            print("No sprites loaded")
        
        # Rest of the initialization remains the same
        self.position = {
            'x': (worldWidth * cellWidth) // 2,
            'y': (worldHeight * cellHeight) // 2
        }
        self.direction = 'down'
        self.speed = 2.5
        
        self.strength = 0.1
        self.maxStrength = 5.0
        self.minStrength = 0.1
        self.restorationRadiusMultiplier = 5
        
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

    def emitHealingWave(self, time):
        if time - self.healingWave['lastUsed'] < self.healingWave['cooldown']:
            return False
        
        self.healingWave['lastUsed'] = time
        self.healingWave['isActive'] = True
        self.healingWave['radius'] = 0
        return True

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
        if not self.healingWave['isActive']:
            return
        
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
            # Draw restoration radius first (so it's behind the character)
            self._drawRestorationRadius(screenX, screenY, zoomLevel)
            
            # Draw character body
            self._drawCharacterBody(screenX, screenY, zoomLevel)
            
            # Draw strength indicator
            self._drawStrengthBar(screenX, screenY, zoomLevel)
            
            # Draw healing wave if active
            if self.healingWave['isActive']:
                radius = self.healingWave['radius'] * zoomLevel
                drawCircle(screenX, screenY, radius,
                          fill=None, border='lightGreen',
                          borderWidth=2, opacity=40)
        
        except Exception as e:
            print(f"Error in character draw: {e}")
            # Emergency fallback
            drawCircle(screenX, screenY, 10, fill='red')

    def _drawRestorationRadius(self, x, y, zoom):
        try:
            radius = self.getRestorationRadius() * zoom
            
            # Main circle opacity based on strength
            base_opacity = 30 + (40 * min(1.0, self.strength))  # 30-70 range
            
            # Draw main circle
            drawCircle(x, y, radius,
                      fill='lightBlue',
                      opacity=base_opacity)
            
            # Draw border
            drawCircle(x, y, radius,
                      fill=None, 
                      border='lightBlue',
                      borderWidth=max(2, zoom * 0.5),
                      opacity=100)
            
            # Add pulse effect
            pulse = radius * (0.8 + 0.2 * math.sin(self.animationFrame))
            drawCircle(x, y, pulse,
                      fill='lightBlue',
                      opacity=base_opacity * 0.5)
        except Exception as e:
            print(f"Failed to draw restoration radius: {e}")

    def _drawCharacterBody(self, screenX, screenY, zoomLevel):
        try:
            size = max(32, self.visual['spriteSize'] * zoomLevel)
            if self.isMoving:
                screenY += math.sin(self.animationFrame * 4) * 2
            
            if hasattr(self, 'sprites') and self.sprites and self.direction in self.sprites:
                sprite = self.sprites[self.direction]
                if sprite:
                    drawImage(sprite,
                             screenX, 
                             screenY,
                             width=size, 
                             height=size,
                             align='center',
                             opacity=100)
                    return
                
            raise Exception("No valid sprite available")
        except Exception as e:
            print(f"Falling back to circle drawing due to: {e}")
            size = max(3, self.visual['baseSize'] * zoomLevel)
            drawCircle(screenX, screenY, size/2,
                      fill=self.colors['body'],
                      border=self.colors['outline'])

    def _drawDirectionIndicator(self, screenX, screenY, zoomLevel):
        'old function'
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

    def _drawStrengthBar(self, x, y, zoom):
        size = max(3, self.visual['baseSize'] * zoom)
        
        # Value label
        drawLabel(f"Strength: {self.strength:.1f}", 
                 x, y - size - 10,
                 fill='white', bold=True,
                 border='black', borderWidth=1)
        
        # Bar background and fill
        width = size * 2
        height = self.visual['strengthIndicatorHeight']
        barX = x - width/2
        barY = y - size - 5
        
        drawRect(barX, barY, width, height, fill='gray', opacity=50)
        
        fill_width = width * (self.strength / self.maxStrength)
        fill_color = self.colors['strength_high' if self.strength > self.maxStrength/2 else 'strength_low']
        drawRect(barX, barY, fill_width, height, fill=fill_color)

    def setStrength(self, strength):
        self.strength = max(self.minStrength, min(self.maxStrength, strength))

    def getRestorationRadius(self):
        # Adjusted to provide a smaller minimum radius
        baseRadius = self.strength * self.restorationRadiusMultiplier
        minRadius = self.visual['baseSize']  # Reduced minimum radius
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

    def _loadSprites(self):
        sprite_dir = 'assets/objects/characters/'
        sprite_files = {
            'down': 'Char1_front.png',
            'up': 'Char1_back.png',
            'left': 'Char1_left.png',
            'right': 'Char1_right.png'
        }
        
        self.sprites = {}
        for direction, filename in sprite_files.items():
            path = os.path.join(sprite_dir, filename)
            if not os.path.exists(path):
                print(f"Missing sprite: {filename}")
                continue
            
            try:
                # Open image and preserve alpha channel
                img = Image.open(path)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                    
                # Create a new RGBA image with transparent background
                new_img = Image.new('RGBA', img.size, (0, 0, 0, 0))
                new_img.paste(img, (0, 0), img)
                
                self.sprites[direction] = CMUImage(new_img)
                print(f"Loaded {direction} sprite with transparency")
            except Exception as e:
                print(f"Failed loading {filename}: {e}")
                self.sprites[direction] = None
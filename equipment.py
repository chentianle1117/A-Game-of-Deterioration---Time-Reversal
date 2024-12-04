from cmu_graphics import *
import random
import math
import time
import os
from PIL import Image

class Equipment:
    TYPES = {
        'power': {
            'color': 'purple',
            'strength_bonus': 0.75,  
            'symbol': '↑',
            'description': 'Healing Power',
            'icon': 'power_icon.png'
        },
        'radius': {
            'color': 'lightBlue',
            'radius_bonus': 8,  
            'symbol': '⊕',
            'description': 'Healing Radius',
            'icon': 'radius_icon.png'
        },
        'burst': {
            'color': 'yellow',
            'heal_amount': 0.5,
            'heal_radius': 3, 
            'symbol': '✷',
            'description': 'Burst Heal',
            'icon': 'burst_icon.png'
        },
        'speed': {
            'color': 'green',
            'speed_bonus': 0.2,
            'symbol': '⚡',
            'description': 'Movement Speed',
            'icon': 'speed_icon.png'
        }
    }

    sprites = {}  # Class-level sprite storage
    
    @classmethod
    def loadSprites(cls):
        sprite_dir = 'assets/objects/equipment/'
        
        for eq_type, data in cls.TYPES.items():
            try:
                path = os.path.join(sprite_dir, data['icon'])
                if not os.path.exists(path):
                    print(f"Missing equipment sprite: {data['icon']}")
                    continue
                
                # Open image and preserve alpha channel
                img = Image.open(path)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Create a new RGBA image with transparent background
                new_img = Image.new('RGBA', img.size, (0, 0, 0, 0))
                new_img.paste(img, (0, 0), img)
                
                cls.sprites[eq_type] = CMUImage(new_img)
                print(f"Loaded {eq_type} equipment sprite with transparency")
            except Exception as e:
                print(f"Failed loading {eq_type} sprite: {e}")
                cls.sprites[eq_type] = None

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 20
        self.collected = False
        
        # Randomly select equipment type
        self.type = random.choice(list(Equipment.TYPES.keys()))
        self.bonus = Equipment.TYPES[self.type].copy()
        # Add instant-use flag
        self.isInstantUse = (self.type == 'burst')

    def draw(self, game):
        if not self.collected:
            screenX, screenY = game.worldToScreen(self.x, self.y)
            
            # Draw background effects
            drawCircle(screenX, screenY, self.size/1.2,
                      fill=self.bonus['color'],
                      opacity=40)
            drawCircle(screenX, screenY, self.size/1.6,
                      fill=self.bonus['color'],
                      opacity=80)
            
            # Pulsing effect
            pulseSize = self.size * (1 + math.sin(time.time() * 3) * 0.2)
            drawCircle(screenX, screenY, pulseSize/1.4,
                      fill=None, border=self.bonus['color'],
                      borderWidth=2, opacity=50)
            
            # Draw sprite if available, fallback to symbol if not
            if self.type in Equipment.sprites and Equipment.sprites[self.type]:
                sprite = Equipment.sprites[self.type]
                sprite_size = self.size * 1.5
                drawImage(sprite,
                         screenX,
                         screenY,
                         width=sprite_size,
                         height=sprite_size,
                         align='center')
            else:
                # Fallback to symbol
                drawLabel(self.bonus['symbol'],
                         screenX, screenY,
                         fill='white',
                         bold=True,
                         size=25)
    
    def getBonuses(self):
        return {'type': self.type, 'isInstantUse': self.isInstantUse, **self.bonus}
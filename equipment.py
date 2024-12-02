from cmu_graphics import *
import random
import math
import time

class Equipment:
    TYPES = {
        'radius': {
            'color': 'lightBlue',
            'radius_bonus': 8,
            'symbol': '⊕',
            'description': 'Healing Radius'
        },
        'power': {
            'color': 'lightGreen',
            'strength_bonus': 0.15,
            'symbol': '↑',
            'description': 'Healing Power'
        },
        'burst': {
            'color': 'purple',
            'heal_amount': 0.4,
            'heal_radius': 5,
            'symbol': '✷',
            'description': 'Burst Heal'
        }
    }

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
            
            # Draw outer glow
            drawCircle(screenX, screenY, self.size/1.2,
                      fill=self.bonus['color'],
                      opacity=40)
            
            # Draw inner circle
            drawCircle(screenX, screenY, self.size/1.6,
                      fill=self.bonus['color'],
                      opacity=80)
            
            # Draw pulsing effect
            pulseSize = self.size * (1 + math.sin(time.time() * 3) * 0.2)
            drawCircle(screenX, screenY, pulseSize/1.4,
                      fill=None,
                      border=self.bonus['color'],
                      borderWidth=2,
                      opacity=50)
            
            # Draw symbol
            drawLabel(self.bonus['symbol'],
                     screenX, screenY,
                     fill='white',
                     bold=True,
                     size=25)
    
    def getBonuses(self):
        return {'type': self.type, 'isInstantUse': self.isInstantUse, **self.bonus}
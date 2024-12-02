from cmu_graphics import *
import random

class Equipment:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 20
        self.collected = False
        
        # Single equipment type with fixed bonuses
        self.bonus = {
            'color': 'lightBlue',
            'strength_bonus': 0.08,   
            'radius_bonus': 6,       
            'symbol': '+'
        }
    
    def draw(self, game):
        if not self.collected:  # Only draw if not collected
            screenX, screenY = game.worldToScreen(self.x, self.y)
            
            # Draw equipment circle
            drawCircle(screenX, screenY, self.size/2,
                      fill=self.bonus['color'],
                      opacity=80)
            
            # Draw symbol
            drawLabel(self.bonus['symbol'],
                     screenX, screenY,
                     fill='white',
                     bold=True,
                     size=25)
    
    def getBonuses(self):
        return self.bonus
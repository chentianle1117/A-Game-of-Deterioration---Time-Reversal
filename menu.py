# menu.py
from cmu_graphics import *

class MenuState:
    def __init__(self, width, height):
        # Window dimensions
        self.width = width
        self.height = height
        
        # Menu colors
        self.colors = {
            'background': 'black',
            'button': rgb(40, 40, 40),
            'button_hover': rgb(60, 60, 60),
            'text': 'white',
            'title': 'white',
            'version': 'gray',
            'instructions': 'lightGray',
            'highlight': 'lightGreen'
        }
        
        # Menu title settings
        self.title = {
            'text': 'Environmental Restoration',
            'subtitle': 'A Game of Healing and Balance',
            'size': 48,
            'y_pos': height // 5
        }
        
        # Game description
        self.description = [
            "Goal: Keep the world's deterioration below 80% before time runs out!",
            "",
            "Key Features:",
            "• Design your terrain in the map editor",
            "• Use healing waves (Space) to restore deteriorating land",
            "• Watch out for the deterioration meter!",
            "",
            "Controls:",
            "WASD/Arrows - Move character",
            "Space - Release healing wave",
            "Shift - Sprint",
            "+/- - Zoom in/out",
            "M - Toggle map view",
            "ESC - Return to menu"
        ]
        
        # Define buttons
        self.buttons = [
            {
                'text': 'Start Your Adventure',
                'action': 'construct_map',
                'y_offset': 20,
                'tooltip': 'Open the map editor to create your own world'
            }
        ]
        
        # Button dimensions
        self.button_width = 240
        self.button_height = 60
        
        # Initialize hover state
        self.hover_button = None
        
    def isMouseOverButton(self, mouseX, mouseY, button):
        """Check if mouse is over a button"""
        buttonX = self.width // 2
        buttonY = self.height // 2 + button['y_offset']
        
        return (abs(mouseX - buttonX) < self.button_width // 2 and
                abs(mouseY - buttonY) < self.button_height // 2)
    
    def drawButton(self, button, isHovered=False):
        """Draw a menu button"""
        # Calculate button position
        centerX = self.width // 2
        centerY = self.height // 2 + button['y_offset']
        
        # Draw button background
        color = self.colors['button_hover'] if isHovered else self.colors['button']
        drawRect(centerX - self.button_width//2,
                centerY - self.button_height//2,
                self.button_width, self.button_height,
                fill=color,
                border=self.colors['text'],
                borderWidth=2)
        
        # Draw button text
        drawLabel(button['text'],
                 centerX, centerY,
                 size=20,
                 bold=True,
                 fill=self.colors['text'])
        
        # Draw tooltip if hovered
        if isHovered and 'tooltip' in button:
            drawLabel(button['tooltip'],
                     centerX,
                     centerY + self.button_height//2 + 20,
                     size=16,
                     fill=self.colors['text'],
                     opacity=70)
    
    def draw(self):
        """Draw the menu screen"""
        # Draw background
        drawRect(0, 0, self.width, self.height,
                fill=self.colors['background'])
        
        # Draw title and subtitle
        drawLabel(self.title['text'],
                 self.width//2,
                 self.title['y_pos'],
                 size=self.title['size'],
                 bold=True,
                 fill=self.colors['title'])
        
        drawLabel(self.title['subtitle'],
                 self.width//2,
                 self.title['y_pos'] + 50,
                 size=24,
                 bold=True,
                 fill=self.colors['highlight'])
        
        # Draw description (aligned to the left)
        startX = self.width//4  # Move text to the left
        startY = self.title['y_pos'] + 100
        lineHeight = 22
        
        for i, line in enumerate(self.description):
            color = self.colors['highlight'] if line.startswith('•') else self.colors['instructions']
            size = 18 if line.startswith('Key Features:') or line.startswith('Controls:') else 16
            bold = line.startswith('Key Features:') or line.startswith('Controls:')
            
            drawLabel(line,
                     startX,  # Use left alignment
                     startY + i * lineHeight,
                     size=size,
                     bold=bold,
                     fill=color,
                     align='left')  # Align text to the left
        
        # Draw buttons (keep centered)
        for button in self.buttons:
            self.drawButton(button, 
                          isHovered=(button == self.hover_button))
        
        # Draw version
        drawLabel('Version 1.0',
                 self.width//2,
                 self.height - 20,
                 size=16,
                 fill=self.colors['version'])
    
    def handleClick(self, mouseX, mouseY):
        """Handle mouse clicks and return the action if a button is clicked"""
        for button in self.buttons:
            if self.isMouseOverButton(mouseX, mouseY, button):
                return button['action']
        return None
    
    def updateHover(self, mouseX, mouseY):
        """Update button hover state"""
        self.hover_button = None
        for button in self.buttons:
            if self.isMouseOverButton(mouseX, mouseY, button):
                self.hover_button = button
                break
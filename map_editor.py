from cmu_graphics import *
import numpy as np
import random

'''
====Terrain Map Generation Referenced Materials:====
https://jackmckew.dev/3d-terrain-in-python.html
https://github.com/fmerizzi/Procedural-terrain-generation-with-style-transfer? (referenced the general ideas, not directly the code)

====AI Assistance Summary====
The following features were implemented with Claude 3.5's help, mostly for debugging and optimization:

paint():
- Optimized brush painting using numpy's ogrid
- Circular brush mask implementation
- Smooth value blending
'''

class MapEditor:
    def __init__(self, width, height, worldWidth, worldHeight):
        self.width = width
        self.height = height
        self.editorWidth = worldWidth // 4
        self.editorHeight = worldHeight // 4
        self.finalWidth = self.editorWidth * 4
        self.finalHeight = self.editorHeight * 4
        self.cellWidth = width / self.editorWidth
        self.cellHeight = height / self.editorHeight
        self.grid = np.zeros((self.editorHeight, self.editorWidth))
        self.brush = {
            'size': 2,
            'minSize': 1,
            'maxSize': 10,
            'value': 1.0,
            'opacity': 0.1
        }
        self.ui = {
            'saveButton': {
                'text': 'Generate World',
                'x': width - 100,
                'y': 30,
                'width': 150,
                'height': 40
            },
            'tools': [
                {'text': 'Water (Lowest)', 'value': 0.0, 'key': 'b'},
                {'text': 'Dirt/Grass (Medium)', 'value': 0.5, 'key': 'm'},
                {'text': 'High Ground', 'value': 1.0, 'key': 'w'}
            ]
        }
        self.mouseX = 0
        self.mouseY = 0

    def draw(self):
        for row in range(self.editorHeight):
            for col in range(self.editorWidth):
                value = self.grid[row, col]
                gray = int(value * 255)
                color = rgb(gray, gray, gray)
                drawRect(col * self.cellWidth, row * self.cellHeight, self.cellWidth + 1, self.cellHeight + 1, fill=color)
        self.drawUI()
        self.drawBrushPreview()

    def drawUI(self):
        panelHeight = 180  # Increased height for new tool
        drawRect(0, 0, 250, panelHeight, fill='black', opacity=50)
        y = 30
        for tool in self.ui['tools']:
            drawLabel(f"{tool['text']} ({tool['key']})", 125, y, fill='white', bold=True)
            y += 25
        drawLabel(f"Brush Size: {self.brush['size']} ([ ])", 125, y, fill='white', bold=True)
        y += 25
        drawLabel("Use medium elevation for", 125, y, fill='white', bold=True)
        y += 20
        drawLabel("best tree growth", 125, y, fill='white', bold=True)
        
        btn = self.ui['saveButton']
        drawRect(btn['x'] - btn['width']//2, btn['y'] - btn['height']//2, 
                btn['width'], btn['height'], fill='darkGray', border='white')
        drawLabel(btn['text'], btn['x'], btn['y'], fill='white', bold=True)
        
    def drawBrushPreview(self):
        radius = self.brush['size'] * max(self.cellWidth, self.cellHeight)
        drawCircle(self.mouseX, self.mouseY, radius, fill=None, border='white', borderWidth=2)
        value = self.brush['value']
        gray = int(value * 255)
        color = rgb(gray, gray, gray)
        drawCircle(self.mouseX, self.mouseY, radius * 0.2, fill=color, opacity=75)

    def generateTerrainMap(self):
        # Create base heightmap by upscaling the editor grid
        upscaled = np.repeat(np.repeat(self.grid, 4, axis=0), 4, axis=1)
        upscaled = upscaled[:self.finalHeight, :self.finalWidth]
        
        # Add subtle random variations
        upscaled += np.random.uniform(-0.05, 0.05, upscaled.shape)
        np.clip(upscaled, 0, 1, out=upscaled)

        terrainMap = []
        for row in range(self.finalHeight):
            terrainRow = []
            for col in range(self.finalWidth):
                height = upscaled[row, col]
                
                # Calculate average height of surrounding area
                avgHeight = 0
                neighbors = 0
                for dr in [-1, 0, 1]:
                    newRow = row + dr
                    if not (0 <= newRow < self.finalHeight): continue
                    for dc in [-1, 0, 1]:
                        newCol = col + dc
                        if not (0 <= newCol < self.finalWidth): continue
                        avgHeight += upscaled[newRow, newCol]
                        neighbors += 1
                avgHeight /= neighbors
                
                # Determine terrain type based on height
                terrain = self._getTerrainType(height, avgHeight)
                
                # Calculate tree growth potential for suitable terrain
                growthPotential = 0.5  # default value
                if terrain in ["dirt", "tall_grass", "tiny_leaves"]:
                    # Adjust based on elevation and add some randomness
                    heightFactor = avgHeight - 0.5
                    randomFactor = np.random.uniform(-0.1, 0.1)
                    growthPotential = max(0.2, min(1.0, 0.5 + heightFactor * 0.5 + randomFactor))
                
                terrainRow.append({
                    "terrain": terrain,
                    "texture": terrain,
                    "explored": False,
                    "growthPotential": growthPotential
                })
            terrainMap.append(terrainRow)

        return terrainMap

    def _getTerrainType(self, height, avgHeight):
        if height < 0.2:
            return "water"
        
        if height < 0.3:
            return "sand" if random.random() < 0.7 else "dirt"
        
        if height < 0.8:
            # Main land area
            if avgHeight < 0.5:
                # Lower elevation
                roll = random.random()
                if roll < 0.4: return "dirt"
                if roll < 0.8: return "tall_grass"
                return "tiny_leaves"
            else:
                # Higher elevation
                roll = random.random()
                if roll < 0.3: return "dirt"
                if roll < 0.7: return "tall_grass"
                return "path_rocks"
        
        if height < 0.95:
            # High ground
            roll = random.random()
            if roll < 0.6: return "path_rocks"
            if roll < 0.8: return "brick"
            return "dirt"
        
        return "snow"  # Mountain peaks

    def updateMousePos(self, mouseX, mouseY):
        self.mouseX = mouseX
        self.mouseY = mouseY

    def getGridCoords(self, mouseX, mouseY):
        col = int(mouseX / self.cellWidth)
        row = int(mouseY / self.cellHeight)
        return row, col

    #====Ogrid function introduced by Claude 3.5====
    def paint(self, mouseX, mouseY):
        row, col = self.getGridCoords(mouseX, mouseY)
        brushSize = self.brush['size']
        y, x = np.ogrid[-brushSize:brushSize+1, -brushSize:brushSize+1]
        mask = x*x + y*y <= brushSize*brushSize
        for dy in range(-brushSize, brushSize + 1):
            for dx in range(-brushSize, brushSize + 1):
                newRow, newCol = row + dy, col + dx
                if not mask[dy+brushSize, dx+brushSize]:
                    continue
                if 0 <= newRow < self.editorHeight and 0 <= newCol < self.editorWidth:
                    current = self.grid[newRow, newCol]
                    target = self.brush['value']
                    self.grid[newRow, newCol] = (current * (1 - self.brush['opacity']) + target * self.brush['opacity'])
    #====Ogrid function introduced by Claude 3.5====

    def handleKey(self, key):
        if key == '[':
            self.brush['size'] = max(self.brush['minSize'], self.brush['size'] - 1)
        elif key == ']':
            self.brush['size'] = min(self.brush['maxSize'], self.brush['size'] + 1)
        else:
            for tool in self.ui['tools']:
                if key == tool['key']:
                    self.brush['value'] = tool['value']

    def isOverSaveButton(self, mouseX, mouseY):
        btn = self.ui['saveButton']
        return (abs(mouseX - btn['x']) < btn['width']//2 and abs(mouseY - btn['y']) < btn['height']//2)

    def handleClick(self, mouseX, mouseY):
        if self.isOverSaveButton(mouseX, mouseY):
            return self.generateTerrainMap()
        return None

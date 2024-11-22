from cmu_graphics import *
import numpy as np

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
        terrainMap = []
        upscaled = np.repeat(np.repeat(self.grid, 4, axis=0), 4, axis=1)
        upscaled = upscaled[:self.finalHeight, :self.finalWidth]
        
        # Add some noise for variation
        noise = np.random.uniform(-0.05, 0.05, upscaled.shape)
        upscaled += noise
        np.clip(upscaled, 0, 1, out=upscaled)

        for row in range(self.finalHeight - 1):
            terrainRow = []
            for col in range(self.finalWidth - 1):
                value = upscaled[row, col]
                
                # Get surrounding values for smoother transitions
                surroundingVals = []
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        r, c = row + dr, col + dc
                        if (0 <= r < self.finalHeight and 
                            0 <= c < self.finalWidth):
                            surroundingVals.append(upscaled[r, c])
                avgVal = sum(surroundingVals) / len(surroundingVals)
                
                # Terrain type decision with more natural distribution
                if value < 0.2:
                    terrain = "water"
                elif value < 0.3:
                    # Transition zone between water and land
                    terrain = "sand" if np.random.rand() < 0.7 else "dirt"
                elif value < 0.8:
                    # Main land area with varied vegetation
                    rand = np.random.rand()
                    if avgVal < 0.5:  # Lower elevation
                        if rand < 0.4:
                            terrain = "dirt"
                        elif rand < 0.8:
                            terrain = "tall_grass"
                        else:
                            terrain = "tiny_leaves"
                    else:  # Higher elevation
                        if rand < 0.3:
                            terrain = "dirt"
                        elif rand < 0.7:
                            terrain = "tall_grass"
                        else:
                            terrain = "path_rocks"
                elif value < 0.95:
                    # Higher ground
                    rand = np.random.rand()
                    if rand < 0.6:
                        terrain = "path_rocks"
                    elif rand < 0.8:
                        terrain = "brick"
                    else:
                        terrain = "dirt"  # Some dirt patches in high ground
                else:
                    # Mountain tops
                    terrain = "snow"

                # Add variation in growth potential for trees
                growthPotential = 0.5
                if terrain in ["dirt", "tall_grass", "tiny_leaves"]:
                    # Calculate growth potential based on elevation and surroundings
                    growthPotential = min(1.0, max(0.2, 
                        0.5 + (avgVal - 0.5) * 0.5 +  # Elevation factor
                        np.random.uniform(-0.1, 0.1)))  # Random variation
                
                terrainRow.append({
                    "terrain": terrain,
                    "texture": terrain,
                    "explored": False,
                    "growthPotential": growthPotential  # Add growth potential
                })
            terrainMap.append(terrainRow)

        print(f"Generated terrain map: {len(terrainMap)}x{len(terrainMap[0])}")
        return terrainMap


    def updateMousePos(self, mouseX, mouseY):
        self.mouseX = mouseX
        self.mouseY = mouseY

    def getGridCoords(self, mouseX, mouseY):
        col = int(mouseX / self.cellWidth)
        row = int(mouseY / self.cellHeight)
        return row, col

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

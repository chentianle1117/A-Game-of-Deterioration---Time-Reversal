from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import os
from cmu_graphics import CMUImage
import math
'''
====Image Cache Implementation Guide:Written by Claude 3.5, implemented by me====

Image Cache Implementation Guide:
1. Cache Structure:
    cache = {
        (terrainType, width, height, state): CMUImage,
        ('water', 32, 32, 0.5): <water_texture>,
        ('dirt', 32, 32, 0.75): <deteriorated_dirt_texture>
    }

 2. Cache Key Design:
    - For normal terrain: (type, width, height, deteriorationLevel)
    - For water: (type, width, height, blurAmount)
    - Round float values (like 0.78123 -> 0.78) to limit cache size

 3. Cache Usage Pattern:
    if cacheKey in self.cache:
        return cached_texture
    else:
        new_texture = create_texture()
        self.cache[cacheKey] = new_texture
        return new_texture

 4. Cache Cleanup:
    - Clear every N updates (e.g., every 30 frames)
    - Clear when window resizes
    - Clear when texture settings change

 5. Memory Management:
    - Limit cache size
    - Use rounded values for cache keys
    - Clear unused textures periodically
'''

'''
====Additional Cache Tutorial Resources referenced:====
https://api.arcade.academy/en/development/programming_guide/textures.html?utm_source=chatgpt.com
https://www.datacamp.com/tutorial/python-cache-introduction?utm_source=chatgpt.com
'''

terrainNameMap = {
    "path_rocks": "PATHROCKS.png",
    "pavement": "PAVEMENT.png",
    "dirt": "DIRT.png",
    "water": "WATER.png",
    "tall_grass": "TALLGRASS.png",
    "tiny_leaves": "TINYLEAVES.png",
    "woodtile": "WOODTILE.png",
    "snow": "SNOW.png",
    "sand": "SAND.png",
    "brick": "BRICKS.png",
}

class TextureManagerOptimized:
    def __init__(self):
        self.textures = {} 
        self.deterioratedTextures = {}  
        self.cache = {}  
        self.updateCounter = 0  
        
        # terrain settings
        self.terrainAttributes = {
            "path_rocks": {"updateFrequency": 10, "maxLife": 500},
            "pavement": {"updateFrequency": 10, "maxLife": 300},
            "dirt": {"updateFrequency": 10, "maxLife": 200},
            "water": {"updateFrequency": 10, "maxLife": 300},
            "tall_grass": {"updateFrequency": 10, "maxLife": 100},
            "tiny_leaves": {"updateFrequency": 10, "maxLife": 100},
            "woodtile": {"updateFrequency": 10, "maxLife": 400},
            "snow": {"updateFrequency": 10, "maxLife": 100},
            "sand": {"updateFrequency": 10, "maxLife": 500},
            "brick": {"updateFrequency": 10, "maxLife": 300}
        }
        self.cellStates = {} 
        self.lastUpdateTimes = {}
        self.deteriorationRate = 0.003
        self.healingRate = 0.015
        self.loadTextures()

    def findTextureDirectory(self):
        currentDir = os.path.dirname(os.path.abspath(__file__))
        possiblePaths = [
            os.path.join(currentDir, "assets", "textures"),
            os.path.join(currentDir, "..", "assets", "textures"),
            "assets/textures",
        ]
        for path in possiblePaths:
            if os.path.exists(path):
                return os.path.abspath(path)
        return None

    def loadTextures(self):
        textureDir = self.findTextureDirectory()
        if not textureDir:
            print("Texture directory not found.")
            return

        originalDir = os.path.join(textureDir, "original landscape")
        deterioratedDir = os.path.join(textureDir, "deteriorated landscape")

        #====Texture Loading Section:Debugged by Claude 3.5====
        for terrainName, filename in terrainNameMap.items():
            originalPath = os.path.join(originalDir, filename)
            deterioratedPath = os.path.join(deterioratedDir, filename)

            # load original
            if os.path.exists(originalPath):
                self.textures[terrainName] = Image.open(originalPath).convert("RGB")
            else:
                print(f"Error: Missing original texture for '{terrainName}'")

            # load deteriorated version
            if os.path.exists(deterioratedPath):
                self.deterioratedTextures[terrainName] = Image.open(deterioratedPath).convert("RGB")
            else:
                if terrainName in self.textures:
                    self.deterioratedTextures[terrainName] = self.textures[terrainName].copy()
                else:
                    print(f"Error: Missing deteriorated texture and fallback for '{terrainName}'")
            #====Texture Loading Section:Debugged by Claude 3.5====

    def getCellKey(self, row, col):
        return f"{row},{col}"

    def initializeCellState(self, row, col, terrainType):
        key = self.getCellKey(row, col)
        if key not in self.cellStates:
            self.cellStates[key] = {
                'lifeRatio': 0.0,
                'terrain': terrainType,
                'lastUpdate': self.updateCounter
            }
            self.lastUpdateTimes[key] = self.updateCounter
        return self.cellStates[key]

    def processCellDeterioration(self, row, col, character=None, elapsedSteps=1):
        try:
            key = self.getCellKey(row, col)
            if key not in self.cellStates:
                return None
            
            cell = self.cellStates[key]
            terrain = cell['terrain']

            # water doesn't deteriorate
            if terrain == "water":
                return 0.0

            if terrain not in self.terrainAttributes:
                print(f"Warning: Missing terrain attributes for {terrain}, using defaults")
                self.terrainAttributes[terrain] = {"updateFrequency": 10, "maxLife": 300}

            # calculate changes
            deterioration = self.deteriorationRate * elapsedSteps
            healing = 0
            
            if character:
                charX, charY = character.getPosition()
                cellX = col * character.cellWidth + (character.cellWidth / 2)
                cellY = row * character.cellHeight + (character.cellHeight / 2)
                
                distance = math.sqrt((charX - cellX) ** 2 + (charY - cellY) ** 2)
                restorationRadius = character.getRestorationRadius()
                
                if distance <= restorationRadius:
                    distanceRatio = 1 - (distance / restorationRadius)
                    healing = self.healingRate * distanceRatio * character.strength * elapsedSteps

            cell['lifeRatio'] = max(0.0, min(1.0, cell['lifeRatio'] + deterioration - healing))
            self.lastUpdateTimes[key] = self.updateCounter
            
            return cell['lifeRatio']
            
        except Exception as e:
            print(f"Error in processCellDeterioration for cell ({row}, {col}): {e}")
            return 0.0

    def calculateGlobalDeterioration(self):
        total = 0
        count = 0
        for key, cell in self.cellStates.items():
            if cell['terrain'] != 'water':
                total += cell['lifeRatio']
                count += 1
        return total / count if count > 0 else 0.0

    def applyGlobalHealing(self, amount):
        healed = False
        for key, cell in self.cellStates.items():
            if cell['terrain'] != 'water':
                old = cell['lifeRatio']
                cell['lifeRatio'] = max(0.0, old - amount)
                if cell['lifeRatio'] != old:
                    healed = True
        return healed

    def updateDeterioration(self, character=None):
        self.updateCounter += 1
        
        for key in list(self.cellStates.keys()):
            row, col = map(int, key.split(','))
            elapsedSteps = self.updateCounter - self.lastUpdateTimes.get(key, 0)
            
            if elapsedSteps > 0:
                self.processCellDeterioration(row, col, character, elapsedSteps)

        # clear cache occasionally
        if self.updateCounter % 30 == 0:
            self.cache.clear()

    def blendDeterioratedTexture(self, image, level, terrainType):
        try:
            if terrainType in self.deterioratedTextures:
                deteriorated = self.deterioratedTextures[terrainType]
            else:
                deteriorated = ImageOps.grayscale(image).convert("RGB")
            
            if image.size != deteriorated.size:
                deteriorated = deteriorated.resize(image.size, Image.LANCZOS)
                
            return Image.blend(image, deteriorated, level)
        except Exception as e:
            print(f"Error blending texture for {terrainType}: {e}")
            return image

    def getTextureForCell(self, row, col, terrainType, width, height, character=None):
        width = max(1, width)  
        height = max(1, height) 
        try:
            cellState = self.initializeCellState(row, col, terrainType)
            lifeRatio = cellState['lifeRatio']
            
            if terrainType not in self.textures:
                return None, lifeRatio

            # special water effect
            if terrainType == 'water':
                blurAmount = abs(math.sin(self.updateCounter * 0.5)) * 2
                cacheKey = (terrainType, width, height, round(blurAmount, 2))
                
                if cacheKey not in self.cache:
                    try:
                        original = self.textures[terrainType]
                        blurred = original.filter(ImageFilter.GaussianBlur(radius=blurAmount))
                        resized = blurred.resize((width, height), Image.LANCZOS)
                        self.cache[cacheKey] = CMUImage(resized)
                    except Exception as e:
                        print(f"Failed to create water texture: {e}")
                        return None, 0.0
                
                return self.cache[cacheKey], 0.0

            # handle other terrain
            roundedRatio = round(lifeRatio, 2)
            cacheKey = (terrainType, width, height, roundedRatio)
            
            if cacheKey not in self.cache:
                try:
                    original = self.textures[terrainType]
                    currentTexture = self.blendDeterioratedTexture(original, lifeRatio, terrainType)
                    resized = currentTexture.resize((width, height), Image.LANCZOS)
                    self.cache[cacheKey] = CMUImage(resized)
                except Exception as e:
                    print(f"Failed to create texture for terrain '{terrainType}': {e}")
                    return None, lifeRatio
                    
            return self.cache[cacheKey], lifeRatio

        except Exception as e:
            print(f"Error in getTextureForCell: {e}")
            return None, 0.0

    def clearCache(self):
        self.cache.clear()

    def setDeteriorationRate(self, rate):
        self.deteriorationRate = max(0.0, min(0.01, rate))

    def setHealingRate(self, rate):
        self.healingRate = max(0.0, min(0.02, rate))

    def getTerrainStats(self, row, col):
        key = self.getCellKey(row, col)
        if key in self.cellStates:
            return {
                'lifeRatio': self.cellStates[key]['lifeRatio'],
                'terrain': self.cellStates[key]['terrain'],
                'lastUpdate': self.lastUpdateTimes[key]
            }
        return None

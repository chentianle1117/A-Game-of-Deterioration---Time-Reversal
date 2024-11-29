from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import os
from cmu_graphics import CMUImage
import math

# Map terrain types to their corresponding file names
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
        self.terrainAttributes = {
            "path_rocks": {"updateFrequency": 10, "maxLife": 600},
            "pavement": {"updateFrequency": 10, "maxLife": 300},
            "dirt": {"updateFrequency": 10, "maxLife": 300},
            "water": {"updateFrequency": 10, "maxLife": 300},
            "tall_grass": {"updateFrequency": 10, "maxLife": 200},
            "tiny_leaves": {"updateFrequency": 10, "maxLife": 250},
            "woodtile": {"updateFrequency": 10, "maxLife": 400},
            "snow": {"updateFrequency": 10, "maxLife": 500},
            "sand": {"updateFrequency": 10, "maxLife": 500},
            "brick": {"updateFrequency": 10, "maxLife": 300}
        }
        self.cellStates = {} 
        self.lastUpdateTimes = {}  
        self.deteriorationRate = 0.001  
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
        """Load textures while preserving terrain attributes"""
        textureDir = self.findTextureDirectory()
        if not textureDir:
            print("Texture directory not found.")
            return

        originalDir = os.path.join(textureDir, "original landscape")
        deterioratedDir = os.path.join(textureDir, "deteriorated landscape")

        # Load textures but don't override terrain attributes
        for terrainName, filename in terrainNameMap.items():
            originalPath = os.path.join(originalDir, filename)
            deterioratedPath = os.path.join(deterioratedDir, filename)

            # Load original texture
            if os.path.exists(originalPath):
                self.textures[terrainName] = Image.open(originalPath).convert("RGB")
            else:
                print(f"Error: Missing original texture for '{terrainName}'")

            # Load deteriorated texture if available
            if os.path.exists(deterioratedPath):
                self.deterioratedTextures[terrainName] = Image.open(deterioratedPath).convert("RGB")
            else:
                # Use original texture as fallback
                if terrainName in self.textures:
                    self.deterioratedTextures[terrainName] = self.textures[terrainName].copy()
                else:
                    print(f"Error: Missing deteriorated texture and fallback for '{terrainName}'")


    def getCellKey(self, row, col):
        """Generate unique key for cell coordinates"""
        return f"{row},{col}"

    def initializeCellState(self, row, col, terrainType):
        """Initialize or return existing cell state"""
        key = self.getCellKey(row, col)
        if key not in self.cellStates:
            self.cellStates[key] = {
                'lifeRatio': 0.0,  # Start fresh
                'terrain': terrainType,
                'lastUpdate': self.updateCounter
            }
            self.lastUpdateTimes[key] = self.updateCounter
        return self.cellStates[key]

    def processCellDeterioration(self, row, col, character=None, elapsedSteps=1):
        """Process deterioration and healing for a single cell with better error handling"""
        try:
            key = self.getCellKey(row, col)
            if key not in self.cellStates:
                return None
            
            cell = self.cellStates[key]
            terrain = cell['terrain']

            # exclude water from deterioration
            if terrain == "water":
                return 0.0

            if terrain not in self.terrainAttributes:
                print(f"Warning: Missing terrain attributes for {terrain}, using defaults")
                self.terrainAttributes[terrain] = {
                    "updateFrequency": 10,
                    "maxLife": 300
                }

            attributes = self.terrainAttributes[terrain]
            
            # Calculate base deterioration
            deterioration = self.deteriorationRate * elapsedSteps
            
            # Apply character's healing effect if in range
            healing = 0
            if character:
                charX, charY = character.getPosition()
                cellX = col * character.cellWidth + (character.cellWidth / 2)
                cellY = row * character.cellHeight + (character.cellHeight / 2)
                
                distance = math.sqrt((charX - cellX) ** 2 + (charY - cellY) ** 2)
                restorationRadius = character.getRestorationRadius()
                
                if distance <= restorationRadius:
                    # Healing is stronger closer to character and scales with character strength
                    distanceRatio = 1 - (distance / restorationRadius)
                    healing = self.healingRate * distanceRatio * character.strength * elapsedSteps

            # Apply net change
            netChange = deterioration - healing
            cell['lifeRatio'] = max(0.0, min(1.0, cell['lifeRatio'] + netChange))
            
            # Update last update time
            self.lastUpdateTimes[key] = self.updateCounter
            
            return cell['lifeRatio']
            
        except Exception as e:
            print(f"Error in processCellDeterioration for cell ({row}, {col}): {e}")
            return 0.0  # Return safe default value
    def calculateGlobalDeterioration(self):
        """Calculate average deterioration across all non-water cells"""
        total = 0
        count = 0
        
        for key, cell in self.cellStates.items():
            if cell['terrain'] != 'water':
                total += cell['lifeRatio']
                count += 1
        if count == 0:
            return 0.0
        return total / count

    def applyGlobalHealing(self, amount):
        """Apply instant healing to all non-water cells"""
        healed = False
        for key, cell in self.cellStates.items():
            if cell['terrain'] != 'water':
                currentLife = cell['lifeRatio']
                # Ensure significant reduction in deterioration
                cell['lifeRatio'] = max(0.0, currentLife - amount)
                if cell['lifeRatio'] != currentLife:
                    healed = True
        return healed

    def updateDeterioration(self, character=None):
        """Global update for all cells"""
        self.updateCounter += 1
        
        # Process all existing cells
        for key in list(self.cellStates.keys()):
            row, col = map(int, key.split(','))
            lastUpdate = self.lastUpdateTimes.get(key, 0)
            elapsedSteps = self.updateCounter - lastUpdate
            
            if elapsedSteps > 0:
                self.processCellDeterioration(row, col, character, elapsedSteps)

        # Clear cache periodically
        if self.updateCounter % 30 == 0:  # Reduced frequency of cache clearing
            self.cache.clear()

    def blendDeterioratedTexture(self, image, level, terrainType):
        """Apply discoloration effect to an image."""
        try:
            # Use the already loaded deteriorated texture if available
            if terrainType in self.deterioratedTextures:
                deteriorated = self.deterioratedTextures[terrainType]
            else:
                # Fallback to grayscale if no deteriorated texture exists
                deteriorated = ImageOps.grayscale(image).convert("RGB")
            
            # Ensure images are the same size
            if image.size != deteriorated.size:
                deteriorated = deteriorated.resize(image.size, Image.LANCZOS)
                
            return Image.blend(image, deteriorated, level)
        except Exception as e:
            print(f"Error in blendDeterioratedTexture for {terrainType}: {e}")
            # Return original image as fallback
            return image

    def getTextureForCell(self, row, col, terrainType, width, height, character=None):
        """Get or create texture for a cell"""
        width = max(1, width)  
        height = max(1, height) 
        try:
            # Initialize if needed
            cellState = self.initializeCellState(row, col, terrainType)
            
            # Get current life ratio
            lifeRatio = cellState['lifeRatio']
            
            if terrainType not in self.textures:
                return None, lifeRatio

            # Special handling for water
            if terrainType == 'water':
                # Use updateCounter to create a pulsing effect
                blurAmount = abs(math.sin(self.updateCounter * 0.5)) * 2  # back and forth between 0 and 2
                cacheKey = (terrainType, width, height, round(blurAmount, 2))
                
                if cacheKey not in self.cache:
                    try:
                        original = self.textures[terrainType]
                        # Apply blur effect for water
                        blurred = original.filter(ImageFilter.GaussianBlur(radius=blurAmount))
                        resized = blurred.resize((width, height), Image.LANCZOS)
                        self.cache[cacheKey] = CMUImage(resized)
                    except Exception as e:
                        print(f"Failed to create water texture: {e}")
                        return None, 0.0
                
                return self.cache[cacheKey], 0.0

            # For other terrain types
            # Round life ratio for cache key to reduce cache size
            roundedRatio = round(lifeRatio, 2)  # Reduced precision for better caching
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
        """Clear the texture cache"""
        self.cache.clear()

    def setDeteriorationRate(self, rate):
        """Set the base deterioration rate"""
        self.deteriorationRate = max(0.0, min(0.01, rate))

    def setHealingRate(self, rate):
        """Set the base healing rate"""
        self.healingRate = max(0.0, min(0.02, rate))

    def getTerrainStats(self, row, col):
        """Get current stats for a cell"""
        key = self.getCellKey(row, col)
        if key in self.cellStates:
            return {
                'lifeRatio': self.cellStates[key]['lifeRatio'],
                'terrain': self.cellStates[key]['terrain'],
                'lastUpdate': self.lastUpdateTimes[key]
            }
        return None

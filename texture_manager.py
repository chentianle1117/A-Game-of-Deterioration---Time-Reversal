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
        self.textures = {}  # Original textures
        self.deterioratedTextures = {}  # Deteriorated textures
        self.cache = {}  # Cached resized textures
        self.updateCounter = 0  # Counter for updates
        self.terrainAttributes = {}  # Update frequency and max life
        self.cellStates = {}  # Track deterioration state per cell
        self.lastUpdateTimes = {}  # Track last update time for each cell
        self.deteriorationRate = 0.005  # Base deterioration rate
        self.healingRate = 0.015  # Base healing rate
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

            # Set default attributes for terrain
            self.terrainAttributes[terrainName] = {
                "updateFrequency": 10,  # Default update frequency
                "maxLife": 300,        # Default max life
            }

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
        """Process deterioration and healing for a single cell"""
        key = self.getCellKey(row, col)
        if key not in self.cellStates:
            return None

        cell = self.cellStates[key]
        terrain = cell['terrain']
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

    def discolorTexture(self, image, level):
        """Apply discoloration effect to an image."""
        grayscale = ImageOps.grayscale(image).convert("RGB")
        return Image.blend(image, grayscale, level)

    def getTextureForCell(self, row, col, terrainType, width, height, character=None):
        """Get or create texture for a cell"""
        # Initialize if needed
        cellState = self.initializeCellState(row, col, terrainType)
        
        # Get current life ratio
        lifeRatio = cellState['lifeRatio']
        
        if terrainType not in self.textures:
            return None, lifeRatio

        # Round life ratio for cache key to reduce cache size
        roundedRatio = round(lifeRatio, 2)  # Reduced precision for better caching
        cacheKey = (terrainType, width, height, roundedRatio)
        
        if cacheKey not in self.cache:
            try:
                original = self.textures[terrainType]
                
                # Apply discoloration effect
                currentTexture = self.discolorTexture(original, lifeRatio)
                resized = currentTexture.resize((width, height), Image.LANCZOS)
                self.cache[cacheKey] = CMUImage(resized)
            except Exception as e:
                print(f"Failed to create texture for terrain '{terrainType}': {e}")
                return None, lifeRatio
                
        return self.cache[cacheKey], lifeRatio

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
